"""
SoulBridge AI - Privacy Manager
Handles data privacy, user data management, and GDPR compliance
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import json
from database_utils import format_query

logger = logging.getLogger(__name__)

class PrivacyManager:
    """Service for managing user privacy, data protection, and compliance"""
    
    def __init__(self, database=None):
        self.database = database
        self.retention_periods = {
            'user_data': 2555,  # 7 years in days (legal requirement)
            'chat_history': 365,  # 1 year
            'credit_transactions': 2555,  # 7 years (financial records)
            'usage_logs': 90,   # 3 months
            'error_logs': 30,   # 1 month
            'session_data': 30, # 1 month
            'ai_interactions': 365  # 1 year
        }
        self.sensitive_fields = [
            'password', 'email', 'phone', 'address', 'ip_address',
            'device_id', 'session_id', 'auth_token'
        ]
    
    def get_user_data_export(self, user_id: int) -> Dict[str, Any]:
        """Export all user data for GDPR compliance (Right to Data Portability)"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get user profile data
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT id, email, display_name, created_at, user_plan, 
                           trial_active, terms_accepted, terms_accepted_at, 
                           profile_image, theme, language_preference
                    FROM users WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT id, email, display_name, created_at, user_plan, 
                           trial_active, terms_accepted, terms_accepted_at, 
                           profile_image, theme, language_preference
                    FROM users WHERE id = ?
                """), (user_id,))
            
            user_data = cursor.fetchone()
            
            if not user_data:
                conn.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Structure user profile data
            profile_data = {
                'user_id': user_data[0],
                'email': user_data[1],
                'display_name': user_data[2],
                'created_at': user_data[3].isoformat() if user_data[3] else None,
                'subscription_plan': user_data[4],
                'trial_active': bool(user_data[5]) if user_data[5] is not None else False,
                'terms_accepted': bool(user_data[6]) if user_data[6] is not None else False,
                'terms_accepted_at': user_data[7].isoformat() if user_data[7] else None,
                'profile_image': user_data[8],
                'theme': user_data[9],
                'language': user_data[10]
            }
            
            # Get usage statistics (aggregated, non-sensitive)
            usage_data = self._get_usage_statistics(cursor, user_id)
            
            # Get wellness gallery contributions (anonymous)
            gallery_data = self._get_wellness_gallery_contributions(cursor, user_id)
            
            # Get subscription data if available
            subscription_data = self._get_subscription_data(cursor, user_id)
            
            # Get referral data
            referral_data = self._get_referral_data(cursor, user_id)
            
            conn.close()
            
            # Compile complete export
            export_data = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'export_version': '1.0',
                'user_profile': profile_data,
                'usage_statistics': usage_data,
                'wellness_contributions': gallery_data,
                'subscription_history': subscription_data,
                'referral_data': referral_data,
                'data_sources': [
                    'user_profile', 'usage_logs', 'wellness_gallery',
                    'subscription_data', 'referral_tracking'
                ],
                'notes': [
                    'Chat conversations are not included to protect privacy',
                    'AI interaction details are anonymized',
                    'IP addresses and sensitive identifiers are excluded',
                    'Data is current as of export timestamp'
                ]
            }
            
            logger.info(f"📊 Data export completed for user {user_id}")
            
            return {
                'success': True,
                'data': export_data,
                'export_size': len(json.dumps(export_data))
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to export user data'
            }
    
    def delete_user_data(self, user_id: int, reason: str = 'user_request') -> Dict[str, Any]:
        """Delete all user data for GDPR compliance (Right to Erasure)"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get user email before deletion for logging
            if self.database.use_postgres:
                cursor.execute("SELECT email FROM users WHERE id = %s"), (user_id,))
            else:
                cursor.execute(format_query("SELECT email FROM users WHERE id = ?"), (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            user_email = user_data[0]
            deletion_timestamp = datetime.now(timezone.utc)
            
            # Tables to clean up (in order due to foreign key constraints)
            cleanup_tables = [
                'terms_log',
                'wellness_gallery',
                'user_subscriptions', 
                'usage_logs',
                'referral_tracking',
                'chat_history',
                'ai_interactions',
                'user_sessions'
            ]
            
            deleted_records = {}
            
            # Delete from related tables first
            for table in cleanup_tables:
                try:
                    if self.database.use_postgres:
                        cursor.execute(f"DELETE FROM {table} WHERE user_id = %s"), (user_id,))
                    else:
                        cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                    deleted_records[table] = cursor.rowcount
                    logger.info(f"Deleted {cursor.rowcount} records from {table}")
                except Exception as table_error:
                    logger.warning(f"Could not delete from {table}: {table_error}")
                    deleted_records[table] = 0
            
            # Finally delete user record
            if self.database.use_postgres:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute(format_query("DELETE FROM users WHERE id = ?"), (user_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'User deletion failed'
                }
            
            # Log deletion for compliance records
            try:
                self._log_data_deletion(cursor, user_id, user_email, reason, 
                                        deletion_timestamp, deleted_records)
            except Exception as log_error:
                logger.warning(f"Could not log deletion: {log_error}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ Complete data deletion for user {user_id} ({user_email}) - reason: {reason}")
            
            return {
                'success': True,
                'message': 'User data deleted successfully',
                'deleted_records': deleted_records,
                'deletion_timestamp': deletion_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error deleting user data for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to delete user data'
            }
    
    def anonymize_user_data(self, user_id: int, reason: str = 'user_request') -> Dict[str, Any]:
        """Anonymize user data while preserving analytics (alternative to deletion)"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            anonymization_timestamp = datetime.now(timezone.utc)
            anonymous_id = f"anon_{user_id}_{int(anonymization_timestamp.timestamp())}"
            
            # Anonymize user profile
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET email = %s,
                        display_name = 'Anonymous User',
                        profile_image = NULL,
                        anonymized_at = %s,
                        anonymization_reason = %s
                    WHERE id = %s
                """), (anonymous_id, anonymization_timestamp, reason, user_id))
            else:
                cursor.execute(format_query("""
                    UPDATE users 
                    SET email = ?,
                        display_name = 'Anonymous User',
                        profile_image = NULL,
                        anonymized_at = ?,
                        anonymization_reason = ?
                    WHERE id = ?
                """), (anonymous_id, anonymization_timestamp, reason, user_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Anonymize wellness gallery contributions (keep content for community)
            try:
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE wellness_gallery 
                        SET user_id = NULL,
                            metadata = jsonb_set(
                                COALESCE(metadata, '{}'),
                                '{anonymized}', 'true'
                            )
                        WHERE user_id = %s
                    """), (user_id,))
                else:
                    cursor.execute(format_query("""
                        UPDATE wellness_gallery 
                        SET user_id = NULL
                        WHERE user_id = ?
                    """), (user_id,))
                anonymized_gallery = cursor.rowcount
            except Exception:
                anonymized_gallery = 0
            
            # Remove sensitive data from logs while keeping usage statistics
            try:
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE usage_logs 
                        SET ip_address = 'anonymized',
                            user_agent = 'anonymized',
                            session_id = 'anonymized'
                        WHERE user_id = %s
                    """), (user_id,))
                else:
                    cursor.execute(format_query("""
                        UPDATE usage_logs 
                        SET ip_address = 'anonymized',
                            user_agent = 'anonymized',
                            session_id = 'anonymized'
                        WHERE user_id = ?
                    """), (user_id,))
                anonymized_logs = cursor.rowcount
            except Exception:
                anonymized_logs = 0
            
            conn.commit()
            conn.close()
            
            logger.info(f"🔒 Data anonymization completed for user {user_id} - reason: {reason}")
            
            return {
                'success': True,
                'message': 'User data anonymized successfully',
                'anonymous_id': anonymous_id,
                'anonymized_gallery_items': anonymized_gallery,
                'anonymized_log_entries': anonymized_logs,
                'anonymization_timestamp': anonymization_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error anonymizing user data for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to anonymize user data'
            }
    
    def get_privacy_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user's current privacy settings"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get privacy-related settings
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT data_sharing_consent, marketing_consent, 
                           analytics_consent, cookie_consent,
                           privacy_settings_updated_at
                    FROM users WHERE id = %s
                """), (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT data_sharing_consent, marketing_consent, 
                           analytics_consent, cookie_consent,
                           privacy_settings_updated_at
                    FROM users WHERE id = ?
                """), (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                data_sharing, marketing, analytics, cookies, updated_at = result
                
                settings = {
                    'data_sharing_consent': bool(data_sharing) if data_sharing is not None else True,
                    'marketing_consent': bool(marketing) if marketing is not None else False,
                    'analytics_consent': bool(analytics) if analytics is not None else True,
                    'cookie_consent': bool(cookies) if cookies is not None else True,
                    'last_updated': updated_at.isoformat() if updated_at else None
                }
            else:
                # Default privacy settings for new users
                settings = {
                    'data_sharing_consent': True,   # Required for service functionality
                    'marketing_consent': False,     # Opt-in only
                    'analytics_consent': True,      # Help improve service
                    'cookie_consent': True,         # Required for functionality
                    'last_updated': None
                }
            
            return {
                'success': True,
                'privacy_settings': settings,
                'retention_periods': self.retention_periods
            }
            
        except Exception as e:
            logger.error(f"Error getting privacy settings for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to load privacy settings'
            }
    
    def update_privacy_settings(self, user_id: int, settings: Dict[str, bool]) -> Dict[str, Any]:
        """Update user's privacy settings"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Update privacy settings
            update_timestamp = datetime.now(timezone.utc)
            
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET data_sharing_consent = %s,
                        marketing_consent = %s,
                        analytics_consent = %s,
                        cookie_consent = %s,
                        privacy_settings_updated_at = %s
                    WHERE id = %s
                """, (
                    settings.get('data_sharing_consent', True),
                    settings.get('marketing_consent', False),
                    settings.get('analytics_consent', True),
                    settings.get('cookie_consent', True),
                    update_timestamp,
                    user_id
                ))
            else:
                cursor.execute(format_query("""
                    UPDATE users 
                    SET data_sharing_consent = ?,
                        marketing_consent = ?,
                        analytics_consent = ?,
                        cookie_consent = ?,
                        privacy_settings_updated_at = ?
                    WHERE id = ?
                """, (
                    settings.get('data_sharing_consent', True),
                    settings.get('marketing_consent', False),
                    settings.get('analytics_consent', True),
                    settings.get('cookie_consent', True),
                    update_timestamp,
                    user_id
                ))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            conn.commit()
            conn.close()
            
            logger.info(f"🔒 Privacy settings updated for user {user_id}")
            
            return {
                'success': True,
                'message': 'Privacy settings updated successfully',
                'updated_at': update_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating privacy settings for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to update privacy settings'
            }
    
    def cleanup_expired_data(self) -> Dict[str, Any]:
        """Clean up expired data based on retention policies"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            cleanup_results = {}
            current_time = datetime.now(timezone.utc)
            
            # Clean up expired data based on retention periods
            cleanup_rules = [
                ('usage_logs', self.retention_periods['usage_logs'], 'created_at'),
                ('error_logs', self.retention_periods['error_logs'], 'created_at'),
                ('session_data', self.retention_periods['session_data'], 'created_at'),
                ('ai_interactions', self.retention_periods['ai_interactions'], 'created_at')
            ]
            
            for table, retention_days, date_column in cleanup_rules:
                try:
                    cutoff_date = current_time - timedelta(days=retention_days)
                    
                    if self.database.use_postgres:
                        cursor.execute(f"""
                            DELETE FROM {table} 
                            WHERE {date_column} < %s
                        """), (cutoff_date,))
                    else:
                        cursor.execute(f"""
                            DELETE FROM {table} 
                            WHERE {date_column} < ?
                        """), (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    cleanup_results[table] = deleted_count
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 Cleaned {deleted_count} expired records from {table}")
                        
                except Exception as cleanup_error:
                    logger.warning(f"Could not cleanup {table}: {cleanup_error}")
                    cleanup_results[table] = 0
            
            conn.commit()
            conn.close()
            
            total_cleaned = sum(cleanup_results.values())
            
            return {
                'success': True,
                'message': f'Cleaned up {total_cleaned} expired records',
                'cleanup_results': cleanup_results,
                'cleanup_timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            return {
                'success': False,
                'error': 'Failed to cleanup expired data'
            }
    
    # Helper methods
    
    def _get_usage_statistics(self, cursor, user_id: int) -> Dict[str, Any]:
        """Get aggregated usage statistics (non-sensitive)"""
        try:
            # This would typically query usage_logs table
            return {
                'total_sessions': 0,
                'features_used': [],
                'account_age_days': 0,
                'last_activity': None
            }
        except Exception:
            return {}
    
    def _get_wellness_gallery_contributions(self, cursor, user_id: int) -> Dict[str, Any]:
        """Get user's wellness gallery contributions"""
        try:
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*), MIN(created_at), MAX(created_at)
                    FROM wellness_gallery 
                    WHERE user_id = %s AND is_approved = TRUE
                """), (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT COUNT(*), MIN(created_at), MAX(created_at)
                    FROM wellness_gallery 
                    WHERE user_id = ? AND is_approved = 1
                """), (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                count, first_contribution, last_contribution = result
                return {
                    'total_contributions': count or 0,
                    'first_contribution': first_contribution.isoformat() if first_contribution else None,
                    'last_contribution': last_contribution.isoformat() if last_contribution else None
                }
            else:
                return {'total_contributions': 0}
                
        except Exception:
            return {'total_contributions': 0}
    
    def _get_subscription_data(self, cursor, user_id: int) -> Dict[str, Any]:
        """Get user's subscription history (non-sensitive)"""
        try:
            # This would typically query subscription tables
            return {
                'current_plan': 'bronze',
                'subscription_start': None,
                'trial_used': False
            }
        except Exception:
            return {}
    
    def _get_referral_data(self, cursor, user_id: int) -> Dict[str, Any]:
        """Get user's referral data"""
        try:
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT referral_code, referral_points
                    FROM users WHERE id = %s
                """), (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT referral_code, referral_points
                    FROM users WHERE id = ?
                """), (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                code, points = result
                return {
                    'referral_code': code,
                    'referral_points': points or 0
                }
            else:
                return {'referral_code': None, 'referral_points': 0}
                
        except Exception:
            return {'referral_code': None, 'referral_points': 0}
    
    def _log_data_deletion(self, cursor, user_id: int, user_email: str, 
                          reason: str, timestamp: datetime, deleted_records: Dict[str, int]):
        """Log data deletion for compliance records"""
        try:
            deletion_log = {
                'user_id': user_id,
                'user_email': user_email,
                'deletion_reason': reason,
                'deleted_records': deleted_records,
                'deletion_timestamp': timestamp.isoformat()
            }
            
            if self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO data_deletion_log 
                    (user_id, user_email, deletion_reason, deletion_details, deleted_at)
                    VALUES (%s, %s, %s, %s, %s)
                """), (user_id, user_email, reason, json.dumps(deletion_log), timestamp))
            else:
                cursor.execute(format_query("""
                    INSERT INTO data_deletion_log 
                    (user_id, user_email, deletion_reason, deletion_details, deleted_at)
                    VALUES (?, ?, ?, ?, ?)
                """), (user_id, user_email, reason, json.dumps(deletion_log), timestamp))
                
        except Exception as log_error:
            logger.warning(f"Could not log data deletion: {log_error}")
    
    def ensure_database_schema(self) -> Dict[str, Any]:
        """Ensure privacy-related database columns and tables exist"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Add privacy columns to users table
            privacy_columns = [
                ('data_sharing_consent', 'BOOLEAN DEFAULT TRUE'),
                ('marketing_consent', 'BOOLEAN DEFAULT FALSE'),
                ('analytics_consent', 'BOOLEAN DEFAULT TRUE'),
                ('cookie_consent', 'BOOLEAN DEFAULT TRUE'),
                ('privacy_settings_updated_at', 'TIMESTAMP'),
                ('anonymized_at', 'TIMESTAMP'),
                ('anonymization_reason', 'TEXT')
            ]
            
            added_columns = []
            
            for column_name, column_def in privacy_columns:
                try:
                    if self.database.use_postgres:
                        cursor.execute(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_def}')
                    else:
                        cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    added_columns.append(column_name)
                except Exception:
                    # Column might already exist
                    pass
            
            # Create data deletion log table
            try:
                if self.database.use_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS data_deletion_log (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            user_email VARCHAR(255) NOT NULL,
                            deletion_reason TEXT,
                            deletion_details JSONB,
                            deleted_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS data_deletion_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            user_email VARCHAR(255) NOT NULL,
                            deletion_reason TEXT,
                            deletion_details TEXT,
                            deleted_at TIMESTAMP NOT NULL,
                            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
            except Exception as table_error:
                logger.warning(f"Could not create data_deletion_log table: {table_error}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"🛠️ Privacy database schema updated - added columns: {added_columns}")
            
            return {
                'success': True,
                'added_columns': added_columns,
                'message': 'Privacy database schema updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error ensuring privacy database schema: {e}")
            return {
                'success': False,
                'error': str(e)
            }