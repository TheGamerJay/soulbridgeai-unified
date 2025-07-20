"""
COPPA Compliance Module for SoulBridge AI
Age verification and parental consent for users under 13
"""
import logging
import json
import uuid
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class AgeVerification:
    user_id: str
    birth_date: datetime
    age_at_registration: int
    verification_method: str  # self_reported, parent_verified
    parent_email: Optional[str]
    parent_consent_status: str  # pending, granted, denied
    parent_consent_date: Optional[datetime]
    consent_token: Optional[str]
    created_at: datetime

@dataclass
class ParentalConsent:
    consent_id: str
    user_id: str
    parent_email: str
    consent_token: str
    status: str  # pending, granted, denied, expired
    requested_at: datetime
    responded_at: Optional[datetime]
    ip_address: str
    verification_code: str

class COPPAComplianceManager:
    """Manages COPPA compliance for users under 13"""
    
    def __init__(self, db_manager=None, email_service=None):
        self.db = db_manager
        self.email_service = email_service
        self.coppa_age_limit = 13  # Users under 13 require parental consent
        self.consent_expiry_days = 365  # Parental consent expires after 1 year
        
        logger.info("COPPA Compliance Manager initialized")
    
    def calculate_age(self, birth_date: datetime) -> int:
        """Calculate age from birth date"""
        today = datetime.now()
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
    def verify_age(self, user_id: str, birth_date: datetime, parent_email: str = None) -> Dict[str, Any]:
        """Verify user age and initiate COPPA compliance if needed"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            age = self.calculate_age(birth_date)
            requires_parental_consent = age < self.coppa_age_limit
            
            # Create age verification record
            verification = AgeVerification(
                user_id=user_id,
                birth_date=birth_date,
                age_at_registration=age,
                verification_method='self_reported',
                parent_email=parent_email,
                parent_consent_status='pending' if requires_parental_consent else 'not_required',
                parent_consent_date=None,
                consent_token=None,
                created_at=datetime.now()
            )
            
            # Store verification record
            query = """
                INSERT INTO age_verifications 
                (user_id, birth_date, age_at_registration, verification_method,
                 parent_email, parent_consent_status, consent_token, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                verification.user_id, verification.birth_date, verification.age_at_registration,
                verification.verification_method, verification.parent_email,
                verification.parent_consent_status, verification.consent_token,
                verification.created_at
            ))
            
            result = {
                'success': True,
                'user_id': user_id,
                'age': age,
                'requires_parental_consent': requires_parental_consent,
                'verification_method': verification.verification_method
            }
            
            if requires_parental_consent:
                if parent_email:
                    # Initiate parental consent process
                    consent_result = self._initiate_parental_consent(user_id, parent_email)
                    result.update(consent_result)
                else:
                    result['error'] = 'Parent email required for users under 13'
                    result['success'] = False
            
            logger.info(f"Age verification completed for user {user_id}: age {age}, consent required: {requires_parental_consent}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying age: {e}")
            return {'success': False, 'error': 'Age verification failed'}
    
    def _initiate_parental_consent(self, user_id: str, parent_email: str) -> Dict[str, Any]:
        """Initiate parental consent process"""
        try:
            consent_id = str(uuid.uuid4())
            consent_token = self._generate_consent_token()
            verification_code = self._generate_verification_code()
            
            # Create parental consent record
            consent = ParentalConsent(
                consent_id=consent_id,
                user_id=user_id,
                parent_email=parent_email,
                consent_token=consent_token,
                status='pending',
                requested_at=datetime.now(),
                responded_at=None,
                ip_address='',  # Will be set when parent responds
                verification_code=verification_code
            )
            
            # Store consent record
            query = """
                INSERT INTO parental_consents
                (consent_id, user_id, parent_email, consent_token, status,
                 requested_at, verification_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                consent.consent_id, consent.user_id, consent.parent_email,
                consent.consent_token, consent.status, consent.requested_at,
                consent.verification_code
            ))
            
            # Send parental consent email
            email_sent = self._send_parental_consent_email(consent)
            
            if email_sent:
                return {
                    'consent_initiated': True,
                    'consent_id': consent_id,
                    'parent_email': parent_email,
                    'message': 'Parental consent email sent. Please check parent email for verification.'
                }
            else:
                return {
                    'consent_initiated': False,
                    'error': 'Failed to send parental consent email'
                }
            
        except Exception as e:
            logger.error(f"Error initiating parental consent: {e}")
            return {'consent_initiated': False, 'error': 'Failed to initiate parental consent'}
    
    def _send_parental_consent_email(self, consent: ParentalConsent) -> bool:
        """Send parental consent email"""
        try:
            if not self.email_service:
                logger.warning("Email service not available, cannot send parental consent email")
                return False
            
            # Create consent URL (in production, use your domain)
            consent_url = f"https://soulbridge.ai/parental-consent?token={consent.consent_token}"
            
            subject = "Parental Consent Required for SoulBridge AI Account"
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .button {{ 
                        background: #28a745; color: white; padding: 12px 24px; 
                        text-decoration: none; border-radius: 5px; display: inline-block; 
                        margin: 20px 0;
                    }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🛡️ Parental Consent Required</h1>
                </div>
                
                <div class="content">
                    <h2>Hello Parent/Guardian,</h2>
                    
                    <p>Your child has requested to create an account on SoulBridge AI, a mental wellness platform. 
                    Under the Children's Online Privacy Protection Act (COPPA), we require your consent before 
                    collecting any personal information from children under 13.</p>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> SoulBridge AI is a mental wellness platform that provides 
                        AI-powered emotional support. While we have strong safety measures, we recommend parental 
                        supervision for young users.
                    </div>
                    
                    <h3>What we collect:</h3>
                    <ul>
                        <li>Basic profile information (name, age)</li>
                        <li>Mood entries and wellness data</li>
                        <li>Chat conversations with AI companions</li>
                        <li>Usage analytics for safety and improvement</li>
                    </ul>
                    
                    <h3>Safety measures:</h3>
                    <ul>
                        <li>AI content filtering and crisis intervention</li>
                        <li>No sharing of personal data with third parties</li>
                        <li>Regular safety monitoring</li>
                        <li>Professional mental health resources provided</li>
                    </ul>
                    
                    <p><strong>Verification Code:</strong> {consent.verification_code}</p>
                    
                    <a href="{consent_url}" class="button">Review and Provide Consent</a>
                    
                    <p>This consent link will expire in 7 days. You can also visit the link above and enter 
                    the verification code manually.</p>
                    
                    <p>If you did not authorize this request or have questions, please contact our support team 
                    at support@soulbridge.ai</p>
                </div>
                
                <div class="footer">
                    <p>SoulBridge AI - Mental Wellness Platform<br>
                    This email was sent regarding COPPA compliance for user account creation.</p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            success = self.email_service.send_email(
                to_email=consent.parent_email,
                subject=subject,
                html_content=html_content
            )
            
            if success:
                logger.info(f"Parental consent email sent to {consent.parent_email}")
            else:
                logger.error(f"Failed to send parental consent email to {consent.parent_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending parental consent email: {e}")
            return False
    
    def process_parental_consent(self, consent_token: str, granted: bool, ip_address: str) -> Dict[str, Any]:
        """Process parental consent response"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Get consent record
            query = "SELECT * FROM parental_consents WHERE consent_token = ? AND status = 'pending'"
            result = self.db.fetch_one(query, (consent_token,))
            
            if not result:
                return {'success': False, 'error': 'Invalid or expired consent token'}
            
            consent_id = result[0]
            user_id = result[1]
            parent_email = result[2]
            
            # Check if consent has expired (7 days)
            requested_at = datetime.fromisoformat(result[5]) if isinstance(result[5], str) else result[5]
            if datetime.now() - requested_at > timedelta(days=7):
                self.db.execute_query(
                    "UPDATE parental_consents SET status = 'expired' WHERE consent_id = ?",
                    (consent_id,)
                )
                return {'success': False, 'error': 'Consent request has expired'}
            
            # Update consent status
            new_status = 'granted' if granted else 'denied'
            self.db.execute_query("""
                UPDATE parental_consents 
                SET status = ?, responded_at = ?, ip_address = ?
                WHERE consent_id = ?
            """, (new_status, datetime.now(), ip_address, consent_id))
            
            # Update age verification record
            self.db.execute_query("""
                UPDATE age_verifications 
                SET parent_consent_status = ?, parent_consent_date = ?
                WHERE user_id = ?
            """, (new_status, datetime.now(), user_id))
            
            # If consent denied, mark user account for deletion
            if not granted:
                self._handle_consent_denial(user_id)
            
            logger.info(f"Parental consent processed: {new_status} for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'consent_status': new_status,
                'processed_at': datetime.now().isoformat(),
                'message': f'Parental consent {new_status} successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing parental consent: {e}")
            return {'success': False, 'error': 'Failed to process consent'}
    
    def _handle_consent_denial(self, user_id: str):
        """Handle parental consent denial by marking account for deletion"""
        try:
            # In production, you might want to:
            # 1. Immediately disable the account
            # 2. Schedule data deletion
            # 3. Send notification to user
            
            self.db.execute_query("""
                UPDATE user_profiles 
                SET account_status = 'consent_denied', updated_at = ?
                WHERE user_id = ?
            """, (datetime.now(), user_id))
            
            logger.info(f"Account marked for deletion due to consent denial: {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling consent denial: {e}")
    
    def check_coppa_compliance(self, user_id: str) -> Dict[str, Any]:
        """Check COPPA compliance status for a user"""
        try:
            if not self.db:
                return {'compliant': False, 'error': 'Database unavailable'}
            
            # Get age verification
            query = "SELECT * FROM age_verifications WHERE user_id = ?"
            result = self.db.fetch_one(query, (user_id,))
            
            if not result:
                return {'compliant': False, 'error': 'No age verification found'}
            
            age_at_registration = result[2]
            parent_consent_status = result[5]
            
            if age_at_registration >= self.coppa_age_limit:
                return {
                    'compliant': True,
                    'reason': 'User is 13 or older',
                    'age_at_registration': age_at_registration
                }
            
            if parent_consent_status == 'granted':
                return {
                    'compliant': True,
                    'reason': 'Parental consent granted',
                    'age_at_registration': age_at_registration,
                    'parent_consent_status': parent_consent_status
                }
            
            return {
                'compliant': False,
                'reason': f'User under 13 without parental consent: {parent_consent_status}',
                'age_at_registration': age_at_registration,
                'parent_consent_status': parent_consent_status
            }
            
        except Exception as e:
            logger.error(f"Error checking COPPA compliance: {e}")
            return {'compliant': False, 'error': 'Failed to check compliance'}
    
    def _generate_consent_token(self) -> str:
        """Generate secure consent token"""
        return hashlib.sha256(f"{uuid.uuid4()}{datetime.now()}".encode()).hexdigest()
    
    def _generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

# Database initialization
def init_coppa_database(db_connection):
    """Initialize COPPA compliance database tables"""
    try:
        # Age verifications table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS age_verifications (
                user_id TEXT PRIMARY KEY,
                birth_date DATE NOT NULL,
                age_at_registration INTEGER NOT NULL,
                verification_method TEXT NOT NULL,
                parent_email TEXT,
                parent_consent_status TEXT NOT NULL,
                parent_consent_date DATETIME,
                consent_token TEXT,
                created_at DATETIME NOT NULL,
                INDEX(age_at_registration),
                INDEX(parent_consent_status)
            )
        ''')
        
        # Parental consents table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS parental_consents (
                consent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                parent_email TEXT NOT NULL,
                consent_token TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                requested_at DATETIME NOT NULL,
                responded_at DATETIME,
                ip_address TEXT,
                verification_code TEXT,
                INDEX(user_id),
                INDEX(consent_token),
                INDEX(status),
                INDEX(requested_at)
            )
        ''')
        
        db_connection.commit()
        logger.info("COPPA compliance database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing COPPA database: {e}")

# Global instance
coppa_manager = None

def init_coppa_compliance(db_manager=None, email_service=None):
    """Initialize COPPA compliance manager"""
    global coppa_manager
    try:
        coppa_manager = COPPAComplianceManager(db_manager, email_service)
        logger.info("COPPA compliance manager initialized successfully")
        return coppa_manager
    except Exception as e:
        logger.error(f"Error initializing COPPA compliance: {e}")
        return None

def get_coppa_manager():
    """Get COPPA compliance manager instance"""
    return coppa_manager