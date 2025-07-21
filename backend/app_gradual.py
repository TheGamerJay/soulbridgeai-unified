#!/usr/bin/env python3
"""
Gradual restoration of SoulBridge AI functionality
Step-by-step approach to identify problematic components
"""
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
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "railway-production-secret-key-2024")

# Global variables for services
services = {
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
        "services": {name: service is not None for name, service in services.items()}
    }), 200

@app.route("/")
def home():
    """Home route with gradual loading"""
    try:
        # Try to serve the main template
        return render_template("chat.html")
    except Exception as e:
        logger.error(f"Template error: {e}")
        return jsonify({
            "service": "SoulBridge AI", 
            "status": "template_error",
            "message": "Chat interface temporarily unavailable",
            "error": str(e)
        }), 200

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

def init_database():
    """Initialize database with error handling"""
    try:
        logger.info("Initializing database...")
        from models import DatabaseManager
        services["database"] = DatabaseManager()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        services["database"] = None
        return False

def init_openai():
    """Initialize OpenAI with error handling"""
    try:
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("OpenAI API key not provided")
            return False
            
        logger.info("Initializing OpenAI...")
        import openai
        services["openai"] = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        logger.info("✅ OpenAI initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI initialization failed: {e}")
        services["openai"] = None
        return False

def init_email():
    """Initialize email service with error handling"""
    try:
        logger.info("Initializing email service...")
        from email_service import EmailService
        services["email"] = EmailService()
        logger.info("✅ Email service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Email service initialization failed: {e}")
        services["email"] = None
        return False

def init_socketio():
    """Initialize SocketIO with error handling"""
    try:
        logger.info("Initializing SocketIO...")
        from flask_socketio import SocketIO
        services["socketio"] = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
        logger.info("✅ SocketIO initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ SocketIO initialization failed: {e}")
        services["socketio"] = None
        return False

def initialize_services():
    """Initialize all services with graceful fallback"""
    logger.info("🚀 Starting SoulBridge AI service initialization...")
    
    # Initialize in order of dependency
    init_functions = [
        ("Database", init_database),
        ("OpenAI", init_openai), 
        ("Email", init_email),
        ("SocketIO", init_socketio),
    ]
    
    results = {}
    for service_name, init_func in init_functions:
        try:
            results[service_name] = init_func()
        except Exception as e:
            logger.error(f"Service {service_name} initialization crashed: {e}")
            results[service_name] = False
    
    # Log results
    working = sum(results.values())
    total = len(results)
    logger.info(f"📊 Service initialization complete: {working}/{total} services operational")
    
    for service_name, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"  {service_name}: {status}")
    
    return results

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting SoulBridge AI on port {port}")
    logger.info(f"Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    # Initialize services but don't fail if they don't work
    service_results = initialize_services()
    
    # Start the server regardless of service status
    logger.info("🌟 Starting Flask server...")
    app.run(
        host="0.0.0.0",
        port=port, 
        debug=False,
        threaded=True,
        use_reloader=False
    )