"""
RecruitAI - Root WSGI Application Entry Point
This file is the entry point for gunicorn in production (Railway)
"""
import sys
import os

# Add RecruitAI folder to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import the actual Flask app from RecruitAI package
from RecruitAI.app import app

if __name__ == "__main__":
    # This runs only for local development
    # In production, gunicorn runs the app directly
    app.run(debug=False, port=5000)
