"""
Quick test script to verify SoulBridge AI Backend setup
"""
import os
import sys
from dotenv import load_dotenv

def check_setup():
    print("🔍 SoulBridge AI Backend Setup Check")
    print("=" * 40)
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        load_dotenv()
    else:
        print("❌ .env file not found")
        return False
    
    # Check OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        print("✅ OpenAI API key configured")
    else:
        print("❌ OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in .env file")
    
    # Check session secret
    session_secret = os.environ.get('SESSION_SECRET')
    if session_secret and session_secret != 'your_session_secret_here':
        print("✅ Session secret configured")
    else:
        print("⚠️  Session secret using default value")
        print("   Consider setting SESSION_SECRET in .env file")
    
    # Check required packages
    try:
        import flask
        print("✅ Flask installed")
    except ImportError:
        print("❌ Flask not installed")
        print("   Run: pip install flask")
    
    try:
        import openai
        print("✅ OpenAI package installed")
    except ImportError:
        print("❌ OpenAI package not installed")
        print("   Run: pip install openai")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Run: pip install python-dotenv")
    
    print("\n🚀 To start the server, run:")
    print("   python app.py")
    print("\n📱 Then open: http://localhost:5000")

if __name__ == "__main__":
    check_setup()
