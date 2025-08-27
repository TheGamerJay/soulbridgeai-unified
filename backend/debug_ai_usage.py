#!/usr/bin/env python3
"""
Debug script to check AI image usage session data
"""
import requests
import json

def debug_ai_usage():
    """Debug AI image usage API"""
    try:
        # Test the usage endpoint to see what it actually returns
        usage_url = "http://127.0.0.1:5000/api/ai-image-generation/usage"
        print("🔍 Debugging AI image usage endpoint...")
        
        # First test without auth (should get 401)
        response = requests.get(usage_url)
        print(f"No auth - Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Endpoint requires authentication as expected")
            
        # For actual testing, we'd need to be logged in with a real session
        # The user should test this directly in their browser developer console
        
        print("\n📝 To debug this issue, run this in browser console while logged in:")
        print("fetch('/api/ai-image-generation/usage', { credentials: 'include' }).then(r => r.json()).then(console.log)")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    debug_ai_usage()