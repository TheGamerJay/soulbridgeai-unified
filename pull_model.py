#!/usr/bin/env python3
"""
Script to manually pull phi3:mini model to Ollama service
Run this after basic Ollama service is running
"""
import requests
import time

def pull_model():
    """Pull phi3:mini model to Ollama service"""
    ollama_url = "http://ollama:11434"  # Internal Railway URL
    
    print("Pulling phi3:mini model...")
    
    response = requests.post(f"{ollama_url}/api/pull", 
                           json={"name": "phi3:mini"},
                           timeout=300)  # 5 minute timeout
    
    if response.status_code == 200:
        print("Model pull successful!")
        return True
    else:
        print(f"Model pull failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    pull_model()