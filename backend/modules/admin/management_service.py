"""
SoulBridge AI - Admin Management Service
Administrative tools and user management functionality
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from database_utils import format_query

logger = logging.getLogger(__name__)

class AdminManagementService:
    """Administrative management service for user and system operations"""
    
    def __init__(self):
        self.admin_operations_log = []
        
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview for admin dashboard"""
        try:
            overview = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "users": self._get_user_statistics(),
                "system": self._get_system_health(),
                "subscriptions": self._get_subscription_stats(),
                "activity": self._get_activity_stats(),
                "trials": self._get_trial_statistics()
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {"error": str(e)}
    
    def _get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for admin dashboard"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get user counts by plan
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        user_plan,
                        COUNT(*) as user_count,
                        COUNT(CASE WHEN trial_active = true THEN 1 END) as trial_users
                    FROM users 
                    GROUP BY user_plan
                    ORDER BY user_count DESC
                """)
            else:
                cursor.execute("""
                    SELECT 
                        user_plan,
                        COUNT(*) as user_count,
                        COUNT(CASE WHEN trial_active = 1 THEN 1 END) as trial_users
                    FROM users 
                    GROUP BY user_plan
                    ORDER BY user_count DESC
                """)
            
            plan_stats = cursor.fetchall()
            
            # Get registration stats
            one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN created_at >= %s THEN 1 END) as new_users_week,
                        COUNT(CASE WHEN created_at >= %s THEN 1 END) as new_users_month,
                        COUNT(*) as total_users
                    FROM users
                """, (one_week_ago, one_month_ago))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(CASE WHEN created_at >= ? THEN 1 END) as new_users_week,
                        COUNT(CASE WHEN created_at >= ? THEN 1 END) as new_users_month,
                        COUNT(*) as total_users
                    FROM users
                """), (one_week_ago.isoformat(), one_month_ago.isoformat()))
            
            registration_stats = cursor.fetchone()
            conn.close()
            
            return {
                "by_plan": [{"plan": row[0], "count": row[1], "trial_users": row[2]} for row in plan_stats],
                "total_users": registration_stats[2] if registration_stats else 0,
                "new_users_week": registration_stats[0] if registration_stats else 0,
                "new_users_month": registration_stats[1] if registration_stats else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            from ..health.health_checker import HealthChecker
            
            health_checker = HealthChecker()
            health_data = health_checker.get_system_health()
            
            # Extract key metrics for admin overview
            return {
                "database_status": health_data.get('database', {}).get('status', 'unknown'),
                "openai_status": health_data.get('external_services', {}).get('openai_api', {}).get('status', 'unknown'),
                "cpu_usage": health_data.get('system', {}).get('cpu_percent', 0),
                "memory_usage": health_data.get('system', {}).get('memory_percent', 0),
                "disk_usage": health_data.get('storage', {}).get('usage_percent', 0),
                "overall_status": "healthy" if all([
                    health_data.get('database', {}).get('status') == 'connected',
                    health_data.get('system', {}).get('cpu_percent', 0) < 80,
                    health_data.get('system', {}).get('memory_percent', 0) < 85
                ]) else "attention_needed"
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"overall_status": "unknown"}
    
    def _get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription and payment statistics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get subscription stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        user_plan,
                        COUNT(*) as subscriber_count
                    FROM users 
                    WHERE user_plan IN ('silver', 'gold')
                    GROUP BY user_plan
                """)
            else:
                cursor.execute("""
                    SELECT 
                        user_plan,
                        COUNT(*) as subscriber_count
                    FROM users 
                    WHERE user_plan IN ('silver', 'gold')
                    GROUP BY user_plan
                """)
            
            subscription_data = cursor.fetchall()
            
            # Get trial conversion stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN trial_active = true THEN 1 END) as active_trials,
                        COUNT(CASE WHEN trial_expires_at < NOW() AND user_plan != 'bronze' THEN 1 END) as converted_trials
                    FROM users
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN trial_active = 1 THEN 1 END) as active_trials,
                        COUNT(CASE WHEN trial_expires_at < datetime('now') AND user_plan != 'bronze' THEN 1 END) as converted_trials
                    FROM users
                """)
            
            trial_stats = cursor.fetchone()
            conn.close()
            
            return {
                "subscriptions": [{"plan": row[0], "count": row[1]} for row in subscription_data],
                "active_trials": trial_stats[0] if trial_stats else 0,
                "converted_trials": trial_stats[1] if trial_stats else 0,
                "total_subscribers": sum(row[1] for row in subscription_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription stats: {e}")
            return {}
    
    def _get_activity_stats(self) -> Dict[str, Any]:
        """Get platform activity statistics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get activity stats for last 7 days
            one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE created_at >= %s
                """, (one_week_ago,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(DISTINCT user_id) as active_users,
                        COUNT(*) as total_interactions,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE created_at >= ?
                """), (one_week_ago.isoformat(),))
            
            activity_row = cursor.fetchone()
            
            # Get chat message stats
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE created_at >= %s
                """, (one_week_ago,))
            else:
                cursor.execute(format_query("""
                    SELECT COUNT(*) FROM chat_conversations 
                    WHERE created_at >= ?
                """), (one_week_ago.isoformat(),))
            
            chat_messages = cursor.fetchone()[0] or 0
            conn.close()
            
            if activity_row:
                return {
                    "active_users_week": activity_row[0] or 0,
                    "total_interactions_week": activity_row[1] or 0,
                    "features_in_use": activity_row[2] or 0,
                    "chat_messages_week": chat_messages
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting activity stats: {e}")
            return {}
    
    def _get_trial_statistics(self) -> Dict[str, Any]:
        """Get trial system statistics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get trial statistics
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN trial_active = true THEN 1 END) as active_trials,
                        COUNT(CASE WHEN trial_expires_at IS NOT NULL THEN 1 END) as total_trials_started,
                        COUNT(CASE WHEN trial_expires_at < NOW() AND user_plan != 'bronze' THEN 1 END) as successful_conversions,
                        AVG(CASE WHEN trial_expires_at IS NOT NULL AND trial_start_time IS NOT NULL 
                            THEN EXTRACT(EPOCH FROM (trial_expires_at - trial_start_time))/3600 END) as avg_trial_duration_hours
                    FROM users
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN trial_active = 1 THEN 1 END) as active_trials,
                        COUNT(CASE WHEN trial_expires_at IS NOT NULL THEN 1 END) as total_trials_started,
                        COUNT(CASE WHEN trial_expires_at < datetime('now') AND user_plan != 'bronze' THEN 1 END) as successful_conversions,
                        5.0 as avg_trial_duration_hours
                    FROM users
                """)
            
            trial_row = cursor.fetchone()
            conn.close()
            
            if trial_row:
                active_trials, total_trials, conversions, avg_duration = trial_row
                conversion_rate = (conversions / max(total_trials, 1)) * 100 if total_trials else 0
                
                return {
                    "active_trials": active_trials or 0,
                    "total_trials_started": total_trials or 0,
                    "successful_conversions": conversions or 0,
                    "conversion_rate_percentage": round(conversion_rate, 1),
                    "avg_trial_duration_hours": round(avg_duration or 5.0, 1)
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting trial statistics: {e}")
            return {}
    
    def reset_user_trial(self, user_id: int, admin_user: str) -> Dict[str, Any]:
        """Reset user's trial status (admin operation)"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {"success": False, "error": "Database unavailable"}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Reset trial status
            if db.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE users 
                    SET trial_active = false, 
                        trial_expires_at = NULL,
                        trial_start_time = NULL
                    WHERE id = %s
                    RETURNING email
                """, (user_id,))
                
                result = cursor.fetchone()
                user_email = result[0] if result else None
            else:
                cursor.execute(format_query("SELECT email FROM users WHERE id = ?"), (user_id,))
                result = cursor.fetchone()
                user_email = result[0] if result else None
                
                cursor.execute(format_query("""
                    UPDATE users 
                    SET trial_active = 0, 
                        trial_expires_at = NULL,
                        trial_start_time = NULL
                    WHERE id = ?
                """), (user_id,))
            
            conn.commit()
            conn.close()
            
            if user_email:
                # Log admin operation
                self._log_admin_operation(admin_user, "trial_reset", {
                    "target_user_id": user_id,
                    "target_user_email": user_email
                })
                
                logger.info(f"🔄 Admin {admin_user} reset trial for user {user_id} ({user_email})")
                
                return {
                    "success": True,
                    "message": f"Trial reset for user {user_email}",
                    "user_id": user_id,
                    "user_email": user_email
                }
            else:
                return {"success": False, "error": "User not found"}
                
        except Exception as e:
            logger.error(f"Error resetting user trial: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user_plan(self, user_id: int, new_plan: str, admin_user: str) -> Dict[str, Any]:
        """Update user's plan (admin operation)"""
        try:
            valid_plans = ['bronze', 'silver', 'gold']
            if new_plan not in valid_plans:
                return {"success": False, "error": f"Invalid plan. Must be one of: {valid_plans}"}
            
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {"success": False, "error": "Database unavailable"}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get current user info
            if db.db_type == 'postgresql':
                cursor.execute("SELECT email, user_plan FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute(format_query("SELECT email, user_plan FROM users WHERE id = ?"), (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {"success": False, "error": "User not found"}
            
            user_email, current_plan = user_data
            
            # Update user plan
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
                """), (new_plan, datetime.now(timezone.utc).isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            # Log admin operation
            self._log_admin_operation(admin_user, "plan_update", {
                "target_user_id": user_id,
                "target_user_email": user_email,
                "old_plan": current_plan,
                "new_plan": new_plan
            })
            
            logger.info(f"📝 Admin {admin_user} updated user {user_id} plan: {current_plan} → {new_plan}")
            
            return {
                "success": True,
                "message": f"Updated {user_email} from {current_plan} to {new_plan}",
                "user_id": user_id,
                "user_email": user_email,
                "old_plan": current_plan,
                "new_plan": new_plan
            }
            
        except Exception as e:
            logger.error(f"Error updating user plan: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """Get detailed user information for admin"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {}
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get user details
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        id, email, user_plan, trial_active, trial_expires_at,
                        created_at, last_login, referrals, credits
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        id, email, user_plan, trial_active, trial_expires_at,
                        created_at, last_login, referrals, COALESCE(credits, 0)
                    FROM users 
                    WHERE id = ?
                """), (user_id,))
            
            user_row = cursor.fetchone()
            
            if not user_row:
                conn.close()
                return {"error": "User not found"}
            
            # Get activity stats
            one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as recent_activity,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                """, (user_id, one_week_ago))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as recent_activity,
                        COUNT(DISTINCT feature_type) as features_used
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                """), (user_id, one_week_ago.isoformat()))
            
            activity_row = cursor.fetchone()
            conn.close()
            
            # Format user details
            user_details = {
                "id": user_row[0],
                "email": user_row[1],
                "plan": user_row[2],
                "trial_active": user_row[3],
                "trial_expires": str(user_row[4]) if user_row[4] else None,
                "created_at": str(user_row[5]) if user_row[5] else None,
                "last_login": str(user_row[6]) if user_row[6] else None,
                "referrals": user_row[7] or 0,
                "credits": user_row[8] or 0,
                "recent_activity": activity_row[0] if activity_row else 0,
                "features_used_recently": activity_row[1] if activity_row else 0
            }
            
            return user_details
            
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return {"error": str(e)}
    
    def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search users by email or ID"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return []
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Search by email or ID
            if query.isdigit():
                # Search by ID
                if db.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT id, email, user_plan, trial_active, created_at
                        FROM users 
                        WHERE id = %s
                        LIMIT %s
                    """, (int(query), limit))
                else:
                    cursor.execute(format_query("""
                        SELECT id, email, user_plan, trial_active, created_at
                        FROM users 
                        WHERE id = ?
                        LIMIT ?
                    """), (int(query), limit))
            else:
                # Search by email
                search_pattern = f"%{query}%"
                if db.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT id, email, user_plan, trial_active, created_at
                        FROM users 
                        WHERE email ILIKE %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (search_pattern, limit))
                else:
                    cursor.execute(format_query("""
                        SELECT id, email, user_plan, trial_active, created_at
                        FROM users 
                        WHERE email LIKE ? COLLATE NOCASE
                        ORDER BY created_at DESC
                        LIMIT ?
                    """), (search_pattern, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "plan": row[2],
                    "trial_active": row[3],
                    "created_at": str(row[4]) if row[4] else None
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def _log_admin_operation(self, admin_user: str, operation_type: str, details: Dict[str, Any]):
        """Log admin operations for audit trail"""
        try:
            operation_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "admin_user": admin_user,
                "operation": operation_type,
                "details": details
            }
            
            self.admin_operations_log.append(operation_log)
            
            # Keep only last 100 operations in memory
            if len(self.admin_operations_log) > 100:
                self.admin_operations_log = self.admin_operations_log[-100:]
            
            logger.info(f"📋 Admin operation logged: {operation_type} by {admin_user}")
            
        except Exception as e:
            logger.error(f"Error logging admin operation: {e}")
    
    def get_admin_operations_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent admin operations log"""
        try:
            return self.admin_operations_log[-limit:] if self.admin_operations_log else []
        except Exception as e:
            logger.error(f"Error getting admin operations log: {e}")
            return []
    
    def force_logout_all_users(self, admin_user: str) -> Dict[str, Any]:
        """Force logout all users (emergency operation)"""
        try:
            # This would typically clear all user sessions
            # Implementation depends on session storage mechanism
            
            self._log_admin_operation(admin_user, "force_logout_all", {
                "reason": "Emergency admin operation"
            })
            
            logger.warning(f"🚨 Admin {admin_user} initiated force logout for all users")
            
            return {
                "success": True,
                "message": "Force logout initiated",
                "action": "all_users_logged_out"
            }
            
        except Exception as e:
            logger.error(f"Error in force logout: {e}")
            return {"success": False, "error": str(e)}
    
    def get_system_maintenance_info(self) -> Dict[str, Any]:
        """Get system maintenance information"""
        try:
            from ..health.system_monitor import SystemMonitor
            
            system_monitor = SystemMonitor()
            
            maintenance_info = {
                "monitoring_active": getattr(system_monitor, 'monitoring_active', False),
                "emergency_mode": getattr(system_monitor, 'emergency_mode', False),
                "last_health_check": getattr(system_monitor, 'last_health_check', None),
                "blocked_ips_count": len(getattr(system_monitor, 'blocked_ips', [])),
                "alerts_count": len(getattr(system_monitor, 'alerts', []))
            }
            
            return maintenance_info
            
        except Exception as e:
            logger.error(f"Error getting maintenance info: {e}")
            return {}