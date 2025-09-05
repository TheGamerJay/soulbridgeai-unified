# health.py
"""
Railway-compatible health checks (no authentication required)
Critical: These endpoints must be accessible for Railway's health probes
"""
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/health")   
def health():
    """Railway default health probe - no authentication required"""
    return jsonify(status="ok", healthy=True), 200

@health_bp.get("/healthz")  
def healthz():
    """Kubernetes-style health check - no authentication required"""
    return jsonify(status="ok"), 200

@health_bp.get("/readyz")   
def readyz():
    """Readiness probe - can add DB/Redis checks later if needed"""
    return jsonify(ready=True), 200