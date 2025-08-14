"""
Minimal Ollama client for local AI responses
"""
import os
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def _default_base():
    # Default to localhost for embedded Ollama setup
    return "http://localhost:11434"

OLLAMA_BASE = (
    os.getenv("DEBUG_OLLAMA_BASE")
    or os.getenv("LLM_BASE")
    or os.getenv("OLLAMA_BASE") 
    or os.getenv("OLLAMA_URL")
    or _default_base()
)

FREE_MODEL = os.getenv("FREE_MODEL", "tinyllama")

# Default options for CPU-only inference - absolutely minimal
DEFAULT_OPTIONS = {
    "num_ctx": 32,    # Tiny context window
    "num_keep": 1,    # Keep almost nothing
    "num_predict": 3, # Only 3 tokens (like "4")
    "temperature": 0.0,  # No randomness at all
    "repeat_penalty": 1.0,  # No penalty
    "num_batch": 1,   # Process one token at a time
    "num_gqa": 1,     # Single group query attention
    "num_gpu": 0,     # Force CPU-only
    "main_gpu": -1,   # No GPU
}

def chat(messages: List[Dict[str, str]], model: str = None, options: dict = None) -> str:
    """
    Minimal Ollama chat client. Expects OpenAI-style messages:
    [{'role':'system'|'user'|'assistant','content':'...'}, ...]
    """
    model = model or FREE_MODEL
    
    try:
        # Use Ollama chat endpoint - generate endpoint doesn't exist
        url = f"{OLLAMA_BASE}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "5m",  # Shorter keep alive
            "options": {**DEFAULT_OPTIONS, **(options or {})}
        }
        
        logger.info(f"Sending request to Ollama: {url} with model: {model}")
        logger.info(f"Messages: {messages}")
        r = requests.post(url, json=payload, timeout=120)  # Give CPU more time
        r.raise_for_status()
        
        data = r.json()
        # Ollama chat API returns message.content
        response = data.get("message", {}).get("content", "").strip()
        logger.info(f"Ollama response received: {len(response)} characters")
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise Exception(f"Ollama unavailable: {e}")
    except Exception as e:
        logger.error(f"Ollama chat error: {e}")
        raise

def is_available() -> bool:
    """Check if Ollama is running and has models"""
    try:
        logger.info(f"Testing Ollama connection to: {OLLAMA_BASE}")
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        logger.info(f"Ollama response status: {r.status_code}")
        if r.status_code != 200:
            logger.warning(f"Ollama returned status {r.status_code}")
            return False
        models = r.json().get("models", [])
        logger.info(f"Ollama models found: {[m.get('name') for m in models]}")
        return len(models) > 0
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        return False

def get_models() -> List[str]:
    """Get list of available models"""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m.get("name") for m in r.json().get("models", [])]
        return models
    except:
        return []

def generate_companion_response(message: str, character: str = "Blayzo", context: str = "") -> Dict[str, Any]:
    """Generate a companion response using Ollama"""
    
    # Character-specific system prompts
    character_prompts = {
        "Blayzo": "You are Blayzo, a warm and supportive AI companion from SoulBridge AI. You're empathetic, understanding, and always ready to listen. Provide thoughtful, caring responses that help users feel heard and supported.",
        "Blayzica": "You are Blayzica, a wise and spiritually-minded AI companion from SoulBridge AI. You have a gentle, mystical personality and offer deep insights with compassion. You speak with wisdom and grace.",
        "Crimson": "You are Crimson, an energetic and action-oriented AI companion from SoulBridge AI. You're passionate about helping people overcome challenges and achieve their goals. You're motivational and solution-focused."
    }
    
    system_prompt = character_prompts.get(character, character_prompts["Blayzo"])
    system_prompt += " Keep your responses conversational, supportive, and under 200 words. Be genuine and avoid being overly formal."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    if context:
        messages.insert(1, {"role": "assistant", "content": f"Context: {context}"})
    
    try:
        response = chat(messages, max_tokens=250)
        return {
            "success": True,
            "response": response,
            "model": "ollama_local",
            "character": character,
            "provider": "local"
        }
    except Exception as e:
        logger.error(f"Ollama companion response failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_recommended": True
        }

if __name__ == "__main__":
    # Test the client
    print("Testing Ollama client...")
    print("Available:", is_available())
    print("Models:", get_models())
    
    if is_available():
        test_response = generate_companion_response("Hello, how are you?", "Blayzo")
        print("Test response:", test_response)