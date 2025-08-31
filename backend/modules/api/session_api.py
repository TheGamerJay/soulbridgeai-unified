"""
SoulBridge AI - Session API
Session management and user status endpoints
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from flask import session, request

logger = logging.getLogger(__name__)

class SessionAPI:
    """Handles session-related API operations"""
    
    def __init__(self):
        pass
    
    def refresh_session(self) -> Dict[str, Any]:
        """Refresh user session data"""
        try:
            if not session.get('user_authenticated') or not session.get('user_id'):
                return {
                    "success": False,
                    "error": "Not authenticated",
                    "action": "login_required"
                }
            
            user_id = session.get('user_id')
            
            # Get fresh user data from database
            user_data = self._get_fresh_user_data(user_id)
            if not user_data:
                return {
                    "success": False,
                    "error": "User not found",
                    "action": "re_authenticate"
                }
            
            # Update session with fresh data
            self._update_session_data(user_data)
            
            logger.info(f"🔄 Session refreshed for user {user_id}")
            
            return {
                "success": True,
                "message": "Session refreshed successfully",
                "user_data": self._get_safe_user_data(user_data)
            }
            
        except Exception as e:
            logger.error(f"Error refreshing session: {e}")
            return {
                "success": False,
                "error": "Failed to refresh session"
            }
    
    def get_user_status(self) -> Dict[str, Any]:
        """Get current user status and session info"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "authenticated": False,
                    "user_id": None,
                    "plan": "bronze",
                    "trial_active": False
                }
            
            user_id = session.get('user_id')
            
            # Get current user status
            status = {
                "authenticated": True,
                "user_id": user_id,
                "email": session.get('user_email'),
                "plan": session.get('user_plan', 'bronze'),
                "trial_active": session.get('trial_active', False),
                "trial_expires": session.get('trial_expires_at'),
                "referrals": session.get('referrals', 0),
                "credits": session.get('artistic_time', 0),
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(
                status["plan"], 
                status["trial_active"], 
                session.get('user_addons', [])
            )
            
            status["effective_access"] = effective_access
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting user status: {e}")
            return {
                "authenticated": False,
                "error": str(e)
            }
    
    def clear_session(self) -> Dict[str, Any]:
        """Clear user session"""
        try:
            user_id = session.get('user_id')
            
            # Clear session
            session.clear()
            
            logger.info(f"🧹 Session cleared for user {user_id}")
            
            return {
                "success": True,
                "message": "Session cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return {
                "success": False,
                "error": "Failed to clear session"
            }
    
    def sync_trial_session(self) -> Dict[str, Any]:
        """Sync trial status with session"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            
            # Get current trial status from database
            trial_data = self._get_trial_status(user_id)
            
            if trial_data:
                # Update session with current trial status
                session['trial_active'] = trial_data['trial_active']
                session['trial_expires_at'] = trial_data['trial_expires_at']
                
                logger.info(f"🔄 Trial session synced for user {user_id}")
                
                return {
                    "success": True,
                    "trial_active": trial_data['trial_active'],
                    "trial_expires_at": trial_data['trial_expires_at'],
                    "message": "Trial status synced"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not sync trial status"
                }
            
        except Exception as e:
            logger.error(f"Error syncing trial session: {e}")
            return {
                "success": False,
                "error": "Failed to sync trial status"
            }
    
    def logout_on_close(self) -> Dict[str, Any]:
        """Handle logout on browser close"""
        try:
            user_id = session.get('user_id')
            
            # Update last activity
            if user_id:
                self._update_last_activity(user_id)
            
            # Clear session
            session.clear()
            
            logger.info(f"👋 Logout on close for user {user_id}")
            
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in logout on close: {e}")
            return {
                "success": False,
                "error": "Logout failed"
            }
    
    def _get_fresh_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get fresh user data from database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return None
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT id, email, user_plan, trial_active, trial_expires_at, 
                           referrals, credits, last_login
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, email, user_plan, trial_active, trial_expires_at,
                           referrals, COALESCE(credits, 0), last_login
                    FROM users 
                    WHERE id = ?
                """, (user_id,))
            
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
                    "last_login": row[7]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting fresh user data: {e}")
            return None
    
    def _update_session_data(self, user_data: Dict[str, Any]):
        """Update session with fresh user data"""
        try:
            session['user_id'] = user_data['id']
            session['user_email'] = user_data['email']
            session['user_plan'] = user_data['user_plan']
            session['trial_active'] = user_data['trial_active']
            session['trial_expires_at'] = str(user_data['trial_expires_at']) if user_data['trial_expires_at'] else None
            session['referrals'] = user_data['referrals']
            session['artistic_time'] = user_data['credits']
            
            # Update effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(
                user_data['user_plan'],
                user_data['trial_active'],
                session.get('user_addons', [])
            )
            
            session['access_silver'] = effective_access.get('access_silver', False)
            session['access_gold'] = effective_access.get('access_gold', False)
            
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
    
    def _get_safe_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get safe user data for API response (no sensitive info)"""
        return {
            "id": user_data.get('id'),
            "email": user_data.get('email'),
            "plan": user_data.get('user_plan'),
            "trial_active": user_data.get('trial_active'),
            "referrals": user_data.get('referrals', 0),
            "credits": user_data.get('credits', 0)
        }
    
    def _get_trial_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get current trial status from database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return None
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT trial_active, trial_expires_at 
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT trial_active, trial_expires_at 
                    FROM users 
                    WHERE id = ?
                """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "trial_active": row[0],
                    "trial_expires_at": str(row[1]) if row[1] else None
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting trial status: {e}")
            return None
    
    def _update_last_activity(self, user_id: int):
        """Update user's last activity timestamp"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE users 
                    SET last_login = %s 
                    WHERE id = %s
                """, (datetime.now(timezone.utc), user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET last_login = ? 
                    WHERE id = ?
                """, (datetime.now(timezone.utc).isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last activity: {e}")