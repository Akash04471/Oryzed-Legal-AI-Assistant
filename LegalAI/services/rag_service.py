import os
import re
import json
import logging
from groq import Groq
from LegalAI.services.embedding_service import get_embedding
from LegalAI.services.qdrant_service import search_similar_chunks

logger = logging.getLogger(__name__)

# Minimum similarity score (cosine distance) to consider search results relevant
SIMILARITY_THRESHOLD = 0.50

# Default Groq model (high-quality and free tier available)
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

_groq_client = None

def get_groq_client():
    """
    Initializes and returns the Groq client.
    Resolves GROQ_API_KEY from the environment.
    """
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not configured in .env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def expand_query(user_message, model_name):
    """
    Uses the LLM to generate alternative formulations of the user's query 
    to improve retrieval recall (Multi-Query Retrieval).
    """
    prompt = f"""You are a legal AI assistant. Your task is to generate 3 alternative versions of the user's legal query to maximize document retrieval in a vector database.
Include abbreviations, full names, and synonymous legal terms. 
Output ONLY a JSON list of strings. Do not include markdown formatting or explanations.

User Query: "{user_message}"
"""
    try:
        client = get_groq_client()
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = chat_completion.choices[0].message.content.strip()
        # Clean potential markdown markdown blocks
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        expanded = json.loads(content)
        if isinstance(expanded, list):
            # Include original query
            return [user_message] + expanded[:3]
    except Exception as e:
        logger.error(f"Query expansion failed: {e}")
        
    return [user_message]


def generate_answer(user_message, chat_history_context=None):
    """
    Coordinates semantic retrieval, multi-query expansion, and answer generation.
    """
    model_name = os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL
    
    # Check if query is non-legal
    if _is_non_legal_query(user_message):
        return {
            "response": (
                "I apologize, but I am a specialized Legal AI Assistant. "
                "I can only provide assistance with legal matters, legal research, case analysis, "
                "statutory interpretation, and legal consultation."
            ),
            "confidence_score": 1.0,
            "sources": []
        }
        
    logger.info(f"Original Query: {user_message}")

    # 1. Expand Query
    queries = expand_query(user_message, model_name)
    logger.info(f"Expanded Queries: {queries}")

    all_results = []
    # 2. Retrieve for all queries (Multi-Query)
    for q in queries:
        try:
            q_vec = get_embedding(q)
            # Retrieve Top-10 per query to ensure high recall before re-ranking
            hits = search_similar_chunks(q_vec, limit=10)
            all_results.extend(hits)
        except Exception as e:
            logger.error(f"Failed to generate embedding for query '{q}': {e}")
            
    # 3. Deduplicate and Sort (Simulated Re-ranking by highest score)
    unique_chunks = {}
    for hit in all_results:
        # Use text as unique key to prevent duplicates
        key = hit["text"]
        if key not in unique_chunks or hit["score"] > unique_chunks[key]["score"]:
            unique_chunks[key] = hit
            
    sorted_results = sorted(unique_chunks.values(), key=lambda x: x["score"], reverse=True)
    
    # Take top 8 unique chunks
    top_results = sorted_results[:8]
    
    best_score = top_results[0]["score"] if top_results else 0.0
    
    logger.info(f"Retrieval complete. Top similarity score: {best_score:.4f}. Retrieved {len(top_results)} unique chunks.")
    
    # 4. Handle Fallback if below threshold
    if not top_results or best_score < SIMILARITY_THRESHOLD:
        logger.info(f"Score {best_score:.4f} is below threshold {SIMILARITY_THRESHOLD}. Triggering general knowledge fallback.")
        return _generate_fallback_answer(user_message, chat_history_context, model_name, best_score)
        
    logger.info("Generating answer from retrieved Qdrant context.")
    
    # 5. Gather context
    context_parts = []
    sources = []
    
    for hit in top_results:
        source_ref = f"{hit['file_name']} (Page {hit['start_page']})"
        if hit["end_page"] != hit["start_page"]:
            source_ref = f"{hit['file_name']} (Pages {hit['start_page']}-{hit['end_page']})"
            
        context_parts.append(
            f"--- Document Source: {hit['file_name']} | Pages: {hit['start_page']}-{hit['end_page']} ---\n"
            f"Content: {hit['text']}\n"
        )
        
        source_meta = {
            "file_name": hit["file_name"],
            "start_page": hit["start_page"],
            "end_page": hit["end_page"],
            "score": hit["score"]
        }
        if source_meta not in sources:
            sources.append(source_meta)
            
    context_text = "\n".join(context_parts)
    
    system_prompt = f"""You are LegalAI, an expert legal assistant with deep knowledge of Indian law.
Your task is to answer the user's legal question using the provided Context.

STRICT RULES:
1. You are EXCLUSIVELY a Legal AI Assistant. 
2. Evaluate the provided Context. If the context is HIGHLY relevant to the user's specific query (e.g. it contains the exact case name, act, or legal principle requested), you MUST use this structured format:
   (1) Introduction
   (2) Facts of the Case
   (3) Legal Issues
   (4) Applicable Laws
   (5) Step-by-Step Legal Analysis
   (6) Judicial Precedents
   (7) Conclusion/Judgment
3. IF THE CONTEXT IS IRRELEVANT (e.g. the user asks about "Satya v Teja Singh" but the context only contains "Balwan Singh"), DO NOT use the structured format above. Instead, write a standard paragraph explaining that the specific details are not in the database, and provide your general legal knowledge on the topic. Never write empty sections like "Facts: Context does not contain sufficient information".
4. CITE YOUR SOURCES explicitly using the Document Source metadata provided in the context (e.g. "As stated in DocumentName.pdf on Page 4...").
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history_context:
        messages.append({"role": "user", "content": f"Previous conversation:\n{chat_history_context}"})
        messages.append({"role": "assistant", "content": "I will maintain this context."})
        
    messages.append({
        "role": "user", 
        "content": f"Context:\n{context_text}\n\nQuestion: {user_message}\n\nProvide the structured legal analysis:"
    })
    
    try:
        client = get_groq_client()
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1
        )
        ai_response = chat_completion.choices[0].message.content
        
        return {
            "response": ai_response,
            "confidence_score": best_score,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error generating Groq response: {e}")
        return _generate_fallback_answer(user_message, chat_history_context, model_name, best_score)


def _generate_fallback_answer(user_message, chat_history_context, model_name, score):
    """
    Generates a general knowledge fallback answer, WITHOUT forcing a rigid format
    that causes hallucinated sections like "Facts of the Case".
    """
    logger.info("Executing graceful fallback logic.")
    system_prompt = """You are LegalAI, an expert legal assistant with deep knowledge of Indian law.
You must answer the query using your general legal knowledge base because specific documents were not found.

STRICT RULES:
1. Provide a professional, direct legal analysis based on established Indian Law, IPC, CrPC, etc.
2. DO NOT use rigid headers like "Facts of the Case" unless the user explicitly provided facts in their prompt.
3. If the user asks about a specific obscure case you do not know, DO NOT hallucinate facts. Gracefully state that you do not have the specific facts for that case, and provide the general legal principles that apply.
4. Do NOT mention "database", "context", "search failed", or "Qdrant".
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    if chat_history_context:
        messages.append({"role": "user", "content": f"Previous conversation:\n{chat_history_context}"})
        messages.append({"role": "assistant", "content": "I will maintain this context."})
        
    messages.append({
        "role": "user",
        "content": f"Question: {user_message}\n\nProvide your professional legal analysis:"
    })
    
    try:
        client = get_groq_client()
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1
        )
        ai_response = chat_completion.choices[0].message.content
        
        return {
            "response": ai_response,
            "confidence_score": score,
            "sources": []
        }
    except Exception as e:
        logger.error(f"Fallback answer generation failed: {e}")
        return {
            "response": "## Error\nI encountered an error while formulating the response.",
            "confidence_score": 0.0,
            "sources": []
        }


def _is_non_legal_query(message):
    msg = message.lower().strip()
    legal_keywords = [
        "law", "section", "ipc", "crpc", "bnss", "iea", "bsa", "bjs", "constitution", "court",
        "judge", "attorney", "advocate", "legal", "statute", "precedent", "fir", "police",
        "complaint", "bail", "criminal", "civil", "divorce", "contract", "agreement", "lease",
        "tenant", "copyright", "patent", "trademark", "tax", "income tax", "corporate", "company",
        "arbitration", "mediation", "tribunal", "writ", "petition", "appeal", "suit", "judgement",
        "verdict", "offence", "ipc section", "bhartiya", "nagrik", "sanhita", "bharatiya",
        "nyaya", "sakshya", "will", "probate", "deed", "power of attorney", "homicide", "theft",
        "fraud", "defamation", "tort", "damages", "injunction", "evidence", "witness"
    ]
    for keyword in legal_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, msg):
            return False
            
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you"]
    if any(msg == g for g in greetings):
        return False
        
    non_legal_topics = [
        "how to code", "write a python", "javascript", "movie", "song", "sports", "cricket",
        "football", "recipe", "cook", "science", "physics", "chemistry", "mathematics",
        "weather", "joke", "funny", "game", "gaming"
    ]
    if any(topic in msg for topic in non_legal_topics):
        return True
        
    return False
