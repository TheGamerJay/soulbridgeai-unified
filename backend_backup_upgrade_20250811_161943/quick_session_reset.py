#!/usr/bin/env python3
"""
Quick session reset server - clears browser session to allow fresh trial
"""

from flask import Flask, session, jsonify, redirect
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'temp-reset-key-123'

@app.route('/reset-session')
def reset_session():
    """Clear all session data to allow fresh trial"""
    session.clear()
    return jsonify({
        "success": True,
        "message": "Session cleared! You can now start a fresh trial.",
        "redirect": "Go back to your main app and try starting trial again"
    })

@app.route('/')
def home():
    return """
    <h1>Session Reset Tool</h1>
    <p><a href="/reset-session">Click here to reset your session</a></p>
    <p>After clicking, go back to your main app and try starting the trial.</p>
    """

if __name__ == '__main__':
    print("Session Reset Server Starting...")
    print("Go to: http://localhost:5555/reset-session")
    app.run(host='0.0.0.0', port=5555, debug=True)