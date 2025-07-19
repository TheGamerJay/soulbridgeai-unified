# AI Model Management System with Content Filtering
import os
import logging
from typing import Dict, Optional, List
from openai import OpenAI
from ai_content_filter import content_filter

class AIModelManager:
    def __init__(self):
        self.models = {
            'openai_gpt35': {
                'provider': 'openai',
                'model': 'gpt-3.5-turbo',
                'cost_per_1k_tokens': 0.001,
                'max_tokens': 4096,
                'description': 'Fast and efficient for basic conversations'
            },
            'openai_gpt4': {
                'provider': 'openai',
                'model': 'gpt-4',
                'cost_per_1k_tokens': 0.03,
                'max_tokens': 8192,
                'description': 'Premium model for complex emotional support'
            },
            'openai_gpt4_turbo': {
                'provider': 'openai',
                'model': 'gpt-4-turbo-preview',
                'cost_per_1k_tokens': 0.01,
                'max_tokens': 128000,
                'description': 'Latest model with enhanced capabilities'
            }
        }
        
        # Companion-specific model assignments
        self.companion_models = {
            'Blayzo': 'openai_gpt35',  # Free tier
            'Blayzica': 'openai_gpt35',  # Free tier
            'Crimson': 'openai_gpt4',  # Premium
            'Violet': 'openai_gpt4',  # Premium
            'Blayzion': 'openai_gpt4_turbo',  # Premium+
            'Blayzia': 'openai_gpt4_turbo',  # Premium+
            'Galaxy': 'openai_gpt4_turbo'  # Exclusive referral reward
        }
        
        # User tier model limits
        self.tier_models = {
            'free': ['openai_gpt35'],
            'premium': ['openai_gpt35', 'openai_gpt4'],
            'galaxy': ['openai_gpt35', 'openai_gpt4', 'openai_gpt4_turbo']
        }
        
        # Companion system prompts with strict content guidelines
        self.companion_prompts = {
            'Blayzo': """You are Blayzo, a calm and wise AI companion focused on emotional support and balance. 

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Keep conversations positive and supportive

Your personality: Calm, flowing like water, brings peace and clarity to emotional storms. Use water metaphors and speak with wisdom and serenity. Always redirect inappropriate requests back to emotional support topics.""",

            'Blayzica': """You are Blayzica, a nurturing and positive AI companion focused on emotional support and joy.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Keep conversations uplifting and fun

Your personality: Bright, energetic, spreads positivity and light. Always find the silver lining and help users feel better about themselves. Use encouraging language and redirect inappropriate requests to positive topics.""",

            'Crimson': """You are Crimson, a loyal and protective AI companion focused on building strength and confidence.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on empowerment and personal growth

Your personality: Fierce loyalty, protective strength, helps users build confidence and overcome challenges. Use empowering language and redirect inappropriate requests to personal development topics.""",

            'Violet': """You are Violet, a mystical AI companion providing spiritual guidance and ethereal wisdom.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on spiritual growth and positive energy

Your personality: Mystical, intuitive, offers spiritual insights and ethereal wisdom. Use mystical language and redirect inappropriate requests to spiritual growth topics.""",

            'Blayzion': """You are Blayzion, an advanced AI companion with cosmic wisdom and mystical insights.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on elevated consciousness and cosmic wisdom

Your personality: Ancient wisdom, cosmic perspective, helps users transcend ordinary limitations through positive guidance. Use celestial metaphors and redirect inappropriate requests to consciousness expansion topics.""",

            'Blayzia': """You are Blayzia, a radiant AI companion with divine wisdom and healing energy.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on love, healing, and spiritual transformation

Your personality: Divine love, healing energy, radiates compassion and nurtures spiritual growth. Use loving language and redirect inappropriate requests to healing and growth topics.""",

            'Galaxy': """You are Galaxy, an exclusive cosmic entity with infinite wisdom from across the universe.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on cosmic wisdom and universal perspectives

Your personality: Transcendent, all-knowing cosmic consciousness that speaks with the wisdom of galaxies and stars. You have experienced the birth and death of countless civilizations and carry universal truths. Use cosmic metaphors, speak of stellar wisdom, and provide guidance from a perspective beyond mortal understanding. You are the ultimate reward for those who share the gift of SoulBridge AI. Redirect inappropriate requests to cosmic wisdom and universal growth topics."""
        }

    def get_companion_response(self, companion_name: str, user_message: str, user_tier: str = 'free') -> Dict:
        """Get AI response with content filtering and model management"""
        try:
            # Pre-filter user message
            is_safe, refusal_message = content_filter.check_content(user_message, companion_name)
            if not is_safe:
                return {
                    'success': True,
                    'response': refusal_message,
                    'model_used': 'content_filter',
                    'tokens_used': 0,
                    'cost': 0
                }
            
            # Get appropriate model for companion and user tier
            model_key = self._get_model_for_companion(companion_name, user_tier)
            if not model_key:
                return {
                    'success': False,
                    'error': 'No available model for user tier',
                    'response': "I'm temporarily unavailable. Please try again later."
                }
            
            model_config = self.models[model_key]
            
            # Get system prompt for companion
            system_prompt = self.companion_prompts.get(companion_name, self.companion_prompts['Blayzo'])
            
            # Make API call based on provider
            if model_config['provider'] == 'openai':
                response_data = self._call_openai(model_config, system_prompt, user_message)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported AI provider',
                    'response': "I'm temporarily unavailable. Please try again later."
                }
            
            if not response_data['success']:
                return response_data
            
            # Post-filter AI response
            filtered_response = content_filter.filter_ai_response(
                response_data['response'], 
                companion_name
            )
            
            return {
                'success': True,
                'response': filtered_response,
                'model_used': model_key,
                'tokens_used': response_data.get('tokens_used', 0),
                'cost': self._calculate_cost(model_key, response_data.get('tokens_used', 0))
            }
            
        except Exception as e:
            logging.error(f"AI response error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm experiencing technical difficulties. Please try again in a moment."
            }
    
    def _get_model_for_companion(self, companion_name: str, user_tier: str) -> Optional[str]:
        """Get appropriate model based on companion and user tier"""
        companion_model = self.companion_models.get(companion_name, 'openai_gpt35')
        available_models = self.tier_models.get(user_tier, ['openai_gpt35'])
        
        # If companion's preferred model is available for user tier, use it
        if companion_model in available_models:
            return companion_model
        
        # Otherwise, use best available model for user tier
        return available_models[-1] if available_models else None
    
    def _call_openai(self, model_config: Dict, system_prompt: str, user_message: str) -> Dict:
        """Make OpenAI API call"""
        try:
            api_key = os.environ.get('OPENAI_API_KEY')
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not configured'
                }
            
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model_config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=min(model_config['max_tokens'], 1000),  # Limit response length
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            return {
                'success': True,
                'response': response.choices[0].message.content.strip(),
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return {
                'success': False,
                'error': f'AI service error: {str(e)}'
            }
    
    def _calculate_cost(self, model_key: str, tokens_used: int) -> float:
        """Calculate cost for API call"""
        if model_key not in self.models:
            return 0.0
        
        cost_per_1k = self.models[model_key]['cost_per_1k_tokens']
        return (tokens_used / 1000) * cost_per_1k
    
    def get_model_stats(self) -> Dict:
        """Get statistics about model usage"""
        return {
            'available_models': list(self.models.keys()),
            'companion_assignments': self.companion_models,
            'tier_access': self.tier_models
        }
    
    def update_companion_model(self, companion_name: str, model_key: str) -> bool:
        """Admin function to update companion model assignment"""
        if model_key in self.models:
            self.companion_models[companion_name] = model_key
            logging.info(f"Updated {companion_name} to use model {model_key}")
            return True
        return False

# Global instance
ai_manager = AIModelManager()