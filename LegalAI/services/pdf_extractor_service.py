import logging
import re
import fitz  # PyMuPDF
import numpy as np

logger = logging.getLogger(__name__)

# Lazy load the easyocr reader so it doesn't slow down the whole application startup
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            # Initialize reader (will download models on first run if missing)
            _ocr_reader = easyocr.Reader(['en'])
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise e
    return _ocr_reader

def extract_text_by_page(file_bytes):
    """
    Extracts text page-by-page from in-memory PDF bytes.
    Automatically falls back to OCR if a page contains no readable text.
    
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
            cleaned_text = clean_text(text)
            
            # If standard extraction yields very little text, treat as scanned and use OCR
            if len(cleaned_text) < 50:
                logger.info(f"Page {page_idx + 1} has insufficient text ({len(cleaned_text)} chars). No text layer detected. Switching to OCR...")
                
                # Render the page to a high-resolution pixmap
                pix = page.get_pixmap(dpi=300)
                
                # Convert the pixmap to a numpy array (RGB)
                # Ensure the pixmap format is RGB for easyocr
                if pix.n - pix.alpha < 3:
                    # e.g., grayscale, convert to RGB equivalent if needed, but easyocr handles grayscale fine too
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                else:
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                    
                # If there's an alpha channel, remove it
                if pix.alpha:
                    img_array = img_array[:, :, :3]
                
                # Perform OCR
                try:
                    reader = get_ocr_reader()
                    ocr_results = reader.readtext(img_array, detail=0)
                    ocr_text = " ".join(ocr_results)
                    cleaned_text = clean_text(ocr_text)
                    logger.info(f"OCR completed successfully for page {page_idx + 1}. Characters extracted: {len(cleaned_text)}")
                except Exception as ocr_e:
                    logger.error(f"OCR failed on page {page_idx + 1}: {ocr_e}")
                    # Keep the original minimal text if OCR fails
                    
            pages_text.append(cleaned_text)
            
        logger.info(f"Successfully processed {len(pages_text)} pages from PDF.")
        return pages_text
    except Exception as e:
        logger.error(f"Error processing PDF bytes: {e}")
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
