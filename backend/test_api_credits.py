#!/usr/bin/env python3
"""
Test the /api/user-credits endpoint to see what it's returning
"""

import requests
import json

def test_api_credits():
    """Test what the API is returning"""
    try:
        # Test the API endpoint
        url = "http://127.0.0.1:5000/api/user-credits"
        
        print("🔍 Testing /api/user-credits endpoint...")
        print(f"URL: {url}")
        
        # Note: This would need proper authentication in a real test
        # For now, this is just to show the structure
        
        print("\\n⚠️ This test requires authentication. To test manually:")
        print("1. Start the Flask app: python app.py")
        print("2. Log into the application in browser")
        print("3. Open browser dev tools > Network tab")
        print("4. Navigate to AI image generation page")
        print("5. Check the /api/user-credits request in Network tab")
        print("6. Look at the response JSON to see actual values")
        
        print("\\n🔧 Or test directly via database:")
        print("Check get_artistic_time() function is working correctly")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_credits()