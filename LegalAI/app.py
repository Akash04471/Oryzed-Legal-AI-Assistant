from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
# Agno imports
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.groq import Groq
# Python standard libraries
import os
import sqlite3
import uuid
from datetime import datetime
import json
# Web Scraping Imports
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any # For type hinting the tool's run method

# Load environment variables
load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set. Please set it in the environment or in a .env file.")

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

print("GROQ_API_KEY =", os.environ.get("GROQ_API_KEY"))
# Database setup
DB_PATH = "legal_chat.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    """)

    conn.commit()
    conn.close()

def create_new_session():
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_sessions (id, title)
        VALUES (?, ?)
    """, (session_id, "New Legal Consultation"))

    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        ORDER BY updated_at DESC
    """)

    sessions = cursor.fetchall()
    conn.close()

    return [{"id": s[0], "title": s[1], "created_at": s[2], "updated_at": s[3]} for s in sessions]

def get_chat_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))

    messages = cursor.fetchall()
    conn.close()

    return [{"id": m[0], "role": m[1], "content": m[2], "timestamp": m[3]} for m in messages]

def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))

    cursor.execute("""
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session_id,))

    conn.commit()
    conn.close()

def update_session_title(session_id, title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    display_title = title[:50] + "..." if len(title) > 50 else title
    
    cursor.execute("""
        UPDATE chat_sessions
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (display_title, session_id))

    conn.commit()
    conn.close()

# ------------------------------------------------------
#             CUSTOM LAW BHOOMI SCRAPER TOOL CLASS
# ------------------------------------------------------

class LawbhoomiScraperTool:
    """
    Tool to fetch and extract all law notes content from the fixed LawBhoomi URL.
    Use this tool for comprehensive, pre-indexed legal research on topics found in notes.
    """
    def __init__(self):
        self.name = "LawbhoomiScraperTool"
        # The description tells the Agent what data this tool provides
        self.description = "A specialized tool that scrapes the text content from the LawBhoomi Law Notes URL: https://lawbhoomi.com/law-notes/. Use it to find detailed legal concepts, notes, and topic summaries. It takes NO arguments."
        self.fixed_url = "https://lawbhoomi.com/law-notes/"

    def run(self) -> str:
        """
        Scrapes the content from the fixed LawBhoomi URL and returns the main text.
        
        Args:
            No arguments needed.

        Returns:
            str: The extracted text content or an error message.
        """
        url = self.fixed_url
        try:
            # 1. Fetch the content
            headers = {
                'User-Agent': 'LegalAI-LawBhoomi-Scraper/1.0 (Python; Flask; Agno Agent)'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # 2. Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 3. Extract the main body text
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract() 

            # Attempt to find the main content block for better accuracy
            main_content = soup.find('div', class_='content-area') 
            if main_content:
                text_content = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to the entire body text
                text_content = soup.body.get_text(separator=' ', strip=True)

            clean_text = ' '.join(text_content.split()) 

            if len(clean_text) < 50:
                 return f"Successfully accessed URL {url}, but extracted very little content. Extracted snippet: {clean_text[:50]}..."

            return f"--- START OF LAW BHOOMI NOTES CONTENT ---\n\n{clean_text}\n\n--- END OF LAW BHOOMI NOTES CONTENT ---"

        except requests.exceptions.RequestException as e:
            return f"Error: Could not access LawBhoomi URL {url}. Details: {e}"
        except Exception as e:
            return f"Error: Failed to process content from URL {url}. Details: {e}"

# ------------------------------------------------------
#              LEGAL AI AGENT  (FIX 1-3)
# ------------------------------------------------------

# Fix 1 — Structured system prompt with Indian law focus
LEGAL_SYSTEM_PROMPT = """You are LegalAI, an expert legal assistant with deep knowledge of Indian law,
constitutional law, criminal law, civil law, corporate law, and international law.

STRICT RULES:
1. ONLY answer legal questions. If asked anything non-legal, respond:
   "I'm specialized in legal matters only. Please ask a legal question."
2. ALWAYS structure responses in this EXACT format:
   ## 📋 Facts & Context
   ## ⚖️ Legal Issues Identified
   ## 🔍 Legal Analysis
   ## 📜 Applicable Laws & Sections
   ## 🏛️ Relevant Case Law
   ## ✅ Conclusion
3. Always cite specific sections (e.g., "Section 302 IPC"), article numbers,
   and case names with years.
4. If using web search results, synthesize them — do not paste them verbatim.
5. Be precise, professional, and cite authoritative sources.
6. For Indian law queries, prioritize IPC, CrPC, CPC, Constitution of India,
   and Supreme Court judgments.
7. Use the LawbhoomiScraperTool for detailed legal concept notes.
8. Use DuckDuckGoTools for current case law and recent judgments."""

# Fix 3 — Initialize agent ONCE at startup, not per request
legal_agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile", temperature=0.1),
    description=LEGAL_SYSTEM_PROMPT,
    instructions=[
        "Always follow the 6-section structured format.",
        "Only answer legal questions — refuse all non-legal queries.",
        "Cite specific Acts, Sections, and case law with years.",
        "Use LawbhoomiScraperTool for detailed legal notes.",
        "Use DuckDuckGoTools for current judgments and recent precedents.",
    ],
    tools=[DuckDuckGoTools(), LawbhoomiScraperTool()],
    markdown=True,
)

# Fix 2 — context window increased to 10 messages, proper format
def get_chat_context(session_id, limit=10):
    """Return last `limit` messages as a formatted string for injection into the prompt."""
    messages = get_chat_history(session_id)
    history  = messages[-limit:]
    if not history:
        return ""
    lines = []
    for m in history[:-1]:   # Exclude the message currently being processed
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)

# ------------------------------------------------------
#                  ROUTES
# ------------------------------------------------------

@app.route("/")
def index():
    return render_template('legal_chat.html')

# Fix 5 — Health endpoint (needed by loading screen)
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model": "llama-3.3-70b-versatile"})

@app.route("/api/new_session", methods=["POST"])
def new_session():
    session_id = create_new_session()
    return jsonify({"session_id": session_id, "status": "success"})

@app.route("/api/sessions", methods=["GET"])
def get_sessions_route():
    return jsonify({"sessions": get_chat_sessions()})

@app.route("/api/chat/<session_id>", methods=["GET"])
def get_chat(session_id):
    return jsonify({"history": get_chat_history(session_id)})

@app.route("/api/chat/<session_id>/message", methods=["POST"])
def send_message(session_id):
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        chat_history = get_chat_history(session_id)

        if len(chat_history) == 0:
            update_session_title(session_id, user_message)

        save_message(session_id, "user", user_message)

        # Fix 2 — inject formatted conversation context (last 10 msgs)
        history_text = get_chat_context(session_id)
        if history_text:
            full_prompt = f"""Previous conversation:\n{history_text}\n\nCurrent question: {user_message}\n\nProvide a complete legal analysis following the structured 6-section format."""
        else:
            full_prompt = f"{user_message}\n\nProvide a complete legal analysis following the structured 6-section format."

        # Fix 3 — use the singleton agent
        # Fix 4 — proper error handling
        try:
            response = legal_agent.run(full_prompt)
            ai_response = response.content if hasattr(response, 'content') else str(response)
        except Exception as agent_err:
            app.logger.error(f"Agent error in send_message: {agent_err}")
            ai_response = "I encountered an error processing your legal query. Please rephrase and try again."

        save_message(session_id, "assistant", ai_response)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        app.logger.error(f"Error in send_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/delete_session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print("Error deleting session:", e)
        return jsonify({"error": "Failed to delete session"}), 500

@app.route("/api/chat/<session_id>/edit/<int:message_id>", methods=["PUT"])
def edit_message(session_id, message_id):
    try:
        data = request.get_json()
        new_message = data.get("message", "").strip()

        if not new_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM chat_messages WHERE id = ? AND session_id = ?",
            (message_id, session_id)
        )

        result = cursor.fetchone()
        if not result or result[0] != 'user':
            conn.close()
            return jsonify({"error": "Message not found or cannot edit assistant messages"}), 404

        cursor.execute("""
            UPDATE chat_messages
            SET content = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ? AND session_id = ?
        """, (new_message, message_id, session_id))

        cursor.execute("""
            DELETE FROM chat_messages
            WHERE session_id = ? AND id > ?
        """, (session_id, message_id))

        cursor.execute("""
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_id,))

        conn.commit()
        conn.close()

        # Fix 2 + 3 + 4 in edit_message route as well
        history_text = get_chat_context(session_id)
        if history_text:
            full_prompt = f"""Previous conversation:\n{history_text}\n\nCurrent question: {new_message}\n\nProvide a complete legal analysis following the structured 6-section format."""
        else:
            full_prompt = f"{new_message}\n\nProvide a complete legal analysis following the structured 6-section format."

        try:
            response = legal_agent.run(full_prompt)
            ai_response = response.content if hasattr(response, 'content') else str(response)
        except Exception as agent_err:
            app.logger.error(f"Agent error in edit_message: {agent_err}")
            ai_response = "I encountered an error processing your legal query. Please rephrase and try again."

        save_message(session_id, "assistant", ai_response)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        app.logger.error(f"Error in edit_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------------------------------------------
#                  RUN APP
# ------------------------------------------------------

if __name__ == "__main__":
    init_db() 
    app.run(host="0.0.0.0", port=8080, debug=True)