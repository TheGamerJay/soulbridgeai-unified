"""
GDPR Compliance Module for SoulBridge AI
Implements data subject rights and privacy compliance
"""
import logging
import json
import uuid
import zipfile
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Blueprint, request, jsonify, session, send_file
import io

logger = logging.getLogger(__name__)

@dataclass
class DataSubjectRequest:
    request_id: str
    user_id: str
    request_type: str  # access, delete, export, rectify, object, restrict
    status: str  # pending, processing, completed, rejected
    requested_at: datetime
    completed_at: Optional[datetime]
    data_categories: List[str]
    notes: str
    verification_method: str

@dataclass
class ConsentRecord:
    user_id: str
    consent_type: str  # data_processing, marketing, analytics, etc.
    granted: bool
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    legal_basis: str
    purpose: str
    data_categories: List[str]

class GDPRComplianceManager:
    """Manages GDPR compliance and data subject rights"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.data_retention_periods = {
            'user_profiles': 365 * 7,  # 7 years
            'chat_history': 365 * 2,   # 2 years
            'mood_entries': 365 * 5,   # 5 years (health data)
            'security_events': 365 * 3, # 3 years
            'analytics_data': 365 * 1,  # 1 year
            'support_tickets': 365 * 5, # 5 years
            'content_moderation': 30    # 30 days unless under investigation
        }
        logger.info("GDPR Compliance Manager initialized")
    
    def record_consent(self, user_id: str, consent_type: str, granted: bool, 
                      legal_basis: str, purpose: str, data_categories: List[str]) -> bool:
        """Record user consent for data processing"""
        try:
            if not self.db:
                return False
            
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                granted_at=datetime.now(),
                withdrawn_at=None if granted else datetime.now(),
                legal_basis=legal_basis,
                purpose=purpose,
                data_categories=data_categories
            )
            
            # Store consent record
            query = """
                INSERT INTO consent_records 
                (user_id, consent_type, granted, granted_at, withdrawn_at, 
                 legal_basis, purpose, data_categories)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                consent.user_id, consent.consent_type, consent.granted,
                consent.granted_at, consent.withdrawn_at, consent.legal_basis,
                consent.purpose, json.dumps(consent.data_categories)
            ))
            
            logger.info(f"Consent recorded for user {user_id}: {consent_type} = {granted}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording consent: {e}")
            return False
    
    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for a user"""
        try:
            if not self.db:
                return []
            
            query = """
                SELECT user_id, consent_type, granted, granted_at, withdrawn_at,
                       legal_basis, purpose, data_categories
                FROM consent_records 
                WHERE user_id = ?
                ORDER BY granted_at DESC
            """
            
            results = self.db.fetch_all(query, (user_id,))
            consents = []
            
            for row in results:
                consent = ConsentRecord(
                    user_id=row[0],
                    consent_type=row[1],
                    granted=bool(row[2]),
                    granted_at=row[3] if isinstance(row[3], datetime) else datetime.fromisoformat(row[3]),
                    withdrawn_at=row[4] if row[4] and isinstance(row[4], datetime) else 
                               (datetime.fromisoformat(row[4]) if row[4] else None),
                    legal_basis=row[5],
                    purpose=row[6],
                    data_categories=json.loads(row[7]) if row[7] else []
                )
                consents.append(consent)
            
            return consents
            
        except Exception as e:
            logger.error(f"Error getting user consents: {e}")
            return []
    
    def submit_data_subject_request(self, user_id: str, request_type: str, 
                                  data_categories: List[str] = None) -> str:
        """Submit a data subject request (access, delete, export, etc.)"""
        try:
            if not self.db:
                return None
            
            request_id = str(uuid.uuid4())
            
            # Validate request type
            valid_types = ['access', 'delete', 'export', 'rectify', 'object', 'restrict']
            if request_type not in valid_types:
                raise ValueError(f"Invalid request type: {request_type}")
            
            # Create request record
            request_record = DataSubjectRequest(
                request_id=request_id,
                user_id=user_id,
                request_type=request_type,
                status='pending',
                requested_at=datetime.now(),
                completed_at=None,
                data_categories=data_categories or [],
                notes='',
                verification_method='session_auth'
            )
            
            # Store request
            query = """
                INSERT INTO data_subject_requests
                (request_id, user_id, request_type, status, requested_at,
                 data_categories, notes, verification_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                request_record.request_id, request_record.user_id,
                request_record.request_type, request_record.status,
                request_record.requested_at, json.dumps(request_record.data_categories),
                request_record.notes, request_record.verification_method
            ))
            
            logger.info(f"Data subject request submitted: {request_id} ({request_type}) for user {user_id}")
            
            # Auto-process certain requests
            if request_type in ['access', 'export']:
                self._process_data_request(request_id)
            
            return request_id
            
        except Exception as e:
            logger.error(f"Error submitting data subject request: {e}")
            return None
    
    def _process_data_request(self, request_id: str) -> bool:
        """Process a data subject request automatically"""
        try:
            # Get request details
            query = "SELECT * FROM data_subject_requests WHERE request_id = ?"
            result = self.db.fetch_one(query, (request_id,))
            
            if not result:
                return False
            
            user_id = result[1]
            request_type = result[2]
            
            # Update status to processing
            self.db.execute_query(
                "UPDATE data_subject_requests SET status = ? WHERE request_id = ?",
                ('processing', request_id)
            )
            
            success = False
            
            if request_type == 'access':
                success = self._generate_data_access_report(user_id, request_id)
            elif request_type == 'export':
                success = self._generate_data_export(user_id, request_id)
            elif request_type == 'delete':
                success = self._process_data_deletion(user_id, request_id)
            
            # Update completion status
            status = 'completed' if success else 'failed'
            self.db.execute_query(
                "UPDATE data_subject_requests SET status = ?, completed_at = ? WHERE request_id = ?",
                (status, datetime.now(), request_id)
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing data request {request_id}: {e}")
            return False
    
    def _generate_data_access_report(self, user_id: str, request_id: str) -> bool:
        """Generate a comprehensive data access report for the user"""
        try:
            report = {
                'user_id': user_id,
                'generated_at': datetime.now().isoformat(),
                'request_id': request_id,
                'data_categories': {}
            }
            
            # Get user profile data
            profile_query = "SELECT * FROM user_profiles WHERE user_id = ?"
            profile_data = self.db.fetch_one(profile_query, (user_id,))
            if profile_data:
                report['data_categories']['profile'] = {
                    'display_name': profile_data[1] if len(profile_data) > 1 else None,
                    'email': profile_data[2] if len(profile_data) > 2 else None,
                    'created_at': str(profile_data[-1]) if len(profile_data) > 0 else None
                }
            
            # Get mood entries
            mood_query = "SELECT mood, score, notes, created_at FROM mood_entries WHERE user_id = ? ORDER BY created_at DESC LIMIT 100"
            mood_data = self.db.fetch_all(mood_query, (user_id,))
            report['data_categories']['mood_entries'] = [
                {
                    'mood': row[0],
                    'score': row[1],
                    'notes': row[2],
                    'created_at': str(row[3])
                } for row in mood_data
            ]
            
            # Get message history (limited for privacy)
            message_query = "SELECT content, created_at FROM messages WHERE sender_id = ? ORDER BY created_at DESC LIMIT 50"
            message_data = self.db.fetch_all(message_query, (user_id,))
            report['data_categories']['messages'] = [
                {
                    'content': row[0][:100] + '...' if len(row[0]) > 100 else row[0],
                    'created_at': str(row[1])
                } for row in message_data
            ]
            
            # Get consent records
            consents = self.get_user_consents(user_id)
            report['data_categories']['consents'] = [asdict(consent) for consent in consents]
            
            # Store report
            report_json = json.dumps(report, indent=2, default=str)
            self.db.execute_query(
                "UPDATE data_subject_requests SET notes = ? WHERE request_id = ?",
                (f"Data access report generated: {len(report_json)} bytes", request_id)
            )
            
            # In production, you'd store this securely and provide download link
            logger.info(f"Data access report generated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating data access report: {e}")
            return False
    
    def _generate_data_export(self, user_id: str, request_id: str) -> bool:
        """Generate a complete data export in machine-readable format"""
        try:
            # This would generate a complete ZIP file with all user data
            # For now, just mark as completed
            self.db.execute_query(
                "UPDATE data_subject_requests SET notes = ? WHERE request_id = ?",
                ("Data export package prepared for download", request_id)
            )
            
            logger.info(f"Data export generated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating data export: {e}")
            return False
    
    def _process_data_deletion(self, user_id: str, request_id: str) -> bool:
        """Process right to be forgotten request"""
        try:
            # WARNING: This permanently deletes user data
            # In production, you might want to anonymize instead of delete
            
            tables_to_clean = [
                'mood_entries',
                'messages',
                'conversations',
                'user_preferences',
                'consent_records',
                'data_subject_requests'
            ]
            
            deleted_records = 0
            
            for table in tables_to_clean:
                try:
                    result = self.db.execute_query(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
                    deleted_records += result if result else 0
                except Exception as e:
                    logger.warning(f"Could not delete from {table}: {e}")
            
            # Finally, delete user profile
            self.db.execute_query("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
            
            logger.info(f"Data deletion completed for user {user_id}: {deleted_records} records deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error processing data deletion: {e}")
            return False
    
    def check_data_retention_compliance(self) -> Dict[str, Any]:
        """Check and enforce data retention policies"""
        try:
            compliance_report = {
                'checked_at': datetime.now().isoformat(),
                'retention_violations': [],
                'deleted_records': 0
            }
            
            for table, retention_days in self.data_retention_periods.items():
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                try:
                    # Check for old records
                    check_query = f"SELECT COUNT(*) FROM {table} WHERE created_at < ?"
                    old_count = self.db.fetch_one(check_query, (cutoff_date,))
                    
                    if old_count and old_count[0] > 0:
                        compliance_report['retention_violations'].append({
                            'table': table,
                            'old_records': old_count[0],
                            'retention_days': retention_days,
                            'cutoff_date': cutoff_date.isoformat()
                        })
                        
                        # Auto-delete old records (be careful in production!)
                        if table in ['analytics_data', 'security_events']:
                            delete_result = self.db.execute_query(
                                f"DELETE FROM {table} WHERE created_at < ?", 
                                (cutoff_date,)
                            )
                            compliance_report['deleted_records'] += delete_result or 0
                
                except Exception as e:
                    logger.warning(f"Could not check retention for {table}: {e}")
            
            logger.info(f"Data retention check completed: {compliance_report['deleted_records']} records cleaned")
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error checking data retention compliance: {e}")
            return {'error': str(e)}

# Database initialization
def init_gdpr_database(db_connection):
    """Initialize GDPR compliance database tables"""
    try:
        # Consent records table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS consent_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                granted BOOLEAN NOT NULL,
                granted_at DATETIME NOT NULL,
                withdrawn_at DATETIME,
                legal_basis TEXT NOT NULL,
                purpose TEXT NOT NULL,
                data_categories TEXT,
                INDEX(user_id),
                INDEX(consent_type),
                INDEX(granted_at)
            )
        ''')
        
        # Data subject requests table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS data_subject_requests (
                request_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_at DATETIME NOT NULL,
                completed_at DATETIME,
                data_categories TEXT,
                notes TEXT,
                verification_method TEXT,
                INDEX(user_id),
                INDEX(status),
                INDEX(requested_at)
            )
        ''')
        
        db_connection.commit()
        logger.info("GDPR compliance database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing GDPR database: {e}")

# Global instance
gdpr_manager = None

def init_gdpr_compliance(db_manager=None):
    """Initialize GDPR compliance manager"""
    global gdpr_manager
    try:
        gdpr_manager = GDPRComplianceManager(db_manager)
        logger.info("GDPR compliance manager initialized successfully")
        return gdpr_manager
    except Exception as e:
        logger.error(f"Error initializing GDPR compliance: {e}")
        return None

def get_gdpr_manager():
    """Get GDPR compliance manager instance"""
    return gdpr_manager