"""
Free Companion API Route
Provides direct Ollama access for free users
"""
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('api_companion_free', __name__)

def j_ok(**kwargs):
    """Helper for successful JSON responses"""
    return jsonify({"success": True, **kwargs})

def j_err(message, status=400):
    """Helper for error JSON responses"""
    return jsonify({"success": False, "error": message}), status

@bp.route("/api/companion/free", methods=['GET', 'POST'])
def companion_free():
    """Free companion endpoint that uses local Ollama directly"""
    data = request.get_json(force=True, silent=True) or {}
    msgs = data.get("messages") or []
    if not msgs: 
        return j_err("Provide chat 'messages' list", 400)

    SYSTEM = ("You are a warm, supportive wellness companion named SoulBridge. "
              "Be empathetic and practical. No medical/legal advice.")
    msgs = [{"role":"system","content": SYSTEM}] + msgs

    try:
        from ollama_client import chat
        text = chat(msgs, model="phi3:mini", max_tokens=220)
        return j_ok(reply=text, source="local", model="phi3:mini")
    except Exception as e:
        logger.error(f"Free companion error: {e}")
        return j_err(f"Local AI unavailable: {str(e)}", 500)