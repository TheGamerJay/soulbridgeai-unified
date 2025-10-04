"""
SoulBridge AI - User API
User-related API endpoints and operations
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from flask import session, request
from database_utils import format_query

logger = logging.getLogger(__name__)

class UserAPI:
    """Handles user-related API operations"""
    
    def __init__(self):
        pass
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get comprehensive user information"""
        try:
            if not session.get('logged_in') or not session.get('user_id'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            
            # Get user data from database
            user_data = self._get_user_data(user_id)
            if not user_data:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(
                user_data['user_plan'],
                user_data['trial_active'],
                session.get('user_addons', [])
            )
            
            # Get usage limits
            from ..tiers.artistic_time import get_feature_limit
            limits = {
                "decoder": get_feature_limit(user_data['user_plan'], "decoder"),
                "fortune": get_feature_limit(user_data['user_plan'], "fortune"),
                "horoscope": get_feature_limit(user_data['user_plan'], "horoscope"),
                "creative_writer": get_feature_limit(user_data['user_plan'], "creative_writer")
            }
            
            return {
                "success": True,
                "user": {
                    "id": user_data['id'],
                    "email": user_data['email'],
                    "plan": user_data['user_plan'],
                    "trial_active": user_data['trial_active'],
                    "trial_expires": user_data['trial_expires_at'],
                    "referrals": user_data['referrals'],
                    "credits": user_data['credits'],
                    "created_at": user_data['created_at'],
                    "last_login": user_data['last_login']
                },
                "access": effective_access,
                "limits": limits
            }
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {
                "success": False,
                "error": "Failed to get user information"
            }
    
    def get_trial_status(self) -> Dict[str, Any]:
        """Get detailed trial status information"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            trial_data = self._get_trial_data(user_id)
            
            if not trial_data:
                return {
                    "success": True,
                    "trial_active": False,
                    "trial_available": False,
                    "message": "No trial data found"
                }
            
            # Calculate trial status
            trial_info = self._calculate_trial_info(trial_data)
            
            return {
                "success": True,
                **trial_info
            }
            
        except Exception as e:
            logger.error(f"Error getting trial status: {e}")
            return {
                "success": False,
                "error": "Failed to get trial status"
            }
    
    def accept_terms(self, terms_version: str) -> Dict[str, Any]:
        """Accept terms of service"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            
            # Save terms acceptance
            success = self._save_terms_acceptance(user_id, terms_version)
            
            if success:
                session['terms_accepted'] = True
                session['terms_version'] = terms_version
                
                logger.info(f"✅ User {user_id} accepted terms version {terms_version}")
                
                return {
                    "success": True,
                    "message": "Terms accepted successfully",
                    "version": terms_version
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to save terms acceptance"
                }
            
        except Exception as e:
            logger.error(f"Error accepting terms: {e}")
            return {
                "success": False,
                "error": "Failed to accept terms"
            }
    
    def get_user_addons(self) -> Dict[str, Any]:
        """Get user's active addons"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            addons = self._get_user_addons(user_id)
            
            return {
                "success": True,
                "addons": addons,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting user addons: {e}")
            return {
                "success": False,
                "error": "Failed to get user addons"
            }
    
    def log_user_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log user action for analytics"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            
            # Use usage tracker to log the action
            from ..analytics.usage_tracker import UsageTracker
            tracker = UsageTracker()
            
            success = tracker.track_feature_usage(user_id, action_type, action_data)
            
            if success:
                return {
                    "success": True,
                    "message": "Action logged successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to log action"
                }
            
        except Exception as e:
            logger.error(f"Error logging user action: {e}")
            return {
                "success": False,
                "error": "Failed to log action"
            }
    
    def check_feature_access(self, feature_name: str) -> Dict[str, Any]:
        """Check if user has access to a specific feature"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "has_access": False,
                    "reason": "not_authenticated"
                }
            
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            # Check feature access
            feature_access_map = {
                'chat': True,  # Available to all
                'voice_chat': effective_access.get('access_silver', False) or effective_access.get('access_gold', False),
                'voice_journaling': effective_access.get('access_silver', False) or effective_access.get('access_gold', False),
                'ai_images': effective_access.get('access_silver', False) or effective_access.get('access_gold', False),
                'meditations': effective_access.get('access_silver', False) or effective_access.get('access_gold', False),
                'analytics': effective_access.get('access_silver', False) or effective_access.get('access_gold', False),
                'mini_studio': effective_access.get('access_gold', False),
                'decoder': True,
                'fortune': True,
                'horoscope': True,
                'creative_writer': True,
                'library': True
            }
            
            has_access = feature_access_map.get(feature_name, False)
            
            return {
                "has_access": has_access,
                "feature": feature_name,
                "user_plan": user_plan,
                "trial_active": trial_active,
                "reason": "access_granted" if has_access else "tier_restriction"
            }
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {
                "has_access": False,
                "reason": "error",
                "error": str(e)
            }
    
    def _get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return None
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.use_postgres:
                # Try with referrals column first, fallback if it doesn't exist
                try:
                    cursor.execute("""
                        SELECT id, email, user_plan, trial_active, trial_expires_at,
                               COALESCE(referrals, 0) as referrals, COALESCE(credits, 0) as credits, 
                               created_at, last_login
                        FROM users 
                        WHERE id = %s
                    """, (user_id,))
                except Exception as e:
                    if "column" in str(e).lower() and "referrals" in str(e).lower():
                        # Close connection and get a new one to avoid aborted transaction
                        conn.close()
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        # Fallback query without referrals column
                        cursor.execute("""
                            SELECT id, email, user_plan, trial_active, trial_expires_at,
                                   0 as referrals, COALESCE(credits, 0) as credits, 
                                   created_at, last_login
                            FROM users 
                            WHERE id = %s
                        """, (user_id,))
                    else:
                        raise
            else:
                cursor.execute(format_query("""
                    SELECT id, email, user_plan, trial_active, trial_expires_at,
                           referrals, COALESCE(credits, 0), created_at, last_login
                    FROM users 
                    WHERE id = ?
                """), (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "user_plan": row[2],
                    "trial_active": row[3],
                    "trial_expires_at": row[4],
                    "referrals": row[5] or 0,
                    "credits": row[6] or 0,
                    "created_at": row[7],
                    "last_login": row[8]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None
    
    def _get_trial_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get trial data from database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return None
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.use_postgres:
                cursor.execute("""
                    SELECT trial_active, trial_expires_at, trial_start_time
                    FROM users
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT trial_active, trial_expires_at, trial_start_time
                    FROM users
                    WHERE id = ?
                """), (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "trial_active": row[0],
                    "trial_expires_at": row[1],
                    "trial_start_time": row[2]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting trial data: {e}")
            return None
    
    def _calculate_trial_info(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trial status and remaining time"""
        try:
            trial_active = trial_data.get('trial_active', False)
            trial_expires = trial_data.get('trial_expires_at')
            
            if not trial_expires:
                return {
                    "trial_active": False,
                    "trial_available": True,
                    "message": "Trial not started"
                }
            
            # Parse expiration time
            if isinstance(trial_expires, str):
                expires_dt = datetime.fromisoformat(trial_expires.replace('Z', '+00:00'))
            else:
                expires_dt = trial_expires
            
            now = datetime.now(timezone.utc)
            time_remaining = expires_dt - now
            
            if time_remaining.total_seconds() > 0 and trial_active:
                return {
                    "trial_active": True,
                    "trial_expires_at": trial_expires,
                    "time_remaining_seconds": int(time_remaining.total_seconds()),
                    "time_remaining_minutes": int(time_remaining.total_seconds() / 60),
                    "message": f"Trial active - {int(time_remaining.total_seconds() / 60)} minutes remaining"
                }
            else:
                return {
                    "trial_active": False,
                    "trial_expired": True,
                    "trial_expires_at": trial_expires,
                    "message": "Trial has expired"
                }
                
        except Exception as e:
            logger.error(f"Error calculating trial info: {e}")
            return {
                "trial_active": False,
                "error": str(e)
            }
    
    def _save_terms_acceptance(self, user_id: int, terms_version: str) -> bool:
        """Save terms acceptance to database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Update terms acceptance
            if db.use_postgres:
                cursor.execute("""
                    UPDATE users
                    SET terms_accepted = true,
                        terms_version = %s,
                        terms_accepted_at = %s
                    WHERE id = %s
                """, (terms_version, datetime.now(timezone.utc), user_id))
            else:
                cursor.execute(format_query("""
                    UPDATE users
                    SET terms_accepted = 1,
                        terms_version = ?,
                        terms_accepted_at = ?
                    WHERE id = ?
                """), (terms_version, datetime.now(timezone.utc).isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving terms acceptance: {e}")
            return False
    
    def _get_user_addons(self, user_id: int) -> List[str]:
        """Get user's active addons"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return []
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.use_postgres:
                cursor.execute("""
                    SELECT addon_type FROM user_addons
                    WHERE user_id = %s AND active = true
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT addon_type FROM user_addons
                    WHERE user_id = ? AND active = 1
                """), (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting user addons: {e}")
            return []
    
    def get_user_plan_info(self) -> Dict[str, Any]:
        """Get user's plan and subscription information"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get subscription details
            subscription_data = self._get_subscription_data(user_id)
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            return {
                "success": True,
                "plan": {
                    "current_plan": user_plan,
                    "trial_active": trial_active,
                    "subscription_active": subscription_data.get('active', False),
                    "subscription_expires": subscription_data.get('expires_at'),
                    "effective_access": effective_access
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting plan info: {e}")
            return {
                "success": False,
                "error": "Failed to get plan information"
            }
    
    def check_feature_limits(self, feature_type: str) -> Dict[str, Any]:
        """Check current usage limits for a feature"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            user_plan = session.get('user_plan', 'bronze')
            
            # Get feature limit
            from ..tiers.artistic_time import get_feature_limit, get_feature_usage_today
            
            daily_limit = get_feature_limit(user_plan, feature_type)
            current_usage = get_feature_usage_today(user_id, feature_type)
            
            remaining = max(0, daily_limit - current_usage) if daily_limit < 999999 else 999999
            
            return {
                "success": True,
                "feature": feature_type,
                "daily_limit": daily_limit,
                "current_usage": current_usage,
                "remaining": remaining,
                "unlimited": daily_limit >= 999999,
                "limit_reached": remaining == 0 and daily_limit < 999999
            }
            
        except Exception as e:
            logger.error(f"Error checking feature limits: {e}")
            return {
                "success": False,
                "error": "Failed to check feature limits"
            }
    
    def _get_subscription_data(self, user_id: int) -> Dict[str, Any]:
        """Get subscription data for user"""
        try:
            # This would integrate with payment system
            # For now, determine based on plan
            user_plan = session.get('user_plan', 'bronze')
            
            return {
                "active": user_plan in ['silver', 'gold'],
                "plan": user_plan,
                "expires_at": None  # Would come from payment system
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription data: {e}")
            return {"active": False}