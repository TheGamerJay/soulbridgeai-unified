"""
SoulBridge AI - Credit Manager
High-level credit management class for easy integration
"""
import logging
from typing import Dict, Any, Optional
from .operations import (
    get_artistic_time, 
    deduct_artistic_time, 
    refund_artistic_time, 
    get_credit_summary
)
from .constants import ARTISTIC_TIME_COSTS, TIER_ARTISTIC_TIME

logger = logging.getLogger(__name__)

class CreditManager:
    """High-level credit management for SoulBridge features"""
    
    def __init__(self):
        self.costs = ARTISTIC_TIME_COSTS
        self.allowances = TIER_ARTISTIC_TIME
    
    def get_balance(self, user_id: int) -> int:
        """Get user's current credit balance"""
        return get_artistic_time(user_id)
    
    def can_afford(self, user_id: int, feature: str) -> bool:
        """Check if user can afford a feature"""
        cost = self.costs.get(feature, 0)
        balance = self.get_balance(user_id)
        return balance >= cost
    
    def charge_feature(self, user_id: int, feature: str) -> Dict[str, Any]:
        """Charge user for a feature and return result"""
        cost = self.costs.get(feature, 0)
        
        if cost == 0:
            return {
                "success": True,
                "cost": 0,
                "message": f"{feature} is free",
                "balance_after": self.get_balance(user_id)
            }
        
        balance_before = self.get_balance(user_id)
        
        if balance_before < cost:
            return {
                "success": False,
                "error": f"Insufficient credits. Need {cost}, have {balance_before}",
                "cost": cost,
                "balance": balance_before
            }
        
        success = deduct_artistic_time(user_id, cost)
        balance_after = self.get_balance(user_id) if success else balance_before
        
        if success:
            return {
                "success": True,
                "cost": cost,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "message": f"Charged {cost} credits for {feature}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to deduct credits",
                "cost": cost,
                "balance": balance_before
            }
    
    def refund_feature(self, user_id: int, feature: str, reason: str = "refund") -> Dict[str, Any]:
        """Refund credits for a failed feature"""
        cost = self.costs.get(feature, 0)
        
        if cost == 0:
            return {
                "success": True,
                "cost": 0,
                "message": f"{feature} was free, no refund needed"
            }
        
        balance_before = self.get_balance(user_id)
        success = refund_artistic_time(user_id, cost, reason)
        balance_after = self.get_balance(user_id) if success else balance_before
        
        if success:
            return {
                "success": True,
                "refunded": cost,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "message": f"Refunded {cost} credits for {feature} ({reason})"
            }
        else:
            return {
                "success": False,
                "error": "Failed to refund credits",
                "attempted_refund": cost
            }
    
    def get_detailed_balance(self, user_id: int) -> Dict[str, Any]:
        """Get detailed credit information for user"""
        return get_credit_summary(user_id)
    
    def get_feature_cost(self, feature: str) -> int:
        """Get cost of a specific feature"""
        return self.costs.get(feature, 0)
    
    def get_affordable_features(self, user_id: int) -> Dict[str, bool]:
        """Get which features user can currently afford"""
        balance = self.get_balance(user_id)
        affordable = {}
        
        for feature, cost in self.costs.items():
            affordable[feature] = balance >= cost
        
        return affordable
    
    def batch_charge(self, user_id: int, charges: Dict[str, int]) -> Dict[str, Any]:
        """Charge multiple features in a single transaction"""
        total_cost = sum(charges.values())
        balance = self.get_balance(user_id)
        
        if balance < total_cost:
            return {
                "success": False,
                "error": f"Insufficient credits for batch operation. Need {total_cost}, have {balance}",
                "total_cost": total_cost,
                "balance": balance,
                "charges": charges
            }
        
        # Deduct total cost
        success = deduct_artistic_time(user_id, total_cost)
        
        if success:
            return {
                "success": True,
                "total_cost": total_cost,
                "balance_before": balance,
                "balance_after": self.get_balance(user_id),
                "charges": charges
            }
        else:
            return {
                "success": False,
                "error": "Failed to process batch charges",
                "total_cost": total_cost,
                "charges": charges
            }
    
    def validate_subscription_credits(self, user_id: int, user_plan: str) -> Dict[str, Any]:
        """Validate user's credits match their subscription tier"""
        try:
            summary = self.get_detailed_balance(user_id)
            expected_allowance = self.allowances.get(user_plan, 0)
            
            return {
                "user_plan": user_plan,
                "expected_allowance": expected_allowance,
                "current_monthly": summary.get("monthly_credits", 0),
                "total_credits": summary.get("total_credits", 0),
                "trial_active": summary.get("trial_active", False),
                "valid": True  # Could add validation logic here
            }
        except Exception as e:
            return {
                "error": str(e),
                "valid": False
            }