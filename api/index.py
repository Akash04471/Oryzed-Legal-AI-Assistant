import sys
import os
from urllib.parse import urlparse

# Add parent directory to sys.path so LegalAI module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Retrieve the original client request path passed by Vercel edge proxy
        raw_path = (
            environ.get('HTTP_X_FORWARDED_PATH')
            or environ.get('HTTP_X_VERCEL_FORWARDED_PATH')
            or environ.get('HTTP_X_FORWARDED_URI')
            or environ.get('PATH_INFO', '/')
        )

        path = urlparse(raw_path).path

        # Strip Vercel function invocation path if present
        if path.startswith('/api/index.py'):
            path = path[len('/api/index.py'):]
        elif path.startswith('/api/index'):
            path = path[len('/api/index'):]

        environ['PATH_INFO'] = path if path else '/'
        return self.app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()
