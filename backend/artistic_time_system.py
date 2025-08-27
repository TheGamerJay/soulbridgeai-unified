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
    "bronze": 0,      # Bronze gets no monthly artistic time
    "silver": 200,    # Silver gets 200 monthly
    "gold": 500,      # Gold gets 500 monthly
}

TRIAL_ARTISTIC_TIME = 60  # Trial users get 60 one-time credits

# ========================================
# CORE FUNCTIONS
# ========================================

def get_database_connection():
    """Get database connection - compatible with Railway deployment"""
    try:
        # Import get_database from database_utils for consistency
        from database_utils import get_database
        db = get_database()
        if db:
            return db.get_connection()
        else:
            logger.error("Failed to get database instance from database_utils")
            return None
    except ImportError:
        logger.warning("Falling back to direct database connection")
        # Fallback to direct connection
        try:
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                # Production: PostgreSQL
                import psycopg2
                return psycopg2.connect(database_url)
            else:
                # Development: SQLite
                import sqlite3
                db_path = os.environ.get('DATABASE_PATH', 'soulbridge.db')
                return sqlite3.connect(db_path)
        except Exception as e:
            logger.error(f"Direct database connection failed: {e}")
            return None
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_artistic_time(user_id: int) -> int:
    """Get user's current artistic time balance"""
    try:
        logger.info(f"Getting artistic time for user {user_id}")
        conn = get_database_connection()
        if not conn:
            logger.error(f"No database connection for user {user_id}")
            # Emergency fallback: give some credits to prevent complete blocking
            if user_id == 104:  # Your user ID - temporary emergency bypass
                logger.warning(f"EMERGENCY BYPASS: Giving user {user_id} 100 credits due to DB connection error")
                return 100
            return 0
        cursor = conn.cursor()
        
        # Get user's plan and credits - use database-agnostic approach
        try:
            # Try PostgreSQL style first
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, 
                       last_credit_reset, trial_credits
                FROM users WHERE id = %s
            """, (user_id,))
        except Exception as db_error:
            logger.warning(f"PostgreSQL query failed, trying SQLite: {db_error}")
            # Fallback to SQLite style
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, 
                       last_credit_reset, trial_credits
                FROM users WHERE id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"No user found with ID {user_id}")
            conn.close()
            return 0
            
        user_plan, current_credits, trial_active, last_reset, trial_credits = result
        logger.info(f"User {user_id} data: plan={user_plan}, artistic_time={current_credits}, trial_active={trial_active}, trial_credits={trial_credits}")
        
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
            try:
                # Try PostgreSQL style first
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = %s, last_credit_reset = %s 
                    WHERE id = %s
                """, (monthly_allowance, today, user_id))
            except Exception:
                # Fallback to SQLite style
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = ?, last_credit_reset = ? 
                    WHERE id = ?
                """, (monthly_allowance, today, user_id))
            conn.commit()
            current_credits = monthly_allowance
            logger.info(f"Reset artistic time for {user_plan} user {user_id}: {monthly_allowance}")
        
        # Add trial credits if trial is active
        total_credits = current_credits or 0
        if trial_active and user_plan == 'bronze':
            trial_balance = trial_credits or TRIAL_ARTISTIC_TIME
            total_credits += trial_balance
            logger.info(f"User {user_id} trial active: added {trial_balance} trial credits")
            
        logger.info(f"User {user_id} final artistic time balance: {total_credits}")
        conn.close()
        return max(0, total_credits)
        
    except Exception as e:
        logger.error(f"Error getting artistic time for user {user_id}: {e}")
        # Emergency fallback: give some credits to prevent complete blocking
        if user_id == 104:  # Your user ID - temporary emergency bypass
            logger.warning(f"EMERGENCY BYPASS: Giving user {user_id} 100 credits due to system error")
            return 100
        return 0

def deduct_artistic_time(user_id: int, amount: int) -> bool:
    """Deduct artistic time from user's balance"""
    try:
        conn = get_database_connection()
        if not conn:
            return False
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
        conn = get_database_connection()
        if not conn:
            return False
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

def refund_artistic_time(user_id: int, amount: int, reason: str = "Generation failed") -> bool:
    """Refund artistic time to user's balance when generation fails"""
    try:
        conn = get_database_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        
        # Get current user info to determine where to refund
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, trial_credits
            FROM users WHERE id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
            
        user_plan, current_credits, trial_active, trial_credits = result
        
        # If user is on trial and has trial credits, refund to trial credits first
        if trial_active and user_plan == 'bronze' and trial_credits is not None:
            # Refund to trial credits
            new_trial_credits = (trial_credits or 0) + amount
            cursor.execute("""
                UPDATE users 
                SET trial_credits = %s
                WHERE id = %s
            """, (new_trial_credits, user_id))
            
            logger.info(f"Refunded {amount} artistic time to trial credits for user {user_id} - {reason}")
        else:
            # Refund to regular artistic time
            cursor.execute("""
                UPDATE users 
                SET artistic_time = COALESCE(artistic_time, 0) + %s
                WHERE id = %s
            """, (amount, user_id))
            
            logger.info(f"Refunded {amount} artistic time to regular balance for user {user_id} - {reason}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error refunding artistic time for user {user_id}: {e}")
        return False

# ========================================
# MIGRATION FUNCTION
# ========================================

def migrate_to_artistic_time():
    """Migrate trainer_credits to artistic_time"""
    try:
        conn = get_database_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        
        # Check if artistic_time column exists
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN artistic_time INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN trial_credits INTEGER DEFAULT 60")
        except:
            pass  # Columns already exist
        
        # Copy trainer_credits to artistic_time (if trainer_credits column still exists)
        try:
            cursor.execute("""
                UPDATE users 
                SET artistic_time = COALESCE(trainer_credits, 0),
                    trial_credits = 60
                WHERE artistic_time IS NULL OR artistic_time = 0
            """)
        except:
            # trainer_credits column might not exist anymore, that's okay
            pass
        
        conn.commit()
        conn.close()
        
        logger.info("Migrated trainer_credits to artistic_time")
        return True
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False