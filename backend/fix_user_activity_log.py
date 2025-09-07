#!/usr/bin/env python3
"""
Fix User Activity Log Table
Create the missing user_activity_log table causing Railway deployment errors
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main fix runner for user_activity_log table"""
    print("User Activity Log Table Fix")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("This script requires Railway DATABASE_URL")
        return False
    
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Railway PostgreSQL'}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("\n=== CREATING user_activity_log TABLE ===")
        
        # Create the missing table
        print("\n1. Creating user_activity_log table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_type VARCHAR(50) NOT NULL,
                    session_duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created user_activity_log table")
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_created
                ON user_activity_log(user_id, created_at)
            """)
            print("✅ Created performance index")
            
            # Add additional indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_created_at
                ON user_activity_log(created_at)
            """)
            print("✅ Created time-based index")
            
            conn.commit()
            
        except Exception as e:
            print(f"⚠️ Table creation error: {e}")
            conn.rollback()
            return False
        
        # Verify the table exists and is accessible
        print("\n2. Verifying table creation...")
        try:
            cursor.execute("SELECT COUNT(*) FROM user_activity_log")
            count = cursor.fetchone()[0]
            print(f"✅ user_activity_log table accessible with {count} records")
            
            # Test the query that was failing
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) 
                FROM user_activity_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            daily_users = cursor.fetchone()[0]
            print(f"✅ Daily users query works: {daily_users} users in last 24h")
            
        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return False
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ USER ACTIVITY LOG TABLE FIX COMPLETED!")
        print("The user_activity_log table has been created successfully.")
        print("Railway deployment errors should now be resolved!")
        
        return True
        
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)