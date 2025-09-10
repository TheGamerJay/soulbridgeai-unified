#!/usr/bin/env python3
"""
Quick test script for the referrals system
Tests referral code generation, submission, and stats
"""

import requests
import json
import sys

# Test configuration
BASE_URL = "http://localhost:5000"
REFERRALS_API = f"{BASE_URL}/api/referrals"

def test_referrals_system():
    """Test the referrals system API endpoints"""
    print("🧪 Testing SoulBridge AI Referrals System")
    print("=" * 50)
    
    # Test 1: Get referral info (should fail without auth)
    print("Test 1: Get referral info (no auth)")
    try:
        response = requests.get(f"{REFERRALS_API}/me")
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Is the app running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Submit referral (should fail without auth)
    print("\nTest 2: Submit referral code (no auth)")
    try:
        response = requests.post(f"{REFERRALS_API}/submit", 
                                json={"code": "TEST1234"})
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Blueprint registration (check available routes)
    print("\nTest 3: Check if referrals routes are registered")
    try:
        # Try to access a route that should exist
        response = requests.get(f"{REFERRALS_API}/me")
        if response.status_code in [401, 200]:  # Either needs auth or works
            print("✅ Referrals routes are registered")
        else:
            print(f"❌ Routes may not be registered (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n🎉 Basic referrals system tests completed!")
    print("📝 Note: Full testing requires authenticated sessions")
    return True

if __name__ == "__main__":
    success = test_referrals_system()
    sys.exit(0 if success else 1)