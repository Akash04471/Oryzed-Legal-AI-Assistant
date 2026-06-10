import os
import re
import logging
from groq import Groq
from LegalAI.services.embedding_service import get_embedding
from LegalAI.services.qdrant_service import search_similar_chunks

logger = logging.getLogger(__name__)

# Minimum similarity score (cosine distance) to consider search results relevant
SIMILARITY_THRESHOLD = 0.55

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
            # Fall back to GROQ_API_KEY in other formats or raise error
            raise ValueError("GROQ_API_KEY environment variable is not configured in .env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def generate_answer(user_message, chat_history_context=None):
    """
    Coordinates semantic retrieval and answer generation using Groq LLM.
    Supports a fallback path if no relevant documents are found in Qdrant.
    
    Args:
        user_message (str): The current user query.
        chat_history_context (str): Formatted conversation history.
        
    Returns:
        dict: A dictionary containing 'response', 'confidence_score', and 'sources'.
    """
    # Use config from env if present, otherwise default
    model_name = os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL
    
    # 1. Generate Query Embedding (now powered by free Hugging Face model)
    try:
        query_vector = get_embedding(user_message)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        # If embedding fails, fallback directly to general knowledge
        return _generate_fallback_answer(user_message, chat_history_context, model_name, 0.0)

    # 2. Retrieve top chunks from Qdrant
    results = search_similar_chunks(query_vector, limit=5)
    
    # Determine best similarity score
    best_score = results[0]["score"] if results else 0.0
    confidence_percentage = min(100, max(0, int(best_score * 100)))
    
    # Check if query is non-legal.
    # Refusal check to keep LegalAI aligned with legal-only limits.
    if _is_non_legal_query(user_message):
        return {
            "response": (
                "I apologize, but I am a specialized Legal AI Assistant. "
                "I can only provide assistance with legal matters, legal research, case analysis, "
                "statutory interpretation, and legal consultation. Please ask me a legal question."
            ),
            "confidence_score": 1.0,
            "sources": []
        }

    # 3. Handle Fallback if below threshold
    if not results or best_score < SIMILARITY_THRESHOLD:
        logger.info(f"Top match similarity {best_score:.4f} is below threshold {SIMILARITY_THRESHOLD}. Using general knowledge fallback.")
        return _generate_fallback_answer(user_message, chat_history_context, model_name, best_score)
        
    # 4. Process high-confidence context RAG path
    logger.info(f"Top match similarity {best_score:.4f} exceeds threshold. Generating answer from retrieved context.")
    
    # Gather chunks and sources
    context_parts = []
    sources = []
    
    for hit in results:
        # Avoid duplicate source references
        source_ref = f"{hit['file_name']} (Page {hit['start_page']})"
        if hit["end_page"] != hit["start_page"]:
            source_ref = f"{hit['file_name']} (Pages {hit['start_page']}-{hit['end_page']})"
            
        context_parts.append(
            f"--- Document Source: {hit['file_name']} | Pages: {hit['start_page']}-{hit['end_page']} ---\n"
            f"Content: {hit['text']}\n"
        )
        
        # Add to structured source metadata list
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
Your task is to answer the user's legal question using the provided Context. If the Context does not contain enough detailed facts to answer the question completely, you MUST seamlessly supplement it with your own extensive legal knowledge to deliver a complete, professional, high-quality response.

STRICT RULES:
1. You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters. Any deviation is strictly prohibited.
2. Do NOT mention words like "Context", "provided documents", "database search", or reference any search mechanism in your output. Present your response directly and authority-first.
3. Every response MUST strictly follow this order:
   (1) Introduction
   (2) Facts of the Case (if applicable)
   (3) Legal Issues
   (4) Applicable Laws (Acts, Sections, Articles, Rules)
   (5) Step-by-Step Legal Analysis
   (6) Judicial Precedents with proper citations
   (7) Conclusion/Judgment
   (8) Legal Consultation including remedies, risks, and strategy.
4. CITE YOUR SOURCES. Cite legal provisions, acts, and landmark cases naturally (e.g. Section 302 of the IPC, or landmark cases). Do NOT include backend file names (such as '.pdf' or file path formats) in your response text. Cite the actual legal act, code, book name, or case title instead.
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Inject chat history if available
    if chat_history_context:
        messages.append({"role": "user", "content": f"Previous conversation for context:\n{chat_history_context}"})
        messages.append({"role": "assistant", "content": "Understood. I will maintain this context and answer the next question using only the retrieved documents."})
        
    messages.append({
        "role": "user", 
        "content": f"Context:\n{context_text}\n\nQuestion: {user_message}\n\nProvide the structured legal analysis:"
    })
    
    try:
        groq_client = get_groq_client()
        chat_completion = groq_client.chat.completions.create(
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
    Generates a structured answer using the model's general knowledge as an alternative fallback.
    """
    system_prompt = """You are LegalAI, an expert legal assistant with deep knowledge of Indian law.
Please answer the query to the best of your legal knowledge as a professional Legal AI Assistant.

STRICT RULES:
1. You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters. Any deviation is strictly prohibited.
2. Do NOT mention that "no relevant documents were found", "context is missing", "the database was checked", "the source is unavailable", or make any other references to backend search failures. Simply deliver a direct, comprehensive legal analysis.
3. Every response MUST strictly follow this order:
   (1) Introduction
   (2) Facts of the Case (if applicable)
   (3) Legal Issues
   (4) Applicable Laws (Acts, Sections, Articles, Rules)
   (5) Step-by-Step Legal Analysis
   (6) Judicial Precedents with proper citations
   (7) Conclusion/Judgment
   (8) Legal Consultation including remedies, risks, and strategy.
"""

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    if chat_history_context:
        messages.append({"role": "user", "content": f"Previous conversation for context:\n{chat_history_context}"})
        messages.append({"role": "assistant", "content": "Understood. I will answer the next query using my general legal knowledge base."})
        
    messages.append({
        "role": "user",
        "content": f"Question: {user_message}\n\nProvide the structured legal analysis:"
    })
    
    try:
        groq_client = get_groq_client()
        chat_completion = groq_client.chat.completions.create(
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
            "response": (
                "## Error\n"
                "I encountered an error while formulating the response. Please check your credentials or try again later."
            ),
            "confidence_score": 0.0,
            "sources": []
        }


def _is_non_legal_query(message):
    """
    Checks if a query is non-legal.
    Keeps the AI restricted to the legal domain.
    """
    msg = message.lower().strip()
    
    # List of keywords that are strictly legal
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
    
    # Check if any legal keyword is present (using word boundaries to avoid matching substrings like "writ" in "write")
    for keyword in legal_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, msg):
            return False
        
    # Check for general conversational queries
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you"]
    if any(msg == g for g in greetings):
        return False
        
    # If no legal keywords are found and it looks like technology, science, sports, etc., block it.
    non_legal_topics = [
        "how to code", "write a python", "javascript", "movie", "song", "sports", "cricket",
        "football", "recipe", "cook", "science", "physics", "chemistry", "mathematics",
        "weather", "joke", "funny", "game", "gaming"
    ]
    if any(topic in msg for topic in non_legal_topics):
        return True
        
    # Default to letting the LLM handle it, but perform a light heuristic check.
    return False
