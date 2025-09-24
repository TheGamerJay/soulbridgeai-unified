#!/usr/bin/env python3
"""
SoulBridge AI - Application Constants
Centralized configuration for all magic numbers and constants
"""

# Feature limits per plan - UNIFIED SOUL COMPANION TIER
PLAN_LIMITS = {
    "soul_companion": {
        "decoder": 0,          # Credit-based through Artistic Time system
        "fortune": 0,          # Credit-based through Artistic Time system
        "horoscope": 0,        # Credit-based through Artistic Time system
        "creative_writer": 0,  # Credit-based through Artistic Time system
        "library_chats": 1000  # High limit for chat storage
    },
    # Legacy tiers kept for compatibility during migration
    "bronze": {
        "decoder": 5,
        "fortune": 5,
        "horoscope": 5,
        "creative_writer": 5,
        "library_chats": 3
    },
    "silver": {
        "decoder": 15,
        "fortune": 12,
        "horoscope": 10,
        "creative_writer": 15,
        "library_chats": 50
    },
    "gold": {
        "decoder": 100,
        "fortune": 150,
        "horoscope": 50,
        "creative_writer": 75,
        "library_chats": 200
    }
}

# Feature access per plan - UNIFIED SOUL COMPANION TIER
FEATURE_ACCESS = {
    "soul_companion": {
        "voice_journal": True,      # All features enabled for unified tier
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": True
    },
    # Legacy tiers kept for compatibility during migration
    "bronze": {
        "voice_journal": False,
        "ai_image": False,
        "creative_writer": True,
        "library": True,
        "mini_studio": False
    },
    "silver": {
        "voice_journal": True,
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": False
    },
    "gold": {
        "voice_journal": True,
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": True
    }
}

# Referral system thresholds  
REFERRAL_THRESHOLDS = {
    "blayzike": 2,
    "blazelian": 4,
    "nyxara": 6,
    "claude_referral": 8,
    "blayzo_referral": 10
}

# Trial system settings
TRIAL_DURATION_HOURS = 5
TRIAL_DURATION_SECONDS = TRIAL_DURATION_HOURS * 3600  # Convert hours to seconds
TRIAL_WARNING_THRESHOLD = 17400  # 10 minutes before expiry
TRIAL_WARNING_MINUTES = 10

# Session settings
SESSION_LIFETIME_HOURS = 24
SESSION_PERMANENT_DURATION_HOURS = 24

# Response and message limits
MAX_RESPONSE_LENGTH = 1000
MAX_MEMORY_ENTRIES = 50
MAX_COMMIT_MESSAGE_LENGTH = 200
MAX_FILE_PATH_LENGTH = 255

# Database connection settings
DB_CONNECTION_TIMEOUT = 30
DB_RETRY_ATTEMPTS = 3
DB_RETRY_DELAY = 1

# Rate limiting
RATE_LIMIT_REQUESTS_PER_HOUR = 100
RATE_LIMIT_REQUESTS_PER_MINUTE = 10

# File paths (relative to app directory)
RATE_LIMIT_FLAG_FILE = "rate_limit_status.json"
CONVERSATION_MEMORY_FILE = "conversation_memory.json"
PROJECT_STATE_FILE = "project_state.json"

# Email settings
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1

# Security settings
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# File upload limits
MAX_FILE_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_EDIT_FOLDERS = ['backend/templates/', 'frontend/', 'static/']

# API timeouts
OPENAI_TIMEOUT_SECONDS = 60
MIXTRAL_TIMEOUT_SECONDS = 120
GENERAL_API_TIMEOUT = 30

# Admin settings
ADMIN_SESSION_TIMEOUT_HOURS = 8
MAX_ADMIN_SESSIONS = 3

# Pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache settings
CACHE_EXPIRY_MINUTES = 30
MEMORY_CACHE_MAX_ENTRIES = 1000

# Logging settings
LOG_MAX_LENGTH = 500
DEBUG_LOG_MAX_ENTRIES = 100

# Background task intervals (in seconds)
CLEANUP_INTERVAL_SECONDS = 21600  # 6 hours
CLEANUP_RETRY_DELAY = 60  # 1 minute
BACKGROUND_SLEEP_INTERVAL = 300  # 5 minutes

# Credit reset amounts
MONTHLY_CREDIT_RESET_AMOUNT = 650

# AI Image generation limits per plan
AI_IMAGE_LIMITS = {
    "bronze": 0,      # Bronze: No AI images (premium feature locked)
    "silver": 12,     # Silver: 12 AI images per month (enhanced tier)  
    "gold": 50        # Gold: 50 AI images per month (premium but realistic)
}

AI_IMAGE_COST = 5  # 5 artistic time credits per AI image

# Legacy mapping removed - all users should be migrated to bronze/silver/gold system