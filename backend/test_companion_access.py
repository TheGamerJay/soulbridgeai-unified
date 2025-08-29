#!/usr/bin/env python3
"""
Test companion access logic directly
"""
import sys
import os

# Test the companion access logic without importing the full Flask app
def normalize_plan(plan):
    """Normalize plan name"""
    if not plan:
        return "bronze"
    
    plan_lower = plan.lower()
    # Migration map for old names
    if plan_lower in ["free"]:
        return "bronze"
    elif plan_lower in ["growth"]:
        return "silver"  
    elif plan_lower in ["max"]:
        return "gold"
    else:
        return plan_lower

def allowed_tiers_for_plan(plan):
    """Get allowed tiers for a plan"""
    if plan == "bronze":
        return set(["bronze"])
    elif plan == "silver":
        return set(["bronze", "silver"])
    elif plan == "gold":
        return set(["bronze", "silver", "gold"])
    else:
        return set(["bronze"])

def companion_unlock_state_new(user_plan: str, trial_active: bool, referrals: int):
    """
    Returns access state for companions based on user's plan, trial status, and referrals.
    - Trial unlocks bronze+silver+gold companions TEMPORARILY
    - Referral-only companions stay locked during trial; they require min_referrals
    """
    canon = normalize_plan(user_plan)
    if trial_active:
        tier_access = set(["bronze", "silver", "gold"])
    else:
        tier_access = allowed_tiers_for_plan(canon)

    # For this test, we don't have COMPANIONS_NEW, so return empty referral set
    referral_unlocked_ids = set()

    return tier_access, referral_unlocked_ids

def user_can_access_companion(user_plan: str, trial_active: bool, referrals: int, comp: dict):
    """
    Final server-side decision for companion access.
    Returns (can_access: bool, reason: str|None)
    """
    tier_access, referral_unlocked_ids = companion_unlock_state_new(user_plan, trial_active, referrals)
    tier_ok = comp["tier"] in tier_access

    # Referral-only companions: require min_referrals and IGNORE trial unlock
    min_refs = comp.get("min_referrals", 0)
    if min_refs > 0:
        return (comp["id"] in referral_unlocked_ids,
                f"Referral companion: requires {min_refs} referrals")

    return (tier_ok, None if tier_ok else f"Tier locked: requires {comp['tier'].title()}")

if __name__ == "__main__":
    print("=== COMPANION ACCESS TEST ===")
    
    # Test cases for Bronze user without trial
    user_plan = 'bronze'
    trial_active = False
    referrals = 0
    
    print(f"Testing for: user_plan={user_plan}, trial_active={trial_active}, referrals={referrals}")
    print()
    
    # Test different companion tiers
    test_companions = [
        {'id': 'comp1', 'tier': 'bronze'},
        {'id': 'comp2', 'tier': 'silver'},
        {'id': 'comp3', 'tier': 'gold'},
        {'id': 'comp4', 'tier': 'referral', 'min_referrals': 5},
    ]
    
    print('Expected Results:')
    print('  Bronze companion: (True, None) - Should be accessible')
    print('  Silver companion: (False, "Tier locked: requires Silver") - Should be locked') 
    print('  Gold companion: (False, "Tier locked: requires Gold") - Should be locked')
    print('  Referral companion: (False, "Referral companion: requires 5 referrals") - Should be locked')
    print()
    
    print('Actual Results:')
    for comp in test_companions:
        result = user_can_access_companion(user_plan, trial_active, referrals, comp)
        tier_name = f'{comp["tier"]} companion'
        if comp.get('min_referrals'):
            tier_name += f' (needs {comp["min_referrals"]} refs)'
        print(f'  {tier_name}: {result}')
    
    print()
    print("=== TEST WITH TRIAL ACTIVE ===")
    
    # Test with trial active
    trial_active = True
    print(f"Testing for: user_plan={user_plan}, trial_active={trial_active}, referrals={referrals}")
    print()
    
    print('Expected Results with Trial:')
    print('  Bronze companion: (True, None) - Should be accessible')
    print('  Silver companion: (True, None) - Should be accessible (trial gives access)')
    print('  Gold companion: (True, None) - Should be accessible (trial gives access)') 
    print('  Referral companion: (False, "Referral companion: requires 5 referrals") - Should still be locked')
    print()
    
    print('Actual Results with Trial:')
    for comp in test_companions:
        result = user_can_access_companion(user_plan, trial_active, referrals, comp)
        tier_name = f'{comp["tier"]} companion'
        if comp.get('min_referrals'):
            tier_name += f' (needs {comp["min_referrals"]} refs)'
        print(f'  {tier_name}: {result}')