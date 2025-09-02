"""
SoulBridge AI - Creative Features Service
Extracted from app.py monolith using strategic bulk extraction
AI-powered creative content generation
"""
import logging
import random
from datetime import datetime
from .features_config import get_random_tarot_cards, validate_zodiac_sign

logger = logging.getLogger(__name__)

class CreativeService:
    """Handles AI-powered creative content generation"""
    
    def __init__(self):
        self.ai_service = None
        self._initialize_ai_service()
    
    def _initialize_ai_service(self):
        """Initialize OpenAI service for creative generation"""
        try:
            import os
            from openai import OpenAI
            if os.environ.get("OPENAI_API_KEY"):
                self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                self.ai_service = True
                logger.info("OpenAI client initialized for creative features")
            else:
                self.client = None
                self.ai_service = None
                logger.warning("No OpenAI API key available")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
            self.ai_service = None
    
    def decode_dream(self, dream_text: str, user_id: int = None, mode: str = "dream") -> dict:
        """Decode content using AI - Handles dreams, lyrics, symbolism, tone analysis"""
        try:
            if not dream_text or len(dream_text.strip()) < 10:
                return {
                    "success": False,
                    "error": "Please provide text of at least 10 characters to decode"
                }
            
            # Use the working chat endpoint internally for OpenAI integration (same as creative writing)
            try:
                import requests
                import os
                
                # Direct call to chat endpoint
                chat_url = f"{os.environ.get('APP_URL', 'http://localhost:8080')}/api/chat"
                logger.info(f"🌐 Making internal call to: {chat_url}")
                
                # Choose character and context based on mode
                if mode == "lyrics":
                    character = "Symbolism Decoder"
                    context = "lyrics_analysis"
                elif mode == "tone":
                    character = "Communication Analyzer"
                    context = "tone_analysis"
                else:
                    character = "Dream Decoder"
                    context = "dream_interpretation"
                
                # For modes like lyrics/tone, the dream_text already contains the full prompt
                # For traditional dream mode, we add our own prompt
                if mode == "dream" and not dream_text.startswith("Analyze this dream"):
                    prompt = f"""You are a professional dream interpreter. Analyze this dream and provide insights:

Dream: {dream_text}

Please provide:
1. Overall meaning and symbolism
2. Key symbols and their interpretations  
3. Emotional themes
4. Potential connections to waking life
5. Guidance or advice

Be supportive, insightful, and avoid negative interpretations."""
                else:
                    # Use the full prompt as-is (for lyrics/tone modes)
                    prompt = dream_text

                payload = {
                    "message": prompt,
                    "character": character,
                    "context": context,
                    "user_tier": "bronze"
                }
                logger.info(f"📤 Sending payload: {payload}")
                
                response = requests.post(chat_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"🤖 Chat endpoint response: {result}")
                    if result.get('success'):
                        return {
                            "success": True,
                            "interpretation": result['response'],
                            "symbols_found": self._extract_symbols(dream_text),
                            "mood": self._analyze_dream_mood(dream_text)
                        }
                else:
                    logger.error(f"❌ Chat endpoint returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call chat endpoint: {e}")
                pass
            
            # Fallback interpretation
            return {
                "success": True,
                "interpretation": f"Your dream about {dream_text[:50]}... contains rich symbolism. Dreams often reflect our subconscious thoughts and daily experiences. Consider what emotions you felt during this dream and how they might relate to your current life situation.",
                "symbols_found": self._extract_symbols(dream_text),
                "mood": "reflective"
            }
            
        except Exception as e:
            logger.error(f"Error decoding dream: {e}")
            return {
                "success": False,
                "error": "Dream decoding temporarily unavailable"
            }
    
    def generate_fortune(self, question: str = None, user_id: int = None) -> dict:
        """Generate fortune reading using AI - Uses same system as decoder"""
        try:
            # Get random tarot cards
            cards = get_random_tarot_cards(3)
            
            # Use the working chat endpoint internally for OpenAI integration (same as decoder)
            try:
                import requests
                import os
                
                # Direct call to chat endpoint
                chat_url = f"{os.environ.get('APP_URL', 'http://localhost:8080')}/api/chat"
                
                prompt = f"""You are a wise tarot reader. The user asks: "{question or 'General reading'}"

The cards drawn are:
1. {cards[0]['name']} - {cards[0]['meaning']}
2. {cards[1]['name']} - {cards[1]['meaning']}  
3. {cards[2]['name']} - {cards[2]['meaning']}

Provide an insightful, positive reading that connects these cards to their question. Be encouraging and wise."""

                response = requests.post(chat_url, json={
                    "message": prompt,
                    "character": "Fortune Teller",
                    "context": "tarot_reading",
                    "user_tier": "bronze"
                })
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"🤖 Chat endpoint response for fortune: {result}")
                    if result.get('success'):
                        return {
                            "success": True,
                            "reading": result['response'],
                            "cards": cards,
                            "question": question or "General reading"
                        }
                else:
                    logger.error(f"❌ Chat endpoint returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call chat endpoint for fortune: {e}")
                pass
            
            # Fallback reading
            card_names = [card['name'] for card in cards]
            reading = f"The cards {', '.join(card_names)} suggest a time of {random.choice(['growth', 'reflection', 'opportunity', 'change'])}. {random.choice(['Trust your intuition.', 'Stay positive.', 'Embrace new possibilities.', 'Focus on your goals.'])}"
            
            return {
                "success": True,
                "reading": reading,
                "cards": cards,
                "question": question or "General reading"
            }
            
        except Exception as e:
            logger.error(f"Error generating fortune: {e}")
            return {
                "success": False,
                "error": "Fortune reading temporarily unavailable"
            }
    
    def generate_horoscope(self, zodiac_sign: str, user_id: int = None) -> dict:
        """Generate horoscope using AI"""
        try:
            if not validate_zodiac_sign(zodiac_sign):
                return {
                    "success": False,
                    "error": "Invalid zodiac sign"
                }
            
            sign = zodiac_sign.lower()
            
            # Use the working chat endpoint internally for OpenAI integration (same as decoder)
            try:
                import requests
                import os
                
                # Direct call to chat endpoint
                chat_url = f"{os.environ.get('APP_URL', 'http://localhost:8080')}/api/chat"
                
                prompt = f"""Create a daily horoscope for {sign.title()}. Include:

1. General outlook for today
2. Love & relationships
3. Career & money
4. Health & wellness
5. Lucky numbers and colors

Make it positive, insightful, and encouraging. Keep it concise but meaningful."""

                response = requests.post(chat_url, json={
                    "message": prompt,
                    "character": "Astrologer",
                    "context": "horoscope_reading",
                    "user_tier": "bronze"
                })
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"🤖 Chat endpoint response for horoscope: {result}")
                    if result.get('success'):
                        return {
                            "success": True,
                            "horoscope": result['response'],
                            "sign": sign.title(),
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "lucky_numbers": random.sample(range(1, 50), 5),
                            "lucky_color": random.choice(['blue', 'green', 'purple', 'gold', 'red'])
                        }
                else:
                    logger.error(f"❌ Chat endpoint returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call chat endpoint for horoscope: {e}")
                pass
            
            # Fallback horoscope
            outlooks = [
                "positive energy surrounds you",
                "new opportunities are coming your way", 
                "it's a great day for personal growth",
                "focus on your relationships today",
                "trust your intuition"
            ]
            
            return {
                "success": True,
                "horoscope": f"Today, {random.choice(outlooks)}. {sign.title()} signs are known for their {random.choice(['strength', 'wisdom', 'creativity', 'compassion'])}. Embrace these qualities today.",
                "sign": sign.title(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "lucky_numbers": random.sample(range(1, 50), 5),
                "lucky_color": random.choice(['blue', 'green', 'purple', 'gold', 'red'])
            }
            
        except Exception as e:
            logger.error(f"Error generating horoscope: {e}")
            return {
                "success": False,
                "error": "Horoscope temporarily unavailable"
            }
    
    def generate_creative_writing(self, prompt: str, style: str = "story", user_id: int = None) -> dict:
        """Generate creative writing using AI - Uses same system as decoder"""
        try:
            if not prompt or len(prompt.strip()) < 5:
                return {
                    "success": False,
                    "error": "Please provide a writing prompt of at least 5 characters"
                }
            
            # Use the working chat endpoint internally for OpenAI integration (same as decoder)
            try:
                import requests
                import os
                
                # Direct call to chat endpoint
                chat_url = f"{os.environ.get('APP_URL', 'http://localhost:8080')}/api/chat"
                
                writing_prompt = f"""Create a {style} based on this prompt: "{prompt}"

Make it creative, engaging, and well-written. Keep it to about 200-300 words."""

                response = requests.post(chat_url, json={
                    "message": writing_prompt,
                    "character": "Creative Writer",
                    "context": "creative_writing",
                    "user_tier": "bronze"
                })
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"🤖 Chat endpoint response for creative writing: {result}")
                    if result.get('success'):
                        return {
                            "success": True,
                            "content": result['response'],
                            "style": style,
                            "prompt": prompt,
                            "word_count": len(result['response'].split())
                        }
                else:
                    logger.error(f"❌ Chat endpoint returned status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Failed to call chat endpoint: {e}")
                pass
            
            # Fallback creative content
            content = f"Based on your prompt '{prompt}', here's a {style}: Once upon a time, in a world where {prompt.lower()}, extraordinary things began to happen. The story unfolds with mystery and wonder, leading to unexpected discoveries and meaningful connections."
            
            return {
                "success": True,
                "content": content,
                "style": style,
                "prompt": prompt,
                "word_count": len(content.split())
            }
            
        except Exception as e:
            logger.error(f"Error generating creative writing: {e}")
            return {
                "success": False,
                "error": "Creative writing temporarily unavailable"
            }
    
    def _extract_symbols(self, dream_text: str) -> list:
        """Extract potential dream symbols from text"""
        common_symbols = ['water', 'flying', 'animals', 'house', 'car', 'people', 'colors', 'numbers']
        found_symbols = []
        
        text_lower = dream_text.lower()
        for symbol in common_symbols:
            if symbol in text_lower:
                found_symbols.append(symbol)
        
        return found_symbols
    
    def _analyze_dream_mood(self, dream_text: str) -> str:
        """Analyze the emotional mood of a dream"""
        positive_words = ['happy', 'joy', 'love', 'peace', 'beautiful', 'amazing', 'wonderful']
        negative_words = ['scared', 'fear', 'angry', 'sad', 'dark', 'nightmare', 'scary']
        
        text_lower = dream_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "contemplative"  # Avoid negative labeling
        else:
            return "neutral"