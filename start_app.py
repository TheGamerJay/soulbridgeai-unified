#!/usr/bin/env python3
"""
Simple app starter that handles environment setup and avoids Unicode issues
"""
import os
import sys
from dotenv import load_dotenv

# Set encoding to handle Unicode properly
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Load environment variables
load_dotenv()

print("Starting SoulBridge AI...")
print(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
print(f"SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")
print(f"DEBUG: {os.getenv('DEBUG', 'False')}")

# Change to backend directory
os.chdir('backend')

# Start the app
try:
    from app import app as flask_app
    print("App module loaded successfully")
    
    # Run the app
    print("Starting Flask development server...")
    flask_app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8080)),
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )
    
except Exception as e:
    print(f"Error starting app: {e}")
    import traceback
    traceback.print_exc()