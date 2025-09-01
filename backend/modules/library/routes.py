"""
SoulBridge AI - Library Routes
All library-related endpoints and page handlers
Extracted from monolith app.py with improvements
"""
import logging
from flask import Blueprint, request, jsonify, session, render_template, redirect
from .library_manager import LibraryManager
from .content_service import ContentService
from .music_service import MusicService

logger = logging.getLogger(__name__)

# Create library blueprint
library_bp = Blueprint('library', __name__, url_prefix='/library')

def _get_current_user():
    """Get current user info from session"""
    if not session.get('logged_in'):
        return None
    
    return {
        'id': session.get('user_id'),
        'email': session.get('user_email'),
        'plan': session.get('user_plan', 'bronze'),
        'trial_active': session.get('trial_active', False)
    }

def _get_services():
    """Get library services with database connection"""
    from ..shared.database import get_database
    
    database = get_database()
    return {
        'library_manager': LibraryManager(database),
        'content_service': ContentService(database),
        'music_service': MusicService(database)
    }

# Page Routes
@library_bp.route('/')
@library_bp.route('/<content_type>')
def library_page(content_type="all"):
    """Unified library page for all content types"""
    try:
        user = _get_current_user()
        if not user:
            return redirect("/login?return_to=library")
        
        # Get library statistics
        services = _get_services()
        stats = services['library_manager'].get_library_stats(user['id'])
        
        return render_template("library.html", 
                             content_type=content_type,
                             user_plan=user['plan'],
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Library page error: {e}")
        return render_template('error.html', 
                             error="Failed to load library"), 500

@library_bp.route('/music')
def music_library_page():
    """Music library page"""
    return library_page('music')

# API Routes - Content Management
@library_bp.route('/api/content', methods=['GET'])
def get_library_content():
    """Get user's library content with filtering"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get query parameters
        content_type = request.args.get('type', 'all')
        limit = request.args.get('limit', 50, type=int)
        search_query = request.args.get('search', '').strip()
        
        services = _get_services()
        
        if search_query:
            # Search across content
            search_type = None if content_type == 'all' else content_type
            content = services['content_service'].search_content(
                user['id'], search_query, search_type
            )
        else:
            # Get content by type with plan limits
            if content_type == 'all':
                content = services['library_manager'].get_user_library(user['id'], None, limit)
            else:
                content_result = services['content_service'].get_content_with_plan_limits(
                    user['id'], content_type, user['plan']
                )
                content = content_result['items']
        
        return jsonify({
            'success': True,
            'content': content,
            'content_type': content_type,
            'total': len(content)
        })
        
    except Exception as e:
        logger.error(f"Get library content error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get content'}), 500

@library_bp.route('/api/content/<int:content_id>', methods=['GET'])
def get_content_item(content_id):
    """Get specific content item"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        content = services['library_manager'].get_content_by_id(user['id'], content_id)
        
        if not content:
            return jsonify({'success': False, 'error': 'Content not found'}), 404
        
        return jsonify({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        logger.error(f"Get content item error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get content'}), 500

@library_bp.route('/api/content/<int:content_id>', methods=['PUT'])
def update_content_item(content_id):
    """Update content item"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        services = _get_services()
        success = services['library_manager'].update_content(user['id'], content_id, data)
        
        if success:
            return jsonify({'success': True, 'message': 'Content updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update content'}), 500
            
    except Exception as e:
        logger.error(f"Update content error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update content'}), 500

@library_bp.route('/api/content/<int:content_id>', methods=['DELETE'])
def delete_content_item(content_id):
    """Delete content item"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        success = services['library_manager'].delete_content(user['id'], content_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Content deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete content'}), 500
            
    except Exception as e:
        logger.error(f"Delete content error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete content'}), 500

@library_bp.route('/api/content/bulk-delete', methods=['POST'])
def bulk_delete_content():
    """Delete multiple content items"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        content_ids = data.get('content_ids', [])
        
        if not content_ids:
            return jsonify({'success': False, 'error': 'No content IDs provided'}), 400
        
        services = _get_services()
        result = services['content_service'].bulk_delete_content(user['id'], content_ids)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Bulk delete error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete content'}), 500

# API Routes - Specific Content Types
@library_bp.route('/api/save-fortune', methods=['POST'])
def save_fortune_reading():
    """Save fortune reading to library"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['question', 'card', 'interpretation', 'spread']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        
        services = _get_services()
        content_id = services['content_service'].save_fortune_reading(
            user['id'],
            data['question'],
            data['card'],
            data['interpretation'],
            data.get('spread', 'single')
        )
        
        if content_id:
            return jsonify({
                'success': True,
                'message': 'Fortune reading saved to library',
                'content_id': content_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save fortune reading'}), 500
            
    except Exception as e:
        logger.error(f"Save fortune error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save fortune reading'}), 500

@library_bp.route('/api/save-chat', methods=['POST'])
def save_chat_conversation():
    """Save chat conversation to library"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        title = data.get('title', 'Untitled Conversation')
        messages = data.get('messages', [])
        companion_id = data.get('companion_id')
        
        if not messages:
            return jsonify({'success': False, 'error': 'No messages to save'}), 400
        
        services = _get_services()
        content_id = services['content_service'].save_chat_conversation(
            user['id'], title, messages, companion_id
        )
        
        if content_id:
            return jsonify({
                'success': True,
                'message': 'Conversation saved to library',
                'content_id': content_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save conversation'}), 500
            
    except Exception as e:
        logger.error(f"Save chat error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save conversation'}), 500

# API Routes - Music Library
@library_bp.route('/api/music', methods=['GET'])
def get_music_library():
    """Get user's music library"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Get query parameters
        source_type = request.args.get('source')  # 'music', 'mini_studio'
        track_type = request.args.get('type')     # 'generated', 'vocals', etc.
        favorites_only = request.args.get('favorites') == 'true'
        
        services = _get_services()
        tracks = services['music_service'].get_user_tracks(
            user['id'], source_type, track_type, favorites_only
        )
        
        return jsonify({
            'success': True,
            'tracks': tracks,
            'total': len(tracks)
        })
        
    except Exception as e:
        logger.error(f"Get music library error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get music library'}), 500

@library_bp.route('/api/music/<int:track_id>', methods=['GET'])
def get_music_track(track_id):
    """Get specific music track"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        track = services['music_service'].get_track(track_id, user['id'])
        
        if not track:
            return jsonify({'success': False, 'error': 'Track not found'}), 404
        
        return jsonify({
            'success': True,
            'track': track
        })
        
    except Exception as e:
        logger.error(f"Get music track error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get track'}), 500

@library_bp.route('/api/music/<int:track_id>', methods=['PUT'])
def update_music_track(track_id):
    """Update music track details"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        services = _get_services()
        success = services['music_service'].update_track(track_id, user['id'], data)
        
        if success:
            return jsonify({'success': True, 'message': 'Track updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update track'}), 500
            
    except Exception as e:
        logger.error(f"Update music track error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update track'}), 500

@library_bp.route('/api/music/<int:track_id>', methods=['DELETE'])
def delete_music_track(track_id):
    """Delete music track"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        delete_file = request.args.get('delete_file', 'true').lower() == 'true'
        
        services = _get_services()
        success = services['music_service'].delete_track(track_id, user['id'], delete_file)
        
        if success:
            return jsonify({'success': True, 'message': 'Track deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete track'}), 500
            
    except Exception as e:
        logger.error(f"Delete music track error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete track'}), 500

@library_bp.route('/api/music/<int:track_id>/favorite', methods=['POST'])
def toggle_music_favorite(track_id):
    """Toggle favorite status for music track"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        result = services['music_service'].toggle_favorite(track_id, user['id'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Toggle favorite error: {e}")
        return jsonify({'success': False, 'error': 'Failed to toggle favorite'}), 500

@library_bp.route('/api/music/<int:track_id>/play', methods=['POST'])
def record_music_play(track_id):
    """Record a play event for analytics"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        success = services['music_service'].record_play(track_id, user['id'])
        
        if success:
            return jsonify({'success': True, 'message': 'Play recorded'})
        else:
            return jsonify({'success': False, 'error': 'Failed to record play'}), 500
            
    except Exception as e:
        logger.error(f"Record play error: {e}")
        return jsonify({'success': False, 'error': 'Failed to record play'}), 500

# API Routes - Statistics and Export
@library_bp.route('/api/stats', methods=['GET'])
def get_library_stats():
    """Get detailed library statistics"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        services = _get_services()
        
        # Get general library stats
        general_stats = services['library_manager'].get_library_stats(user['id'])
        
        # Get music-specific stats
        music_stats = services['music_service'].get_library_stats(user['id'])
        
        return jsonify({
            'success': True,
            'stats': {
                'general': general_stats,
                'music': music_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

@library_bp.route('/api/export', methods=['GET'])
def export_library():
    """Export user's library for backup/download"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        content_type = request.args.get('type')  # Optional filter
        
        services = _get_services()
        result = services['content_service'].export_user_library(user['id'], content_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Export library error: {e}")
        return jsonify({'success': False, 'error': 'Failed to export library'}), 500

# API Routes - Music Track Addition (for integrations)
@library_bp.route('/api/music/add', methods=['POST'])
def add_music_track():
    """Add a new music track to library"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        title = data.get('title', 'Untitled Track')
        file_path = data.get('file_path')
        source_type = data.get('source_type', 'music')
        track_type = data.get('track_type', 'generated')
        tags = data.get('tags', '')
        metadata = data.get('metadata', {})
        
        services = _get_services()
        
        # Validate file if provided
        if file_path:
            validation = services['music_service'].validate_audio_file(file_path)
            if not validation['valid']:
                return jsonify({'success': False, 'error': validation['error']}), 400
        
        track_id = services['music_service'].add_track(
            user['id'], title, file_path, source_type, track_type, tags, metadata
        )
        
        if track_id:
            return jsonify({
                'success': True,
                'message': 'Track added to library',
                'track_id': track_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to add track'}), 500
            
    except Exception as e:
        logger.error(f"Add track error: {e}")
        return jsonify({'success': False, 'error': 'Failed to add track'}), 500