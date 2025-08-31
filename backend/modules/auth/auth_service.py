"""
SoulBridge AI - Authentication Service
Extracted from app.py monolith for modular architecture
"""
import os
import logging
import psycopg2
from datetime import datetime, timezone
from flask import session
from ..shared.database import get_database

logger = logging.getLogger(__name__)

class AuthService:
    """Handles authentication business logic"""
    
    def __init__(self):
        self.db = get_database()
    
    def authenticate(self, email: str, password: str) -> dict:
        """Authenticate user credentials"""
        try:
            # Use clean authentication system
            from simple_auth import SimpleAuth
            auth = SimpleAuth(self.db)
            
            result = auth.authenticate(email, password)
            return result
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication system temporarily unavailable"}
    
    def register_user(self, email: str, password: str, form_data: dict) -> dict:
        """Register new user"""
        try:
            # Implementation for user registration
            # This would need to be extracted from the monolith
            pass
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": "Registration system temporarily unavailable"}
    
    def migrate_legacy_plan(self, auth_result: dict):
        """Migrate legacy plan names in database"""
        try:
            raw_plan = auth_result.get('plan_type', 'bronze')
            raw_user_plan = auth_result.get('user_plan', 'bronze')
            
            plan_mapping = {
                'bronze': 'bronze',
                'silver': 'silver', 
                'gold': 'gold'
            }
            
            # Use user_plan field first, fallback to plan_type
            actual_plan = raw_user_plan or raw_plan
            session['user_plan'] = plan_mapping.get(actual_plan, actual_plan or 'bronze')
            session['display_name'] = auth_result.get('display_name', 'User')
            
            # Auto-migrate legacy plans in database
            if raw_plan in plan_mapping or raw_user_plan in plan_mapping:
                self._update_database_plans(auth_result["user_id"], raw_plan, raw_user_plan, plan_mapping)
                
        except Exception as e:
            logger.error(f"Plan migration error: {e}")
    
    def _update_database_plans(self, user_id: int, raw_plan: str, raw_user_plan: str, plan_mapping: dict):
        """Update database with migrated plan names"""
        try:
            if not self.db:
                return
                
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            new_plan_type = plan_mapping.get(raw_plan, raw_plan)
            new_user_plan = plan_mapping.get(raw_user_plan, raw_user_plan)
            
            if self.db.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET plan_type = %s, user_plan = %s 
                    WHERE id = %s AND (plan_type = %s OR user_plan = %s)
                """, (new_plan_type, new_user_plan, user_id, raw_plan, raw_user_plan))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET plan_type = ?, user_plan = ? 
                    WHERE id = ? AND (plan_type = ? OR user_plan = ?)
                """, (new_plan_type, new_user_plan, user_id, raw_plan, raw_user_plan))
                
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"🧼 Migrated legacy database plans for user {user_id}: {raw_plan}/{raw_user_plan} → {new_plan_type}/{new_user_plan}")
            conn.close()
            
        except Exception as e:
            logger.error(f"Database plan update error: {e}")
    
    def restore_trial_status(self, email: str):
        """Restore trial status from database"""
        try:
            session["trial_active"] = False
            
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT trial_started_at, trial_companion, trial_used_permanently, trial_expires_at
                FROM users WHERE email = %s
            """, (email,))
            
            trial_result = cursor.fetchone()
            conn.close()
            
            if trial_result:
                trial_started_at, trial_companion, trial_used_permanently, trial_expires_at = trial_result
                
                if not trial_used_permanently and trial_expires_at:
                    now = datetime.now(timezone.utc)
                    
                    # Handle timezone-aware comparison
                    if hasattr(trial_expires_at, 'tzinfo') and trial_expires_at.tzinfo:
                        expires_dt = trial_expires_at
                    else:
                        expires_dt = trial_expires_at.replace(tzinfo=timezone.utc)
                    
                    if now < expires_dt:
                        # Trial is still active
                        session["trial_active"] = True
                        session["trial_companion"] = trial_companion
                        session["trial_expires_at"] = expires_dt.isoformat()
                        time_remaining = int((expires_dt - now).total_seconds() / 60)
                        logger.info(f"✅ TRIAL RESTORED: {trial_companion} trial active for {time_remaining} minutes")
                    else:
                        logger.info(f"⏰ Trial expired during login for {email}")
                else:
                    logger.info(f"ℹ️ User {email} has no active trial (used_permanently: {trial_used_permanently})")
            else:
                logger.info(f"ℹ️ No trial data found for user {email}")
                
        except Exception as e:
            logger.warning(f"Failed to restore trial status: {e}")
    
    def restore_artistic_time(self, user_id: int):
        """Restore artistic time and trial credits from database"""
        try:
            if not user_id:
                return
                
            from ..tiers.artistic_time import get_artistic_time
            
            total_artistic_time = get_artistic_time(user_id)
            logger.info(f"🎨 RESTORED artistic time for user {user_id}: {total_artistic_time} credits")
            
            # Also restore trial credits to session for backwards compatibility
            if session.get('trial_active', False):
                self._restore_trial_credits(user_id)
                
        except Exception as e:
            logger.warning(f"Failed to restore artistic time: {e}")
    
    def _restore_trial_credits(self, user_id: int):
        """Restore trial credits to session"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT trial_credits FROM users WHERE id = %s", (user_id,))
            trial_credits_result = cursor.fetchone()
            
            if trial_credits_result and trial_credits_result[0] is not None:
                session['trial_credits'] = trial_credits_result[0]
                logger.info(f"🔄 RESTORED trial credits to session: {trial_credits_result[0]}")
            conn.close()
            
        except Exception as e:
            logger.warning(f"Failed to restore trial credits: {e}")
    
    def set_tier_access_flags(self):
        """Set isolated tier access flags to prevent cross-contamination"""
        try:
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Define isolated access flags - trial gives access, but limits stay on plan
            session['access_bronze'] = True  # Everyone gets bronze features
            session['access_silver'] = user_plan in ['silver', 'gold']  # NO trial modification
            session['access_gold'] = user_plan == 'gold'  # NO trial modification
            session['access_trial'] = trial_active
            session.modified = True
            
            logger.info(f"[AUTH] Access flags set: bronze={session['access_bronze']}, silver={session['access_silver']}, gold={session['access_gold']}, trial={session['access_trial']}")
            
        except Exception as e:
            logger.error(f"Failed to set tier access flags: {e}")

def has_accepted_terms() -> bool:
    """Check if user has accepted terms"""
    from flask import session
    
    # Check session first (faster)
    if session.get('terms_accepted'):
        return True
    
    # Check database if session doesn't have it
    try:
        user_id = session.get('user_id')
        if not user_id:
            return False
            
        db = get_database()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if db.is_postgresql():
                cursor.execute("SELECT terms_accepted FROM users WHERE id = %s", (user_id,))
            else:  # SQLite
                cursor.execute("SELECT terms_accepted FROM users WHERE id = ?", (user_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                # Update session cache
                session['terms_accepted'] = True
                return True
                
    except Exception as e:
        logger.error(f"Error checking terms acceptance: {e}")
    
    return False