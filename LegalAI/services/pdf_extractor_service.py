import logging
import re
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_text_by_page(file_bytes):
    """
    Extracts text page-by-page from in-memory PDF bytes.
    
    Args:
        file_bytes (bytes): The PDF file contents.
        
    Returns:
        list of str: List containing the extracted text for each page (1-indexed mapping).
    """
    pages_text = []
    
    try:
        # Open PDF from in-memory bytes stream
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text()
            
            # Basic cleaning: remove null bytes and standardize whitespace
            cleaned_text = clean_text(text)
            pages_text.append(cleaned_text)
            
        logger.info(f"Successfully extracted {len(pages_text)} pages from PDF bytes stream.")
        return pages_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF bytes: {e}")
        raise e


def clean_text(text):
    """
    Cleans extracted text by removing non-printable characters and normalizing whitespace.
    """
    if not text:
        return ""
        
    # Replace null bytes
    text = text.replace('\x00', ' ')
    
    # Normalize whitespaces and replace multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespaces
    return text.strip()
