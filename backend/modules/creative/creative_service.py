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
            
            # Direct OpenAI API call to bypass authentication issues
            if self.client:
                try:
                    # Choose character and context based on mode
                    if mode == "lyrics":
                        character_prompt = "You are a Symbolism Decoder, expert at analyzing lyrics, poetry, and artistic content for deeper meanings."
                    elif mode == "tone":
                        character_prompt = "You are a Communication Analyzer, expert at reading tone, intent, and subtext in messages."
                    else:
                        character_prompt = "You are a Dream Decoder, expert at interpreting dreams and subconscious symbolism."
                    
                    # For modes like lyrics/tone, the dream_text already contains the full prompt
                    # For traditional dream mode, we add our own prompt
                    if mode == "dream" and not dream_text.startswith("Analyze this dream"):
                        user_message = f"""Analyze this dream and provide insights:

{dream_text}

Please provide:
1. Overall meaning and symbolism
2. Key symbols and their interpretations  
3. Emotional themes
4. Potential connections to waking life
5. Guidance or advice

Be supportive, insightful, and avoid negative interpretations."""
                    else:
                        # Use the full prompt as-is (for lyrics/tone modes)
                        user_message = dream_text

                    logger.info(f"🤖 Making direct OpenAI call for {mode} mode")
                    
                    # Direct OpenAI call
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": character_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.9,
                        max_tokens=800
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_response = response.choices[0].message.content.strip()
                        logger.info(f"✅ Got OpenAI response: {ai_response[:100]}...")
                        
                        return {
                            "success": True,
                            "interpretation": ai_response,
                            "symbols_found": self._extract_symbols(dream_text),
                            "mood": self._analyze_dream_mood(dream_text)
                        }
                    
                except Exception as e:
                    logger.error(f"OpenAI API call failed: {e}")
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
    
    def generate_fortune(self, question: str = None, user_id: int = None, spread_type: str = "three") -> dict:
        """Generate fortune reading using AI - Supports multiple spread types"""
        try:
            # Define spread configurations
            spread_configs = {
                "one": {
                    "cards": 1,
                    "positions": ["Guidance"],
                    "description": "Single card guidance"
                },
                "three": {
                    "cards": 3,
                    "positions": ["Past", "Present", "Future"],
                    "description": "Three card spread"
                },
                "five": {
                    "cards": 5,
                    "positions": ["Situation", "Challenge", "Hidden Influences", "Advice", "Outcome"],
                    "description": "Five card cross spread"
                },
                "celtic": {
                    "cards": 10,
                    "positions": ["Present Situation", "Challenge", "Distant Past", "Recent Past", "Possible Outcome", "Near Future", "Your Approach", "External Influences", "Hopes & Fears", "Final Outcome"],
                    "description": "Celtic Cross - Full life reading"
                }
            }
            
            # Get spread configuration
            config = spread_configs.get(spread_type, spread_configs["three"])
            card_count = config["cards"]
            positions = config["positions"]
            
            # Get random tarot cards
            cards = get_random_tarot_cards(card_count)
            
            # Direct OpenAI API call to bypass authentication issues
            if self.client:
                try:
                    # Build card descriptions with positions
                    card_descriptions = []
                    for i, card in enumerate(cards):
                        position = positions[i] if i < len(positions) else f"Card {i+1}"
                        card_descriptions.append(f"{position}: {card['name']} - {card['meaning']}")
                    
                    prompt = f"""You are a wise tarot reader. The user asks: "{question or 'General reading'}"

{config['description']} - {card_count} cards drawn:

{chr(10).join(card_descriptions)}

Provide an insightful, positive reading that connects these cards to their question. Explain how each position relates to their situation. Be encouraging and wise."""

                    logger.info(f"🔮 Making direct OpenAI call for fortune reading")
                    
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a wise Fortune Teller, expert at tarot reading and spiritual guidance."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9,
                        max_tokens=600
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_response = response.choices[0].message.content.strip()
                        logger.info(f"✅ Got OpenAI fortune response: {ai_response[:100]}...")
                        
                        # Add position information to cards
                        positioned_cards = []
                        for i, card in enumerate(cards):
                            position = positions[i] if i < len(positions) else f"Card {i+1}"
                            positioned_card = card.copy()
                            positioned_card["position"] = position
                            positioned_cards.append(positioned_card)
                        
                        return {
                            "success": True,
                            "reading": ai_response,
                            "cards": positioned_cards,
                            "spread_type": spread_type,
                            "spread_description": config["description"],
                            "question": question or "General reading"
                        }
                        
                except Exception as e:
                    logger.error(f"OpenAI fortune API call failed: {e}")
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
            
            # Direct OpenAI API call to bypass authentication issues
            if self.client:
                try:
                    prompt = f"""Create a daily horoscope for {sign.title()}. Include:

1. General outlook for today
2. Love & relationships
3. Career & money
4. Health & wellness
5. Lucky numbers and colors

Make it positive, insightful, and encouraging. Keep it concise but meaningful."""

                    logger.info(f"⭐ Making direct OpenAI call for horoscope")
                    
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an Astrologer, expert at creating insightful and uplifting horoscopes."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9,
                        max_tokens=500
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_response = response.choices[0].message.content.strip()
                        logger.info(f"✅ Got OpenAI horoscope response: {ai_response[:100]}...")
                        
                        return {
                            "success": True,
                            "horoscope": ai_response,
                            "sign": sign.title(),
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "lucky_numbers": random.sample(range(1, 50), 5),
                            "lucky_color": random.choice(['blue', 'green', 'purple', 'gold', 'red'])
                        }
                        
                except Exception as e:
                    logger.error(f"OpenAI horoscope API call failed: {e}")
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
        """Generate creative writing using direct OpenAI integration"""
        try:
            if not prompt or len(prompt.strip()) < 5:
                return {
                    "success": False,
                    "error": "Please provide a writing prompt of at least 5 characters"
                }
            
            # Direct OpenAI API call like decode_dream does
            if self.client:
                try:
                    # Style-specific character prompts and instructions
                    style_configs = {
                        "story": {
                            "character": "You are a Creative Story Writer, expert at crafting engaging short stories with compelling characters and plot.",
                            "instruction": f"Write a creative short story based on this prompt: '{prompt}'. Include dialogue, vivid descriptions, and emotional depth. Keep it around 250-400 words."
                        },
                        "lyrics": {
                            "character": "You are a Song Lyricist, expert at writing emotional and meaningful song lyrics with rhythm and flow.",
                            "instruction": f"Write song lyrics based on this theme: '{prompt}'. Include verses, a chorus, and bridge. Make it emotional and relatable with good rhythm. Format with clear verse/chorus structure."
                        },
                        "poem": {
                            "character": "You are a Poet, expert at creating beautiful poetry that captures emotions and imagery.",
                            "instruction": f"Write a poem inspired by: '{prompt}'. Use vivid imagery, metaphors, and emotional language. Choose an appropriate style (free verse, rhyming, etc.) that fits the theme."
                        },
                        "script": {
                            "character": "You are a Screenwriter, expert at writing compelling dialogue and dramatic scenes.",
                            "instruction": f"Write a script/dialogue scene based on: '{prompt}'. Include character names, dialogue, and stage directions. Make it dramatic and engaging with realistic conversation."
                        },
                        "essay": {
                            "character": "You are a Creative Essay Writer, expert at crafting thoughtful and engaging essays.",
                            "instruction": f"Write a creative essay about: '{prompt}'. Include personal insights, examples, and compelling arguments. Make it engaging and thought-provoking."
                        },
                        "letter": {
                            "character": "You are a Letter Writer, expert at crafting personal and meaningful correspondence.",
                            "instruction": f"Write a heartfelt letter based on: '{prompt}'. Make it personal, genuine, and emotionally resonant. Include appropriate greetings and closings."
                        },
                        "creative": {
                            "character": "You are a Creative Fiction Writer, expert at experimental and imaginative storytelling.",
                            "instruction": f"Write a creative fiction piece inspired by: '{prompt}'. Be experimental, imaginative, and unique. Break conventional rules if it serves the story."
                        }
                    }
                    
                    # Get config for the requested style, default to story
                    config = style_configs.get(style, style_configs["story"])
                    
                    logger.info(f"🎨 Making direct OpenAI call for creative writing: {style}")
                    
                    # Direct OpenAI call
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": config["character"]},
                            {"role": "user", "content": config["instruction"]}
                        ],
                        temperature=0.9,  # High creativity
                        max_tokens=800
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_content = response.choices[0].message.content.strip()
                        logger.info(f"✅ Generated {style}: {ai_content[:100]}...")
                        
                        return {
                            "success": True,
                            "content": ai_content,
                            "style": style,
                            "prompt": prompt,
                            "word_count": len(ai_content.split())
                        }
                    
                except Exception as e:
                    logger.error(f"OpenAI creative writing failed: {e}")
            
            # Only fall back if OpenAI is completely unavailable
            return {
                "success": False,
                "error": "Creative writing service temporarily unavailable. Please try again later."
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