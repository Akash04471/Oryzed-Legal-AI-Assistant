import sys
import os
from urllib.parse import urlparse

# Add the parent directory to sys.path so we can import LegalAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Extract path from RAW_URI, REQUEST_URI, HTTP_X_FORWARDED_URI, or PATH_INFO
        uri = (
            environ.get('RAW_URI')
            or environ.get('REQUEST_URI')
            or environ.get('HTTP_X_FORWARDED_URI')
            or environ.get('PATH_INFO', '')
        )
        
        # Parse path part (excluding query string)
        path = urlparse(uri).path
        
        # Strip Vercel's serverless function rewrite prefix if present
        if path.startswith('/api/index.py'):
            path = path[len('/api/index.py'):]
        elif path.startswith('/api/index'):
            path = path[len('/api/index'):]
            
        environ['PATH_INFO'] = path if path else '/'
        return self.app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)


# Vercel needs the 'app' variable to be exposed
if __name__ == "__main__":
    app.run()

