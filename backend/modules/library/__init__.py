"""
SoulBridge AI - Library Module
Unified library system for managing user content
Handles chat conversations, creative content, and music tracks
"""

from .library_manager import LibraryManager
from .content_service import ContentService
from .music_service import MusicService
from .routes import library_bp

__all__ = [
    'LibraryManager',
    'ContentService',
    'MusicService',
    'library_bp'
]