import os
import sys
import json
from dotenv import load_dotenv

# Ensure the repository root is in the path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

load_dotenv()
# Try loading from LegalAI/.env if not in root
if not os.environ.get("OPENAI_API_KEY"):
    env_path = os.path.join(ROOT_DIR, "LegalAI", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

from LegalAI.app import app, get_db_connection, adapt_sql

def test_chat_endpoint():
    print("Initializing Flask test client...")
    client = app.test_client()
    
    # 1. Get a valid user and session from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username FROM users LIMIT 1")
        user = cursor.fetchone()
        if not user:
            print("No users found in database. Creating a temp test user...")
            from werkzeug.security import generate_password_hash
            cursor.execute(
                adapt_sql("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"),
                ("testuser", "test@oryzed.com", generate_password_hash("password123"))
            )
            conn.commit()
            cursor.execute("SELECT id, username FROM users LIMIT 1")
            user = cursor.fetchone()
            
        user_id, username = user
        print(f"Using user: {username} (ID: {user_id})")
        
        cursor.execute(adapt_sql("SELECT id FROM chat_sessions WHERE user_id = ? LIMIT 1"), (user_id,))
        session_row = cursor.fetchone()
        if not session_row:
            print("No sessions found for user. Creating a temp test session...")
            import uuid
            session_id = str(uuid.uuid4())
            cursor.execute(
                adapt_sql("INSERT INTO chat_sessions (id, title, user_id) VALUES (?, ?, ?)"),
                (session_id, "Test Session", user_id)
            )
            conn.commit()
        else:
            session_id = session_row[0]
            
        print(f"Using session ID: {session_id}")
    except Exception as e:
        print(f"Database query failed: {e}")
        conn.close()
        return
    finally:
        conn.close()
        
    # 2. Simulate a logged-in session
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        
    # 3. Post a message to the chat API
    print("\nSending POST request to chat endpoint...")
    try:
        response = client.post(
            f"/api/chat/{session_id}/message",
            data=json.dumps({"message": "What is the penalty for contract breach?"}),
            content_type="application/json"
        )
        print(f"Response status code: {response.status_code}")
        print("Response data:")
        print(response.get_data(as_text=True))
    except Exception as e:
        print(f"Request execution failed: {e}")

if __name__ == "__main__":
    test_chat_endpoint()
