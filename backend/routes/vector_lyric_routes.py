"""
Vector Lyric API Routes
API endpoints for vector-based lyric similarity search and management
"""

import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
import traceback
import json

from services.vector_lyric_service import create_vector_lyric_service
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan

logger = logging.getLogger(__name__)

# Create blueprint
vector_lyric_bp = Blueprint('vector_lyric', __name__, url_prefix='/api/vector-lyrics')

# Initialize service
try:
    vector_service = create_vector_lyric_service()
    logger.info("✅ Vector lyric service loaded")
except Exception as e:
    logger.error(f"❌ Failed to load vector lyric service: {e}")
    vector_service = None

@vector_lyric_bp.route('/health', methods=['GET'])
def health_check():
    """Check health of vector lyric service"""
    try:
        if not vector_service:
            return jsonify({
                'success': False,
                'error': 'Vector lyric service unavailable'
            }), 503
        
        health = vector_service.health_check()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'vector-lyric-service',
            'health': health
        })
        
    except Exception as e:
        logger.error(f"❌ Health check error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Health check failed'
        }), 500

@vector_lyric_bp.route('/search', methods=['POST'])
@require_auth
@rate_limit_moderate
def search_similar_lyrics():
    """Search for similar lyrics using vector similarity"""
    
    if not vector_service:
        return jsonify({
            'success': False,
            'error': 'Vector lyric service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        query_text = data.get('query_text', '').strip()
        if not query_text:
            return jsonify({
                'success': False,
                'error': 'Query text is required'
            }), 400
        
        # Get search parameters
        similarity_threshold = data.get('similarity_threshold', 0.7)
        max_results = data.get('max_results', 10)
        genre_filter = data.get('genre_filter')
        mood_filter = data.get('mood_filter')
        
        # Tier-based limitations
        if user_plan == 'bronze':
            max_results = min(max_results, 5)
            similarity_threshold = max(similarity_threshold, 0.8)  # Higher threshold = fewer results
        elif user_plan == 'silver':
            max_results = min(max_results, 15)
            similarity_threshold = max(similarity_threshold, 0.6)
        # Gold tier has no restrictions
        
        # Search for similar lyrics
        similar_lyrics = vector_service.find_similar_lyrics(
            query_text=query_text,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            genre_filter=genre_filter,
            mood_filter=mood_filter
        )
        
        logger.info(f"✅ Vector search for user {user_id}: {len(similar_lyrics)} results")
        
        return jsonify({
            'success': True,
            'query_text': query_text,
            'results': similar_lyrics,
            'count': len(similar_lyrics),
            'search_params': {
                'similarity_threshold': similarity_threshold,
                'max_results': max_results,
                'genre_filter': genre_filter,
                'mood_filter': mood_filter
            },
            'user_tier_limits': {
                'plan': user_plan,
                'max_results_allowed': max_results,
                'min_similarity_threshold': similarity_threshold
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Vector search error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500

@vector_lyric_bp.route('/store', methods=['POST'])
@require_auth
@rate_limit_moderate
def store_lyric_embedding():
    """Store a lyric with its embedding (Gold tier only)"""
    
    if not vector_service:
        return jsonify({
            'success': False,
            'error': 'Vector lyric service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Only Gold tier can store lyrics
        if user_plan != 'gold':
            return jsonify({
                'success': False,
                'error': 'Lyric storage is available for Gold tier only',
                'upgrade_required': True
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['lyric_id', 'artist_id', 'title', 'lyrics']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Field {field} is required'
                }), 400
        
        # Store lyric embedding
        success = vector_service.store_lyric_embedding(
            lyric_id=data['lyric_id'],
            artist_id=data['artist_id'],
            title=data['title'],
            lyrics=data['lyrics'],
            genre=data.get('genre', 'unknown'),
            mood=data.get('mood', 'neutral'),
            language=data.get('language', 'en')
        )
        
        if success:
            logger.info(f"✅ Stored lyric embedding for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Lyric embedding stored successfully',
                'lyric_id': data['lyric_id']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to store lyric embedding'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Store lyric error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Storage failed'
        }), 500

@vector_lyric_bp.route('/consent/<artist_id>', methods=['GET'])
@require_auth
@rate_limit_moderate
def get_artist_consent(artist_id):
    """Get artist consent information"""
    
    if not vector_service:
        return jsonify({
            'success': False,
            'error': 'Vector lyric service unavailable'
        }), 503
    
    try:
        consent_info = vector_service.get_artist_consent(artist_id)
        
        if consent_info:
            return jsonify({
                'success': True,
                'artist_id': artist_id,
                'consent': consent_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Artist consent record not found'
            }), 404
        
    except Exception as e:
        logger.error(f"❌ Get consent error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get consent information'
        }), 500

@vector_lyric_bp.route('/consent', methods=['POST'])
@require_auth
@rate_limit_moderate
def update_artist_consent():
    """Update artist consent (Admin only)"""
    
    if not vector_service:
        return jsonify({
            'success': False,
            'error': 'Vector lyric service unavailable'
        }), 503
    
    try:
        # Check if user is admin (simplified check)
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # For now, only Gold tier can manage consent
        if user_plan != 'gold':
            return jsonify({
                'success': False,
                'error': 'Consent management requires Gold tier',
                'upgrade_required': True
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        if not data.get('artist_id') or not data.get('artist_name'):
            return jsonify({
                'success': False,
                'error': 'artist_id and artist_name are required'
            }), 400
        
        # Update consent
        success = vector_service.update_artist_consent(
            artist_id=data['artist_id'],
            artist_name=data['artist_name'],
            consent_given=data.get('consent_given', False),
            training_allowed=data.get('training_allowed', False),
            commercial_use=data.get('commercial_use', False),
            attribution_required=data.get('attribution_required', True),
            restrictions=data.get('restrictions', {})
        )
        
        if success:
            logger.info(f"✅ Updated consent for artist {data['artist_id']}")
            return jsonify({
                'success': True,
                'message': 'Artist consent updated successfully',
                'artist_id': data['artist_id']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update artist consent'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Update consent error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Consent update failed'
        }), 500

@vector_lyric_bp.route('/statistics', methods=['GET'])
@require_auth
@rate_limit_moderate
def get_lyric_statistics():
    """Get statistics about stored lyrics and embeddings"""
    
    if not vector_service:
        return jsonify({
            'success': False,
            'error': 'Vector lyric service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Only Silver and Gold can see statistics
        if user_plan == 'bronze':
            return jsonify({
                'success': False,
                'error': 'Statistics require Silver or Gold tier',
                'upgrade_required': True
            }), 403
        
        stats = vector_service.get_lyric_statistics()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Statistics error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500

@vector_lyric_bp.route('/features', methods=['GET'])
@require_auth
def get_vector_features():
    """Get available vector features for user's tier"""
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        features = {
            'bronze': {
                'search_enabled': True,
                'max_search_results': 5,
                'min_similarity_threshold': 0.8,
                'storage_enabled': False,
                'consent_management': False,
                'statistics_enabled': False
            },
            'silver': {
                'search_enabled': True,
                'max_search_results': 15,
                'min_similarity_threshold': 0.6,
                'storage_enabled': False,
                'consent_management': False,
                'statistics_enabled': True
            },
            'gold': {
                'search_enabled': True,
                'max_search_results': 50,
                'min_similarity_threshold': 0.3,
                'storage_enabled': True,
                'consent_management': True,
                'statistics_enabled': True
            }
        }
        
        user_features = features.get(user_plan, features['bronze'])
        
        return jsonify({
            'success': True,
            'user_plan': user_plan,
            'features': user_features,
            'service_available': vector_service is not None
        })
        
    except Exception as e:
        logger.error(f"❌ Features error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Failed to get features'
        }), 500