#!/usr/bin/env python3
"""
Script to clean up unwanted models from Ollama and keep only tinyllama
"""
import requests
import os
import json

def cleanup_models():
    """Remove unwanted models and keep only FREE_MODEL"""
    model_name = os.getenv("FREE_MODEL", "tinyllama")
    ollama_url = "http://localhost:11434"
    
    try:
        # Get current models
        print("Checking available models...")
        response = requests.get(f"{ollama_url}/api/tags", timeout=30)
        
        if response.status_code != 200:
            print(f"Failed to get models: {response.status_code}")
            return False
            
        models = response.json().get("models", [])
        print(f"Found {len(models)} models")
        
        for model in models:
            model_full_name = model.get("name", "")
            print(f"Found model: {model_full_name}")
            
            # Keep only the desired model (tinyllama)
            if not model_full_name.startswith(model_name):
                print(f"Removing unwanted model: {model_full_name}")
                delete_response = requests.delete(f"{ollama_url}/api/delete", 
                                                json={"name": model_full_name},
                                                timeout=60)
                if delete_response.status_code == 200:
                    print(f"✓ Removed {model_full_name}")
                else:
                    print(f"✗ Failed to remove {model_full_name}: {delete_response.text}")
            else:
                print(f"✓ Keeping {model_full_name}")
        
        print("Model cleanup complete!")
        return True
        
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    cleanup_models()