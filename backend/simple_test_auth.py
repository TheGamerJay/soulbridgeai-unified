#!/usr/bin/env python3
"""Simple Authentication Test for SoulBridge AI"""

import requests
import time

# Test Configuration
BASE_URL = "http://localhost:8080"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_DISPLAY_NAME = "Test User"

def test_registration():
    """Test user registration"""
    print("Testing registration...")
    
    registration_data = {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'confirm_password': TEST_PASSWORD,
        'display_name': TEST_DISPLAY_NAME
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", data=registration_data, allow_redirects=False)
        print(f"Registration response status: {response.status_code}")
        
        if response.status_code == 302:
            print("Registration successful - redirected to login")
            return True
        else:
            print(f"Registration failed with status: {response.status_code}")
            print(f"Response text: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Registration test error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\nTesting login...")
    
    login_data = {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }
    
    try:
        session = requests.Session()
        response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print("Login successful - redirected")
            return True
        else:
            print(f"Login failed with status: {response.status_code}")
            print(f"Response text: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Login test error: {e}")
        return False

if __name__ == "__main__":
    print("SoulBridge AI Authentication Test")
    print("=" * 50)
    
    # Test registration
    reg_success = test_registration()
    
    # Wait a moment
    time.sleep(1)
    
    # Test login
    login_success = test_login()
    
    print("\nTest Results:")
    print(f"Registration: {'PASS' if reg_success else 'FAIL'}")
    print(f"Login: {'PASS' if login_success else 'FAIL'}")