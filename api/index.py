import sys
import os

# Add the parent directory to sys.path so we can import LegalAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Prefer original path from Vercel headers if present
        raw_path = (
            environ.get('HTTP_X_FORWARDED_PATH')
            or environ.get('HTTP_X_MATCHED_PATH')
            or environ.get('PATH_INFO', '')
        )
        
        # Clean up Vercel serverless entry point prefix
        if raw_path.startswith('/api/index.py'):
            raw_path = raw_path[len('/api/index.py'):]
        elif raw_path.startswith('/api/index'):
            raw_path = raw_path[len('/api/index'):]
            
        environ['PATH_INFO'] = raw_path if raw_path else '/'
        return self.app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Vercel needs the 'app' variable to be exposed
if __name__ == "__main__":
    app.run()

