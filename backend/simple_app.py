#!/usr/bin/env python3
"""
Ultra-simple Flask app for Railway deployment
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health")
def health():
    """Ultra-simple health check"""
    return {"status": "healthy", "service": "SoulBridge AI"}, 200

@app.route("/")
def home():
    """Home endpoint"""
    return {"message": "SoulBridge AI is running", "status": "ok"}, 200

@app.route("/test")
def test():
    """Test endpoint"""
    return {"test": "success", "message": "API is working"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)