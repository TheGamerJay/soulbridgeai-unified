"""
SoulBridge AI - Meditation Generator
AI-powered meditation script generation with personalized content
"""
import logging
from typing import Dict, Any, List, Optional
import json
import random

logger = logging.getLogger(__name__)

class MeditationGenerator:
    """Generates personalized meditation scripts using AI"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        
        # Meditation script templates for fallback
        self.script_templates = {
            'stress': {
                'introduction': "Welcome to your stress relief meditation. Find a comfortable position and allow yourself to begin releasing the tension of the day.",
                'preparation': "Close your eyes or soften your gaze. Take three deep breaths, letting each exhale carry away a bit of stress.",
                'main_segments': [
                    "Focus on your breath as it flows naturally in and out",
                    "Notice any areas of tension in your body and breathe into them",
                    "Imagine stress leaving your body with each exhale",
                    "Allow your mind to become calm and peaceful"
                ],
                'conclusion': "Take a moment to appreciate this gift of peace you've given yourself. When you're ready, gently open your eyes."
            },
            'anxiety': {
                'introduction': "Welcome to your anxiety support meditation. You are safe, you are here, and you are grounded.",
                'preparation': "Feel your body supported by the surface beneath you. Take slow, calming breaths.",
                'main_segments': [
                    "Notice 5 things you can see around you",
                    "Notice 4 things you can touch or feel",
                    "Notice 3 things you can hear",
                    "Notice 2 things you can smell",
                    "Notice 1 thing you can taste"
                ],
                'conclusion': "You are grounded, you are safe, and you can handle whatever comes your way."
            },
            'sleep': {
                'introduction': "Welcome to your sleep preparation meditation. It's time to let go of the day and prepare for restful sleep.",
                'preparation': "Make yourself comfortable in bed. Let your body sink into the mattress and pillow.",
                'main_segments': [
                    "Tense and release each muscle group, starting with your toes",
                    "Feel your entire body becoming heavy and relaxed",
                    "Imagine yourself in a peaceful, safe place",
                    "Allow your mind to become quiet and still"
                ],
                'conclusion': "Let yourself drift into peaceful, restorative sleep."
            },
            'healing': {
                'introduction': "Welcome to your emotional healing meditation. This is a sacred space for your heart and soul.",
                'preparation': "Place one hand on your heart and one on your belly. Feel your own loving presence.",
                'main_segments': [
                    "Send loving-kindness to yourself",
                    "Forgive yourself for any perceived shortcomings",
                    "Embrace all parts of yourself with compassion",
                    "Feel your heart opening to healing and growth"
                ],
                'conclusion': "You are worthy of love, healing, and peace. Carry this feeling with you."
            },
            'confidence': {
                'introduction': "Welcome to your confidence meditation. You have everything you need within you.",
                'preparation': "Sit tall with your shoulders back. Feel your own strength and presence.",
                'main_segments': [
                    "Recall a time when you felt truly confident and capable",
                    "Feel that confidence filling your body now",
                    "Repeat positive affirmations about your abilities",
                    "Visualize yourself succeeding in your goals"
                ],
                'conclusion': "You are capable, worthy, and ready to share your gifts with the world."
            },
            'breathing': {
                'introduction': "Welcome to your breathing meditation. Your breath is your anchor to the present moment.",
                'preparation': "Find a rhythm that feels natural and comfortable. There's no need to force anything.",
                'main_segments': [
                    "Breathe in for 4 counts",
                    "Hold for 4 counts",
                    "Breathe out for 4 counts",
                    "Hold empty for 4 counts"
                ],
                'conclusion': "Your breath is always available to bring you back to peace and presence."
            }
        }
        
        # Audio cue templates
        self.audio_cues = {
            'bell': {'type': 'bell', 'description': 'Gentle meditation bell'},
            'nature': {'type': 'nature', 'description': 'Soft nature sounds'},
            'breath': {'type': 'breath_guide', 'description': 'Breathing rhythm guide'},
            'silence': {'type': 'silence', 'description': 'Peaceful silence'}
        }
    
    def generate_meditation_script(self, meditation_id: str, user_id: int = None, 
                                 duration_minutes: int = 10) -> Dict[str, Any]:
        """Generate a personalized meditation script"""
        try:
            # Get meditation category from ID
            category = self._get_category_from_id(meditation_id)
            
            # Try AI generation if available
            if self.openai_client and user_id:
                ai_result = self._generate_ai_script(meditation_id, category, user_id, duration_minutes)
                if ai_result['success']:
                    return ai_result
                else:
                    logger.warning(f"AI script generation failed, using template: {ai_result.get('error')}")
            
            # Fallback to template-based generation
            return self._generate_template_script(meditation_id, category, duration_minutes)
            
        except Exception as e:
            logger.error(f"Error generating meditation script for {meditation_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to generate meditation script'
            }
    
    def _generate_ai_script(self, meditation_id: str, category: str, user_id: int, 
                          duration_minutes: int) -> Dict[str, Any]:
        """Generate meditation script using AI"""
        try:
            # Get user context (meditation history, preferences)
            user_context = self._get_user_context(user_id)
            
            # Create AI prompt
            prompt = self._create_meditation_prompt(meditation_id, category, duration_minutes, user_context)
            
            # Generate script using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meditation teacher creating personalized guided meditations. Create warm, calming, and supportive meditation scripts that help users find peace and healing. Format your response as a structured JSON with introduction, main_practice, and conclusion sections."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            script_content = response.choices[0].message.content
            
            # Parse AI response
            try:
                ai_script = json.loads(script_content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured script from text
                ai_script = self._structure_ai_response(script_content)
            
            # Add timing and audio cues
            ai_script['timing'] = self._generate_timing_cues(duration_minutes)
            ai_script['audio_cues'] = self._select_audio_cues(category)
            
            logger.info(f"🤖 Generated AI meditation script for {meditation_id}")
            
            return {
                'success': True,
                'script': ai_script,
                'generation_method': 'ai'
            }
            
        except Exception as e:
            logger.error(f"Error in AI script generation: {e}")
            return {
                'success': False,
                'error': f'AI generation failed: {str(e)}'
            }
    
    def _generate_template_script(self, meditation_id: str, category: str, 
                                duration_minutes: int) -> Dict[str, Any]:
        """Generate meditation script using templates"""
        try:
            # Get template for category
            template = self.script_templates.get(category, self.script_templates['stress'])
            
            # Create script structure
            script = {
                'title': self._get_meditation_title(meditation_id),
                'category': category,
                'duration_minutes': duration_minutes,
                'introduction': template['introduction'],
                'preparation': template['preparation'],
                'main_practice': self._expand_main_segments(template['main_segments'], duration_minutes),
                'conclusion': template['conclusion'],
                'timing': self._generate_timing_cues(duration_minutes),
                'audio_cues': self._select_audio_cues(category)
            }
            
            logger.info(f"📝 Generated template meditation script for {meditation_id}")
            
            return {
                'success': True,
                'script': script,
                'generation_method': 'template'
            }
            
        except Exception as e:
            logger.error(f"Error in template script generation: {e}")
            return {
                'success': False,
                'error': f'Template generation failed: {str(e)}'
            }
    
    def _create_meditation_prompt(self, meditation_id: str, category: str, 
                                duration_minutes: int, user_context: Dict[str, Any]) -> str:
        """Create AI prompt for meditation generation"""
        
        meditation_title = self._get_meditation_title(meditation_id)
        
        # User personalization context
        experience_level = user_context.get('experience_level', 'beginner')
        preferred_style = user_context.get('preferred_style', 'gentle')
        current_mood = user_context.get('current_mood', 'neutral')
        
        prompt = f"""Create a {duration_minutes}-minute guided meditation script for "{meditation_title}" in the {category} category.

User Context:
- Experience level: {experience_level}
- Preferred style: {preferred_style}
- Current mood/need: {current_mood}

Please create a meditation script that includes:
1. A warm, welcoming introduction (1-2 minutes)
2. Preparation and settling instructions (1 minute)  
3. Main meditation practice appropriate for the theme (most of the time)
4. Gentle conclusion and transition back (1 minute)

The script should be:
- Warm and supportive in tone
- Appropriate for the {category} theme
- Suitable for {experience_level} practitioners
- Structured for exactly {duration_minutes} minutes

Format as JSON with these keys:
- "introduction": welcoming opening
- "preparation": settling and breathing instructions
- "main_practice": core meditation content with specific techniques
- "conclusion": gentle ending and transition back

Make it personal, calming, and healing."""

        return prompt
    
    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user context for personalization (placeholder)"""
        # In a full implementation, this would query user's meditation history,
        # preferences, and current state
        return {
            'experience_level': 'beginner',  # Would come from user profile
            'preferred_style': 'gentle',     # Would come from preferences
            'current_mood': 'stressed',      # Could be from recent app usage
            'total_sessions': 0,             # From meditation history
            'favorite_categories': []        # From session data
        }
    
    def _get_category_from_id(self, meditation_id: str) -> str:
        """Extract category from meditation ID"""
        if meditation_id.startswith('stress'):
            return 'stress'
        elif meditation_id.startswith('anxiety'):
            return 'anxiety'
        elif meditation_id.startswith('sleep'):
            return 'sleep'
        elif meditation_id.startswith('healing'):
            return 'healing'
        elif meditation_id.startswith('confidence'):
            return 'confidence'
        elif meditation_id.startswith('breathing'):
            return 'breathing'
        else:
            return 'stress'  # Default fallback
    
    def _get_meditation_title(self, meditation_id: str) -> str:
        """Get human-readable title from meditation ID"""
        title_map = {
            'stress-breathing-basic': 'Basic Breathing for Stress Relief',
            'stress-body-scan': 'Body Scan Meditation',
            'anxiety-grounding-54321': 'Grounding Technique (5-4-3-2-1)',
            'sleep-body-relaxation': 'Progressive Muscle Relaxation',
            'healing-self-compassion': 'Self-Compassion Practice',
            'confidence-affirmations': 'Confidence Affirmations',
            'breathing-box-breathing': 'Box Breathing Exercise'
        }
        
        return title_map.get(meditation_id, meditation_id.replace('-', ' ').title())
    
    def _expand_main_segments(self, segments: List[str], duration_minutes: int) -> str:
        """Expand main practice segments based on duration"""
        if duration_minutes <= 5:
            # Short version - pick 2-3 key segments
            selected_segments = segments[:3]
        elif duration_minutes <= 10:
            # Medium version - use most segments
            selected_segments = segments
        else:
            # Long version - expand with more detail
            selected_segments = segments + [
                "Continue to breathe deeply and mindfully",
                "Allow yourself to go even deeper into relaxation",
                "Rest in this peaceful state"
            ]
        
        return " ".join([f"• {segment}" for segment in selected_segments])
    
    def _generate_timing_cues(self, duration_minutes: int) -> List[Dict[str, Any]]:
        """Generate timing cues for the meditation"""
        total_seconds = duration_minutes * 60
        
        # Basic timing structure
        cues = [
            {'time': 0, 'type': 'start', 'instruction': 'Begin meditation'},
            {'time': 60, 'type': 'settle', 'instruction': 'Settle into practice'},
            {'time': total_seconds - 120, 'type': 'prepare_end', 'instruction': 'Begin to prepare for conclusion'},
            {'time': total_seconds - 30, 'type': 'transition', 'instruction': 'Slowly begin to return'},
            {'time': total_seconds, 'type': 'end', 'instruction': 'Complete meditation'}
        ]
        
        # Add middle cues for longer meditations
        if duration_minutes >= 10:
            middle_time = total_seconds // 2
            cues.insert(2, {
                'time': middle_time, 
                'type': 'deepening', 
                'instruction': 'Deepen your practice'
            })
        
        if duration_minutes >= 20:
            quarter_time = total_seconds // 4
            three_quarter_time = (total_seconds * 3) // 4
            cues.insert(2, {
                'time': quarter_time, 
                'type': 'guidance', 
                'instruction': 'Continue with gentle awareness'
            })
            cues.insert(-2, {
                'time': three_quarter_time, 
                'type': 'integration', 
                'instruction': 'Begin to integrate your experience'
            })
        
        return sorted(cues, key=lambda x: x['time'])
    
    def _select_audio_cues(self, category: str) -> List[Dict[str, Any]]:
        """Select appropriate audio cues for the category"""
        audio_map = {
            'stress': ['bell', 'nature'],
            'anxiety': ['breath', 'bell'],
            'sleep': ['nature', 'silence'],
            'healing': ['bell', 'nature'],
            'confidence': ['bell'],
            'breathing': ['breath', 'bell']
        }
        
        selected_types = audio_map.get(category, ['bell'])
        return [self.audio_cues[audio_type] for audio_type in selected_types]
    
    def _structure_ai_response(self, content: str) -> Dict[str, Any]:
        """Structure AI response if JSON parsing fails"""
        # Simple text parsing to create structured response
        lines = content.strip().split('\n')
        
        script = {
            'introduction': '',
            'preparation': '',
            'main_practice': '',
            'conclusion': ''
        }
        
        current_section = 'introduction'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to identify section transitions
            if any(word in line.lower() for word in ['preparation', 'prepare', 'settle']):
                current_section = 'preparation'
            elif any(word in line.lower() for word in ['main', 'practice', 'focus', 'breathe']):
                current_section = 'main_practice'
            elif any(word in line.lower() for word in ['conclusion', 'end', 'finish', 'complete']):
                current_section = 'conclusion'
            
            # Add content to current section
            if script[current_section]:
                script[current_section] += ' '
            script[current_section] += line
        
        return script
    
    def generate_meditation_variations(self, base_meditation_id: str, count: int = 3) -> Dict[str, Any]:
        """Generate variations of a base meditation"""
        try:
            variations = []
            category = self._get_category_from_id(base_meditation_id)
            
            for i in range(count):
                # Create variation with different focus
                variation_id = f"{base_meditation_id}-v{i+1}"
                variation = {
                    'id': variation_id,
                    'title': f"{self._get_meditation_title(base_meditation_id)} (Variation {i+1})",
                    'category': category,
                    'focus': self._get_variation_focus(category, i),
                    'description': f"A unique take on {self._get_meditation_title(base_meditation_id)}"
                }
                variations.append(variation)
            
            return {
                'success': True,
                'variations': variations,
                'base_meditation': base_meditation_id
            }
            
        except Exception as e:
            logger.error(f"Error generating meditation variations: {e}")
            return {
                'success': False,
                'error': 'Failed to generate variations'
            }
    
    def _get_variation_focus(self, category: str, variation_index: int) -> str:
        """Get focus theme for meditation variations"""
        focus_themes = {
            'stress': ['breath-focused', 'body-based', 'visualization'],
            'anxiety': ['grounding', 'cognitive', 'somatic'],
            'sleep': ['progressive relaxation', 'imagery', 'counting'],
            'healing': ['self-compassion', 'forgiveness', 'inner-child'],
            'confidence': ['affirmations', 'visualization', 'body-posture'],
            'breathing': ['rhythm-based', 'nostril-alternate', 'belly-breath']
        }
        
        themes = focus_themes.get(category, ['mindfulness', 'awareness', 'presence'])
        return themes[variation_index % len(themes)]