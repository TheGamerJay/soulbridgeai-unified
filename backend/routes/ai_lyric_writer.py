"""
AI Lyric Writer API Routes
RESTful endpoints for advanced lyric generation with consent management
"""

import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
import traceback

from services.lyric_writer import (
    AILyricWriter, ConsentRecord, create_lyric_writer_service
)
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan, deduct_usage
from flask import render_template

logger = logging.getLogger(__name__)

# Create blueprint
ai_lyric_writer_bp = Blueprint('ai_lyric_writer', __name__, url_prefix='/api/ai-lyrics')

# Add route for serving the interface
@ai_lyric_writer_bp.route('/interface', methods=['GET'])
@require_auth
def ai_lyric_interface():
    """Serve the AI Lyric Writer interface"""
    return render_template('ai_lyric_writer.html')

# Initialize service
try:
    lyric_writer_service = create_lyric_writer_service()
    logger.info("✅ AI Lyric Writer service loaded")
except Exception as e:
    logger.error(f"❌ Failed to load AI Lyric Writer service: {e}")
    lyric_writer_service = None

@ai_lyric_writer_bp.route('/generate', methods=['POST'])
@require_auth
@rate_limit_moderate()
def generate_lyrics():
    """Generate AI lyrics with consent and similarity checks"""
    
    if not lyric_writer_service:
        return jsonify({
            'success': False,
            'error': 'AI Lyric Writer service unavailable'
        }), 503
    
    try:
        # Get user info
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        prompt = data.get('prompt', '').strip()
        genre = data.get('genre', 'pop').lower()
        mood = data.get('mood', 'neutral').lower()
        language = data.get('language', 'en').lower()
        check_similarity = data.get('check_similarity', True)
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt is required'
            }), 400
        
        if len(prompt) > 500:
            return jsonify({
                'success': False,
                'error': 'Prompt too long (max 500 characters)'
            }), 400
        
        # Check usage limits based on plan
        usage_limits = {
            'bronze': 5,  # 5 lyric generations per day
            'silver': 20,  # 20 per day
            'gold': -1  # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 5)
        
        if daily_limit != -1:  # Not unlimited
            current_usage = get_daily_usage(user_id, 'ai_lyrics')
            if current_usage >= daily_limit:
                return jsonify({
                    'success': False,
                    'error': f'Daily limit reached ({daily_limit} generations per day for {user_plan} tier)',
                    'upgrade_required': user_plan == 'bronze'
                }), 429
        
        # Generate lyrics
        result = lyric_writer_service.generate_lyrics(
            prompt=prompt,
            genre=genre,
            mood=mood,
            language=language,
            user_id=user_id,
            check_similarity=check_similarity
        )
        
        if result['success']:
            # Deduct usage
            if daily_limit != -1:
                deduct_usage(user_id, 'ai_lyrics', 1)
            
            logger.info(f"✅ Generated lyrics for user {user_id}, genre: {genre}, mood: {mood}")
            
            return jsonify({
                'success': True,
                'lyric_id': result['lyric_id'],
                'lyrics': result['lyrics'],
                'metadata': result['metadata'],
                'remaining_usage': max(0, daily_limit - current_usage - 1) if daily_limit != -1 else -1
            })
        
        else:
            logger.warning(f"❌ Lyric generation failed for user {user_id}: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Error in generate_lyrics: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_lyric_writer_bp.route('/check-similarity', methods=['POST'])
@require_auth
@rate_limit_moderate()
def check_similarity():
    """Check similarity against existing lyrics"""
    
    if not lyric_writer_service:
        return jsonify({
            'success': False,
            'error': 'AI Lyric Writer service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        query_text = data.get('text', '').strip()
        threshold = data.get('threshold', 0.85)
        limit = data.get('limit', 10)
        
        if not query_text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        # Validate threshold
        if not (0.0 <= threshold <= 1.0):
            return jsonify({
                'success': False,
                'error': 'Threshold must be between 0.0 and 1.0'
            }), 400
        
        # Find similar lyrics
        similar_lyrics = lyric_writer_service.lyric_db.find_similar_lyrics(
            query_text, threshold, limit
        )
        
        # Format results
        results = []
        for lyric_data, similarity_score in similar_lyrics:
            results.append({
                'lyric_id': lyric_data.lyric_id,
                'title': lyric_data.title,
                'artist_id': lyric_data.artist_id,
                'genre': lyric_data.genre,
                'mood': lyric_data.mood,
                'similarity_score': round(similarity_score, 3),
                'consent_status': lyric_data.consent_status,
                'preview': lyric_data.lyrics[:100] + "..." if len(lyric_data.lyrics) > 100 else lyric_data.lyrics
            })
        
        return jsonify({
            'success': True,
            'similar_count': len(results),
            'threshold_used': threshold,
            'similar_lyrics': results
        })
        
    except Exception as e:
        logger.error(f"❌ Error in check_similarity: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_lyric_writer_bp.route('/consent', methods=['POST'])
@require_auth
@rate_limit_moderate()
def manage_consent():
    """Manage artist consent for AI training"""
    
    if not lyric_writer_service:
        return jsonify({
            'success': False,
            'error': 'AI Lyric Writer service unavailable'
        }), 503
    
    try:
        # Only allow admins or verified artists to manage consent
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # For now, only Gold tier can manage consent
        if user_plan != 'gold':
            return jsonify({
                'success': False,
                'error': 'Gold tier required for consent management'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        artist_id = data.get('artist_id', '').strip()
        artist_name = data.get('artist_name', '').strip()
        consent_given = data.get('consent_given', False)
        training_allowed = data.get('training_allowed', False)
        commercial_use = data.get('commercial_use', False)
        attribution_required = data.get('attribution_required', True)
        restrictions = data.get('restrictions', {})
        consent_expires_str = data.get('consent_expires')
        
        if not artist_id or not artist_name:
            return jsonify({
                'success': False,
                'error': 'Artist ID and name are required'
            }), 400
        
        consent_expires = None
        if consent_expires_str:
            try:
                consent_expires = datetime.fromisoformat(consent_expires_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid consent expiration date format'
                }), 400
        
        # Create consent record
        consent_record = ConsentRecord(
            artist_id=artist_id,
            artist_name=artist_name,
            consent_given=consent_given,
            consent_date=datetime.now(timezone.utc),
            consent_expires=consent_expires,
            training_allowed=training_allowed,
            commercial_use=commercial_use,
            attribution_required=attribution_required,
            restrictions=restrictions
        )
        
        # Record consent
        success = lyric_writer_service.consent_manager.record_consent(consent_record)
        
        if success:
            logger.info(f"✅ Consent recorded for artist {artist_name} by user {user_id}")
            return jsonify({
                'success': True,
                'message': f'Consent recorded for {artist_name}',
                'consent_record': consent_record.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to record consent'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in manage_consent: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_lyric_writer_bp.route('/consent/<artist_id>', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_consent(artist_id):
    """Get consent status for an artist"""
    
    if not lyric_writer_service:
        return jsonify({
            'success': False,
            'error': 'AI Lyric Writer service unavailable'
        }), 503
    
    try:
        consent_record = lyric_writer_service.consent_manager.get_consent(artist_id)
        
        if not consent_record:
            return jsonify({
                'success': False,
                'error': 'No consent record found'
            }), 404
        
        return jsonify({
            'success': True,
            'consent_record': consent_record.to_dict()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_consent: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_lyric_writer_bp.route('/compliance-check', methods=['POST'])
@require_auth
@rate_limit_moderate()
def check_compliance():
    """Check consent compliance for a specific use case"""
    
    if not lyric_writer_service:
        return jsonify({
            'success': False,
            'error': 'AI Lyric Writer service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        artist_id = data.get('artist_id', '').strip()
        use_case = data.get('use_case', 'generation').lower()
        
        if not artist_id:
            return jsonify({
                'success': False,
                'error': 'Artist ID is required'
            }), 400
        
        if use_case not in ['training', 'generation', 'commercial']:
            return jsonify({
                'success': False,
                'error': 'Invalid use case. Must be: training, generation, or commercial'
            }), 400
        
        compliance_result = lyric_writer_service.check_consent_compliance(artist_id, use_case)
        
        return jsonify({
            'success': True,
            'artist_id': artist_id,
            'use_case': use_case,
            'compliance': compliance_result
        })
        
    except Exception as e:
        logger.error(f"❌ Error in check_compliance: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_lyric_writer_bp.route('/stats', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_stats():
    """Get AI lyric writer statistics"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Usage limits by plan
        usage_limits = {
            'bronze': 5,
            'silver': 20, 
            'gold': -1  # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 5)
        current_usage = get_daily_usage(user_id, 'ai_lyrics')
        
        stats = {
            'user_plan': user_plan,
            'daily_limit': daily_limit,
            'current_usage': current_usage,
            'remaining_usage': max(0, daily_limit - current_usage) if daily_limit != -1 else -1,
            'features': {
                'similarity_check': True,
                'consent_management': user_plan == 'gold',
                'commercial_use': user_plan in ['silver', 'gold'],
                'unlimited_generation': user_plan == 'gold'
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_stats: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def get_daily_usage(user_id: str, feature: str) -> int:
    """Get daily usage count for a feature"""
    try:
        # This would integrate with your usage tracking system
        # For now, return 0 as placeholder
        return 0
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        return 0