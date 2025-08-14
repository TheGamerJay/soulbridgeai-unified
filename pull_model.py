#!/usr/bin/env python3
"""
Script to manually pull model to Ollama service
Run this after basic Ollama service is running
"""
import requests
import time
import os

def pull_model():
    """Pull model to Ollama service using FREE_MODEL environment variable"""
    model_name = os.getenv("FREE_MODEL", "tinyllama")
    ollama_url = "http://localhost:11434"  # Use localhost for embedded setup
    
    print(f"Pulling {model_name} model...")
    
    response = requests.post(f"{ollama_url}/api/pull", 
                           json={"name": model_name},
                           timeout=300)  # 5 minute timeout
    
    if response.status_code == 200:
        print("Model pull successful!")
        return True
    else:
        print(f"Model pull failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    pull_model()