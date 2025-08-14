"""
Ollama Admin API Route
Allows manual model management
"""
import logging
import os
import requests
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('api_ollama_admin', __name__)

@bp.route("/api/ollama/pull-model", methods=['GET', 'POST'])
def pull_model():
    """Manually pull phi3:mini model to Ollama"""
    try:
        ollama_base = os.getenv("LLM_BASE", "http://ollama:11434")
        model_name = os.getenv("FREE_COMPANION_MODEL", "phi3:mini")
        
        logger.info(f"Attempting to pull model {model_name} from {ollama_base}")
        
        # Send pull request to Ollama
        response = requests.post(
            f"{ollama_base}/api/pull",
            json={"name": model_name},
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully triggered pull for {model_name}")
            return jsonify({
                "success": True,
                "message": f"Model {model_name} pull initiated",
                "model": model_name,
                "ollama_base": ollama_base
            })
        else:
            logger.error(f"Failed to pull model: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"Pull failed: {response.status_code} - {response.text}",
                "model": model_name,
                "ollama_base": ollama_base
            }), 500
            
    except Exception as e:
        logger.error(f"Error pulling model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/api/ollama/status", methods=['GET'])
def ollama_status():
    """Check Ollama status and available models"""
    try:
        ollama_base = os.getenv("LLM_BASE", "http://ollama:11434")
        
        # Check available models
        response = requests.get(f"{ollama_base}/api/tags", timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                "success": True,
                "ollama_base": ollama_base,
                "models": response.json(),
                "status": "connected"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Ollama not responding: {response.status_code}",
                "ollama_base": ollama_base,
                "status": "disconnected"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "error"
        }), 500