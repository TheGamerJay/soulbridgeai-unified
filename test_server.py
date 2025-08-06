#!/usr/bin/env python3
"""
Quick test to check if our changes are working
"""
import requests
import time

def test_server():
    try:
        # Test if server is running
        response = requests.get('http://localhost:5000/', timeout=5)
        print(f"✅ Server is running on port 5000")
        print(f"Response status: {response.status_code}")
        
        # Check if it has our companion image fix
        if "companion_avatar" in response.text:
            print("✅ Server has companion image fix")
        else:
            print("❌ Server missing companion image fix")
            
        # Check if it has our timer fix
        if "Math.floor(trial_remaining / 3600)" in response.text:
            print("✅ Server has timer fix")
        else:
            print("❌ Server missing timer fix")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server on port 5000: {e}")
        
    try:
        # Test port 8080 too
        response = requests.get('http://localhost:8080/', timeout=5)
        print(f"✅ Server is also running on port 8080")
        print(f"Response status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server on port 8080: {e}")

if __name__ == "__main__":
    test_server()