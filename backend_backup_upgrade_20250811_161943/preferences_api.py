"""
User Preferences API endpoints
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging
import json

logger = logging.getLogger(__name__)

def create_preferences_api(preferences_manager, rate_limiter, security_monitor):
    """Create preferences API blueprint"""
    
    preferences_api = Blueprint('preferences', __name__, url_prefix='/api/preferences')
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @preferences_api.route('/', methods=['GET'])
    @require_auth
    def get_preferences():
        """Get all user preferences"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            preferences = preferences_manager.get_user_preferences(user_id)
            
            return jsonify({
                'success': True,
                'preferences': preferences
            })
            
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/<category>', methods=['GET'])
    @require_auth
    def get_category_preferences(category):
        """Get preferences for specific category"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            if category not in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                return jsonify({'error': 'Invalid preference category'}), 400
            
            all_preferences = preferences_manager.get_user_preferences(user_id)
            category_preferences = all_preferences.get(category, {})
            
            return jsonify({
                'success': True,
                'category': category,
                'preferences': category_preferences
            })
            
        except Exception as e:
            logger.error(f"Error getting category preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/<category>', methods=['PUT'])
    @require_auth
    def update_category_preferences(category):
        """Update preferences for specific category"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            if category not in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                return jsonify({'error': 'Invalid preference category'}), 400
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"preferences_{user_id}", max_requests=20, window=300):
                return jsonify({'error': 'Too many preference updates. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'preference_update', {
                    'category': category,
                    'updated_fields': list(data.keys())
                })
            
            success = preferences_manager.update_user_preferences(user_id, category, data)
            
            if not success:
                return jsonify({'error': 'Failed to update preferences'}), 500
            
            # Get updated preferences
            updated_preferences = preferences_manager.get_user_preferences(user_id)
            category_preferences = updated_preferences.get(category, {})
            
            return jsonify({
                'success': True,
                'message': f'{category.title()} preferences updated successfully',
                'preferences': category_preferences
            })
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/theme', methods=['GET'])
    @require_auth
    def get_theme_config():
        """Get complete theme configuration"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            theme_config = preferences_manager.get_theme_config(user_id)
            
            return jsonify({
                'success': True,
                'theme': theme_config
            })
            
        except Exception as e:
            logger.error(f"Error getting theme config: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/themes', methods=['GET'])
    @require_auth
    def get_available_themes():
        """Get all available themes"""
        try:
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            # Get predefined themes
            predefined_themes = preferences_manager.themes
            
            # Get user's custom themes
            user_id = session['user_id']
            custom_themes = preferences_manager.get_user_custom_themes(user_id)
            
            return jsonify({
                'success': True,
                'predefined_themes': predefined_themes,
                'custom_themes': custom_themes
            })
            
        except Exception as e:
            logger.error(f"Error getting available themes: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/themes/custom', methods=['POST'])
    @require_auth
    def create_custom_theme():
        """Create a new custom theme"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'name' not in data or 'theme_data' not in data:
                return jsonify({'error': 'Theme name and data required'}), 400
            
            theme_name = data['name'].strip()
            theme_data = data['theme_data']
            
            if not theme_name:
                return jsonify({'error': 'Theme name cannot be empty'}), 400
            
            # Validate theme data structure
            required_keys = ['primary', 'secondary', 'background', 'surface', 'text', 'accent']
            if not all(key in theme_data for key in required_keys):
                return jsonify({'error': 'Invalid theme data - missing required properties'}), 400
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"custom_theme_{user_id}", max_requests=5, window=3600):
                return jsonify({'error': 'Too many custom themes created. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'custom_theme_created', {
                    'theme_name': theme_name
                })
            
            success = preferences_manager.create_custom_theme(user_id, theme_name, theme_data)
            
            if not success:
                return jsonify({'error': 'Failed to create custom theme'}), 500
            
            return jsonify({
                'success': True,
                'message': f'Custom theme "{theme_name}" created successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating custom theme: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/export', methods=['GET'])
    @require_auth
    def export_preferences():
        """Export all user preferences"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'preferences_exported', {})
            
            export_data = preferences_manager.export_user_preferences(user_id)
            
            if not export_data:
                return jsonify({'error': 'Failed to export preferences'}), 500
            
            return jsonify({
                'success': True,
                'export_data': export_data
            })
            
        except Exception as e:
            logger.error(f"Error exporting preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/import', methods=['POST'])
    @require_auth
    def import_preferences():
        """Import user preferences from backup"""
        try:
            user_id = session['user_id']
            data = request.get_json()
            
            if not data or 'export_data' not in data:
                return jsonify({'error': 'Export data required'}), 400
            
            export_data = data['export_data']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"import_prefs_{user_id}", max_requests=3, window=3600):
                return jsonify({'error': 'Too many imports. Please wait.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'preferences_imported', {})
            
            success = preferences_manager.import_user_preferences(user_id, export_data)
            
            if not success:
                return jsonify({'error': 'Failed to import preferences'}), 500
            
            return jsonify({
                'success': True,
                'message': 'Preferences imported successfully'
            })
            
        except Exception as e:
            logger.error(f"Error importing preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/analytics', methods=['GET'])
    @require_auth
    def get_preference_analytics():
        """Get analytics about user preference usage"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            analytics = preferences_manager.get_preference_analytics(user_id)
            
            return jsonify({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error getting preference analytics: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @preferences_api.route('/reset/<category>', methods=['POST'])
    @require_auth
    def reset_category_preferences(category):
        """Reset preferences for specific category to defaults"""
        try:
            user_id = session['user_id']
            
            if not preferences_manager:
                return jsonify({'error': 'Preferences system unavailable'}), 503
            
            if category not in ['ui', 'notifications', 'privacy', 'ai', 'accessibility']:
                return jsonify({'error': 'Invalid preference category'}), 400
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'preferences_reset', {
                    'category': category
                })
            
            # Get default preferences for category
            defaults = preferences_manager._get_category_defaults(category)
            
            success = preferences_manager.update_user_preferences(user_id, category, defaults)
            
            if not success:
                return jsonify({'error': 'Failed to reset preferences'}), 500
            
            return jsonify({
                'success': True,
                'message': f'{category.title()} preferences reset to defaults',
                'preferences': defaults
            })
            
        except Exception as e:
            logger.error(f"Error resetting preferences: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return preferences_api

def init_preferences_api(preferences_manager, rate_limiter, security_monitor):
    """Initialize and return preferences API blueprint"""
    try:
        api = create_preferences_api(preferences_manager, rate_limiter, security_monitor)
        logger.info("Preferences API initialized successfully")
        return api
    except Exception as e:
        logger.error(f"Error initializing preferences API: {e}")
        return None