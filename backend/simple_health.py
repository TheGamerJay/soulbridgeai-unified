# Simple Health Check for Railway Deployment
from flask import jsonify
from datetime import datetime
import uuid

def simple_health_check():
    """Ultra-simple health check that always works"""
    return jsonify({
        "status": "healthy",
        "service": "SoulBridge AI",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": "Service is running"
    }), 200