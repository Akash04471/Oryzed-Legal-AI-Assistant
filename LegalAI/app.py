from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
from functools import wraps
# Web Scraping Imports
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any # For type hinting the tool's run method
from typing import Optional
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Database setup
DB_PATH = "legal_chat.db"


def _get_llm_api_key() -> str:
    """
    Resolve provider key in a backward-compatible way.

    Primary key is GROQ_API_KEY. If missing, OPENAI_API_KEY is accepted as
    fallback because some environments only define a generic provider key.
    """
    return (os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()


def _looks_like_auth_error(raw_error: str) -> bool:
    normalized = (raw_error or "").lower()
    patterns = [
        "invalid api key",
        "invalid_api_key",
        "authentication",
        "unauthorized",
        "incorrect api key",
        "api key",
    ]
    return any(p in normalized for p in patterns)


def _fallback_legal_response(user_message: str) -> str:
    """
    Safe fallback response when model provider is unavailable.
    Keeps legal UX functional even when external LLM auth/config fails.
    """
    msg = (user_message or "").lower()

    if "fir" in msg or "first information report" in msg:
        return """## Facts & Context
You are asking about the process to file an FIR in India.

## Legal Issues Identified
1. Where and how an FIR can be registered.
2. What to do if police refuse to register an FIR.

## Legal Analysis
An FIR is the first formal information recorded by police regarding a cognizable offence.
You may file it at the police station having jurisdiction, and zero FIR can also be filed at any police station in urgent matters.

## Applicable Laws & Sections
Section 173 Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) (earlier Section 154 CrPC):
Police shall record information relating to cognizable offences.

## Relevant Case Law
Lalita Kumari v. Government of Uttar Pradesh (2013) 14 SCC 1:
Registration of FIR is mandatory when information discloses a cognizable offence.

## Conclusion
Practical steps:
1. Go to police station and provide complaint with facts, date, place, accused details if known, and evidence.
2. Ask for FIR number and free copy after registration.
3. If refused, send complaint to Superintendent of Police (SP).
4. If still not registered, approach Magistrate under applicable BNSS/CrPC remedy.
"""

    return """## Facts & Context
Your legal query was received, but the AI provider is temporarily unavailable.

## Legal Issues Identified
The backend could not access the legal reasoning model due to configuration/authentication failure.

## Legal Analysis
The application has stored your question and can continue session history, but advanced AI legal synthesis is currently limited.

## Applicable Laws & Sections
N/A until the external model connection is restored.

## Relevant Case Law
N/A in fallback mode.

## Conclusion
Please retry after fixing server API credentials. If you share your legal question, I can still provide a basic procedural response.
"""

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    # Backward-compatible migration for existing databases.
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in cursor.fetchall()]
    if "email" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    cursor.execute("PRAGMA table_info(chat_sessions)")
    session_columns = [column[1] for column in cursor.fetchall()]
    if "user_id" not in session_columns:
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN user_id INTEGER")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)")

    conn.commit()
    conn.close()


def get_user_by_username(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    return {"id": user[0], "username": user[1], "email": user[2], "password_hash": user[3]}


def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    return {"id": user[0], "username": user[1], "email": user[2], "password_hash": user[3]}


def create_user(username: str, email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def api_login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped


def ensure_session_exists(session_id: str, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def create_new_session(user_id: int):
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_sessions (id, title, user_id)
        VALUES (?, ?, ?)
    """, (session_id, "New Legal Research", user_id))

    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (user_id,))

    sessions = cursor.fetchall()
    conn.close()

    return [{"id": s[0], "title": s[1], "created_at": s[2], "updated_at": s[3]} for s in sessions]

def get_chat_history(session_id: str, user_id: int):
    if not ensure_session_exists(session_id, user_id):
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.role, m.content, m.timestamp
        FROM chat_messages m
        INNER JOIN chat_sessions s ON s.id = m.session_id
        WHERE m.session_id = ? AND s.user_id = ?
        ORDER BY timestamp ASC
    """, (session_id, user_id))

    messages = cursor.fetchall()
    conn.close()

    return [{"id": m[0], "role": m[1], "content": m[2], "timestamp": m[3]} for m in messages]

def save_message(session_id: str, role: str, content: str, user_id: int):
    if not ensure_session_exists(session_id, user_id):
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))

    cursor.execute("""
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (session_id, user_id))

    conn.commit()
    conn.close()
    return True

def update_session_title(session_id: str, title: str, user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    display_title = title[:50] + "..." if len(title) > 50 else title
    
    cursor.execute("""
        UPDATE chat_sessions
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (display_title, session_id, user_id))

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
"🚨 CRITICAL: You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters. Any deviation is strictly prohibited.",

"❌ STRICTLY REFUSE: If asked about anything non-legal (technology, entertainment, sports, personal advice, science, etc.), respond EXACTLY: 'I apologize, but I am a specialized Legal AI Assistant. I can only provide assistance with legal matters, legal research, case analysis, statutory interpretation, and legal consultation. Please ask me a legal question.'",

"✅ LEGAL DOMAIN LIMITATION: You may ONLY answer queries related to Constitutional Law, Criminal Law, Civil Law, Contract Law, Corporate Law, Family Law, Property Law, Administrative Law, Tax Law, Labour Law, Intellectual Property Law, International Law, Procedural Law, Legal Drafting, Case Analysis, Statutory Interpretation, and Legal Consultation.",

"📋 MANDATORY RESPONSE STRUCTURE: Every response MUST strictly follow this order: (1) Introduction, (2) Facts of the Case (if applicable), (3) Legal Issues, (4) Applicable Laws (Acts, Sections, Articles, Rules), (5) Step-by-Step Legal Analysis, (6) Judicial Precedents with proper citations, (7) Conclusion/Judgment, (8) Legal Consultation including remedies, risks, and strategy.",

"⚖️ CASE LAW FORMAT (COMPULSORY): Whenever discussing a case, include: Facts, Legal Issues, Applicable Law (with Sections/Articles), Arguments (if relevant), Judgment, Court’s Reasoning, and Final Holding.",

"🔍 RESEARCH: Use reliable and authoritative legal sources such as Indian Kanoon, SCC Online, Manupatra, Bar & Bench, LiveLaw, Law Bhoomi, CaseMine, Drishti Judiciary, and Law Commission Reports. Ensure all answers are legally accurate and updated.",

"📚 LEGAL AUTHORITY: Always support answers with statutory provisions, case laws with citations, and where relevant, include Law Commission Reports, official gazettes, or recognized legal commentaries.",

"⚖️ LEGAL ANALYSIS: Apply law to facts in a logical, step-by-step manner. Address multiple interpretations where relevant and provide reasoned legal arguments, not just conclusions.",

"💼 PROFESSIONAL LANGUAGE: Use formal, precise, and professional legal language while ensuring clarity and readability. Avoid unnecessary jargon but maintain legal depth.",

"⚖️ ACCURACY & COMPLETENESS: Ensure responses are comprehensive yet concise, legally sound, and free from unsupported claims or assumptions.",

"🔒 ETHICS: Maintain neutrality, objectivity, and legal integrity. Do not provide misleading, speculative, or biased legal advice.",

"🧠 MEMORY & CONTEXT: Maintain continuity across the conversation. Use prior user inputs to refine answers and avoid contradictions.",

"🔄 CONTINUITY: Ensure coherence in ongoing discussions. Do not repeat information unless necessary or requested.",

"❓ FOLLOW-UP MECHANISM: Ask relevant follow-up questions where facts are incomplete, jurisdiction is unclear, or better legal precision is required.",

"⚖️ LEGAL CONSULTATION MODE: Always include practical legal advice such as available remedies, procedural steps, risks, benefits, and likely outcomes.",

"🚫 NO GENERAL ANSWERS: Do not provide vague or generic responses. Every answer must be structured, specific, and legally reasoned.",

"⚖️ STRATEGIC INSIGHT: Where applicable, suggest legal strategy, procedural approach, and alternative remedies available to the user.",

"📈 ADVANCED ANALYSIS (OPTIONAL): Where relevant, include comparative legal position, doctrinal interpretation, or criticism of judicial precedents to enhance depth.",

"⚖️ LEGAL ONLY ENFORCEMENT: Under no circumstances should you answer non-legal queries. Your role is strictly limited to legal consultation and analysis."""




LLM_READY = False
LLM_INIT_ERROR = ""
legal_agent: Optional[Agent] = None


def init_legal_agent() -> None:
    global legal_agent, LLM_READY, LLM_INIT_ERROR

    api_key = _get_llm_api_key()
    if not api_key:
        LLM_READY = False
        LLM_INIT_ERROR = "Missing GROQ_API_KEY (or OPENAI_API_KEY fallback)."
        legal_agent = None
        app.logger.warning("LLM disabled: %s", LLM_INIT_ERROR)
        return

    # Normalize to GROQ_API_KEY so agno/groq model reads expected env var.
    os.environ["GROQ_API_KEY"] = api_key

    try:
        legal_agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile", temperature=0.1),
            description=LEGAL_SYSTEM_PROMPT,
            instructions=[
                "🚨 CRITICAL: You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters. Any deviation is strictly prohibited.",
                "❌ STRICTLY REFUSE: If asked about anything non-legal (technology, entertainment, sports, personal advice, science, etc.), respond EXACTLY: 'I apologize, but I am a specialized Legal AI Assistant. I can only provide assistance with legal matters, legal research, case analysis, statutory interpretation, and legal consultation. Please ask me a legal question.'",
                "✅ LEGAL DOMAIN LIMITATION: You may ONLY answer queries related to Constitutional Law, Criminal Law, Civil Law, Contract Law, Corporate Law, Family Law, Property Law, Administrative Law, Tax Law, Labour Law, Intellectual Property Law, International Law, Procedural Law, Legal Drafting, Case Analysis, Statutory Interpretation, and Legal Consultation.",
                "📋 MANDATORY RESPONSE STRUCTURE: Every response MUST strictly follow this order: (1) Introduction, (2) Facts of the Case (if applicable), (3) Legal Issues, (4) Applicable Laws (Acts, Sections, Articles, Rules), (5) Step-by-Step Legal Analysis, (6) Judicial Precedents with proper citations, (7) Conclusion/Judgment, (8) Legal Consultation including remedies, risks, and strategy.",
                "⚖️ CASE LAW FORMAT (COMPULSORY): Whenever discussing a case, include: Facts, Legal Issues, Applicable Law (with Sections/Articles), Arguments (if relevant), Judgment, Court’s Reasoning, and Final Holding.",
                "🔍 RESEARCH: Use reliable and authoritative legal sources such as Indian Kanoon, SCC Online, Manupatra, Bar & Bench, LiveLaw, Law Bhoomi, CaseMine, Drishti Judiciary, and Law Commission Reports. Ensure all answers are legally accurate and updated.",
                "📚 LEGAL AUTHORITY: Always support answers with statutory provisions, case laws with citations, and where relevant, include Law Commission Reports, official gazettes, or recognized legal commentaries.",
                "⚖️ LEGAL ANALYSIS: Apply law to facts in a logical, step-by-step manner. Address multiple interpretations where relevant and provide reasoned legal arguments, not just conclusions.",
                "💼 PROFESSIONAL LANGUAGE: Use formal, precise, and professional legal language while ensuring clarity and readability. Avoid unnecessary jargon but maintain legal depth.",
                "⚖️ ACCURACY & COMPLETENESS: Ensure responses are comprehensive yet concise, legally sound, and free from unsupported claims or assumptions.",
                "🔒 ETHICS: Maintain neutrality, objectivity, and legal integrity. Do not provide misleading, speculative, or biased legal advice.",
                "🧠 MEMORY & CONTEXT: Maintain continuity across the conversation. Use prior user inputs to refine answers and avoid contradictions.",
                "🔄 CONTINUITY: Ensure coherence in ongoing discussions. Do not repeat information unless necessary or requested.",
                "❓ FOLLOW-UP MECHANISM: Ask relevant follow-up questions where facts are incomplete, jurisdiction is unclear, or better legal precision is required.",
                "⚖️ LEGAL CONSULTATION MODE: Always include practical legal advice such as available remedies, procedural steps, risks, benefits, and likely outcomes.",
                "🚫 NO GENERAL ANSWERS: Do not provide vague or generic responses. Every answer must be structured, specific, and legally reasoned.",
                "⚖️ STRATEGIC INSIGHT: Where applicable, suggest legal strategy, procedural approach, and alternative remedies available to the user.",
                "📈 ADVANCED ANALYSIS (OPTIONAL): Where relevant, include comparative legal position, doctrinal interpretation, or criticism of judicial precedents to enhance depth.",
                "⚖️ LEGAL ONLY ENFORCEMENT: Under no circumstances should you answer non-legal queries. Your role is strictly limited to legal consultation and analysis."
         ],
            tools=[DuckDuckGoTools(), LawbhoomiScraperTool()],
            markdown=True,
        )
        LLM_READY = True
        LLM_INIT_ERROR = ""
    except Exception as e:
        LLM_READY = False
        LLM_INIT_ERROR = str(e)
        legal_agent = None
        app.logger.exception("Failed to initialize legal agent")

# Fix 2 — context window increased to 10 messages, proper format
def get_chat_context(session_id: str, user_id: int, limit=10):
    """Return last `limit` messages as a formatted string for injection into the prompt."""
    messages = get_chat_history(session_id, user_id) or []
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
@login_required
def index():
    return render_template('legal_chat.html', username=session.get("username", ""))


@app.route("/terms")
def terms_and_conditions():
    return render_template("terms.html", username=session.get("username", ""))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    error = ""
    notice = ""
    if request.args.get("signup") == "success":
        notice = "Account created successfully. Please login to continue."

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Email and password are required."
        else:
            user = get_user_by_email(email)
            if not user or not check_password_hash(user["password_hash"], password):
                error = "Invalid email or password."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("index"))

    return render_template("login.html", error=error, notice=notice)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        session.clear()

    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password or not confirm_password:
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters long."
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif get_user_by_username(username):
            error = "Username already exists."
        elif get_user_by_email(email):
            error = "Email is already registered."
        else:
            create_user(username, email, password)
            session.clear()
            return redirect(url_for("login", signup="success"))

    return render_template("signup.html", error=error)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# Fix 5 — Health endpoint (needed by loading screen)
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model": "llama-3.3-70b-versatile",
        "llm_ready": LLM_READY,
        "llm_error": LLM_INIT_ERROR if not LLM_READY else "",
    })

@app.route("/api/new_session", methods=["POST"])
@api_login_required
def new_session():
    session_id = create_new_session(session["user_id"])
    return jsonify({"session_id": session_id, "status": "success"})

@app.route("/api/sessions", methods=["GET"])
@api_login_required
def get_sessions_route():
    return jsonify({"sessions": get_chat_sessions(session["user_id"])})

@app.route("/api/chat/<session_id>", methods=["GET"])
@api_login_required
def get_chat(session_id):
    history = get_chat_history(session_id, session["user_id"])
    if history is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"history": history})

@app.route("/api/chat/<session_id>/message", methods=["POST"])
@api_login_required
def send_message(session_id):
    try:
        user_id = session["user_id"]
        if not ensure_session_exists(session_id, user_id):
            return jsonify({"error": "Session not found"}), 404

        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        chat_history = get_chat_history(session_id, user_id) or []

        if len(chat_history) == 0:
            update_session_title(session_id, user_message, user_id)

        save_message(session_id, "user", user_message, user_id)

        # Fix 2 — inject formatted conversation context (last 10 msgs)
        history_text = get_chat_context(session_id, user_id)
        if history_text:
            full_prompt = f"""Previous conversation:\n{history_text}\n\nCurrent question: {user_message}\n\nProvide a complete legal analysis following the structured 6-section format."""
        else:
            full_prompt = f"{user_message}\n\nProvide a complete legal analysis following the structured 6-section format."

        # Fix 3 — use the singleton agent
        # Fix 4 — proper error handling
        if not LLM_READY or legal_agent is None:
            ai_response = _fallback_legal_response(user_message)
        else:
            try:
                response = legal_agent.run(full_prompt)
                ai_response = response.content if hasattr(response, 'content') else str(response)

                # Some provider SDK errors are returned as plain content strings.
                # Guard against leaking raw provider payloads to the user.
                if _looks_like_auth_error(ai_response):
                    app.logger.error("Provider auth/config error in model response: %s", ai_response)
                    ai_response = _fallback_legal_response(user_message)
            except Exception as agent_err:
                app.logger.error(f"Agent error in send_message: {agent_err}")
                ai_response = _fallback_legal_response(user_message)

        save_message(session_id, "assistant", ai_response, user_id)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        app.logger.error(f"Error in send_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/delete_session/<session_id>", methods=["DELETE"])
@api_login_required
def delete_session(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        user_id = session["user_id"]

        cursor.execute(
            """
            DELETE FROM chat_messages
            WHERE session_id IN (
                SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?
            )
            """,
            (session_id, user_id),
        )
        cursor.execute('DELETE FROM chat_sessions WHERE id = ? AND user_id = ?', (session_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Session not found"}), 404

        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print("Error deleting session:", e)
        return jsonify({"error": "Failed to delete session"}), 500

@app.route("/api/chat/<session_id>/edit/<int:message_id>", methods=["PUT"])
@api_login_required
def edit_message(session_id, message_id):
    try:
        user_id = session["user_id"]
        if not ensure_session_exists(session_id, user_id):
            return jsonify({"error": "Session not found"}), 404

        data = request.get_json()
        new_message = data.get("message", "").strip()

        if not new_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT m.role
            FROM chat_messages m
            INNER JOIN chat_sessions s ON s.id = m.session_id
            WHERE m.id = ? AND m.session_id = ? AND s.user_id = ?
            """,
            (message_id, session_id, user_id)
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
            WHERE id = ? AND user_id = ?
        """, (session_id, user_id))

        conn.commit()
        conn.close()

        # Fix 2 + 3 + 4 in edit_message route as well
        history_text = get_chat_context(session_id, user_id)
        if history_text:
            full_prompt = f"""Previous conversation:\n{history_text}\n\nCurrent question: {new_message}\n\nProvide a complete legal analysis following the structured 6-section format."""
        else:
            full_prompt = f"{new_message}\n\nProvide a complete legal analysis following the structured 6-section format."

        if not LLM_READY or legal_agent is None:
            ai_response = _fallback_legal_response(new_message)
        else:
            try:
                response = legal_agent.run(full_prompt)
                ai_response = response.content if hasattr(response, 'content') else str(response)
                if _looks_like_auth_error(ai_response):
                    app.logger.error("Provider auth/config error in model response: %s", ai_response)
                    ai_response = _fallback_legal_response(new_message)
            except Exception as agent_err:
                app.logger.error(f"Agent error in edit_message: {agent_err}")
                ai_response = _fallback_legal_response(new_message)

        save_message(session_id, "assistant", ai_response, user_id)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        app.logger.error(f"Error in edit_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------------------------------------------
#                  RUN APP
# ------------------------------------------------------

init_db()
init_legal_agent()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)