"""
SoulBridge AI - Voice Chat Service
Real-time voice chat with AI companions
Extracted from monolith app.py with improvements
"""
import os
import json
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class VoiceChatService:
    """Voice chat service for real-time AI conversations"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI client if available"""
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for voice chat")
            else:
                logger.warning("OpenAI API key not set - voice chat will use mock responses")
        except ImportError:
            logger.warning("OpenAI package not installed - voice chat will use mock responses")
    
    def validate_access(self, user_plan: str, trial_active: bool) -> bool:
        """Validate if user can access voice chat (Silver/Gold tier only)"""
        from ..tiers.artistic_time import get_effective_access
        
        # Get effective access
        access = get_effective_access(user_plan, trial_active, None)
        return access.get('access_silver') or access.get('access_gold')
    
    def process_voice_audio(self, audio_file, companion_id: Optional[str] = None) -> Dict[str, Any]:
        """Process voice audio for chat - transcription + AI response"""
        try:
            # Validate audio file
            validation = self._validate_audio_file(audio_file)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # Transcribe audio
            transcription_result = self._transcribe_audio(audio_file)
            if not transcription_result["success"]:
                return transcription_result
            
            transcription = transcription_result["transcription"]
            
            # Generate AI response
            response_result = self._generate_ai_response(
                transcription, 
                companion_id or 'blayzo'
            )
            
            if not response_result["success"]:
                return response_result
            
            return {
                "success": True,
                "transcription": transcription,
                "ai_response": response_result["response"],
                "companion": response_result["companion"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Voice chat processing failed: {e}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def _validate_audio_file(self, audio_file) -> Dict[str, Any]:
        """Validate uploaded audio file"""
        if not audio_file or not audio_file.filename:
            return {"valid": False, "error": "No audio file provided"}
        
        # Check file extension
        allowed_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'}
        file_ext = os.path.splitext(audio_file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return {
                "valid": False,
                "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            }
        
        # Check file size (max 10MB for voice chat)
        audio_file.seek(0, 2)  # Seek to end
        size = audio_file.tell()
        audio_file.seek(0)  # Seek back to beginning
        
        max_size = 10 * 1024 * 1024  # 10MB
        if size > max_size:
            return {
                "valid": False,
                "error": f"Audio file too large (max {max_size // (1024*1024)}MB)"
            }
        
        return {"valid": True}
    
    def _transcribe_audio(self, audio_file) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            if not self.openai_client:
                # Return mock transcription for development
                return {
                    "success": True,
                    "transcription": "Hello, this is a mock transcription for development testing.",
                    "provider": "mock"
                }
            
            logger.info(f"🎙️ Transcribing voice chat audio: {audio_file.filename}")
            
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                audio_file.save(tmp_file.name)
                
                # Transcribe using Whisper
                with open(tmp_file.name, 'rb') as audio_data:
                    transcription_response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data
                    )
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                transcription_text = transcription_response.text.strip()
                
                if not transcription_text:
                    return {
                        "success": False,
                        "error": "No speech detected in audio"
                    }
                
                logger.info(f"✅ Voice chat transcription successful: {len(transcription_text)} characters")
                
                return {
                    "success": True,
                    "transcription": transcription_text,
                    "provider": "whisper"
                }
                
        except Exception as e:
            logger.error(f"❌ Voice chat transcription failed: {e}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
    
    def _generate_ai_response(self, user_input: str, companion_id: str) -> Dict[str, Any]:
        """Generate AI response based on companion personality"""
        try:
            # Load companion configuration
            companion = self._get_companion_config(companion_id)
            
            if not self.openai_client:
                # Return mock response for development
                mock_responses = [
                    f"Hello! I'm {companion['name']}. Thank you for sharing that with me.",
                    f"I understand what you're saying. As your {companion['name']}, I'm here to support you.",
                    f"That's interesting! Let me think about that from my perspective as {companion['name']}."
                ]
                import random
                return {
                    "success": True,
                    "response": random.choice(mock_responses),
                    "companion": companion,
                    "provider": "mock"
                }
            
            # Create personality-based system prompt
            personality = companion['personality']
            system_prompt = f"""
            You are {companion['name']}, an AI companion with a {personality['style']} personality.
            Your tone should be {personality['tone']}.
            Your areas of expertise include: {', '.join(personality['expertise'])}.
            
            Respond to the user in a warm, conversational way that matches your personality.
            Keep responses concise but meaningful (1-3 sentences).
            Focus on being supportive and engaging.
            """
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            logger.info(f"✅ AI response generated for {companion['name']}: {len(ai_response)} characters")
            
            return {
                "success": True,
                "response": ai_response,
                "companion": companion,
                "provider": "gpt-4"
            }
            
        except Exception as e:
            logger.error(f"❌ AI response generation failed: {e}")
            return {
                "success": False,
                "error": f"Response generation failed: {str(e)}"
            }
    
    def _get_companion_config(self, companion_id: str) -> Dict[str, Any]:
        """Get companion configuration"""
        companions = {
            'blayzo': {
                'id': 'blayzo',
                'name': 'Blayzo',
                'avatar': '/static/logos/Blayzo.png',
                'tier': 'bronze',
                'personality': {
                    'style': 'wise and supportive',
                    'tone': 'calm and encouraging',
                    'expertise': ['meditation', 'mindfulness', 'personal growth']
                }
            },
            'blayzica': {
                'id': 'blayzica',
                'name': 'Blayzica',
                'avatar': '/static/logos/Blayzica.png',
                'tier': 'bronze',
                'personality': {
                    'style': 'nurturing and empathetic',
                    'tone': 'warm and understanding',
                    'expertise': ['emotional support', 'relationships', 'self-care']
                }
            },
            'sky': {
                'id': 'sky',
                'name': 'Sky',
                'avatar': '/static/logos/Sky.png',
                'tier': 'silver',
                'personality': {
                    'style': 'inspiring and creative',
                    'tone': 'uplifting and energetic',
                    'expertise': ['creativity', 'goal setting', 'motivation']
                }
            },
            'crimson': {
                'id': 'crimson',
                'name': 'Companion Crimson',
                'avatar': '/static/logos/Companion Crimson.png',
                'tier': 'gold',
                'personality': {
                    'style': 'passionate and direct',
                    'tone': 'confident and empowering',
                    'expertise': ['leadership', 'confidence building', 'breakthrough moments']
                }
            },
            'violet': {
                'id': 'violet',
                'name': 'Companion Violet',
                'avatar': '/static/logos/Companion Violet.png',
                'tier': 'gold',
                'personality': {
                    'style': 'gentle and intuitive',
                    'tone': 'soothing and wise',
                    'expertise': ['deep healing', 'spiritual guidance', 'inner peace']
                }
            }
        }
        
        return companions.get(companion_id, companions['blayzo'])
    
    def get_available_companions(self, user_plan: str, trial_active: bool) -> List[Dict[str, Any]]:
        """Get list of companions available to user based on their tier"""
        from ..tiers.artistic_time import get_effective_access
        
        # Get effective access
        access = get_effective_access(user_plan, trial_active, None)
        accessible_tiers = []
        
        if access.get('access_bronze'): accessible_tiers.append('bronze')
        if access.get('access_silver'): accessible_tiers.append('silver')
        if access.get('access_gold'): accessible_tiers.append('gold')
        
        # Get all companions
        all_companions = [
            self._get_companion_config('blayzo'),
            self._get_companion_config('blayzica'),
            self._get_companion_config('sky'),
            self._get_companion_config('crimson'),
            self._get_companion_config('violet')
        ]
        
        # Filter by accessible tiers
        available_companions = [
            companion for companion in all_companions
            if companion['tier'] in accessible_tiers
        ]
        
        logger.info(f"User has access to {len(available_companions)} companions")
        
        return available_companions