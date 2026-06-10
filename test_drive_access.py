import os
import sys
import json
from dotenv import load_dotenv

# Ensure the repository root is in the path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

load_dotenv()
# Try loading from LegalAI/.env if not in root
if not os.environ.get("OPENAI_API_KEY"):
    env_path = os.path.join(ROOT_DIR, "LegalAI", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

from LegalAI.services.google_drive_service import get_drive_service

def diagnose():
    print("Initializing Google Drive service account diagnostics...")
    try:
        service = get_drive_service()
        print("Successfully authenticated and built Google Drive service client.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # List ALL files the service account can see anywhere (no parent filter)
    print("\nQuerying ALL files visible to this service account...")
    try:
        results = service.files().list(
            q="trashed=false",
            fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
            pageSize=50
        ).execute()
        files = results.get('files', [])
        print(f"Total files visible: {len(files)}")
        for f in files:
            print(f" - Name: {f['name']} | ID: {f['id']} | MimeType: {f['mimeType']} | Parents: {f.get('parents')}")
    except Exception as e:
        print(f"Failed to query all files: {e}")

    # Check the specific folder ID directly
    folder_id = os.environ.get("DRIVE_FOLDER_ID", "1MvelAg8i_h_SxkuOnkO4rAxAIEXRz7io")
    print(f"\nChecking metadata of folder '{folder_id}' directly...")
    try:
        folder = service.files().get(fileId=folder_id, fields="id, name, mimeType, owners").execute()
        print(f"Folder found! Name: {folder['name']} | MimeType: {folder['mimeType']} | Owners: {folder.get('owners')}")
    except Exception as e:
        print(f"Failed to fetch metadata for folder '{folder_id}': {e}")

if __name__ == "__main__":
    diagnose()
