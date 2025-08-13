# ===============================
# 📁 backend/cors_setup.py
# CORS setup for Mini Studio
# ===============================
import os
from flask import request

def setup_cors(app):
    """Add CORS support to Flask app"""
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    
    @app.after_request
    def after_request(response):
        # Add CORS headers for API routes
        if request.path.startswith('/api/'):
            if cors_origins == "*":
                response.headers['Access-Control-Allow-Origin'] = '*'
            else:
                origin = request.headers.get('Origin')
                if origin in cors_origins.split(','):
                    response.headers['Access-Control-Allow-Origin'] = origin
            
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        """Handle preflight OPTIONS requests"""
        response = app.make_default_options_response()
        
        if cors_origins == "*":
            response.headers['Access-Control-Allow-Origin'] = '*'
        else:
            origin = request.headers.get('Origin')
            if origin in cors_origins.split(','):
                response.headers['Access-Control-Allow-Origin'] = origin
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response