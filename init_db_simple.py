#!/usr/bin/env python3
"""
Simple Database Initialization Script for SoulBridge AI
"""
import os
import psycopg2
import json

def init_db():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: No DATABASE_URL found")
        return False
        
    print("Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL database")
        
        # Create users table
        print("Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan_type VARCHAR(50) DEFAULT 'foundation',
                is_admin BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create companions table
        print("Creating companions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                character_type VARCHAR(50) NOT NULL,
                description TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Insert companions
        print("Adding companions...")
        companions = [
            ('Blayzion', 'warrior', 'A brave warrior companion', False),
            ('Blayzia', 'healer', 'A wise healer companion', False),
            ('Violet', 'mage', 'A powerful mage companion', True),
            ('Crimson', 'rogue', 'A cunning rogue companion', True)
        ]
        
        for name, ctype, desc, premium in companions:
            cursor.execute("""
                INSERT INTO companions (name, character_type, description, is_premium)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (name, ctype, desc, premium))
        
        # Create dev account
        print("Creating dev account...")
        cursor.execute("""
            INSERT INTO users (email, password_hash, plan_type, is_admin)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                is_admin = EXCLUDED.is_admin,
                plan_type = EXCLUDED.plan_type
        """, ('dagamerjay13@gmail.com', 'dev_hash_123', 'transformation', True))
        
        cursor.close()
        conn.close()
        
        print("SUCCESS: Database initialized!")
        print("Tables: users, companions")
        print("Companions: Blayzion, Blayzia, Violet, Crimson")
        print("Dev account: dagamerjay13@gmail.com")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("SoulBridge AI Database Setup")
    print("=" * 30)
    
    if init_db():
        print("Database ready!")
    else:
        print("Setup failed!")