#!/usr/bin/env python3
"""
Minimal Flask app for Railway testing
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "SoulBridge AI (Minimal)",
                "message": "Minimal app running successfully",
            }
        ),
        200,
    )


@app.route("/")
def home():
    return (
        jsonify({"message": "SoulBridge AI is running", "status": "minimal_mode"}),
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting minimal SoulBridge AI on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
