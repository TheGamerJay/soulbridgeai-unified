"""
Advanced User Preferences and Customization System
Personalized settings, themes, and behavioral preferences
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"

class NotificationFrequency(Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"

class PrivacyLevel(Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"

@dataclass
class UIPreferences:
    theme: str = "light"
    accent_color: str = "#667eea"
    font_size: str = "medium"
    animation_enabled: bool = True
    sidebar_collapsed: bool = False
    dashboard_layout: str = "grid"
    language: str = "en"
    timezone: str = "UTC"
    
@dataclass
class NotificationPreferences:
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    sound_enabled: bool = True
    vibration_enabled: bool = True
    frequency: str = "immediate"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    weekend_notifications: bool = True
    
@dataclass
class PrivacyPreferences:
    profile_visibility: str = "friends"
    mood_sharing: str = "friends"
    activity_tracking: bool = True
    data_analytics: bool = True
    marketing_emails: bool = False
    third_party_sharing: bool = False
    location_tracking: bool = False
    
@dataclass
class AIPreferences:
    personality_type: str = "balanced"
    response_length: str = "medium"
    conversation_style: str = "supportive"
    proactive_suggestions: bool = True
    learning_enabled: bool = True
    memory_retention: int = 30  # days
    emoji_usage: str = "moderate"
    
@dataclass
class AccessibilityPreferences:
    high_contrast: bool = False
    large_text: bool = False
    screen_reader_mode: bool = False
    keyboard_navigation: bool = False
    reduced_motion: bool = False
    focus_indicators: bool = True
    alt_text_enabled: bool = True

class UserPreferencesManager:
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Default preference sets
        self.default_preferences = {
            'ui': UIPreferences(),
            'notifications': NotificationPreferences(),
            'privacy': PrivacyPreferences(),
            'ai': AIPreferences(),
            'accessibility': AccessibilityPreferences()
        }
        
        # Predefined themes
        self.themes = {
            'light': {
                'name': 'Light Theme',
                'primary': '#667eea',
                'secondary': '#764ba2',
                'background': '#ffffff',
                'surface': '#f8f9fa',
                'text': '#333333',
                'accent': '#667eea'
            },
            'dark': {
                'name': 'Dark Theme',
                'primary': '#667eea',
                'secondary': '#764ba2',
                'background': '#1a1a1a',
                'surface': '#2d2d2d',
                'text': '#ffffff',
                'accent': '#667eea'
            },
            'ocean': {
                'name': 'Ocean Theme',
                'primary': '#0077be',
                'secondary': '#00a8cc',
                'background': '#f0f8ff',
                'surface': '#e6f3ff',
                'text': '#003d5c',
                'accent': '#0077be'
            },
            'forest': {
                'name': 'Forest Theme',
                'primary': '#2d5a27',
                'secondary': '#4a7c59',
                'background': '#f9fdf9',
                'surface': '#f0f7f0',
                'text': '#1a3017',
                'accent': '#2d5a27'
            },
            'sunset': {
                'name': 'Sunset Theme',
                'primary': '#ff6b35',
                'secondary': '#f7931e',
                'background': '#fffaf7',
                'surface': '#fff4ed',
                'text': '#5a2d1a',
                'accent': '#ff6b35'
            }
        }
        
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences"""
        try:
            if not self.db:
                return self._get_default_preferences()
            
            query = """
            SELECT preference_category, preference_data, updated_at 
            FROM user_preferences 
            WHERE user_id = ?
            """
            results = self.db.fetch_all(query, (user_id,))
            
            preferences = {}
            for category, data, updated_at in results:
                try:
                    preferences[category] = json.loads(data)
                    preferences[category]['_updated_at'] = updated_at
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in preferences for user {user_id}, category {category}")
                    preferences[category] = self._get_category_defaults(category)
            
            # Fill missing categories with defaults
            for category in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                if category not in preferences:
                    preferences[category] = self._get_category_defaults(category)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return self._get_default_preferences()
    
    def update_user_preferences(self, user_id: str, category: str, preferences: Dict[str, Any]) -> bool:
        """Update specific category of user preferences"""
        try:
            if not self.db:
                return False
            
            # Validate category
            if category not in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                raise ValueError(f"Invalid preference category: {category}")
            
            # Merge with existing preferences
            existing_prefs = self.get_user_preferences(user_id)
            existing_category = existing_prefs.get(category, {})
            
            # Remove metadata
            if '_updated_at' in existing_category:
                del existing_category['_updated_at']
            
            updated_prefs = {**existing_category, **preferences}
            
            # Validate preferences
            validated_prefs = self._validate_preferences(category, updated_prefs)
            
            # Store in database
            query = """
            INSERT OR REPLACE INTO user_preferences 
            (user_id, preference_category, preference_data, updated_at)
            VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                user_id,
                category,
                json.dumps(validated_prefs),
                datetime.now().isoformat()
            ))
            
            logger.info(f"Updated {category} preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def get_theme_config(self, user_id: str) -> Dict[str, Any]:
        """Get complete theme configuration for user"""
        try:
            user_prefs = self.get_user_preferences(user_id)
            ui_prefs = user_prefs.get('ui', {})
            
            theme_name = ui_prefs.get('theme', 'light')
            
            if theme_name in self.themes:
                theme_config = self.themes[theme_name].copy()
            else:
                theme_config = self.themes['light'].copy()
            
            # Apply user customizations
            if ui_prefs.get('accent_color'):
                theme_config['accent'] = ui_prefs['accent_color']
                theme_config['primary'] = ui_prefs['accent_color']
            
            # Add UI preferences
            theme_config.update({
                'font_size': ui_prefs.get('font_size', 'medium'),
                'animation_enabled': ui_prefs.get('animation_enabled', True),
                'sidebar_collapsed': ui_prefs.get('sidebar_collapsed', False),
                'dashboard_layout': ui_prefs.get('dashboard_layout', 'grid'),
                'language': ui_prefs.get('language', 'en'),
                'timezone': ui_prefs.get('timezone', 'UTC')
            })
            
            return theme_config
            
        except Exception as e:
            logger.error(f"Error getting theme config: {e}")
            return self.themes['light']
    
    def create_custom_theme(self, user_id: str, theme_name: str, theme_data: Dict[str, str]) -> bool:
        """Create a custom theme for user"""
        try:
            if not self.db:
                return False
            
            # Validate theme data
            required_keys = ['primary', 'secondary', 'background', 'surface', 'text', 'accent']
            if not all(key in theme_data for key in required_keys):
                raise ValueError("Missing required theme properties")
            
            query = """
            INSERT OR REPLACE INTO user_custom_themes 
            (user_id, theme_name, theme_data, created_at)
            VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                user_id,
                theme_name,
                json.dumps(theme_data),
                datetime.now().isoformat()
            ))
            
            logger.info(f"Created custom theme '{theme_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom theme: {e}")
            return False
    
    def get_user_custom_themes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all custom themes for user"""
        try:
            if not self.db:
                return []
            
            query = """
            SELECT theme_name, theme_data, created_at 
            FROM user_custom_themes 
            WHERE user_id = ?
            ORDER BY created_at DESC
            """
            results = self.db.fetch_all(query, (user_id,))
            
            themes = []
            for name, data, created_at in results:
                try:
                    theme_data = json.loads(data)
                    theme_data['name'] = name
                    theme_data['created_at'] = created_at
                    themes.append(theme_data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid theme JSON for user {user_id}, theme {name}")
            
            return themes
            
        except Exception as e:
            logger.error(f"Error getting custom themes: {e}")
            return []
    
    def export_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Export all user preferences for backup/transfer"""
        try:
            preferences = self.get_user_preferences(user_id)
            custom_themes = self.get_user_custom_themes(user_id)
            
            export_data = {
                'user_id': user_id,
                'exported_at': datetime.now().isoformat(),
                'preferences': preferences,
                'custom_themes': custom_themes,
                'version': '1.0'
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting preferences: {e}")
            return {}
    
    def import_user_preferences(self, user_id: str, import_data: Dict[str, Any]) -> bool:
        """Import user preferences from backup"""
        try:
            if 'preferences' not in import_data:
                raise ValueError("Invalid import data - missing preferences")
            
            preferences = import_data['preferences']
            
            # Import each category
            for category, prefs in preferences.items():
                if category in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                    # Remove metadata
                    clean_prefs = {k: v for k, v in prefs.items() if not k.startswith('_')}
                    self.update_user_preferences(user_id, category, clean_prefs)
            
            # Import custom themes
            if 'custom_themes' in import_data:
                for theme in import_data['custom_themes']:
                    if 'name' in theme:
                        theme_name = theme['name']
                        theme_data = {k: v for k, v in theme.items() 
                                    if k not in ['name', 'created_at']}
                        self.create_custom_theme(user_id, theme_name, theme_data)
            
            logger.info(f"Imported preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing preferences: {e}")
            return False
    
    def get_preference_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics about user preference usage"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            analytics = {
                'customization_level': self._calculate_customization_level(preferences),
                'last_updated': self._get_last_update_time(preferences),
                'theme_usage': preferences.get('ui', {}).get('theme', 'light'),
                'notification_settings': self._analyze_notification_preferences(preferences),
                'accessibility_features': self._count_accessibility_features(preferences),
                'privacy_score': self._calculate_privacy_score(preferences)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting preference analytics: {e}")
            return {}
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default preferences for all categories"""
        return {
            'ui': asdict(self.default_preferences['ui']),
            'notifications': asdict(self.default_preferences['notifications']),
            'privacy': asdict(self.default_preferences['privacy']),
            'ai': asdict(self.default_preferences['ai']),
            'accessibility': asdict(self.default_preferences['accessibility'])
        }
    
    def _get_category_defaults(self, category: str) -> Dict[str, Any]:
        """Get default preferences for specific category"""
        if category in self.default_preferences:
            return asdict(self.default_preferences[category])
        return {}
    
    def _validate_preferences(self, category: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize preference values"""
        validated = preferences.copy()
        
        if category == 'ui':
            # Validate theme
            if 'theme' in validated:
                valid_themes = list(self.themes.keys()) + ['custom']
                if validated['theme'] not in valid_themes:
                    validated['theme'] = 'light'
            
            # Validate colors (basic hex validation)
            if 'accent_color' in validated:
                if not validated['accent_color'].startswith('#') or len(validated['accent_color']) != 7:
                    validated['accent_color'] = '#667eea'
            
            # Validate font size
            if 'font_size' in validated:
                if validated['font_size'] not in ['small', 'medium', 'large']:
                    validated['font_size'] = 'medium'
                    
        elif category == 'notifications':
            # Validate frequency
            if 'frequency' in validated:
                valid_frequencies = [e.value for e in NotificationFrequency]
                if validated['frequency'] not in valid_frequencies:
                    validated['frequency'] = 'immediate'
                    
        elif category == 'privacy':
            # Validate visibility levels
            for key in ['profile_visibility', 'mood_sharing']:
                if key in validated:
                    valid_levels = [e.value for e in PrivacyLevel]
                    if validated[key] not in valid_levels:
                        validated[key] = 'friends'
        
        return validated
    
    def _calculate_customization_level(self, preferences: Dict[str, Any]) -> str:
        """Calculate how much the user has customized their preferences"""
        defaults = self._get_default_preferences()
        customized_count = 0
        total_count = 0
        
        for category, prefs in preferences.items():
            if category in defaults:
                default_prefs = defaults[category]
                for key, value in prefs.items():
                    if not key.startswith('_'):
                        total_count += 1
                        if key in default_prefs and default_prefs[key] != value:
                            customized_count += 1
        
        if total_count == 0:
            return 'none'
        
        percentage = (customized_count / total_count) * 100
        if percentage < 10:
            return 'minimal'
        elif percentage < 30:
            return 'light'
        elif percentage < 60:
            return 'moderate'
        else:
            return 'extensive'
    
    def _get_last_update_time(self, preferences: Dict[str, Any]) -> Optional[str]:
        """Get the most recent update time across all preferences"""
        latest = None
        for category, prefs in preferences.items():
            if '_updated_at' in prefs:
                if latest is None or prefs['_updated_at'] > latest:
                    latest = prefs['_updated_at']
        return latest
    
    def _analyze_notification_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze notification preferences"""
        notif_prefs = preferences.get('notifications', {})
        enabled_channels = sum([
            notif_prefs.get('email_enabled', True),
            notif_prefs.get('push_enabled', True),
            notif_prefs.get('sms_enabled', False)
        ])
        
        return {
            'enabled_channels': enabled_channels,
            'frequency': notif_prefs.get('frequency', 'immediate'),
            'quiet_hours_enabled': bool(notif_prefs.get('quiet_hours_start'))
        }
    
    def _count_accessibility_features(self, preferences: Dict[str, Any]) -> int:
        """Count enabled accessibility features"""
        accessibility_prefs = preferences.get('accessibility', {})
        return sum([
            accessibility_prefs.get('high_contrast', False),
            accessibility_prefs.get('large_text', False),
            accessibility_prefs.get('screen_reader_mode', False),
            accessibility_prefs.get('keyboard_navigation', False),
            accessibility_prefs.get('reduced_motion', False)
        ])
    
    def _calculate_privacy_score(self, preferences: Dict[str, Any]) -> int:
        """Calculate privacy score (0-100)"""
        privacy_prefs = preferences.get('privacy', {})
        score = 0
        
        # More private settings increase score
        if privacy_prefs.get('profile_visibility') == 'private':
            score += 25
        elif privacy_prefs.get('profile_visibility') == 'friends':
            score += 15
        
        if privacy_prefs.get('mood_sharing') == 'private':
            score += 25
        elif privacy_prefs.get('mood_sharing') == 'friends':
            score += 15
        
        if not privacy_prefs.get('activity_tracking', True):
            score += 15
        if not privacy_prefs.get('data_analytics', True):
            score += 15
        if not privacy_prefs.get('marketing_emails', False):
            score += 10
        if not privacy_prefs.get('third_party_sharing', False):
            score += 20
        if not privacy_prefs.get('location_tracking', False):
            score += 15
        
        return min(score, 100)

def init_preferences_database(db_connection):
    """Initialize user preferences database tables"""
    try:
        # User preferences table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT NOT NULL,
                preference_category TEXT NOT NULL,
                preference_data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, preference_category),
                INDEX(user_id),
                INDEX(updated_at)
            )
        ''')
        
        # Custom themes table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS user_custom_themes (
                user_id TEXT NOT NULL,
                theme_name TEXT NOT NULL,
                theme_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, theme_name),
                INDEX(user_id),
                INDEX(created_at)
            )
        ''')
        
        db_connection.commit()
        logger.info("User preferences database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing preferences database: {e}")

# Global instance
preferences_manager_instance = None

def init_preferences_manager(db_manager):
    """Initialize user preferences manager"""
    global preferences_manager_instance
    try:
        preferences_manager_instance = UserPreferencesManager(db_manager)
        logger.info("User preferences manager initialized successfully")
        return preferences_manager_instance
    except Exception as e:
        logger.error(f"Error initializing preferences manager: {e}")
        return None

def get_preferences_manager():
    """Get preferences manager instance"""
    return preferences_manager_instance