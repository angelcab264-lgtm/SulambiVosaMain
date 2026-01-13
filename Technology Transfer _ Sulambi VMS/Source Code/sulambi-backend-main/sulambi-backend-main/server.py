from flask import Flask, send_from_directory, jsonify
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

@Server.route("/")
def healthCheck():
  """Health check endpoint for Railway deployment"""
  return jsonify({
    "status": "online",
    "message": "Sulambi VMS Backend is running"
  }), 200

@Server.route("/health")
def healthCheckDetailed():
  """Detailed health check endpoint"""
  return jsonify({
    "status": "online",
    "service": "Sulambi VMS Backend",
    "database": "connected" if os.getenv("DATABASE_URL") else "sqlite"
  }), 200

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
  # Railway provides PORT automatically, bind to 0.0.0.0 for external access
  host = os.getenv("HOST", "0.0.0.0")
  port = int(os.getenv("PORT", 8000))
  
  # Run Flask dev server (only in development)
  # In production, Railway will use Gunicorn via Procfile
  Server.run(host=host, port=port, debug=False)
