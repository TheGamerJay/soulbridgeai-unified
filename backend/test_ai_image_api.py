#!/usr/bin/env python3
"""
Test script to diagnose AI image generation API errors
"""
import requests
import json

def test_ai_image_api():
    """Test the AI image generation API to see the actual error"""
    try:
        # Test the usage endpoint first (requires no auth)
        usage_url = "http://127.0.0.1:5000/api/ai-image-generation/usage"
        print("Testing usage endpoint...")
        
        response = requests.get(usage_url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("Authentication required - as expected")
        elif response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test the generation endpoint (will fail due to no auth, but we can see if there are syntax errors)
        gen_url = "http://127.0.0.1:5000/api/ai-image-generation/generate"
        print(f"\nTesting generation endpoint...")
        
        payload = {
            "prompt": "test image",
            "style": "realistic"
        }
        
        response = requests.post(gen_url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("Authentication required - endpoint is reachable")
        elif response.status_code == 500:
            print(f"Server error: {response.text}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    test_ai_image_api()