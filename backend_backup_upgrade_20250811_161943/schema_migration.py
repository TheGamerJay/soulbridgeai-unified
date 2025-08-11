"""
Schema migration to be run on Railway deployment
Converts trial columns to proper BOOLEAN type
"""
import os
from database import Database

def migrate_schema():
    """Convert trial columns to BOOLEAN type"""
    try:
        db = Database()
        if not db.use_postgres:
            print("Skipping migration - not using PostgreSQL")
            return True
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("Starting schema migration...")
        
        # Check current column types
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('trial_active', 'trial_used_permanently')
        """)
        
        columns = cursor.fetchall()
        for col_name, data_type in columns:
            print(f"Current {col_name}: {data_type}")
        
        # Convert trial_active to boolean if needed
        try:
            cursor.execute("""
                ALTER TABLE users 
                ALTER COLUMN trial_active TYPE BOOLEAN 
                USING CASE WHEN trial_active::integer = 1 THEN TRUE ELSE FALSE END
            """)
            print("Converted trial_active to BOOLEAN")
        except Exception as e:
            print(f"trial_active already BOOLEAN or error: {e}")
        
        # Convert trial_used_permanently to boolean if needed  
        try:
            cursor.execute("""
                ALTER TABLE users 
                ALTER COLUMN trial_used_permanently TYPE BOOLEAN 
                USING CASE WHEN trial_used_permanently::integer = 1 THEN TRUE ELSE FALSE END
            """)
            print("Converted trial_used_permanently to BOOLEAN")
        except Exception as e:
            print(f"trial_used_permanently already BOOLEAN or error: {e}")
        
        conn.commit()
        conn.close()
        
        print("Schema migration completed!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_schema()