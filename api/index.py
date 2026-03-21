import sys
import os

# Add the parent directory to sys.path so we can import LegalAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

# Vercel needs the 'app' variable to be exposed
if __name__ == "__main__":
    app.run()
