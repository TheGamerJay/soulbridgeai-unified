"""
Configuration Management
Centralized settings for all modules
"""
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Config:
    """Base configuration class"""
    
    # Core Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'
    
    # Database Settings
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///backend/soulbridge.db')
    
    # OpenAI Settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Email Settings
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    EMAIL_FROM = os.environ.get('EMAIL_FROM', 'soulbridgeai.contact@gmail.com')
    
    # Stripe Settings
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Stripe Price IDs
    PRICE_SILVER_MONTHLY = os.environ.get('PRICE_SILVER_MONTHLY', 'price_1RxcFwBR4omRdqnXPW1Sx34k')
    PRICE_SILVER_YEARLY = os.environ.get('PRICE_SILVER_YEARLY', 'price_1RxcJjBR4omRdqnXgtbnvF2A')
    PRICE_GOLD_MONTHLY = os.environ.get('PRICE_GOLD_MONTHLY', 'price_1RxcSPBR4omRdqnXNvqJCAbB')
    PRICE_GOLD_YEARLY = os.environ.get('PRICE_GOLD_YEARLY', 'price_1RxcbwBR4omRdqnXTxU9jtES')

class TierConfig:
    """Tier system configuration"""
    
    # Tier Hierarchy
    TIER_HIERARCHY = {
        'bronze': 1,
        'silver': 2, 
        'gold': 3
    }
    
    # Daily Limits by Tier
    DAILY_LIMITS = {
        'bronze': {
            'decoder': 3,
            'fortune': 2,
            'horoscope': 3,
            'creative_writer': 2,
            'companion_messages': 5
        },
        'silver': {
            'decoder': 15,
            'fortune': 8,
            'horoscope': 10,
            'creative_writer': 20,
            'companion_messages': 25
        },
        'gold': {
            'decoder': 999,  # Unlimited
            'fortune': 999,  # Unlimited
            'horoscope': 999,  # Unlimited
            'creative_writer': 999,  # Unlimited
            'companion_messages': 999  # Unlimited
        }
    }
    
    # Monthly Credit Allocations
    MONTHLY_CREDITS = {
        'bronze': 0,
        'silver': 200,
        'gold': 500
    }
    
    # Trial Settings
    TRIAL_DURATION_HOURS = 5
    TRIAL_CREDITS = 60
    
    # Feature Access by Tier
    FEATURE_ACCESS = {
        'ai_images': 'silver',
        'voice_journal': 'silver',
        'meditations': 'silver',
        'relationships': 'silver',
        'mini_studio': 'gold'
    }

class StudioConfig:
    """Studio system configuration"""
    
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_BPM = 120
    DIFFSINGER_DEFAULT_VOICE = 'default'
    DIFFSINGER_MODEL_PATH = '../models/diffsinger'
    
    # Feature Flags
    MINI_STUDIO_ENABLED = os.environ.get('MINI_STUDIO_ENABLED', '1') == '1'
    STUDIO_LIBRARY_ENABLED = os.environ.get('STUDIO_LIBRARY_ENABLED', '1') == '1'
    USE_DIFFUSERS = os.environ.get('USE_DIFFUSERS', '0') == '1'

def get_config() -> Dict[str, Any]:
    """Get all configuration as dictionary"""
    return {
        'core': Config(),
        'tiers': TierConfig(),
        'studio': StudioConfig()
    }

def validate_required_env_vars():
    """Validate that required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'OPENAI_API_KEY',
        'STRIPE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("✅ All required environment variables are set")

# Export commonly used configs
config = Config()
tier_config = TierConfig()
studio_config = StudioConfig()