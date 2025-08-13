#!/usr/bin/env python3
"""
Credit Costs for Premium Features
Defines how many credits each premium feature costs
"""

# Credit costs per feature usage
CREDIT_COSTS = {
    "ai_images": 5,           # 5 credits per AI image generation
    "voice_journaling": 4,    # 4 credits per voice journal entry
    "mini_studio": 1,         # 1 credit per minute of mini studio time
    "relationship_profiles": 6,  # 6 credits per relationship profile  
    "meditations": 3,         # 3 credits per meditation session
}

# Trial credits
TRIAL_CREDITS = 60  # Free users get 60 credits during 5-hour trial

def get_feature_cost(feature_name: str) -> int:
    """Get credit cost for a feature"""
    return CREDIT_COSTS.get(feature_name, 0)

def calculate_trial_examples():
    """Calculate what 60 trial credits can buy"""
    examples = {}
    for feature, cost in CREDIT_COSTS.items():
        examples[feature] = TRIAL_CREDITS // cost
    return examples

if __name__ == "__main__":
    print("Credit Costs:")
    for feature, cost in CREDIT_COSTS.items():
        print(f"  {feature}: {cost} credits")
    
    print(f"\nWith {TRIAL_CREDITS} trial credits, you can get:")
    examples = calculate_trial_examples()
    for feature, count in examples.items():
        print(f"  {count} {feature}")