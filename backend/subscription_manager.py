#!/usr/bin/env python3
"""
Subscription Grace Period Manager
Handles subscription cancellation with proper grace periods
"""

import os
import psycopg2
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("No DATABASE_URL found")
    return psycopg2.connect(database_url)

def ensure_subscription_schema():
    """Ensure subscription management columns exist"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Add subscription expiration tracking columns
        missing_columns = [
            ('subscription_status', 'VARCHAR(50) DEFAULT \'free\''),
            ('subscription_expires_at', 'TIMESTAMP'),
            ('subscription_cancelled_at', 'TIMESTAMP'),
            ('grace_period_active', 'BOOLEAN DEFAULT FALSE')
        ]
        
        for column_name, column_def in missing_columns:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                conn.commit()
                logger.info(f"📊 SCHEMA: Added column users.{column_name}")
            except psycopg2.Error as e:
                if 'already exists' in str(e).lower():
                    logger.info(f"📊 SCHEMA: Column users.{column_name} already exists")
                    conn.rollback()
                else:
                    logger.error(f"📊 SCHEMA ERROR adding users.{column_name}: {e}")
                    conn.rollback()
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"📊 SCHEMA ERROR: {e}")
        return False

def cancel_subscription(user_id: int, plan_type: str, current_period_end: datetime):
    """
    Cancel subscription but keep benefits until billing period ends
    This implements the roadmap requirement for grace periods
    """
    try:
        ensure_subscription_schema()
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Mark subscription as cancelled but keep benefits until expiration
        cur.execute("""
            UPDATE users 
            SET subscription_status = 'cancelled',
                subscription_cancelled_at = CURRENT_TIMESTAMP,
                subscription_expires_at = %s,
                grace_period_active = TRUE
            WHERE id = %s
        """, (current_period_end, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🚫 SUBSCRIPTION CANCELLED: User {user_id} {plan_type} plan cancelled, benefits until {current_period_end}")
        return True
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        return False

def check_subscription_status(user_id: int) -> Dict[str, Any]:
    """
    Check if user has active subscription or is in grace period
    Returns subscription details including grace period status
    """
    try:
        ensure_subscription_schema()
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_plan, subscription_status, subscription_expires_at, 
                   subscription_cancelled_at, grace_period_active
            FROM users WHERE id = %s
        """, (user_id,))
        
        result = cur.fetchone()
        conn.close()
        
        if not result:
            return {"active": False, "plan": "free", "grace_period": False}
        
        user_plan, sub_status, expires_at, cancelled_at, grace_active = result
        
        # Check if subscription has expired
        now = datetime.utcnow()
        is_expired = expires_at and now > expires_at
        
        # Determine actual status
        if is_expired and grace_active:
            # Grace period has ended - revert to free
            revert_to_free(user_id)
            return {"active": False, "plan": "free", "grace_period": False, "expired": True}
        
        elif sub_status == 'cancelled' and grace_active and not is_expired:
            # In grace period - keep benefits
            return {
                "active": True, 
                "plan": user_plan, 
                "grace_period": True,
                "expires_at": expires_at,
                "cancelled_at": cancelled_at
            }
        
        elif sub_status == 'active':
            # Active subscription
            return {"active": True, "plan": user_plan, "grace_period": False}
        
        else:
            # Free or fully expired
            return {"active": False, "plan": "free", "grace_period": False}
        
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return {"active": False, "plan": "free", "grace_period": False}

def revert_to_free(user_id: int):
    """
    Revert user to bronze tier after grace period expires
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users 
            SET user_plan = 'free',
                subscription_status = 'free',
                grace_period_active = FALSE,
                subscription_expires_at = NULL,
                subscription_cancelled_at = NULL
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"⬇️ REVERTED TO BRONZE: User {user_id} grace period ended, reverted to bronze tier")
        return True
        
    except Exception as e:
        logger.error(f"Error reverting to free: {e}")
        return False

def cleanup_expired_subscriptions():
    """
    Periodic cleanup task to revert expired grace period users to bronze tier
    This should be run daily via cron job or scheduler
    """
    try:
        ensure_subscription_schema()
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find users whose grace period has expired
        cur.execute("""
            SELECT id, user_plan 
            FROM users 
            WHERE grace_period_active = TRUE 
            AND subscription_expires_at < CURRENT_TIMESTAMP
        """)
        
        expired_users = cur.fetchall()
        
        if expired_users:
            # Revert all expired users to free
            user_ids = [user[0] for user in expired_users]
            cur.execute("""
                UPDATE users 
                SET user_plan = 'free',
                    subscription_status = 'free', 
                    grace_period_active = FALSE,
                    subscription_expires_at = NULL,
                    subscription_cancelled_at = NULL
                WHERE id = ANY(%s)
            """, (user_ids,))
            
            conn.commit()
            logger.info(f"🧹 CLEANUP: Reverted {len(expired_users)} expired users to bronze tier")
        
        conn.close()
        return len(expired_users)
        
    except Exception as e:
        logger.error(f"Error cleaning up expired subscriptions: {e}")
        return 0

def get_grace_period_info(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed grace period information for user
    """
    status = check_subscription_status(user_id)
    
    if status.get("grace_period"):
        expires_at = status.get("expires_at")
        if expires_at:
            now = datetime.utcnow()
            time_remaining = expires_at - now
            
            return {
                "in_grace_period": True,
                "plan": status["plan"],
                "expires_at": expires_at,
                "cancelled_at": status.get("cancelled_at"),
                "days_remaining": time_remaining.days,
                "hours_remaining": int(time_remaining.total_seconds() / 3600)
            }
    
    return {"in_grace_period": False}

if __name__ == "__main__":
    # Test schema creation
    ensure_subscription_schema()
    print("✅ Subscription schema updated")