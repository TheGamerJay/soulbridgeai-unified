#!/usr/bin/env python3
"""
Initialize password reset tokens table
Run this once to set up the proper password reset system
"""

import sqlite3
import os

def init_password_reset_table():
    """Create password_reset_tokens table with proper indexes"""
    db_path = 'soulbridge.db'
    
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Create the password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP NULL,
                request_ip TEXT NULL,
                request_ua TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS prt_user_idx ON password_reset_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS prt_created_idx ON password_reset_tokens(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS prt_token_hash_idx ON password_reset_tokens(token_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS prt_expires_idx ON password_reset_tokens(expires_at)")
        
        conn.commit()
        print("Password reset tokens table created successfully")
        
        # Show table info
        cursor.execute("PRAGMA table_info(password_reset_tokens)")
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating password reset table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Initializing password reset tokens table...")
    success = init_password_reset_table()
    if success:
        print("Password reset system ready!")
    else:
        print("Failed to initialize password reset system")