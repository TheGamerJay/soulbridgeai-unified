"""
Authentication Services
Business logic for authentication operations
"""
import logging
from typing import Optional
from datetime import datetime, timezone

from shared.utils.helpers import validate_password_strength, is_trial_expired, log_action
from .models import User, UserRepository

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication business logic"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def register_user(self, email: str, password: str, user_plan: str = "bronze") -> Optional[User]:
        """Register new user with validation"""
        try:
            # Validate password strength
            password_validation = validate_password_strength(password)
            if not password_validation['is_valid']:
                logger.error(f"Password validation failed for {email}: {password_validation['errors']}")
                return None
            
            # Create user
            user = self.user_repo.create_user(email, password, user_plan)
            
            if user:
                log_action(
                    user_id=user.id,
                    action='user_registered',
                    details={
                        'email': email,
                        'plan': user_plan,
                        'password_score': password_validation['score']
                    }
                )
                logger.info(f"✅ User registered successfully: {email}")
            
            return user
        
        except Exception as e:
            logger.error(f"❌ Registration service error for {email}: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user and update trial status"""
        try:
            user = self.user_repo.authenticate_user(email, password)
            
            if user:
                # Check and update trial status if expired
                if user.trial_active and is_trial_expired(user.trial_expires_at):
                    logger.info(f"Trial expired for user {user.id}, deactivating")
                    self._deactivate_expired_trial(user.id)
                    user.trial_active = False
                
                log_action(
                    user_id=user.id,
                    action='user_authenticated',
                    details={
                        'email': email,
                        'plan': user.user_plan,
                        'trial_active': user.trial_active
                    }
                )
            
            return user
        
        except Exception as e:
            logger.error(f"❌ Authentication service error for {email}: {e}")
            return None
    
    def activate_trial(self, user_id: int, trial_hours: int = 5) -> bool:
        """Activate trial for user with business logic"""
        try:
            # Get user to verify eligibility
            user = self.user_repo.get_user_by_id(user_id)
            
            if not user:
                logger.error(f"User not found for trial activation: {user_id}")
                return False
            
            # Only bronze users can activate trial
            if user.user_plan != 'bronze':
                logger.error(f"Trial activation denied - user not bronze tier: {user_id}")
                return False
            
            # Check if trial already active and not expired
            if user.trial_active and not is_trial_expired(user.trial_expires_at):
                logger.error(f"Trial activation denied - trial already active: {user_id}")
                return False
            
            # Activate trial
            success = self.user_repo.activate_trial(user_id, trial_hours)
            
            if success:
                log_action(
                    user_id=user_id,
                    action='trial_activated',
                    details={
                        'duration_hours': trial_hours,
                        'email': user.email
                    }
                )
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Trial activation service error for user {user_id}: {e}")
            return False
    
    def update_user_plan(self, user_id: int, new_plan: str) -> bool:
        """Update user subscription plan with validation"""
        try:
            valid_plans = ['bronze', 'silver', 'gold']
            if new_plan not in valid_plans:
                logger.error(f"Invalid plan specified: {new_plan}")
                return False
            
            success = self.user_repo.update_user_plan(user_id, new_plan)
            
            if success:
                # If upgrading to paid plan, deactivate trial
                if new_plan in ['silver', 'gold']:
                    self._deactivate_trial(user_id)
                
                log_action(
                    user_id=user_id,
                    action='plan_updated',
                    details={'new_plan': new_plan}
                )
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Plan update service error for user {user_id}: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with trial status check"""
        try:
            user = self.user_repo.get_user_by_id(user_id)
            
            if user and user.trial_active and is_trial_expired(user.trial_expires_at):
                # Trial expired, update status
                self._deactivate_expired_trial(user_id)
                user.trial_active = False
            
            return user
        
        except Exception as e:
            logger.error(f"❌ Get user service error for user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with trial status check"""
        try:
            user = self.user_repo.get_user_by_email(email)
            
            if user and user.trial_active and is_trial_expired(user.trial_expires_at):
                # Trial expired, update status
                self._deactivate_expired_trial(user.id)
                user.trial_active = False
            
            return user
        
        except Exception as e:
            logger.error(f"❌ Get user by email service error for {email}: {e}")
            return None
    
    def _deactivate_expired_trial(self, user_id: int) -> None:
        """Internal method to deactivate expired trial"""
        try:
            query = "UPDATE users SET trial_active = ? WHERE id = ?"
            db = self.user_repo.db
            db.execute_query(query, (False, user_id))
            
            log_action(
                user_id=user_id,
                action='trial_expired',
                details={'auto_deactivated': True}
            )
            
            logger.info(f"✅ Trial deactivated for user {user_id} (expired)")
        
        except Exception as e:
            logger.error(f"❌ Error deactivating expired trial for user {user_id}: {e}")
    
    def _deactivate_trial(self, user_id: int) -> None:
        """Internal method to deactivate trial (for plan upgrades)"""
        try:
            query = "UPDATE users SET trial_active = ?, trial_expires_at = ? WHERE id = ?"
            db = self.user_repo.db
            db.execute_query(query, (False, None, user_id))
            
            log_action(
                user_id=user_id,
                action='trial_deactivated',
                details={'reason': 'plan_upgrade'}
            )
            
            logger.info(f"✅ Trial deactivated for user {user_id} (plan upgrade)")
        
        except Exception as e:
            logger.error(f"❌ Error deactivating trial for user {user_id}: {e}")
    
    def validate_user_access(self, user_id: int, required_plan: str) -> bool:
        """Validate if user has access to required plan level"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Calculate effective plan
            effective_plan = user.user_plan
            if user.trial_active and user.user_plan == 'bronze':
                effective_plan = 'gold'  # Trial gives Gold access
            
            # Check tier hierarchy
            tier_hierarchy = {'bronze': 1, 'silver': 2, 'gold': 3}
            
            user_tier = tier_hierarchy.get(effective_plan, 0)
            required_tier = tier_hierarchy.get(required_plan, 999)
            
            return user_tier >= required_tier
        
        except Exception as e:
            logger.error(f"❌ Access validation error for user {user_id}: {e}")
            return False