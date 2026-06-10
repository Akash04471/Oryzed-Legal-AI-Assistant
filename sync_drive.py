#!/usr/bin/env python
import os
import sys
import logging
from dotenv import load_dotenv

# Ensure the repository root is in the path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Set up logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("sync_drive_cli")

def main():
    logger.info("Initializing Google Drive RAG Sync Pipeline CLI...")
    
    # Load environment variables
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        env_path = os.path.join(ROOT_DIR, "LegalAI", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    
    # 1. Verify key environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        logger.error("Error: OPENAI_API_KEY environment variable is not set. Cannot proceed.")
        sys.exit(1)
        
    google_creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    google_creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "credentials.json"
    
    if not google_creds_json and not os.path.exists(os.path.join(ROOT_DIR, google_creds_file)):
        logger.warning(
            f"Warning: No service account credentials found. "
            f"Set GOOGLE_SERVICE_ACCOUNT_JSON or place {google_creds_file} in the project root."
        )

    # 2. Trigger sync
    try:
        from LegalAI.services.sync_service import sync_google_drive
        
        folder_id = os.environ.get("DRIVE_FOLDER_ID")
        if folder_id:
            logger.info(f"Synchronizing from folder ID: {folder_id}")
        else:
            logger.info("Synchronizing from default Google Drive folder...")
            
        stats = sync_google_drive(folder_id)
        
        if "error" in stats:
            logger.error(f"Sync process completed with error: {stats['error']}")
            sys.exit(1)
            
        print("\n" + "="*50)
        print("           SYNCHRONIZATION COMPLETED            ")
        print("="*50)
        print(f"Total PDFs found on Drive: {stats.get('total', 0)}")
        print(f"Newly processed/updated:   {stats.get('processed', 0)}")
        print(f"Skipped (up-to-date):      {stats.get('skipped', 0)}")
        print(f"Failed to process:         {stats.get('failed', 0)}")
        print("="*50)
        
        if stats.get("details"):
            print("\nSync Details:")
            for item in stats["details"]:
                status_symbol = "✅" if item["status"] == "success" else "❌"
                err_msg = f" - Error: {item['error']}" if "error" in item else ""
                print(f"  {status_symbol} {item['file_name']} ({item['action']}){err_msg}")
        print("="*50 + "\n")
        
        if stats.get("failed", 0) > 0:
            sys.exit(2)
            
    except Exception as e:
        logger.exception(f"An unexpected error occurred during sync: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
