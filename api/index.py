import sys
import os

# Set VERCEL environment flag
os.environ["VERCEL"] = "1"

# Add parent directory to sys.path so LegalAI module can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from LegalAI.app import app as flask_app

class VercelWSGIMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # 1. Reset SCRIPT_NAME so Werkzeug doesn't prefix /api/index.py
        environ['SCRIPT_NAME'] = ''
        
        # 2. Extract true requested URL path
        raw_path = (
            environ.get('HTTP_X_FORWARDED_URI')
            or environ.get('REQUEST_URI')
            or environ.get('RAW_URI')
            or environ.get('PATH_INFO', '/')
        )
        
        # Strip query string
        clean_path = raw_path.split('?')[0]
        
        # Strip Vercel function prefix if present
        if clean_path.startswith('/api/index.py'):
            clean_path = clean_path[13:] or '/'
        elif clean_path.startswith('/api/index'):
            clean_path = clean_path[10:] or '/'
            
        if not clean_path.startswith('/'):
            clean_path = '/' + clean_path
            
        environ['PATH_INFO'] = clean_path
        return self.app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
