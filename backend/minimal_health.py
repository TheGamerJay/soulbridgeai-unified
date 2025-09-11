#!/usr/bin/env python3
"""
Minimal health check app for Railway debugging
Tests if basic Flask app can start without all the heavy modules
"""
import os
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minimal_app():
    """Create minimal Flask app for health checking only"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "healthy": True}), 200
    
    @app.route('/healthz') 
    def healthz():
        return jsonify({"status": "ok"}), 200
        
    @app.route('/readyz')
    def readyz():
        return jsonify({"ready": True}), 200
    
    @app.route('/')
    def index():
        return jsonify({"message": "Minimal SoulBridge AI - Health Check Only"}), 200
    
    logger.info("✅ Minimal health app created successfully")
    return app

if __name__ == '__main__':
    app = create_minimal_app()
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🚀 Starting minimal health app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)