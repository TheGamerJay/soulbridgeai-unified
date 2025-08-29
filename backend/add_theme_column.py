#!/usr/bin/env python3
"""
Add theme_preferences column to users table
"""

import os
import psycopg2
import json
from database_utils import get_database

def add_theme_column():
    """Add theme_preferences column to users table"""
    try:
        # For production PostgreSQL
        if os.environ.get('DATABASE_URL'):
            print("Adding theme_preferences column to PostgreSQL...")
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cursor = conn.cursor()
            
            # Add theme_preferences column if it doesn't exist
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS theme_preferences TEXT DEFAULT NULL;
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("PostgreSQL theme_preferences column added successfully")
            
        # For local SQLite
        db = get_database()
        if db:
            print("Adding theme_preferences column to SQLite...")
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'theme_preferences' not in columns:
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN theme_preferences TEXT DEFAULT NULL
                """)
                conn.commit()
                print("SQLite theme_preferences column added successfully")
            else:
                print("SQLite theme_preferences column already exists")
                
            conn.close()
            
    except Exception as e:
        print(f"Error adding theme column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_theme_column()