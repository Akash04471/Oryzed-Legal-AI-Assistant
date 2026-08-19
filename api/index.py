import sys
import os

# Set VERCEL environment flag
os.environ["VERCEL"] = "1"

# Add parent directory to sys.path so LegalAI module can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from LegalAI.app import app
