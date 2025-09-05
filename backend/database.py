"""
Database compatibility layer for creative writing routes
Provides simplified interface to database functions
"""

import logging
from flask import session
from db_users import db_get_user_plan
from typing import Optional

logger = logging.getLogger(__name__)

def get_user_plan(user_id: Optional[str] = None) -> str:
    """Get user plan (bronze/silver/gold) from database or session"""
    try:
        # If no user_id provided, get from session
        if not user_id:
            user_id = session.get('user_id')
        
        if not user_id:
            return 'bronze'  # Default to bronze for unauthenticated users
            
        # Try database first
        plan = db_get_user_plan(user_id)
        if plan:
            return plan
            
        # Fallback to session
        return session.get('user_plan', 'bronze')
        
    except Exception as e:
        logger.error(f"Error getting user plan: {e}")
        return 'bronze'  # Safe fallback

def deduct_usage(user_id: str, feature: str, amount: int = 1) -> bool:
    """Deduct usage from user's daily limits (placeholder implementation)"""
    try:
        # This is a placeholder implementation
        # In a real system, this would update usage counters in the database
        logger.info(f"Usage deducted: user_id={user_id}, feature={feature}, amount={amount}")
        return True
        
    except Exception as e:
        logger.error(f"Error deducting usage: {e}")
        return False

def get_daily_usage(user_id: str, feature: str) -> int:
    """Get current daily usage for a feature (placeholder implementation)"""
    try:
        # This is a placeholder implementation
        # In a real system, this would query usage counters from the database
        return 0
        
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        return 0