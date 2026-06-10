import sys
import os
import warnings

# Silence pydantic protected namespace warnings from external libraries like Agno
warnings.filterwarnings("ignore", category=UserWarning, message=".*protected namespace.*")

# Ensure the parent directory is in sys.path so absolute imports of 'LegalAI' succeed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

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
import random
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl
import base64
from io import BytesIO
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None
try:
    from PIL import Image
except ImportError:
    Image = None
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Database setup
import tempfile
try:
    import psycopg2
    from psycopg2 import extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On Vercel, the filesystem is read-only except /tmp.
if os.environ.get("VERCEL"):
    DB_PATH = os.path.join(tempfile.gettempdir(), "legal_chat.db")
else:
    DB_PATH = os.path.join(BASE_DIR, "legal_chat.db")

# Detect DB type
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = HAS_POSTGRES and DATABASE_URL is not None

def get_db_connection():
    """
    Returns a database connection.
    Uses Postgres if DATABASE_URL is set, otherwise uses local SQLite.
    """
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    
    return sqlite3.connect(DB_PATH)

def adapt_sql(sql: str) -> str:
    """Adapts SQLite syntax to Postgres if needed."""
    if IS_POSTGRES:
        # Replace ? with %s for Postgres placeholders
        sql = sql.replace("?", "%s")
        # Handle SQLite AUTOINCREMENT -> Postgres SERIAL
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        # Handle SQLite CURRENT_TIMESTAMP -> Postgres NOW() or keep it if Postgres supports it
        # Actually Postgres supports CURRENT_TIMESTAMP
    return sql


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


def extract_file_content(file) -> str:
    """Extracts text from uploaded file based on its extension/mimetype."""
    if not file:
        return ""
    
    filename = secure_filename(file.filename).lower()
    
    try:
        if filename.endswith('.txt'):
            return file.read().decode('utf-8', errors='replace')
            
        elif filename.endswith('.pdf') and PyPDF2:
            pdf_reader = PyPDF2.PdfReader(file)
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)[:15000] # safety limit
            
        elif (filename.endswith('.doc') or filename.endswith('.docx')) and docx:
            doc = docx.Document(file)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])[:15000] # safety limit
            
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            # Using Groq vision model to extract text from image
            image_data = file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            groq_key = _get_llm_api_key()
            if not groq_key:
                return "[Error: Vision API key not found for image analysis]"
                
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            ext = filename.split('.')[-1]
            if ext == "jpg": ext = "jpeg"
            mime_type = f"image/{ext}"
            
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image and briefly describe its legal context or contents."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=1024
            )
            return f"[Image Description/Extracted Text]: {response.choices[0].message.content}"
    except Exception as e:
        app.logger.error(f"Error extracting file content: {e}")
        return f"[Error extracting file content: {str(e)}]"
        
    return "[Unsupported file format or required library missing]"


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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        app.logger.info(f"Initializing database at: {DB_PATH}")

        cursor.execute(adapt_sql("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        cursor.execute(adapt_sql("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        cursor.execute(adapt_sql("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
            )
        """))

        # Backward-compatible migration for existing databases.
        if not IS_POSTGRES:
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
        else:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            user_columns = [column[0] for column in cursor.fetchall()]
        
        if "email" not in user_columns:
            cursor.execute(adapt_sql("ALTER TABLE users ADD COLUMN email TEXT"))

        cursor.execute(adapt_sql("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"))

        if not IS_POSTGRES:
            cursor.execute("PRAGMA table_info(chat_sessions)")
            session_columns = [column[1] for column in cursor.fetchall()]
        else:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_sessions'")
            session_columns = [column[0] for column in cursor.fetchall()]
            
        if "user_id" not in session_columns:
            cursor.execute(adapt_sql("ALTER TABLE chat_sessions ADD COLUMN user_id INTEGER"))

        cursor.execute(adapt_sql("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)"))
        cursor.execute(adapt_sql("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"))

        cursor.execute(adapt_sql("""
            CREATE TABLE IF NOT EXISTS otp_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                otp TEXT NOT NULL,
                expiry_time TIMESTAMP NOT NULL,
                purpose TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        cursor.execute(adapt_sql("CREATE INDEX IF NOT EXISTS idx_otp_store_email ON otp_store(email)"))

        cursor.execute(adapt_sql("""
            CREATE TABLE IF NOT EXISTS synced_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_file_id TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        cursor.execute(adapt_sql("CREATE INDEX IF NOT EXISTS idx_synced_files_drive_id ON synced_files(drive_file_id)"))

        conn.commit()
        conn.close()
        app.logger.info("Database initialization successful.")
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        # On serverless environments, we log the error but don't always crash the whole process
        # unless it's a critical fatal error.
        if os.environ.get("VERCEL"):
            app.logger.warning("Continuing app startup despite database initialization warning.")
        else:
            raise e


def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(adapt_sql("SELECT id, username, email, password_hash FROM users WHERE username = ?"), (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    return {"id": user[0], "username": user[1], "email": user[2], "password_hash": user[3]}


def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(adapt_sql("SELECT id, username, email, password_hash FROM users WHERE email = ?"), (email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    return {"id": user[0], "username": user[1], "email": user[2], "password_hash": user[3]}


def create_user(username: str, email: str, password: str):
    """Creates a new user in the database. Compatible with both SQLite and Postgres."""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute(
            adapt_sql("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"),
            (username, email, password_hash),
        )
        conn.commit()
        
        # Safe ID retrieval for multiple database types
        user_id = None
        try:
            if not IS_POSTGRES:
                user_id = cursor.lastrowid
            else:
                # If we really needed the ID in Postgres, we would use RETURNING
                # But for signup, the username/email is the unique identifier for immediate next steps
                pass
        except:
            pass
            
        return user_id
    except Exception as e:
        app.logger.error(f"Error creating user {username}: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


# ------------------------------------------------------
#                  OTP HELPER FUNCTIONS
# ------------------------------------------------------

def generate_otp():
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email, otp):
    """Sends OTP via email using SMTP."""
    sender_email = os.environ.get("MAIL_USER")
    password = os.environ.get("MAIL_PASS")
    smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("MAIL_PORT", 465))

    if not sender_email or not password:
        app.logger.error("Email credentials not configured in .env")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Your Oryzed Verification Code: {otp}"
    message["From"] = f"Oryzed <{sender_email}>"
    message["To"] = receiver_email
    
    # Anti-Spam transactional headers
    message["Auto-Submitted"] = "auto-generated"
    message["Precedence"] = "bulk"
    message["X-Auto-Response-Suppress"] = "All"

    text = f"Your Oryzed Verification Code is: {otp}\nThis code is valid for 5 minutes."
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            .body-wrap {{
                background-color: #f6f9fc;
                padding: 30px 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: #333333;
            }}
            .card {{
                max-width: 480px;
                margin: 0 auto;
                background-color: #ffffff;
                border: 1px solid #e6ebf1;
                border-radius: 8px;
                padding: 32px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }}
            .logo-text {{
                font-size: 20px;
                font-weight: 700;
                color: #0c2340;
                margin-bottom: 24px;
                letter-spacing: 0.5px;
            }}
            .title {{
                font-size: 20px;
                font-weight: 600;
                color: #0c2340;
                margin-bottom: 16px;
            }}
            .subtitle {{
                font-size: 14px;
                line-height: 1.5;
                color: #525f7f;
                margin-bottom: 24px;
            }}
            .otp-container {{
                background-color: #f6f9fc;
                border: 1px solid #e6ebf1;
                border-radius: 6px;
                padding: 16px;
                margin: 20px 0;
                text-align: center;
            }}
            .otp-code {{
                font-size: 32px;
                font-weight: 700;
                letter-spacing: 6px;
                color: #1a6eb5;
                margin: 0;
            }}
            .expiry {{
                font-size: 12px;
                color: #8898aa;
                margin-top: 20px;
                text-align: center;
            }}
            .footer {{
                margin-top: 32px;
                border-top: 1px solid #e6ebf1;
                padding-top: 16px;
                font-size: 11px;
                color: #8898aa;
                text-align: center;
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0;">
        <div class="body-wrap">
            <div class="card">
                <div class="logo-text">Oryzed Legal AI</div>
                <div class="title">Verification Code</div>
                <div class="subtitle">
                    Please use the verification code below to access your research workspace. This code is valid for 5 minutes.
                </div>
                <div class="otp-container">
                    <h1 class="otp-code">{otp}</h1>
                </div>
                <div class="expiry">
                    If you did not request this code, you can safely ignore this email.
                </div>
                <div class="footer">
                    Oryzed Legal AI Assistant &bull; Transactional Verification Code
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
        # FALLBACK: Log to console so developer can see the OTP if email fails
        print(f"\n[DEVELOPMENT OTP FALLBACK] TO: {receiver_email} | CODE: {otp}\n")
        return False

def save_otp(email, otp, purpose):
    """Saves OTP to database with 5 minute expiry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Invalidate previous unused OTPs for this email and purpose
    cursor.execute(adapt_sql("UPDATE otp_store SET is_used = 1 WHERE email = ? AND purpose = ? AND is_used = 0"), (email, purpose))
    
    expiry_time = datetime.now()
    # Add 5 minutes to expiry
    from datetime import timedelta
    expiry_at = datetime.now() + timedelta(minutes=5)
    
    cursor.execute(
        adapt_sql("INSERT INTO otp_store (email, otp, expiry_time, purpose) VALUES (?, ?, ?, ?)"),
        (email, otp, expiry_at.strftime('%Y-%m-%d %H:%M:%S'), purpose)
    )
    conn.commit()
    conn.close()

def verify_otp_logic(email, otp, purpose):
    """Verifies OTP and handles expiration/attempts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the latest active OTP
    cursor.execute(
        adapt_sql("SELECT id, otp, expiry_time, attempts FROM otp_store WHERE email = ? AND purpose = ? AND is_used = 0 ORDER BY created_at DESC LIMIT 1"),
        (email, purpose)
    )
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, "No active verification code found. Please request a new one."
    
    otp_id, stored_otp, expiry_val, attempts = row
    
    # Handle different database drivers returning different types for TIMESTAMP
    if isinstance(expiry_val, str):
        # SQLite usually returns a string
        expiry_time = datetime.strptime(expiry_val[:19], '%Y-%m-%d %H:%M:%S')
    else:
        # Postgres (psycopg2) usually returns a native datetime object
        expiry_time = expiry_val
    
    if datetime.now() > expiry_time:
        cursor.execute(adapt_sql("UPDATE otp_store SET is_used = 1 WHERE id = ?"), (otp_id,))
        conn.commit()
        conn.close()
        return False, "Verification code has expired. Please try again."
    
    if attempts >= 3:
        cursor.execute(adapt_sql("UPDATE otp_store SET is_used = 1 WHERE id = ?"), (otp_id,))
        conn.commit()
        conn.close()
        return False, "Too many failed attempts. Please request a new code."
    
    if stored_otp != otp:
        cursor.execute(adapt_sql("UPDATE otp_store SET attempts = attempts + 1 WHERE id = ?"), (otp_id,))
        conn.commit()
        conn.close()
        return False, f"Invalid code. {2 - attempts} attempts remaining."
    
    # Success: Mark OTP as used
    cursor.execute(adapt_sql("UPDATE otp_store SET is_used = 1 WHERE id = ?"), (otp_id,))
    conn.commit()
    conn.close()
    return True, "success"


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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(adapt_sql("SELECT 1 FROM chat_sessions WHERE id = ? AND user_id = ?"), (session_id, user_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def create_new_session(user_id: int):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(adapt_sql("""
        INSERT INTO chat_sessions (id, title, user_id)
        VALUES (?, ?, ?)
    """), (session_id, "New Legal Research", user_id))

    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(adapt_sql("""
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """), (user_id,))

    sessions = cursor.fetchall()
    conn.close()

    return [{"id": s[0], "title": s[1], "created_at": s[2], "updated_at": s[3]} for s in sessions]

def get_chat_history(session_id: str, user_id: int):
    if not ensure_session_exists(session_id, user_id):
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(adapt_sql("""
        SELECT m.id, m.role, m.content, m.timestamp
        FROM chat_messages m
        INNER JOIN chat_sessions s ON s.id = m.session_id
        WHERE m.session_id = ? AND s.user_id = ?
        ORDER BY timestamp ASC
    """), (session_id, user_id))

    messages = cursor.fetchall()
    conn.close()

    return [{"id": m[0], "role": m[1], "content": m[2], "timestamp": m[3]} for m in messages]

def save_message(session_id: str, role: str, content: str, user_id: int):
    if not ensure_session_exists(session_id, user_id):
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(adapt_sql("""
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    """), (session_id, role, content))

    cursor.execute(adapt_sql("""
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """), (session_id, user_id))

    conn.commit()
    conn.close()
    return True

def update_session_title(session_id: str, title: str, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    display_title = title[:50] + "..." if len(title) > 50 else title
    
    cursor.execute(adapt_sql("""
        UPDATE chat_sessions
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """), (display_title, session_id, user_id))

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
        model_name = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        legal_agent = Agent(
            model=Groq(id=model_name, temperature=0.1),
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
        # Use a safe print if logger isn't ready
        print(f"Failed to initialize legal agent: {e}")

# Fix 2 + 3 + 4: Lazy initialization of the agent
def get_legal_agent():
    global legal_agent
    if legal_agent is None and not LLM_READY:
        init_legal_agent()
    return legal_agent

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
def index():
    return render_template('legal_chat.html', username=session.get("username", ""))


@app.route("/terms")
def terms_and_conditions():
    return render_template("terms.html", username=session.get("username", ""))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        # Handle AJAX login request
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request."}), 400
            
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email and password are required."}), 400
        
        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"status": "error", "message": "Invalid email or password."}), 401
        
        # Valid credentials, now send OTP
        otp = generate_otp()
        email_sent = send_otp_email(email, otp)
        
        # We always save the OTP even if email fails, so the fallback code in console works
        save_otp(email, otp, 'login')
        
        if email_sent:
            return jsonify({"status": "otp_sent", "email": email})
        else:
            # If email fails, we return success anyway in development if we logged it to console
            # Change this to error if you want strict email requirement
            return jsonify({
                "status": "otp_sent", 
                "email": email, 
                "warning": "Email failed to send, but verification code generated (Check server console)."
            })

    notice = ""
    if request.args.get("signup") == "success":
        notice = "Account created successfully. Please login to continue."
    
    return render_template("login.html", notice=notice)

@app.route("/verify-login-otp", methods=["POST"])
def verify_login_otp():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request."}), 400
        
    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip()
    
    if not email or not otp:
        return jsonify({"status": "error", "message": "OTP is required."}), 400
        
    success, message = verify_otp_logic(email, otp, 'login')
    
    if success:
        user = get_user_by_email(email)
        if not user:
             return jsonify({"status": "error", "message": "User not found."}), 404
             
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"status": "success", "redirect": url_for("index")})
    else:
        return jsonify({"status": "error", "message": message}), 401


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        session.clear()

    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request."}), 400
            
        username = data.get("username", "").strip().lower()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        if not username or not email or not password or not confirm_password:
            return jsonify({"status": "error", "message": "All fields are required."}), 400
        elif len(username) < 3:
            return jsonify({"status": "error", "message": "Username must be at least 3 characters long."}), 400
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return jsonify({"status": "error", "message": "Please enter a valid email address."}), 400
        elif len(password) < 8:
            return jsonify({"status": "error", "message": "Password must be at least 8 characters long."}), 400
        elif password != confirm_password:
            return jsonify({"status": "error", "message": "Passwords do not match."}), 400
        elif get_user_by_username(username):
            return jsonify({"status": "error", "message": "Username already exists."}), 400
        elif get_user_by_email(email):
            return jsonify({"status": "error", "message": "Email is already registered."}), 400
        
        # All valid, send OTP
        otp = generate_otp()
        email_sent = send_otp_email(email, otp)
        
        # Always save for potential fallback/manual override
        save_otp(email, otp, 'signup')
        
        if email_sent:
            return jsonify({"status": "otp_sent", "email": email})
        else:
            # Allow proceeding in development if email fails
            return jsonify({
                "status": "otp_sent", 
                "email": email,
                "warning": "Email failed to send, but verification code generated (Check server console)."
            })

    return render_template("signup.html")

@app.route("/verify-signup-otp", methods=["POST"])
def verify_signup_otp():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request."}), 400
        
    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    otp = data.get("otp", "").strip()
    
    if not otp:
        return jsonify({"status": "error", "message": "Verification code is required."}), 400
        
    success, message = verify_otp_logic(email, otp, 'signup')
    
    if success:
        try:
            create_user(username, email, password)
            return jsonify({"status": "success", "redirect": url_for("login", signup="success")})
        except Exception as e:
            # If creation fails (e.g., unexpected constraint violation), inform the user
            app.logger.error(f"Signup completion failed for {email}: {e}")
            return jsonify({"status": "error", "message": "Account creation failed. Please try again or contact support."}), 500
    else:
        return jsonify({"status": "error", "message": message}), 401


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# Fix 5 — Health endpoint (needed by loading screen)
@app.route("/ping")
def ping():
    return "pong", 200

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

@app.route("/api/documents", methods=["GET"])
@api_login_required
def get_synced_documents():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(adapt_sql("SELECT file_name, upload_date FROM synced_files ORDER BY file_name ASC"))
        files = cursor.fetchall()
        conn.close()
        return jsonify({
            "status": "success",
            "documents": [{"name": f[0], "upload_date": f[1]} for f in files]
        })
    except Exception as e:
        app.logger.error(f"Error fetching synced documents: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve documents"}), 500

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

        if request.content_type and request.content_type.startswith('multipart/form-data'):
            user_message = request.form.get("message", "").strip()
            file = request.files.get("file")
            
            if file and file.filename:
                extracted_text = extract_file_content(file)
                user_message += f"\n\n[Attached File Content: {file.filename}]\n{extracted_text}"
        else:
            data = request.get_json()
            user_message = data.get("message", "").strip() if data else ""

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        chat_history = get_chat_history(session_id, user_id) or []

        if len(chat_history) == 0:
            update_session_title(session_id, user_message, user_id)

        save_message(session_id, "user", user_message, user_id)

        # Get conversation context (last 10 msgs)
        history_text = get_chat_context(session_id, user_id)

        # Call our new RAG service to process retrieval and generation
        from LegalAI.services.rag_service import generate_answer
        try:
            rag_result = generate_answer(user_message, history_text)
            ai_response = rag_result["response"]
            confidence_score = rag_result.get("confidence_score", 0.0)
            sources = rag_result.get("sources", [])
        except Exception as rag_err:
            app.logger.error(f"RAG service error in send_message: {rag_err}")
            ai_response = _fallback_legal_response(user_message)
            confidence_score = 0.0
            sources = []

        save_message(session_id, "assistant", ai_response, user_id)

        return jsonify({
            "response": ai_response,
            "status": "success",
            "confidence_score": confidence_score,
            "sources": sources
        })

    except Exception as e:
        app.logger.error(f"Error in send_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/delete_session/<session_id>", methods=["DELETE"])
@api_login_required
def delete_session(session_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        user_id = session["user_id"]

        cursor.execute(
            adapt_sql("""
            DELETE FROM chat_messages
            WHERE session_id IN (
                SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?
            )
            """),
            (session_id, user_id),
        )
        cursor.execute(adapt_sql('DELETE FROM chat_sessions WHERE id = ? AND user_id = ?'), (session_id, user_id))

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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            adapt_sql("""
            SELECT m.role
            FROM chat_messages m
            INNER JOIN chat_sessions s ON s.id = m.session_id
            WHERE m.id = ? AND m.session_id = ? AND s.user_id = ?
            """),
            (message_id, session_id, user_id)
        )

        result = cursor.fetchone()
        if not result or result[0] != 'user':
            conn.close()
            return jsonify({"error": "Message not found or cannot edit assistant messages"}), 404

        cursor.execute(adapt_sql("""
            UPDATE chat_messages
            SET content = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ? AND session_id = ?
        """), (new_message, message_id, session_id))

        cursor.execute(adapt_sql("""
            DELETE FROM chat_messages
            WHERE session_id = ? AND id > ?
        """), (session_id, message_id))

        cursor.execute(adapt_sql("""
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """), (session_id, user_id))

        conn.commit()
        conn.close()

        # Get conversation context
        history_text = get_chat_context(session_id, user_id)

        # Call RAG Service to generate answer
        from LegalAI.services.rag_service import generate_answer
        try:
            rag_result = generate_answer(new_message, history_text)
            ai_response = rag_result["response"]
            confidence_score = rag_result.get("confidence_score", 0.0)
            sources = rag_result.get("sources", [])
        except Exception as rag_err:
            app.logger.error(f"RAG service error in edit_message: {rag_err}")
            ai_response = _fallback_legal_response(new_message)
            confidence_score = 0.0
            sources = []

        save_message(session_id, "assistant", ai_response, user_id)

        return jsonify({
            "response": ai_response,
            "status": "success",
            "confidence_score": confidence_score,
            "sources": sources
        })

    except Exception as e:
        app.logger.error(f"Error in edit_message: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------------------------------------------
#                  PROFILE ROUTE
# ------------------------------------------------------

@app.route('/profile')
def profile():
    if "user_id" not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(adapt_sql("SELECT id, username, email, created_at FROM users WHERE id = ?"), (session["user_id"],))
    user = c.fetchone()
    conn.close()

    if not user:
        session.clear()
        return redirect(url_for('login'))

    created_at_val = user[3]
    created_at_formatted = "Unknown"
    
    if isinstance(created_at_val, str):
        try:
            created_at_formatted = datetime.strptime(created_at_val[:19], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        except:
            # Fallback if the format varies
            created_at_formatted = created_at_val.split()[0] if created_at_val else "Unknown"
    elif hasattr(created_at_val, 'strftime'):
        created_at_formatted = created_at_val.strftime('%B %d, %Y')

    user_dict = {
        "id": user[0],
        "username": user[1],
        "email": user[2] if user[2] else "Not provided",
        "created_at_formatted": created_at_formatted
    }
    return render_template('profile.html', user=user_dict, username=user_dict["username"])

# ------------------------------------------------------
#                  RUN APP
# ------------------------------------------------------

init_db()
# AI agent will be lazy-loaded on demand


# Secure admin synchronization route (suited for Vercel Cron or manual triggers)
@app.route("/api/admin/sync", methods=["POST"])
def admin_sync():
    # Authenticate via request header or parameter token
    req_token = request.headers.get("Authorization") or request.args.get("token")
    env_token = os.environ.get("ADMIN_SYNC_TOKEN")
    
    if env_token and req_token != f"Bearer {env_token}" and req_token != env_token:
        return jsonify({"error": "Unauthorized sync request"}), 401
        
    folder_id = request.args.get("folder_id")
    
    try:
        from LegalAI.services.sync_service import sync_google_drive
        stats = sync_google_drive(folder_id)
        if isinstance(stats, dict) and "error" in stats:
            return jsonify({"status": "failed", "error": stats["error"]}), 500
        return jsonify({"status": "success", "sync_stats": stats})
    except Exception as e:
        app.logger.error(f"Admin sync failed: {e}")
        return jsonify({"status": "failed", "error": str(e)}), 500


def start_local_sync_scheduler():
    """
    Spawns a background daemon thread that periodically runs
    Google Drive synchronization (every 24 hours).
    Does not run if running inside a serverless / Vercel context.
    """
    if os.environ.get("VERCEL"):
        # Serverless environment: background threads are not persistent.
        return
        
    import threading
    import time

    def run_scheduler():
        app.logger.info("Local background sync scheduler started.")
        # Wait for the app to fully initialize and embedding model to load
        time.sleep(30)
        while True:
            try:
                app.logger.info("Background synchronization running...")
                from LegalAI.services.sync_service import sync_google_drive
                sync_google_drive()
                app.logger.info("Background synchronization completed.")
            except Exception as e:
                app.logger.error(f"Background synchronization thread failed: {e}")
            
            # Sleep for 24 hours (86400 seconds)
            time.sleep(24 * 3600)
            
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

if __name__ == "__main__":
    # Pre-load the embedding model before starting the server or sync threads.
    # This prevents connection resets caused by heavy model loading mid-request.
    try:
        from LegalAI.services.embedding_service import preload_model
        preload_model()
    except Exception as e:
        app.logger.warning(f"Embedding model preload skipped: {e}")

    # Initialize Qdrant collection (handles dimension mismatch auto-recreation)
    try:
        from LegalAI.services.qdrant_service import init_collection
        init_collection()
    except Exception as e:
        app.logger.warning(f"Qdrant collection init skipped: {e}")

    start_local_sync_scheduler()
    # use_reloader=False prevents watchdog from detecting model cache file writes
    # and restarting the server mid-operation. Use manual restart for code changes.
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)