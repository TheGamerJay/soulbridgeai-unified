"""
SoulBridge AI - Credit Operations
Core credit system operations: get, deduct, refund, reset
Consolidated from scattered implementations across the monolith
"""
import logging
from datetime import date
from typing import Optional
from .constants import ARTISTIC_TIME_COSTS, TIER_ARTISTIC_TIME, TRIAL_ARTISTIC_TIME

logger = logging.getLogger(__name__)

def ensure_user_data_initialized(user_id: int, db) -> bool:
    """Ensure user has all required artistic time columns with proper default values"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get current user data
        if db.use_postgres:
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, trial_credits, last_credit_reset
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, trial_credits, last_credit_reset
                FROM users WHERE id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"User {user_id} not found for credit initialization")
            conn.close()
            return False
            
        user_plan, artistic_time, trial_active, trial_credits, last_reset = result
        logger.debug(f"Credit data for user {user_id}: plan={user_plan}, artistic_time={artistic_time}, trial_active={trial_active}, trial_credits={trial_credits}")
        
        # Initialize missing data
        updates = []
        params = []
        
        # Initialize artistic_time if NULL and user is subscriber
        if artistic_time is None and user_plan in ['silver', 'gold']:
            monthly_allowance = TIER_ARTISTIC_TIME.get(user_plan, 0)
            updates.append("artistic_time = %s" if db.use_postgres else "artistic_time = ?")
            params.append(monthly_allowance)
            logger.info(f"Initializing artistic_time for {user_plan} user {user_id} with {monthly_allowance}")
        
        # Initialize trial_credits if NULL and user has active trial
        if trial_credits is None and trial_active and user_plan == 'bronze':
            updates.append("trial_credits = %s" if db.use_postgres else "trial_credits = ?")
            params.append(TRIAL_ARTISTIC_TIME)
            logger.info(f"Initializing trial_credits for Bronze trial user {user_id} with {TRIAL_ARTISTIC_TIME}")
        
        # Apply updates if needed
        if updates:
            param_placeholder = "%s" if db.use_postgres else "?"
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = {param_placeholder}"
            params.append(user_id)
            
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"Updated user {user_id} with missing credit data")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error initializing credit data for user {user_id}: {e}")
        return False

def get_artistic_time(user_id: int) -> int:
    """Get user's current artistic time balance from new credit system"""
    try:
        # Import here to avoid circular imports
        try:
            from database_utils import get_database
        except ImportError:
            from ..shared.database import get_database
        
        db = get_database()
        if not db:
            logger.error(f"No database connection for credits user {user_id}")
            return 0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # First check new user_credits table
        if db.use_postgres:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            credits = result[0] or 0
            logger.debug(f"Credits from new system for user {user_id}: {credits}")
            conn.close()
            return max(0, credits)
        
        # Fallback to old system for migration period
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, trial_credits
            FROM users WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"No user found for credits: {user_id}")
            conn.close()
            return 0
            
        user_plan, current_credits, trial_active, trial_credits = result
        
        # Calculate total from old system
        total_credits = current_credits or 0
        if trial_active and user_plan == 'bronze':
            trial_balance = trial_credits or TRIAL_ARTISTIC_TIME
            total_credits += trial_balance
            
        logger.debug(f"Credits from old system for user {user_id}: {total_credits}")
        conn.close()
        return max(0, total_credits)
        
    except Exception as e:
        logger.error(f"Error getting credits for user {user_id}: {e}")
        return 0

def deduct_artistic_time(user_id: int, amount: int) -> bool:
    """Deduct artistic time from user's balance using new credit system"""
    try:
        # Import here to avoid circular imports
        try:
            from database_utils import get_database
        except ImportError:
            from ..shared.database import get_database
        
        db = get_database()
        if not db:
            logger.error(f"No database connection for deducting credits user {user_id}")
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check current balance from new system first
        if db.use_postgres:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            current_credits = result[0] or 0
            if current_credits < amount:
                logger.warning(f"Insufficient credits for user {user_id}: need {amount}, have {current_credits}")
                conn.close()
                return False
            
            # Deduct from new system
            new_balance = current_credits - amount
            if db.use_postgres:
                cursor.execute("""
                    UPDATE user_credits SET credits_remaining = %s WHERE user_id = %s
                """, (new_balance, user_id))
            else:
                cursor.execute("""
                    UPDATE user_credits SET credits_remaining = ? WHERE user_id = ?
                """, (new_balance, user_id))
            
            # Add to ledger
            cursor.execute("""
                INSERT INTO credit_ledger (user_id, delta, reason, metadata)
                VALUES (?, ?, ?, ?)
            """, (user_id, -amount, 'feature_usage', '{}'))
            
            conn.commit()
            conn.close()
            logger.info(f"Deducted {amount} credits from user {user_id} (new system): {current_credits} -> {new_balance}")
            return True
        
        # Fallback to old system during migration
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, trial_credits
            FROM users WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"User {user_id} not found for credit deduction")
            conn.close()
            return False
            
        user_plan, current_credits, trial_active, trial_credits = result
        
        # Use old system logic as fallback
        monthly_balance = current_credits or 0
        trial_balance = 0
        
        if trial_active and user_plan == 'bronze':
            trial_balance = trial_credits or 0
        
        total_available = monthly_balance + trial_balance
        
        if total_available < amount:
            logger.warning(f"Insufficient credits for user {user_id}: need {amount}, have {total_available}")
            conn.close()
            return False
        
        # Deduct using old system
        new_trial_credits = trial_credits or 0
        new_monthly_credits = monthly_balance
        
        if trial_balance > 0:
            trial_deduction = min(amount, trial_balance)
            new_trial_credits = trial_balance - trial_deduction
            remaining_amount = amount - trial_deduction
            
            if remaining_amount > 0:
                new_monthly_credits = monthly_balance - remaining_amount
        else:
            new_monthly_credits = monthly_balance - amount
        
        cursor.execute("""
            UPDATE users 
            SET artistic_time = ?, trial_credits = ?
            WHERE id = ?
        """, (new_monthly_credits, new_trial_credits, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Deducted {amount} credits from user {user_id} (old system): monthly={new_monthly_credits}, trial={new_trial_credits}")
        return True
        
    except Exception as e:
        logger.error(f"Error deducting credits for user {user_id}: {e}")
        return False

def refund_artistic_time(user_id: int, amount: int, reason: str = "refund") -> bool:
    """Refund artistic time to user's balance using new credit system"""
    try:
        # Import here to avoid circular imports
        try:
            from database_utils import get_database
        except ImportError:
            from ..shared.database import get_database
        
        db = get_database()
        if not db:
            logger.error(f"No database connection for refunding credits user {user_id}")
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if user exists in new system
        if db.use_postgres:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT credits_remaining FROM user_credits WHERE user_id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            # Use new system
            current_credits = result[0] or 0
            new_balance = current_credits + amount
            
            if db.use_postgres:
                cursor.execute("""
                    UPDATE user_credits SET credits_remaining = %s WHERE user_id = %s
                """, (new_balance, user_id))
            else:
                cursor.execute("""
                    UPDATE user_credits SET credits_remaining = ? WHERE user_id = ?
                """, (new_balance, user_id))
            
            # Add to ledger
            cursor.execute("""
                INSERT INTO credit_ledger (user_id, delta, reason, metadata)
                VALUES (?, ?, ?, ?)
            """, (user_id, amount, reason, '{}'))
            
            conn.commit()
            conn.close()
            logger.info(f"Refunded {amount} credits to user {user_id} (new system): {current_credits} -> {new_balance} (reason: {reason})")
            return True
        
        # Fallback to old system
        cursor.execute("""
            SELECT user_plan, artistic_time, trial_active, trial_credits
            FROM users WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"User {user_id} not found for credit refund")
            conn.close()
            return False
            
        user_plan, current_credits, trial_active, trial_credits = result
        
        # Use old system logic
        if trial_active and user_plan == 'bronze':
            new_trial_credits = (trial_credits or 0) + amount
            cursor.execute("""
                UPDATE users 
                SET trial_credits = ?
                WHERE id = ?
            """, (new_trial_credits, user_id))
        else:
            new_monthly_credits = (current_credits or 0) + amount
            cursor.execute("""
                UPDATE users 
                SET artistic_time = ?
                WHERE id = ?
            """, (new_monthly_credits, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Refunded {amount} credits to user {user_id} (old system, reason: {reason})")
        return True
        
    except Exception as e:
        logger.error(f"Error refunding credits for user {user_id}: {e}")
        return False

def get_feature_cost(feature_name: str) -> int:
    """Get the artistic time cost for a specific feature"""
    return ARTISTIC_TIME_COSTS.get(feature_name, 0)

def get_monthly_allowance(tier: str) -> int:
    """Get the monthly artistic time allowance for a tier"""
    return TIER_ARTISTIC_TIME.get(tier, 0)

def get_credit_summary(user_id: int) -> dict:
    """Get comprehensive credit summary for user"""
    try:
        # Import here to avoid circular imports
        from ..shared.database import get_database
        
        db = get_database()
        if not db:
            return {"error": "No database connection"}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get user credit data
        if db.use_postgres:
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, trial_credits, 
                       last_credit_reset, trial_expires_at
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT user_plan, artistic_time, trial_active, trial_credits,
                       last_credit_reset, trial_expires_at
                FROM users WHERE id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return {"error": "User not found"}
        
        user_plan, monthly_credits, trial_active, trial_credits, last_reset, trial_expires = result
        
        # Calculate totals
        total_credits = get_artistic_time(user_id)
        monthly_allowance = get_monthly_allowance(user_plan)
        
        summary = {
            "user_id": user_id,
            "user_plan": user_plan,
            "total_credits": total_credits,
            "monthly_credits": monthly_credits or 0,
            "monthly_allowance": monthly_allowance,
            "trial_active": trial_active,
            "trial_credits": trial_credits or 0,
            "last_reset": last_reset,
            "trial_expires_at": trial_expires
        }
        
        conn.close()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting credit summary for user {user_id}: {e}")
        return {"error": str(e)}