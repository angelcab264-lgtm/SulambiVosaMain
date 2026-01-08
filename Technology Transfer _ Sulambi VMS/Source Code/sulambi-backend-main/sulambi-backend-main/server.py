from flask import Flask, send_from_directory, request
from flask_cors import CORS
from app.blueprint import ApiBlueprint
from dotenv import load_dotenv
import sys
import os

load_dotenv()

def testFunction():
  import data.automation.eventTableMigrator

# Create Flask app (needed for both dev and production)
Server = Flask(__name__)
CORS(Server, resources={r"/*": {
  "origins": "*",
  "allow_headers": "*",
  "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  "supports_credentials": True
}})

# Add after_request handler to ensure CORS headers are always present
# Note: flask-cors already handles CORS, but we add this as a fallback for error responses
# We check if headers already exist to avoid duplicates
@Server.after_request
def after_request(response):
    """Ensure CORS headers are always present on all responses (only if not already set by flask-cors)"""
    # Only add headers if they don't already exist (to avoid duplicates)
    if 'Access-Control-Allow-Origin' not in response.headers:
        origin = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    return response

@Server.route("/uploads/<path:path>")
def staticFileHost(path):
  response = send_from_directory("uploads", path)
  response.headers['Access-Control-Allow-Origin'] = '*'
  response.headers['Access-Control-Allow-Methods'] = 'GET'
  response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
  response.headers['Cache-Control'] = 'public, max-age=3600'
  return response

Server.register_blueprint(ApiBlueprint)

# Export app for Gunicorn (production)
app = Server

if __name__ == "__main__":
  if ("--init" in sys.argv):
    import app.database.tableInitializer
    exit()
  if ("--migrate-photo-captions" in sys.argv):
    from app.database.migrate_photo_captions import migrate_photo_captions
    migrate_photo_captions()
    exit()
  if ("--test" in sys.argv):
    testFunction()
    exit()
  if ("--reset" in sys.argv):
    if (os.path.isfile(os.getenv("DB_PATH"))):
      os.remove(os.getenv("DB_PATH"))
    exit()

  # Use environment variables for production, defaults for development
  host = os.getenv("HOST", "localhost")
  port = int(os.getenv("PORT", 8000))
  
  # Run Flask dev server (only in development)
  Server.run(host=host, port=port, debug=True)