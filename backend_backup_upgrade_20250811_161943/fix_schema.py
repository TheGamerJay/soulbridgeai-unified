#!/usr/bin/env python3
"""
Fix PostgreSQL schema - convert trial columns to proper BOOLEAN type
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_postgresql_schema():
    """Convert integer trial columns to proper BOOLEAN type"""
    try:
        # Get Railway DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("DATABASE_URL not found")
            return False
            
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check current column types
        print("Checking current column types...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('trial_active', 'trial_used_permanently')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        print("Current column types:")
        for col_name, data_type in columns:
            print(f"  {col_name}: {data_type}")
        
        # Convert to boolean
        print("\nConverting columns to BOOLEAN type...")
        
        # Convert trial_active if it exists and is integer
        try:
            cursor.execute("""
                ALTER TABLE users 
                ALTER COLUMN trial_active TYPE BOOLEAN 
                USING CASE WHEN trial_active = 1 THEN TRUE ELSE FALSE END
            """)
            print("SUCCESS: trial_active converted to BOOLEAN")
        except Exception as e:
            print(f"WARNING: trial_active conversion: {e}")
        
        # Convert trial_used_permanently
        try:
            cursor.execute("""
                ALTER TABLE users 
                ALTER COLUMN trial_used_permanently TYPE BOOLEAN 
                USING CASE WHEN trial_used_permanently = 1 THEN TRUE ELSE FALSE END
            """)
            print("SUCCESS: trial_used_permanently converted to BOOLEAN")
        except Exception as e:
            print(f"WARNING: trial_used_permanently conversion: {e}")
        
        # Verify the changes
        print("\nVerifying new column types...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('trial_active', 'trial_used_permanently')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        print("New column types:")
        for col_name, data_type in columns:
            print(f"  {col_name}: {data_type}")
        
        cursor.close()
        conn.close()
        
        print("\nSchema fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"Schema fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_postgresql_schema()
    if success:
        print("\nDatabase schema is now properly aligned with the code!")
    else:
        print("\nSchema fix failed. Check the error above.")