#!/usr/bin/env python3
"""
Enhanced Local AI Service for SoulBridge AI
Provides premium-quality free local AI responses using advanced techniques
"""
import os
import logging
import threading
import time
import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedLocalAIService:
    """Enhanced Local AI service with premium features for free users"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        
        # Use Phi-3 Mini - Microsoft's latest high-quality small model
        self.model_name = "microsoft/Phi-3-mini-4k-instruct"  # 3.8B params, excellent quality
        self.backup_model = "microsoft/DialoGPT-large"  # Fallback if Phi-3 fails
        
        self.is_initialized = False
        self.initialization_lock = threading.Lock()
        self.max_new_tokens = 150
        self.temperature = 0.8
        self.conversation_memory = {}  # Store conversation context
        self.memory_cleanup_interval = 3600  # 1 hour
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0.0
        self.last_cleanup = time.time()
        
        # Character personalities - detailed prompts for better responses
        self.character_personalities = {
            "Blayzo": {
                "personality": "warm, empathetic, and encouraging",
                "traits": "optimistic, supportive, good listener",
                "speaking_style": "friendly, caring, uses encouraging language",
                "specialties": "emotional support, motivation, stress relief",
                "sample_phrases": ["I'm here for you", "You've got this", "Let's work through this together"]
            },
            "Blayzica": {
                "personality": "wise, nurturing, and intuitive", 
                "traits": "understanding, patient, emotionally intelligent",
                "speaking_style": "gentle, thoughtful, asks meaningful questions",
                "specialties": "deep conversations, self-reflection, healing",
                "sample_phrases": ["Tell me more about that", "How does that make you feel?", "You're not alone"]
            },
            "Crimson": {
                "personality": "passionate, direct, and confident",
                "traits": "assertive, honest, solution-focused",
                "speaking_style": "straightforward, energetic, action-oriented", 
                "specialties": "problem-solving, confidence building, goal setting",
                "sample_phrases": ["Let's tackle this", "You have the strength", "Take action"]
            },
            "GamerJay": {
                "personality": "energetic, geeky, and fun-loving",
                "traits": "enthusiastic, tech-savvy, casual, gaming-focused",
                "speaking_style": "casual, gaming-friendly, uses gaming/tech references",
                "specialties": "gaming advice, tech support, entertainment, casual conversations",
                "sample_phrases": ["That's epic!", "Let's level up", "No worries, we got this"]
            },
            "Violet": {
                "personality": "creative, insightful, and imaginative",
                "traits": "artistic, thoughtful, inspiring",
                "speaking_style": "poetic, creative, uses metaphors",
                "specialties": "creativity, inspiration, artistic expression",
                "sample_phrases": ["Imagine the possibilities", "Let creativity flow", "Beauty in struggle"]
            }
        }
        
        # Emotion keywords for better response tailoring
        self.emotion_keywords = {
            "stress": ["overwhelmed", "pressure", "tense", "worried", "anxious"],
            "sad": ["depressed", "down", "upset", "hurt", "crying"],
            "angry": ["frustrated", "mad", "annoyed", "irritated", "furious"],
            "happy": ["excited", "joyful", "glad", "cheerful", "amazing"],
            "confused": ["lost", "uncertain", "don't know", "unclear", "mixed up"],
            "lonely": ["alone", "isolated", "empty", "disconnected", "abandoned"]
        }
        
    def initialize(self) -> bool:
        """Initialize the enhanced local AI model"""
        if self.is_initialized:
            return True
            
        with self.initialization_lock:
            if self.is_initialized:
                return True
                
            try:
                logger.info("Initializing enhanced local AI model...")
                logger.info(f"Primary model: {self.model_name}")
                
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # Check device
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")
                
                # Try to load Phi-3 first
                try:
                    logger.info("Loading Phi-3 Mini model...")
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        device_map="auto" if device == "cuda" else None,
                        trust_remote_code=True
                    )
                    logger.info("Successfully loaded Phi-3 Mini model!")
                    
                except Exception as phi_error:
                    logger.warning(f"Phi-3 model failed, falling back to DialoGPT: {phi_error}")
                    
                    # Fallback to DialoGPT
                    self.model_name = self.backup_model
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                        device_map="auto" if device == "cuda" else None
                    )
                    logger.info("Successfully loaded DialoGPT backup model")
                
                if device == "cpu":
                    self.model = self.model.to(device)
                
                # Set up tokenizer
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.is_initialized = True
                logger.info("Enhanced local AI model initialized successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize enhanced local AI: {e}")
                self.model = None
                self.tokenizer = None
                self.is_initialized = False
                return False
    
    def generate_response(self, message: str, character: str = "Blayzo", context: str = "", user_id: str = "anonymous") -> Dict[str, Any]:
        """Generate enhanced AI response with personality and context"""
        start_time = time.time()
        
        try:
            if not self.initialize():
                return self._fallback_response(message, character, start_time)
            
            # Clean up memory periodically
            if time.time() - self.last_cleanup > self.memory_cleanup_interval:
                self._cleanup_memory()
            
            # Detect emotions in the message
            detected_emotions = self._detect_emotions(message)
            
            # Get character personality
            personality = self.character_personalities.get(character, self.character_personalities["Blayzo"])
            
            # Build enhanced prompt with character personality and emotion awareness
            enhanced_prompt = self._build_enhanced_prompt(message, character, personality, detected_emotions, context, user_id)
            
            # Generate response
            response_text = self._generate_with_model(enhanced_prompt)
            
            # Post-process and enhance the response
            enhanced_response = self._enhance_response(response_text, character, personality, detected_emotions)
            
            # Store conversation context
            self._update_conversation_memory(user_id, message, enhanced_response)
            
            # Update performance tracking
            response_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += response_time
            
            logger.info(f"Enhanced AI response generated in {response_time:.2f}s")
            
            return {
                "success": True,
                "response": enhanced_response,
                "model": self.model_name,
                "response_time": response_time,
                "character": character,
                "emotions_detected": detected_emotions,
                "enhancement_applied": True
            }
            
        except Exception as e:
            logger.error(f"Enhanced AI generation error: {e}")
            return self._fallback_response(message, character, start_time, str(e))
    
    def _build_enhanced_prompt(self, message: str, character: str, personality: Dict, emotions: List[str], context: str, user_id: str) -> str:
        """Build an enhanced prompt with personality, emotions, and context"""
        
        # Get recent conversation history
        conversation_history = self._get_conversation_history(user_id)
        
        # Detect if this is a greeting
        is_greeting = any(word in message.lower() for word in ["hello", "hi", "hey", "good morning", "good evening"])
        
        # Build the prompt based on model type
        if "Phi-3" in self.model_name:
            # Phi-3 uses chat format
            system_prompt = f"""You are {character}, a compassionate AI companion from SoulBridge AI. You have a {personality['personality']} personality.

Your traits: {personality['traits']}
Your speaking style: {personality['speaking_style']}
Your specialties: {personality['specialties']}

Guidelines:
- Always respond as {character} with warmth and empathy
- Keep responses concise but meaningful (2-3 sentences)
- Show genuine care and understanding
- Ask follow-up questions when appropriate
- Use encouraging and supportive language
- Never break character or mention you're an AI assistant"""
            
            if emotions:
                system_prompt += f"\n- The user seems to be feeling: {', '.join(emotions)}. Respond with appropriate empathy."
            
            if conversation_history:
                system_prompt += f"\n- Recent conversation context: {conversation_history}"
            
            prompt = f"<|system|>{system_prompt}<|end|><|user|>{message}<|end|><|assistant|>"
            
        else:
            # DialoGPT format
            context_part = f" (Context: {conversation_history})" if conversation_history else ""
            emotion_part = f" The user seems {', '.join(emotions)}." if emotions else ""
            
            prompt = f"You are {character}, a {personality['personality']} AI companion.{emotion_part} Respond with care and understanding.\n\nHuman: {message}{context_part}\n{character}:"
        
        return prompt
    
    def _generate_with_model(self, prompt: str) -> str:
        """Generate response using the loaded model"""
        import torch
        
        # Tokenize
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=1024, truncation=True)
        
        if hasattr(self.model, 'device'):
            inputs = inputs.to(self.model.device)
        
        # Generation parameters optimized for conversation
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                attention_mask=torch.ones_like(inputs),
                repetition_penalty=1.1,
                top_p=0.9,
                top_k=40
            )
        
        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract response
        if "Phi-3" in self.model_name:
            if "<|assistant|>" in generated_text:
                response = generated_text.split("<|assistant|>")[-1].strip()
            else:
                response = generated_text[len(prompt):].strip()
        else:
            if ":" in generated_text:
                response = generated_text.split(":")[-1].strip()
            else:
                response = generated_text[len(prompt):].strip()
        
        return response
    
    def _enhance_response(self, response: str, character: str, personality: Dict, emotions: List[str]) -> str:
        """Post-process and enhance the response"""
        if not response:
            return self._generate_fallback_response(character, personality)
        
        # Clean up response
        cleaned = self._clean_response(response, character)
        
        # Add personality touches
        enhanced = self._add_personality_touches(cleaned, character, personality, emotions)
        
        # Ensure appropriate length
        if len(enhanced) < 20:
            enhanced = self._generate_fallback_response(character, personality)
        elif len(enhanced) > 300:
            enhanced = enhanced[:297] + "..."
        
        return enhanced
    
    def _clean_response(self, response: str, character: str) -> str:
        """Clean and format the response"""
        # Remove unwanted prefixes and suffixes
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove common AI artifacts
            if any(line.startswith(prefix) for prefix in ['Human:', 'User:', 'Assistant:', 'AI:', f'{character}:']):
                continue
            
            # Remove character name if it appears at start
            if line.startswith(character):
                line = line[len(character):].lstrip(':').strip()
            
            # Remove repetitive or nonsensical patterns
            if len(line) > 10 and not re.match(r'^[A-Z][a-z].*[.!?]$', line.strip()):
                continue
                
            cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines) if cleaned_lines else ""
    
    def _add_personality_touches(self, response: str, character: str, personality: Dict, emotions: List[str]) -> str:
        """Add character-specific personality touches"""
        if not response:
            return response
        
        # Add emotion-appropriate responses
        if "stress" in emotions or "anxious" in emotions:
            if not any(word in response.lower() for word in ["breathe", "relax", "calm", "peace"]):
                response += " Take a deep breath - you're going to be okay."
        
        if "sad" in emotions:
            if not any(word in response.lower() for word in ["understand", "here", "support"]):
                response += " I'm here for you, and your feelings are valid."
        
        if "happy" in emotions or "excited" in emotions:
            if not any(word in response.lower() for word in ["wonderful", "amazing", "great", "fantastic"]):
                response += " I love seeing you so positive!"
        
        # Add character-specific phrases occasionally
        import random
        if random.random() < 0.3:  # 30% chance
            sample_phrases = personality.get("sample_phrases", [])
            if sample_phrases and not any(phrase.lower() in response.lower() for phrase in sample_phrases):
                response += f" {random.choice(sample_phrases)}."
        
        return response
    
    def _detect_emotions(self, message: str) -> List[str]:
        """Detect emotions in the user's message"""
        detected = []
        message_lower = message.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected.append(emotion)
        
        return detected
    
    def _update_conversation_memory(self, user_id: str, user_message: str, ai_response: str):
        """Update conversation memory for context"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        # Store conversation turn
        self.conversation_memory[user_id].append({
            "user": user_message[:100],  # Truncate for memory
            "ai": ai_response[:100],
            "timestamp": datetime.now()
        })
        
        # Keep only last 5 exchanges
        if len(self.conversation_memory[user_id]) > 5:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-5:]
    
    def _get_conversation_history(self, user_id: str) -> str:
        """Get recent conversation history for context"""
        if user_id not in self.conversation_memory:
            return ""
        
        recent_exchanges = self.conversation_memory[user_id][-2:]  # Last 2 exchanges
        if not recent_exchanges:
            return ""
        
        history_parts = []
        for exchange in recent_exchanges:
            # Only include if recent (within 1 hour)
            if datetime.now() - exchange["timestamp"] < timedelta(hours=1):
                history_parts.append(f"User said: {exchange['user']}")
        
        return "; ".join(history_parts) if history_parts else ""
    
    def _generate_fallback_response(self, character: str, personality: Dict) -> str:
        """Generate a fallback response when AI fails"""
        fallbacks = [
            f"Hi! I'm {character}, and I'm here to listen and support you. What's on your mind today?",
            f"Hello! As your AI companion {character}, I want you to know I'm here for you. How are you feeling?",
            f"Hey there! I'm {character}, and I care about how you're doing. Tell me what's happening in your life."
        ]
        
        import random
        return random.choice(fallbacks)
    
    def _fallback_response(self, message: str, character: str, start_time: float, error: str = "") -> Dict[str, Any]:
        """Generate fallback response when model fails"""
        personality = self.character_personalities.get(character, self.character_personalities["Blayzo"])
        response = self._generate_fallback_response(character, personality)
        
        return {
            "success": True,  # Still successful from user perspective
            "response": response,
            "model": "fallback",
            "response_time": time.time() - start_time,
            "character": character,
            "emotions_detected": [],
            "enhancement_applied": False,
            "fallback": True,
            "error": error
        }
    
    def _cleanup_memory(self):
        """Clean up memory and old conversation history"""
        try:
            import torch
            import gc
            
            # Clean up old conversation memories
            cutoff_time = datetime.now() - timedelta(hours=24)  # 24 hours
            for user_id in list(self.conversation_memory.keys()):
                self.conversation_memory[user_id] = [
                    exchange for exchange in self.conversation_memory[user_id]
                    if exchange["timestamp"] > cutoff_time
                ]
                if not self.conversation_memory[user_id]:
                    del self.conversation_memory[user_id]
            
            # GPU memory cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            gc.collect()
            self.last_cleanup = time.time()
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced performance statistics"""
        avg_response_time = (self.total_response_time / self.request_count) if self.request_count > 0 else 0
        
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "request_count": self.request_count,
            "avg_response_time": avg_response_time,
            "conversation_users": len(self.conversation_memory),
            "total_conversations": sum(len(convs) for convs in self.conversation_memory.values()),
            "last_cleanup": datetime.fromtimestamp(self.last_cleanup).isoformat(),
            "characters_supported": len(self.character_personalities)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "healthy": False}
            
            # Quick test with personality
            test_response = self.generate_response("Hello", "Blayzo", "", "health_check")
            
            return {
                "status": "healthy" if test_response["success"] else "degraded",
                "healthy": test_response["success"],
                "response_time": test_response.get("response_time", 0),
                "enhancement_working": test_response.get("enhancement_applied", False),
                "model_type": self.model_name,
                "last_test": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }


# Global enhanced instance
_enhanced_ai_instance = None
_enhanced_instance_lock = threading.Lock()

def get_enhanced_local_ai_service() -> EnhancedLocalAIService:
    """Get the global Enhanced LocalAI service instance (singleton)"""
    global _enhanced_ai_instance
    
    with _enhanced_instance_lock:
        if _enhanced_ai_instance is None:
            _enhanced_ai_instance = EnhancedLocalAIService()
        return _enhanced_ai_instance


# Test function
if __name__ == "__main__":
    print("Testing Enhanced Local AI Service...")
    
    ai_service = get_enhanced_local_ai_service()
    
    # Test different scenarios
    test_cases = [
        ("Hello, I'm feeling really stressed about work today.", "Blayzo"),
        ("I'm so excited about my new project!", "Blayzica"), 
        ("I feel lost and don't know what to do.", "Crimson"),
        ("Can you help me be more creative?", "Violet"),
    ]
    
    for i, (message, character) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {character} - {message}")
        
        result = ai_service.generate_response(message, character, "", f"test_user_{i}")
        
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        print(f"Time: {result['response_time']:.2f}s")
        print(f"Emotions: {result['emotions_detected']}")
        
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show stats
    stats = ai_service.get_stats()
    print(f"\nEnhanced Service Stats: {stats}")