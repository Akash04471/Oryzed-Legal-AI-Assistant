import sys
import os
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Print environ keys for debugging in Vercel logs if needed
        path_info = environ.get('PATH_INFO', '')
        
        # If PATH_INFO is already populated by WSGI server (e.g., /login or /terms)
        # and doesn't point to internal function wrapper, keep it intact!
        if path_info and not path_info.startswith('/api/index') and not path_info.startswith('/api'):
            return self.app(environ, start_response)
            
        # Otherwise inspect original request headers passed by Vercel proxy
        uri = (
            environ.get('HTTP_X_FORWARDED_URI')
            or environ.get('HTTP_X_MATCHED_PATH')
            or environ.get('RAW_URI')
            or environ.get('REQUEST_URI')
            or path_info
        )

        path = urlparse(uri).path
        if path.startswith('/api/index.py'):
            path = path[len('/api/index.py'):]
        elif path.startswith('/api/index'):
            path = path[len('/api/index'):]

        environ['PATH_INFO'] = path if path else '/'
        return self.app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()
