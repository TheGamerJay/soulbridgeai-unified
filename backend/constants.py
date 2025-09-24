#!/usr/bin/env python3
"""
SoulBridge AI - Application Constants
Centralized configuration for all magic numbers and constants
"""

# Feature costs - KEEP ORIGINAL COSTS FROM MODULES/CREDITS/CONSTANTS.PY
# This section removed to avoid duplication - use modules/credits/constants.py instead

# Soul Companion tier system (only 2 tiers)
PLAN_LIMITS = {
    "soul_companion": {
        # All features are credit-based, no daily limits
        "monthly_credits": 100,  # Free tier gets 100 credits
        "library_chats": 1000
    },
    "soul_companion_pro": {
        # Pro tier gets more credits monthly
        "monthly_credits": 300,  # Pro tier gets 300 credits/month
        "library_chats": 1000
    }
}

# Feature access - ALL FEATURES ENABLED FOR BOTH TIERS (credit-gated)
FEATURE_ACCESS = {
    "soul_companion": {
        "voice_journal": True,      # All features enabled, credit-gated
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": True,
        "soul_riddle": True,
        "decoder": True,
        "fortune": True,
        "horoscope": True,
        "meditation": True
    },
    "soul_companion_pro": {
        "voice_journal": True,      # Same features, just more credits
        "ai_image": True,
        "creative_writer": True,
        "library": True,
        "mini_studio": True,
        "soul_riddle": True,
        "decoder": True,
        "fortune": True,
        "horoscope": True,
        "meditation": True
    }
}

# Credit packages and pricing (per blueprint)
CREDIT_PACKAGES = {
    "signup_bonus": {"credits": 100, "price": 0.00, "description": "Free signup bonus"},
    "monthly_subscription": {"credits": 300, "price": 12.99, "description": "Soul Companion Pro monthly"},
    "yearly_subscription": {"credits": 300, "price": 117.00, "description": "Soul Companion Pro yearly (25% savings)"},
    "topup_small": {"credits": 50, "price": 2.99, "description": "Small top-up pack"},
    "topup_medium": {"credits": 120, "price": 5.99, "description": "Medium top-up pack"},
    "topup_large": {"credits": 300, "price": 12.99, "description": "Large top-up pack"}
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