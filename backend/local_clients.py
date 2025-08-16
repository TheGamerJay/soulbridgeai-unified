"""
Local AI Client Wrappers
Handles local AI models with fallback to simple template-based responses
"""
import os
import logging
from typing import Dict, Any, Optional
from simple_ai_service import get_simple_ai_service

logger = logging.getLogger(__name__)

class LocalAIClient:
    """Local AI client with multiple fallback levels"""
    
    def __init__(self):
        self.simple_ai = get_simple_ai_service()
        self.premium_ai = None
        self.enhancement_level = "simple"
        
        # Try to load premium AI if available
        try:
            from backend.premium_free_ai_service import get_premium_free_ai_service
            self.premium_ai = get_premium_free_ai_service()
            self.enhancement_level = "premium"
            logger.info("✅ Premium local AI loaded")
        except Exception as e:
            logger.info(f"Premium AI not available, using simple AI: {e}")
        
        logger.info(f"Local AI client initialized with {self.enhancement_level} enhancement")
    
    def is_available(self) -> bool:
        """Local AI is always available as fallback"""
        return True
    
    def generate_companion_response(
        self,
        message: str,
        character: str = "Blayzo", 
        context: str = "",
        user_plan: str = "free"
    ) -> Dict[str, Any]:
        """
        Generate companion response using local AI
        
        Args:
            message: User message
            character: Character name
            context: Conversation context
            user_plan: User's subscription plan
            
        Returns:
            Response dict with success status and content
        """
        try:
            # Try premium AI first if available
            if self.premium_ai:
                try:
                    response = self.premium_ai.generate_response(
                        message=message,
                        character=character,
                        context=context,
                        user_id=f"local_{user_plan}"
                    )
                    
                    if response.get("success", False):
                        logger.info(f"Premium local AI response for {character}")
                        return response
                    else:
                        logger.warning("Premium AI failed, falling back to simple AI")
                        
                except Exception as e:
                    logger.warning(f"Premium AI error, falling back to simple AI: {e}")
            
            # Fallback to simple AI
            response = self.simple_ai.generate_response(
                message=message,
                character=character,
                context=context,
                user_id=f"simple_{user_plan}"
            )
            
            logger.info(f"Simple local AI response for {character}")
            return response
            
        except Exception as e:
            logger.error(f"All local AI failed: {e}")
            
            # Ultimate fallback - basic template
            return {
                "success": True,
                "response": f"Hello! I'm {character}, your AI companion. I'm here to listen and support you. What would you like to talk about?",
                "model": "fallback_template",
                "character": character,
                "enhancement_level": "fallback",
                "error_recovery": True
            }
    
    def get_available_characters(self) -> list:
        """Get list of available characters"""
        if self.premium_ai:
            try:
                # If premium AI has character method
                if hasattr(self.premium_ai, 'character_profiles'):
                    return list(self.premium_ai.character_profiles.keys())
            except Exception:
                pass
        
        # Default characters from simple AI
        if hasattr(self.simple_ai, 'character_responses'):
            return list(self.simple_ai.character_responses.keys())
        
        return ["Blayzo", "Blayzica", "Crimson", "Violet"]
    
    def get_client_status(self) -> Dict[str, Any]:
        """Get detailed client status"""
        status = {
            "client": "Local AI",
            "available": True,
            "enhancement_level": self.enhancement_level,
            "characters": self.get_available_characters(),
            "fallback_levels": []
        }
        
        # Add available fallback levels
        if self.premium_ai:
            status["fallback_levels"].append("premium_local_ai")
        
        status["fallback_levels"].extend(["simple_template_ai", "basic_fallback"])
        
        # Get stats from active services
        try:
            if self.premium_ai and hasattr(self.premium_ai, 'get_stats'):
                status["premium_stats"] = self.premium_ai.get_stats()
        except Exception:
            pass
        
        try:
            if hasattr(self.simple_ai, 'get_stats'):
                status["simple_stats"] = self.simple_ai.get_stats()
        except Exception:
            pass
        
        return status
    
    def warm_up(self) -> bool:
        """Warm up the AI models (useful for first-time loading)"""
        try:
            # Test both AI services
            test_message = "Hello"
            test_character = "Blayzo"
            
            if self.premium_ai:
                self.premium_ai.generate_response(test_message, test_character)
            
            self.simple_ai.generate_response(test_message, test_character)
            
            logger.info("Local AI models warmed up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error warming up local AI: {e}")
            return False

class HybridLocalClient:
    """Hybrid client that can switch between different local AI approaches"""
    
    def __init__(self):
        self.local_client = LocalAIClient()
        self.stats = {
            "requests": 0,
            "premium_used": 0,
            "simple_used": 0,
            "fallback_used": 0
        }
    
    def generate_response(
        self,
        message: str,
        character: str = "Blayzo",
        context: str = "",
        user_plan: str = "free",
        preferred_quality: str = "auto"  # auto, fast, quality
    ) -> Dict[str, Any]:
        """
        Generate response with quality preference
        
        Args:
            preferred_quality: 'fast' for simple AI, 'quality' for premium, 'auto' to decide
        """
        self.stats["requests"] += 1
        
        # Force simple AI for 'fast' preference
        if preferred_quality == "fast":
            response = self.local_client.simple_ai.generate_response(message, character, context)
            self.stats["simple_used"] += 1
            response["quality_mode"] = "fast"
            return response
        
        # Use full fallback chain for 'quality' or 'auto'
        response = self.local_client.generate_companion_response(message, character, context, user_plan)
        
        # Update stats based on what was actually used
        enhancement = response.get("enhancement_level", "unknown")
        if "premium" in enhancement:
            self.stats["premium_used"] += 1
        elif "simple" in enhancement or "template" in enhancement:
            self.stats["simple_used"] += 1
        else:
            self.stats["fallback_used"] += 1
        
        response["quality_mode"] = preferred_quality
        return response
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total = self.stats["requests"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "premium_ratio": self.stats["premium_used"] / total,
            "simple_ratio": self.stats["simple_used"] / total,
            "fallback_ratio": self.stats["fallback_used"] / total
        }

# Global instances
_local_client_instance = None
_hybrid_client_instance = None

def get_local_client() -> LocalAIClient:
    """Get the local AI client instance"""
    global _local_client_instance
    if _local_client_instance is None:
        _local_client_instance = LocalAIClient()
    return _local_client_instance

def get_hybrid_local_client() -> HybridLocalClient:
    """Get the hybrid local client instance"""
    global _hybrid_client_instance
    if _hybrid_client_instance is None:
        _hybrid_client_instance = HybridLocalClient()
    return _hybrid_client_instance

if __name__ == "__main__":
    # Test the local AI client
    client = get_local_client()
    
    print("Testing Local AI Client...")
    status = client.get_client_status()
    print(f"Status: {status}")
    
    print("\nWarming up models...")
    warmed = client.warm_up()
    print(f"Warm-up successful: {warmed}")
    
    print("\nTesting response generation...")
    
    test_cases = [
        ("Hello there!", "Blayzo"),
        ("I'm feeling stressed", "Blayzo"), 
        ("I got great news!", "Blayzica"),
        ("I need motivation", "Crimson"),
        ("I want to be creative", "Violet")
    ]
    
    for message, character in test_cases:
        response = client.generate_companion_response(message, character)
        print(f"\n{character}: '{message}'")
        print(f"Success: {response['success']}")
        print(f"Response: {response['response'][:100]}...")
        print(f"Model: {response.get('model', 'unknown')}")
        print(f"Enhancement: {response.get('enhancement_level', 'unknown')}")
    
    print("\n" + "="*50)
    print("Testing Hybrid Client...")
    
    hybrid = get_hybrid_local_client()
    
    # Test different quality modes
    for quality in ["fast", "auto", "quality"]:
        response = hybrid.generate_response(
            "How can I be more productive?",
            "Crimson",
            preferred_quality=quality
        )
        print(f"\nQuality mode '{quality}':")
        print(f"Response: {response['response'][:80]}...")
        print(f"Enhancement: {response.get('enhancement_level', 'unknown')}")
    
    print(f"\nPerformance stats: {hybrid.get_performance_stats()}")