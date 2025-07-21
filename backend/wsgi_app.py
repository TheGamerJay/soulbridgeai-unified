#!/usr/bin/env python3
"""
WSGI-compatible SoulBridge AI App for Gunicorn deployment
Fixes eventlet monkey patching and application context issues
"""

# CRITICAL: eventlet monkey patching MUST be first
import eventlet
eventlet.monkey_patch()

import os
import sys
import logging
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, session, redirect

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Flask app
def create_app():
    """Factory function to create Flask app"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "railway-production-secret-key-2024")
    
    # Global variables for services
    app.services = {
        "database": None,
        "openai": None, 
        "email": None,
        "socketio": None
    }
    
    @app.route("/health")
    def health():
        """Production health check with service status"""
        return jsonify({
            "status": "healthy",
            "service": "SoulBridge AI", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {name: service is not None for name, service in app.services.items()}
        }), 200

    @app.route("/")
    def home():
        """Home route"""
        try:
            # Initialize services if needed
            with app.app_context():
                if not app.services["database"]:
                    init_services_lazy(app)
                return render_template("chat.html")
        except Exception as e:
            logger.error(f"Home route error: {e}")
            return jsonify({"error": "Service temporarily unavailable", "details": str(e)}), 503

    @app.route("/login")
    def login():
        """Login route"""
        try:
            return render_template("login.html")
        except Exception as e:
            logger.error(f"Login template error: {e}")
            return jsonify({"error": "Login page temporarily unavailable"}), 200

    @app.route("/register")  
    def register():
        """Register route"""
        try:
            return render_template("register.html")
        except Exception as e:
            logger.error(f"Register template error: {e}")
            return jsonify({"error": "Register page temporarily unavailable"}), 200

    @app.route("/subscription")
    def subscription():
        """Subscription route"""
        try:
            return render_template("subscription.html")
        except Exception as e:
            logger.error(f"Subscription template error: {e}")
            return jsonify({"error": "Subscription page temporarily unavailable"}), 200

    @app.route("/profile")
    def profile():
        """Profile route"""
        try:
            if not session.get("user_authenticated", False):
                return redirect("/login")
            return render_template("profile.html")
        except Exception as e:
            logger.error(f"Profile template error: {e}")
            return jsonify({"error": "Profile page temporarily unavailable"}), 200

    # API routes
    @app.route("/api/select-plan", methods=["POST"])
    def select_plan():
        """Plan selection API"""
        try:
            data = request.get_json()
            plan_type = data.get("plan_type", "foundation")
            
            session["user_plan"] = plan_type
            session["plan_selected_at"] = time.time()
            session["first_time_user"] = False
            
            return jsonify({
                "success": True,
                "plan": plan_type,
                "redirect": "/"
            })
        except Exception as e:
            logger.error(f"Plan selection error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app

def init_services_lazy(app):
    """Initialize services lazily when needed"""
    try:
        logger.info("🚀 Lazy initializing services...")
        
        # Database
        if not app.services["database"]:
            try:
                from auth import Database
                app.services["database"] = Database()
                logger.info("✅ Database initialized")
            except Exception as e:
                logger.error(f"❌ Database failed: {e}")
        
        # OpenAI
        if not app.services["openai"] and os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                app.services["openai"] = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI failed: {e}")
        
        # Email
        if not app.services["email"]:
            try:
                from email_service import EmailService
                app.services["email"] = EmailService()
                logger.info("✅ Email service initialized")
            except Exception as e:
                logger.error(f"❌ Email service failed: {e}")
        
        working = sum(1 for service in app.services.values() if service is not None)
        logger.info(f"📊 Services operational: {working}/3")
        
    except Exception as e:
        logger.error(f"Service initialization error: {e}")

# Create the app instance for Gunicorn
app = create_app()

# For direct execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI WSGI on port {port}")
    logger.info(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    with app.app_context():
        init_services_lazy(app)
    
    logger.info("🌟 Starting Flask server...")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)