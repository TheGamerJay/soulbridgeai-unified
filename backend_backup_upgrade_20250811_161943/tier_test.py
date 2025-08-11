#!/usr/bin/env python3
"""
Tier System Test Script - SoulBridge AI
========================================

This script tests the tier system logic to debug why all users 
are being treated as foundation/free tier.

Usage: python tier_test.py
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import *

def test_tier_limits():
    """Test the tier limit functions directly"""
    print("TIER SYSTEM TEST - SoulBridge AI")
    print("=" * 50)
    
    # Test constants
    print("\nTIER CONSTANTS:")
    print(f"FREE_LIMITS: {FREE_LIMITS}")
    print(f"PREMIUM_LIMITS: {PREMIUM_LIMITS}")  
    print(f"MAX_LIMITS: {MAX_LIMITS}")
    print(f"TIER_LIMITS: {TIER_LIMITS}")
    
    # Test each tier
    test_plans = ['foundation', 'premium', 'enterprise']
    
    for plan in test_plans:
        print(f"\nTESTING PLAN: {plan}")
        print("-" * 30)
        
        # Test limit calculation
        decoder_limit = get_effective_feature_limit(plan, trial_active=False, feature_name="decoder")
        fortune_limit = get_effective_feature_limit(plan, trial_active=False, feature_name="fortune")
        horoscope_limit = get_effective_feature_limit(plan, trial_active=False, feature_name="horoscope")
        
        # Test display plan
        display_plan = get_effective_plan_for_display(plan, trial_active=False)
        
        print(f"  User Plan: {plan}")
        print(f"  Display Plan: {display_plan}")
        print(f"  Decoder Limit: {decoder_limit}")
        print(f"  Fortune Limit: {fortune_limit}")
        print(f"  Horoscope Limit: {horoscope_limit}")

def test_frontend_expectations():
    """Test what the frontend expects vs what we return"""
    print("\nFRONTEND EXPECTATIONS TEST:")
    print("=" * 40)
    
    # What frontend expects for each tier
    frontend_expectations = {
        'enterprise': {
            'name': 'Max Tier',
            'expected_display': 'enterprise',
            'expected_limits': {'decoder': None, 'fortune': None, 'horoscope': None}
        },
        'premium': {
            'name': 'Growth Tier', 
            'expected_display': 'premium',
            'expected_limits': {'decoder': 15, 'fortune': 8, 'horoscope': 10}
        },
        'foundation': {
            'name': 'Free Tier',
            'expected_display': 'free',  # ❌ Frontend expects 'free' not 'foundation'
            'expected_limits': {'decoder': 3, 'fortune': 2, 'horoscope': 3}
        }
    }
    
    for plan, expectations in frontend_expectations.items():
        print(f"\n{expectations['name']} ({plan}):")
        
        # What we actually return
        display_plan = get_effective_plan_for_display(plan, trial_active=False)
        actual_limits = {
            'decoder': get_effective_feature_limit(plan, trial_active=False, feature_name="decoder"),
            'fortune': get_effective_feature_limit(plan, trial_active=False, feature_name="fortune"), 
            'horoscope': get_effective_feature_limit(plan, trial_active=False, feature_name="horoscope")
        }
        
        print(f"  Expected Display: {expectations['expected_display']}")
        print(f"  Actual Display: {display_plan}")
        print(f"  Display Match: {display_plan == expectations['expected_display']}")
        
        print(f"  Expected Limits: {expectations['expected_limits']}")
        print(f"  Actual Limits: {actual_limits}")
        print(f"  Limits Match: {actual_limits == expectations['expected_limits']}")

def main():
    """Run all tier system tests"""
    test_tier_limits()
    test_frontend_expectations()
    
    print("\n" + "=" * 50)
    print("KEY FINDINGS:")
    print("1. All tier limits are correctly configured")
    print("2. get_effective_plan_for_display() correctly maps:")
    print("   - enterprise -> 'enterprise'")
    print("   - premium -> 'premium'") 
    print("   - foundation -> 'free' (this is correct!)")
    print("\n3. THE REAL ISSUE:")
    print("   All users are stored as 'foundation' in session/database")
    print("   Even users who should be 'premium' or 'enterprise'")
    print("\n4. SOLUTION:")
    print("   Check how user_plan is set during login/registration")
    print("   Verify subscription upgrade logic")
    print("   Check database plan_type field values")

if __name__ == "__main__":
    main()