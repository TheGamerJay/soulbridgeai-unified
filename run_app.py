#!/usr/bin/env python3
"""
App runner that bypasses Unicode issues and starts the Flask app
"""
import os
import sys
from dotenv import load_dotenv

# Set proper encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# Change to project directory first
os.chdir('C:/Users/jaaye/OneDrive/Desktop/soulbridgeai-unified')

# Load environment from correct path
load_dotenv('.env')

# Change to backend directory
os.chdir('backend')

print("Starting SoulBridge AI...")
print(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
print(f"SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")

# Suppress Unicode output by redirecting stdout temporarily
import io
from contextlib import redirect_stdout, redirect_stderr

# Capture the imports to avoid Unicode print statements
print("Loading app modules...")
with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
    try:
        # Import the app module - this will trigger all the Unicode prints
        import app
        print("App loaded successfully!")
    except Exception as e:
        print(f"Error loading app: {e}")
        sys.exit(1)

# Now run the app
try:
    print("Starting Flask server on port 8080...")
    port = int(os.environ.get("PORT", 8080))
    
    # Start the Flask app directly - services will initialize on first request
    app.app.run(
        host="0.0.0.0", 
        port=port, 
        debug=os.getenv('DEBUG', 'False').lower() == 'true',
        threaded=True,
        use_reloader=False
    )
    
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error running app: {e}")
    import traceback
    traceback.print_exc()