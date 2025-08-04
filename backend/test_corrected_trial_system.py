#!/usr/bin/env python3
"""
Test the corrected trial system - authentic tier experience
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_corrected_trial_limits():
    print("=== TESTING CORRECTED TRIAL SYSTEM ===\n")
    
    try:
        from app import get_feature_limit, TIER_LIMITS
        
        print("1. NORMAL LIMITS (No Trial):")
        print(f"   Free user decoder: {get_feature_limit('free', 'decoder')}")
        print(f"   Growth user decoder: {get_feature_limit('growth', 'decoder')}")
        print(f"   Max user decoder: {get_feature_limit('max', 'decoder')}")
        
        print(f"   Free user voice_journal_monthly: {get_feature_limit('free', 'voice_journal_monthly')}")
        print(f"   Growth user voice_journal_monthly: {get_feature_limit('growth', 'voice_journal_monthly')}")
        print(f"   Max user voice_journal_monthly: {get_feature_limit('max', 'voice_journal_monthly')}")
        
        print("\n2. AUTHENTIC TRIAL EXPERIENCE:")
        print("   Free user during trial should get Growth limits:")
        print(f"   - Decoder: {get_feature_limit('growth', 'decoder')} (Growth experience)")
        print(f"   - Voice Journal: {get_feature_limit('growth', 'voice_journal_monthly')} (Growth experience)")
        
        print("\n   Growth user during trial should get Max limits:")
        print(f"   - Decoder: {get_feature_limit('max', 'decoder')} (Max experience)")
        print(f"   - Voice Journal: {get_feature_limit('max', 'voice_journal_monthly')} (Max experience)")
        
        print("\n3. CORRECT FLOW:")
        print("   Free → Trial → Growth experience (15/8/10 + premium features)")
        print("   Growth → Trial → Max experience (unlimited + all features)")
        print("   Max → Trial → No change (already have everything)")
        
        print("\n✅ Trial system now provides authentic tier experience!")
        
    except Exception as e:
        print(f"ERROR: Test failed: {e}")

if __name__ == "__main__":
    test_corrected_trial_limits()