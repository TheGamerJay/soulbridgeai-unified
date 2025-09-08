"""
SoulBridge AI - User Profile Service
Handles user profile data management, display names, and preferences
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class ProfileService:
    """Service for managing user profile data and preferences"""
    
    def __init__(self, database=None):
        self.database = database
        self.required_columns = [
            'profile_image', 'profile_image_data', 'display_name', 
            'theme_preferences', 'trial_started_at', 'trial_companion',
            'trial_used_permanently'
        ]
    
    def get_user_profile(self, user_id: int, include_access: bool = True) -> Dict[str, Any]:
        """Get comprehensive user profile data"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Ensure required columns exist
            self._ensure_profile_columns(cursor)
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            # Get user data
            cursor.execute(f"""
                SELECT id, email, display_name, created_at, email_verified, user_plan,
                       profile_image, profile_image_data, theme_preferences,
                       trial_active, trial_started_at, trial_expires_at, trial_used_permanently
                FROM users WHERE id = {placeholder}
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {'success': False, 'error': 'User not found'}
            
            # Build profile data
            profile_data = {
                'id': result[0],
                'email': result[1],
                'displayName': result[2] or result[1].split('@')[0],  # Fallback to email prefix
                'joinDate': result[3].isoformat() if result[3] else None,
                'createdDate': result[3].isoformat() if result[3] else None,  # Compatibility
                'emailVerified': result[4] or False,
                'plan': result[5] or 'bronze',
                'isActive': True,
                'addons': []  # TODO: Get from session or separate table
            }
            
            # Handle profile image
            profile_image = self._get_profile_image_url(result[6], result[7], user_id)
            profile_data['profileImage'] = profile_image
            
            # Handle theme preferences
            if result[8]:
                try:
                    profile_data['themePreferences'] = json.loads(result[8])
                except:
                    profile_data['themePreferences'] = {}
            else:
                profile_data['themePreferences'] = {}
            
            # Trial information
            profile_data['trial'] = {
                'active': result[9] or False,
                'startedAt': result[10].isoformat() if result[10] else None,
                'expiresAt': result[11].isoformat() if result[11] else None,
                'usedPermanently': result[12] or False
            }
            
            # Add access information if requested
            if include_access:
                profile_data['access'] = self._calculate_access_permissions(profile_data)
            
            logger.info(f"👤 Retrieved profile for user {user_id}")
            
            return {
                'success': True,
                'user': profile_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {'success': False, 'error': f'Failed to retrieve profile: {str(e)}'}
    
    def update_profile(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            # Validate and filter allowed fields
            allowed_fields = ['display_name', 'theme_preferences']
            filtered_updates = {}
            
            for field, value in updates.items():
                if field == 'displayName':
                    filtered_updates['display_name'] = str(value).strip()
                elif field == 'themePreferences' and isinstance(value, dict):
                    filtered_updates['theme_preferences'] = json.dumps(value)
            
            if not filtered_updates:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Update database
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Ensure required columns exist
            self._ensure_profile_columns(cursor)
            
            # Build update query
            set_clauses = []
            values = []
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            for field, value in filtered_updates.items():
                set_clauses.append(f"{field} = {placeholder}")
                values.append(value)
            
            values.append(user_id)  # For WHERE clause
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = {placeholder}"
            logger.info(f"📝 Executing update query: {query} with values: {values}")
            cursor.execute(query, values)
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                logger.info(f"📝 Successfully updated profile for user {user_id}: {list(filtered_updates.keys())}")
                return {'success': True, 'message': 'Profile updated successfully'}
            else:
                logger.warning(f"📝 Update query returned 0 rows for user {user_id}")
                return {'success': False, 'error': 'User not found or no changes made'}
            
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return {'success': False, 'error': f'Failed to update profile: {str(e)}'}
    
    def get_display_name(self, user_id: int) -> str:
        """Get user's display name with fallback"""
        try:
            if not self.database:
                return "User"
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"SELECT display_name, email FROM users WHERE id = {placeholder}", (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0] or result[1].split('@')[0]  # Fallback to email prefix
            
            return "User"
            
        except Exception as e:
            logger.error(f"Failed to get display name: {e}")
            return "User"
    
    def set_display_name(self, user_id: int, display_name: str) -> Dict[str, Any]:
        """Set user's display name"""
        try:
            if not display_name or not display_name.strip():
                return {'success': False, 'error': 'Display name cannot be empty'}
            
            display_name = display_name.strip()
            
            if len(display_name) > 50:
                return {'success': False, 'error': 'Display name must be 50 characters or less'}
            
            return self.update_profile(user_id, {'displayName': display_name})
            
        except Exception as e:
            logger.error(f"Failed to set display name: {e}")
            return {'success': False, 'error': f'Failed to set display name: {str(e)}'}
    
    def get_profile_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user profile statistics and activity"""
        try:
            # Get basic profile info
            profile_result = self.get_user_profile(user_id, include_access=False)
            if not profile_result['success']:
                return profile_result
            
            profile = profile_result['user']
            
            # Calculate account age
            if profile.get('createdDate'):
                try:
                    created = datetime.fromisoformat(profile['createdDate'])
                    account_age_days = (datetime.now() - created).days
                except:
                    account_age_days = 0
            else:
                account_age_days = 0
            
            # Get library stats if library module is available
            library_stats = self._get_library_stats(user_id)
            
            stats = {
                'accountAge': {
                    'days': account_age_days,
                    'joinDate': profile.get('createdDate')
                },
                'plan': {
                    'current': profile.get('plan', 'bronze'),
                    'trial': profile.get('trial', {})
                },
                'library': library_stats,
                'profile': {
                    'hasCustomImage': bool(profile.get('profileImage') and 
                                         not profile.get('profileImage', '').endswith('New IntroLogo.png')),
                    'hasCustomTheme': bool(profile.get('themePreferences')),
                    'displayName': profile.get('displayName'),
                    'emailVerified': profile.get('emailVerified', False)
                }
            }
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile stats: {e}")
            return {'success': False, 'error': f'Failed to get profile statistics: {str(e)}'}
    
    def preserve_session_profile_data(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Preserve important profile data from session during login/logout"""
        preserved = {}
        
        # Preserve trial data
        trial_keys = ['trial_active', 'trial_started_at', 'trial_expires_at', 
                     'trial_used_permanently', 'trial_warning_sent']
        
        for key in trial_keys:
            if key in session:
                preserved[key] = session[key]
        
        # Preserve custom profile image (exclude defaults)
        profile_image = session.get('profile_image')
        if (profile_image and 
            profile_image not in ['/static/logos/Sapphire.png', '/static/logos/New IntroLogo.png']):
            preserved['profile_image'] = profile_image
        
        # Preserve theme preferences
        user_themes = session.get('user_themes')
        if user_themes:
            preserved['user_themes'] = user_themes
        
        return preserved
    
    def restore_session_profile_data(self, session: Dict[str, Any], preserved: Dict[str, Any]) -> None:
        """Restore preserved profile data to session"""
        for key, value in preserved.items():
            session[key] = value
    
    def setup_new_user_profile(self, user_id: int, email: str, display_name: str = None) -> Dict[str, Any]:
        """Set up profile for a new user"""
        try:
            # Set default display name if not provided
            if not display_name:
                display_name = email.split('@')[0]
            
            # Update profile with initial data
            result = self.update_profile(user_id, {
                'displayName': display_name
            })
            
            if result['success']:
                logger.info(f"✅ Set up new user profile: {email} (ID: {user_id})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to setup new user profile: {e}")
            return {'success': False, 'error': f'Failed to setup profile: {str(e)}'}
    
    def _get_profile_image_url(self, profile_image: str, profile_image_data: str, user_id: int) -> str:
        """Get the appropriate profile image URL"""
        if profile_image and profile_image.startswith('/api/profile-image/'):
            return profile_image
        elif profile_image_data:
            return f"/api/profile-image/{user_id}"
        elif profile_image and not profile_image.endswith(('Sapphire.png', 'New IntroLogo.png')):
            return f"/api/profile-image/{user_id}"
        else:
            return '/static/logos/New IntroLogo.png'
    
    def _calculate_access_permissions(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate user access permissions based on plan and trial status"""
        plan = profile.get('plan', 'bronze')
        trial_active = profile.get('trial', {}).get('active', False)
        
        # Determine effective plan
        if trial_active and plan == 'bronze':
            effective_plan = 'gold'  # Trial gives Gold access
        else:
            effective_plan = plan
        
        # Set access flags
        access = {
            'plan': plan,
            'effective_plan': effective_plan,
            'trial_active': trial_active,
            'access_bronze': True,  # Everyone has Bronze access
            'access_silver': plan in ['silver', 'gold'],  # NO trial modification for Silver features
            'access_gold': plan == 'gold',  # NO trial modification for Gold features
            'companion_access': effective_plan,  # Trial DOES affect companion access
            'trial_credits': 0  # Will be set by credits system if needed
        }
        
        return access
    
    def _get_library_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's library statistics (placeholder for library module integration)"""
        try:
            # Try to import library manager if available
            from ..library.library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            return library_manager.get_library_stats(user_id)
        except ImportError:
            logger.info("Library module not available for profile stats")
            return {
                'total_items': 0,
                'by_type': {},
                'recent_activity': []
            }
        except Exception as e:
            logger.error(f"Failed to get library stats: {e}")
            return {
                'total_items': 0,
                'by_type': {},
                'recent_activity': [],
                'error': str(e)
            }
    
    def _ensure_profile_columns(self, cursor) -> None:
        """Ensure all required profile columns exist in the database"""
        try:
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                # PostgreSQL
                for column in self.required_columns:
                    if column in ['trial_used_permanently']:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} BOOLEAN DEFAULT FALSE")
                    elif column in ['trial_started_at']:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} TIMESTAMP")
                    else:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} TEXT")
            else:
                # SQLite - check if columns exist first
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                for column in self.required_columns:
                    if column not in existing_columns:
                        if column in ['trial_used_permanently']:
                            cursor.execute(f"ALTER TABLE users ADD COLUMN {column} BOOLEAN DEFAULT FALSE")
                        elif column in ['trial_started_at']:
                            cursor.execute(f"ALTER TABLE users ADD COLUMN {column} TIMESTAMP")
                        else:
                            cursor.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
                            
            logger.debug("Profile columns ensured in database")
            
        except Exception as e:
            logger.warning(f"Failed to ensure profile columns: {e}")
    
    def get_community_avatar(self, user_id: int) -> Dict[str, Any]:
        """Get user's community avatar/companion info"""
        try:
            # This would typically be stored in session or database
            # For now, return basic structure
            return {
                'success': True,
                'companion': {
                    'name': 'Soul',
                    'companion_id': 'default',
                    'avatar_url': '/static/companions/default.png'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get community avatar: {e}")
            return {'success': False, 'error': str(e)}
    
    def set_community_avatar(self, user_id: int, companion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set user's community avatar/companion"""
        try:
            # Validate companion data
            required_fields = ['companion_id', 'name', 'avatar_url']
            for field in required_fields:
                if field not in companion_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # TODO: Validate companion access based on user's plan
            # TODO: Store companion selection in database
            
            logger.info(f"👤 Set community avatar for user {user_id}: {companion_data['companion_id']}")
            
            return {
                'success': True,
                'message': 'Avatar updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to set community avatar: {e}")
            return {'success': False, 'error': str(e)}