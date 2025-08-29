"""
Companion Routes
AI companion selection and chat endpoints
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import logging

from shared.middleware.session_manager import SessionManager, login_required, plan_required
from shared.utils.helpers import sanitize_input, log_action, get_user_ip
from .models import get_companion_repository, CompanionTier
from .services import CompanionService

logger = logging.getLogger(__name__)

# Create companions blueprint
companions_bp = Blueprint('companions', __name__, url_prefix='/companions')

# Initialize services
companion_repo = get_companion_repository()
companion_service = CompanionService()

@companions_bp.route('/')
@login_required
def companion_selection():
    """Companion selection page"""
    try:
        user_context = SessionManager.get_user_context()
        user_plan = user_context['user_plan']
        trial_active = user_context['trial_active']
        
        # Get user referral count (placeholder - implement when referral system is added)
        referral_count = 0
        
        # Get accessible companions
        accessible_companions = companion_repo.get_accessible_companions(
            user_plan, trial_active, referral_count
        )
        
        # Get companion stats
        companion_stats = companion_repo.get_companion_stats_by_tier(
            user_plan, trial_active, referral_count
        )
        
        # Organize companions by tier for display
        bronze_companions = [c for c in accessible_companions if c.tier == CompanionTier.BRONZE]
        silver_companions = [c for c in accessible_companions if c.tier == CompanionTier.SILVER]
        gold_companions = [c for c in accessible_companions if c.tier == CompanionTier.GOLD]
        referral_companions = [c for c in accessible_companions if c.tier == CompanionTier.REFERRAL]
        
        # Get all companions for display (with lock status)
        all_companions_by_tier = {
            'bronze': companion_repo.get_companions_by_tier(CompanionTier.BRONZE),
            'silver': companion_repo.get_companions_by_tier(CompanionTier.SILVER),
            'gold': companion_repo.get_companions_by_tier(CompanionTier.GOLD),
            'referral': companion_repo.get_companions_by_tier(CompanionTier.REFERRAL)
        }
        
        # Add accessibility info
        accessible_ids = {c.id for c in accessible_companions}
        
        template_data = {
            **user_context,
            'bronze_companions': bronze_companions,
            'silver_companions': silver_companions,
            'gold_companions': gold_companions,
            'referral_companions': referral_companions,
            'all_companions_by_tier': all_companions_by_tier,
            'accessible_ids': accessible_ids,
            'companion_stats': companion_stats,
            'referral_count': referral_count
        }
        
        return render_template('companions/selection.html', **template_data)
    
    except Exception as e:
        logger.error(f"❌ Companion selection error: {e}")
        return render_template('errors/500.html'), 500

@companions_bp.route('/api/accessible')
@login_required
def api_accessible_companions():
    """API endpoint for accessible companions"""
    try:
        user_context = SessionManager.get_user_context()
        user_plan = user_context['user_plan']
        trial_active = user_context['trial_active']
        referral_count = 0  # Placeholder
        
        accessible_companions = companion_repo.get_accessible_companions(
            user_plan, trial_active, referral_count
        )
        
        companions_data = []
        for companion in accessible_companions:
            companions_data.append({
                'id': companion.id,
                'name': companion.name,
                'tier': companion.tier.value,
                'image_url': companion.image_url,
                'description': companion.description,
                'greeting': companion.greeting
            })
        
        return jsonify({
            'companions': companions_data,
            'total': len(companions_data),
            'user_plan': user_plan,
            'trial_active': trial_active
        })
    
    except Exception as e:
        logger.error(f"❌ API accessible companions error: {e}")
        return jsonify({'error': 'Failed to get companions'}), 500

@companions_bp.route('/api/check-access/<companion_id>')
@login_required
def api_check_access(companion_id):
    """API endpoint to check companion access"""
    try:
        user_context = SessionManager.get_user_context()
        user_plan = user_context['user_plan']
        trial_active = user_context['trial_active']
        referral_count = 0  # Placeholder
        
        can_access, reason = companion_repo.can_access_companion(
            companion_id, user_plan, trial_active, referral_count
        )
        
        companion = companion_repo.get_companion_by_id(companion_id)
        
        return jsonify({
            'can_access': can_access,
            'reason': reason,
            'companion': {
                'id': companion.id,
                'name': companion.name,
                'tier': companion.tier.value
            } if companion else None
        })
    
    except Exception as e:
        logger.error(f"❌ API check access error: {e}")
        return jsonify({'error': 'Access check failed'}), 500

@companions_bp.route('/chat/<companion_id>')
@login_required
def companion_chat(companion_id):
    """Chat with specific companion"""
    try:
        user_context = SessionManager.get_user_context()
        user_plan = user_context['user_plan']
        trial_active = user_context['trial_active']
        referral_count = 0  # Placeholder
        
        # Sanitize companion ID
        companion_id = sanitize_input(companion_id)
        
        # Check if user can access this companion
        can_access, reason = companion_repo.can_access_companion(
            companion_id, user_plan, trial_active, referral_count
        )
        
        if not can_access:
            logger.warning(f"⚠️ User {user_context['user_id']} denied access to companion {companion_id}: {reason}")
            return redirect(url_for('companions.companion_selection'))
        
        # Get companion data
        companion = companion_repo.get_companion_by_id(companion_id)
        
        if not companion:
            logger.error(f"❌ Companion not found: {companion_id}")
            return redirect(url_for('companions.companion_selection'))
        
        # Log companion access
        log_action(
            user_id=user_context['user_id'],
            action='companion_chat_started',
            details={
                'companion_id': companion_id,
                'companion_name': companion.name,
                'companion_tier': companion.tier.value,
                'user_plan': user_plan,
                'trial_active': trial_active,
                'ip': get_user_ip(request)
            }
        )
        
        # Set current companion in session
        session['current_companion'] = companion_id
        session.modified = True
        
        template_data = {
            **user_context,
            'companion': companion,
            'companion_data': {
                'id': companion.id,
                'name': companion.name,
                'tier': companion.tier.value,
                'image_url': companion.image_url,
                'greeting': companion.greeting,
                'description': companion.description,
                'personality': companion.personality
            }
        }
        
        return render_template('companions/chat.html', **template_data)
    
    except Exception as e:
        logger.error(f"❌ Companion chat error: {e}")
        return render_template('errors/500.html'), 500

@companions_bp.route('/api/chat/<companion_id>', methods=['POST'])
@login_required
def api_companion_chat(companion_id):
    """API endpoint for companion chat"""
    try:
        user_context = SessionManager.get_user_context()
        user_plan = user_context['user_plan']
        trial_active = user_context['trial_active']
        referral_count = 0  # Placeholder
        
        # Sanitize companion ID
        companion_id = sanitize_input(companion_id)
        
        # Check access
        can_access, reason = companion_repo.can_access_companion(
            companion_id, user_plan, trial_active, referral_count
        )
        
        if not can_access:
            return jsonify({'error': f'Access denied: {reason}'}), 403
        
        # Get message from request
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = sanitize_input(data['message'])
        if not user_message.strip():
            return jsonify({'error': 'Empty message'}), 400
        
        # Get companion
        companion = companion_repo.get_companion_by_id(companion_id)
        if not companion:
            return jsonify({'error': 'Companion not found'}), 404
        
        # Generate response using companion service
        response = companion_service.generate_response(
            companion_id=companion_id,
            user_message=user_message,
            user_context=user_context
        )
        
        if response.get('error'):
            return jsonify({'error': response['error']}), 500
        
        # Log chat interaction
        log_action(
            user_id=user_context['user_id'],
            action='companion_chat_message',
            details={
                'companion_id': companion_id,
                'message_length': len(user_message),
                'response_length': len(response.get('response', '')),
                'ip': get_user_ip(request)
            }
        )
        
        return jsonify({
            'response': response['response'],
            'companion_name': companion.name,
            'companion_id': companion_id
        })
    
    except Exception as e:
        logger.error(f"❌ API companion chat error: {e}")
        return jsonify({'error': 'Chat failed'}), 500

@companions_bp.route('/switch/<companion_id>')
@login_required
def switch_companion(companion_id):
    """Switch to different companion"""
    try:
        user_context = SessionManager.get_user_context()
        
        # Redirect to companion chat
        return redirect(url_for('companions.companion_chat', companion_id=companion_id))
    
    except Exception as e:
        logger.error(f"❌ Switch companion error: {e}")
        return redirect(url_for('companions.companion_selection'))

# Legacy route redirects for compatibility
@companions_bp.route('/select')
def select_redirect():
    """Redirect old select route"""
    return redirect(url_for('companions.companion_selection'))

@companions_bp.route('/community')
def community_redirect():
    """Redirect old community route"""
    return redirect(url_for('companions.companion_selection'))