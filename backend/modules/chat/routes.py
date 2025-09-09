"""
SoulBridge AI - Chat Routes  
Main chat system routes and endpoints
Extracted from monolith app.py with improvements
"""
import logging
from flask import Blueprint, request, jsonify, session, render_template, redirect
from datetime import datetime

from ..auth.session_manager import requires_login, get_user_id
from ..companions.companion_data import get_companion_by_id, get_all_companions
from ..companions.access_control import can_access_companion
from ..tiers.artistic_time import get_effective_access
from .chat_service import ChatService
from .conversation_manager import ConversationManager
from .message_handler import MessageHandler

logger = logging.getLogger(__name__)

# Create chat blueprint
chat_bp = Blueprint('chat', __name__)

# Initialize chat services
chat_service = ChatService()
conversation_manager = ConversationManager()
message_handler = MessageHandler()

@chat_bp.route('/chat')
@requires_login
def chat_home():
    """Main chat page - redirect to companion selection if needed"""
    try:
        user_id = get_user_id()
        
        # Check if user has selected a companion
        selected_companion = session.get('selected_companion')
        
        if not selected_companion:
            return redirect("/companion-selection")
        
        # Verify user still has access to selected companion
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        referrals = session.get('referrals', 0)
        
        companion = get_companion_by_id(selected_companion)
        if not companion:
            return redirect("/companion-selection")
        
        access_check = can_access_companion(user_plan, trial_active, referrals, companion)
        if not access_check['can_access']:
            return redirect("/tiers?upgrade_required=true")
        
        # Get user's effective access for UI limits
        effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
        
        # Get chat statistics
        chat_stats = chat_service.get_chat_stats(user_id)
        message_stats = message_handler.get_user_message_stats(user_id)
        rate_limit_info = message_handler.get_rate_limit_info(user_id, user_plan)
        
        return render_template('chat.html',
                             companion=companion,
                             effective_access=effective_access,
                             chat_stats=chat_stats,
                             message_stats=message_stats,
                             rate_limit_info=rate_limit_info,
                             user_plan=user_plan,
                             trial_active=trial_active)
        
    except Exception as e:
        logger.error(f"Error loading chat page: {e}")
        return render_template('error.html', error="Failed to load chat")

@chat_bp.route('/chat/<companion_id>')
@requires_login
def chat_companion(companion_id):
    """Chat with specific companion"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        referrals = session.get('referrals', 0)
        
        # Get companion data
        companion = get_companion_by_id(companion_id)
        if not companion:
            return render_template('error.html', error="Companion not found"), 404
        
        # Check access permissions
        access_check = can_access_companion(user_plan, trial_active, referrals, companion)
        if not access_check['can_access']:
            return redirect("/tiers?upgrade_required=true")
        
        # Set selected companion in session
        session['selected_companion'] = companion_id
        
        # Update new companion persistence system
        try:
            from display_name_helpers import set_companion_data
            companion_data = {
                'companion_id': companion_id,
                'name': companion.get('display_name', companion.get('name', companion_id)),
                'tier': companion.get('tier', 'bronze')
            }
            set_companion_data(user_id, companion_data)
            logger.info(f"✅ Updated companion persistence for user {user_id}: {companion_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not update companion persistence: {e}")
        
        # Start conversation session
        session_id = conversation_manager.start_conversation_session(user_id, companion_id)
        
        # Get effective access for UI
        effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
        
        # Get conversation history
        chat_stats = chat_service.get_chat_stats(user_id)
        conversation_summary = conversation_manager.get_conversation_summary(user_id, companion_id)
        
        return render_template('chat.html',
                             companion=companion,
                             session_id=session_id,
                             effective_access=effective_access,
                             chat_stats=chat_stats,
                             conversation_summary=conversation_summary,
                             user_plan=user_plan,
                             trial_active=trial_active)
        
    except Exception as e:
        logger.error(f"Error loading companion chat {companion_id}: {e}")
        return render_template('error.html', error="Failed to load companion chat")

@chat_bp.route('/api/chat/send', methods=['POST'])
@requires_login
def send_chat_message():
    """Send a message to AI companion - Uses 1 Artistic Time credit per message"""
    try:
        user_id = get_user_id()
        
        # Check and deduct credits for chat message (1 credit)
        from ...modules.credits.operations import get_artistic_time, deduct_artistic_time
        
        current_credits = get_artistic_time(user_id)
        if current_credits < 1:
            return jsonify({
                "success": False,
                "error": "Insufficient Artistic Time credits for chat message",
                "credits_needed": 1,
                "current_credits": current_credits,
                "upgrade_required": True
            }), 402  # Payment Required
        
        # Deduct 1 credit for the message
        if not deduct_artistic_time(user_id, 1):
            return jsonify({
                "success": False,
                "error": "Failed to deduct credits for chat message"
            }), 500
        
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        message = data.get('message', '').strip()
        companion_id = data.get('companion_id') or session.get('selected_companion')
        session_id = data.get('session_id')
        
        if not companion_id:
            return jsonify({"success": False, "error": "No companion selected"}), 400
        
        # Validate message
        validation = message_handler.validate_message(message, user_id, user_plan, trial_active)
        if not validation['valid']:
            return jsonify({"success": False, "error": validation['error']}), 400
        
        # Verify access to companion
        companion = get_companion_by_id(companion_id)
        if not companion:
            return jsonify({"success": False, "error": "Companion not found"}), 404
        
        referrals = session.get('referrals', 0)
        access_check = can_access_companion(user_plan, trial_active, referrals, companion)
        if not access_check['can_access']:
            return jsonify({
                "success": False, 
                "error": "Access denied to this companion",
                "reason": access_check.get('reason', 'Upgrade required')
            }), 403
        
        # Update session activity if provided
        if session_id:
            conversation_manager.update_session_activity(session_id)
        
        # Process the message
        logger.info(f"💬 Processing message from user {user_id} to {companion['name']}")
        
        response_data = chat_service.process_chat_message(
            message=validation['cleaned_message'],
            companion_id=companion_id,
            user_id=user_id,
            user_plan=user_plan,
            trial_active=trial_active
        )
        
        if not response_data['success']:
            return jsonify({
                "success": False,
                "error": response_data.get('error', 'Failed to generate response'),
                "fallback": response_data.get('fallback')
            }), 500
        
        # Track usage
        message_handler.track_message_usage(
            user_id=user_id,
            companion_id=companion_id,
            message_length=len(validation['cleaned_message']),
            model_used=response_data.get('model_used', 'unknown'),
            tokens_used=response_data.get('tokens_used')
        )
        
        # Get updated rate limit info
        rate_limit_info = message_handler.get_rate_limit_info(user_id, user_plan)
        
        # Get updated credit balance after deduction
        remaining_credits = get_artistic_time(user_id)
        
        return jsonify({
            "success": True,
            "message": validation['cleaned_message'],
            "response": response_data['response'],
            "companion": response_data['companion'],
            "model_used": response_data.get('model_used'),
            "tokens_used": response_data.get('tokens_used'),
            "rate_limit_info": rate_limit_info,
            "session_id": session_id,
            "credits_charged": 1,
            "credits_remaining": remaining_credits
        })
        
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to send message",
            "details": str(e)
        }), 500

@chat_bp.route('/api/chat/history/<companion_id>')
@requires_login
def get_chat_history(companion_id):
    """Get conversation history with a companion"""
    try:
        user_id = get_user_id()
        limit = request.args.get('limit', 20, type=int)
        
        # Verify access to companion
        companion = get_companion_by_id(companion_id)
        if not companion:
            return jsonify({"success": False, "error": "Companion not found"}), 404
        
        # Get conversation history from chat service
        history = chat_service._get_conversation_history(user_id, companion_id, limit)
        
        return jsonify({
            "success": True,
            "companion_id": companion_id,
            "companion_name": companion['name'],
            "history": history,
            "total_messages": len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get chat history"
        }), 500

@chat_bp.route('/api/chat/clear-history', methods=['POST'])
@requires_login
def clear_chat_history():
    """Clear conversation history"""
    try:
        user_id = get_user_id()
        data = request.get_json() or {}
        companion_id = data.get('companion_id')
        
        # Clear history
        success = chat_service.clear_conversation_history(user_id, companion_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Chat history cleared" + (f" with {companion_id}" if companion_id else " for all companions")
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear chat history"
            }), 500
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to clear chat history"
        }), 500

@chat_bp.route('/api/chat/stats')
@requires_login
def get_chat_stats():
    """Get user's chat statistics"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        
        days = request.args.get('days', 7, type=int)
        
        # Get various statistics
        chat_stats = chat_service.get_chat_stats(user_id)
        message_stats = message_handler.get_user_message_stats(user_id, days)
        rate_limit_info = message_handler.get_rate_limit_info(user_id, user_plan)
        conversation_insights = conversation_manager.get_conversation_insights(user_id, days)
        
        return jsonify({
            "success": True,
            "stats": {
                "chat_stats": chat_stats,
                "message_stats": message_stats,
                "rate_limit_info": rate_limit_info,
                "conversation_insights": conversation_insights,
                "active_sessions": conversation_manager.get_user_active_sessions(user_id)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get chat statistics"
        }), 500

@chat_bp.route('/api/chat/session/<session_id>/end', methods=['POST'])
@requires_login
def end_chat_session(session_id):
    """End a conversation session"""
    try:
        success = conversation_manager.end_conversation_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Conversation session ended"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Session not found or already ended"
            }), 404
        
    except Exception as e:
        logger.error(f"Error ending chat session: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to end session"
        }), 500

@chat_bp.route('/api/chat/models/debug')
@requires_login
def debug_model_selection():
    """Debug endpoint to check model selection by tier"""
    try:
        tier = request.args.get('tier', 'bronze')
        trial_active = request.args.get('trial', 'false').lower() == 'true'
        
        model = chat_service.get_model_for_tier(tier, trial_active)
        
        return jsonify({
            "success": True,
            "tier": tier,
            "trial_active": trial_active,
            "selected_model": model,
            "tier_models": chat_service.tier_models,
            "openai_available": chat_service.openai_client is not None
        })
        
    except Exception as e:
        logger.error(f"Error in model debug: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Admin/Debug endpoints
@chat_bp.route('/api/admin/chat/cleanup-sessions', methods=['POST'])
@requires_login
def admin_cleanup_sessions():
    """Admin endpoint to cleanup inactive sessions"""
    try:
        # Check admin access
        if not session.get('is_admin', False):
            return jsonify({"success": False, "error": "Admin access required"}), 403
        
        hours = request.json.get('max_inactive_hours', 2) if request.json else 2
        cleaned_up = conversation_manager.cleanup_inactive_sessions(hours)
        
        return jsonify({
            "success": True,
            "sessions_cleaned": cleaned_up,
            "message": f"Cleaned up {cleaned_up} inactive sessions"
        })
        
    except Exception as e:
        logger.error(f"Error in admin cleanup sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def init_chat_system(app, database_manager=None, openai_client=None):
    """Initialize the chat system with app dependencies"""
    global chat_service, conversation_manager, message_handler
    
    # Configure chat service with dependencies
    if openai_client:
        chat_service.openai_client = openai_client
    
    # Set up periodic cleanup of inactive sessions
    if app.config.get('AUTO_CLEANUP_CHAT_SESSIONS', True):
        import threading
        import time
        
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    conversation_manager.cleanup_inactive_sessions(2)
                except Exception as e:
                    logger.error(f"Error in chat session cleanup worker: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Chat session cleanup worker started")
    
    logger.info("Chat system initialized successfully")