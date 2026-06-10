import logging
import tiktoken

logger = logging.getLogger(__name__)

def chunk_document(file_name, pages_text, upload_date):
    """
    Chunks extracted page texts of a document into segments of 500-1000 tokens.
    
    Args:
        file_name (str): Name of the file.
        pages_text (list of str): List of extracted text for each page (0-indexed list).
        upload_date (str): Upload/Modification date of the document (ISO format or similar).
        
    Returns:
        list of dict: List of chunks, where each chunk has 'text' and 'metadata'.
    """
    tokenizer = tiktoken.get_encoding("cl100k_base")
    chunks = []
    
    current_chunk_text = []
    current_chunk_tokens = 0
    start_page = 1  # 1-indexed page number
    
    for page_idx, page_text in enumerate(pages_text):
        page_num = page_idx + 1
        # Tokenize the page content
        tokens = tokenizer.encode(page_text)
        num_tokens = len(tokens)
        
        # Scenario 1: A single page is larger than 900 tokens.
        # We must split this page into multiple sub-chunks to avoid exceeding 1000 tokens.
        if num_tokens > 900:
            # First, flush any accumulated chunk before processing this large page
            if current_chunk_text:
                chunks.append({
                    "text": " ".join(current_chunk_text),
                    "metadata": {
                        "file_name": file_name,
                        "start_page": start_page,
                        "end_page": page_num - 1 if page_num - 1 >= start_page else start_page,
                        "upload_date": upload_date
                    }
                })
                current_chunk_text = []
                current_chunk_tokens = 0
            
            # Split the large page content into chunks of ~800 tokens with 100 tokens overlap
            i = 0
            while i < num_tokens:
                chunk_tokens = tokens[i : i + 800]
                chunk_text = tokenizer.decode(chunk_tokens)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "file_name": file_name,
                        "start_page": page_num,
                        "end_page": page_num,
                        "upload_date": upload_date
                    }
                })
                i += 700  # 100 token overlap step
            
            # The next accumulated chunk starts at the next page
            start_page = page_num + 1
            
        # Scenario 2: The current page fits. We check if adding it exceeds 900 tokens.
        else:
            if current_chunk_tokens + num_tokens > 900:
                # Flush the current accumulated chunk
                chunks.append({
                    "text": " ".join(current_chunk_text),
                    "metadata": {
                        "file_name": file_name,
                        "start_page": start_page,
                        "end_page": page_num - 1 if page_num - 1 >= start_page else start_page,
                        "upload_date": upload_date
                    }
                })
                # Start a new chunk with the current page text
                current_chunk_text = [page_text]
                current_chunk_tokens = num_tokens
                start_page = page_num
            else:
                # Accumulate the page
                current_chunk_text.append(page_text)
                current_chunk_tokens += num_tokens
                
    # Flush any remaining text in the buffer
    if current_chunk_text:
        chunks.append({
            "text": " ".join(current_chunk_text),
            "metadata": {
                "file_name": file_name,
                "start_page": start_page,
                "end_page": len(pages_text),
                "upload_date": upload_date
            }
        })
        
    logger.info(f"Chunked document '{file_name}' into {len(chunks)} segments.")
    return chunks
