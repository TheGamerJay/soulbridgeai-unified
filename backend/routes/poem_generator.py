"""
Poem Generator API Routes
RESTful endpoints for comprehensive poetry generation
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime, timezone
import traceback
from typing import List

from services.poem_generator import (
    PoemGenerator, PoemType, create_poem_generator_service
)
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan, deduct_usage
from consent import user_has_consent

logger = logging.getLogger(__name__)

# Create blueprint
poem_generator_bp = Blueprint('poem_generator', __name__, url_prefix='/api/poems')

# Add route for serving the interface
@poem_generator_bp.route('/interface', methods=['GET'])
@require_auth
def poem_interface():
    """Serve the Poem Generator interface"""
    return render_template('poem_generator.html')

# Initialize service
try:
    poem_generator_service = create_poem_generator_service()
    logger.info("✅ Poem Generator service loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Poem Generator service: {e}")
    poem_generator_service = None

@poem_generator_bp.route('/generate', methods=['POST'])
@require_auth
@rate_limit_moderate
def generate_poem():
    """Generate a poem of the specified type"""
    
    if not poem_generator_service:
        return jsonify({
            'success': False,
            'error': 'Poem Generator service unavailable'
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
        
        poem_type_str = data.get('poem_type', '').lower()
        theme = data.get('theme', '').strip()
        mood = data.get('mood', 'neutral').lower()
        language = data.get('language', 'en').lower()
        custom_word = data.get('custom_word', '').strip()  # For acrostics
        
        if not poem_type_str or not theme:
            return jsonify({
                'success': False,
                'error': 'Poem type and theme are required'
            }), 400
        
        # Convert poem type
        try:
            poem_type = PoemType(poem_type_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid poem type: {poem_type_str}',
                'available_types': [pt.value for pt in PoemType]
            }), 400
        
        # Validate acrostic word
        if poem_type == PoemType.ACROSTIC and not custom_word:
            return jsonify({
                'success': False,
                'error': 'Acrostic poems require a custom word'
            }), 400
        
        if len(theme) > 100:
            return jsonify({
                'success': False,
                'error': 'Theme too long (max 100 characters)'
            }), 400
        
        # Check usage limits based on plan
        usage_limits = {
            'bronze': 3,  # 3 poem generations per day
            'silver': 15,  # 15 per day
            'gold': -1  # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 3)
        
        if daily_limit != -1:  # Not unlimited
            current_usage = get_daily_usage(user_id, 'poems')
            if current_usage >= daily_limit:
                return jsonify({
                    'success': False,
                    'error': f'Daily limit reached ({daily_limit} poems per day for {user_plan} tier)',
                    'upgrade_required': user_plan == 'bronze'
                }), 429
        
        # Check if user wants their prompt/result saved for training
        contribute_to_training = user_has_consent(user_id, "poems")
        
        # Generate poem
        result = poem_generator_service.generate_poem(
            poem_type=poem_type,
            theme=theme,
            mood=mood,
            language=language,
            user_id=user_id,
            custom_word=custom_word if poem_type == PoemType.ACROSTIC else None,
            contribute=contribute_to_training  # Pass consent flag
        )
        
        if result['success']:
            # Deduct usage
            if daily_limit != -1:
                deduct_usage(user_id, 'poems', 1)
            
            logger.info(f"✅ Generated {poem_type.value} for user {user_id}, theme: {theme}, contribute: {contribute_to_training}")
            
            return jsonify({
                'success': True,
                'poem': result['poem'],
                'validation': result['validation'],
                'remaining_usage': max(0, daily_limit - current_usage - 1) if daily_limit != -1 else -1,
                'contribute_status': contribute_to_training
            })
        
        else:
            logger.warning(f"❌ Poem generation failed for user {user_id}: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Error in generate_poem: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@poem_generator_bp.route('/validate', methods=['POST'])
@require_auth
@rate_limit_moderate
def validate_poem():
    """Validate a poem against its structure requirements"""
    
    if not poem_generator_service:
        return jsonify({
            'success': False,
            'error': 'Poem Generator service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        poem_type_str = data.get('poem_type', '').lower()
        content = data.get('content', '').strip()
        
        if not poem_type_str or not content:
            return jsonify({
                'success': False,
                'error': 'Poem type and content are required'
            }), 400
        
        # Convert poem type
        try:
            poem_type = PoemType(poem_type_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid poem type: {poem_type_str}',
                'available_types': [pt.value for pt in PoemType]
            }), 400
        
        # Validate the poem
        validation = poem_generator_service.structure_manager.validate_poem(poem_type, content)
        
        return jsonify({
            'success': True,
            'poem_type': poem_type.value,
            'validation': validation
        })
        
    except Exception as e:
        logger.error(f"❌ Error in validate_poem: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@poem_generator_bp.route('/types', methods=['GET'])
@require_auth
def get_poem_types():
    """Get available poem types and their structures"""
    
    if not poem_generator_service:
        return jsonify({
            'success': False,
            'error': 'Poem Generator service unavailable'
        }), 503
    
    try:
        poem_types = []
        
        for poem_type in PoemType:
            structure = poem_generator_service.structure_manager.get_structure(poem_type)
            
            poem_types.append({
                'type': poem_type.value,
                'name': poem_type.value.replace('_', ' ').title(),
                'lines': structure.lines if structure.lines > 0 else 'Variable',
                'syllable_pattern': structure.syllable_pattern,
                'rhyme_scheme': structure.rhyme_scheme.value if structure.rhyme_scheme else None,
                'description': get_poem_description(poem_type),
                'difficulty': get_poem_difficulty(poem_type),
                'special_rules': list(structure.special_rules.keys()) if structure.special_rules else []
            })
        
        return jsonify({
            'success': True,
            'poem_types': poem_types
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_poem_types: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@poem_generator_bp.route('/user-poems', methods=['GET'])
@require_auth
@rate_limit_moderate
def get_user_poems():
    """Get user's generated poems"""
    
    if not poem_generator_service:
        return jsonify({
            'success': False,
            'error': 'Poem Generator service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        poem_type_str = request.args.get('type', '').lower()
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        
        poem_type = None
        if poem_type_str:
            try:
                poem_type = PoemType(poem_type_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid poem type: {poem_type_str}'
                }), 400
        
        poems = poem_generator_service.get_user_poems(user_id, poem_type, limit)
        
        return jsonify({
            'success': True,
            'poems': poems,
            'count': len(poems),
            'filter_type': poem_type.value if poem_type else 'all'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_poems: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@poem_generator_bp.route('/stats', methods=['GET'])
@require_auth
@rate_limit_moderate
def get_stats():
    """Get poem generator statistics"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Usage limits by plan
        usage_limits = {
            'bronze': 3,
            'silver': 15, 
            'gold': -1  # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 3)
        current_usage = get_daily_usage(user_id, 'poems')
        
        stats = {
            'user_plan': user_plan,
            'daily_limit': daily_limit,
            'current_usage': current_usage,
            'remaining_usage': max(0, daily_limit - current_usage) if daily_limit != -1 else -1,
            'features': {
                'all_poem_types': True,
                'validation': True,
                'structure_analysis': True,
                'syllable_counting': True,
                'rhyme_analysis': True,
                'unlimited_generation': user_plan == 'gold'
            },
            'available_types': [pt.value for pt in PoemType]
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

@poem_generator_bp.route('/analyze', methods=['POST'])
@require_auth
@rate_limit_moderate
def analyze_poem():
    """Analyze a poem's structure, syllables, and rhyme scheme"""
    
    if not poem_generator_service:
        return jsonify({
            'success': False,
            'error': 'Poem Generator service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required for analysis'
            }), 400
        
        lines = content.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines
        
        # Analyze syllables
        syllable_counts = []
        for line in lines:
            count = poem_generator_service.syllable_counter.count_line_syllables(line)
            syllable_counts.append(count)
        
        # Analyze rhyme scheme
        rhyme_analysis = poem_generator_service.rhyme_analyzer.analyze_rhyme_scheme(lines)
        
        # Try to identify poem type based on structure
        identified_types = []
        for poem_type in PoemType:
            structure = poem_generator_service.structure_manager.get_structure(poem_type)
            
            # Check if it matches this type
            matches = True
            confidence = 1.0
            
            if structure.lines > 0 and len(lines) != structure.lines:
                matches = False
            elif structure.syllable_pattern:
                # Check syllable pattern similarity
                if len(syllable_counts) == len(structure.syllable_pattern):
                    differences = sum(abs(a - e) for a, e in zip(syllable_counts, structure.syllable_pattern))
                    total_expected = sum(structure.syllable_pattern)
                    confidence = max(0.0, 1.0 - (differences / total_expected))
                    if confidence < 0.7:
                        matches = False
                else:
                    matches = False
            
            if matches:
                identified_types.append({
                    'type': poem_type.value,
                    'confidence': round(confidence, 3)
                })
        
        # Sort by confidence
        identified_types.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
            'success': True,
            'analysis': {
                'line_count': len(lines),
                'syllable_counts': syllable_counts,
                'total_syllables': sum(syllable_counts),
                'average_syllables': round(sum(syllable_counts) / len(syllable_counts), 2) if syllable_counts else 0,
                'rhyme_analysis': rhyme_analysis,
                'identified_types': identified_types[:3],  # Top 3 matches
                'structure_summary': {
                    'is_structured': len(set(syllable_counts)) <= 3,  # Low variation suggests structure
                    'has_rhyme': rhyme_analysis['quality_score'] > 0.3,
                    'regularity_score': calculate_regularity_score(syllable_counts)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_poem: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

def get_poem_description(poem_type: PoemType) -> str:
    """Get description for poem type"""
    descriptions = {
        PoemType.HAIKU: "Traditional Japanese form with 5-7-5 syllable pattern, focusing on nature and present moment",
        PoemType.SONNET: "14-line poem with strict rhyme scheme, traditionally about love or philosophical themes",
        PoemType.FREE_VERSE: "Poetry without regular meter, rhyme, or structure, focusing on natural speech patterns",
        PoemType.ACROSTIC: "Poem where first letters of each line spell out a word or phrase",
        PoemType.LIMERICK: "Humorous 5-line poem with AABBA rhyme scheme and bouncy rhythm",
        PoemType.TANKA: "Japanese form with 5-7-5-7-7 syllable pattern, often about nature or emotions",
        PoemType.CINQUAIN: "5-line poem with 2-4-6-8-2 syllable pattern creating a diamond shape",
        PoemType.VILLANELLE: "19-line poem with complex repetition pattern and only two rhyme sounds"
    }
    return descriptions.get(poem_type, "Poetry form")

def get_poem_difficulty(poem_type: PoemType) -> str:
    """Get difficulty level for poem type"""
    difficulties = {
        PoemType.HAIKU: "Beginner",
        PoemType.FREE_VERSE: "Beginner",
        PoemType.ACROSTIC: "Beginner",
        PoemType.CINQUAIN: "Intermediate",
        PoemType.LIMERICK: "Intermediate",
        PoemType.TANKA: "Intermediate",
        PoemType.SONNET: "Advanced",
        PoemType.VILLANELLE: "Expert"
    }
    return difficulties.get(poem_type, "Intermediate")

def calculate_regularity_score(syllable_counts: List[int]) -> float:
    """Calculate how regular the syllable pattern is"""
    if not syllable_counts:
        return 0.0
    
    # Check for repeated patterns
    unique_counts = len(set(syllable_counts))
    total_lines = len(syllable_counts)
    
    # More unique patterns = less regular
    regularity = 1.0 - (unique_counts / total_lines)
    return round(regularity, 3)

def get_daily_usage(user_id: str, feature: str) -> int:
    """Get daily usage count for a feature"""
    try:
        # This would integrate with your usage tracking system
        # For now, return 0 as placeholder
        return 0
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        return 0