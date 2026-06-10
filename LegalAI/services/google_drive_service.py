import io
import os
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Default target folder ID if not specified
DEFAULT_FOLDER_ID = "1MvelAg8i_h_SxkuOnkO4rAxAIEXRz7io"

def get_drive_service():
    """
    Initializes and returns a Google Drive API service client.
    First checks for GOOGLE_SERVICE_ACCOUNT_JSON (JSON string).
    Next checks for GOOGLE_APPLICATION_CREDENTIALS (path to JSON file).
    Finally defaults to 'credentials.json' file if present in the workspace root.
    """
    creds = None
    
    # 1. Try GOOGLE_SERVICE_ACCOUNT_JSON env var
    service_account_json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json_str:
        try:
            creds_info = json.loads(service_account_json_str)
            creds = service_account.Credentials.from_service_account_info(creds_info)
            logger.info("Successfully loaded Google credentials from GOOGLE_SERVICE_ACCOUNT_JSON env var.")
        except Exception as e:
            logger.error(f"Error parsing GOOGLE_SERVICE_ACCOUNT_JSON env var: {e}")

    # 2. Try GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CREDENTIALS_PATH
    if not creds:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GOOGLE_CREDENTIALS_PATH")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        if not creds_path:
            # Fall back to root directory credentials.json
            creds_path = os.path.join(base_dir, "credentials.json")
        elif not os.path.isabs(creds_path):
            # Resolve relative paths against the project root base_dir
            creds_path = os.path.join(base_dir, creds_path)
            
        if os.path.exists(creds_path):
            try:
                creds = service_account.Credentials.from_service_account_file(creds_path)
                logger.info(f"Successfully loaded Google credentials from file: {creds_path}")
            except Exception as e:
                logger.error(f"Error loading credentials file {creds_path}: {e}")
        else:
            logger.warning(f"Google credentials file not found at: {creds_path}")

    if not creds:
        raise ValueError(
            "Google Drive API credentials are not configured. "
            "Please set GOOGLE_SERVICE_ACCOUNT_JSON in environment variables or "
            "provide a valid credentials.json service account file in the workspace root."
        )

    # Scopes
    scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/drive.readonly'])
    return build('drive', 'v3', credentials=scoped_creds)


def get_all_subfolder_ids(service, root_folder_id):
    """
    Recursively finds all subfolder IDs starting from root_folder_id using BFS.
    """
    folder_ids = [root_folder_id]
    queue = [root_folder_id]
    
    while queue:
        current_id = queue.pop(0)
        query = f"'{current_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        page_token = None
        while True:
            try:
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                subfolders = results.get('files', [])
                for sf in subfolders:
                    sf_id = sf['id']
                    if sf_id not in folder_ids:
                        folder_ids.append(sf_id)
                        queue.append(sf_id)
                        
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"Error fetching subfolders for {current_id}: {e}")
                break
                
    return folder_ids


def list_pdfs_in_folder(folder_id=None):
    """
    Lists all PDF files recursively inside the specified Google Drive folder and its subfolders.
    
    Args:
        folder_id (str): The folder ID. Defaults to DEFAULT_FOLDER_ID.
        
    Returns:
        list of dict: List containing dictionaries with 'id', 'name', 'modifiedTime', and 'createdTime'.
    """
    if not folder_id:
        folder_id = os.environ.get("DRIVE_FOLDER_ID", DEFAULT_FOLDER_ID)
        
    service = get_drive_service()
    
    # 1. Get all subfolders recursively
    logger.info(f"Resolving all subfolders for root folder: {folder_id}")
    try:
        all_folder_ids = get_all_subfolder_ids(service, folder_id)
        logger.info(f"Resolved {len(all_folder_ids)} folders in total.")
    except Exception as e:
        logger.error(f"Failed to resolve subfolders for {folder_id}: {e}")
        all_folder_ids = [folder_id]
        
    files = []
    
    # 2. List PDFs for each folder
    for f_id in all_folder_ids:
        query = f"'{f_id}' in parents and mimeType='application/pdf' and trashed=false"
        page_token = None
        while True:
            try:
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, modifiedTime)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"Failed to list PDF files from folder {f_id}: {e}")
                break
                
    logger.info(f"Found {len(files)} PDF files recursively inside folder: {folder_id}")
    return files


def download_file_bytes(file_id):
    """
    Downloads the content of a file from Google Drive as a byte stream in memory.
    
    Args:
        file_id (str): The Google Drive file ID.
        
    Returns:
        bytes: The downloaded file contents.
    """
    service = get_drive_service()
    
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        file_data = fh.read()
        logger.info(f"Downloaded file {file_id} successfully ({len(file_data)} bytes).")
        return file_data
    except Exception as e:
        logger.error(f"Failed to download file {file_id} from Google Drive: {e}")
        raise e
