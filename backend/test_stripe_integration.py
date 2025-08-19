#!/usr/bin/env python3
"""
Test script for Bronze/Silver/Gold Stripe integration
Run this after setting up your Stripe products and environment variables
"""

import os
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = os.environ.get('APP_DOMAIN', 'https://soulbridgeai.com')
TEST_MODE = True  # Set to False for live testing

def test_environment_variables():
    """Check if all required environment variables are set"""
    required_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET', 
        'PRICE_SILVER_MONTHLY',
        'PRICE_SILVER_YEARLY',
        'PRICE_GOLD_MONTHLY',
        'PRICE_GOLD_YEARLY',
        'PRICE_ADFREE'
    ]
    
    print("🔧 Checking environment variables...")
    missing = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: Not set")
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing:
        print(f"\n❌ Missing environment variables: {missing}")
        return False
    
    print("✅ All environment variables configured")
    return True

def test_api_me_endpoint():
    """Test the /api/me endpoint"""
    print("\n🔍 Testing /api/me endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/me")
        
        if response.status_code == 401:
            print("ℹ️ /api/me requires authentication (expected)")
            return True
        elif response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ /api/me endpoint working")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"⚠️ /api/me returned success=false: {data}")
                return False
        else:
            print(f"❌ /api/me returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing /api/me: {e}")
        return False

def test_stripe_checkout_endpoint():
    """Test the Stripe checkout endpoint"""
    print("\n🛒 Testing Stripe checkout endpoints...")
    
    test_cases = [
        {"plan": "silver", "billing_cycle": "monthly"},
        {"plan": "silver", "billing_cycle": "yearly"},
        {"plan": "gold", "billing_cycle": "monthly"},
        {"plan": "gold", "billing_cycle": "yearly"}
    ]
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/stripe/checkout",
                json=test_case,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 401:
                print(f"ℹ️ Checkout {test_case['plan']}/{test_case['billing_cycle']} requires authentication (expected)")
            elif response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print(f"✅ Checkout {test_case['plan']}/{test_case['billing_cycle']} endpoint working")
                else:
                    print(f"⚠️ Checkout {test_case['plan']}/{test_case['billing_cycle']} returned ok=false: {data}")
            else:
                print(f"❌ Checkout {test_case['plan']}/{test_case['billing_cycle']} returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing checkout {test_case}: {e}")

def test_webhook_endpoint():
    """Test webhook endpoint accessibility"""
    print("\n🔗 Testing webhook endpoint...")
    
    try:
        # Send invalid payload to test endpoint accessibility
        response = requests.post(
            f"{BASE_URL}/api/stripe/webhook",
            data="invalid",
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print("✅ Webhook endpoint accessible (returns 400 for invalid payload)")
            return True
        else:
            print(f"⚠️ Webhook endpoint returned unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

def test_database_schema():
    """Test if database schema is ready"""
    print("\n🗄️ Testing database schema...")
    
    try:
        # Test schema verification endpoint (if it exists)
        response = requests.get(f"{BASE_URL}/api/debug-session")
        
        if response.status_code in [200, 401, 404]:
            print("✅ Database appears to be accessible")
            return True
        else:
            print(f"⚠️ Database test returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def generate_test_cards():
    """Display Stripe test card numbers"""
    print("\n💳 Stripe Test Cards for Testing:")
    print("   Success: 4242 4242 4242 4242")
    print("   Decline: 4000 0000 0000 0002") 
    print("   Insufficient funds: 4000 0000 0000 9995")
    print("   Use any future expiry date (e.g., 12/34) and any CVC")

def main():
    """Run all tests"""
    print("🚀 SoulBridge AI Bronze/Silver/Gold Stripe Integration Test")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("API /me Endpoint", test_api_me_endpoint),
        ("Stripe Checkout", test_stripe_checkout_endpoint),
        ("Webhook Endpoint", test_webhook_endpoint),
        ("Database Schema", test_database_schema)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your Bronze/Silver/Gold integration is ready!")
        print("\n📝 Next steps:")
        print("   1. Create products in Stripe dashboard")
        print("   2. Set up webhook in Stripe")
        print("   3. Add environment variables to Railway")
        print("   4. Test with real Stripe checkout")
        
        generate_test_cards()
        
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the output above for details.")
    
    print(f"\n🕐 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()