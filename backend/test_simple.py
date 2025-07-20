try:
    import os
    import logging
    from flask import Flask, render_template, request, jsonify, session
    from openai import OpenAI
    from dotenv import load_dotenv

    print("✅ All imports successful")

    # Load environment variables from .env file
    load_dotenv()
    print("✅ Environment loaded")

    # Test OpenAI key
    api_key = os.environ.get("OPENAI_API_KEY")
    print(f"✅ API Key found: {api_key[:10]}..." if api_key else "❌ No API key")

    # Test Flask app creation
    app = Flask(__name__)
    print("✅ Flask app created")

    @app.route("/")
    def test():
        return "SoulBridge AI is working!"

    print("🚀 Starting simple test server...")
    app.run(host="0.0.0.0", port=5000, debug=True)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    input("Press Enter to exit...")
