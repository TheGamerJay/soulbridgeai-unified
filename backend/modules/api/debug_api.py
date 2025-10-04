"""
SoulBridge AI - Debug API
Debug and development endpoints for testing and troubleshooting
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from flask import session, request
from database_utils import format_query

logger = logging.getLogger(__name__)

class DebugAPI:
    """Handles debug and development API operations"""
    
    def __init__(self):
        self.debug_enabled = True  # Would be controlled by environment
        
    def force_session_reset(self) -> Dict[str, Any]:
        """Force reset user session (debug only)"""
        try:
            if not self._is_debug_mode():
                return {
                    "success": False,
                    "error": "Debug mode not enabled"
                }
            
            user_id = session.get('user_id')
            session.clear()
            
            logger.warning(f"🔧 DEBUG: Force session reset for user {user_id}")
            
            return {
                "success": True,
                "message": "Session force reset completed",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error in force session reset: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reset_to_bronze(self) -> Dict[str, Any]:
        """Reset user to bronze tier (debug only)"""
        try:
            if not self._is_debug_mode():
                return {
                    "success": False,
                    "error": "Debug mode not enabled"
                }
            
            user_id = session.get('user_id')
            if not user_id:
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            # Reset to bronze in database
            success = self._update_user_plan(user_id, 'bronze')
            
            if success:
                # Update session
                session['user_plan'] = 'bronze'
                session['trial_active'] = False
                session['access_silver'] = False
                session['access_gold'] = False
                
                logger.warning(f"🔧 DEBUG: Reset user {user_id} to bronze tier")
                
                return {
                    "success": True,
                    "message": "User reset to bronze tier",
                    "user_id": user_id,
                    "new_plan": "bronze"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update user plan"
                }
            
        except Exception as e:
            logger.error(f"Error resetting to bronze: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def upgrade_to_tier(self, tier: str) -> Dict[str, Any]:
        """Upgrade user to specific tier (debug only)"""
        try:
            if not self._is_debug_mode():
                return {
                    "success": False,
                    "error": "Debug mode not enabled"
                }
            
            valid_tiers = ['bronze', 'silver', 'gold']
            if tier not in valid_tiers:
                return {
                    "success": False,
                    "error": f"Invalid tier. Must be one of: {valid_tiers}"
                }
            
            user_id = session.get('user_id')
            if not user_id:
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            # Update user plan
            success = self._update_user_plan(user_id, tier)
            
            if success:
                # Update session
                session['user_plan'] = tier
                
                # Update effective access
                from ..tiers.artistic_time import get_effective_access
                effective_access = get_effective_access(tier, False, [])
                session['access_silver'] = effective_access.get('access_silver', False)
                session['access_gold'] = effective_access.get('access_gold', False)
                
                logger.warning(f"🔧 DEBUG: Upgraded user {user_id} to {tier} tier")
                
                return {
                    "success": True,
                    "message": f"User upgraded to {tier} tier",
                    "user_id": user_id,
                    "new_plan": tier
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update user plan"
                }
            
        except Exception as e:
            logger.error(f"Error upgrading to tier: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reset_trial_state(self) -> Dict[str, Any]:
        """Reset trial state (debug only)"""
        try:
            if not self._is_debug_mode():
                return {
                    "success": False,
                    "error": "Debug mode not enabled"
                }
            
            user_id = session.get('user_id')
            if not user_id:
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            # Reset trial in database
            success = self._reset_trial_database(user_id)
            
            if success:
                # Update session
                session['trial_active'] = False
                session['trial_expires_at'] = None
                
                logger.warning(f"🔧 DEBUG: Reset trial state for user {user_id}")
                
                return {
                    "success": True,
                    "message": "Trial state reset",
                    "user_id": user_id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to reset trial state"
                }
            
        except Exception as e:
            logger.error(f"Error resetting trial state: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_current_plan_info(self) -> Dict[str, Any]:
        """Get current plan information (debug)"""
        try:
            if not session.get('user_authenticated'):
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
            
            user_id = session.get('user_id')
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            return {
                "success": True,
                "user_id": user_id,
                "plan_info": {
                    "current_plan": user_plan,
                    "trial_active": trial_active,
                    "trial_expires": session.get('trial_expires_at'),
                    "effective_access": effective_access,
                    "session_data": {
                        "access_silver": session.get('access_silver', False),
                        "access_gold": session.get('access_gold', False),
                        "artistic_time": session.get('artistic_time', 0)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting current plan info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def refresh_session_debug(self) -> Dict[str, Any]:
        """Refresh session with debug info"""
        try:
            if not self._is_debug_mode():
                return {
                    "success": False,
                    "error": "Debug mode not enabled"
                }
            
            # Use session API to refresh
            from .session_api import SessionAPI
            session_api = SessionAPI()
            
            result = session_api.refresh_session()
            
            # Add debug info
            result["debug_info"] = {
                "session_keys": list(session.keys()),
                "request_info": {
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                    "user_agent": request.headers.get('User-Agent', 'unknown')[:100]
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in debug session refresh: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        import os
        return os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    
    def _update_user_plan(self, user_id: int, new_plan: str) -> bool:
        """Update user plan in database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE users 
                    SET user_plan = %s, updated_at = %s
                    WHERE id = %s
                """, (new_plan, datetime.now(timezone.utc), user_id))
            else:
                cursor.execute(format_query("""
                    UPDATE users 
                    SET user_plan = ?, updated_at = ?
                    WHERE id = ?
                """, (new_plan, datetime.now(timezone.utc).isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user plan: {e}")
            return False
    
    def _reset_trial_database(self, user_id: int) -> bool:
        """Reset trial status in database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE users 
                    SET trial_active = false,
                        trial_expires_at = NULL,
                        trial_start_time = NULL
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    UPDATE users 
                    SET trial_active = 0,
                        trial_expires_at = NULL,
                        trial_start_time = NULL
                    WHERE id = ?
                """), (user_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting trial in database: {e}")
            return False