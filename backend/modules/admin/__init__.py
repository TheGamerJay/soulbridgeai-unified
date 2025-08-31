"""
SoulBridge AI - Admin Module
Complete admin system extracted using strategic bulk extraction
21 routes + 292+ lines of admin functionality
"""

from .admin_utils import (
    get_total_users,
    get_active_sessions_count,
    get_active_users_count,
    check_database_health,
    get_premium_conversions,
    get_trial_statistics,
    get_system_stats,
    get_user_management_stats
)
from .admin_styles import get_admin_css, get_admin_dashboard_template
from .routes import admin_bp

__all__ = [
    'get_total_users',
    'get_active_sessions_count', 
    'get_active_users_count',
    'check_database_health',
    'get_premium_conversions',
    'get_trial_statistics',
    'get_system_stats',
    'get_user_management_stats',
    'get_admin_css',
    'get_admin_dashboard_template',
    'admin_bp'
]