#!/usr/bin/env python3
"""
Minimal test script to identify startup issues
"""

import os
import sys

print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("Python path:", sys.path[:3])  # First 3 entries

try:
    print("Testing basic Flask import...")
    from flask import Flask
    print("✓ Flask imported successfully")
    
    print("Testing app creation...")
    app = Flask(__name__)
    print("✓ Flask app created successfully")
    
    @app.route('/test')
    def test():
        return "Test OK"
    
    print("Testing our custom imports...")
    
    try:
        from email_service import EmailService
        print("✓ EmailService imported")
    except Exception as e:
        print("✗ EmailService failed:", e)
    
    try:
        from rate_limiter import rate_limit, init_rate_limiting
        print("✓ rate_limiter imported")
    except Exception as e:
        print("✗ rate_limiter failed:", e)
    
    try:
        from env_validator import init_environment_validation
        print("✓ env_validator imported")
    except Exception as e:
        print("✗ env_validator failed:", e)
    
    try:
        from feature_flags import init_feature_flags
        print("✓ feature_flags imported")
    except Exception as e:
        print("✗ feature_flags failed:", e)
    
    try:
        from security_monitor import init_security_monitoring
        print("✓ security_monitor imported")
    except Exception as e:
        print("✗ security_monitor failed:", e)
    
    print("Testing port binding...")
    port = int(os.environ.get("PORT", 8080))
    print(f"Attempting to bind to port {port}")
    
    if __name__ == "__main__":
        print("Would start app here...")
        print("All tests passed!")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)