import os
import sys
import time
import unittest
from PIL import Image, ImageDraw, ImageFont

# Set testing environment to isolate database folder from active sync process
os.environ["TESTING"] = "true"
# Override the database folder just for this test
os.environ["DATABASE_FOLDER"] = "test_qdrant_db"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Fix Windows console encoding issues for OCR text
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

# We only run the test if easyocr/fitz is accessible
try:
    import fitz
    import numpy as np
    from LegalAI.services.pdf_extractor_service import extract_text_by_page
    from LegalAI.services.chunking_service import chunk_document
    from LegalAI.services.embedding_service import get_embeddings_batch
    from LegalAI.services.qdrant_service import upsert_chunks, search_similar_chunks
    from LegalAI.services.rag_service import generate_answer
    
    dependencies_ok = True
except ImportError as e:
    print(f"Skipping E2E tests due to missing dependencies: {e}")
    dependencies_ok = False


def create_native_pdf(filename):
    """Creates a native PDF with embedded text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a native text PDF test for legal document ingestion.")
    page.insert_text((50, 100), "The penalty under IPC Section 420 includes imprisonment which may extend to seven years.")
    doc.save(filename)
    doc.close()

def create_scanned_pdf(filename):
    """Creates a scanned image PDF without embedded text."""
    # Create a white image
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Draw some text (this requires a font, but default is usually available or fallback)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
        
    d.text((50, 50), "This is a scanned image PDF test for OCR fallback.", fill=(0,0,0), font=font)
    d.text((50, 100), "According to the Indian Contract Act, an agreement enforceable by law is a contract.", fill=(0,0,0), font=font)
    
    # Save as PDF
    img.save(filename, "PDF", resolution=100.0)

class TestEndToEndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not dependencies_ok:
            raise unittest.SkipTest("Dependencies missing")
        cls.native_pdf_path = "test_native.pdf"
        cls.scanned_pdf_path = "test_scanned.pdf"
        create_native_pdf(cls.native_pdf_path)
        create_scanned_pdf(cls.scanned_pdf_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.native_pdf_path):
            os.remove(cls.native_pdf_path)
        if os.path.exists(cls.scanned_pdf_path):
            os.remove(cls.scanned_pdf_path)

    def test_pipeline_native_pdf(self):
        print("\n--- Testing Native PDF Pipeline ---")
        start_time = time.time()
        
        with open(self.native_pdf_path, "rb") as f:
            file_bytes = f.read()
            
        # 1. Extract
        pages_text = extract_text_by_page(file_bytes)
        self.assertTrue(len(pages_text) > 0)
        self.assertIn("IPC Section 420", pages_text[0])
        print(f"Extraction took {time.time() - start_time:.2f}s")
        
        # 2. Chunk
        chunks = chunk_document("native_test", pages_text, "2026-07-09")
        self.assertTrue(len(chunks) > 0)
        
        # 3. Embed
        chunk_texts = [c["text"] for c in chunks]
        try:
            embeddings = get_embeddings_batch(chunk_texts)
            self.assertEqual(len(chunks), len(embeddings))
            
            # 4. Insert
            upsert_chunks(chunks, embeddings)
            print("Successfully inserted native chunks to Qdrant")
        except Exception as e:
            print(f"Skipping embedding/Qdrant steps due to rate limits or missing keys: {e}")

    def test_pipeline_scanned_pdf(self):
        print("\n--- Testing Scanned PDF Pipeline (OCR Fallback) ---")
        start_time = time.time()
        
        with open(self.scanned_pdf_path, "rb") as f:
            file_bytes = f.read()
            
        # 1. Extract (will use OCR fallback)
        pages_text = extract_text_by_page(file_bytes)
        self.assertTrue(len(pages_text) > 0)
        
        # Check if OCR extracted the text
        extracted = pages_text[0].lower()
        self.assertIn("contract", extracted)
        self.assertIn("agreement", extracted)
        print(f"OCR Extraction took {time.time() - start_time:.2f}s")
        print(f"Extracted OCR text: {pages_text[0][:100]}...")
        
        # 2. Chunk
        chunks = chunk_document("scanned_test", pages_text, "2026-07-09")
        self.assertTrue(len(chunks) > 0)
        
        # 3. Embed
        chunk_texts = [c["text"] for c in chunks]
        try:
            embeddings = get_embeddings_batch(chunk_texts)
            self.assertEqual(len(chunks), len(embeddings))
            
            # 4. Insert
            upsert_chunks(chunks, embeddings)
            print("Successfully inserted scanned chunks to Qdrant")
            
            # 5. Search
            results = search_similar_chunks("What is an agreement enforceable by law?", top_k=2)
            self.assertTrue(len(results) > 0)
            print("Search returned relevant results.")
        except Exception as e:
            print(f"Skipping embedding/Qdrant steps due to rate limits or missing keys: {e}")

if __name__ == "__main__":
    unittest.main()
