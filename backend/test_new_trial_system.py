#!/usr/bin/env python3
"""
Test the new clean trial system functions
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Test the new tier limits
def test_tier_limits():
    print("Testing new TIER_LIMITS...")
    
    # Import the updated TIER_LIMITS from app.py
    from app import TIER_LIMITS
    
    # Check that new consistent naming exists
    expected_plans = ['free', 'growth', 'max', 'trial']
    for plan in expected_plans:
        if plan in TIER_LIMITS:
            print(f"OK {plan} plan exists")
            limits = TIER_LIMITS[plan]
            print(f"  - decoder: {limits['decoder']}")
            print(f"  - fortune: {limits['fortune']}")
            print(f"  - horoscope: {limits['horoscope']}")
        else:
            print(f"ERROR {plan} plan MISSING")
    
    print()

# Test the new functions
def test_new_functions():
    print("Testing new trial system functions...")
    
    try:
        from app import get_feature_limit, is_trial_active
        
        # Test get_feature_limit
        decoder_limit_free = get_feature_limit('free', 'decoder')
        decoder_limit_growth = get_feature_limit('growth', 'decoder') 
        decoder_limit_trial = get_feature_limit('trial', 'decoder')
        
        print(f"OK get_feature_limit works:")
        print(f"  - free decoder: {decoder_limit_free}")
        print(f"  - growth decoder: {decoder_limit_growth}")
        print(f"  - trial decoder: {decoder_limit_trial}")
        
        # Test is_trial_active (will return False since no DB connection)
        trial_status = is_trial_active(123)  # fake user_id
        print(f"OK is_trial_active works (no DB): {trial_status}")
        
    except Exception as e:
        print(f"ERROR Function test failed: {e}")
    
    print()

# Test the API endpoints by importing them
def test_api_endpoints():
    print("Testing new API endpoints exist...")
    
    try:
        from app import app
        
        # Check if new endpoints exist
        endpoints = []
        for rule in app.url_map.iter_rules():
            endpoints.append(rule.rule)
        
        required_endpoints = ['/api/user-plan', '/api/start-trial']
        
        for endpoint in required_endpoints:
            if endpoint in endpoints:
                print(f"OK {endpoint} endpoint exists")
            else:
                print(f"ERROR {endpoint} endpoint MISSING")
                
    except Exception as e:
        print(f"ERROR API endpoint test failed: {e}")
    
    print()

def test_javascript_file():
    print("Testing new JavaScript file...")
    
    js_file = os.path.join(os.path.dirname(__file__), 'static', 'js', 'new_trial_system.js')
    
    if os.path.exists(js_file):
        print(f"OK new_trial_system.js exists")
        with open(js_file, 'r') as f:
            content = f.read()
            
        # Check for key functions
        required_functions = ['refreshTrialUI', 'updateLimits', 'startTrial', 'isCompanionUnlocked']
        for func in required_functions:
            if func in content:
                print(f"OK {func} function exists")
            else:
                print(f"ERROR {func} function MISSING")
    else:
        print(f"ERROR new_trial_system.js file MISSING")
    
    print()

if __name__ == "__main__":
    print("=== NEW TRIAL SYSTEM TEST ===\n")
    
    test_tier_limits()
    test_new_functions()
    test_api_endpoints()
    test_javascript_file()
    
    print("=== TEST COMPLETE ===")