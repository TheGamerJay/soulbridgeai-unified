"""
User Consent Management Routes
Interface for users to manage AI training consent for their creative works
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime, timezone
import traceback

from services.vector_lyric_service import create_vector_lyric_service
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan

logger = logging.getLogger(__name__)

# Create blueprint
consent_bp = Blueprint('consent', __name__, url_prefix='/api/consent')

# Initialize vector service for consent management
try:
    vector_service = create_vector_lyric_service()
    logger.info("✅ Vector service loaded for consent management")
except Exception as e:
    logger.error(f"❌ Failed to load vector service: {e}")
    vector_service = None

@consent_bp.route('/status', methods=['GET'])
@require_auth
def get_user_consent_status():
    """Get current user's AI training consent status"""
    
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'Unknown User')
        
        if not vector_service:
            return jsonify({
                'success': False,
                'error': 'Consent service unavailable'
            }), 503
        
        # Get current consent status
        consent_info = vector_service.get_artist_consent(f"user_{user_id}")
        
        if consent_info:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'consent_status': {
                    'consent_given': consent_info.get('consent_given', False),
                    'training_allowed': consent_info.get('training_allowed', False),
                    'commercial_use': consent_info.get('commercial_use', False),
                    'attribution_required': consent_info.get('attribution_required', True),
                    'consent_date': consent_info.get('consent_date'),
                    'restrictions': consent_info.get('restrictions', {}),
                    'consent_version': consent_info.get('consent_version', '1.0')
                }
            })
        else:
            # No consent record - return default (no consent)
            return jsonify({
                'success': True,
                'user_id': user_id,
                'consent_status': {
                    'consent_given': False,
                    'training_allowed': False,
                    'commercial_use': False,
                    'attribution_required': True,
                    'consent_date': None,
                    'restrictions': {},
                    'consent_version': '1.0'
                }
            })
        
    except Exception as e:
        logger.error(f"❌ Error getting consent status: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent status'
        }), 500

@consent_bp.route('/update', methods=['POST'])
@require_auth
@rate_limit_moderate
def update_user_consent():
    """Update user's AI training consent preferences"""
    
    try:
        user_id = session.get('user_id')
        username = session.get('username', 'Unknown User')
        
        if not vector_service:
            return jsonify({
                'success': False,
                'error': 'Consent service unavailable'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No consent data provided'
            }), 400
        
        # Extract consent preferences
        consent_given = data.get('consent_given', False)
        training_allowed = data.get('training_allowed', False)
        commercial_use = data.get('commercial_use', False)
        attribution_required = data.get('attribution_required', True)
        restrictions = data.get('restrictions', {})
        
        # If consent is denied, ensure training is not allowed
        if not consent_given:
            training_allowed = False
            commercial_use = False
        
        # Update consent record
        success = vector_service.update_artist_consent(
            artist_id=f"user_{user_id}",
            artist_name=username,
            consent_given=consent_given,
            training_allowed=training_allowed,
            commercial_use=commercial_use,
            attribution_required=attribution_required,
            restrictions=restrictions
        )
        
        if success:
            logger.info(f"✅ Updated AI training consent for user {user_id}: consent={consent_given}, training={training_allowed}")
            
            # Log consent change for audit trail
            consent_action = "granted" if consent_given else "revoked"
            training_action = "allowed" if training_allowed else "denied"
            
            return jsonify({
                'success': True,
                'message': f'AI training consent {consent_action} successfully',
                'consent_status': {
                    'consent_given': consent_given,
                    'training_allowed': training_allowed,
                    'commercial_use': commercial_use,
                    'attribution_required': attribution_required,
                    'restrictions': restrictions,
                    'effective_date': datetime.now(timezone.utc).isoformat()
                },
                'impact': {
                    'immediate_effect': True,
                    'applies_to_future_content': True,
                    'retroactive_removal': not training_allowed,
                    'description': f"Your creative works will {'be used' if training_allowed else 'NOT be used'} for AI training from this moment forward."
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update consent preferences'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error updating consent: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Consent update failed'
        }), 500

@consent_bp.route('/info', methods=['GET'])
def get_consent_information():
    """Get information about AI training consent (public endpoint)"""
    
    try:
        consent_info = {
            'what_is_ai_training_consent': {
                'description': 'AI Training Consent determines whether your creative works (lyrics, poems, stories) can be used to improve our AI models.',
                'when_applies': 'When you create content using SoulBridge AI tools',
                'what_data': ['Your generated lyrics', 'Your poems and stories', 'Your creative writing', 'Style patterns and themes'],
                'what_not_included': ['Personal information', 'Account details', 'Private messages', 'Payment information']
            },
            'consent_options': {
                'consent_given': {
                    'description': 'Allow your creative works to be used for AI improvement',
                    'benefits': ['Help improve AI for all users', 'Contribute to creative AI advancement', 'Better personalized suggestions'],
                    'requirements': ['All usage is anonymous', 'No personal attribution', 'Content quality standards apply']
                },
                'training_allowed': {
                    'description': 'Specifically allow training AI models with your content',
                    'impact': 'Your creative works may influence future AI outputs',
                    'control': 'Can be revoked at any time'
                },
                'commercial_use': {
                    'description': 'Allow commercial use of training data derived from your content',
                    'note': 'Your original works remain yours - only allows AI learning'
                },
                'attribution_required': {
                    'description': 'Require attribution when your style influences AI outputs',
                    'default': True,
                    'note': 'Currently for internal tracking only'
                }
            },
            'your_rights': {
                'opt_out_anytime': 'You can revoke consent at any time',
                'immediate_effect': 'Changes take effect immediately for new content',
                'retroactive_removal': 'Previous training data can be marked for exclusion',
                'data_portability': 'You can request export of your consent history',
                'transparency': 'You can see how your consent preferences are applied'
            },
            'data_handling': {
                'anonymization': 'All creative works are anonymized before training',
                'quality_filtering': 'Only high-quality content is used for training',
                'retention_policy': 'Training data is retained according to our data policy',
                'security': 'All training data is encrypted and securely stored'
            }
        }
        
        return jsonify({
            'success': True,
            'consent_information': consent_info,
            'last_updated': '2024-09-05',
            'version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting consent info: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent information'
        }), 500

@consent_bp.route('/history', methods=['GET'])
@require_auth
def get_consent_history():
    """Get user's consent change history (audit trail)"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Only Silver and Gold users can view consent history
        if user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': 'Consent history requires Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        # For now, return current consent as history
        # In future, implement full audit trail
        if not vector_service:
            return jsonify({
                'success': False,
                'error': 'Consent service unavailable'
            }), 503
        
        consent_info = vector_service.get_artist_consent(f"user_{user_id}")
        
        if consent_info:
            history = [{
                'action': 'consent_updated',
                'date': consent_info.get('consent_date', datetime.now(timezone.utc).isoformat()),
                'consent_given': consent_info.get('consent_given'),
                'training_allowed': consent_info.get('training_allowed'),
                'commercial_use': consent_info.get('commercial_use'),
                'version': consent_info.get('consent_version', '1.0')
            }]
        else:
            history = []
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'consent_history': history,
            'total_changes': len(history)
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting consent history: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent history'
        }), 500

@consent_bp.route('/prompt', methods=['GET'])
@require_auth
def get_consent_prompt():
    """Get consent prompt for user interface"""
    
    try:
        user_id = session.get('user_id')
        
        # Check if user has already set consent preferences
        has_consent_record = False
        if vector_service:
            consent_info = vector_service.get_artist_consent(f"user_{user_id}")
            has_consent_record = consent_info is not None
        
        prompt_data = {
            'show_prompt': not has_consent_record,
            'title': '🤖 AI Training Consent',
            'message': {
                'header': 'Help Us Improve AI for Everyone',
                'body': [
                    'Your creative works can help train our AI to be more helpful and creative.',
                    'This is completely optional and you can change your mind at any time.',
                    'All data is anonymized and used only to improve AI capabilities.'
                ],
                'benefits': [
                    '🎨 Better AI suggestions for your creative process',
                    '🌟 Contribute to advancing creative AI technology', 
                    '🔒 Your original works always remain yours',
                    '⚡ Immediate effect - changes apply right away'
                ]
            },
            'options': {
                'consent_given': {
                    'label': 'Allow AI Learning',
                    'description': 'Let AI learn from my creative works to improve suggestions for all users',
                    'default': False
                },
                'training_allowed': {
                    'label': 'Training Permission', 
                    'description': 'Allow my content to be used in AI model training (requires consent)',
                    'default': False,
                    'requires': 'consent_given'
                },
                'commercial_use': {
                    'label': 'Commercial Training',
                    'description': 'Allow commercial use of AI models trained with my content',
                    'default': False,
                    'requires': 'training_allowed'
                },
                'attribution_required': {
                    'label': 'Attribution Preference',
                    'description': 'I would like attribution when my style influences AI outputs',
                    'default': True
                }
            },
            'legal': {
                'note': 'By providing consent, you agree to the AI Training Terms in our Terms of Service.',
                'links': {
                    'terms_of_service': '/legal/terms',
                    'privacy_policy': '/legal/privacy',
                    'ai_training_policy': '/legal/ai-training'
                }
            }
        }
        
        return jsonify({
            'success': True,
            'prompt': prompt_data,
            'user_has_consent_record': has_consent_record
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting consent prompt: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent prompt'
        }), 500