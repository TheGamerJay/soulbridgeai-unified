#!/usr/bin/env python3
"""
Test the password reset system
"""

import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
from database_utils import format_query

def test_password_reset_table():
    """Test if password reset tokens table works"""
    try:
        conn = sqlite3.connect('soulbridge.db', timeout=30.0)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_tokens'")
        table_exists = cursor.fetchone()
        print(f"Table exists: {bool(table_exists)}")
        
        if not table_exists:
            print("ERROR: password_reset_tokens table does not exist!")
            return False
        
        # Test insert
        test_user_id = 999999  # Fake user ID for testing
        test_token = secrets.token_urlsafe(32)
        test_token_hash = hashlib.sha256(test_token.encode('utf-8')).hexdigest()
        test_expires = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        
        cursor.execute(format_query("""
            INSERT INTO password_reset_tokens 
            (user_id, token_hash, expires_at, request_ip, request_ua)
            VALUES (?, ?, ?, ?, ?)
        """), (test_user_id, test_token_hash, test_expires, '127.0.0.1', 'test-agent'))
        
        test_id = cursor.lastrowid
        print(f"Test insert successful: ID {test_id}")
        
        # Test select
        cursor.execute(format_query(SELECT * FROM password_reset_tokens WHERE id = ?"), (test_id,))
        result = cursor.fetchone()
        print(f"Test select result: {result}")
        
        # Clean up test data
        cursor.execute(format_query(DELETE FROM password_reset_tokens WHERE id = ?"), (test_id,))
        conn.commit()
        print("Test data cleaned up")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing password reset system...")
    success = test_password_reset_table()
    if success:
        print("Password reset table test PASSED!")
    else:
        print("Password reset table test FAILED!")