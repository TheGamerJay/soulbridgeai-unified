"""
Authentication Models
User data models and database operations
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

from shared.database.connection import get_database
from shared.utils.helpers import hash_password, verify_password, validate_email, calculate_trial_expiry

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User model"""
    id: Optional[int] = None
    email: str = ""
    password_hash: str = ""
    password_salt: str = ""
    user_plan: str = "bronze"
    trial_active: bool = False
    trial_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True

class UserRepository:
    """User database operations"""
    
    def __init__(self):
        self.db = get_database()
    
    def create_user(self, email: str, password: str, user_plan: str = "bronze") -> Optional[User]:
        """Create new user"""
        try:
            # Validate email
            if not validate_email(email):
                logger.error(f"Invalid email format: {email}")
                return None
            
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                logger.error(f"User already exists: {email}")
                return None
            
            # Hash password
            password_data = hash_password(password)
            
            # Create user record
            query = """
                INSERT INTO users (email, password_hash, password_salt, user_plan, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            
            now = datetime.now(timezone.utc)
            result = self.db.execute_query(
                query,
                (email.lower(), password_data['hash'], password_data['salt'], user_plan, now)
            )
            
            if result > 0:
                # Get the created user
                user = self.get_user_by_email(email)
                logger.info(f"✅ User created successfully: {email}")
                return user
            else:
                logger.error(f"❌ Failed to create user: {email}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error creating user {email}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            query = """
                SELECT id, email, password_hash, password_salt, user_plan, 
                       trial_active, trial_expires_at, created_at, last_login, is_active
                FROM users WHERE email = ?
            """
            
            result = self.db.execute_query(query, (email.lower(),), fetch='one')
            
            if result:
                if isinstance(result, tuple):
                    # SQLite tuple result
                    return User(
                        id=result[0],
                        email=result[1],
                        password_hash=result[2],
                        password_salt=result[3],
                        user_plan=result[4],
                        trial_active=bool(result[5]),
                        trial_expires_at=result[6],
                        created_at=result[7],
                        last_login=result[8],
                        is_active=bool(result[9]) if result[9] is not None else True
                    )
                else:
                    # PostgreSQL dict result
                    return User(
                        id=result['id'],
                        email=result['email'],
                        password_hash=result['password_hash'],
                        password_salt=result['password_salt'],
                        user_plan=result['user_plan'],
                        trial_active=bool(result['trial_active']),
                        trial_expires_at=result['trial_expires_at'],
                        created_at=result['created_at'],
                        last_login=result['last_login'],
                        is_active=bool(result.get('is_active', True))
                    )
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error getting user by email {email}: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            query = """
                SELECT id, email, password_hash, password_salt, user_plan, 
                       trial_active, trial_expires_at, created_at, last_login, is_active
                FROM users WHERE id = ?
            """
            
            result = self.db.execute_query(query, (user_id,), fetch='one')
            
            if result:
                if isinstance(result, tuple):
                    return User(
                        id=result[0],
                        email=result[1],
                        password_hash=result[2],
                        password_salt=result[3],
                        user_plan=result[4],
                        trial_active=bool(result[5]),
                        trial_expires_at=result[6],
                        created_at=result[7],
                        last_login=result[8],
                        is_active=bool(result[9]) if result[9] is not None else True
                    )
                else:
                    return User(
                        id=result['id'],
                        email=result['email'],
                        password_hash=result['password_hash'],
                        password_salt=result['password_salt'],
                        user_plan=result['user_plan'],
                        trial_active=bool(result['trial_active']),
                        trial_expires_at=result['trial_expires_at'],
                        created_at=result['created_at'],
                        last_login=result['last_login'],
                        is_active=bool(result.get('is_active', True))
                    )
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error getting user by ID {user_id}: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                logger.warning(f"⚠️ Authentication failed - user not found: {email}")
                return None
            
            if not user.is_active:
                logger.warning(f"⚠️ Authentication failed - user inactive: {email}")
                return None
            
            # Verify password
            if verify_password(password, user.password_hash, user.password_salt):
                # Update last login
                self.update_last_login(user.id)
                logger.info(f"✅ User authenticated successfully: {email}")
                return user
            else:
                logger.warning(f"⚠️ Authentication failed - wrong password: {email}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error authenticating user {email}: {e}")
            return None
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            query = "UPDATE users SET last_login = ? WHERE id = ?"
            result = self.db.execute_query(query, (datetime.now(timezone.utc), user_id))
            return result > 0
        except Exception as e:
            logger.error(f"❌ Error updating last login for user {user_id}: {e}")
            return False
    
    def activate_trial(self, user_id: int, trial_hours: int = 5) -> bool:
        """Activate trial for user"""
        try:
            trial_expires = calculate_trial_expiry(trial_hours)
            query = """
                UPDATE users 
                SET trial_active = ?, trial_expires_at = ? 
                WHERE id = ? AND user_plan = 'bronze'
            """
            
            result = self.db.execute_query(query, (True, trial_expires, user_id))
            
            if result > 0:
                logger.info(f"✅ Trial activated for user {user_id}, expires: {trial_expires}")
                return True
            else:
                logger.warning(f"⚠️ Trial activation failed for user {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error activating trial for user {user_id}: {e}")
            return False
    
    def update_user_plan(self, user_id: int, new_plan: str) -> bool:
        """Update user's subscription plan"""
        try:
            query = "UPDATE users SET user_plan = ? WHERE id = ?"
            result = self.db.execute_query(query, (new_plan, user_id))
            
            if result > 0:
                logger.info(f"✅ User plan updated to {new_plan} for user {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Plan update failed for user {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error updating plan for user {user_id}: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            query = "UPDATE users SET is_active = ? WHERE id = ?"
            result = self.db.execute_query(query, (False, user_id))
            
            if result > 0:
                logger.info(f"✅ User {user_id} deactivated")
                return True
            else:
                logger.warning(f"⚠️ User deactivation failed for user {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error deactivating user {user_id}: {e}")
            return False