# ========================================
# ARTISTIC TIME CREDIT SYSTEM
# Simple, unified credit management
# ========================================

import os
import logging
from datetime import datetime, date
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ========================================
# CREDIT COSTS
# ========================================

ARTISTIC_TIME_COSTS = {
    "ai_images": 5,
    "voice_journaling": 10, 
    "relationship_profiles": 15,
    "meditations": 8,
    "mini_studio": 20,
}

# ========================================
# TIER ALLOWANCES (Monthly)
# ========================================

TIER_ARTISTIC_TIME = {
    "bronze": 0,      # Bronze gets no monthly credits
    "silver": 100,    # Silver gets 100 monthly
    "gold": 500,      # Gold gets 500 monthly
}

TRIAL_ARTISTIC_TIME = 60  # Trial users get 60 one-time credits

# ========================================
# CORE FUNCTIONS
# ========================================

def get_database():
    """Get database connection"""
    try:
        from database_utils import get_database
        return get_database()
    except ImportError:
        logger.error("database_utils not found")
        return None

def get_artistic_time(user_id: int) -> int:
    """Get user's current artistic time balance"""
    try:
        db = get_database()
        if not db:
            return 0
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get user's plan and credits
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, 
                   last_credit_reset, trial_credits
            FROM users WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return 0
            
        user_plan, current_credits, trial_active, last_reset, trial_credits = result
        
        # Check if monthly reset is needed
        today = date.today()
        needs_reset = (
            last_reset is None or 
            last_reset.year != today.year or 
            last_reset.month != today.month
        )
        
        if needs_reset and user_plan in ['silver', 'gold']:
            # Reset monthly credits
            monthly_allowance = TIER_ARTISTIC_TIME.get(user_plan, 0)
            cursor.execute("""
                UPDATE users 
                SET artistic_time = %s, last_credit_reset = %s 
                WHERE id = %s
            """, (monthly_allowance, today, user_id))
            conn.commit()
            current_credits = monthly_allowance
            logger.info(f"Reset artistic time for {user_plan} user {user_id}: {monthly_allowance}")
        
        # Add trial credits if trial is active
        total_credits = current_credits or 0
        if trial_active and user_plan == 'bronze':
            trial_balance = trial_credits or TRIAL_ARTISTIC_TIME
            total_credits += trial_balance
            
        conn.close()
        return max(0, total_credits)
        
    except Exception as e:
        logger.error(f"Error getting artistic time for user {user_id}: {e}")
        return 0

def deduct_artistic_time(user_id: int, amount: int) -> bool:
    """Deduct artistic time from user's balance"""
    try:
        db = get_database()
        if not db:
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, trial_credits
            FROM users WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
            
        user_plan, current_credits, trial_active, trial_credits = result
        
        # Calculate total available credits
        total_available = current_credits or 0
        if trial_active and user_plan == 'bronze':
            total_available += (trial_credits or TRIAL_ARTISTIC_TIME)
        
        if total_available < amount:
            conn.close()
            return False
        
        # Deduct from trial credits first, then regular credits
        if trial_active and user_plan == 'bronze' and trial_credits > 0:
            trial_deduction = min(amount, trial_credits)
            new_trial_credits = trial_credits - trial_deduction
            remaining_deduction = amount - trial_deduction
            
            cursor.execute("""
                UPDATE users 
                SET trial_credits = %s
                WHERE id = %s
            """, (new_trial_credits, user_id))
            
            if remaining_deduction > 0:
                new_credits = (current_credits or 0) - remaining_deduction
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = %s
                    WHERE id = %s
                """, (new_credits, user_id))
        else:
            # Deduct from regular credits
            new_credits = (current_credits or 0) - amount
            cursor.execute("""
                UPDATE users 
                SET artistic_time = %s
                WHERE id = %s
            """, (new_credits, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deducted {amount} artistic time from user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deducting artistic time for user {user_id}: {e}")
        return False

def get_feature_cost(feature: str) -> int:
    """Get artistic time cost for a feature"""
    return ARTISTIC_TIME_COSTS.get(feature, 0)

def add_artistic_time(user_id: int, amount: int) -> bool:
    """Add artistic time to user's balance (for purchases)"""
    try:
        db = get_database()
        if not db:
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET artistic_time = COALESCE(artistic_time, 0) + %s
            WHERE id = %s
        """, (amount, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {amount} artistic time to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding artistic time for user {user_id}: {e}")
        return False

# ========================================
# MIGRATION FUNCTION
# ========================================

def migrate_to_artistic_time():
    """Migrate trainer_credits to artistic_time"""
    try:
        db = get_database()
        if not db:
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if artistic_time column exists
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN artistic_time INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN trial_credits INTEGER DEFAULT 60")
        except:
            pass  # Columns already exist
        
        # Copy trainer_credits to artistic_time
        cursor.execute("""
            UPDATE users 
            SET artistic_time = COALESCE(trainer_credits, 0),
                trial_credits = 60
            WHERE artistic_time IS NULL OR artistic_time = 0
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Migrated trainer_credits to artistic_time")
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False