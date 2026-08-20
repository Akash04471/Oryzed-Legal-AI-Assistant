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
        # 1. Reset SCRIPT_NAME so Flask resolves paths from root '/'
        environ['SCRIPT_NAME'] = ''
        
        # 2. Get true request PATH_INFO passed to serverless function
        path = environ.get('PATH_INFO', '/')
        
        # Strip Vercel function filename if prepended by router
        if path.startswith('/api/index.py'):
            path = path[13:] or '/'
        elif path.startswith('/api/index'):
            path = path[10:] or '/'
            
        if not path.startswith('/'):
            path = '/' + path
            
        environ['PATH_INFO'] = path
        return self.app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
