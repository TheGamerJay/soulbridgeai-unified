#!/usr/bin/env python3
"""
Setup script for Music Studio integration
Handles database schema updates and environment configuration
"""

import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def setup_database_schema():
    """Add Music Studio tables and columns to existing database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("🔧 Adding Music Studio columns to users table...")
        
        # Add music studio columns to existing users table
        music_columns = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trainer_credits INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS disclaimer_accepted_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_credit_reset DATE"
        ]
        
        for sql in music_columns:
            try:
                cursor.execute(sql)
                logger.info(f"  ✅ {sql}")
            except Exception as e:
                logger.warning(f"  ⚠️ Column may already exist: {e}")
        
        logger.info("🎵 Creating Music Studio tables...")
        
        # Create songs table
        songs_table = """
        CREATE TABLE IF NOT EXISTS songs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(200),
            tags VARCHAR(200),
            file_path VARCHAR(500),
            likes INTEGER DEFAULT 0,
            play_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
        cursor.execute(songs_table)
        logger.info("  ✅ Songs table created")
        
        # Create trainer purchases table
        trainer_purchases_table = """
        CREATE TABLE IF NOT EXISTS trainer_purchases (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            credits INTEGER NOT NULL,
            stripe_session_id VARCHAR(255) UNIQUE,
            paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
        cursor.execute(trainer_purchases_table)
        logger.info("  ✅ Trainer purchases table created")
        
        # Create max trials table
        max_trials_table = """
        CREATE TABLE IF NOT EXISTS max_trials (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            expires_at TIMESTAMP NOT NULL,
            credits_granted INTEGER DEFAULT 60,
            active BOOLEAN DEFAULT TRUE
        )
        """
        cursor.execute(max_trials_table)
        logger.info("  ✅ Max trials table created")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database schema setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
        return False

def check_required_env_vars():
    """Check if required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = ['DATABASE_URL', 'SECRET_KEY']
    optional_vars = ['STRIPE_SECRET_KEY', 'STRIPE_PUBLIC_KEY', 'TRAINER_PRICE_350', 'ADMIN_TOKEN']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            logger.info(f"  ✅ {var} is set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            logger.info(f"  ✅ {var} is set")
    
    if missing_required:
        logger.error(f"❌ Missing required environment variables: {missing_required}")
        return False
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional environment variables: {missing_optional}")
        logger.info("Note: Music Studio will work with limited functionality without Stripe integration")
    
    return True

def create_env_template():
    """Create .env template with required variables"""
    env_template = """
# SoulBridge AI Music Studio Environment Variables
# Required variables
SECRET_KEY=your_secret_key_here
DATABASE_URL=your_database_url_here

# Stripe Integration (for credit purchases)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
TRAINER_PRICE_350=price_your_stripe_price_id  # $3.50 product price ID

# Admin access for cron endpoints
ADMIN_TOKEN=your_super_long_random_admin_token

# Existing SoulBridge AI variables (keep your current values)
# Add your existing environment variables here...
"""
    
    env_file = os.path.join(os.path.dirname(__file__), '.env.music_studio_template')
    with open(env_file, 'w') as f:
        f.write(env_template.strip())
    
    logger.info(f"📄 Environment template created: {env_file}")

def main():
    """Main setup function"""
    logger.info("🎵 Starting SoulBridge AI Music Studio Setup...")
    
    # Check environment variables
    if not check_required_env_vars():
        logger.error("❌ Environment variable check failed")
        create_env_template()
        return False
    
    # Setup database
    if not setup_database_schema():
        logger.error("❌ Database setup failed")
        return False
    
    logger.info("🎉 Music Studio setup completed successfully!")
    logger.info("🚀 You can now restart your application to use Music Studio features")
    
    return True

if __name__ == "__main__":
    main()