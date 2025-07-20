#!/usr/bin/env python3
"""
Minimal SoulBridge AI Flask App for Railway deployment
This version focuses on core functionality and reliable startup
"""

import os
import logging
from flask import Flask, jsonify, send_from_directory, make_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app with React build folder
app = Flask(
    __name__,
    static_folder="../frontend/build",
    static_url_path="",
    template_folder="templates",
)

app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


# CORS handling
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


# Health check endpoint
@app.route("/health")
def health():
    """Health check for Railway"""
    return jsonify(
        {
            "status": "healthy",
            "service": "SoulBridge AI",
            "version": "1.0.0",
            "timestamp": "2025-01-19",
        }
    )


# API test endpoint
@app.route("/api/test")
def api_test():
    """Test API endpoint"""
    return jsonify({"message": "SoulBridge AI API is working!", "status": "success"})


# Simple chat endpoint (fallback responses)
@app.route("/api/chat", methods=["POST"])
def chat():
    """Basic chat endpoint with fallback responses"""
    try:
        from flask import request

        data = request.get_json() or {}
        message = data.get("message", "")
        character = data.get("character", "Blayzo")

        # Fallback responses when OpenAI is not available
        responses = {
            "Blayzo": [
                "I hear you, and I'm here to support you through whatever you're facing.",
                "That's an interesting perspective. Tell me more about how you're feeling.",
                "I appreciate you sharing that with me. How can I help you work through this?",
                "Your thoughts and feelings are valid. What would help you most right now?",
            ],
            "Blayzica": [
                "Hey! I'm so glad you reached out to me. What's on your mind?",
                "That sounds like you've got a lot going on. I'm here to listen!",
                "I love that you're sharing this with me. Let's figure this out together!",
                "You're doing great by talking about this. What feels most important to you?",
            ],
        }

        import random

        character_responses = responses.get(character, responses["Blayzo"])
        reply = random.choice(character_responses)

        return jsonify({"reply": reply, "character": character, "status": "success"})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return (
            jsonify(
                {
                    "reply": "I'm having trouble right now, but I'm still here for you!",
                    "status": "error",
                }
            ),
            500,
        )


# React Frontend Serving Routes
@app.route("/")
def serve_react_app():
    """Serve the React app's index.html"""
    try:
        return send_from_directory(app.static_folder, "index.html")
    except Exception as e:
        logger.error(f"Error serving React app: {e}")
        return (
            jsonify(
                {
                    "error": "Frontend not available",
                    "message": "The React frontend couldn't be loaded",
                }
            ),
            500,
        )


@app.route("/<path:path>")
def serve_react_static(path):
    """Serve React static files or fallback to index.html for client-side routing"""
    try:
        # Handle Google verification file specifically
        if path == "googlea4d68d68f81c1843.html":
            response = make_response(
                "google-site-verification: googlea4d68d68f81c1843.html"
            )
            response.headers["Content-Type"] = "text/plain"
            return response

        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            # For client-side routing, always return index.html
            return send_from_directory(app.static_folder, "index.html")
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI (minimal) on port {port}")
    logger.info("Running in safe mode with fallback responses")
    app.run(host="0.0.0.0", port=port, debug=False)
