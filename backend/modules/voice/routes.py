"""
SoulBridge AI - Voice Routes
Voice chat and voice journaling endpoints
Extracted from monolith app.py with improvements
"""
import logging
from flask import Blueprint, request, jsonify, session, render_template, redirect
from .voice_chat_service import VoiceChatService
from .voice_journal_service import VoiceJournalService
from .audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

# Create voice blueprint
voice_bp = Blueprint('voice', __name__, url_prefix='/voice')

# Initialize services
voice_chat_service = VoiceChatService()
voice_journal_service = VoiceJournalService()
audio_processor = AudioProcessor()

def _get_current_user():
    """Get current user info from session"""
    if not session.get('user_authenticated'):
        return None
    
    return {
        'id': session.get('user_id'),
        'email': session.get('user_email'),
        'plan': session.get('user_plan', 'bronze'),
        'trial_active': session.get('trial_active', False)
    }

def _check_credits(user_id: int, feature: str) -> dict:
    """Check and deduct credits for voice features"""
    try:
        from ..credits import get_artistic_time, deduct_artistic_time, get_feature_cost
        
        cost = get_feature_cost(feature)
        current_credits = get_artistic_time(user_id)
        
        if current_credits < cost:
            return {
                "success": False,
                "error": f"Insufficient credits. Need {cost}, you have {current_credits}.",
                "credits_needed": cost,
                "credits_available": current_credits
            }
        
        # Deduct credits
        if deduct_artistic_time(user_id, cost):
            logger.info(f"💳 Deducted {cost} credits from user {user_id} for {feature}")
            return {
                "success": True,
                "credits_deducted": cost,
                "credits_remaining": current_credits - cost
            }
        else:
            return {
                "success": False,
                "error": "Failed to deduct credits"
            }
            
    except Exception as e:
        logger.error(f"Credit check error: {e}")
        return {
            "success": False,
            "error": "Credit system error"
        }

def _refund_credits(user_id: int, feature: str, reason: str = "processing_failed"):
    """Refund credits on failure"""
    try:
        from ..credits import refund_artistic_time, get_feature_cost
        
        cost = get_feature_cost(feature)
        if refund_artistic_time(user_id, cost, reason):
            logger.info(f"💰 Refunded {cost} credits to user {user_id}: {reason}")
            return True
        else:
            logger.error(f"❌ Failed to refund {cost} credits to user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Credit refund error: {e}")
        return False

# Voice Chat Routes
@voice_bp.route('/chat')
def voice_chat_page():
    """Render the voice chat page (Silver/Gold tier only)"""
    try:
        user = _get_current_user()
        if not user:
            return render_template('login.html', error="Please log in to access voice chat"), 401
        
        # Check tier access - Silver/Gold only
        if not voice_chat_service.validate_access(user['plan'], user['trial_active']):
            return redirect("/subscription?feature=voice-chat")
        
        # Get available companions
        companions = voice_chat_service.get_available_companions(
            user['plan'], user['trial_active']
        )
        
        return render_template("voice_chat.html", companions=companions)
        
    except Exception as e:
        logger.error(f"Voice chat page error: {e}")
        return render_template('error.html', 
                             error="Failed to load voice chat"), 500

@voice_bp.route('/chat/process', methods=['POST'])
def voice_chat_process():
    """Process voice chat audio - Whisper transcription + GPT-4 response"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check tier access - Silver/Gold only
        if not voice_chat_service.validate_access(user['plan'], user['trial_active']):
            return jsonify({
                "success": False, 
                "error": "Voice Chat requires Silver or Gold tier"
            }), 403
        
        # Validate request
        if 'audio' not in request.files:
            return jsonify({
                "success": False, 
                "error": "No audio file provided"
            }), 400
        
        audio_file = request.files['audio']
        companion_id = request.form.get('companion_id', 'blayzo')
        
        # Process voice audio
        result = voice_chat_service.process_voice_audio(audio_file, companion_id)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Voice chat processing error: {e}")
        return jsonify({
            "success": False, 
            "error": "Processing failed"
        }), 500

@voice_bp.route('/chat/companions', methods=['GET'])
def get_voice_chat_companions():
    """Get available companions for voice chat"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check tier access
        if not voice_chat_service.validate_access(user['plan'], user['trial_active']):
            return jsonify({
                "success": False, 
                "error": "Voice Chat requires Silver or Gold tier"
            }), 403
        
        companions = voice_chat_service.get_available_companions(
            user['plan'], user['trial_active']
        )
        
        return jsonify({
            "success": True,
            "companions": companions
        })
        
    except Exception as e:
        logger.error(f"Get companions error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to get companions"
        }), 500

# Voice Journaling Routes
@voice_bp.route('/journal')
def voice_journaling_page():
    """Voice journaling page"""
    try:
        user = _get_current_user()
        if not user:
            return redirect("/login")
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return redirect("/subscription?feature=voice-journaling")
        
        return render_template("voice_journaling.html")
        
    except Exception as e:
        logger.error(f"Voice journaling page error: {e}")
        return render_template('error.html', 
                             error="Failed to load voice journaling"), 500

@voice_bp.route('/journal/transcribe', methods=['POST'])
def voice_journaling_transcribe():
    """Transcribe and analyze voice recording"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return jsonify({
                "success": False, 
                "error": "Voice Journaling requires Silver tier, Gold tier, addon, or trial"
            }), 403
        
        # Validate request
        if 'audio' not in request.files:
            return jsonify({
                "success": False, 
                "error": "No audio file provided"
            }), 400
        
        audio_file = request.files['audio']
        
        # Validate audio file
        validation = voice_journal_service.validate_audio_file(audio_file)
        if not validation["valid"]:
            return jsonify({
                "success": False, 
                "error": validation["error"]
            }), 400
        
        # Check and deduct credits
        credit_result = _check_credits(user['id'], "voice_journaling")
        if not credit_result["success"]:
            return jsonify(credit_result), 403
        
        try:
            # Transcribe audio
            transcription_result = voice_journal_service.transcribe_audio(audio_file)
            if not transcription_result["success"]:
                _refund_credits(user['id'], "voice_journaling", "transcription_failed")
                return jsonify(transcription_result), 500
            
            transcription = transcription_result["transcription"]
            
            # Analyze emotions
            analysis_result = voice_journal_service.analyze_emotions(transcription)
            if not analysis_result["success"]:
                _refund_credits(user['id'], "voice_journaling", "analysis_failed")
                return jsonify(analysis_result), 500
            
            analysis = analysis_result["analysis"]
            
            logger.info(f"✅ Voice journal processed for user {user['id']}")
            
            return jsonify({
                "success": True,
                "transcription": transcription,
                "analysis": analysis,
                "credits_used": credit_result["credits_deducted"],
                "credits_remaining": credit_result["credits_remaining"]
            })
            
        except Exception as processing_error:
            # Refund credits on processing failure
            _refund_credits(user['id'], "voice_journaling", "processing_error")
            raise processing_error
            
    except Exception as e:
        logger.error(f"Voice journaling transcription error: {e}")
        return jsonify({
            "success": False, 
            "error": "Processing failed. Credits have been refunded."
        }), 500

@voice_bp.route('/journal/save', methods=['POST'])
def voice_journaling_save():
    """Save voice journal entry"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return jsonify({
                "success": False, 
                "error": "Voice Journaling requires Silver tier, Gold tier, addon, or trial"
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False, 
                "error": "No data provided"
            }), 400
        
        # Save entry
        result = voice_journal_service.save_entry(
            user['id'],
            data.get('transcription'),
            data.get('analysis')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Voice journal save error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to save entry"
        }), 500

@voice_bp.route('/journal/entries', methods=['GET'])
def voice_journaling_entries():
    """Get user's voice journal entries"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return jsonify({
                "success": False, 
                "error": "Voice Journaling requires Silver tier, Gold tier, addon, or trial"
            }), 403
        
        # Get entries
        limit = request.args.get('limit', 10, type=int)
        result = voice_journal_service.get_entries(user['id'], limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get voice journal entries error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to retrieve entries"
        }), 500

@voice_bp.route('/journal/entries/<entry_id>', methods=['DELETE'])
def voice_journaling_delete_entry(entry_id):
    """Delete a voice journal entry"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return jsonify({
                "success": False, 
                "error": "Voice Journaling requires Silver tier, Gold tier, addon, or trial"
            }), 403
        
        # Delete entry
        result = voice_journal_service.delete_entry(user['id'], entry_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Delete voice journal entry error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to delete entry"
        }), 500

@voice_bp.route('/journal/trends', methods=['GET'])
def voice_journaling_trends():
    """Get emotional trends from journal entries"""
    try:
        user = _get_current_user()
        if not user:
            return jsonify({
                "success": False, 
                "error": "Authentication required"
            }), 401
        
        # Check access
        user_addons = session.get('user_addons', [])
        if not voice_journal_service.validate_access(
            user['plan'], user_addons, user['trial_active']
        ):
            return jsonify({
                "success": False, 
                "error": "Voice Journaling requires Silver tier, Gold tier, addon, or trial"
            }), 403
        
        # Get trends
        days = request.args.get('days', 30, type=int)
        result = voice_journal_service.get_emotion_trends(user['id'], days)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get emotion trends error: {e}")
        return jsonify({
            "success": False, 
            "error": "Failed to analyze trends"
        }), 500

# Audio Processing Routes
@voice_bp.route('/audio/validate', methods=['POST'])
def validate_audio():
    """Validate uploaded audio file"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                "success": False, 
                "error": "No audio file provided"
            }), 400
        
        audio_file = request.files['audio']
        feature_type = request.form.get('feature_type', 'voice_chat')
        
        # Validate audio
        validation = audio_processor.validate_audio_file(
            audio_file, feature_type=feature_type
        )
        
        return jsonify({
            "success": validation["valid"],
            "validation": validation
        })
        
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return jsonify({
            "success": False, 
            "error": "Validation failed"
        }), 500

@voice_bp.route('/audio/analyze', methods=['POST'])
def analyze_audio():
    """Analyze audio quality"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                "success": False, 
                "error": "No audio file provided"
            }), 400
        
        audio_file = request.files['audio']
        
        # Analyze quality
        analysis = audio_processor.analyze_audio_quality(audio_file)
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Audio analysis error: {e}")
        return jsonify({
            "success": False, 
            "error": "Analysis failed"
        }), 500