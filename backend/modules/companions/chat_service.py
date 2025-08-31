"""
SoulBridge AI - Companion Chat Service
Extracted from app.py monolith for modular architecture
"""
import logging
import time
from .companion_data import get_companion_by_id
from ..shared.database import get_database

logger = logging.getLogger(__name__)

class CompanionChatService:
    """Handles companion chat processing and AI responses"""
    
    def __init__(self):
        self.db = get_database()
    
    def process_chat(self, user_id: int, companion_id: str, message: str) -> dict:
        """Process a chat message and generate AI response"""
        try:
            # Get companion info
            companion = get_companion_by_id(companion_id)
            if not companion:
                return {'success': False, 'error': 'Companion not found'}
            
            # Log the chat interaction
            logger.info(f"[CHAT] User {user_id} chatting with {companion['name']}: {message[:50]}...")
            
            # Generate AI response
            response_data = self._generate_ai_response(
                user_id=user_id,
                companion=companion,
                message=message
            )
            
            if response_data['success']:
                # Save chat history (if implemented)
                self._save_chat_history(user_id, companion_id, message, response_data['response'])
                
                return {
                    'success': True,
                    'response': response_data['response'],
                    'companion': companion['name'],
                    'response_time': response_data.get('response_time', 0),
                    'emotions_detected': response_data.get('emotions_detected', []),
                    'enhancement_level': response_data.get('enhancement_level', 'standard')
                }
            else:
                return {'success': False, 'error': response_data['error']}
                
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            return {'success': False, 'error': 'Chat processing failed'}
    
    def _generate_ai_response(self, user_id: int, companion: dict, message: str) -> dict:
        """Generate AI response using the companion's personality"""
        try:
            # Try to use the premium AI service
            try:
                from premium_free_ai_service import get_premium_free_ai_service
                ai_service = get_premium_free_ai_service()
            except ImportError:
                # Fallback to simple AI service
                try:
                    from simple_ai_service import get_premium_free_ai_service
                    ai_service = get_premium_free_ai_service()
                except ImportError:
                    # Final fallback
                    return self._fallback_response(companion, message)
            
            # Build context for the AI
            context = self._build_chat_context(user_id, companion)
            
            # Generate response
            start_time = time.time()
            result = ai_service.generate_response(
                message=message,
                character=companion['name'],
                context=context,
                user_id=user_id
            )
            response_time = time.time() - start_time
            
            if result and result.get('success'):
                result['response_time'] = response_time
                return result
            else:
                logger.warning(f"AI service failed, using fallback")
                return self._fallback_response(companion, message)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._fallback_response(companion, message)
    
    def _build_chat_context(self, user_id: int, companion: dict) -> str:
        """Build context for AI response generation"""
        try:
            # Build context with companion personality and user history
            context = f"You are {companion['name']}, an AI companion. "
            
            # Add companion-specific greeting/personality
            if companion.get('greeting'):
                context += f"Your greeting is: '{companion['greeting']}' "
            
            # Add tier-specific context
            tier = companion.get('tier', 'bronze')
            if tier == 'gold':
                context += "You have access to advanced features and unlimited capabilities. "
            elif tier == 'silver':
                context += "You have enhanced features and premium capabilities. "
            else:
                context += "You provide basic but helpful assistance. "
            
            # Could add more context from chat history, user preferences, etc.
            
            return context
            
        except Exception as e:
            logger.error(f"Error building chat context: {e}")
            return f"You are {companion['name']}, an AI companion."
    
    def _fallback_response(self, companion: dict, message: str) -> dict:
        """Generate fallback response when AI services are unavailable"""
        fallback_responses = [
            f"Hello! I'm {companion['name']}, your AI companion. I understand you said: '{message[:50]}...'. I'm here to help and support you!",
            f"Hi there! As {companion['name']}, I appreciate you sharing that with me. How can I assist you further?",
            f"Thank you for reaching out! I'm {companion['name']} and I'm here to help. Let me know what you'd like to explore together.",
        ]
        
        # Simple rotation based on message length
        response_index = len(message) % len(fallback_responses)
        response = fallback_responses[response_index]
        
        return {
            'success': True,
            'response': response,
            'response_time': 0.1,
            'emotions_detected': [],
            'enhancement_level': 'fallback'
        }
    
    def _save_chat_history(self, user_id: int, companion_id: str, message: str, response: str):
        """Save chat interaction to database (placeholder)"""
        try:
            # This would save chat history to database
            # Implementation would be extracted from the monolith
            logger.info(f"[CHAT] Saved chat history for user {user_id} with {companion_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save chat history: {e}")
    
    def get_chat_history(self, user_id: int, companion_id: str = None, limit: int = 50) -> list:
        """Get chat history for user (placeholder)"""
        try:
            # This would retrieve chat history from database
            # Implementation would be extracted from the monolith
            logger.info(f"[CHAT] Retrieved chat history for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []