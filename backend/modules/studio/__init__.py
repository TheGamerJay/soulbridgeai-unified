"""
SoulBridge AI - Mini Studio Module
Professional music production system with Docker microservices
Integrates with real AI models: MusicGen, DiffSinger, OpenAI
"""

from .studio_service import StudioService
from .routes import studio_bp

__all__ = [
    'StudioService',
    'studio_bp'
]