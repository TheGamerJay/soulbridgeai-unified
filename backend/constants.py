#!/usr/bin/env python3
"""
SoulBridge AI - Application Constants
Centralized configuration for all magic numbers and constants
"""

# Feature limits per plan
PLAN_LIMITS = {
    "bronze": {
        "decoder": 3,
        "fortune": 2, 
        "horoscope": 3,
        "creative_writer": 2,  # 2 uses per day for bronze tier
        "library_chats": 3     # Save max 3 chat conversations
    },
    "silver": {
        "decoder": 15,
        "fortune": 8,
        "horoscope": 10,
        "creative_writer": 20,  # 20 uses per day
        "library_chats": 50     # Save max 50 chat conversations
    },
    "gold": {
        "decoder": 999999,  # Large number that displays as "unlimited"
        "fortune": 999999,  # Large number that displays as "unlimited"
        "horoscope": 999999,  # Large number that displays as "unlimited"
        "creative_writer": 999999,  # Large number that displays as "unlimited"
        "library_chats": 999999     # Large number that displays as "unlimited"
    }
}

# Feature access per plan
FEATURE_ACCESS = {
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
    "blazelian": 5,
    "claude_referral": 8,
    "blayzo_skin": 10
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
    "free": 5,
    "growth": 50, 
    "max": 999999
}

# Legacy plan migration mapping (for backward compatibility only; do not use for new features)
LEGACY_PLAN_MAPPING = {
    'foundation': 'free',
    'premium': 'growth', 
    'enterprise': 'max'
}