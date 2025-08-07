#!/usr/bin/env python3
"""
Simple script to add missing columns to SQLite database
"""
import sqlite3
import os

def main():
    # Connect to SQLite database
    db_path = 'soulbridge.db'
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Connected to SQLite database")
        
        # Add all missing columns for registration to work
        sql_commands = [
            "ALTER TABLE users ADD COLUMN plan_type TEXT DEFAULT 'free';",
            "ALTER TABLE users ADD COLUMN user_plan TEXT DEFAULT 'free';", 
            "ALTER TABLE users ADD COLUMN trial_active INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN trial_companion TEXT;", 
            "ALTER TABLE users ADD COLUMN trial_used_permanently BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP;",
            "ALTER TABLE users ADD COLUMN trial_warning_sent INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN decoder_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN fortune_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN horoscope_used INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN feature_preview_seen INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN display_name TEXT;",
            "ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 1;",
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        ]
        
        for sql in sql_commands:
            try:
                cursor.execute(sql)
                print(f"✅ Executed: {sql}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Column already exists: {sql}")
                else:
                    print(f"❌ Error: {e} - {sql}")
        
        conn.commit()
        conn.close()
        print("✅ All migrations completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
