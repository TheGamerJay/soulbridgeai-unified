"""
Writing Suite API Routes
RESTful endpoints for comprehensive writing generation
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime, timezone
import traceback
import json

from services.writing_suite import (
    WritingSuite, WritingType, ToneStyle, WritingPrompt, 
    ScriptFormat, ArticleStructure, LetterFormat,
    create_writing_suite_service
)
from security_config import require_auth, rate_limit_moderate
from database import get_user_plan, deduct_usage
from consent import user_has_consent

logger = logging.getLogger(__name__)

# Create blueprint
writing_suite_bp = Blueprint('writing_suite', __name__, url_prefix='/api/writing')

# Add route for serving the interface
@writing_suite_bp.route('/interface', methods=['GET'])
@require_auth
def writing_interface():
    """Serve the Writing Suite interface"""
    return render_template('writing_suite.html')

# Initialize service
try:
    writing_suite_service = create_writing_suite_service()
    logger.info("✅ Writing Suite service loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Writing Suite service: {e}")
    writing_suite_service = None

@writing_suite_bp.route('/generate', methods=['POST'])
@require_auth
@rate_limit_moderate()
def generate_writing():
    """Generate writing based on prompt"""
    
    if not writing_suite_service:
        return jsonify({
            'success': False,
            'error': 'Writing Suite service unavailable'
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
        
        # Extract prompt data
        writing_type_str = data.get('writing_type', '').lower()
        topic = data.get('topic', '').strip()
        tone_str = data.get('tone', 'professional').lower()
        length = data.get('length', 'medium').lower()
        target_audience = data.get('target_audience', '').strip()
        key_points = data.get('key_points', [])
        additional_requirements = data.get('additional_requirements', '').strip()
        format_specs = data.get('format_specifications', {})
        save_title = data.get('save_title', '').strip()
        
        # Validate required fields
        if not writing_type_str or not topic:
            return jsonify({
                'success': False,
                'error': 'Writing type and topic are required'
            }), 400
        
        # Validate enums
        try:
            writing_type = WritingType(writing_type_str)
            tone = ToneStyle(tone_str)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid parameter: {str(e)}',
                'available_writing_types': [wt.value for wt in WritingType],
                'available_tones': [ts.value for ts in ToneStyle]
            }), 400
        
        if len(topic) > 200:
            return jsonify({
                'success': False,
                'error': 'Topic too long (max 200 characters)'
            }), 400
        
        if len(key_points) > 10:
            return jsonify({
                'success': False,
                'error': 'Too many key points (max 10)'
            }), 400
        
        # Check usage limits
        usage_limits = {
            'bronze': 5,   # 5 writing generations per day
            'silver': 20,  # 20 per day
            'gold': -1     # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 5)
        
        if daily_limit != -1:
            current_usage = get_daily_usage(user_id, 'writing_generation')
            if current_usage >= daily_limit:
                return jsonify({
                    'success': False,
                    'error': f'Daily limit reached ({daily_limit} writing generations per day for {user_plan} tier)',
                    'upgrade_required': user_plan == 'bronze'
                }), 429
        
        # Check if user wants their prompt/result saved for training
        content_type = "scripts" if writing_type.value in ["screenplay", "stage_play", "tv_script", "radio_script"] else \
                      "articles" if writing_type.value in ["news_article", "blog_post", "academic_article", "opinion_piece"] else \
                      "letters" if "letter" in writing_type.value else "creative"
        contribute_to_training = user_has_consent(user_id, content_type)
        
        # Create writing prompt
        prompt = WritingPrompt(
            writing_type=writing_type,
            topic=topic,
            tone=tone,
            length=length,
            target_audience=target_audience or "general audience",
            key_points=key_points,
            additional_requirements=additional_requirements,
            format_specifications=format_specs
        )
        
        # Generate writing
        writing_output = writing_suite_service.generate_writing(prompt, contribute=contribute_to_training)
        
        # Save if title provided
        writing_id = None
        if save_title:
            writing_id = writing_suite_service.save_writing(user_id, save_title, writing_output, prompt)
        
        # Deduct usage
        if daily_limit != -1:
            deduct_usage(user_id, 'writing_generation', 1)
        
        logger.info(f"✅ Generated {writing_type.value} for user {user_id}, topic: {topic}, contribute: {contribute_to_training}")
        
        # Prepare response
        response_data = {
            'success': True,
            'writing': {
                'content': writing_output.content,
                'word_count': writing_output.word_count,
                'character_count': writing_output.character_count,
                'estimated_reading_time': writing_output.estimated_reading_time,
                'style_score': writing_output.style_score,
                'readability_score': writing_output.readability_score,
                'format_analysis': writing_output.format_analysis,
                'suggestions': writing_output.suggestions
            },
            'prompt_details': {
                'writing_type': writing_type.value,
                'topic': topic,
                'tone': tone.value,
                'length': length,
                'target_audience': target_audience
            },
            'remaining_usage': max(0, daily_limit - current_usage - 1) if daily_limit != -1 else -1,
            'contribute_status': contribute_to_training
        }
        
        if writing_id:
            response_data['writing_id'] = writing_id
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error in generate_writing: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@writing_suite_bp.route('/types', methods=['GET'])
@require_auth
def get_writing_types():
    """Get available writing types and their descriptions"""
    
    try:
        writing_types = []
        
        # Define categories and descriptions
        categories = {
            'scripts': {
                'name': 'Scripts & Screenplays',
                'types': [
                    {
                        'value': WritingType.SCREENPLAY.value,
                        'name': 'Screenplay',
                        'description': 'Movie script with proper formatting, character dialogue, and scene directions',
                        'features': ['Scene headers', 'Character names', 'Action lines', 'Dialogue', 'Transitions']
                    },
                    {
                        'value': WritingType.STAGE_PLAY.value,
                        'name': 'Stage Play',
                        'description': 'Theater script with character list, stage directions, and dramatic dialogue',
                        'features': ['Character list', 'Stage directions', 'Act/Scene structure', 'Lighting cues']
                    },
                    {
                        'value': WritingType.TV_SCRIPT.value,
                        'name': 'TV Script',
                        'description': 'Television episode script with commercial breaks and time constraints',
                        'features': ['Teaser/Acts', 'Commercial breaks', 'Time codes', 'Camera directions']
                    },
                    {
                        'value': WritingType.RADIO_SCRIPT.value,
                        'name': 'Radio Script',
                        'description': 'Audio-only script with sound effects and voice-over directions',
                        'features': ['Voice-over', 'Sound effects', 'Music cues', 'Time markers']
                    }
                ]
            },
            'articles': {
                'name': 'Articles & Posts',
                'types': [
                    {
                        'value': WritingType.NEWS_ARTICLE.value,
                        'name': 'News Article',
                        'description': 'Factual journalism piece with headline, byline, and inverted pyramid structure',
                        'features': ['Headline', 'Byline', 'Lead paragraph', 'Facts', 'Quotes']
                    },
                    {
                        'value': WritingType.BLOG_POST.value,
                        'name': 'Blog Post',
                        'description': 'Engaging online article with SEO-friendly structure and conversational tone',
                        'features': ['SEO title', 'Subheadings', 'Bullet points', 'Call-to-action']
                    },
                    {
                        'value': WritingType.ACADEMIC_ARTICLE.value,
                        'name': 'Academic Article',
                        'description': 'Scholarly writing with citations, formal tone, and research-based content',
                        'features': ['Abstract', 'Citations', 'Formal tone', 'Methodology']
                    },
                    {
                        'value': WritingType.OPINION_PIECE.value,
                        'name': 'Opinion Piece',
                        'description': 'Persuasive editorial with strong viewpoint and supporting arguments',
                        'features': ['Strong thesis', 'Arguments', 'Counter-arguments', 'Call to action']
                    }
                ]
            },
            'letters': {
                'name': 'Letters & Correspondence',
                'types': [
                    {
                        'value': WritingType.BUSINESS_LETTER.value,
                        'name': 'Business Letter',
                        'description': 'Professional correspondence with formal structure and tone',
                        'features': ['Letterhead', 'Date', 'Address', 'Formal salutation', 'Professional closing']
                    },
                    {
                        'value': WritingType.PERSONAL_LETTER.value,
                        'name': 'Personal Letter',
                        'description': 'Informal correspondence with personal tone and casual structure',
                        'features': ['Casual greeting', 'Personal anecdotes', 'Warm closing']
                    },
                    {
                        'value': WritingType.COVER_LETTER.value,
                        'name': 'Cover Letter',
                        'description': 'Job application letter highlighting qualifications and interest',
                        'features': ['Job reference', 'Qualifications', 'Company research', 'Call for interview']
                    },
                    {
                        'value': WritingType.RESIGNATION_LETTER.value,
                        'name': 'Resignation Letter',
                        'description': 'Professional notice of employment termination with transition details',
                        'features': ['Notice period', 'Reason (optional)', 'Transition offer', 'Gratitude']
                    }
                ]
            },
            'creative': {
                'name': 'Creative Writing',
                'types': [
                    {
                        'value': WritingType.SHORT_FICTION.value,
                        'name': 'Short Fiction',
                        'description': 'Complete fictional story with characters, plot, and resolution',
                        'features': ['Character development', 'Plot structure', 'Dialogue', 'Setting']
                    },
                    {
                        'value': WritingType.FLASH_FICTION.value,
                        'name': 'Flash Fiction',
                        'description': 'Very short story (under 300 words) with immediate impact',
                        'features': ['Single moment', 'Twist ending', 'Minimal characters', 'Immediate impact']
                    },
                    {
                        'value': WritingType.CREATIVE_ESSAY.value,
                        'name': 'Creative Essay',
                        'description': 'Personal reflection combining storytelling with analysis',
                        'features': ['Personal voice', 'Narrative elements', 'Reflection', 'Imagery']
                    },
                    {
                        'value': WritingType.MEMOIR_EXCERPT.value,
                        'name': 'Memoir Excerpt',
                        'description': 'Personal life story segment with emotional depth and reflection',
                        'features': ['First person', 'True events', 'Emotional depth', 'Life lessons']
                    }
                ]
            }
        }
        
        # Get tone styles
        tones = []
        tone_descriptions = {
            ToneStyle.FORMAL: "Proper, structured language suitable for official documents",
            ToneStyle.CASUAL: "Relaxed, conversational style for informal communication",
            ToneStyle.PROFESSIONAL: "Polished business tone balancing friendliness with competence",
            ToneStyle.FRIENDLY: "Warm, approachable language that builds rapport",
            ToneStyle.PERSUASIVE: "Compelling language designed to influence and convince",
            ToneStyle.INFORMATIVE: "Clear, factual presentation focused on education",
            ToneStyle.CREATIVE: "Imaginative, expressive language with artistic flair",
            ToneStyle.HUMOROUS: "Light-hearted, entertaining approach with wit",
            ToneStyle.SERIOUS: "Thoughtful, weighty tone for important topics",
            ToneStyle.EMPATHETIC: "Understanding, compassionate language showing care"
        }
        
        for tone in ToneStyle:
            tones.append({
                'value': tone.value,
                'name': tone.value.replace('_', ' ').title(),
                'description': tone_descriptions.get(tone, 'Writing tone style')
            })
        
        return jsonify({
            'success': True,
            'categories': categories,
            'tones': tones,
            'lengths': [
                {'value': 'short', 'name': 'Short', 'description': 'Brief, concise writing'},
                {'value': 'medium', 'name': 'Medium', 'description': 'Standard length with good detail'},
                {'value': 'long', 'name': 'Long', 'description': 'Comprehensive, detailed writing'}
            ]
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_writing_types: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@writing_suite_bp.route('/user-writings', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_user_writings():
    """Get user's generated writings"""
    
    if not writing_suite_service:
        return jsonify({
            'success': False,
            'error': 'Writing Suite service unavailable'
        }), 503
    
    try:
        user_id = session.get('user_id')
        writing_type_str = request.args.get('type', '').lower()
        limit = min(int(request.args.get('limit', 20)), 50)
        
        writing_type = None
        if writing_type_str:
            try:
                writing_type = WritingType(writing_type_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid writing type: {writing_type_str}'
                }), 400
        
        writings = writing_suite_service.get_user_writings(user_id, writing_type, limit)
        
        return jsonify({
            'success': True,
            'writings': writings,
            'count': len(writings),
            'filter_type': writing_type.value if writing_type else 'all'
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_writings: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@writing_suite_bp.route('/stats', methods=['GET'])
@require_auth
@rate_limit_moderate()
def get_stats():
    """Get writing suite statistics and user limits"""
    
    try:
        user_id = session.get('user_id')
        user_plan = get_user_plan(user_id)
        
        # Usage limits by plan
        usage_limits = {
            'bronze': 5,   # 5 writing generations per day
            'silver': 20,  # 20 per day
            'gold': -1     # Unlimited
        }
        
        daily_limit = usage_limits.get(user_plan, 5)
        current_usage = get_daily_usage(user_id, 'writing_generation')
        
        stats = {
            'user_plan': user_plan,
            'daily_limit': daily_limit,
            'current_usage': current_usage,
            'remaining_usage': max(0, daily_limit - current_usage) if daily_limit != -1 else -1,
            'features': {
                'all_writing_types': True,
                'all_tones': True,
                'format_customization': user_plan in ['silver', 'gold'],
                'unlimited_generation': user_plan == 'gold',
                'advanced_analytics': user_plan == 'gold',
                'export_options': user_plan in ['silver', 'gold'],
                'save_writings': True,
                'style_analysis': True
            },
            'available_categories': 4,  # scripts, articles, letters, creative
            'total_writing_types': len(WritingType),
            'available_tones': len(ToneStyle)
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

@writing_suite_bp.route('/analyze', methods=['POST'])
@require_auth
@rate_limit_moderate()
def analyze_writing():
    """Analyze existing writing content"""
    
    if not writing_suite_service:
        return jsonify({
            'success': False,
            'error': 'Writing Suite service unavailable'
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        content = data.get('content', '').strip()
        writing_type_str = data.get('writing_type', '').lower()
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required for analysis'
            }), 400
        
        if len(content) > 50000:  # Limit analysis size
            return jsonify({
                'success': False,
                'error': 'Content too long for analysis (max 50,000 characters)'
            }), 400
        
        # Basic analysis
        word_count = len(content.split())
        character_count = len(content)
        reading_time = max(1, word_count // 200)
        
        # Format analysis based on type
        format_analysis = {}
        if writing_type_str:
            if writing_type_str in ['screenplay', 'stage_play']:
                format_analysis = {
                    'character_names': len(re.findall(r'^[A-Z]{3,}:', content, re.MULTILINE)),
                    'scene_headers': len(re.findall(r'^(INT\.|EXT\.)', content, re.MULTILINE)),
                    'action_lines': len(re.findall(r'^[^A-Z].*[^:]$', content, re.MULTILINE)),
                    'dialogue_lines': len(re.findall(r'^\s{4,}[^(]', content, re.MULTILINE))
                }
            elif writing_type_str in ['news_article', 'blog_post']:
                format_analysis = {
                    'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
                    'has_headline': content.split('\n')[0].isupper(),
                    'subheading_count': content.count('##') + content.count('###'),
                    'avg_paragraph_length': word_count / max(1, len(content.split('\n\n')))
                }
            elif 'letter' in writing_type_str:
                format_analysis = {
                    'has_date': any(month in content for month in ['January', 'February', 'March']),
                    'has_salutation': 'Dear' in content or 'Hello' in content,
                    'has_closing': any(closing in content for closing in ['Sincerely', 'Best regards', 'Warmly']),
                    'formality_score': 0.8 if 'Sir/Madam' in content else 0.5
                }
        
        # Style analysis (simplified)
        style_score = min(1.0, max(0.0, (word_count / 1000) * 0.1 + 0.5))  # Rough estimate
        readability_score = max(0, 100 - (word_count / 100))  # Simplified
        
        # Generate suggestions
        suggestions = []
        if word_count < 50:
            suggestions.append("Content is very short - consider expanding key points")
        if word_count > 2000:
            suggestions.append("Content is quite long - consider breaking into sections")
        if content.count('.') / max(1, word_count) < 0.05:
            suggestions.append("Consider adding more sentence variety")
        
        analysis = {
            'word_count': word_count,
            'character_count': character_count,
            'estimated_reading_time': reading_time,
            'style_score': round(style_score, 2),
            'readability_score': round(readability_score, 2),
            'format_analysis': format_analysis,
            'suggestions': suggestions,
            'structure_analysis': {
                'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
                'sentence_count': len(re.findall(r'[.!?]+', content)),
                'avg_sentence_length': round(word_count / max(1, len(re.findall(r'[.!?]+', content))), 2)
            }
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_writing: {traceback.format_exc()}")
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