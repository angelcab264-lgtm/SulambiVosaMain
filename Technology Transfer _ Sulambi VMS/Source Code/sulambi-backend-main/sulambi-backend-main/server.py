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

# Allow common development and production origins
# Get production frontend URL from environment or use default
PRODUCTION_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://sulambi-vosa.onrender.com")

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:8080",
    PRODUCTION_FRONTEND_URL,  # Production frontend (configurable via FRONTEND_URL env var)
    "https://www.sulambi-vosa.com",  # Custom domain with www
    "https://sulambi-vosa.com",  # Custom domain without www
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000"
]

def is_allowed_origin(origin):
    """Check if origin is allowed, including Render subdomains and custom domains"""
    if not origin:
        return False
    
    # Check exact match
    if origin in allowed_origins:
        return True
    
    # Allow any Render subdomain (for flexibility in deployment)
    if origin.endswith('.onrender.com'):
        return True
    
    # Allow custom domain (sulambi-vosa.com) with or without www
    if 'sulambi-vosa.com' in origin:
        return True
    
    return False

# Configure CORS - must use specific origins (not wildcard) when credentials are enabled
# Allow all methods and headers for development
CORS(Server, 
     resources={r"/*": {
         "origins": allowed_origins,
         "allow_headers": "*",
         "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
         "supports_credentials": True,
         "expose_headers": "*"
     }},
     supports_credentials=True)

# Handle CORS preflight (OPTIONS) requests explicitly
@Server.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        from flask import jsonify, make_response
        origin = request.headers.get('Origin')
        if is_allowed_origin(origin):
            response = make_response(jsonify({"status": "ok"}), 200)
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response
        else:
            # Log blocked origin for debugging
            print(f"[CORS] Blocked preflight request from origin: {origin}")
            return make_response(jsonify({"error": "Origin not allowed"}), 403)

# Add CORS headers to all responses (including errors)
# Must use specific origin, not wildcard, when credentials are enabled
@Server.after_request
def after_request(response):
    origin = request.headers.get('Origin', '')
    # Use the request origin if it's in allowed list or is a Render domain
    if is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
    elif allowed_origins:
        # Default to first allowed origin if origin not found
        response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle errors and ensure CORS headers are set even on exceptions
@Server.errorhandler(Exception)
def handle_error(error):
    from flask import jsonify
    origin = request.headers.get('Origin', '') if request else ''
    response = jsonify({
        'message': str(error),
        'error': type(error).__name__
    })
    response.status_code = 500 if not hasattr(error, 'code') else error.code
    
    # Set CORS headers even on errors
    if is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
    elif allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
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