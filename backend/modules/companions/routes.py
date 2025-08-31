"""
SoulBridge AI - Companion Routes
Extracted from app.py monolith for modular architecture
"""
import logging
from flask import Blueprint, render_template, request, session, jsonify, redirect
from ..auth.session_manager import requires_login, get_user_id
from .companion_data import get_all_companions, get_companion_by_id, get_companions_by_tier
from .access_control import (
    get_user_companion_access, 
    require_companion_access,
    can_access_companion,
    companion_unlock_state_new
)
from .chat_service import CompanionChatService

logger = logging.getLogger(__name__)

# Create blueprint for companion routes
companions_bp = Blueprint('companions', __name__)

@companions_bp.route("/companion-selection")
@requires_login
def companion_selection():
    """Companion selection page"""
    try:
        access_info = get_user_companion_access()
        companions = get_all_companions()
        
        return render_template("companion_selection.html", 
                             companions=companions,
                             access_info=access_info)
        
    except Exception as e:
        logger.error(f"Error in companion selection: {e}")
        return render_template("error.html", error="Unable to load companion selection")

@companions_bp.route("/chat")
@requires_login  
def chat_home():
    """Main chat page - redirect to companion selection if needed"""
    try:
        # Check if user has selected a companion
        selected_companion = session.get('selected_companion')
        
        if not selected_companion:
            return redirect("/companion-selection")
        
        # Check if user still has access to selected companion
        if not require_companion_access(selected_companion):
            # Access revoked, back to selection
            session.pop('selected_companion', None)
            return redirect("/companion-selection")
        
        companion = get_companion_by_id(selected_companion)
        return render_template("chat.html", companion=companion)
        
    except Exception as e:
        logger.error(f"Error in chat home: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/chat/<tier>")
@requires_login
def chat_tier(tier):
    """Chat page for specific tier"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Check if user can access this tier
        if not can_access_companion(user_plan, tier, trial_active):
            return redirect("/companion-selection")
        
        companions = get_companions_by_tier(tier)
        return render_template("chat_tier.html", 
                             tier=tier, 
                             companions=companions)
        
    except Exception as e:
        logger.error(f"Error in tier chat {tier}: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/chat/<tier>/<companion_id>")
@requires_login
def companion_specific_chat(tier, companion_id):
    """Chat with specific companion"""
    try:
        # Verify companion exists and user has access
        companion = get_companion_by_id(companion_id)
        if not companion:
            logger.warning(f"Companion not found: {companion_id}")
            return redirect("/companion-selection")
        
        if not require_companion_access(companion_id):
            logger.warning(f"User lacks access to companion: {companion_id}")
            return redirect("/companion-selection")
        
        # Set as selected companion
        session['selected_companion'] = companion_id
        session.modified = True
        
        return render_template("companion_chat.html", 
                             companion=companion,
                             tier=tier)
        
    except Exception as e:
        logger.error(f"Error in companion chat {companion_id}: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/api/companions")
@requires_login
def api_companions():
    """API endpoint for companion data"""
    try:
        access_info = get_user_companion_access()
        companions = get_all_companions()
        
        # Add access information to each companion
        for companion in companions:
            companion['can_access'] = require_companion_access(companion['id'])
        
        return jsonify({
            'success': True,
            'companions': companions,
            'access_info': access_info
        })
        
    except Exception as e:
        logger.error(f"Error in companions API: {e}")
        return jsonify({'success': False, 'error': 'Failed to load companions'}), 500

@companions_bp.route("/api/sapphire-chat", methods=["POST"])
@requires_login
def sapphire_chat():
    """Main chat processing endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        companion_id = data.get('companion_id') or session.get('selected_companion')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        if not companion_id:
            return jsonify({'success': False, 'error': 'No companion selected'}), 400
        
        # Verify access to companion
        if not require_companion_access(companion_id):
            return jsonify({'success': False, 'error': 'Access denied to this companion'}), 403
        
        # Process chat message
        chat_service = CompanionChatService()
        result = chat_service.process_chat(
            user_id=get_user_id(),
            companion_id=companion_id,
            message=message
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in sapphire chat: {e}")
        return jsonify({'success': False, 'error': 'Chat processing failed'}), 500

@companions_bp.route("/voice-chat")
@requires_login
def voice_chat():
    """Voice chat page (Gold tier feature)"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Voice chat requires Gold tier access
        if not can_access_companion(user_plan, 'gold', trial_active):
            return redirect("/companion-selection")
        
        return render_template("voice_chat.html")
        
    except Exception as e:
        logger.error(f"Error in voice chat: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/api/voice-chat/process", methods=["POST"])
@requires_login
def process_voice_chat():
    """Process voice chat messages (Gold tier feature)"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Voice chat requires Gold tier access
        if not can_access_companion(user_plan, 'gold', trial_active):
            return jsonify({'success': False, 'error': 'Gold tier required'}), 403
        
        # Voice chat processing logic would go here
        return jsonify({'success': True, 'message': 'Voice chat processing not implemented yet'})
        
    except Exception as e:
        logger.error(f"Error in voice chat processing: {e}")
        return jsonify({'success': False, 'error': 'Voice processing failed'}), 500

@companions_bp.route("/community/companions")
def community_companions():
    """Community companion showcase (public page)"""
    try:
        companions = get_all_companions()
        return render_template("community_companions.html", companions=companions)
        
    except Exception as e:
        logger.error(f"Error in community companions: {e}")
        return render_template("error.html", error="Unable to load community page")