import logging
from LegalAI.services.google_drive_service import list_pdfs_in_folder, download_file_bytes
from LegalAI.services.pdf_extractor_service import extract_text_by_page
from LegalAI.services.chunking_service import chunk_document
from LegalAI.services.embedding_service import get_embeddings_batch
from LegalAI.services.qdrant_service import upsert_chunks, delete_file_chunks

logger = logging.getLogger(__name__)

def sync_google_drive(folder_id=None):
    """
    Scans the specified Google Drive folder for PDF files and synchronizes
    new or updated documents to the Qdrant knowledge base.
    
    Args:
        folder_id (str, optional): Google Drive folder ID. Defaults to environment config.
        
    Returns:
        dict: Sync statistics (total, processed, skipped, failed).
    """
    # Import locally to prevent circular imports during app initialization
    from LegalAI.app import get_db_connection, adapt_sql
    
    stats = {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "details": []
    }
    
    try:
        drive_files = list_pdfs_in_folder(folder_id)
    except Exception as e:
        logger.error(f"Failed to scan Google Drive folder: {e}")
        return {"error": str(e)}
        
    stats["total"] = len(drive_files)
    
    conn = get_db_connection()
    
    for file in drive_files:
        file_id = file["id"]
        file_name = file["name"]
        # Use modifiedTime or createdTime as the file's upload_date reference
        upload_date = file.get("modifiedTime") or file.get("createdTime")
        
        logger.info(f"Checking sync state for file '{file_name}' ({file_id})")
        
        try:
            cursor = conn.cursor()
            # Check if this file has been processed previously
            cursor.execute(
                adapt_sql("SELECT upload_date FROM synced_files WHERE drive_file_id = ?"),
                (file_id,)
            )
            row = cursor.fetchone()
            
            is_new = row is None
            is_updated = False
            
            if not is_new:
                stored_upload_date = row[0]
                # If modified time is newer, we re-sync the document
                if upload_date != stored_upload_date:
                    is_updated = True
                    
            if not is_new and not is_updated:
                logger.info(f"File '{file_name}' is already up-to-date. Skipping.")
                stats["skipped"] += 1
                continue
                
            action = "indexing" if is_new else "re-indexing"
            logger.info(f"Starting {action} for file '{file_name}'...")
            
            # 1. Download bytes from Drive
            file_bytes = download_file_bytes(file_id)
            
            # 2. Extract text page-by-page
            pages_text = extract_text_by_page(file_bytes)
            if not pages_text or all(not p.strip() for p in pages_text):
                logger.warning(
                    f"File '{file_name}' contains no readable text. This usually happens "
                    f"if it is a scanned image PDF without an OCR text layer. Skipping."
                )
                stats["skipped"] += 1
                continue
                
            # 3. Chunk text into 500-1000 token segments
            chunks = chunk_document(file_name, pages_text, upload_date)
            if not chunks:
                logger.warning(f"No chunks created for file '{file_name}'. Skipping.")
                stats["skipped"] += 1
                continue
                
            # 4. Generate Embeddings
            chunk_texts = [c["text"] for c in chunks]
            embeddings = get_embeddings_batch(chunk_texts)
            
            # 5. Store in Qdrant (remove old versions if updating)
            if is_updated:
                delete_file_chunks(file_name)
            upsert_chunks(chunks, embeddings)
            
            # 6. Update database sync status
            if is_new:
                cursor.execute(
                    adapt_sql("INSERT INTO synced_files (drive_file_id, file_name, upload_date) VALUES (?, ?, ?)"),
                    (file_id, file_name, upload_date)
                )
            else:
                cursor.execute(
                    adapt_sql("UPDATE synced_files SET file_name = ?, upload_date = ?, synced_at = CURRENT_TIMESTAMP WHERE drive_file_id = ?"),
                    (file_name, upload_date, file_id)
                )
            
            conn.commit()
            
            logger.info(f"File '{file_name}' synchronized successfully.")
            stats["processed"] += 1
            stats["details"].append({"file_name": file_name, "status": "success", "action": action})
            
        except Exception as e:
            logger.error(f"Failed to synchronize file '{file_name}': {e}")
            conn.rollback()
            stats["failed"] += 1
            stats["details"].append({"file_name": file_name, "status": "failed", "error": str(e)})
            
    conn.close()
    logger.info(f"Synchronization finished: {stats['processed']} processed, {stats['skipped']} skipped, {stats['failed']} failed.")
    return stats
