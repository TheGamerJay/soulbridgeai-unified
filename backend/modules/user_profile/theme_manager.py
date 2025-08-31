"""
SoulBridge AI - Theme Manager
Handles user theme preferences and tier-specific themes
Extracted from backend/app.py with improvements
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ThemeManager:
    """Manager for user theme preferences and customization"""
    
    def __init__(self, database=None):
        self.database = database
        self.tier_default_themes = {
            'bronze': {
                'background': '#0f172a',
                'text': '#22d3ee', 
                'accent': '#22d3ee'
            },
            'silver': {
                'background': '#1a1a1a',
                'text': '#C0C0C0',
                'accent': '#C0C0C0'
            },
            'gold': {
                'background': '#1a1a1a',
                'text': '#FFD700',
                'accent': '#FFD700'
            },
            'general': {
                'background': '#0f172a',
                'text': '#22d3ee',
                'accent': '#06b6d4'
            }
        }
    
    def save_theme(self, user_id: int, tier: str, theme_data: Dict[str, str]) -> Dict[str, Any]:
        """Save user's theme preferences for specific tier"""
        try:
            # Validate theme data
            required_fields = ['background', 'text', 'accent']
            for field in required_fields:
                if field not in theme_data:
                    return {'success': False, 'error': f'Missing theme field: {field}'}
            
            # Validate color format (basic validation)
            for field, color in theme_data.items():
                if not self._validate_color(color):
                    return {'success': False, 'error': f'Invalid color format for {field}: {color}'}
            
            # Get existing themes to merge
            existing_themes = self._load_themes_from_database(user_id)
            
            # Update with new tier theme
            existing_themes[tier] = {
                'background': theme_data['background'],
                'text': theme_data['text'],
                'accent': theme_data['accent'],
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to database
            success = self._save_themes_to_database(user_id, existing_themes)
            
            if success:
                logger.info(f"🎨 Saved theme for user {user_id}, tier {tier}: {theme_data}")
                return {'success': True, 'message': 'Theme saved successfully'}
            else:
                return {'success': False, 'error': 'Failed to save theme to database'}
            
        except Exception as e:
            logger.error(f"Failed to save theme: {e}")
            return {'success': False, 'error': f'Failed to save theme: {str(e)}'}
    
    def get_theme(self, user_id: int, tier: str = 'general') -> Dict[str, Any]:
        """Get user's theme for specific tier"""
        try:
            # Load themes from database
            themes = self._load_themes_from_database(user_id)
            
            # Return tier-specific theme if exists
            if tier in themes:
                theme_data = themes[tier]
                # Remove metadata from response
                clean_theme = {
                    'background': theme_data.get('background'),
                    'text': theme_data.get('text'),
                    'accent': theme_data.get('accent')
                }
                return {'success': True, 'theme': clean_theme}
            
            # Return default theme for tier
            default_theme = self.tier_default_themes.get(tier, self.tier_default_themes['general'])
            return {'success': True, 'theme': default_theme}
            
        except Exception as e:
            logger.error(f"Failed to get theme: {e}")
            return {
                'success': True, 
                'theme': self.tier_default_themes.get(tier, self.tier_default_themes['general'])
            }
    
    def get_all_themes(self, user_id: int) -> Dict[str, Any]:
        """Get all user's themes across all tiers"""
        try:
            themes = self._load_themes_from_database(user_id)
            
            # Fill in defaults for missing tiers
            all_themes = {}
            for tier in ['bronze', 'silver', 'gold', 'general']:
                if tier in themes:
                    all_themes[tier] = {
                        'background': themes[tier].get('background'),
                        'text': themes[tier].get('text'),
                        'accent': themes[tier].get('accent')
                    }
                else:
                    all_themes[tier] = self.tier_default_themes[tier]
            
            return {'success': True, 'themes': all_themes}
            
        except Exception as e:
            logger.error(f"Failed to get all themes: {e}")
            return {'success': False, 'error': str(e)}
    
    def reset_theme(self, user_id: int, tier: str) -> Dict[str, Any]:
        """Reset theme to default for specific tier"""
        try:
            default_theme = self.tier_default_themes.get(tier, self.tier_default_themes['general'])
            return self.save_theme(user_id, tier, default_theme)
            
        except Exception as e:
            logger.error(f"Failed to reset theme: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_theme_into_session(self, user_id: int, session: Dict[str, Any]) -> None:
        """Load user's themes into session for quick access"""
        try:
            themes = self._load_themes_from_database(user_id)
            
            if themes:
                session['user_themes'] = themes
                # Also set general theme for compatibility
                general_theme = themes.get('general', self.tier_default_themes['general'])
                session['user_theme'] = general_theme
                logger.info(f"🎨 Loaded themes into session for user {user_id}")
            else:
                # Set default themes
                session['user_theme'] = self.tier_default_themes['general']
                session['user_themes'] = {}
                logger.info(f"🎨 Set default themes for user {user_id}")
                
        except Exception as e:
            logger.warning(f"Failed to load themes into session: {e}")
            # Set defaults on error
            session['user_theme'] = self.tier_default_themes['general']
            session['user_themes'] = {}
    
    def get_theme_presets(self) -> Dict[str, Any]:
        """Get available theme presets for each tier"""
        presets = {
            'bronze': [
                {
                    'name': 'Ocean Blue',
                    'theme': {'background': '#0f172a', 'text': '#22d3ee', 'accent': '#06b6d4'}
                },
                {
                    'name': 'Night Sky',
                    'theme': {'background': '#1a1a2e', 'text': '#22d3ee', 'accent': '#16213e'}
                },
                {
                    'name': 'Forest Green',
                    'theme': {'background': '#0f1419', 'text': '#22d3ee', 'accent': '#10b981'}
                }
            ],
            'silver': [
                {
                    'name': 'Silver Classic',
                    'theme': {'background': '#1a1a1a', 'text': '#C0C0C0', 'accent': '#C0C0C0'}
                },
                {
                    'name': 'Silver Moon',
                    'theme': {'background': '#2a2a2a', 'text': '#E5E5E5', 'accent': '#B8B8B8'}
                },
                {
                    'name': 'Platinum',
                    'theme': {'background': '#1c1c1c', 'text': '#E5E7EB', 'accent': '#D1D5DB'}
                }
            ],
            'gold': [
                {
                    'name': 'Golden Hour',
                    'theme': {'background': '#1a1a1a', 'text': '#FFD700', 'accent': '#FFA500'}
                },
                {
                    'name': 'Royal Gold',
                    'theme': {'background': '#2a1810', 'text': '#FFD700', 'accent': '#B8860B'}
                },
                {
                    'name': 'Amber Glow',
                    'theme': {'background': '#1c1810', 'text': '#FFBF00', 'accent': '#FF8C00'}
                }
            ]
        }
        
        return {'success': True, 'presets': presets}
    
    def apply_preset(self, user_id: int, tier: str, preset_name: str) -> Dict[str, Any]:
        """Apply a theme preset to user's tier"""
        try:
            presets_result = self.get_theme_presets()
            if not presets_result['success']:
                return presets_result
            
            presets = presets_result['presets']
            
            if tier not in presets:
                return {'success': False, 'error': f'No presets available for tier: {tier}'}
            
            # Find the preset
            preset = None
            for p in presets[tier]:
                if p['name'] == preset_name:
                    preset = p['theme']
                    break
            
            if not preset:
                return {'success': False, 'error': f'Preset not found: {preset_name}'}
            
            # Apply the preset
            return self.save_theme(user_id, tier, preset)
            
        except Exception as e:
            logger.error(f"Failed to apply preset: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_themes_from_database(self, user_id: int) -> Dict[str, Any]:
        """Load user's themes from database"""
        try:
            if not self.database:
                return {}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"SELECT theme_preferences FROM users WHERE id = {placeholder}", (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                themes_data = json.loads(result[0])
                if isinstance(themes_data, dict):
                    return themes_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to load themes from database: {e}")
            return {}
    
    def _save_themes_to_database(self, user_id: int, themes: Dict[str, Any]) -> bool:
        """Save user's themes to database"""
        try:
            if not self.database:
                return False
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Ensure theme_preferences column exists
            try:
                if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS theme_preferences TEXT")
                else:
                    cursor.execute("PRAGMA table_info(users)")
                    columns = [col[1] for col in cursor.fetchall()]
                    if 'theme_preferences' not in columns:
                        cursor.execute("ALTER TABLE users ADD COLUMN theme_preferences TEXT")
            except Exception as migration_error:
                logger.warning(f"Theme column migration warning: {migration_error}")
            
            # Save themes
            themes_json = json.dumps(themes)
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            cursor.execute(f"UPDATE users SET theme_preferences = {placeholder} WHERE id = {placeholder}", 
                         (themes_json, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save themes to database: {e}")
            return False
    
    def _validate_color(self, color: str) -> bool:
        """Validate color format (hex colors)"""
        try:
            if not color or not isinstance(color, str):
                return False
            
            # Basic hex color validation
            if color.startswith('#') and len(color) in [4, 7]:
                hex_part = color[1:]
                return all(c in '0123456789ABCDEFabcdef' for c in hex_part)
            
            # Could add support for rgb(), rgba(), hsl(), etc. in the future
            return False
            
        except Exception:
            return False
    
    def export_themes(self, user_id: int) -> Dict[str, Any]:
        """Export user's themes for backup/transfer"""
        try:
            themes = self._load_themes_from_database(user_id)
            
            export_data = {
                'user_id': user_id,
                'export_date': datetime.now().isoformat(),
                'themes': themes,
                'version': '1.0'
            }
            
            return {'success': True, 'data': export_data}
            
        except Exception as e:
            logger.error(f"Failed to export themes: {e}")
            return {'success': False, 'error': str(e)}
    
    def import_themes(self, user_id: int, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import themes from backup data"""
        try:
            if 'themes' not in theme_data:
                return {'success': False, 'error': 'Invalid theme data format'}
            
            themes = theme_data['themes']
            
            # Validate themes
            for tier, theme in themes.items():
                if not isinstance(theme, dict):
                    continue
                
                # Validate required fields
                if not all(field in theme for field in ['background', 'text', 'accent']):
                    return {'success': False, 'error': f'Invalid theme data for tier: {tier}'}
                
                # Validate colors
                for field in ['background', 'text', 'accent']:
                    if not self._validate_color(theme[field]):
                        return {'success': False, 'error': f'Invalid color in {tier}.{field}'}
            
            # Save imported themes
            success = self._save_themes_to_database(user_id, themes)
            
            if success:
                logger.info(f"🎨 Imported themes for user {user_id}")
                return {'success': True, 'message': 'Themes imported successfully'}
            else:
                return {'success': False, 'error': 'Failed to save imported themes'}
            
        except Exception as e:
            logger.error(f"Failed to import themes: {e}")
            return {'success': False, 'error': str(e)}