#!/usr/bin/env python3
"""
Ultra-minimal Flask app for Railway health check testing
This MUST work if Railway environment is properly configured
"""
import os
import sys
from flask import Flask, jsonify
from datetime import datetime

# Create the simplest possible Flask app
app = Flask(__name__)

@app.route("/health")
def health():
    """Absolute minimal health check"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "port": os.environ.get("PORT", "unknown")
    })

@app.route("/")
def home():
    """Basic home route"""
    return jsonify({
        "service": "SoulBridge AI",
        "status": "minimal mode",
        "message": "This is a minimal version for debugging Railway deployment"
    })

@app.route("/debug")
def debug():
    """Debug information"""
    return jsonify({
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment": {
            "PORT": os.environ.get("PORT"),
            "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT"),
            "SECRET_KEY": "SET" if os.environ.get("SECRET_KEY") else "NOT SET",
            "RESEND_API_KEY": "SET" if os.environ.get("RESEND_API_KEY") else "NOT SET",
            "OPENAI_API_KEY": "SET" if os.environ.get("OPENAI_API_KEY") else "NOT SET",
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting minimal Flask app on port {port}")
    print(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    # Use the most basic possible server configuration
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=False, 
        threaded=True,
        use_reloader=False
    )