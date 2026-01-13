#!/bin/bash
# Startup script for Railway deployment
# This script navigates to the backend directory and starts the server

cd "Technology Transfer _ Sulambi VMS/Source Code/sulambi-backend-main/sulambi-backend-main"

# Initialize database (or continue if already initialized)
python server.py --init || true

# Start Gunicorn server
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 server:app
