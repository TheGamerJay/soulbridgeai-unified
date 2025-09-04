# health.py
"""
Health checks blueprint for operational monitoring
Provides standardized health and readiness endpoints
"""
from flask import Blueprint, jsonify

health_bp = Blueprint("ops_health", __name__)

@health_bp.route("/healthz", methods=["GET"])
def healthz():
    """Health check endpoint - always returns OK if service is running"""
    return jsonify(status="ok"), 200

@health_bp.route("/readyz", methods=["GET"])  
def readyz():
    """Readiness check endpoint - indicates if service can handle requests"""
    return jsonify(ready=True), 200

@health_bp.route("/livez", methods=["GET"])
def livez():
    """Liveness check endpoint - indicates if service is alive"""
    return jsonify(alive=True), 200