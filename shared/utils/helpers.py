"""
Common Utility Functions
Shared helpers used across all modules
"""
import hashlib
import secrets
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Hash password with salt for secure storage"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use SHA-256 with salt for password hashing
    password_salt = password + salt
    password_hash = hashlib.sha256(password_salt.encode()).hexdigest()
    
    return {
        'hash': password_hash,
        'salt': salt
    }

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash"""
    computed_hash = hash_password(password, salt)['hash']
    return computed_hash == stored_hash

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return feedback"""
    result = {
        'is_valid': True,
        'errors': [],
        'score': 0
    }
    
    # Length check
    if len(password) < 8:
        result['errors'].append('Password must be at least 8 characters long')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Character variety checks
    if not re.search(r'[a-z]', password):
        result['errors'].append('Password must contain at least one lowercase letter')
        result['is_valid'] = False
    else:
        result['score'] += 1
        
    if not re.search(r'[A-Z]', password):
        result['errors'].append('Password must contain at least one uppercase letter')
        result['is_valid'] = False
    else:
        result['score'] += 1
        
    if not re.search(r'\d', password):
        result['errors'].append('Password must contain at least one number')
        result['is_valid'] = False
    else:
        result['score'] += 1
    
    # Bonus points for special characters
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['score'] += 1
    
    return result

def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def sanitize_input(input_str: str) -> str:
    """Basic input sanitization"""
    if not isinstance(input_str, str):
        return str(input_str)
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_str)
    return sanitized.strip()

def get_user_ip(request) -> str:
    """Get user IP address from request, handling proxies"""
    # Check for forwarded IP first (behind proxy/load balancer)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or 'unknown'

def format_datetime(dt: Optional[datetime], format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime object to string"""
    if dt is None:
        return 'Never'
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime(format_str)

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    if not dt_str:
        return None
    
    try:
        # Handle ISO format with Z timezone
        if dt_str.endswith('Z'):
            dt_str = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str)
    except ValueError:
        try:
            # Fallback to common formats
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"Could not parse datetime string: {dt_str}")
            return None

def is_trial_expired(trial_expires_at: Optional[datetime]) -> bool:
    """Check if trial has expired"""
    if not trial_expires_at:
        return True
    
    if isinstance(trial_expires_at, str):
        trial_expires_at = parse_datetime(trial_expires_at)
    
    if not trial_expires_at:
        return True
    
    now = datetime.now(timezone.utc)
    # Ensure timezone awareness
    if trial_expires_at.tzinfo is None:
        trial_expires_at = trial_expires_at.replace(tzinfo=timezone.utc)
    
    return now > trial_expires_at

def calculate_trial_expiry(hours: int = 5) -> datetime:
    """Calculate trial expiry time"""
    return datetime.now(timezone.utc) + timedelta(hours=hours)

def log_action(user_id: Optional[str], action: str, details: Dict[str, Any] = None):
    """Log user action for audit trail"""
    log_data = {
        'user_id': user_id or 'anonymous',
        'action': action,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': details or {}
    }
    logger.info(f"USER_ACTION: {log_data}")

def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_bool_conversion(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, int):
        return bool(value)
    return default

def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate string to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_safe_redirect_url(url: str) -> bool:
    """Check if URL is safe for redirect (prevents open redirect attacks)"""
    if not url:
        return False
    
    # Allow relative URLs
    if url.startswith('/'):
        return True
    
    # Block external URLs for security
    if url.startswith(('http://', 'https://', '//')):
        return False
    
    return True