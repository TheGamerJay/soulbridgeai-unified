"""
SoulBridge AI - Relationship Service
Manages relationship profiles with credit-based creation and analysis
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import uuid

logger = logging.getLogger(__name__)

class RelationshipService:
    """Service for managing relationship profiles"""
    
    def __init__(self, database=None, credits_manager=None):
        self.database = database
        self.credits_manager = credits_manager
        self.relationship_cost = 15  # Default from constants
        self.max_profiles_per_user = 50
        self.relationship_types = [
            'romantic', 'family', 'friend', 'colleague', 'mentor', 
            'acquaintance', 'business', 'other'
        ]
        self.connection_strengths = [
            'very_weak', 'weak', 'moderate', 'strong', 'very_strong'
        ]
        self.meeting_frequencies = [
            'daily', 'weekly', 'bi_weekly', 'monthly', 'quarterly',
            'bi_annually', 'annually', 'rarely', 'never'
        ]
    
    def check_access_and_limits(self, user_id: int, user_plan: str, 
                               trial_active: bool, user_addons: list = None) -> Dict[str, Any]:
        """Check if user has access to relationship profiles"""
        try:
            user_addons = user_addons or []
            
            # Check basic access - Silver/Gold tier, addon, or trial
            if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
                return {
                    'has_access': False,
                    'error': 'Relationship Profiles requires Silver/Gold tier, addon, or trial'
                }
            
            # Check artistic time credits
            if self.credits_manager:
                current_credits = self.credits_manager.get_artistic_time(user_id)
                if current_credits < self.relationship_cost:
                    return {
                        'has_access': False,
                        'error': f'Insufficient artistic time. Need {self.relationship_cost} artistic time, you have {current_credits}.'
                    }
            
            # Check profile count limit
            current_count = len(self.get_user_profiles(user_id))
            if current_count >= self.max_profiles_per_user:
                return {
                    'has_access': False,
                    'error': f'Maximum number of profiles reached ({self.max_profiles_per_user})'
                }
            
            return {
                'has_access': True,
                'current_credits': current_credits if self.credits_manager else 0,
                'profiles_count': current_count,
                'profiles_remaining': self.max_profiles_per_user - current_count
            }
            
        except Exception as e:
            logger.error(f"Failed to check relationship profile access: {e}")
            return {
                'has_access': False,
                'error': 'Failed to check access permissions'
            }
    
    def create_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new relationship profile"""
        try:
            # Validate profile data
            validation_result = self._validate_profile_data(profile_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Deduct credits first (prevents abuse)
            if self.credits_manager:
                if not self.credits_manager.deduct_artistic_time(user_id, self.relationship_cost):
                    return {
                        'success': False,
                        'error': 'Failed to deduct artistic time. Please try again.'
                    }
                
                logger.info(f"💳 Deducted {self.relationship_cost} artistic time from user {user_id} for relationship profile")
            
            # Create profile
            profile = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'name': profile_data.get('name'),
                'type': profile_data.get('type'),
                'connection_strength': profile_data.get('connectionStrength'),
                'meeting_frequency': profile_data.get('meetingFrequency'),
                'last_contact': profile_data.get('lastContact'),
                'notes': profile_data.get('notes', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'analysis_data': {},  # For future AI analysis results
                'interaction_history': []  # Track interactions over time
            }
            
            # Save to database or session
            if self.database:
                success = self._save_to_database(user_id, profile)
            else:
                success = self._save_to_session(user_id, profile)
            
            if success:
                logger.info(f"👥 Created relationship profile for user {user_id}: {profile['name']}")
                return {
                    'success': True,
                    'profile': profile,
                    'message': 'Profile created successfully'
                }
            else:
                # Refund credits since creation failed
                if self.credits_manager:
                    self.credits_manager.refund_artistic_time(
                        user_id, self.relationship_cost, 
                        "Relationship profile creation failed"
                    )
                
                return {'success': False, 'error': 'Failed to save profile'}
            
        except Exception as e:
            logger.error(f"Failed to create relationship profile: {e}")
            
            # Refund credits on error
            if self.credits_manager:
                if self.credits_manager.refund_artistic_time(
                    user_id, self.relationship_cost, 
                    "Relationship profile creation failed"
                ):
                    logger.info(f"💰 Refunded {self.relationship_cost} artistic time to user {user_id} due to creation failure")
                else:
                    logger.error(f"❌ Failed to refund artistic time to user {user_id}")
            
            return {
                'success': False, 
                'error': 'Failed to create profile. Your artistic time has been refunded.'
            }
    
    def get_user_profiles(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all relationship profiles for a user"""
        try:
            if self.database:
                return self._get_from_database(user_id)
            else:
                return self._get_from_session(user_id)
            
        except Exception as e:
            logger.error(f"Failed to get user profiles: {e}")
            return []
    
    def get_profile_by_id(self, user_id: int, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get specific relationship profile by ID"""
        try:
            profiles = self.get_user_profiles(user_id)
            
            for profile in profiles:
                if profile.get('id') == profile_id:
                    return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get profile by ID: {e}")
            return None
    
    def update_profile(self, user_id: int, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing relationship profile"""
        try:
            # Get current profile
            current_profile = self.get_profile_by_id(user_id, profile_id)
            if not current_profile:
                return {'success': False, 'error': 'Profile not found'}
            
            # Validate updates
            allowed_fields = [
                'name', 'type', 'connectionStrength', 'meetingFrequency',
                'lastContact', 'notes'
            ]
            
            updated_profile = current_profile.copy()
            
            for field, value in updates.items():
                if field in allowed_fields:
                    # Convert camelCase to snake_case for internal storage
                    internal_field = self._camel_to_snake(field)
                    updated_profile[internal_field] = value
            
            updated_profile['updated_at'] = datetime.now().isoformat()
            
            # Save updates
            if self.database:
                success = self._update_in_database(user_id, profile_id, updated_profile)
            else:
                success = self._update_in_session(user_id, profile_id, updated_profile)
            
            if success:
                logger.info(f"📝 Updated relationship profile {profile_id} for user {user_id}")
                return {'success': True, 'profile': updated_profile}
            else:
                return {'success': False, 'error': 'Failed to update profile'}
            
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_profile(self, user_id: int, profile_id: str) -> Dict[str, Any]:
        """Delete a relationship profile"""
        try:
            # Check if profile exists
            profile = self.get_profile_by_id(user_id, profile_id)
            if not profile:
                return {'success': False, 'error': 'Profile not found'}
            
            # Delete from storage
            if self.database:
                success = self._delete_from_database(user_id, profile_id)
            else:
                success = self._delete_from_session(user_id, profile_id)
            
            if success:
                logger.info(f"🗑️ Deleted relationship profile {profile_id} for user {user_id}")
                return {'success': True, 'message': 'Profile deleted successfully'}
            else:
                return {'success': False, 'error': 'Failed to delete profile'}
            
        except Exception as e:
            logger.error(f"Failed to delete profile: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_profile_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's relationship profiles"""
        try:
            profiles = self.get_user_profiles(user_id)
            
            if not profiles:
                return {
                    'total_profiles': 0,
                    'by_type': {},
                    'by_strength': {},
                    'by_frequency': {},
                    'recent_contacts': 0,
                    'created_this_month': 0
                }
            
            # Calculate statistics
            stats = {
                'total_profiles': len(profiles),
                'by_type': {},
                'by_strength': {},
                'by_frequency': {},
                'recent_contacts': 0,
                'created_this_month': 0
            }
            
            # Count by categories
            current_month = datetime.now().strftime('%Y-%m')
            month_ago = datetime.now() - timedelta(days=30)
            
            for profile in profiles:
                # Count by type
                profile_type = profile.get('type', 'other')
                stats['by_type'][profile_type] = stats['by_type'].get(profile_type, 0) + 1
                
                # Count by connection strength
                strength = profile.get('connection_strength', 'moderate')
                stats['by_strength'][strength] = stats['by_strength'].get(strength, 0) + 1
                
                # Count by meeting frequency
                frequency = profile.get('meeting_frequency', 'rarely')
                stats['by_frequency'][frequency] = stats['by_frequency'].get(frequency, 0) + 1
                
                # Count recent contacts
                last_contact = profile.get('last_contact')
                if last_contact:
                    try:
                        contact_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                        if contact_date >= month_ago:
                            stats['recent_contacts'] += 1
                    except:
                        pass
                
                # Count created this month
                created_at = profile.get('created_at')
                if created_at and created_at.startswith(current_month):
                    stats['created_this_month'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get profile statistics: {e}")
            return {'error': str(e)}
    
    def search_profiles(self, user_id: int, query: str) -> List[Dict[str, Any]]:
        """Search user's relationship profiles"""
        try:
            profiles = self.get_user_profiles(user_id)
            
            if not query.strip():
                return profiles
            
            query_lower = query.lower().strip()
            matching_profiles = []
            
            for profile in profiles:
                # Search in name
                name = profile.get('name', '').lower()
                
                # Search in notes
                notes = profile.get('notes', '').lower()
                
                # Search in type
                profile_type = profile.get('type', '').lower()
                
                if (query_lower in name or 
                    query_lower in notes or 
                    query_lower in profile_type):
                    matching_profiles.append(profile)
            
            logger.info(f"🔍 Found {len(matching_profiles)} matching profiles for user {user_id}")
            return matching_profiles
            
        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            return []
    
    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate relationship profile data"""
        try:
            # Required fields
            required_fields = ['name', 'type']
            for field in required_fields:
                if field not in profile_data or not profile_data[field]:
                    return {'valid': False, 'error': f'Missing required field: {field}'}
            
            # Validate name
            name = profile_data.get('name', '').strip()
            if not name or len(name) < 1:
                return {'valid': False, 'error': 'Name is required'}
            
            if len(name) > 100:
                return {'valid': False, 'error': 'Name must be 100 characters or less'}
            
            # Validate type
            profile_type = profile_data.get('type')
            if profile_type not in self.relationship_types:
                return {'valid': False, 'error': f'Invalid relationship type: {profile_type}'}
            
            # Validate connection strength (optional)
            connection_strength = profile_data.get('connectionStrength')
            if connection_strength and connection_strength not in self.connection_strengths:
                return {'valid': False, 'error': f'Invalid connection strength: {connection_strength}'}
            
            # Validate meeting frequency (optional)
            meeting_frequency = profile_data.get('meetingFrequency')
            if meeting_frequency and meeting_frequency not in self.meeting_frequencies:
                return {'valid': False, 'error': f'Invalid meeting frequency: {meeting_frequency}'}
            
            # Validate notes length (optional)
            notes = profile_data.get('notes', '')
            if len(notes) > 1000:
                return {'valid': False, 'error': 'Notes must be 1000 characters or less'}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Profile validation error: {e}")
            return {'valid': False, 'error': 'Failed to validate profile data'}
    
    def _camel_to_snake(self, camel_str: str) -> str:
        """Convert camelCase to snake_case"""
        result = ''
        for i, char in enumerate(camel_str):
            if char.isupper() and i > 0:
                result += '_'
            result += char.lower()
        return result
    
    # Database implementation placeholders
    def _save_to_database(self, user_id: int, profile: Dict[str, Any]) -> bool:
        """Save profile to database (placeholder for future implementation)"""
        # TODO: Implement database storage using user_library table
        # Could use content_type='relationship_profile' with profile data in metadata
        return False
    
    def _get_from_database(self, user_id: int) -> List[Dict[str, Any]]:
        """Get profiles from database (placeholder)"""
        # TODO: Implement database retrieval
        return []
    
    def _update_in_database(self, user_id: int, profile_id: str, profile: Dict[str, Any]) -> bool:
        """Update profile in database (placeholder)"""
        # TODO: Implement database update
        return False
    
    def _delete_from_database(self, user_id: int, profile_id: str) -> bool:
        """Delete profile from database (placeholder)"""
        # TODO: Implement database deletion
        return False
    
    # Session implementation (current fallback)
    def _save_to_session(self, user_id: int, profile: Dict[str, Any]) -> bool:
        """Save profile to session storage (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        # Placeholder for session-based storage
        return True
    
    def _get_from_session(self, user_id: int) -> List[Dict[str, Any]]:
        """Get profiles from session storage (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        # Placeholder for session-based retrieval
        return []
    
    def _update_in_session(self, user_id: int, profile_id: str, profile: Dict[str, Any]) -> bool:
        """Update profile in session (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        return True
    
    def _delete_from_session(self, user_id: int, profile_id: str) -> bool:
        """Delete profile from session (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        return True
    
    def get_relationship_types(self) -> List[str]:
        """Get available relationship types"""
        return self.relationship_types
    
    def get_connection_strengths(self) -> List[str]:
        """Get available connection strength options"""
        return self.connection_strengths
    
    def get_meeting_frequencies(self) -> List[str]:
        """Get available meeting frequency options"""
        return self.meeting_frequencies