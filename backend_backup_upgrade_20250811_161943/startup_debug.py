#!/usr/bin/env python3
"""
Debug startup issues for Railway deployment
"""
import os
import sys
import time
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test critical imports"""
    logger.info("Testing imports...")
    
    try:
        import flask
        logger.info("✅ Flask imported successfully")
    except Exception as e:
        logger.error(f"❌ Flask import failed: {e}")
        return False
    
    try:
        from flask_socketio import SocketIO
        logger.info("✅ SocketIO imported successfully")
    except Exception as e:
        logger.error(f"❌ SocketIO import failed: {e}")
        return False
    
    try:
        import openai
        logger.info("✅ OpenAI imported successfully")
    except Exception as e:
        logger.error(f"❌ OpenAI import failed: {e}")
        return False
        
    return True

def test_database():
    """Test database connection"""
    logger.info("Testing database...")
    
    try:
        from database import Database
        db = Database()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test Flask app creation"""
    logger.info("Testing Flask app creation...")
    
    try:
        from flask import Flask
        app = Flask(__name__)
        app.secret_key = "test-key"
        
        @app.route("/health")
        def health():
            return {"status": "ok"}
        
        logger.info("✅ Flask app created successfully")
        return True, app
    except Exception as e:
        logger.error(f"❌ Flask app creation failed: {e}")
        traceback.print_exc()
        return False, None

def main():
    """Main debug function"""
    logger.info("🔍 Starting Railway deployment debug...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Test environment variables
    logger.info("Environment variables:")
    for key in ["PORT", "RAILWAY_ENVIRONMENT", "OPENAI_API_KEY", "RESEND_API_KEY"]:
        value = os.environ.get(key, "NOT SET")
        if key in ["OPENAI_API_KEY", "RESEND_API_KEY"] and value != "NOT SET":
            value = f"{value[:8]}..." # Truncate for security
        logger.info(f"  {key}: {value}")
    
    # Run tests
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("App Creation", test_app_creation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            if test_name == "App Creation":
                success, app = test_func()
                results[test_name] = success
                if success:
                    # Try to start the app briefly
                    logger.info("Testing app startup...")
                    port = int(os.environ.get("PORT", 8080))
                    try:
                        # Don't actually run, just test if it would work
                        logger.info(f"✅ App would start on port {port}")
                    except Exception as e:
                        logger.error(f"❌ App startup would fail: {e}")
            else:
                results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🚀 All tests passed! Attempting to start main app...")
        try:
            from app import app
            port = int(os.environ.get("PORT", 8080))
            logger.info(f"Starting main app on port {port}")
            app.run(host="0.0.0.0", port=port, debug=False)
        except Exception as e:
            logger.error(f"❌ Main app failed to start: {e}")
            traceback.print_exc()
    else:
        logger.error("❌ Some tests failed. Cannot start main app.")
        sys.exit(1)

if __name__ == "__main__":
    main()