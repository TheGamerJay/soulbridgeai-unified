"""
SoulBridge AI - Terms Service
Manages terms of service acceptance, versioning, and compliance tracking
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class TermsService:
    """Service for managing terms of service acceptance and compliance"""
    
    def __init__(self, database=None):
        self.database = database
        self.current_version = 'v1.0'
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'zh']
        self.required_acceptances = [
            'ai_understanding',
            'terms_privacy', 
            'age_confirmation',
            'responsible_use'
        ]
        
    def has_accepted_terms(self, user_id: int, version: str = None) -> bool:
        """Check if user has accepted current or specific version of terms"""
        try:
            if not self.database:
                logger.warning("Database unavailable - cannot verify terms acceptance")
                return False
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Check specific version or current version
            check_version = version or self.current_version
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT terms_accepted, terms_version 
                    FROM users 
                    WHERE id = %s AND terms_accepted = TRUE
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT terms_accepted, terms_version 
                    FROM users 
                    WHERE id = ? AND terms_accepted = 1
                """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False
            
            accepted, user_version = result
            
            # If checking specific version, must match exactly
            if version:
                return bool(accepted) and user_version == check_version
            
            # For current version check, accept if user has any valid version
            # (version upgrades handled separately)
            return bool(accepted)
            
        except Exception as e:
            logger.error(f"Error checking terms acceptance for user {user_id}: {e}")
            return False
    
    def get_terms_status(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive terms acceptance status for user"""
        try:
            if not self.database:
                return {
                    'accepted': False,
                    'version': None,
                    'accepted_at': None,
                    'language': 'en',
                    'needs_update': True,
                    'current_version': self.current_version
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT terms_accepted, terms_accepted_at, terms_version, terms_language 
                    FROM users WHERE id = %s
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT terms_accepted, terms_accepted_at, terms_version, terms_language 
                    FROM users WHERE id = ?
                """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                accepted, accepted_at, version, language = result
                
                # Check if update needed
                needs_update = not accepted or version != self.current_version
                
                return {
                    'accepted': bool(accepted) if accepted is not None else False,
                    'version': version or 'none',
                    'accepted_at': accepted_at.isoformat() if accepted_at else None,
                    'language': language or 'en',
                    'needs_update': needs_update,
                    'current_version': self.current_version
                }
            else:
                # New user - no terms record
                return {
                    'accepted': False,
                    'version': None,
                    'accepted_at': None,
                    'language': 'en',
                    'needs_update': True,
                    'current_version': self.current_version
                }
                
        except Exception as e:
            logger.error(f"Error getting terms status for user {user_id}: {e}")
            return {
                'accepted': False,
                'version': None,
                'accepted_at': None,
                'language': 'en',
                'needs_update': True,
                'current_version': self.current_version,
                'error': str(e)
            }
    
    def accept_terms(self, user_id: int, acceptances: Dict[str, bool], 
                     language: str = 'en', version: str = None) -> Dict[str, Any]:
        """Record user's acceptance of terms of service"""
        try:
            # Validate all required acceptances
            for field in self.required_acceptances:
                if not acceptances.get(field):
                    return {
                        'success': False,
                        'error': f'Missing required acceptance: {field}',
                        'field': field
                    }
            
            # Validate language
            if language not in self.supported_languages:
                language = 'en'  # Default to English
            
            # Use provided version or current version
            terms_version = version or self.current_version
            acceptance_date = datetime.now(timezone.utc)
            
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Update user's terms acceptance
            try:
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE users 
                        SET terms_accepted = %s, terms_accepted_at = %s, 
                            terms_version = %s, terms_language = %s 
                        WHERE id = %s
                    """, (True, acceptance_date, terms_version, language, user_id))
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET terms_accepted = ?, terms_accepted_at = ?, 
                            terms_version = ?, terms_language = ? 
                        WHERE id = ?
                    """, (True, acceptance_date, terms_version, language, user_id))
                
                if cursor.rowcount == 0:
                    conn.close()
                    return {
                        'success': False,
                        'error': 'User not found'
                    }
                
            except Exception as db_error:
                logger.warning(f"Full terms update failed, trying minimal update: {db_error}")
                # Fallback: try just updating basic acceptance if columns don't exist
                try:
                    if self.database.use_postgres:
                        cursor.execute("UPDATE users SET terms_accepted = %s WHERE id = %s", 
                                       (True, user_id))
                    else:
                        cursor.execute("UPDATE users SET terms_accepted = ? WHERE id = ?", 
                                       (True, user_id))
                except Exception as fallback_error:
                    logger.error(f"Even fallback terms update failed: {fallback_error}")
                    conn.close()
                    return {
                        'success': False,
                        'error': 'Failed to save terms acceptance'
                    }
            
            # Record acceptance details in terms_log if table exists
            try:
                acceptance_details = {
                    'acceptances': acceptances,
                    'user_agent': 'SoulBridge AI App',
                    'ip_address': 'internal',  # Would be populated from request in routes
                    'timestamp': acceptance_date.isoformat()
                }
                
                if self.database.use_postgres:
                    cursor.execute("""
                        INSERT INTO terms_log (user_id, terms_version, language, 
                                               acceptance_details, accepted_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (user_id, terms_version, language, 
                          json.dumps(acceptance_details), acceptance_date))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO terms_log 
                        (user_id, terms_version, language, acceptance_details, accepted_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, terms_version, language, 
                          json.dumps(acceptance_details), acceptance_date))
                          
            except Exception as log_error:
                logger.info(f"Terms log table doesn't exist or failed: {log_error}")
                # Continue without logging - not critical
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Terms accepted by user {user_id} - version {terms_version}, language {language}")
            
            return {
                'success': True,
                'message': 'Terms accepted successfully',
                'version': terms_version,
                'language': language,
                'accepted_at': acceptance_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error accepting terms for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to process terms acceptance'
            }
    
    def revoke_terms_acceptance(self, user_id: int, reason: str = '') -> Dict[str, Any]:
        """Revoke user's terms acceptance (for GDPR compliance)"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Update user's terms acceptance to false
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET terms_accepted = FALSE, 
                        terms_revoked_at = %s,
                        terms_revoke_reason = %s
                    WHERE id = %s
                """, (datetime.now(timezone.utc), reason, user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET terms_accepted = 0,
                        terms_revoked_at = ?,
                        terms_revoke_reason = ?
                    WHERE id = ?
                """, (datetime.now(timezone.utc), reason, user_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            conn.commit()
            conn.close()
            
            logger.info(f"🚫 Terms revoked for user {user_id} - reason: {reason}")
            
            return {
                'success': True,
                'message': 'Terms acceptance revoked',
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error revoking terms for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to revoke terms acceptance'
            }
    
    def get_terms_content(self, language: str = 'en', version: str = None) -> Dict[str, Any]:
        """Get terms content for display"""
        try:
            # Use current version if not specified
            content_version = version or self.current_version
            
            # Validate language
            if language not in self.supported_languages:
                language = 'en'
            
            # Base terms content (would typically be stored in database or files)
            base_terms = {
                'version': content_version,
                'language': language,
                'effective_date': '2024-01-01',
                'last_updated': '2024-01-01',
                'sections': {
                    'acceptance': {
                        'title': 'Acceptance of Terms',
                        'content': 'By using SoulBridge AI, you agree to be bound by these Terms of Service.'
                    },
                    'description': {
                        'title': 'Description of Service',
                        'content': 'SoulBridge AI is an AI-powered wellness and personal growth platform.'
                    },
                    'user_responsibilities': {
                        'title': 'User Responsibilities',
                        'content': 'Users must use the service responsibly and in accordance with applicable laws.'
                    },
                    'privacy': {
                        'title': 'Privacy',
                        'content': 'Your privacy is important to us. Please review our Privacy Policy.'
                    },
                    'ai_disclosure': {
                        'title': 'AI Service Disclosure',
                        'content': 'This service uses artificial intelligence. AI responses may not always be accurate.'
                    },
                    'age_requirements': {
                        'title': 'Age Requirements',
                        'content': 'You must be at least 13 years old to use this service.'
                    },
                    'termination': {
                        'title': 'Termination',
                        'content': 'We reserve the right to terminate accounts that violate these terms.'
                    },
                    'changes': {
                        'title': 'Changes to Terms',
                        'content': 'We may update these terms from time to time.'
                    }
                },
                'required_acceptances': [
                    {
                        'id': 'ai_understanding',
                        'label': 'I understand this service uses AI technology',
                        'required': True
                    },
                    {
                        'id': 'terms_privacy',
                        'label': 'I accept the Terms of Service and Privacy Policy',
                        'required': True
                    },
                    {
                        'id': 'age_confirmation',
                        'label': 'I confirm I am at least 13 years old',
                        'required': True
                    },
                    {
                        'id': 'responsible_use',
                        'label': 'I agree to use this service responsibly',
                        'required': True
                    }
                ]
            }
            
            return {
                'success': True,
                'terms': base_terms
            }
            
        except Exception as e:
            logger.error(f"Error getting terms content: {e}")
            return {
                'success': False,
                'error': 'Failed to load terms content'
            }
    
    def check_terms_update_needed(self, user_id: int) -> Dict[str, Any]:
        """Check if user needs to accept updated terms"""
        try:
            status = self.get_terms_status(user_id)
            
            if not status.get('accepted'):
                return {
                    'update_needed': True,
                    'reason': 'no_acceptance',
                    'current_version': self.current_version,
                    'user_version': status.get('version')
                }
            
            if status.get('version') != self.current_version:
                return {
                    'update_needed': True,
                    'reason': 'version_mismatch',
                    'current_version': self.current_version,
                    'user_version': status.get('version')
                }
            
            return {
                'update_needed': False,
                'current_version': self.current_version,
                'user_version': status.get('version')
            }
            
        except Exception as e:
            logger.error(f"Error checking terms update for user {user_id}: {e}")
            return {
                'update_needed': True,
                'reason': 'error',
                'error': str(e)
            }
    
    def get_acceptance_statistics(self) -> Dict[str, Any]:
        """Get terms acceptance statistics for admin dashboard"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get overall acceptance stats
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN terms_accepted = TRUE THEN 1 ELSE 0 END) as accepted_users,
                        SUM(CASE WHEN terms_version = %s THEN 1 ELSE 0 END) as current_version_users
                    FROM users
                """, (self.current_version,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN terms_accepted = 1 THEN 1 ELSE 0 END) as accepted_users,
                        SUM(CASE WHEN terms_version = ? THEN 1 ELSE 0 END) as current_version_users
                    FROM users
                """, (self.current_version,))
            
            result = cursor.fetchone()
            
            if result:
                total, accepted, current_version = result
                
                stats = {
                    'total_users': total or 0,
                    'accepted_users': accepted or 0,
                    'current_version_users': current_version or 0,
                    'acceptance_rate': round((accepted / total * 100), 2) if total > 0 else 0,
                    'current_version_rate': round((current_version / total * 100), 2) if total > 0 else 0
                }
            else:
                stats = {
                    'total_users': 0,
                    'accepted_users': 0,
                    'current_version_users': 0,
                    'acceptance_rate': 0,
                    'current_version_rate': 0
                }
            
            # Get version breakdown
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT terms_version, COUNT(*) 
                    FROM users 
                    WHERE terms_accepted = TRUE
                    GROUP BY terms_version
                    ORDER BY COUNT(*) DESC
                """)
            else:
                cursor.execute("""
                    SELECT terms_version, COUNT(*) 
                    FROM users 
                    WHERE terms_accepted = 1
                    GROUP BY terms_version
                    ORDER BY COUNT(*) DESC
                """)
            
            version_breakdown = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'success': True,
                'stats': stats,
                'version_breakdown': version_breakdown,
                'current_version': self.current_version
            }
            
        except Exception as e:
            logger.error(f"Error getting acceptance statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def ensure_database_schema(self) -> Dict[str, Any]:
        """Ensure terms-related database columns exist"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Add terms columns to users table if they don't exist
            terms_columns = [
                ('terms_accepted', 'BOOLEAN DEFAULT FALSE'),
                ('terms_accepted_at', 'TIMESTAMP'),
                ('terms_version', "VARCHAR(50) DEFAULT 'v1.0'"),
                ('terms_language', "VARCHAR(10) DEFAULT 'en'"),
                ('terms_revoked_at', 'TIMESTAMP'),
                ('terms_revoke_reason', 'TEXT')
            ]
            
            added_columns = []
            
            for column_name, column_def in terms_columns:
                try:
                    if self.database.use_postgres:
                        cursor.execute(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_def}')
                    else:
                        # SQLite doesn't support IF NOT EXISTS in ALTER TABLE
                        cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    added_columns.append(column_name)
                    
                except Exception as col_error:
                    # Column might already exist
                    logger.debug(f"Column {column_name} might already exist: {col_error}")
            
            # Create terms_log table for detailed logging
            try:
                if self.database.use_postgres:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS terms_log (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            terms_version VARCHAR(50) NOT NULL,
                            language VARCHAR(10) NOT NULL,
                            acceptance_details JSONB,
                            accepted_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            UNIQUE(user_id, terms_version)
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS terms_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            terms_version VARCHAR(50) NOT NULL,
                            language VARCHAR(10) NOT NULL,
                            acceptance_details TEXT,
                            accepted_at TIMESTAMP NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, terms_version)
                        )
                    """)
                    
                logger.info("✅ Terms log table created or exists")
                
            except Exception as table_error:
                logger.warning(f"Could not create terms_log table: {table_error}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"🛠️ Terms database schema updated - added columns: {added_columns}")
            
            return {
                'success': True,
                'added_columns': added_columns,
                'message': 'Database schema updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error ensuring database schema: {e}")
            return {
                'success': False,
                'error': str(e)
            }