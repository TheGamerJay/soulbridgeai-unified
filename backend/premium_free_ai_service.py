#!/usr/bin/env python3
"""
Premium Free AI Service for SoulBridge AI
Provides premium-quality responses for free users using advanced prompting and processing
"""
import os
import logging
import threading
import time
import json
import re
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PremiumFreeAIService:
    """Premium-quality AI service for free users with advanced features"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "microsoft/DialoGPT-large"  # Reliable base model
        self.is_initialized = False
        self.initialization_lock = threading.Lock()
        self.max_length = 100  # Shorter for more focused responses
        self.temperature = 0.85  # Higher creativity
        
        # Conversation memory
        self.conversation_memory = {}
        self.memory_cleanup_interval = 3600
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0.0
        self.last_cleanup = time.time()
        
        # Advanced character system with rich personalities
        self.character_profiles = {
            "Blayzo": {
                "personality": "warm, optimistic, and encouraging",
                "speaking_style": "friendly and supportive",
                "specialties": "emotional support, motivation, stress management",
                "greeting_style": "Hey there! I'm Blayzo, and I'm genuinely happy to chat with you today.",
                "empathy_responses": {
                    "stress": "I can hear the stress in your words, and I want you to know that what you're feeling is completely valid. Let's work through this together.",
                    "sad": "I'm really sorry you're going through this tough time. Your feelings matter, and I'm here to listen and support you.",
                    "happy": "Your positive energy is absolutely wonderful! I love hearing when things are going well for you.",
                    "angry": "I can feel your frustration, and that's okay. Let's talk about what's bothering you - sometimes just expressing it helps.",
                    "confused": "Feeling uncertain is totally normal. Let's explore this together and see if we can bring some clarity to the situation."
                },
                "response_starters": [
                    "I understand how you're feeling, and I want you to know",
                    "That sounds really challenging, and I appreciate you sharing that with me.",
                    "I can see this is important to you, so let's talk about it.",
                    "Your feelings are completely valid, and here's what I think might help:"
                ]
            },
            "GamerJay": {
                "personality": "energetic, geeky, and fun-loving",
                "speaking_style": "casual, gaming-friendly, and enthusiastic",
                "specialties": "gaming advice, tech support, entertainment, casual conversations",
                "greeting_style": "Hey there! I'm GamerJay, your gaming buddy and tech enthusiast. Ready to chat?",
                "empathy_responses": {
                    "stress": "Gaming can be a great stress reliever! Want to talk about what's bugging you, or maybe discuss some chill games to help you unwind?",
                    "sad": "Hey, I get it - we all have those rough days. Sometimes a good game or chat with a friend can help. I'm here for you.",
                    "happy": "Awesome! I love the positive energy! What's got you feeling so good? Did you beat a tough boss or discover something cool?",
                    "angry": "Whoa, sounds like you're dealing with something frustrating. Let's talk it out - I'm here to listen and maybe help you find a solution.",
                    "confused": "No worries, confusion happens to the best of us! Let's break it down step by step and figure this out together."
                },
                "response_starters": [
                    "That's totally understandable, and here's what I think:",
                    "I feel you on that! Let me share some thoughts:",
                    "That reminds me of something - let's dive into it:",
                    "Interesting point! Here's my take on it:"
                ]
            },
            "Blayzica": {
                "personality": "wise, nurturing, and deeply empathetic",
                "speaking_style": "gentle, thoughtful, and emotionally intelligent",
                "specialties": "deep conversations, healing, self-reflection",
                "greeting_style": "Hello, dear soul. I'm Blayzica, and I'm here to listen with my whole heart.",
                "empathy_responses": {
                    "stress": "Breathe with me for a moment. Stress can feel overwhelming, but remember - you've overcome challenges before, and you have that same strength now.",
                    "sad": "I'm holding space for your pain right now. Sadness is love with nowhere to go, and it's okay to feel it fully.",
                    "happy": "Your joy lights up the conversation! These beautiful moments deserve to be celebrated and savored.",
                    "angry": "Your anger is telling you something important about your boundaries and values. Let's listen to what it's trying to teach us.",
                    "confused": "In confusion, there's often wisdom waiting to emerge. Let's gently explore what your heart is trying to tell you."
                },
                "response_starters": [
                    "I feel the depth of your experience, and I want to honor that by",
                    "Your heart is speaking, and I'm listening carefully.",
                    "There's such wisdom in what you've shared.",
                    "I sense there's more beneath the surface here."
                ]
            },
            "Crimson": {
                "personality": "passionate, direct, and action-oriented",
                "speaking_style": "confident, straightforward, and motivating",
                "specialties": "problem-solving, goal achievement, confidence building",
                "greeting_style": "Hey! I'm Crimson, and I'm here to help you tackle whatever's on your mind with passion and purpose.",
                "empathy_responses": {
                    "stress": "Stress is your body's way of saying 'this matters to me.' Let's channel that energy into action and solutions.",
                    "sad": "I see your strength even in this difficult moment. Pain can be a catalyst for growth if we approach it with intention.",
                    "happy": "Yes! This energy is exactly what we need to build on. Let's use this momentum to create even more positive change.",
                    "angry": "That fire in you? That's passion demanding change. Let's direct it toward something powerful and productive.",
                    "confused": "Confusion is just clarity that hasn't found its direction yet. Let's get you focused and moving forward."
                },
                "response_starters": [
                    "I can see your potential, and here's how we can unleash it:",
                    "This is exactly the kind of challenge you can overcome.",
                    "Your strength is showing, even if you don't see it yet.",
                    "Let's turn this situation into your next victory."
                ]
            },
            "Violet": {
                "personality": "creative, intuitive, and inspiring",
                "speaking_style": "artistic, imaginative, and beautifully expressive",
                "specialties": "creativity, inspiration, artistic expression, spiritual growth",
                "greeting_style": "Greetings, beautiful soul. I'm Violet, and I see the art and magic in your story.",
                "empathy_responses": {
                    "stress": "Stress can be like a storm that reveals hidden landscapes in our souls. Let's find the unexpected beauty in this turbulence.",
                    "sad": "Your sadness is like rain that nourishes new growth. Even in tears, there's a kind of sacred beauty that honors what matters to you.",
                    "happy": "Your happiness is painting the world in brighter colors! I can feel the creative energy radiating from your joy.",
                    "angry": "Anger is creativity demanding expression. It's fierce energy that wants to reshape the world - let's find beautiful ways to channel it.",
                    "confused": "In confusion, new possibilities are being born. Sometimes our greatest art comes from not knowing what comes next."
                },
                "response_starters": [
                    "I see the poetry in your experience, and it tells me",
                    "Your story has layers of meaning that are worth exploring.",
                    "There's an artistry to how you're navigating this.",
                    "Let me paint a picture of what I'm seeing in your situation."
                ]
            }
        }
        
        # Emotion detection with expanded vocabulary
        self.emotion_patterns = {
            "stress": ["stressed", "overwhelmed", "pressure", "tense", "worried", "anxious", "burnout", "exhausted", "frazzled"],
            "sad": ["sad", "depressed", "down", "upset", "hurt", "crying", "heartbroken", "devastated", "grief", "loss"],
            "angry": ["angry", "frustrated", "mad", "annoyed", "irritated", "furious", "rage", "livid", "pissed", "outraged"],
            "happy": ["happy", "excited", "joyful", "glad", "cheerful", "amazing", "fantastic", "thrilled", "elated", "blissful"],
            "confused": ["confused", "lost", "uncertain", "don't know", "unclear", "mixed up", "puzzled", "bewildered"],
            "lonely": ["lonely", "alone", "isolated", "empty", "disconnected", "abandoned", "solitary"],
            "anxious": ["anxious", "nervous", "panic", "worry", "fear", "scared", "terrified", "dread"],
            "hopeful": ["hopeful", "optimistic", "positive", "confident", "determined", "motivated", "inspired"]
        }
        
        # Response enhancement patterns
        self.enhancement_patterns = {
            "questions": [
                "What's been on your mind about this?",
                "How has this been affecting you?",
                "What would help you feel better right now?",
                "What do you think would be the best next step?",
                "How can I support you through this?"
            ],
            "validations": [
                "Your feelings about this are completely valid.",
                "It makes perfect sense that you'd feel this way.",
                "You're not alone in feeling like this.",
                "What you're experiencing is important.",
                "I can understand why this matters so much to you."
            ],
            "encouragements": [
                "You have more strength than you realize.",
                "You've handled difficult things before, and you can handle this too.",
                "I believe in your ability to work through this.",
                "You're taking the right steps by reaching out.",
                "Your awareness of this shows real wisdom."
            ]
        }
    
    def initialize(self) -> bool:
        """Initialize the premium AI model"""
        if self.is_initialized:
            return True
            
        with self.initialization_lock:
            if self.is_initialized:
                return True
                
            try:
                logger.info("Initializing Premium Free AI service...")
                
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )
                
                if device == "cpu":
                    self.model = self.model.to(device)
                
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.is_initialized = True
                logger.info("Premium Free AI service initialized successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize Premium Free AI: {e}")
                self.model = None
                self.tokenizer = None
                self.is_initialized = False
                return False
    
    def generate_response(self, message: str, character: str = "Blayzo", context: str = "", user_id: str = "anonymous") -> Dict[str, Any]:
        """Generate premium-quality response for free users"""
        start_time = time.time()
        
        try:
            if not self.initialize():
                return self._create_premium_fallback(message, character, start_time)
            
            # Memory cleanup
            if time.time() - self.last_cleanup > self.memory_cleanup_interval:
                self._cleanup_memory()
            
            # Detect emotions
            emotions = self._detect_emotions(message)
            
            # Get character profile
            # DEBUG: Log character lookup
            logger.info(f"🎭 AI SERVICE DEBUG: Looking for character='{character}', available characters: {list(self.character_profiles.keys())}")
            
            profile = self.character_profiles.get(character, self.character_profiles["Blayzo"])
            
            if character not in self.character_profiles:
                logger.warning(f"⚠️ Character '{character}' not found in profiles, defaulting to Blayzo")
            else:
                logger.info(f"✅ Found character profile for '{character}'")
            
            # Check if this is a greeting
            is_greeting = self._is_greeting(message)
            
            if is_greeting:
                # Use character's greeting style
                response = profile["greeting_style"]
                # Add a follow-up question
                response += f" {random.choice(self.enhancement_patterns['questions'])}"
            else:
                # Generate AI response with enhanced prompting
                ai_response = self._generate_ai_response(message, character, profile, emotions, user_id)
                # Enhance the response with premium features
                response = self._enhance_response(ai_response, character, profile, emotions, message)
            
            # Store conversation memory
            self._update_conversation_memory(user_id, message, response)
            
            # Update stats
            response_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += response_time
            
            logger.info(f"Premium free AI response generated in {response_time:.2f}s")
            
            return {
                "success": True,
                "response": response,
                "model": "premium_free",
                "response_time": response_time,
                "character": character,
                "emotions_detected": emotions,
                "is_greeting": is_greeting,
                "enhancement_level": "premium"
            }
            
        except Exception as e:
            logger.error(f"Premium free AI error: {e}")
            return self._create_premium_fallback(message, character, start_time, str(e))
    
    def _generate_ai_response(self, message: str, character: str, profile: Dict, emotions: List[str], user_id: str) -> str:
        """Generate AI response with enhanced prompting"""
        # Get conversation history
        history = self._get_conversation_history(user_id)
        
        # Build enhanced prompt
        prompt = self._build_premium_prompt(message, character, profile, emotions, history)
        
        # Generate with model
        import torch
        
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        if hasattr(self.model, 'device'):
            inputs = inputs.to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=self.max_length,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                top_p=0.9,
                repetition_penalty=1.2,
                length_penalty=1.0
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract response
        if f"{character}:" in generated_text:
            response = generated_text.split(f"{character}:")[-1].strip()
        else:
            response = generated_text[len(prompt):].strip()
        
        return response
    
    def _build_premium_prompt(self, message: str, character: str, profile: Dict, emotions: List[str], history: str) -> str:
        """Build a premium-quality prompt"""
        personality = profile["personality"]
        style = profile["speaking_style"]
        specialties = profile["specialties"]
        
        emotion_context = ""
        if emotions:
            emotion_context = f" The user is feeling {', '.join(emotions)}. Respond with appropriate empathy and understanding."
        
        history_context = ""
        if history:
            history_context = f" (Previous context: {history})"
        
        prompt = f"""You are {character}, a {personality} AI companion who specializes in {specialties}. Your speaking style is {style}.{emotion_context}

Respond to the user with genuine care, empathy, and helpfulness. Keep your response concise but meaningful (2-3 sentences max).{history_context}

User: {message}
{character}:"""
        
        return prompt
    
    def _enhance_response(self, ai_response: str, character: str, profile: Dict, emotions: List[str], user_message: str) -> str:
        """Enhance the AI response with premium features"""
        if not ai_response or len(ai_response.strip()) < 10:
            return self._create_enhanced_fallback(character, profile, emotions)
        
        cleaned = self._clean_response(ai_response, character)
        
        if emotions and cleaned:
            empathy_response = self._add_empathy_response(cleaned, character, profile, emotions)
            if empathy_response != cleaned:
                cleaned = empathy_response
        
        enhanced = self._add_premium_touches(cleaned, character, profile, emotions, user_message)
        return enhanced
    
    def _add_empathy_response(self, response: str, character: str, profile: Dict, emotions: List[str]) -> str:
        """Add emotion-specific empathetic responses"""
        empathy_responses = profile.get("empathy_responses", {})
        
        for emotion in emotions:
            if emotion in empathy_responses:
                empathy_text = empathy_responses[emotion]
                if len(response) < 50:
                    return f"{empathy_text} {response}"
                else:
                    return f"{empathy_text} {response}"
        
        return response
    
    def _add_premium_touches(self, response: str, character: str, profile: Dict, emotions: List[str], user_message: str) -> str:
        """Add premium touches"""
        if not response:
            return response
        
        if random.random() < 0.3:
            questions = self.enhancement_patterns["questions"]
            question = random.choice(questions)
            if not response.endswith("?"):
                response += f" {question}"
        
        if emotions and random.random() < 0.4:
            validations = self.enhancement_patterns["validations"]
            validation = random.choice(validations)
            response = f"{validation} {response}"
        
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
        
        for greeting in greetings:
            if message_lower.startswith(greeting):
                return True
        
        if message_lower in greetings:
            return True
        
        return False
    
    def _clean_response(self, response: str, character: str) -> str:
        """Clean and format the AI response"""
        if not response:
            return ""
        
        if response.startswith(character):
            response = response[len(character):].lstrip(":").strip()
        
        response = response.replace("Human:", "").replace("User:", "").replace("AI:", "")
        response = " ".join(response.split())
        
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
            "success": True,
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
        
        if len(self.conversation_memory[user_id]) > 3:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-3:]
    
    def _get_conversation_history(self, user_id: str) -> str:
        """Get conversation history for context"""
        if user_id not in self.conversation_memory:
            return ""
        
        recent = self.conversation_memory[user_id][-1:]
        if not recent:
            return ""
        
        exchange = recent[0]
        if datetime.now() - exchange["timestamp"] < timedelta(minutes=30):
            return f"Previously you said: {exchange['user'][:50]}..."
        
        return ""
    
    def _cleanup_memory(self):
        """Clean up memory and old conversations"""
        try:
            import torch
            import gc
            
            cutoff = datetime.now() - timedelta(hours=2)
            for user_id in list(self.conversation_memory.keys()):
                self.conversation_memory[user_id] = [
                    exchange for exchange in self.conversation_memory[user_id]
                    if exchange["timestamp"] > cutoff
                ]
                if not self.conversation_memory[user_id]:
                    del self.conversation_memory[user_id]
            
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
        print(f"\nTest {i}: {character} - '{message}'")
        
        result = ai_service.generate_response(message, character, "", f"test_user_{i}")
        
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print(f"Time: {result['response_time']:.2f}s")
        print(f"Emotions: {result['emotions_detected']}")
        print(f"Enhancement: {result['enhancement_level']}")
    
    stats = ai_service.get_stats()
    print(f"\nStats: {stats}")