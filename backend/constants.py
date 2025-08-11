#!/usr/bin/env python3
"""
SoulBridge AI - Application Constants
Centralized configuration for all magic numbers and constants
"""

# Feature limits per plan
PLAN_LIMITS = {
    "free": {
        "decoder": 3,
        "fortune": 2, 
        "horoscope": 3
    },
    "growth": {
        "decoder": 15,
        "fortune": 8,
        "horoscope": 10
    },
    "max": {
        "decoder": float("inf"),
        "fortune": float("inf"), 
        "horoscope": float("inf")
    }
}

# Feature access per plan
FEATURE_ACCESS = {
    "free": {
        "voice_journal": False,
        "ai_image": False,
        "creative_writer": True,
        "library": True,
        "mini_studio": False
    },
    "growth": {
        "voice_journal": True,
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": False
    },
    "max": {
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
TRIAL_DURATION_SECONDS = 18000  # 5 hours
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