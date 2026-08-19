import sys
import os
import logging
from urllib.parse import parse_qs

# Set VERCEL environment flag
os.environ["VERCEL"] = "1"

# Add parent directory to sys.path so LegalAI module can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

init_error = None
try:
    from LegalAI.app import app
except Exception as err:
    init_error = str(err)
    logging.error(f"Error initializing LegalAI.app in Vercel handler: {err}", exc_info=True)
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def error_handler(path):
        return jsonify({
            "error": "Application Initialization Failed on Vercel",
            "details": init_error,
            "hint": "Check Vercel Environment Variables and requirements."
        }), 500


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
