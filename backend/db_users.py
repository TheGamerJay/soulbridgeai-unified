# db_users.py
# Database helper functions for user operations with Bronze/Silver/Gold tier system

import logging
from database_utils import get_database
from sql_utils import adapt_placeholders, to_db_bool, to_db_ts, from_db_ts

logger = logging.getLogger(__name__)

def db_fetch_user_row(user_id):
    """
    Fetch complete user row from database.
    Returns dict with all user data or None if not found.
    """
    if not user_id:
        return None
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for user fetch")
            return None
            
        conn = db.get_connection()
        try:
            # First, try to get user data including profile image columns
            try:
                q = """
                    SELECT id, email, display_name, created_at, user_plan, trial_active, trial_expires_at, trial_used_permanently, profile_image, profile_image_data
                    FROM users WHERE id = %s
                """
                q = adapt_placeholders(db, q)
                cur = conn.cursor()
                cur.execute(q, (user_id,))
                row = cur.fetchone()
            except Exception as profile_error:
                # If profile columns don't exist, fall back to basic query
                logger.warning(f"Profile columns missing, using basic query for user {user_id}: {profile_error}")
                q = """
                    SELECT id, email, display_name, created_at, user_plan, trial_active, trial_expires_at, trial_used_permanently
                    FROM users WHERE id = %s
                """
                q = adapt_placeholders(db, q)
                cur = conn.cursor()
                cur.execute(q, (user_id,))
                row = cur.fetchone()
            
            if not row:
                return None
            
            # Row tuple indices consistent across drivers
            return {
                "id": row[0],
                "email": row[1],
                "display_name": row[2],
                "created_at": row[3],
                "user_plan": row[4] or "bronze",
                "plan": row[4] or "bronze",  # Use user_plan as plan
                "trial_active": bool(row[5]) if row[5] is not None else False,
                "trial_expires_at": from_db_ts(db, row[6]),
                "trial_used_permanently": bool(row[7]) if row[7] is not None else False,
                # Profile image data from database
                "profile_image": row[8] if len(row) > 8 else None,
                "profile_image_data": row[9] if len(row) > 9 else None,
                # Set defaults for missing columns
                "stripe_customer_id": None,
                "plan_type": row[4] or "bronze",
            }
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        return None

def db_set_user_plan(user_id, plan: str):
    """
    Update user's subscription plan in database.
    Updates both new 'plan' column and legacy columns for compatibility.
    """
    if not user_id or not plan:
        return False
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for plan update")
            return False
            
        conn = db.get_connection()
        try:
            # Update user plan (only update existing columns)
            q = """
                UPDATE users 
                SET user_plan = %s 
                WHERE id = %s
            """
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (plan, user_id))
            conn.commit()
            
            logger.info(f"Updated user {user_id} plan to {plan}")
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to update plan for user {user_id}: {e}")
        return False

def db_attach_stripe_customer_id(user_id, customer_id: str):
    """
    Associate Stripe customer ID with user account.
    Note: stripe_customer_id column doesn't exist in current schema, function disabled.
    """
    logger.warning("Stripe customer ID storage not available - column missing from schema")
    return False  # Disabled until column is added to schema

def db_find_user_by_stripe_customer(customer_id: str):
    """
    Find user by Stripe customer ID.
    Returns dict with user info or None if not found.
    """
    if not customer_id:
        return None
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for Stripe customer lookup")
            return None
            
        conn = db.get_connection()
        try:
            q = "SELECT id, email, plan FROM users WHERE stripe_customer_id = %s"
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (customer_id,))
            row = cur.fetchone()
            
            if not row:
                return None
                
            return {
                "id": row[0],
                "email": row[1],
                "plan": row[2] or "bronze"
            }
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to find user by Stripe customer {customer_id}: {e}")
        return None

def db_get_trial_state(user_id):
    """
    Get trial state for user.
    Returns tuple (trial_active, trial_expires_at).
    """
    if not user_id:
        return (False, None)
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for trial state lookup")
            return (False, None)
            
        conn = db.get_connection()
        try:
            q = "SELECT trial_active, trial_expires_at FROM users WHERE id = %s"
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (user_id,))
            row = cur.fetchone()
            
            if not row:
                return (False, None)
                
            return (bool(row[0]) if row[0] is not None else False, from_db_ts(db, row[1]))
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to get trial state for user {user_id}: {e}")
        return (False, None)

def db_set_trial(user_id, active: bool, expires_at):
    """
    Set trial state for user.
    Used to activate/deactivate the 5-hour trial.
    """
    if not user_id:
        return False
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for trial state update")
            return False
            
        conn = db.get_connection()
        try:
            q = "UPDATE users SET trial_active = %s, trial_expires_at = %s WHERE id = %s"
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (to_db_bool(db, active), to_db_ts(db, expires_at), user_id))
            conn.commit()
            
            logger.info(f"Set trial for user {user_id}: active={active}, expires={expires_at}")
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to set trial for user {user_id}: {e}")
        return False

def db_get_user_plan(user_id):
    """
    Get user's current plan, checking both new and legacy columns.
    Returns the plan string or 'bronze' as default.
    """
    if not user_id:
        return "bronze"
        
    try:
        db = get_database()
        if not db:
            return "bronze"
            
        conn = db.get_connection()
        try:
            q = "SELECT plan, user_plan, plan_type FROM users WHERE id = %s"
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (user_id,))
            row = cur.fetchone()
            
            if not row:
                return "bronze"
            
            # Prefer new plan column, fallback to legacy columns
            plan = row[0] or row[1] or row[2] or "bronze"
            
            # Map legacy plan names to new tier system
            plan_mapping = {
                'foundation': 'bronze',
                'free': 'bronze',
                'premium': 'silver',
                'growth': 'silver',
                'enterprise': 'gold',
                'max': 'gold'
            }
            
            return plan_mapping.get(plan, plan)
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to get plan for user {user_id}: {e}")
        return "bronze"

def db_migrate_user_plan(user_id):
    """
    Migrate user from legacy plan names to new Bronze/Silver/Gold system.
    Returns True if migration was performed.
    """
    if not user_id:
        return False
        
    try:
        user_data = db_fetch_user_row(user_id)
        if not user_data:
            return False
            
        # Check if migration is needed
        current_plan = user_data.get('plan') or user_data.get('user_plan') or user_data.get('plan_type')
        
        plan_mapping = {
            'foundation': 'bronze',
            'free': 'bronze',
            'premium': 'silver',
            'growth': 'silver',
            'enterprise': 'gold',
            'max': 'gold'
        }
        
        if current_plan in plan_mapping:
            new_plan = plan_mapping[current_plan]
            if db_set_user_plan(user_id, new_plan):
                logger.info(f"Migrated user {user_id} from {current_plan} to {new_plan}")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Failed to migrate plan for user {user_id}: {e}")
        return False

def db_add_artistic_time(user_id, credits_amount):
    """
    Add trainer credits to user's account.
    Credits are stored in session for immediate use.
    """
    if not user_id or not credits_amount:
        return False
        
    try:
        # For now, we'll add credits to the session since that's where the current system tracks them
        # In the future, this could be enhanced to store in database for persistence
        from flask import session
        
        current_credits = session.get('artistic_time', 0)
        new_credits = current_credits + int(credits_amount)
        session['artistic_time'] = new_credits
        
        logger.info(f"💎 Added {credits_amount} trainer credits to user {user_id} (total: {new_credits})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add trainer credits to user {user_id}: {e}")
        return False