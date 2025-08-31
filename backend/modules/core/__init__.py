# SoulBridge AI - Core Routes System
from .navigation_service import NavigationService
from .page_renderer import PageRenderer
from .routes import core_bp, init_core_system

__all__ = [
    'NavigationService',
    'PageRenderer', 
    'core_bp',
    'init_core_system'
]