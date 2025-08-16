#!/usr/bin/env python3
"""
Simple script to add trial columns to PostgreSQL database
Run this in your Railway environment or with DATABASE_URL set
"""
import os

def main():
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv not installed, skip loading .env
        ...
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found - this script is for PostgreSQL production database")
        print("💡 For local SQLite, the migration was already completed")
        return
    
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL")
        
        # Add all missing columns for registration to work
        sql_commands = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type TEXT DEFAULT 'free';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_plan TEXT DEFAULT 'free';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_active INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_companion TEXT;", 
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used_permanently BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_warning_sent INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS decoder_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS fortune_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS horoscope_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS feature_preview_seen INTEGER DEFAULT 0;"
        ]
        
        for sql in sql_commands:
            cursor.execute(sql)
            print(f"✅ Executed: {sql}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 All missing columns added successfully to PostgreSQL!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure psycopg2 is installed and DATABASE_URL is correct")

if __name__ == "__main__":
    main()