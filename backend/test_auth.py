#!/usr/bin/env python3
"""
Simple authentication test script for SoulBridge AI
Tests login and registration functionality
"""
import requests
import sys
import json
from urllib.parse import urljoin

def test_auth_endpoints(base_url="http://localhost:8080"):
    """Test authentication endpoints"""
    print(f"Testing authentication endpoints at {base_url}")
    
    # Test data
    test_email = "test@example.com"
    test_password = "testpassword123"
    test_display_name = "Test User"
    
    session = requests.Session()
    
    try:
        # Test 1: Get registration page
        print("\n1. Testing registration page...")
        register_url = urljoin(base_url, "/register")
        response = session.get(register_url)
        if response.status_code == 200:
            print("✅ Registration page loads successfully")
        else:
            print(f"❌ Registration page failed: {response.status_code}")
            return False
        
        # Test 2: Register new user
        print("\n2. Testing user registration...")
        register_post_url = urljoin(base_url, "/auth/register")
        register_data = {
            'email': test_email,
            'password': test_password,
            'confirm_password': test_password,
            'display_name': test_display_name
        }
        
        response = session.post(register_post_url, data=register_data, allow_redirects=False)
        if response.status_code in [302, 303]:  # Redirect expected
            print("✅ Registration successful (redirect received)")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        # Test 3: Get login page
        print("\n3. Testing login page...")
        login_url = urljoin(base_url, "/login")
        response = session.get(login_url)
        if response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        
        # Test 4: Login with registered user
        print("\n4. Testing user login...")
        login_post_url = urljoin(base_url, "/auth/login")
        login_data = {
            'email': test_email,
            'password': test_password
        }
        
        response = session.post(login_post_url, data=login_data, allow_redirects=False)
        if response.status_code in [302, 303]:  # Redirect expected
            print("✅ Login successful (redirect received)")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        # Test 5: Access protected page
        print("\n5. Testing protected page access...")
        chat_url = urljoin(base_url, "/chat")
        response = session.get(chat_url, allow_redirects=False)
        if response.status_code == 200:
            print("✅ Protected page accessible after login")
        elif response.status_code in [302, 303]:
            # Check if redirected to login
            location = response.headers.get('Location', '')
            if 'login' in location:
                print("❌ Still redirected to login - session not working")
                return False
            else:
                print("✅ Redirected to allowed page")
        else:
            print(f"❌ Protected page access failed: {response.status_code}")
            return False
        
        # Test 6: Test logout
        print("\n6. Testing logout...")
        logout_url = urljoin(base_url, "/auth/logout")
        response = session.get(logout_url, allow_redirects=False)
        if response.status_code in [302, 303]:
            print("✅ Logout successful (redirect received)")
        else:
            print(f"❌ Logout failed: {response.status_code}")
            return False
        
        # Test 7: Verify logout worked
        print("\n7. Testing access after logout...")
        response = session.get(chat_url, allow_redirects=False)
        if response.status_code in [302, 303]:
            location = response.headers.get('Location', '')
            if 'login' in location:
                print("✅ Redirected to login after logout - logout working")
            else:
                print(f"❌ Unexpected redirect after logout: {location}")
                return False
        else:
            print(f"❌ Should be redirected to login after logout: {response.status_code}")
            return False
        
        print("\n🎉 All authentication tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {base_url}")
        print("Make sure the SoulBridge AI server is running")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_validation():
    """Test form validation"""
    print("\n🧪 Testing form validation...")
    base_url = "http://localhost:8080"
    
    session = requests.Session()
    register_post_url = urljoin(base_url, "/auth/register")
    
    # Test invalid email
    print("\n1. Testing invalid email...")
    response = session.post(register_post_url, data={
        'email': 'invalid-email',
        'password': 'password123',
        'confirm_password': 'password123',
        'display_name': 'Test User'
    }, allow_redirects=True)
    
    if "valid email" in response.text.lower():
        print("✅ Invalid email validation working")
    else:
        print("❌ Invalid email validation not working")
    
    # Test password mismatch
    print("\n2. Testing password mismatch...")
    response = session.post(register_post_url, data={
        'email': 'test2@example.com',
        'password': 'password123',
        'confirm_password': 'different123',
        'display_name': 'Test User'
    }, allow_redirects=True)
    
    if "do not match" in response.text.lower():
        print("✅ Password mismatch validation working")
    else:
        print("❌ Password mismatch validation not working")
    
    # Test short password
    print("\n3. Testing short password...")
    response = session.post(register_post_url, data={
        'email': 'test3@example.com',
        'password': '123',
        'confirm_password': '123',
        'display_name': 'Test User'
    }, allow_redirects=True)
    
    if "8 characters" in response.text.lower():
        print("✅ Short password validation working")
    else:
        print("❌ Short password validation not working")

if __name__ == "__main__":
    print("🚀 SoulBridge AI Authentication Test Suite")
    print("=" * 50)
    
    # Run main authentication tests
    success = test_auth_endpoints()
    
    # Run validation tests
    test_validation()
    
    if success:
        print("\n✅ Authentication system is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Authentication system has issues that need to be fixed")
        sys.exit(1)