"""
Clean Display Name Routes - One Writer, One Reader
"""
from flask import Blueprint, request, jsonify, session
from security_config import require_auth
from display_name_helpers import set_display_name, get_display_name, get_profile_image
import logging

logger = logging.getLogger(__name__)

clean_display_bp = Blueprint('clean_display', __name__)

# POST /api/display-name - THE ONLY WRITER
@clean_display_bp.route('/api/display-name', methods=['POST'])
@require_auth
def update_display_name():
    """Single writer endpoint for display names"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'No user ID in session'}), 401
            
        data = request.get_json() or {}
        name = data.get('displayName', '').strip()
        
        # Validation with guardrails
        if not name:
            return jsonify({'success': False, 'error': 'Display name cannot be empty'}), 400
            
        if name.lower() in ['soulbridge user', 'user']:
            return jsonify({'success': False, 'error': 'Invalid display name'}), 400
            
        if len(name) > 50:
            return jsonify({'success': False, 'error': 'Display name too long (max 50 chars)'}), 400
        
        # DB write with commit
        success = set_display_name(user_id, name)
        
        if success:
            # Session mirrors DB after successful commit
            session['display_name'] = name
            session['user_name'] = name
            session.modified = True
            
            logger.info(f"✅ WRITER SUCCESS: User {user_id} → '{name}'")
            return jsonify({'success': True, 'displayName': name})
        else:
            return jsonify({'success': False, 'error': 'Failed to update display name'}), 500
            
    except Exception as e:
        logger.error(f"Display name update error: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

# GET /api/me - THE ONLY READER  
@clean_display_bp.route('/api/me', methods=['GET'])
@require_auth
def me():
    """Single reader endpoint - DB is source of truth"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'No user ID in session'}), 401
        
        # DB read first - source of truth for both display name and profile image
        name = get_display_name(user_id)
        profile_image_url = get_profile_image(user_id)
        
        # Session mirrors DB (never overrides it)
        session['display_name'] = name if name != "User" else ""
        session['user_name'] = session['display_name']
        session['profile_image'] = profile_image_url
        session.modified = True
        
        # Response shape: { success: true, user: { id, displayName, ... } }
        user_data = {
            'id': user_id,
            'displayName': name,
            # Add other user fields as needed
            'email': session.get('email', ''),
            'plan': session.get('user_plan', 'bronze'),
            'profileImage': profile_image_url
        }
        
        response = jsonify({'success': True, 'user': user_data})
        
        # No caching headers
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Cookie'
        
        logger.info(f"✅ READER SUCCESS: User {user_id} → '{name}' | Image: {profile_image_url}")
        return response
        
    except Exception as e:
        logger.error(f"Me endpoint error: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500