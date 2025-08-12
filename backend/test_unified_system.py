#!/usr/bin/env python3
"""
Test script for the unified tier system
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from unified_tier_system import (
    get_effective_plan, get_feature_limit, DAILY_LIMITS, MONTHLY_CREDITS
)

def test_unified_system():
    print("Testing Unified Tier System")
    print("=" * 50)
    
    # Test 1: Free user, no trial
    print("\nTest 1: Free user, no trial")
    plan = "free"
    trial = False
    effective = get_effective_plan(plan, trial)
    decoder_limit = get_feature_limit(plan, "decoder", trial)
    print(f"Plan: {plan}, Trial: {trial}")
    print(f"Effective Plan: {effective}")
    print(f"Decoder Limit: {decoder_limit}")
    assert effective == "free", f"Expected 'free', got '{effective}'"
    assert decoder_limit == 3, f"Expected 3, got {decoder_limit}"
    print("PASS")
    
    # Test 2: Growth user, no trial  
    print("\nTest 2: Growth user, no trial")
    plan = "growth"
    trial = False
    effective = get_effective_plan(plan, trial)
    decoder_limit = get_feature_limit(plan, "decoder", trial)
    fortune_limit = get_feature_limit(plan, "fortune", trial)
    print(f"Plan: {plan}, Trial: {trial}")
    print(f"Effective Plan: {effective}")
    print(f"Decoder Limit: {decoder_limit}")
    print(f"Fortune Limit: {fortune_limit}")
    assert effective == "growth", f"Expected 'growth', got '{effective}'"
    assert decoder_limit == 15, f"Expected 15, got {decoder_limit}"
    assert fortune_limit == 8, f"Expected 8, got {fortune_limit}"
    print("PASS")
    
    # Test 3: Free user WITH trial (critical test)
    print("\nTest 3: Free user WITH trial (should get Max features but Free limits)")
    plan = "free"
    trial = True
    effective = get_effective_plan(plan, trial)
    decoder_limit = get_feature_limit(plan, "decoder", trial)
    print(f"Plan: {plan}, Trial: {trial}")
    print(f"Effective Plan: {effective}")
    print(f"Decoder Limit: {decoder_limit}")
    assert effective == "max", f"Expected 'max', got '{effective}'"
    assert decoder_limit == 3, f"Expected 3 (Free limit), got {decoder_limit}"
    print("PASS - Trial gives Max features but keeps Free limits!")
    
    # Test 4: Growth user WITH trial
    print("\nTest 4: Growth user WITH trial (should get Max features but Growth limits)")
    plan = "growth"
    trial = True
    effective = get_effective_plan(plan, trial)
    decoder_limit = get_feature_limit(plan, "decoder", trial)
    fortune_limit = get_feature_limit(plan, "fortune", trial)
    print(f"Plan: {plan}, Trial: {trial}")
    print(f"Effective Plan: {effective}")
    print(f"Decoder Limit: {decoder_limit}")
    print(f"Fortune Limit: {fortune_limit}")
    assert effective == "max", f"Expected 'max', got '{effective}'"
    assert decoder_limit == 15, f"Expected 15 (Growth limit), got {decoder_limit}"
    assert fortune_limit == 8, f"Expected 8 (Growth limit), got {fortune_limit}"
    print("PASS - Trial gives Max features but keeps Growth limits!")
    
    # Test 5: Max user with trial (should remain Max)
    print("\nTest 5: Max user WITH trial")
    plan = "max"
    trial = True
    effective = get_effective_plan(plan, trial)
    decoder_limit = get_feature_limit(plan, "decoder", trial)
    print(f"Plan: {plan}, Trial: {trial}")
    print(f"Effective Plan: {effective}")
    print(f"Decoder Limit: {decoder_limit}")
    assert effective == "max", f"Expected 'max', got '{effective}'"
    assert decoder_limit == 999999, f"Expected 999999, got {decoder_limit}"
    print("PASS")
    
    print("\nALL TESTS PASSED!")
    print("The unified system correctly:")
    print("- Gives trial users Max FEATURES")
    print("- But keeps their actual plan's LIMITS")
    print("- No more confusion between features and limits!")

if __name__ == "__main__":
    test_unified_system()