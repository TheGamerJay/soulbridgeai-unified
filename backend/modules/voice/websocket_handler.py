"""
SoulBridge AI - Voice WebSocket Handler
Real-time voice processing WebSocket server for voice chat
Extracted from backend/voice_websocket.py with improvements
"""
import json
import logging
import asyncio
import base64
from datetime import datetime
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VoiceWebSocketHandler:
    """Advanced voice processing WebSocket handler for real-time AI conversations"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.companion_configs = self._load_companion_configs()
        
    def register_events(self):
        """Register all WebSocket events for voice chat"""
        
        @self.socketio.on('connect', namespace='/voice')
        def handle_connect():
            """Handle voice chat WebSocket connection"""
            try:
                # Import here to avoid circular imports
                from ..auth.session_manager import get_current_user
                from ..tiers.artistic_time import get_effective_access
                from ..shared.database import get_database
                
                user = get_current_user()
                if not user.get('id'):
                    logger.warning('Unauthenticated voice chat connection attempt')
                    disconnect()
                    return False
                
                user_id = user['id']
                user_plan = user.get('plan', 'bronze')
                
                # Check if user has Silver/Gold access or trial
                db = get_database()
                trial_active, trial_expires_at = self._get_trial_state(user_id, db)
                access = get_effective_access(user_plan, trial_active, trial_expires_at)
                
                # Voice chat requires Silver or Gold tier
                if not (access.get('access_silver') or access.get('access_gold')):
                    logger.warning(f'User {user_id} attempted voice chat without Silver/Gold access')
                    emit('access_denied', {
                        'error': 'Voice chat requires Silver or Gold tier',
                        'current_plan': user_plan,
                        'required_plan': 'silver'
                    })
                    disconnect()
                    return False
                
                # Create user session
                session_id = f"voice_{user_id}_{datetime.now().timestamp()}"
                join_room(session_id)
                
                self.active_sessions[session_id] = {
                    'user_id': user_id,
                    'plan': user_plan,
                    'access': access,
                    'connected_at': datetime.now(),
                    'companion': None,
                    'audio_settings': {
                        'sample_rate': 22050,
                        'channels': 1,
                        'format': 'webm'
                    },
                    'conversation_context': []
                }
                
                logger.info(f'✅ Voice chat connected: User {user_id}, Session {session_id}')
                
                emit('connected', {
                    'session_id': session_id,
                    'status': 'connected',
                    'features': ['speech_recognition', 'text_to_speech', 'ai_conversation'],
                    'audio_settings': self.active_sessions[session_id]['audio_settings']
                })
                
            except Exception as e:
                logger.error(f'Voice connection error: {e}')
                emit('error', {'message': 'Connection failed'})
                disconnect()
        
        @self.socketio.on('disconnect', namespace='/voice')
        def handle_disconnect():
            """Handle voice chat disconnection"""
            try:
                from ..auth.session_manager import get_current_user
                
                user = get_current_user()
                if not user.get('id'):
                    return
                
                # Clean up session
                session_to_remove = None
                for session_id, session_data in self.active_sessions.items():
                    if session_data['user_id'] == user.get('id'):
                        session_to_remove = session_id
                        break
                
                if session_to_remove:
                    del self.active_sessions[session_to_remove]
                    logger.info(f'🔌 Voice chat disconnected: Session {session_to_remove}')
                
            except Exception as e:
                logger.error(f'Voice disconnect error: {e}')
        
        @self.socketio.on('select_companion', namespace='/voice')
        def handle_companion_selection(data):
            """Handle companion selection for voice chat"""
            try:
                from ..auth.session_manager import get_current_user
                
                companion_id = data.get('companion_id')
                if not companion_id:
                    emit('error', {'message': 'Companion ID required'})
                    return
                
                user = get_current_user()
                if not user.get('id'):
                    emit('error', {'message': 'Authentication required'})
                    return
                
                session = self._get_user_session(user['id'])
                if not session:
                    emit('error', {'message': 'No active session'})
                    return
                
                # Validate companion access
                if not self._validate_companion_access(companion_id, session):
                    emit('error', {'message': 'Companion not accessible'})
                    return
                
                # Load companion configuration
                companion_config = self.companion_configs.get(companion_id)
                if not companion_config:
                    emit('error', {'message': 'Companion not found'})
                    return
                
                session['companion'] = companion_config
                
                logger.info(f'🤖 Companion selected: {companion_id} for user {user["id"]}')
                
                emit('companion_selected', {
                    'companion': companion_config,
                    'voice_settings': companion_config.get('voice', {}),
                    'personality': companion_config.get('personality', {})
                })
                
            except Exception as e:
                logger.error(f'Companion selection error: {e}')
                emit('error', {'message': 'Failed to select companion'})
        
        @self.socketio.on('audio_data', namespace='/voice')
        def handle_audio_data(data):
            """Handle incoming audio data for real-time processing"""
            try:
                from ..auth.session_manager import get_current_user
                
                user = get_current_user()
                if not user.get('id'):
                    emit('error', {'message': 'Authentication required'})
                    return
                
                session = self._get_user_session(user['id'])
                if not session or not session.get('companion'):
                    emit('error', {'message': 'No active session or companion'})
                    return
                
                # Process audio data
                audio_chunk = data.get('audio')
                if not audio_chunk:
                    return
                
                # Decode base64 audio
                try:
                    audio_bytes = base64.b64decode(audio_chunk)
                except Exception as e:
                    logger.error(f'Audio decode error: {e}')
                    return
                
                # Process audio chunk (transcription simulation)
                asyncio.create_task(self._process_audio_chunk(session, audio_bytes))
                
            except Exception as e:
                logger.error(f'Audio processing error: {e}')
                emit('error', {'message': 'Audio processing failed'})
        
        @self.socketio.on('speech_complete', namespace='/voice')
        def handle_speech_complete(data):
            """Handle completed speech for AI response generation"""
            try:
                from ..auth.session_manager import get_current_user
                
                user = get_current_user()
                if not user.get('id'):
                    emit('error', {'message': 'Authentication required'})
                    return
                
                session = self._get_user_session(user['id'])
                if not session:
                    emit('error', {'message': 'No active session'})
                    return
                
                transcript = data.get('transcript', '').strip()
                if not transcript:
                    return
                
                logger.info(f'💬 Speech received from user {user["id"]}: "{transcript[:50]}..."')
                
                # Generate AI response
                asyncio.create_task(self._generate_ai_response(session, transcript))
                
            except Exception as e:
                logger.error(f'Speech processing error: {e}')
                emit('error', {'message': 'Speech processing failed'})
        
        @self.socketio.on('update_settings', namespace='/voice')
        def handle_settings_update(data):
            """Handle voice chat settings updates"""
            try:
                from ..auth.session_manager import get_current_user
                
                user = get_current_user()
                if not user.get('id'):
                    emit('error', {'message': 'Authentication required'})
                    return
                
                session = self._get_user_session(user['id'])
                if not session:
                    emit('error', {'message': 'No active session'})
                    return
                
                # Update audio settings
                if 'audio_settings' in data:
                    session['audio_settings'].update(data['audio_settings'])
                
                logger.info(f'⚙️ Settings updated for user {user["id"]}')
                
                emit('settings_updated', {
                    'audio_settings': session['audio_settings']
                })
                
            except Exception as e:
                logger.error(f'Settings update error: {e}')
                emit('error', {'message': 'Settings update failed'})
    
    def _get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active session for user"""
        for session_data in self.active_sessions.values():
            if session_data['user_id'] == user_id:
                return session_data
        return None
    
    def _get_trial_state(self, user_id: int, db) -> tuple:
        """Get user's trial state from database"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            placeholder = "%s" if hasattr(db, 'postgres_url') and db.postgres_url else "?"
            
            cursor.execute(f"SELECT trial_active, trial_expires_at FROM users WHERE id = {placeholder}", (user_id,))
            result = cursor.fetchone()
            
            if result:
                trial_active, trial_expires_at = result
                return trial_active, trial_expires_at
            
            conn.close()
            return False, None
            
        except Exception as e:
            logger.error(f"Error getting trial state for user {user_id}: {e}")
            return False, None
    
    def _validate_companion_access(self, companion_id: str, session: Dict[str, Any]) -> bool:
        """Validate if user can access the selected companion"""
        access = session.get('access', {})
        accessible_tiers = []
        
        if access.get('access_bronze'): accessible_tiers.append('bronze')
        if access.get('access_silver'): accessible_tiers.append('silver') 
        if access.get('access_gold'): accessible_tiers.append('gold')
        
        companion_config = self.companion_configs.get(companion_id)
        if not companion_config:
            return False
            
        required_tier = companion_config.get('tier', 'bronze')
        return required_tier in accessible_tiers
    
    def _load_companion_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load companion configurations"""
        return {
            'blayzo': {
                'id': 'blayzo',
                'name': 'Blayzo',
                'avatar': '/static/logos/Blayzo.png',
                'tier': 'bronze',
                'voice': {
                    'type': 'male',
                    'pitch': 1.0,
                    'rate': 1.0,
                    'volume': 1.0
                },
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
                'voice': {
                    'type': 'female',
                    'pitch': 1.2,
                    'rate': 1.0,
                    'volume': 1.0
                },
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
                'voice': {
                    'type': 'female',
                    'pitch': 1.1,
                    'rate': 1.1,
                    'volume': 1.0
                },
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
                'voice': {
                    'type': 'female',
                    'pitch': 0.9,
                    'rate': 0.9,
                    'volume': 1.0
                },
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
                'voice': {
                    'type': 'female',
                    'pitch': 1.3,
                    'rate': 0.8,
                    'volume': 1.0
                },
                'personality': {
                    'style': 'gentle and intuitive',
                    'tone': 'soothing and wise',
                    'expertise': ['deep healing', 'spiritual guidance', 'inner peace']
                }
            }
        }
    
    async def _process_audio_chunk(self, session: Dict[str, Any], audio_bytes: bytes):
        """Process audio chunk for real-time transcription"""
        try:
            # Simulate audio processing (in production would use actual speech-to-text)
            await asyncio.sleep(0.1)  # Simulate processing delay
            
            # Emit audio level data for visualization
            audio_level = len(audio_bytes) / 1024  # Rough approximation
            self.socketio.emit('audio_level', {
                'level': min(audio_level, 1.0),
                'timestamp': datetime.now().isoformat()
            }, namespace='/voice', room=f"voice_{session['user_id']}")
            
        except Exception as e:
            logger.error(f'Audio chunk processing error: {e}')
    
    async def _generate_ai_response(self, session: Dict[str, Any], user_input: str):
        """Generate AI response based on user input and companion personality"""
        try:
            companion = session['companion']
            user_id = session['user_id']
            
            # Add to conversation context
            session['conversation_context'].append({
                'type': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 messages for context
            if len(session['conversation_context']) > 10:
                session['conversation_context'] = session['conversation_context'][-10:]
            
            # Simulate AI processing time
            await asyncio.sleep(1.0 + len(user_input) * 0.01)
            
            # Generate response based on companion personality
            response = self._generate_contextual_response(
                user_input, 
                companion, 
                session['conversation_context']
            )
            
            # Add AI response to context
            session['conversation_context'].append({
                'type': 'companion',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f'🤖 AI response generated for user {user_id}: "{response[:50]}..."')
            
            # Emit response
            self.socketio.emit('ai_response', {
                'response': response,
                'companion': companion['name'],
                'voice_settings': companion['voice'],
                'timestamp': datetime.now().isoformat()
            }, namespace='/voice', room=f"voice_{user_id}")
            
        except Exception as e:
            logger.error(f'AI response generation error: {e}')
            self.socketio.emit('error', {
                'message': 'Failed to generate response'
            }, namespace='/voice', room=f"voice_{session['user_id']}")
    
    def _generate_contextual_response(
        self, 
        user_input: str, 
        companion: Dict[str, Any], 
        context: list
    ) -> str:
        """Generate contextual AI response based on companion personality"""
        personality = companion['personality']
        style = personality['style']
        tone = personality['tone']
        expertise = personality['expertise']
        
        # Simple response generation (in production would use advanced AI)
        input_lower = user_input.lower()
        
        # Context-aware responses
        if any(word in input_lower for word in ['sad', 'depressed', 'down', 'upset']):
            if 'empathetic' in style:
                return "I can hear the pain in your voice. It's okay to feel this way, and I'm here to support you through this. What's weighing most heavily on your heart right now?"
            elif 'direct' in style:
                return "I understand you're going through a tough time. Let's work together to find some clarity and strength. What's the first small step we can take?"
            else:
                return "Thank you for sharing that with me. Your feelings are valid, and it takes courage to express them. How can we nurture some peace in this moment?"
        
        elif any(word in input_lower for word in ['happy', 'excited', 'great', 'wonderful']):
            if 'creative' in style:
                return "I love hearing that joy in your voice! Your positive energy is contagious. What's sparking this wonderful feeling, and how can we amplify it?"
            elif 'wise' in style:
                return "It's beautiful to witness your happiness. These moments of joy are precious gifts. What wisdom are you gaining from this experience?"
            else:
                return "Your happiness radiates through your words! I'm so glad you're experiencing this. What would you like to celebrate or explore about this feeling?"
        
        else:
            # Generic responses based on personality
            if 'wise' in style:
                return "I appreciate you sharing that with me. There's wisdom in every experience. What insights are emerging for you as we explore this together?"
            elif 'nurturing' in style:
                return "Thank you for trusting me with your thoughts. I'm here to support you however you need. What feels most important to you right now?"
            elif 'inspiring' in style:
                return "Your voice carries such possibility! Every conversation is a chance for growth and discovery. What would you like to explore or create today?"
            elif 'passionate' in style:
                return "I can feel your energy through your words! There's power in what you're sharing. What action or breakthrough are you ready for?"
            else:
                return "I'm honored to be part of your journey. Your voice and experiences matter deeply. What would feel most supportive or meaningful to discuss?"

def register_voice_websocket(app, socketio):
    """Register voice chat WebSocket functionality with the Flask app"""
    try:
        voice_handler = VoiceWebSocketHandler(socketio)
        voice_handler.register_events()
        
        logger.info("✅ Voice WebSocket system registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register voice WebSocket system: {e}")
        return False