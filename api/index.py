import sys
import os
from urllib.parse import parse_qs

# Add parent directory to sys.path so LegalAI module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LegalAI.app import app

class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        qs_params = parse_qs(query_string)

        if '__path__' in qs_params and qs_params['__path__']:
            path = qs_params['__path__'][0]
            if not path.startswith('/'):
                path = '/' + path
            environ['PATH_INFO'] = path
        elif environ.get('PATH_INFO', '').startswith('/api/index'):
            environ['PATH_INFO'] = '/'

        return self.app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()
