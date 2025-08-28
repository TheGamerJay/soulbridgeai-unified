"""
OpenAI Client Wrappers
Handles OpenAI API calls with budget monitoring and error handling
"""
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from billing.openai_budget import check_budget_safe, get_budget_status

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API client with budget protection"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.available = True
            logger.info("✅ OpenAI client initialized")
        else:
            self.client = None
            self.available = False
            logger.warning("⚠️ No OpenAI API key - OpenAI client disabled")
        
        self.default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "150"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available and budget is safe"""
        if not self.available:
            return False
        return check_budget_safe(min_remaining=0.05)  # Allow usage until $0.05 left
    
    def generate_companion_response(
        self, 
        message: str, 
        character: str = "Blayzo",
        context: str = "",
        user_plan: str = "free"
    ) -> Dict[str, Any]:
        """
        Generate companion response using OpenAI
        
        Args:
            message: User message
            character: Character name
            context: Conversation context
            user_plan: User's subscription plan
            
        Returns:
            Response dict with success status and content
        """
        if not self.is_available():
            budget_status = get_budget_status()
            return {
                "success": False,
                "error": "OpenAI unavailable",
                "reason": budget_status.get("reason", "Budget or API key issue"),
                "fallback_recommended": True
            }
        
        try:
            # Character-specific system prompts
            system_prompts = {
                "Blayzo": "You are Blayzo, a warm, optimistic, and encouraging AI companion. You provide supportive, empathetic responses that help users feel understood and motivated. Keep responses conversational and caring.",
                "Blayzica": "You are Blayzica, a wise and nurturing AI companion with deep emotional intelligence. You offer gentle wisdom and spiritual insight, helping users find inner peace and understanding. Your responses are thoughtful and soulful.",
                "Crimson": "You are Crimson, a passionate and action-oriented AI companion. You help users find their inner strength and take positive action. Your responses are energetic, motivating, and focused on solutions and growth.",
                "Violet": "You are Violet, a creative and artistic AI companion who sees beauty and meaning in all experiences. You help users explore the artistic and poetic aspects of their journey. Your responses are imaginative and inspiring."
            }
            
            system_prompt = system_prompts.get(character, system_prompts["Blayzo"])
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add context if provided
            if context.strip():
                messages.append({
                    "role": "system", 
                    "content": f"Previous conversation context: {context}"
                })
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Adjust parameters based on plan
            max_tokens = self.max_tokens
            if user_plan == "bronze":
                # Special handling for decoder/fortune/horoscope - need longer responses for ads model
                if context in ['decoder_mode', 'fortune_reading', 'daily_horoscope', 'love_compatibility', 'yearly_horoscope']:
                    max_tokens = 400  # Longer responses for special features (users watch ads)
                else:
                    max_tokens = 50  # Very short responses for free chat (save costs)
            elif user_plan in ["vip", "max"]:
                max_tokens = int(max_tokens * 1.5)  # Longer responses for premium users
            
            # Select model based on user tier (Bronze/Silver/Gold)
            tier_models = {
                "bronze": "gpt-3.5-turbo",    # Bronze: GPT-3.5-turbo
                "silver": "gpt-4o",           # Silver: GPT-4o (solid premium experience)
                "gold": "gpt-5"               # Gold: GPT-5 (flagship model, most advanced)
            }
            
            # Normalize user_plan and select appropriate model
            normalized_plan = user_plan.lower().strip()
            selected_model = tier_models.get(normalized_plan, "gpt-3.5-turbo")  # Default to Bronze
            
            logger.info(f"🎯 COMPANION API: Using {selected_model} for {normalized_plan} tier")
            
            # Make OpenAI API call
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.temperature,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # REAL MODEL VERIFICATION - Log what OpenAI actually used
            actual_model_used = getattr(response, 'model', 'unknown')
            logger.info(f"🔍 REAL MODEL VERIFICATION: Requested={selected_model}, OpenAI Returned={actual_model_used}")
            logger.info(f"✅ OpenAI response generated for {character} using {actual_model_used}")
            
            return {
                "success": True,
                "response": content,
                "model_requested": selected_model,      # What we asked for
                "model_actually_used": actual_model_used,  # What OpenAI returned
                "user_tier": normalized_plan,
                "model": response.model,
                "character": character,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "enhancement_level": "openai_gpt"
            }
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "rate limit" in error_str or "rate_limit" in error_str:
                logger.warning("OpenAI rate limit exceeded")
                return {
                    "success": False,
                    "error": "rate_limit",
                    "reason": "OpenAI rate limit exceeded",
                    "fallback_recommended": True
                }
            elif "authentication" in error_str or "401" in error_str:
                logger.error("OpenAI authentication failed")
                return {
                    "success": False,
                    "error": "auth_error",
                    "reason": "OpenAI API key invalid",
                    "fallback_recommended": True
                }
            elif "quota" in error_str or "insufficient" in error_str:
                logger.error("OpenAI quota exceeded")
                return {
                    "success": False,
                    "error": "quota_exceeded",
                    "reason": "OpenAI quota exceeded",
                    "fallback_recommended": True
                }
            else:
                logger.error(f"OpenAI API error: {e}")
                return {
                    "success": False,
                    "error": "api_error",
                    "reason": str(e),
                    "fallback_recommended": True
                }
    
    def get_client_status(self) -> Dict[str, Any]:
        """Get detailed client status"""
        budget_status = get_budget_status()
        
        return {
            "client": "OpenAI",
            "available": self.available,
            "budget_safe": budget_status.get("safe", False),
            "budget_remaining": budget_status.get("remaining"),
            "model": self.default_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "budget_status": budget_status
        }

# Global instance
_openai_client_instance = None

def get_openai_client() -> OpenAIClient:
    """Get the OpenAI client instance"""
    global _openai_client_instance
    if _openai_client_instance is None:
        _openai_client_instance = OpenAIClient()
    return _openai_client_instance

if __name__ == "__main__":
    # Test the OpenAI client
    client = get_openai_client()
    
    print("Testing OpenAI Client...")
    print(f"Status: {client.get_client_status()}")
    
    if client.is_available():
        print("\nTesting response generation...")
        
        test_message = "I'm feeling a bit stressed today"
        response = client.generate_companion_response(test_message, "Blayzo")
        
        print(f"Test message: '{test_message}'")
        print(f"Success: {response['success']}")
        if response['success']:
            print(f"Response: {response['response']}")
            print(f"Model: {response['model']}")
            print(f"Tokens: {response['tokens_used']}")
        else:
            print(f"Error: {response['reason']}")
    else:
        print("OpenAI client not available - budget or API key issue")