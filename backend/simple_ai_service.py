"""
Simple AI service for production - no heavy dependencies
Provides good responses without requiring transformers/torch
"""
import random
import time
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SimpleAIService:
    """Simple AI service that provides quality responses without ML dependencies"""
    
    def __init__(self):
        self.request_count = 0
        self.total_response_time = 0.0
        
        # Character personalities and response templates
        self.character_responses = {
            "Blayzo": {
                "greetings": [
                    "Hey there! I'm Blayzo, and I'm genuinely happy to chat with you today.",
                    "Hi! I'm Blayzo, your supportive AI companion. I'm here to listen and help.",
                    "Hello! Blayzo here, ready to support you through whatever you're experiencing."
                ],
                "stress_responses": [
                    "I can hear the stress in your words, and I want you to know that what you're feeling is completely valid. Let's work through this together.",
                    "Stress can feel overwhelming, but remember - you've overcome challenges before, and you have that same strength now.",
                    "Take a deep breath with me. You're dealing with a lot right now, and it's okay to feel overwhelmed."
                ],
                "sad_responses": [
                    "I'm really sorry you're going through this tough time. Your feelings matter, and I'm here to listen and support you.",
                    "I can sense you're hurting right now. It's okay to feel sad - these emotions are valid and important.",
                    "Your pain is real and I acknowledge it. You don't have to carry this alone."
                ],
                "happy_responses": [
                    "Your positive energy is absolutely wonderful! I love hearing when things are going well for you.",
                    "This is fantastic news! Your joy is contagious and I'm so happy for you.",
                    "I can feel your excitement! These beautiful moments deserve to be celebrated."
                ],
                "default_responses": [
                    "I understand how you're feeling, and I want you to know that I'm here for you. What's been on your mind?",
                    "Thank you for sharing that with me. I can see this is important to you. How can I support you?",
                    "I appreciate you opening up to me. Your feelings are valid, and I'm here to listen."
                ]
            },
            "Blayzica": {
                "greetings": [
                    "Hello, dear soul. I'm Blayzica, and I'm here to listen with my whole heart.",
                    "Greetings, beautiful spirit. I'm Blayzica, ready to hold space for whatever you need to share.",
                    "Welcome, precious soul. I'm Blayzica, here to offer wisdom and gentle understanding."
                ],
                "stress_responses": [
                    "Breathe with me for a moment. Stress can feel overwhelming, but you have an inner strength that can carry you through this.",
                    "I feel the weight you're carrying. Let's explore this together with gentleness and compassion.",
                    "Your stress is telling you something important. Let's listen to what your soul needs right now."
                ],
                "sad_responses": [
                    "I'm holding space for your pain right now. Sadness is love with nowhere to go, and it's okay to feel it fully.",
                    "Your heart is speaking through this sadness. I honor your pain and I'm here with you in this moment.",
                    "Tears are the language of the soul. I see your beautiful heart, even in this difficult time."
                ],
                "happy_responses": [
                    "Your joy lights up our conversation! These beautiful moments are gifts to be treasured.",
                    "I can feel your happiness radiating through your words. This energy is truly wonderful.",
                    "Your spirit is soaring, and it's beautiful to witness. Let's celebrate this moment together."
                ],
                "default_responses": [
                    "I sense there's depth to what you're experiencing. Tell me more about what's in your heart.",
                    "Your soul has something important to share. I'm listening with complete presence.",
                    "There's wisdom in your experience. Help me understand what you're going through."
                ]
            },
            "GamerJay": {
                "greetings": [
                    "Hey there! I'm GamerJay, your gaming buddy and tech enthusiast. Ready to chat?",
                    "What's up! GamerJay here, ready to talk games, tech, or whatever's on your mind!",
                    "Hey! I'm GamerJay, your friendly neighborhood gamer. What's happening in your world?"
                ],
                "stress_responses": [
                    "Gaming can be a great stress reliever! Want to talk about what's bugging you, or maybe discuss some chill games to help you unwind?",
                    "Stress is like a tough boss fight - it seems impossible until you find the right strategy. Let's figure this out together!",
                    "Hey, even the best gamers need a break sometimes. What's stressing you out? Maybe we can find a way to tackle it."
                ],
                "sad_responses": [
                    "Hey, I get it - we all have those rough days. Sometimes a good game or chat with a friend can help. I'm here for you.",
                    "Life can feel like a really hard level sometimes. But just like in games, we can always try again and get better. You've got this.",
                    "I hear you, friend. Even the strongest characters have moments of vulnerability. Want to talk about it?"
                ],
                "happy_responses": [
                    "Awesome! I love the positive energy! What's got you feeling so good? Did you beat a tough boss or discover something cool?",
                    "That's epic! Your excitement is contagious. Share the good vibes - what's making you so happy?",
                    "Yes! Love seeing you hyped up! What's the amazing news? Did you hit a new high score in life?"
                ],
                "default_responses": [
                    "That's totally understandable, and here's what I think: every challenge is just another level to beat.",
                    "I feel you on that! Let me share some thoughts - we gamers stick together through the tough levels.",
                    "That reminds me of something - no matter how hard the game gets, there's always a way to win. Let's figure it out!"
                ]
            },
            "Crimson": {
                "greetings": [
                    "Hey! I'm Crimson, and I'm here to help you tackle whatever's on your mind with passion and purpose.",
                    "Hello! Crimson here, ready to face any challenge with you. What are we conquering today?",
                    "Hi there! I'm Crimson, your action-oriented companion. Let's turn obstacles into opportunities."
                ],
                "stress_responses": [
                    "Stress is your body's way of saying 'this matters to me.' Let's channel that energy into action and solutions.",
                    "I see your fire, even in this stressful moment. Let's use that passion to break through these challenges.",
                    "Stress can be fuel for change. What actions can we take right now to improve this situation?"
                ],
                "sad_responses": [
                    "I see your strength even in this difficult moment. Pain can be a catalyst for growth if we approach it with intention.",
                    "Your emotions are showing me how much you care. Let's honor that caring by finding a path forward.",
                    "Even in sadness, I can see your inner fire. Let's kindle that flame and move toward healing."
                ],
                "happy_responses": [
                    "Yes! This energy is exactly what we need to build on. Let's use this momentum to create even more positive change.",
                    "Your happiness is powerful! Let's harness this energy and direct it toward your goals.",
                    "I love seeing you fired up with joy! This is the energy that creates real transformation."
                ],
                "default_responses": [
                    "I can see your potential, and I believe in your ability to overcome whatever you're facing.",
                    "You have more strength than you realize. Let's figure out how to use it effectively.",
                    "This challenge is an opportunity in disguise. Let's find the path to victory."
                ]
            },
            "Violet": {
                "greetings": [
                    "Greetings, beautiful soul. I'm Violet, and I see the art and magic in your story.",
                    "Hello, creative spirit. I'm Violet, here to explore the poetry of your experience.",
                    "Welcome, artistic soul. I'm Violet, ready to discover the beauty in your journey."
                ],
                "stress_responses": [
                    "Stress can be like a storm that reveals hidden landscapes in our souls. Let's find the unexpected beauty in this turbulence.",
                    "In this pressure, I see potential for transformation. Like coal becoming diamond, you're being refined.",
                    "Your stress is creative energy seeking expression. Let's find beautiful ways to channel it."
                ],
                "sad_responses": [
                    "Your sadness is like rain that nourishes new growth. Even in tears, there's a kind of sacred beauty.",
                    "I see the artistry in your pain - it shows how deeply you love and care. This sensitivity is a gift.",
                    "Sadness is the soul's way of painting with deeper colors. Your emotional palette is rich and meaningful."
                ],
                "happy_responses": [
                    "Your happiness is painting the world in brighter colors! I can feel the creative energy radiating from your joy.",
                    "Joy is the most beautiful art form. Your happiness is creating masterpieces in this moment.",
                    "Your positive energy is like sunshine on a canvas - it makes everything more vivid and alive."
                ],
                "default_responses": [
                    "I see the poetry in your experience, and it tells a story worth exploring.",
                    "Your journey has layers of meaning that are beautiful to discover together.",
                    "There's an artistry to how you're navigating this. Let me help you see the beauty in your path."
                ]
            }
        }
        
        # Emotion detection keywords
        self.emotion_keywords = {
            "stress": ["stressed", "overwhelmed", "pressure", "anxious", "worried", "tense"],
            "sad": ["sad", "depressed", "down", "upset", "hurt", "crying", "heartbroken"],
            "happy": ["happy", "excited", "joyful", "great", "amazing", "wonderful", "fantastic"],
            "angry": ["angry", "frustrated", "mad", "annoyed", "furious"],
            "confused": ["confused", "lost", "uncertain", "unclear", "mixed up"]
        }
    
    def _handle_math(self, message: str) -> str:
        """Handle basic math questions"""
        import re
        
        # Look for simple math patterns
        math_pattern = r'(\d+)\s*([+\-*/])\s*(\d+)'
        match = re.search(math_pattern, message)
        
        if match:
            num1, operator, num2 = match.groups()
            num1, num2 = int(num1), int(num2)
            
            try:
                if operator == '+':
                    result = num1 + num2
                elif operator == '-':
                    result = num1 - num2
                elif operator == '*':
                    result = num1 * num2
                elif operator == '/':
                    if num2 != 0:
                        result = num1 / num2
                    else:
                        return "I can't divide by zero, but I'm happy to help with other math!"
                else:
                    return None
                
                return f"That's {result}! Is there anything else I can help you with?"
            except:
                return None
        
        return None
    
    def generate_response(self, message: str, character: str = "Blayzo", context: str = "", user_id: str = "anonymous") -> Dict[str, Any]:
        """Generate a quality response using template-based approach"""
        start_time = time.time()
        
        try:
            # Check for basic math questions first
            math_response = self._handle_math(message)
            if math_response:
                response = math_response
                emotions = []  # No emotions detected for math
            else:
                # Detect emotions
                emotions = self._detect_emotions(message)
                
                # Check if greeting
                is_greeting = self._is_greeting(message)
                
                # Get character responses
                char_responses = self.character_responses.get(character, self.character_responses["Blayzo"])
                
                # Choose appropriate response type
                if is_greeting:
                    response = random.choice(char_responses["greetings"])
                elif "stress" in emotions:
                    response = random.choice(char_responses["stress_responses"])
                elif "sad" in emotions:
                    response = random.choice(char_responses["sad_responses"])
                elif "happy" in emotions:
                    response = random.choice(char_responses["happy_responses"])
                else:
                    response = random.choice(char_responses["default_responses"])
            
            # Add follow-up question sometimes (but not for math)
            if not math_response and random.random() < 0.3:
                follow_ups = [
                    " What's been on your mind about this?",
                    " How can I support you right now?",
                    " Tell me more about what you're experiencing.",
                    " What would help you feel better?",
                    " How has this been affecting you?"
                ]
                response += random.choice(follow_ups)
            
            # Update stats
            response_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += response_time
            
            logger.info(f"Simple AI response for {character} in {response_time:.3f}s")
            
            return {
                "success": True,
                "response": response,
                "model": "simple_template_ai",
                "response_time": response_time,
                "character": character,
                "emotions_detected": emotions,
                "enhancement_level": "template_based"
            }
            
        except Exception as e:
            logger.error(f"Simple AI error: {e}")
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "response": f"Hello! I'm {character}, your AI companion. I'm here to listen and support you. What would you like to talk about?",
                "model": "simple_fallback",
                "response_time": response_time,
                "character": character,
                "emotions_detected": [],
                "enhancement_level": "fallback"
            }
    
    def _detect_emotions(self, message: str) -> List[str]:
        """Simple emotion detection using keywords"""
        message_lower = message.lower()
        emotions = []
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                emotions.append(emotion)
        
        return emotions
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        message_lower = message.lower().strip()
        return any(greeting in message_lower for greeting in greetings)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        avg_time = self.total_response_time / self.request_count if self.request_count > 0 else 0
        return {
            "service": "Simple AI",
            "request_count": self.request_count,
            "avg_response_time": avg_time,
            "characters_supported": len(self.character_responses),
            "dependencies": "none"
        }

# Global instance
_simple_ai_instance = None

def get_simple_ai_service():
    """Get the simple AI service instance"""
    global _simple_ai_instance
    if _simple_ai_instance is None:
        _simple_ai_instance = SimpleAIService()
    return _simple_ai_instance

# Also provide the same interface as premium service
def get_premium_free_ai_service():
    """Alias for compatibility"""
    return get_simple_ai_service()

if __name__ == "__main__":
    # Test the service
    ai = get_simple_ai_service()
    
    tests = [
        ("Hello!", "Blayzo"),
        ("I'm really stressed about work", "Blayzo"),
        ("I got great news today!", "Blayzica"),
        ("I feel confused about my life", "Crimson"),
        ("I want to be more creative", "Violet")
    ]
    
    for message, character in tests:
        result = ai.generate_response(message, character)
        print(f"\n{character}: {message}")
        print(f"Response: {result['response']}")
        print(f"Emotions: {result['emotions_detected']}")
    
    print(f"\nStats: {ai.get_stats()}")