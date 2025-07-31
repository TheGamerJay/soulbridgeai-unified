import os
from app import app

if __name__ == "__main__":
    # Development configuration
    app.config["DEBUG"] = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    port = int(os.environ.get("PORT", 5000))
    print(f"\nSoulBridge AI Backend starting on http://localhost:{port}")
    print("Make sure your OPENAI_API_KEY is set in the .env file")
    print("Press Ctrl+C to stop the server\n")

    app.run(host="0.0.0.0", port=port, debug=True)
