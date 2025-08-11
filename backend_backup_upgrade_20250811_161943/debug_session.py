#!/usr/bin/env python3
"""
Debug script to check current session and tier isolation
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Quick test script
print("=== TIER ISOLATION DEBUG ===")
print("\nTo test this properly, we need to:")
print("1. Check what user_plan values are being set in the session")  
print("2. Check if get_effective_plan is being called correctly")
print("3. Verify trial_active status for different users")

# Test the get_effective_plan function directly
def get_effective_plan(user_plan: str, trial_active: bool) -> str:
    """Get effective plan for FEATURE ACCESS (not usage limits)"""  
    # Defensive migration for any legacy plans that slip through
    legacy_mapping = {'foundation': 'free', 'premium': 'growth', 'enterprise': 'max'}
    user_plan = legacy_mapping.get(user_plan, user_plan)
    
    # Ensure we only work with valid plans
    if user_plan not in ['free', 'growth', 'max']:
        print(f"⚠️ Unknown plan '{user_plan}' defaulting to 'free'")
        user_plan = 'free'
    
    # FIXED: During trial, unlock all features (max access) but keep subscription limits
    # Trial gives 'max' feature access while usage limits stay tied to actual subscription
    if trial_active:
        return 'max'  # Unlock all features during trial
    else:
        return user_plan  # Use real plan when no trial

print("\n=== TESTING get_effective_plan FUNCTION ===")
test_cases = [
    ('free', False, 'free'),
    ('growth', False, 'growth'), 
    ('max', False, 'max'),
    ('free', True, 'max'),
    ('growth', True, 'max'),
    ('max', True, 'max')
]

print("user_plan | trial_active | expected | actual   | status")
print("-" * 55)
for user_plan, trial_active, expected in test_cases:
    actual = get_effective_plan(user_plan, trial_active)
    status = "OK" if actual == expected else "FAIL"
    print(f"{user_plan:9} | {trial_active:12} | {expected:8} | {actual:8} | {status}")

print("\n=== POSSIBLE ISSUES ===")
print("1. All users might have user_plan='max' set incorrectly")
print("2. All users might have trial_active=True incorrectly") 
print("3. Session effective_plan might be cached incorrectly")
print("4. Before_request might not be calling get_effective_plan")

print("\n=== NEXT STEPS ===")
print("1. Check actual session data for different user types")
print("2. Fix session caching to always calculate effective_plan")
print("3. Add debug logging to see what values are being used")