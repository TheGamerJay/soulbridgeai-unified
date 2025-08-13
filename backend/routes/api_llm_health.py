"""
LLM Health Check API
"""
from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)
bp = Blueprint("api_llm_health", __name__)

@bp.route("/api/llm/health", methods=["GET"])
def llm_health():
    """Check health of local LLM (Ollama)"""
    try:
        from ollama_client import is_available, get_models, OLLAMA_BASE
        
        if is_available():
            models = get_models()
            return jsonify({
                "success": True,
                "status": "healthy",
                "base_url": OLLAMA_BASE,
                "models": models,
                "model_count": len(models)
            })
        else:
            return jsonify({
                "success": False,
                "status": "unavailable", 
                "base_url": OLLAMA_BASE,
                "models": [],
                "error": "Ollama not running or no models available"
            }), 502
            
    except Exception as e:
        logger.error(f"LLM health check error: {e}")
        return jsonify({
            "success": False,
            "status": "error",
            "error": str(e)
        }), 500

@bp.route("/api/llm/test", methods=["GET"]) 
def llm_test():
    """Test local LLM with a simple query"""
    try:
        from ollama_client import generate_companion_response
        
        test_response = generate_companion_response(
            message="Hello, please respond with just 'Test successful!'",
            character="Blayzo"
        )
        
        return jsonify({
            "success": test_response.get("success", False),
            "response": test_response.get("response", ""),
            "model": test_response.get("model", ""),
            "test_passed": "Test successful" in test_response.get("response", "")
        })
        
    except Exception as e:
        logger.error(f"LLM test error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500