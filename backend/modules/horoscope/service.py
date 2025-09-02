"""
SoulBridge AI - Horoscope Service
Python logic for generating personalized zodiac horoscopes with visual cards
Similar architecture to the tarot service but focused on astrology
"""

import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HoroscopeService:
    """Handles zodiac horoscope generation with visual cards"""
    
    def __init__(self):
        self.ai_service = None
        self.horoscope_data = None
        self._initialize_ai_service()
        self._load_horoscope_data()
    
    def _initialize_ai_service(self):
        """Initialize OpenAI service for horoscope generation"""
        try:
            from openai import OpenAI
            if os.environ.get("OPENAI_API_KEY"):
                self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                self.ai_service = True
                logger.info("OpenAI client initialized for horoscope features")
            else:
                self.client = None
                self.ai_service = None
                logger.warning("No OpenAI API key available for horoscope")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for horoscope: {e}")
            self.client = None
            self.ai_service = None
    
    def _load_horoscope_data(self):
        """Load zodiac meanings and traits from JSON file"""
        try:
            data_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'horoscope_texts.json'
            )
            
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.horoscope_data = json.load(f)
                logger.info("Horoscope data loaded successfully")
            else:
                logger.error(f"Horoscope data file not found: {data_file}")
                self.horoscope_data = {}
                
        except Exception as e:
            logger.error(f"Failed to load horoscope data: {e}")
            self.horoscope_data = {}
    
    def get_zodiac_signs(self) -> List[Dict[str, Any]]:
        """Get list of all zodiac signs with basic info"""
        signs = []
        
        if not self.horoscope_data:
            return signs
            
        for sign_key, sign_data in self.horoscope_data.items():
            if sign_key != 'meta':  # Skip metadata
                signs.append({
                    'key': sign_key,
                    'name': sign_data.get('name', sign_key.title()),
                    'symbol': sign_data.get('symbol', ''),
                    'dates': sign_data.get('dates', ''),
                    'element': sign_data.get('element', ''),
                    'ruling_planet': sign_data.get('ruling_planet', ''),
                    'image': f'/static/horoscope/{sign_key}.png'
                })
        
        return signs
    
    def validate_zodiac_sign(self, sign: str) -> bool:
        """Validate if the provided sign is a valid zodiac sign"""
        if not sign or not self.horoscope_data:
            return False
        
        sign_lower = sign.lower().strip()
        return sign_lower in self.horoscope_data and sign_lower != 'meta'
    
    def get_sign_info(self, sign: str) -> Dict[str, Any]:
        """Get detailed information about a zodiac sign"""
        if not self.validate_zodiac_sign(sign):
            return {}
        
        sign_lower = sign.lower().strip()
        sign_data = self.horoscope_data.get(sign_lower, {})
        
        return {
            'key': sign_lower,
            'name': sign_data.get('name', sign.title()),
            'symbol': sign_data.get('symbol', ''),
            'dates': sign_data.get('dates', ''),
            'element': sign_data.get('element', ''),
            'ruling_planet': sign_data.get('ruling_planet', ''),
            'traits': sign_data.get('traits', {}),
            'meanings': sign_data.get('meanings', {}),
            'image': f'/static/horoscope/{sign_lower}.png',
            'back_image': '/static/horoscope/back.png'
        }
    
    def generate_daily_horoscope(self, sign: str, user_id: int = None, 
                                reading_type: str = "general") -> Dict[str, Any]:
        """Generate personalized daily horoscope with AI interpretation"""
        try:
            if not self.validate_zodiac_sign(sign):
                return {
                    "success": False,
                    "error": "Invalid zodiac sign provided"
                }
            
            sign_lower = sign.lower().strip()
            sign_info = self.get_sign_info(sign_lower)
            sign_data = self.horoscope_data.get(sign_lower, {})
            
            # Get random daily theme
            daily_themes = sign_data.get('daily_themes', [])
            theme = random.choice(daily_themes) if daily_themes else "Today brings new opportunities"
            
            # Generate AI-powered horoscope
            if self.client:
                try:
                    # Create personalized prompt based on reading type
                    if reading_type == "love":
                        focus = "love, relationships, and romantic connections"
                    elif reading_type == "career":
                        focus = "career, work, and professional opportunities"
                    elif reading_type == "health":
                        focus = "health, wellness, and vitality"
                    else:
                        focus = "all areas of life with balanced guidance"
                    
                    prompt = f"""You are a wise astrologer speaking as Fortune Teller Sky from SoulBridge AI. 
Create a personalized daily horoscope for {sign_info['name']} ({sign_info['symbol']}).

Sign Details:
- Element: {sign_info['element']}
- Ruling Planet: {sign_info['ruling_planet']} 
- Key Traits: {', '.join(sign_data.get('traits', {}).get('positive', []))}
- Today's Theme: {theme}

Focus on: {focus}

Speak directly to the person as their spiritual guide:
1. Start with a warm, personal greeting mentioning their sign
2. Provide insights about {focus} for today
3. Include 1-2 specific actionable guidance points
4. Reference their {sign_info['element']} element or {sign_info['ruling_planet']} influence
5. End with an encouraging, mystical closing
6. Keep it warm, personal, and uplifting (200-300 words)

Write as if you're personally consulting with them about their day ahead."""

                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are Fortune Teller Sky, a wise and compassionate astrologer from SoulBridge AI who provides personal, uplifting horoscope guidance."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=400
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_reading = response.choices[0].message.content.strip()
                        logger.info(f"✅ Generated AI horoscope for {sign_info['name']}")
                        
                        return {
                            "success": True,
                            "sign": sign_info,
                            "reading": ai_reading,
                            "theme": theme,
                            "reading_type": reading_type,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "lucky_numbers": random.sample(range(1, 50), 3),
                            "lucky_color": random.choice(['crimson', 'gold', 'emerald', 'sapphire', 'amethyst', 'silver'])
                        }
                        
                except Exception as e:
                    logger.error(f"OpenAI horoscope generation failed: {e}")
                    pass
            
            # Fallback horoscope without AI
            fallback_readings = [
                f"As a {sign_info['name']}, your {sign_info['element']} energy is particularly strong today.",
                f"The influence of {sign_info['ruling_planet']} brings opportunities for growth and positive change.",
                f"{theme} - trust in your natural {sign_info['name']} instincts to guide you forward.",
                "Today is a wonderful day to embrace your unique qualities and share them with the world."
            ]
            
            fallback_reading = " ".join(fallback_readings)
            
            return {
                "success": True,
                "sign": sign_info,
                "reading": fallback_reading,
                "theme": theme,
                "reading_type": reading_type,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "lucky_numbers": random.sample(range(1, 50), 3),
                "lucky_color": random.choice(['crimson', 'gold', 'emerald', 'sapphire', 'amethyst', 'silver'])
            }
            
        except Exception as e:
            logger.error(f"Error generating horoscope: {e}")
            return {
                "success": False,
                "error": "Horoscope generation temporarily unavailable"
            }
    
    def get_compatibility(self, sign1: str, sign2: str) -> Dict[str, Any]:
        """Get zodiac compatibility analysis between two signs"""
        try:
            if not self.validate_zodiac_sign(sign1) or not self.validate_zodiac_sign(sign2):
                return {
                    "success": False,
                    "error": "Invalid zodiac signs provided"
                }
            
            sign1_info = self.get_sign_info(sign1)
            sign2_info = self.get_sign_info(sign2)
            
            # Simple compatibility based on elements
            element_compatibility = {
                ('Fire', 'Fire'): 85,
                ('Fire', 'Air'): 90,
                ('Fire', 'Earth'): 60,
                ('Fire', 'Water'): 50,
                ('Air', 'Air'): 80,
                ('Air', 'Earth'): 55,
                ('Air', 'Water'): 65,
                ('Earth', 'Earth'): 75,
                ('Earth', 'Water'): 85,
                ('Water', 'Water'): 90
            }
            
            elements = (sign1_info['element'], sign2_info['element'])
            compatibility_score = element_compatibility.get(elements, element_compatibility.get(elements[::-1], 70))
            
            return {
                "success": True,
                "sign1": sign1_info,
                "sign2": sign2_info,
                "compatibility_score": compatibility_score,
                "elements": elements
            }
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return {
                "success": False,
                "error": "Compatibility calculation failed"
            }
    
    def generate_monthly_horoscope(self, sign: str, user_id: int = None) -> Dict[str, Any]:
        """Generate comprehensive monthly horoscope with AI interpretation"""
        try:
            if not self.validate_zodiac_sign(sign):
                return {
                    "success": False,
                    "error": "Invalid zodiac sign provided"
                }
            
            sign_lower = sign.lower().strip()
            sign_info = self.get_sign_info(sign_lower)
            sign_data = self.horoscope_data.get(sign_lower, {})
            
            # Get monthly themes
            monthly_themes = sign_data.get('monthly_themes', [])
            theme = random.choice(monthly_themes) if monthly_themes else "This month brings transformation and growth"
            
            # Generate AI-powered monthly horoscope
            if self.client:
                try:
                    current_month = datetime.now().strftime("%B %Y")
                    
                    prompt = f"""You are Fortune Teller Sky, creating a comprehensive monthly horoscope for {sign_info['name']} ({sign_info['symbol']}) for {current_month}.

Sign Details:
- Element: {sign_info['element']}
- Ruling Planet: {sign_info['ruling_planet']}
- Key Traits: {', '.join(sign_data.get('traits', {}).get('positive', []))}
- Monthly Theme: {theme}

Create a detailed monthly forecast covering:
1. Overall energy and theme for the month
2. Love & relationships developments 
3. Career & financial opportunities
4. Health & wellness focus
5. Personal growth insights
6. Key dates or planetary influences to watch

Speak directly as their spiritual guide with warmth and wisdom.
Keep it comprehensive yet uplifting (400-500 words).
Reference their element and ruling planet influence throughout."""

                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are Fortune Teller Sky, providing detailed monthly astrological guidance with wisdom and compassion."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=600
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        ai_reading = response.choices[0].message.content.strip()
                        logger.info(f"✅ Generated monthly horoscope for {sign_info['name']}")
                        
                        return {
                            "success": True,
                            "sign": sign_info,
                            "reading": ai_reading,
                            "theme": theme,
                            "month": datetime.now().strftime("%B %Y"),
                            "key_dates": self._generate_key_dates()
                        }
                        
                except Exception as e:
                    logger.error(f"OpenAI monthly horoscope generation failed: {e}")
                    pass
            
            # Fallback monthly horoscope without AI
            fallback_reading = f"""Dear {sign_info['name']}, this month brings exciting opportunities aligned with your {sign_info['element']} element nature. {theme} 

Your ruling planet {sign_info['ruling_planet']} encourages you to embrace your natural strengths while remaining open to new experiences. Focus on nurturing relationships, pursuing career growth, and maintaining balance in all areas of life.

This is an excellent time for {sign_info['name']} individuals to trust their instincts and take positive action toward their goals."""
            
            return {
                "success": True,
                "sign": sign_info,
                "reading": fallback_reading,
                "theme": theme,
                "month": datetime.now().strftime("%B %Y"),
                "key_dates": self._generate_key_dates()
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly horoscope: {e}")
            return {
                "success": False,
                "error": "Monthly horoscope generation temporarily unavailable"
            }
    
    def _generate_key_dates(self) -> List[str]:
        """Generate some key dates for the month"""
        current_month = datetime.now().month
        key_dates = [
            f"{current_month}/7-9: Energy peak period",
            f"{current_month}/15-17: Relationship focus", 
            f"{current_month}/23-25: Career opportunities"
        ]
        return key_dates