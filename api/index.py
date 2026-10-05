import sys
import os

# Set VERCEL environment flag
os.environ["VERCEL"] = "1"

# Add parent directory to sys.path so LegalAI module can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from urllib.parse import parse_qs
from LegalAI.app import app as flask_app

class VercelWSGIMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # 1. Reset SCRIPT_NAME so Flask resolves paths from root '/'
        environ['SCRIPT_NAME'] = ''
        
        # 2. Extract target path from __path parameter forwarded by vercel.json rewrite
        query_string = environ.get('QUERY_STRING', '')
        qs = parse_qs(query_string)
        
        target_path = None
        if '__path' in qs and qs['__path']:
            target_path = qs['__path'][0]
            
        # Fallback to headers if __path parameter is not present
        if not target_path or target_path == '/':
            target_path = (
                environ.get('HTTP_X_MATCHED_PATH')
                or environ.get('HTTP_X_FORWARDED_URI')
                or environ.get('PATH_INFO', '/')
            )
            
        # Strip function filename if prepended
        if target_path.startswith('/api/index.py'):
            target_path = target_path[13:] or '/'
        elif target_path.startswith('/api/index'):
            target_path = target_path[10:] or '/'
            
        # Clean double slashes e.g. //login -> /login
        while target_path.startswith('//'):
            target_path = target_path[1:]
            
        if not target_path.startswith('/'):
            target_path = '/' + target_path
            
        environ['PATH_INFO'] = target_path
        return self.app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
