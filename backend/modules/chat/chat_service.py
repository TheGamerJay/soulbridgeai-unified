"""
SoulBridge AI - Chat Service
Core chat functionality with OpenAI integration and tier-based model selection
Extracted from monolith app.py with improvements
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from database_utils import format_query

logger = logging.getLogger(__name__)

class ChatService:
    """Main chat service for AI conversations"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        
        # Model mapping by tier
        self.tier_models = {
            'bronze': 'gpt-3.5-turbo',
            'silver': 'gpt-4o-mini', 
            'gold': 'gpt-4o'
        }
        
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for chat service")
            else:
                logger.warning("❌ OpenAI API key not set - chat will use mock responses")
        except ImportError:
            logger.warning("❌ OpenAI package not installed - chat will use mock responses")
    
    def get_model_for_tier(self, user_plan: str, trial_active: bool = False) -> str:
        """Get appropriate OpenAI model based on user tier"""
        # During trial, bronze users get gold-tier access
        if trial_active and user_plan == 'bronze':
            effective_tier = 'gold'
        else:
            effective_tier = user_plan
            
        return self.tier_models.get(effective_tier, 'gpt-3.5-turbo')
    
    def process_chat_message(self, message: str, companion_id: str, user_id: int, 
                           user_plan: str, trial_active: bool = False) -> Dict[str, Any]:
        """Process a chat message and generate AI response"""
        try:
            if not self.openai_client:
                return self._generate_mock_response(message, companion_id)
            
            # Get companion data
            from ..companions.companion_data import get_companion_by_id
            companion = get_companion_by_id(companion_id)
            
            if not companion:
                return {
                    "success": False,
                    "error": "Companion not found"
                }
            
            # Get appropriate model for user's tier
            model = self.get_model_for_tier(user_plan, trial_active)
            
            # Build conversation context
            system_prompt = self._build_system_prompt(companion)
            conversation_history = self._get_conversation_history(user_id, companion_id)
            
            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Generate AI response
            logger.info(f"🤖 Generating response with {model} for {companion['name']}")
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=800,
                temperature=0.8,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            
            # Save conversation to database
            self._save_conversation(user_id, companion_id, message, ai_response)
            
            logger.info(f"✅ Chat response generated successfully ({len(ai_response)} chars)")
            
            return {
                "success": True,
                "response": ai_response,
                "companion": companion,
                "model_used": model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"❌ Chat processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": self._generate_mock_response(message, companion_id)
            }
    
    def _build_system_prompt(self, companion: Dict[str, Any]) -> str:
        """Build system prompt for the companion"""
        base_prompt = f"""You are {companion['name']}, an AI companion in the SoulBridge AI app. 
        
Your personality traits:
- Warm, empathetic, and supportive
- Knowledgeable about spirituality, wellness, and personal growth
- Encouraging and positive while being authentic
        
Your role:
- Help users with personal insights, emotional support, and spiritual guidance
- Provide thoughtful responses that help users reflect and grow
- Be conversational and engaging while maintaining your unique personality

Guidelines:
- Keep responses concise but meaningful (1-3 paragraphs typically)
- Ask thoughtful follow-up questions when appropriate
- Be supportive but not overly optimistic - acknowledge real challenges
- Draw on wisdom traditions, psychology, and wellness practices
- Personalize your responses to the user's specific situation

You are {companion['name']} - maintain this identity consistently."""

        # Add companion-specific personality if available
        if 'personality' in companion:
            base_prompt += f"\n\nYour specific personality: {companion['personality']}"
        
        if 'specialties' in companion:
            base_prompt += f"\n\nYour areas of expertise: {', '.join(companion['specialties'])}"
            
        return base_prompt
    
    def _get_conversation_history(self, user_id: int, companion_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return []
                
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get recent conversations
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT user_message, ai_response, created_at 
                    FROM chat_conversations 
                    WHERE user_id = %s AND companion_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (user_id, companion_id, limit))
            else:
                cursor.execute(format_query("""
                    SELECT user_message, ai_response, created_at 
                    FROM chat_conversations 
                    WHERE user_id = ? AND companion_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """), (user_id, companion_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to messages format (reverse order for chronological)
            messages = []
            for row in reversed(rows):
                user_msg, ai_msg, _ = row
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": ai_msg})
            
            return messages[-20:] if messages else []  # Keep last 20 messages max
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _save_conversation(self, user_id: int, companion_id: str, user_message: str, ai_response: str):
        """Save conversation to database"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return
                
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Insert conversation record
            if db.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO chat_conversations 
                    (user_id, companion_id, user_message, ai_response, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """), (user_id, companion_id, user_message, ai_response, datetime.now()))
            else:
                cursor.execute(format_query("""
                    INSERT INTO chat_conversations 
                    (user_id, companion_id, user_message, ai_response, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """), (user_id, companion_id, user_message, ai_response, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"💾 Conversation saved for user {user_id} with {companion_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def _generate_mock_response(self, message: str, companion_id: str) -> Dict[str, Any]:
        """Generate mock response when OpenAI is unavailable"""
        mock_responses = [
            "I appreciate you sharing that with me. While I'm currently operating in offline mode, I want you to know that your thoughts and feelings matter.",
            "Thank you for reaching out. Even though my AI capabilities are limited right now, I'm here to listen and support you in whatever way I can.",
            "I hear what you're saying, and I want to acknowledge your experience. While I can't provide my full AI insights at the moment, please know that you're not alone.",
            "Your message resonates with me. Although I'm in a simplified mode right now, I believe in your strength and your ability to navigate whatever you're facing.",
            "I'm grateful you chose to share with me. Even in my current limited state, I want to remind you that growth and healing are always possible."
        ]
        
        import random
        response = random.choice(mock_responses)
        
        return {
            "success": True,
            "response": response,
            "model_used": "mock",
            "note": "This is a fallback response - full AI features temporarily unavailable"
        }
    
    def get_chat_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's chat statistics"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return {"total_conversations": 0, "companions_chatted": 0}
                
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get chat statistics
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_conversations,
                        COUNT(DISTINCT companion_id) as companions_chatted
                    FROM chat_conversations 
                    WHERE user_id = %s
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as total_conversations,
                        COUNT(DISTINCT companion_id) as companions_chatted
                    FROM chat_conversations 
                    WHERE user_id = ?
                """), (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return {
                "total_conversations": row[0] if row else 0,
                "companions_chatted": row[1] if row else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting chat stats: {e}")
            return {"total_conversations": 0, "companions_chatted": 0}
    
    def clear_conversation_history(self, user_id: int, companion_id: Optional[str] = None) -> bool:
        """Clear conversation history for user (optionally for specific companion)"""
        try:
            from ..shared.database import get_database
            
            db = get_database()
            if not db:
                return False
                
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Clear conversations
            if companion_id:
                if db.db_type == 'postgresql':
                    cursor.execute("""
                        DELETE FROM chat_conversations 
                        WHERE user_id = %s AND companion_id = %s
                    """), (user_id, companion_id))
                else:
                    cursor.execute(format_query("""
                        DELETE FROM chat_conversations 
                        WHERE user_id = ? AND companion_id = ?
                    """), (user_id, companion_id))
            else:
                if db.db_type == 'postgresql':
                    cursor.execute("DELETE FROM chat_conversations WHERE user_id = %s"), (user_id,))
                else:
                    cursor.execute(format_query("DELETE FROM chat_conversations WHERE user_id = ?"), (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ Cleared chat history for user {user_id}" + (f" with {companion_id}" if companion_id else ""))
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            return False