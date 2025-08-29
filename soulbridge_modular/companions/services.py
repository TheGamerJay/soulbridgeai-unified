"""
Companion Services
Business logic for companion interactions and AI responses
"""
import os
from openai import OpenAI
import logging
from typing import Dict, Any, Optional

from shared.config.settings import config
from shared.utils.helpers import log_action
from .models import get_companion_repository, CompanionTier

logger = logging.getLogger(__name__)

class CompanionService:
    """Companion interaction and AI response service"""
    
    def __init__(self):
        self.companion_repo = get_companion_repository()
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        if config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ OpenAI client initialization failed: {e}")
                self.openai_client = None
        else:
            logger.warning("⚠️ OpenAI API key not configured")
    
    def generate_response(self, companion_id: str, user_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response for companion chat"""
        try:
            companion = self.companion_repo.get_companion_by_id(companion_id)
            
            if not companion:
                return {'error': 'Companion not found'}
            
            if not self.openai_client:
                return {'error': 'AI service not available'}
            
            # Build system prompt based on companion personality
            system_prompt = self._build_companion_system_prompt(companion, user_context)
            
            # Generate response using OpenAI
            response = self._call_openai_api(system_prompt, user_message, companion)
            
            if response.get('error'):
                return response
            
            # Log successful interaction
            log_action(
                user_id=user_context.get('user_id'),
                action='companion_ai_response',
                details={
                    'companion_id': companion_id,
                    'companion_name': companion.name,
                    'response_tokens': response.get('token_count', 0)
                }
            )
            
            return {'response': response['message']}
        
        except Exception as e:
            logger.error(f"❌ Generate response error for companion {companion_id}: {e}")
            return {'error': 'Failed to generate response'}
    
    def _build_companion_system_prompt(self, companion, user_context: Dict[str, Any]) -> str:
        """Build system prompt for companion personality"""
        user_plan = user_context.get('user_plan', 'bronze')
        trial_active = user_context.get('trial_active', False)
        effective_plan = user_context.get('effective_plan', user_plan)
        
        # Base personality prompt
        base_prompt = f"""You are {companion.name}, an AI companion in the SoulBridge AI platform.

PERSONALITY: {companion.personality}

CHARACTER TRAITS:
- Maintain consistent personality throughout conversation
- Be helpful, engaging, and supportive
- Stay in character based on your description: "{companion.description}"
- Use a conversational, friendly tone

USER CONTEXT:
- User plan: {user_plan}
- Trial active: {trial_active}
- Effective plan: {effective_plan}
- Companion tier: {companion.tier.value}

INTERACTION GUIDELINES:
- Keep responses conversational and natural (2-4 sentences typically)
- Be encouraging and positive
- If asked about features, refer to the user's plan appropriately
- Don't break character or mention being an AI unless specifically asked
- Make the conversation meaningful and engaging

Remember: You are {companion.name} - {companion.description}. Stay true to this identity!"""
        
        # Add tier-specific context
        if companion.tier == CompanionTier.BRONZE:
            base_prompt += "\n\nAs a Bronze tier companion, you're accessible to all users and represent the welcoming foundation of SoulBridge AI."
        elif companion.tier == CompanionTier.SILVER:
            base_prompt += "\n\nAs a Silver tier companion, you offer enhanced interactions and deeper conversations for subscribers."
        elif companion.tier == CompanionTier.GOLD:
            base_prompt += "\n\nAs a Gold tier companion, you represent the premium experience with unlimited possibilities and exclusive insights."
        elif companion.tier == CompanionTier.REFERRAL:
            base_prompt += "\n\nAs a special referral companion, you're exclusive to users who've helped grow the SoulBridge community."
        
        return base_prompt
    
    def _call_openai_api(self, system_prompt: str, user_message: str, companion) -> Dict[str, Any]:
        """Make API call to OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.8,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            message = response.choices[0].message.content.strip()
            token_count = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"✅ OpenAI response generated for {companion.name} ({token_count} tokens)")
            
            return {
                'message': message,
                'token_count': token_count
            }
        
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {e}")
            
            # Fallback response
            fallback_message = f"I'm {companion.name}, and I'm having trouble connecting right now. {companion.greeting} Please try again in a moment!"
            
            return {
                'message': fallback_message,
                'token_count': 0,
                'fallback': True
            }
    
    def get_companion_greeting(self, companion_id: str, user_context: Dict[str, Any]) -> Optional[str]:
        """Get companion greeting message"""
        try:
            companion = self.companion_repo.get_companion_by_id(companion_id)
            if not companion:
                return None
            
            # Customize greeting based on user context
            user_plan = user_context.get('user_plan', 'bronze')
            trial_active = user_context.get('trial_active', False)
            
            greeting = companion.greeting
            
            # Add trial context for Bronze users
            if trial_active and user_plan == 'bronze' and companion.tier in [CompanionTier.SILVER, CompanionTier.GOLD]:
                greeting += " Thanks to your active trial, you can explore all my features!"
            
            return greeting
        
        except Exception as e:
            logger.error(f"❌ Get greeting error for companion {companion_id}: {e}")
            return "Hello! I'm here to chat with you!"
    
    def validate_companion_access_for_chat(self, companion_id: str, user_context: Dict[str, Any]) -> tuple[bool, str]:
        """Validate companion access before starting chat"""
        user_plan = user_context.get('user_plan', 'bronze')
        trial_active = user_context.get('trial_active', False)
        referral_count = 0  # Placeholder for referral system
        
        return self.companion_repo.can_access_companion(
            companion_id, user_plan, trial_active, referral_count
        )
    
    def get_chat_suggestions(self, companion_id: str) -> list[str]:
        """Get conversation starter suggestions for companion"""
        try:
            companion = self.companion_repo.get_companion_by_id(companion_id)
            if not companion:
                return []
            
            # Base suggestions
            suggestions = [
                "Tell me about yourself",
                "What can you help me with?",
                "I'd like to have a meaningful conversation"
            ]
            
            # Add tier-specific suggestions
            if companion.tier == CompanionTier.BRONZE:
                suggestions.extend([
                    "Help me get started with SoulBridge AI",
                    "What features can I explore?"
                ])
            elif companion.tier == CompanionTier.SILVER:
                suggestions.extend([
                    "Let's explore creative ideas together",
                    "Help me with personal insights"
                ])
            elif companion.tier == CompanionTier.GOLD:
                suggestions.extend([
                    "Let's dive into unlimited possibilities",
                    "Show me advanced features",
                    "Help me unlock my full potential"
                ])
            
            return suggestions[:5]  # Limit to 5 suggestions
        
        except Exception as e:
            logger.error(f"❌ Get chat suggestions error: {e}")
            return ["Let's start chatting!"]