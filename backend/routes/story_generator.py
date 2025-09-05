"""
Story Generator API Routes
RESTful endpoints for comprehensive story generation and analysis
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime, timezone
import traceback
import json
from typing import List

from services.story_generator import (
    StoryGenerator, StoryGenre, StoryLength, NarrativeStructure,
    create_story_generator_service
)
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan, deduct_usage

logger = logging.getLogger(__name__)

# Create blueprint
story_generator_bp = Blueprint('story_generator', __name__, url_prefix='/api/stories')

# Add route for serving the interface
@story_generator_bp.route('/interface', methods=['GET'])
@require_auth
def story_interface():
    """Serve the Story Generator interface"""
    return render_template('story_generator.html')

# Initialize service
try:
    story_generator_service = create_story_generator_service()
    logger.info("✅ Story Generator service loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Story Generator service: {e}")
    story_generator_service = None

@story_generator_bp.route('/generate-outline', methods=['POST'])
@require_auth
@rate_limit_moderate()
def generate_outline():
    """Generate a comprehensive story outline"""
    
    if not story_generator_service:
        return jsonify({
            'success': False,
            'error': 'Story Generator service unavailable'
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
        
        genre_str = data.get('genre', '').lower()
        length_str = data.get('length', '').lower()
        premise = data.get('premise', '').strip()
        themes = data.get('themes', [])
        structure_str = data.get('structure', 'three_act').lower()
        character_count = int(data.get('character_count', 3))
        
        if not genre_str or not length_str or not premise:
            return jsonify({
                'success': False,
                'error': 'Genre, length, and premise are required'
            }), 400
        
        # Validate inputs
        try:
            genre = StoryGenre(genre_str)
            length = StoryLength(length_str)
            structure = NarrativeStructure(structure_str)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid parameter: {str(e)}',
                'available_genres': [g.value for g in StoryGenre],
                'available_lengths': [l.value for l in StoryLength],
                'available_structures': [s.value for s in NarrativeStructure]
            }), 400
        
        if len(premise) > 500:
            return jsonify({
                'success': False,
                'error': 'Premise too long (max 500 characters)'
            }), 400
        
        if character_count < 1 or character_count > 8:
            return jsonify({
                'success': False,
                'error': 'Character count must be between 1 and 8'
            }), 400
        
        # Check usage limits
        usage_limits = {
            'bronze': 2,  # 2 story outlines per day
            'silver': 10, # 10 per day
            'gold': -1    # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 2)
        
        if daily_limit != -1:
            current_usage = get_daily_usage(user_id, 'story_outlines')
            if current_usage >= daily_limit:
                return jsonify({
                    'success': False,
                    'error': f'Daily limit reached ({daily_limit} story outlines per day for {user_plan} tier)',
                    'upgrade_required': user_plan == 'bronze'
                }), 429
        
        # Generate outline
        outline = story_generator_service.generate_outline(
            genre=genre,
            length=length,
            premise=premise,
            themes=themes,
            structure_type=structure,
            character_count=character_count
        )
        
        # Save outline
        outline_id = story_generator_service.database.save_outline(user_id, outline)
        
        # Deduct usage
        if daily_limit != -1:
            deduct_usage(user_id, 'story_outlines', 1)
        
        logger.info(f"✅ Generated {genre.value} {length.value} outline for user {user_id}")
        
        # Convert outline to dict for JSON response
        outline_dict = {
            'id': outline_id,
            'title': outline.title,
            'genre': outline.genre.value,
            'length': outline.length.value,
            'premise': outline.premise,
            'characters': [
                {
                    'name': char.name,
                    'role': char.role,
                    'archetype': char.archetype,
                    'motivation': char.motivation,
                    'conflict': char.conflict,
                    'traits': char.traits,
                    'age': char.age,
                    'occupation': char.occupation
                } for char in outline.characters
            ],
            'structure': {
                'type': outline.structure.structure_type.value,
                'plot_points': [
                    {
                        'name': pp.name,
                        'description': pp.description,
                        'chapter': pp.chapter,
                        'position': pp.word_position,
                        'characters': pp.character_focus,
                        'conflict_type': pp.conflict_type
                    } for pp in outline.structure.plot_points
                ],
                'themes': outline.structure.themes,
                'subplots': outline.structure.subplots
            },
            'chapters': outline.chapters,
            'word_count_target': outline.word_count_target,
            'themes': outline.themes,
            'target_audience': outline.target_audience,
            'setting': outline.setting
        }
        
        return jsonify({
            'success': True,
            'outline': outline_dict,
            'remaining_usage': max(0, daily_limit - current_usage - 1) if daily_limit != -1 else -1
        })
        
    except Exception as e:
        logger.error(f"❌ Error in generate_outline: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@story_generator_bp.route('/generate-content', methods=['POST'])
@require_auth
@rate_limit_moderate()
def generate_content():
    """Generate story content from outline"""
    
    if not story_generator_service:
        return jsonify({
            'success': False,
            'error': 'Story Generator service unavailable'
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
        
        outline_data = data.get('outline')
        chapter_number = data.get('chapter_number')  # Optional
        
        if not outline_data:
            return jsonify({
                'success': False,
                'error': 'Story outline is required'
            }), 400
        
        # Check usage limits for content generation
        usage_limits = {
            'bronze': 1,   # 1 story generation per day
            'silver': 5,   # 5 per day
            'gold': -1     # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 1)
        
        if daily_limit != -1:
            current_usage = get_daily_usage(user_id, 'story_content')
            if current_usage >= daily_limit:
                return jsonify({
                    'success': False,
                    'error': f'Daily limit reached ({daily_limit} story generations per day for {user_plan} tier)',
                    'upgrade_required': user_plan == 'bronze'
                }), 429
        
        # Reconstruct outline object from JSON
        # This is a simplified reconstruction - in production you might want to store/retrieve from DB
        outline = story_generator_service._reconstruct_outline_from_dict(outline_data)
        
        # Generate content
        content = story_generator_service.generate_story_content(outline, chapter_number)
        
        # If generating full story, save it
        if not chapter_number:
            story_id = story_generator_service.save_story(
                user_id=user_id,
                title=outline.title,
                genre=outline.genre,
                length_type=outline.length,
                content=content,
                outline=outline
            )
            
            # Deduct usage
            if daily_limit != -1:
                deduct_usage(user_id, 'story_content', 1)
            
            logger.info(f"✅ Generated full story content for user {user_id}: {outline.title}")
            
            return jsonify({
                'success': True,
                'story_id': story_id,
                'content': content,
                'word_count': len(content.split()),
                'remaining_usage': max(0, daily_limit - current_usage - 1) if daily_limit != -1 else -1
            })
        else:
            # Just return chapter content without saving
            return jsonify({
                'success': True,
                'chapter': chapter_number,
                'content': content,
                'word_count': len(content.split())
            })
        
    except Exception as e:
        logger.error(f"❌ Error in generate_content: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@story_generator_bp.route('/analyze', methods=['POST'])
@require_auth
@rate_limit_moderate()
def analyze_story():
    """Analyze story content for structure, pacing, and style"""
    
    if not story_generator_service:
        return jsonify({
            'success': False,
            'error': 'Story Generator service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        content = data.get('content', '').strip()
        title = data.get('title', '').strip()
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required for analysis'
            }), 400
        
        if len(content) > 100000:  # Limit analysis to reasonable size
            return jsonify({
                'success': False,
                'error': 'Content too long for analysis (max 100,000 characters)'
            }), 400
        
        # Perform analysis
        analysis = story_generator_service.analyze_story(content, title)
        
        # Convert analysis to dict
        analysis_dict = {
            'word_count': analysis.word_count,
            'sentence_count': analysis.sentence_count,
            'paragraph_count': analysis.paragraph_count,
            'avg_sentence_length': analysis.avg_sentence_length,
            'readability_score': analysis.readability_score,
            'point_of_view': analysis.pov,
            'tense': analysis.tense,
            'dialogue_percentage': analysis.dialogue_percentage,
            'character_mentions': analysis.character_mentions,
            'identified_themes': analysis.theme_indicators,
            'plot_structure': analysis.plot_structure_analysis,
            'pacing_analysis': analysis.pacing_analysis,
            'conflict_types': analysis.conflict_types,
            'recommendations': generate_writing_recommendations(analysis)
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis_dict
        })
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_story: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@story_generator_bp.route('/user-stories', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_user_stories():
    """Get user's generated stories"""
    
    if not story_generator_service:
        return jsonify({
            'success': False,
            'error': 'Story Generator service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        genre_str = request.args.get('genre', '').lower()
        limit = min(int(request.args.get('limit', 20)), 50)
        
        genre = None
        if genre_str:
            try:
                genre = StoryGenre(genre_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid genre: {genre_str}'
                }), 400
        
        stories = story_generator_service.get_user_stories(user_id, genre, limit)
        
        return jsonify({
            'success': True,
            'stories': stories,
            'count': len(stories),
            'filter_genre': genre.value if genre else 'all'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_stories: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@story_generator_bp.route('/genres', methods=['GET'])
@require_auth
def get_genres():
    """Get available story genres and metadata"""
    
    try:
        genres = []
        
        genre_descriptions = {
            StoryGenre.FANTASY: "Magical worlds with mythical creatures, wizards, and epic quests",
            StoryGenre.SCI_FI: "Future technology, space exploration, and scientific speculation",
            StoryGenre.MYSTERY: "Puzzles to solve, clues to follow, and secrets to uncover",
            StoryGenre.ROMANCE: "Love stories focusing on relationships and emotional connections",
            StoryGenre.THRILLER: "Fast-paced suspense with danger and high stakes",
            StoryGenre.HORROR: "Frightening tales designed to create suspense and fear",
            StoryGenre.DRAMA: "Character-driven stories exploring human emotions and relationships",
            StoryGenre.COMEDY: "Humorous stories designed to entertain and amuse",
            StoryGenre.ADVENTURE: "Action-packed journeys and exciting escapades",
            StoryGenre.HISTORICAL: "Stories set in the past, exploring historical periods",
            StoryGenre.WESTERN: "Tales of the American Old West with cowboys and frontier life",
            StoryGenre.LITERARY: "Character and theme-focused literary fiction"
        }
        
        for genre in StoryGenre:
            genres.append({
                'value': genre.value,
                'name': genre.value.replace('_', ' ').title(),
                'description': genre_descriptions.get(genre, 'Story genre'),
                'popular': genre in [StoryGenre.FANTASY, StoryGenre.SCI_FI, StoryGenre.MYSTERY, StoryGenre.ROMANCE]
            })
        
        lengths = []
        length_descriptions = {
            StoryLength.FLASH_FICTION: "Very short stories (50-300 words)",
            StoryLength.SHORT_STORY: "Short stories (500-2,000 words)",
            StoryLength.NOVELETTE: "Medium-length stories (3,000-7,500 words)",
            StoryLength.NOVELLA: "Long stories (10,000-25,000 words)",
            StoryLength.NOVEL_OUTLINE: "Full novel outline (chapter-by-chapter structure)"
        }
        
        for length in StoryLength:
            lengths.append({
                'value': length.value,
                'name': length.value.replace('_', ' ').title(),
                'description': length_descriptions.get(length, 'Story length')
            })
        
        structures = []
        structure_descriptions = {
            NarrativeStructure.THREE_ACT: "Classic beginning, middle, and end structure",
            NarrativeStructure.HEROS_JOURNEY: "Joseph Campbell's monomyth structure",
            NarrativeStructure.FREYTAG_PYRAMID: "Five-part dramatic structure with climax at center",
            NarrativeStructure.SEVEN_POINT: "Seven key plot points for story development",
            NarrativeStructure.SAVE_THE_CAT: "Blake Snyder's screenplay structure adapted for prose",
            NarrativeStructure.FICHTEAN_CURVE: "Multiple rising crises leading to climax"
        }
        
        for structure in NarrativeStructure:
            structures.append({
                'value': structure.value,
                'name': structure.value.replace('_', ' ').title(),
                'description': structure_descriptions.get(structure, 'Story structure')
            })
        
        return jsonify({
            'success': True,
            'genres': genres,
            'lengths': lengths,
            'structures': structures
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_genres: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@story_generator_bp.route('/stats', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_stats():
    """Get story generator statistics and user limits"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Usage limits by plan
        usage_limits = {
            'bronze': {'outlines': 2, 'content': 1},
            'silver': {'outlines': 10, 'content': 5},
            'gold': {'outlines': -1, 'content': -1}
        }
        
        limits = usage_limits.get(user_plan, usage_limits['bronze'])
        
        outline_usage = get_daily_usage(user_id, 'story_outlines')
        content_usage = get_daily_usage(user_id, 'story_content')
        
        stats = {
            'user_plan': user_plan,
            'daily_limits': {
                'story_outlines': limits['outlines'],
                'story_content': limits['content']
            },
            'current_usage': {
                'story_outlines': outline_usage,
                'story_content': content_usage
            },
            'remaining_usage': {
                'story_outlines': max(0, limits['outlines'] - outline_usage) if limits['outlines'] != -1 else -1,
                'story_content': max(0, limits['content'] - content_usage) if limits['content'] != -1 else -1
            },
            'features': {
                'all_genres': True,
                'all_lengths': user_plan in ['silver', 'gold'],
                'advanced_analysis': user_plan == 'gold',
                'unlimited_outlines': user_plan == 'gold',
                'unlimited_content': user_plan == 'gold',
                'character_development': True,
                'plot_structure': True
            },
            'available_genres': len(StoryGenre),
            'available_structures': len(NarrativeStructure)
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

def generate_writing_recommendations(analysis) -> List[str]:
    """Generate writing improvement recommendations based on analysis"""
    recommendations = []
    
    # Sentence length recommendations
    if analysis.avg_sentence_length > 25:
        recommendations.append("Consider using shorter sentences for better readability")
    elif analysis.avg_sentence_length < 10:
        recommendations.append("Try varying sentence length for better flow")
    
    # Dialogue recommendations
    if analysis.dialogue_percentage < 10:
        recommendations.append("Adding dialogue could make your story more engaging")
    elif analysis.dialogue_percentage > 70:
        recommendations.append("Balance dialogue with narrative description")
    
    # Readability recommendations
    if analysis.readability_score < 30:
        recommendations.append("Story may be too complex - consider simplifying language")
    elif analysis.readability_score > 80:
        recommendations.append("Story reads well with good accessibility")
    
    # Structure recommendations
    if not analysis.plot_structure_analysis.get('resolution_present', False):
        recommendations.append("Consider adding a clearer resolution to your story")
    
    # Pacing recommendations
    if analysis.pacing_analysis.get('variance', 0) < 5:
        recommendations.append("Try varying sentence and paragraph lengths for better pacing")
    
    # Character recommendations
    char_count = len(analysis.character_mentions)
    if char_count < 2:
        recommendations.append("Consider adding more characters for richer storytelling")
    elif char_count > 8:
        recommendations.append("You have many characters - ensure each serves a purpose")
    
    return recommendations[:5]  # Limit to top 5 recommendations

def get_daily_usage(user_id: str, feature: str) -> int:
    """Get daily usage count for a feature"""
    try:
        # This would integrate with your usage tracking system
        # For now, return 0 as placeholder
        return 0
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        return 0