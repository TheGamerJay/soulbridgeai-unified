#!/usr/bin/env python3
"""
Database Initialization Script for SoulBridge AI
Sets up all necessary tables and initial data
"""
import os
import sys
import psycopg2
from psycopg2 import sql
import json
from datetime import datetime

def initialize_database():
    """Initialize PostgreSQL database with all required tables and data"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: No DATABASE_URL found")
        return False
        
    print(f"🔗 Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Create users table
        print("📋 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                plan_type VARCHAR(50) DEFAULT 'foundation',
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create companions table
        print("📋 Creating companions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                character_type VARCHAR(50) NOT NULL,
                description TEXT,
                personality_traits JSONB DEFAULT '{}',
                is_premium BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create chat_sessions table
        print("📋 Creating chat_sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                companion_id INTEGER REFERENCES companions(id),
                session_token VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create chat_messages table
        print("📋 Creating chat_messages table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES chat_sessions(id),
                user_id INTEGER REFERENCES users(id),
                companion_id INTEGER REFERENCES companions(id),
                message_type VARCHAR(20) NOT NULL, -- 'user' or 'companion'
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Create user_subscriptions table
        print("📋 Creating user_subscriptions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                plan_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                stripe_subscription_id VARCHAR(255),
                metadata JSONB DEFAULT '{}'
            )
        """)
        
        # Insert default companions
        print("👥 Adding default companions...")
        companions_data = [
            {
                'name': 'Blayzion',
                'character_type': 'warrior',
                'description': 'A brave and loyal warrior companion ready to fight alongside you.',
                'personality_traits': {
                    'brave': 95,
                    'loyal': 90,
                    'protective': 85,
                    'strategic': 75
                },
                'is_premium': False
            },
            {
                'name': 'Blayzia',
                'character_type': 'healer',
                'description': 'A wise and compassionate healer who provides comfort and guidance.',
                'personality_traits': {
                    'compassionate': 95,
                    'wise': 88,
                    'nurturing': 92,
                    'patient': 85
                },
                'is_premium': False
            },
            {
                'name': 'Violet',
                'character_type': 'mage',
                'description': 'A mysterious and powerful mage with deep knowledge of the arcane.',
                'personality_traits': {
                    'intelligent': 95,
                    'mysterious': 80,
                    'curious': 85,
                    'powerful': 90
                },
                'is_premium': True
            },
            {
                'name': 'Crimson',
                'character_type': 'rogue',
                'description': 'A cunning and agile rogue who excels in stealth and strategy.',
                'personality_traits': {
                    'cunning': 90,
                    'agile': 88,
                    'stealthy': 92,
                    'independent': 75
                },
                'is_premium': True
            }
        ]
        
        for companion in companions_data:
            cursor.execute("""
                INSERT INTO companions (name, character_type, description, personality_traits, is_premium)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                companion['name'],
                companion['character_type'], 
                companion['description'],
                json.dumps(companion['personality_traits']),
                companion['is_premium']
            ))
        
        # Create development user account
        print("👤 Creating development user account...")
        dev_email = "dagamerjay13@gmail.com"
        dev_password_hash = "$2b$12$ZaWzRWdZO4aEkhoZsyDwc.gx3kWyFEJ0BPcb8fGPEdaGpcc.VFAni"  # Real bcrypt hash for 'Yariel13'
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, plan_type, is_admin, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                is_admin = EXCLUDED.is_admin,
                plan_type = EXCLUDED.plan_type
        """, (
            dev_email,
            dev_password_hash,
            'transformation',  # Premium plan for dev
            True,  # Admin access
            json.dumps({'dev_mode': True, 'created_by': 'init_script'})
        ))
        
        # Create indexes for better performance
        print("🔧 Creating database indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        cursor.close()
        conn.close()
        
        print("✅ Database initialization completed successfully!")
        print("📊 Tables created:")
        print("   - users")
        print("   - companions") 
        print("   - chat_sessions")
        print("   - chat_messages")
        print("   - user_subscriptions")
        print("👥 Companions added: Blayzion, Blayzia, Violet, Crimson")
        print("👤 Dev account created: dagamerjay13@gmail.com")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("SoulBridge AI Database Initialization")
    print("=" * 50)
    
    if initialize_database():
        print("\n🎉 Database is ready for SoulBridge AI!")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)