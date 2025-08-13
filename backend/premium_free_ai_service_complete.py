# Complete the premium_free_ai_service.py

User: {message}
{character}:"""
        
        return prompt
    
    def _enhance_response(self, ai_response: str, character: str, profile: Dict, emotions: List[str], user_message: str) -> str:
        """Enhance the AI response with premium features"""
        if not ai_response or len(ai_response.strip()) < 10:
            # Generate premium fallback
            return self._create_enhanced_fallback(character, profile, emotions)
        
        # Clean the response
        cleaned = self._clean_response(ai_response, character)
        
        # Add emotion-specific empathy if detected
        if emotions and cleaned:
            empathy_response = self._add_empathy_response(cleaned, character, profile, emotions)
            if empathy_response != cleaned:
                cleaned = empathy_response
        
        # Add premium enhancements
        enhanced = self._add_premium_touches(cleaned, character, profile, emotions, user_message)
        
        return enhanced
    
    def _add_empathy_response(self, response: str, character: str, profile: Dict, emotions: List[str]) -> str:
        """Add emotion-specific empathetic responses"""
        empathy_responses = profile.get("empathy_responses", {})
        
        # Find the most relevant emotion
        for emotion in emotions:
            if emotion in empathy_responses:
                empathy_text = empathy_responses[emotion]
                # Integrate empathy naturally
                if len(response) < 50:  # Short response, lead with empathy
                    return f"{empathy_text} {response}"
                else:
                    # Longer response, blend empathy
                    return f"{empathy_text} {response}"
        
        return response
    
    def _add_premium_touches(self, response: str, character: str, profile: Dict, emotions: List[str], user_message: str) -> str:
        """Add premium touches to make the response feel more personal and caring"""
        if not response:
            return response
        
        # Sometimes add a follow-up question (30% chance)
        if random.random() < 0.3:
            questions = self.enhancement_patterns["questions"]
            question = random.choice(questions)
            if not response.endswith("?"):
                response += f" {question}"
        
        # Sometimes add validation (40% chance if emotions detected)
        if emotions and random.random() < 0.4:
            validations = self.enhancement_patterns["validations"]
            validation = random.choice(validations)
            response = f"{validation} {response}"
        
        # Sometimes add encouragement (25% chance)
        if random.random() < 0.25:
            encouragements = self.enhancement_patterns["encouragements"]
            encouragement = random.choice(encouragements)
            response += f" {encouragement}"
        
        return response
    
    def _detect_emotions(self, message: str) -> List[str]:
        """Detect emotions in the user message"""
        message_lower = message.lower()
        detected = []
        
        for emotion, patterns in self.emotion_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                detected.append(emotion)
        
        return detected
    
    def _is_greeting(self, message: str) -> bool:
        """Check if the message is a greeting"""
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "howdy", "greetings"]
        message_lower = message.lower().strip()
        
        # Check if message starts with greeting
        for greeting in greetings:
            if message_lower.startswith(greeting):
                return True
        
        # Check if message is just a greeting
        if message_lower in greetings:
            return True
        
        return False
    
    def _clean_response(self, response: str, character: str) -> str:
        """Clean and format the AI response"""
        if not response:
            return ""
        
        # Remove character name if it appears
        if response.startswith(character):
            response = response[len(character):].lstrip(":").strip()
        
        # Remove common artifacts
        response = response.replace("Human:", "").replace("User:", "").replace("AI:", "")
        
        # Clean up extra spaces and newlines
        response = " ".join(response.split())
        
        # Ensure proper sentence ending
        if response and not response[-1] in ".!?":
            response += "."
        
        return response
    
    def _create_enhanced_fallback(self, character: str, profile: Dict, emotions: List[str]) -> str:
        """Create an enhanced fallback response"""
        greeting = profile.get("greeting_style", f"Hello! I'm {character}, and I'm here to help you.")
        
        if emotions:
            emotion_text = f" I can sense you're feeling {', '.join(emotions[:2])}, and I want you to know that's completely okay."
            return greeting + emotion_text
        
        return greeting
    
    def _create_premium_fallback(self, message: str, character: str, start_time: float, error: str = "") -> Dict[str, Any]:
        """Create premium fallback response when AI fails"""
        profile = self.character_profiles.get(character, self.character_profiles["Blayzo"])
        emotions = self._detect_emotions(message)
        response = self._create_enhanced_fallback(character, profile, emotions)
        
        return {
            "success": True,  # Still successful from user perspective
            "response": response,
            "model": "premium_fallback",
            "response_time": time.time() - start_time,
            "character": character,
            "emotions_detected": emotions,
            "is_greeting": False,
            "enhancement_level": "fallback"
        }
    
    def _update_conversation_memory(self, user_id: str, user_message: str, ai_response: str):
        """Update conversation memory for context"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        self.conversation_memory[user_id].append({
            "user": user_message[:150],
            "ai": ai_response[:150],
            "timestamp": datetime.now()
        })
        
        # Keep only last 3 exchanges
        if len(self.conversation_memory[user_id]) > 3:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-3:]
    
    def _get_conversation_history(self, user_id: str) -> str:
        """Get conversation history for context"""
        if user_id not in self.conversation_memory:
            return ""
        
        recent = self.conversation_memory[user_id][-1:]  # Just the last exchange
        if not recent:
            return ""
        
        # Only include if recent (within 30 minutes)
        exchange = recent[0]
        if datetime.now() - exchange["timestamp"] < timedelta(minutes=30):
            return f"Previously you said: {exchange['user'][:50]}..."
        
        return ""
    
    def _cleanup_memory(self):
        """Clean up memory and old conversations"""
        try:
            import torch
            import gc
            
            # Clean old conversations
            cutoff = datetime.now() - timedelta(hours=2)  # 2 hours
            for user_id in list(self.conversation_memory.keys()):
                self.conversation_memory[user_id] = [
                    exchange for exchange in self.conversation_memory[user_id]
                    if exchange["timestamp"] > cutoff
                ]
                if not self.conversation_memory[user_id]:
                    del self.conversation_memory[user_id]
            
            # GPU cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            gc.collect()
            self.last_cleanup = time.time()
            logger.info("Premium AI memory cleanup completed")
            
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_response_time = (self.total_response_time / self.request_count) if self.request_count > 0 else 0
        
        return {
            "service": "Premium Free AI",
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "request_count": self.request_count,
            "avg_response_time": avg_response_time,
            "active_conversations": len(self.conversation_memory),
            "characters_supported": len(self.character_profiles),
            "emotion_detection": True,
            "conversation_memory": True,
            "premium_enhancements": True
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the premium service"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "healthy": False}
            
            test_result = self.generate_response("Hello, how are you?", "Blayzo", "", "health_check")
            
            return {
                "status": "healthy" if test_result["success"] else "degraded",
                "healthy": test_result["success"],
                "response_time": test_result.get("response_time", 0),
                "premium_features": test_result.get("enhancement_level") == "premium",
                "last_test": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }


# Global instance management
_premium_ai_instance = None
_premium_instance_lock = threading.Lock()

def get_premium_free_ai_service() -> PremiumFreeAIService:
    """Get the global Premium Free AI service instance"""
    global _premium_ai_instance
    
    with _premium_instance_lock:
        if _premium_ai_instance is None:
            _premium_ai_instance = PremiumFreeAIService()
        return _premium_ai_instance


# Test the premium service
if __name__ == "__main__":
    print("Testing Premium Free AI Service...")
    
    ai_service = get_premium_free_ai_service()
    
    test_scenarios = [
        ("Hello!", "Blayzo"),
        ("I'm really stressed about work and feeling overwhelmed", "Blayzo"),
        ("I just got amazing news about my promotion!", "Blayzica"),
        ("I feel so confused about my relationship", "Crimson"),
        ("I want to be more creative in my life", "Violet"),
        ("I'm feeling lonely and isolated lately", "Blayzo"),
    ]
    
    for i, (message, character) in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {character} responding to: '{message}'")
        print('='*60)
        
        result = ai_service.generate_response(message, character, "", f"test_user_{i}")
        
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print(f"Time: {result['response_time']:.2f}s")
        print(f"Emotions detected: {result['emotions_detected']}")
        print(f"Enhancement level: {result['enhancement_level']}")
        
        if result.get('is_greeting'):
            print("Type: Greeting response")
    
    print(f"\n{'='*60}")
    print("SERVICE STATISTICS")
    print('='*60)
    stats = ai_service.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print(f"\n{'='*60}")
    print("HEALTH CHECK")
    print('='*60)
    health = ai_service.health_check()
    for key, value in health.items():
        print(f"{key}: {value}")