"""
Advanced Security & Authentication Manager for SoulBridge AI
Provides 2FA, audit logging, session management, and security monitoring
"""

import json
import logging
import hashlib
import secrets
import time
import uuid
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from functools import wraps
from flask import request, session, jsonify, g
from werkzeug.security import check_password_hash, generate_password_hash

# Optional imports with fallbacks for CI/CD
try:
    import pyotp
    import qrcode
    from PIL import Image
    TOTP_AVAILABLE = True
except ImportError:
    pyotp = None
    qrcode = None
    Image = None
    TOTP_AVAILABLE = False

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    geoip2 = None
    GEOIP_AVAILABLE = False

try:
    import user_agents
    USER_AGENTS_AVAILABLE = True
except ImportError:
    user_agents = None
    USER_AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_id: str
    user_id: Optional[str]
    event_type: str
    description: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    metadata: Dict[str, Any]
    risk_level: str  # low, medium, high, critical


@dataclass
class LoginAttempt:
    """Login attempt tracking"""
    attempt_id: str
    email: str
    ip_address: str
    user_agent: str
    success: bool
    failure_reason: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class UserSession:
    """Enhanced user session"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool
    metadata: Dict[str, Any]


@dataclass
class SecurityAlert:
    """Security alert"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    user_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    resolved_at: Optional[datetime]


class SecurityManager:
    """Comprehensive security and authentication manager"""
    
    def __init__(self, db_manager=None, app_name="SoulBridge AI"):
        self.db = db_manager
        self.app_name = app_name
        
        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.session_timeout = 3600  # 1 hour
        self.password_min_length = 8
        self.require_2fa_for_admin = True
        
        # In-memory stores for real-time security monitoring
        self.failed_attempts = {}  # IP -> count, timestamp
        self.active_sessions = {}  # session_id -> UserSession
        self.security_alerts = []
        self.blocked_ips = set()
        
        # Initialize GeoIP database if available
        self.geoip_reader = None
        if GEOIP_AVAILABLE:
            try:
                # You would need to download GeoLite2-City.mmdb
                # self.geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')
                pass
            except Exception as e:
                logger.warning(f"GeoIP database not available: {e}")
    
    def get_db_connection(self):
        """Get database connection handling different database types"""
        if not self.db:
            return None
        
        if hasattr(self.db, 'db_manager') and hasattr(self.db.db_manager, 'connection'):
            return self.db.db_manager.connection
        elif hasattr(self.db, 'connection'):
            return self.db.connection
        else:
            return None
    
    def setup_database_tables(self):
        """Set up security-related database tables"""
        if not self.db:
            return
        
        try:
            connection = self.get_db_connection()
            if not connection:
                logger.warning("No database connection available for security tables")
                return
                
            cursor = connection.cursor()
            
            # Security events (audit log)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50),
                    event_type VARCHAR(100) NOT NULL,
                    description TEXT NOT NULL,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    risk_level VARCHAR(20) DEFAULT 'low',
                    metadata JSONB DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Login attempts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    attempt_id VARCHAR(50) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    failure_reason VARCHAR(255),
                    metadata JSONB DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # 2FA secrets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_2fa (
                    user_id VARCHAR(50) PRIMARY KEY,
                    secret_key VARCHAR(255) NOT NULL,
                    backup_codes TEXT[],
                    is_enabled BOOLEAN DEFAULT FALSE,
                    setup_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Security alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id VARCHAR(50) PRIMARY KEY,
                    alert_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    user_id VARCHAR(50),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Password history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_history (
                    history_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_events_user_time ON security_events(user_id, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_events_type_time ON security_events(event_type, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(ip_address, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id, is_active, last_activity DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_alerts_type_time ON security_alerts(alert_type, created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_history_user_time ON password_history(user_id, created_at DESC)")
            
            logger.info("Security database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up security tables: {e}")
            raise
    
    # 2FA/MFA Implementation
    
    def generate_2fa_secret(self, user_id: str, email: str) -> Dict[str, Any]:
        """Generate 2FA secret and QR code for user"""
        if not TOTP_AVAILABLE:
            raise Exception("2FA not available - missing dependencies")
        
        try:
            # Generate secret
            secret = pyotp.random_base32()
            
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=email,
                issuer_name=self.app_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for web display
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            
            # Store in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO user_2fa (user_id, secret_key, backup_codes, is_enabled)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET secret_key = EXCLUDED.secret_key, 
                                  backup_codes = EXCLUDED.backup_codes,
                                  setup_at = CURRENT_TIMESTAMP
                """, (user_id, secret, backup_codes, False))
            
            # Log security event
            self.log_security_event(
                user_id=user_id,
                event_type="2fa_setup_initiated",
                description="2FA setup initiated",
                risk_level="low"
            )
            
            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{img_base64}",
                "backup_codes": backup_codes,
                "manual_entry_key": secret
            }
            
        except Exception as e:
            logger.error(f"Error generating 2FA secret: {e}")
            raise
    
    def verify_2fa_code(self, user_id: str, code: str) -> bool:
        """Verify 2FA code or backup code"""
        if not TOTP_AVAILABLE:
            return False
        
        try:
            if not self.db:
                return False
            
            connection = self.get_db_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("""
                SELECT secret_key, backup_codes, is_enabled 
                FROM user_2fa WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            secret_key, backup_codes, is_enabled = result
            
            if not is_enabled:
                return False
            
            # Try TOTP code first
            totp = pyotp.TOTP(secret_key)
            if totp.verify(code, valid_window=1):  # Allow 1 window tolerance
                # Update last used
                cursor.execute("""
                    UPDATE user_2fa SET last_used = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (user_id,))
                
                self.log_security_event(
                    user_id=user_id,
                    event_type="2fa_success",
                    description="2FA code verified successfully",
                    risk_level="low"
                )
                return True
            
            # Try backup codes
            if backup_codes and code.upper() in backup_codes:
                # Remove used backup code
                backup_codes.remove(code.upper())
                cursor.execute("""
                    UPDATE user_2fa SET backup_codes = %s, last_used = CURRENT_TIMESTAMP 
                    WHERE user_id = %s
                """, (backup_codes, user_id))
                
                self.log_security_event(
                    user_id=user_id,
                    event_type="2fa_backup_code_used",
                    description="2FA backup code used",
                    risk_level="medium"
                )
                return True
            
            # Log failed attempt
            self.log_security_event(
                user_id=user_id,
                event_type="2fa_failed",
                description="2FA code verification failed",
                risk_level="medium"
            )
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying 2FA code: {e}")
            return False
    
    def enable_2fa(self, user_id: str, verification_code: str) -> bool:
        """Enable 2FA after verifying setup code"""
        if not TOTP_AVAILABLE or not self.db:
            return False
        
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("""
                SELECT secret_key FROM user_2fa 
                WHERE user_id = %s AND is_enabled = FALSE
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            secret_key = result[0]
            
            # Verify the code
            totp = pyotp.TOTP(secret_key)
            if totp.verify(verification_code, valid_window=1):
                # Enable 2FA
                cursor.execute("""
                    UPDATE user_2fa SET is_enabled = TRUE 
                    WHERE user_id = %s
                """, (user_id,))
                
                self.log_security_event(
                    user_id=user_id,
                    event_type="2fa_enabled",
                    description="2FA enabled for account",
                    risk_level="low"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enabling 2FA: {e}")
            return False
    
    def disable_2fa(self, user_id: str, password: str) -> bool:
        """Disable 2FA with password confirmation"""
        try:
            if not self.db:
                return False
            
            # Verify password first
            connection = self.get_db_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            if not result or not check_password_hash(result[0], password):
                return False
            
            # Disable 2FA
            cursor.execute("""
                UPDATE user_2fa SET is_enabled = FALSE 
                WHERE user_id = %s
            """, (user_id,))
            
            self.log_security_event(
                user_id=user_id,
                event_type="2fa_disabled",
                description="2FA disabled for account",
                risk_level="medium"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error disabling 2FA: {e}")
            return False
    
    def is_2fa_enabled(self, user_id: str) -> bool:
        """Check if 2FA is enabled for user"""
        try:
            if not self.db:
                return False
            
            connection = self.get_db_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("""
                SELECT is_enabled FROM user_2fa WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            return result and result[0]
            
        except Exception as e:
            logger.error(f"Error checking 2FA status: {e}")
            return False
    
    # Session Management
    
    def create_session(self, user_id: str, remember_me: bool = False) -> str:
        """Create a new user session"""
        try:
            session_id = secrets.token_urlsafe(32)
            ip_address = self.get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            
            # Set expiration time
            if remember_me:
                expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                expires_at = datetime.utcnow() + timedelta(seconds=self.session_timeout)
            
            user_session = UserSession(
                session_id=session_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True,
                metadata={}
            )
            
            # Store in memory
            self.active_sessions[session_id] = user_session
            
            # Store in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return session_id
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO user_sessions 
                    (session_id, user_id, ip_address, user_agent, expires_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, user_id, ip_address, user_agent, expires_at, json.dumps({})))
            
            self.log_security_event(
                user_id=user_id,
                event_type="session_created",
                description="New session created",
                risk_level="low"
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def validate_session(self, session_id: str) -> Optional[UserSession]:
        """Validate and refresh session"""
        try:
            user_session = self.active_sessions.get(session_id)
            
            if not user_session:
                # Try to load from database
                if self.db:
                    connection = self.get_db_connection()
                    if not connection:
                        return None
                    cursor = connection.cursor()
                    cursor.execute("""
                        SELECT user_id, ip_address, user_agent, created_at, 
                               last_activity, expires_at, is_active, metadata
                        FROM user_sessions WHERE session_id = %s
                    """, (session_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        user_session = UserSession(
                            session_id=session_id,
                            user_id=result[0],
                            ip_address=result[1],
                            user_agent=result[2],
                            created_at=result[3],
                            last_activity=result[4],
                            expires_at=result[5],
                            is_active=result[6],
                            metadata=result[7] or {}
                        )
                        self.active_sessions[session_id] = user_session
            
            if not user_session or not user_session.is_active:
                return None
            
            # Check expiration
            if datetime.utcnow() > user_session.expires_at:
                self.invalidate_session(session_id)
                return None
            
            # Update last activity
            user_session.last_activity = datetime.utcnow()
            
            # Update in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return user_session
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = %s
                """, (session_id,))
            
            return user_session
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        try:
            if session_id in self.active_sessions:
                user_session = self.active_sessions[session_id]
                del self.active_sessions[session_id]
                
                self.log_security_event(
                    user_id=user_session.user_id,
                    event_type="session_invalidated",
                    description="Session invalidated",
                    risk_level="low"
                )
            
            # Update database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return
                cursor = connection.cursor()
                cursor.execute("""
                    UPDATE user_sessions SET is_active = FALSE 
                    WHERE session_id = %s
                """, (session_id,))
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
    
    def invalidate_all_user_sessions(self, user_id: str, except_session: str = None):
        """Invalidate all sessions for a user except specified one"""
        try:
            # Remove from memory
            sessions_to_remove = []
            for sid, user_session in self.active_sessions.items():
                if user_session.user_id == user_id and sid != except_session:
                    sessions_to_remove.append(sid)
            
            for sid in sessions_to_remove:
                del self.active_sessions[sid]
            
            # Update database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return
                cursor = connection.cursor()
                if except_session:
                    cursor.execute("""
                        UPDATE user_sessions SET is_active = FALSE 
                        WHERE user_id = %s AND session_id != %s
                    """, (user_id, except_session))
                else:
                    cursor.execute("""
                        UPDATE user_sessions SET is_active = FALSE 
                        WHERE user_id = %s
                    """, (user_id,))
            
            self.log_security_event(
                user_id=user_id,
                event_type="all_sessions_invalidated",
                description="All user sessions invalidated",
                risk_level="medium"
            )
            
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all active sessions for a user"""
        try:
            sessions = []
            
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return []
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT session_id, ip_address, user_agent, created_at, 
                           last_activity, expires_at, is_active
                    FROM user_sessions 
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY last_activity DESC
                """, (user_id,))
                
                for result in cursor.fetchall():
                    session_info = {
                        "session_id": result[0],
                        "ip_address": str(result[1]),
                        "user_agent": result[2],
                        "created_at": result[3].isoformat(),
                        "last_activity": result[4].isoformat(),
                        "expires_at": result[5].isoformat(),
                        "is_current": result[0] == session.get('session_id'),
                        "location": self.get_location_from_ip(str(result[1])),
                        "device_info": self.parse_user_agent(result[2])
                    }
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    # Audit Logging
    
    def log_security_event(self, user_id: Optional[str], event_type: str, 
                          description: str, risk_level: str = "low", 
                          metadata: Dict = None):
        """Log a security event"""
        try:
            event = SecurityEvent(
                event_id=f"event_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                event_type=event_type,
                description=description,
                ip_address=self.get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow(),
                metadata=metadata or {},
                risk_level=risk_level
            )
            
            # Store in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO security_events 
                    (event_id, user_id, event_type, description, ip_address, 
                     user_agent, risk_level, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (event.event_id, event.user_id, event.event_type, 
                      event.description, event.ip_address, event.user_agent,
                      event.risk_level, json.dumps(event.metadata)))
            
            # Check if this event should trigger an alert
            self._check_for_security_alerts(event)
            
            logger.info(f"Security event logged: {event_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def _check_for_security_alerts(self, event: SecurityEvent):
        """Check if security event should trigger an alert"""
        try:
            # Multiple failed login attempts
            if event.event_type == "login_failed":
                recent_failures = self._count_recent_failures(event.ip_address)
                if recent_failures >= 3:
                    self._create_security_alert(
                        alert_type="multiple_failed_logins",
                        severity="medium",
                        title="Multiple Failed Login Attempts",
                        description=f"Multiple failed login attempts from IP {event.ip_address}",
                        user_id=event.user_id,
                        metadata={"ip_address": event.ip_address, "failure_count": recent_failures}
                    )
            
            # High-risk events
            if event.risk_level == "high":
                self._create_security_alert(
                    alert_type="high_risk_event",
                    severity="high",
                    title="High Risk Security Event",
                    description=event.description,
                    user_id=event.user_id,
                    metadata=event.metadata
                )
            
        except Exception as e:
            logger.error(f"Error checking for security alerts: {e}")
    
    def _create_security_alert(self, alert_type: str, severity: str, title: str,
                              description: str, user_id: Optional[str] = None,
                              metadata: Dict = None):
        """Create a security alert"""
        try:
            alert = SecurityAlert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                user_id=user_id,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                resolved_at=None
            )
            
            self.security_alerts.append(alert)
            
            # Store in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO security_alerts 
                    (alert_id, alert_type, severity, title, description, user_id, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (alert.alert_id, alert.alert_type, alert.severity,
                      alert.title, alert.description, alert.user_id,
                      json.dumps(alert.metadata)))
            
            logger.warning(f"Security alert created: {title} ({severity})")
            
        except Exception as e:
            logger.error(f"Error creating security alert: {e}")
    
    # Utility Methods
    
    def get_client_ip(self) -> str:
        """Get client IP address considering proxies"""
        try:
            # Check for forwarded IP headers
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            else:
                return request.remote_addr or '127.0.0.1'
        except:
            return '127.0.0.1'
    
    def get_location_from_ip(self, ip_address: str) -> Dict[str, str]:
        """Get location information from IP address"""
        if not GEOIP_AVAILABLE or not self.geoip_reader:
            return {"country": "Unknown", "city": "Unknown"}
        
        try:
            response = self.geoip_reader.city(ip_address)
            return {
                "country": response.country.name or "Unknown",
                "city": response.city.name or "Unknown",
                "region": response.subdivisions.most_specific.name or "Unknown"
            }
        except:
            return {"country": "Unknown", "city": "Unknown"}
    
    def parse_user_agent(self, user_agent_string: str) -> Dict[str, str]:
        """Parse user agent string"""
        if not USER_AGENTS_AVAILABLE or not user_agent_string:
            return {"browser": "Unknown", "os": "Unknown", "device": "Unknown"}
        
        try:
            ua = user_agents.parse(user_agent_string)
            return {
                "browser": f"{ua.browser.family} {ua.browser.version_string}",
                "os": f"{ua.os.family} {ua.os.version_string}",
                "device": ua.device.family
            }
        except:
            return {"browser": "Unknown", "os": "Unknown", "device": "Unknown"}
    
    def _count_recent_failures(self, ip_address: str, window_minutes: int = 15) -> int:
        """Count recent login failures from IP"""
        try:
            if not self.db:
                return 0
            
            connection = self.get_db_connection()
            if not connection:
                return 0
            cursor = connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = %s AND success = FALSE 
                AND timestamp > NOW() - INTERVAL '%s minutes'
            """, (ip_address, window_minutes))
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error counting recent failures: {e}")
            return 0
    
    # Password and Authentication Methods
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        try:
            return generate_password_hash(password, method='pbkdf2:sha256:600000')
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            # If password_hash doesn't start with hash indicators, it might be plaintext
            if not any(password_hash.startswith(prefix) for prefix in ['pbkdf2:', 'scrypt:', 'argon2:']):
                # This is likely a plaintext password (legacy/development)
                logger.warning("Comparing against plaintext password - this is insecure!")
                return password == password_hash
            
            return check_password_hash(password_hash, password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with enhanced security logging"""
        try:
            ip_address = self.get_client_ip()
            
            # Check for too many failed attempts from this IP
            recent_failures = self._count_recent_failures(ip_address)
            if recent_failures >= self.max_login_attempts:
                self.log_security_event(
                    user_id=None,
                    event_type="login_blocked",
                    description=f"Login blocked due to too many failed attempts from {ip_address}",
                    risk_level="high",
                    metadata={"email": email, "failure_count": recent_failures}
                )
                return {"success": False, "error": "Too many failed attempts. Please try again later."}
            
            # Log login attempt
            attempt = LoginAttempt(
                attempt_id=f"attempt_{uuid.uuid4().hex[:8]}",
                email=email,
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', ''),
                success=False,
                failure_reason=None,
                timestamp=datetime.utcnow(),
                metadata={}
            )
            
            # Try to find user (this would need to be adapted to your user storage system)
            user_data = None
            user_id = None
            
            # For now, return placeholder - this needs integration with your user system
            # You would typically query your user database here
            
            if user_data and self.verify_password(password, user_data.get('password_hash', '')):
                # Successful login
                attempt.success = True
                
                # Log successful login
                self.log_security_event(
                    user_id=user_id,
                    event_type="login_success",
                    description="User login successful",
                    risk_level="low",
                    metadata={"email": email}
                )
                
                # Create session
                session_id = self.create_session(user_id)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "session_id": session_id,
                    "requires_2fa": self.is_2fa_enabled(user_id)
                }
            else:
                # Failed login
                attempt.failure_reason = "Invalid credentials"
                
                # Log failed login
                self.log_security_event(
                    user_id=user_id,
                    event_type="login_failed",
                    description="Login failed - invalid credentials",
                    risk_level="medium",
                    metadata={"email": email}
                )
                
                return {"success": False, "error": "Invalid email or password"}
            
            # Store login attempt in database
            if self.db:
                connection = self.get_db_connection()
                if not connection:
                    return {"success": False, "error": "Database connection error"}
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO login_attempts 
                    (attempt_id, email, ip_address, user_agent, success, failure_reason, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (attempt.attempt_id, attempt.email, attempt.ip_address,
                      attempt.user_agent, attempt.success, attempt.failure_reason,
                      json.dumps(attempt.metadata)))
        
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return {"success": False, "error": "Authentication service error"}
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        issues = []
        score = 0
        
        if len(password) < self.password_min_length:
            issues.append(f"Password must be at least {self.password_min_length} characters long")
        else:
            score += 1
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 1
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 1
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        else:
            score += 1
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        else:
            score += 1
        
        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 2:
            strength = "medium"
        
        return {
            "valid": len(issues) == 0,
            "strength": strength,
            "score": score,
            "issues": issues
        }


# Global security manager instance
security_manager = None


def init_security_features(app, db_manager=None):
    """Initialize security features for Flask app"""
    global security_manager
    
    security_manager = SecurityManager(db_manager, app.config.get('APP_NAME', 'SoulBridge AI'))
    
    # Set up database tables
    if db_manager:
        security_manager.setup_database_tables()
    
    logger.info("Security features initialized")
    
    return security_manager


def require_2fa(f):
    """Decorator to require 2FA for sensitive operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not security_manager:
            return jsonify({"error": "Security not initialized"}), 500
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Check if 2FA is enabled and verified for this session
        if security_manager.is_2fa_enabled(user_id):
            if not session.get('2fa_verified'):
                return jsonify({"error": "2FA verification required"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def security_headers(f):
    """Decorator to add security headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    return decorated_function