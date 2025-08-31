"""
SoulBridge AI - Voice Module
Complete voice chat and voice journaling system extracted from monolith
Handles real-time voice chat, voice journaling, and audio processing
"""

from .voice_chat_service import VoiceChatService
from .voice_journal_service import VoiceJournalService
from .websocket_handler import VoiceWebSocketHandler
from .audio_processor import AudioProcessor
from .routes import voice_bp

__all__ = [
    'VoiceChatService',
    'VoiceJournalService', 
    'VoiceWebSocketHandler',
    'AudioProcessor',
    'voice_bp'
]