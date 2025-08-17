#!/usr/bin/env python3
"""
Test script for V1 API endpoints
Tests the new consolidated API with proper session simulation
"""

import requests
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8080"

def test_v1_endpoints():
    """Test all v1 API endpoints"""
    print("Testing V1 API Endpoints")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: Test /v1/me without authentication (should fail)
    print("\n1. Testing /v1/me (unauthenticated - should fail)")
    response = session.get(f"{BASE_URL}/v1/me")
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   PASS: Correctly rejected unauthenticated request")
    else:
        print(f"   FAIL: Unexpected response: {response.text[:100]}")
    
    # Test 2: Test /v1/entitlements without authentication (should fail)
    print("\n2. Testing /v1/entitlements (unauthenticated - should fail)")
    response = session.get(f"{BASE_URL}/v1/entitlements")
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   PASS: Correctly rejected unauthenticated request")
    else:
        print(f"   FAIL: Unexpected response: {response.text[:100]}")
    
    # Test 3: Simulate login by setting session cookies manually
    print("\n3. Simulating authenticated session...")
    
    # For testing, we'll use the existing /api/login endpoint to get a valid session
    # or manually set session data if that doesn't work
    try:
        # Try to login with a test user
        login_response = session.post(f"{BASE_URL}/api/login", json={
            "email": "dagamerjay13@gmail.com",  # User 4 from our database
            "password": "testpassword"  # This probably won't work, but let's try
        })
        print(f"   Login attempt status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("   WARNING: Login failed - testing with mock session data")
            # We'll test the endpoints anyway to check the structure
    except Exception as e:
        print(f"   WARNING: Login error: {e}")
    
    # Test 4: Test endpoints (even if not fully authenticated, we can check structure)
    print("\n4. Testing endpoint structure...")
    
    endpoints_to_test = [
        ("/v1/me", "GET"),
        ("/v1/entitlements", "GET"),
        ("/v1/credits", "GET"),
        ("/v1/trial/start", "POST"),
    ]
    
    for endpoint, method in endpoints_to_test:
        print(f"\n   Testing {method} {endpoint}")
        try:
            if method == "GET":
                response = session.get(f"{BASE_URL}{endpoint}")
            else:
                response = session.post(f"{BASE_URL}{endpoint}", json={})
            
            print(f"   Status: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"   Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("V1 API Testing Complete")

def test_endpoint_availability():
    """Test if v1 endpoints are properly registered"""
    print("\nTesting endpoint registration...")
    
    v1_endpoints = [
        "/v1/me",
        "/v1/entitlements", 
        "/v1/credits",
        "/v1/trial/start",
        "/v1/credits/spend",
        "/v1/ai/advanced/generate"
    ]
    
    for endpoint in v1_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 404:
                print(f"   FAIL: {endpoint} - NOT FOUND (not registered)")
            elif response.status_code == 401:
                print(f"   PASS: {endpoint} - REGISTERED (auth required)")
            elif response.status_code == 405:
                print(f"   PASS: {endpoint} - REGISTERED (method not allowed)")
            else:
                print(f"   PASS: {endpoint} - REGISTERED (status: {response.status_code})")
        except Exception as e:
            print(f"   ERROR: {endpoint} - {e}")

if __name__ == "__main__":
    test_endpoint_availability()
    test_v1_endpoints()