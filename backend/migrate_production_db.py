#!/usr/bin/env python3
"""
Production Database Migration Script
Adds trial system columns to PostgreSQL users table
"""
import os
import sys
from datetime import datetime

def run_postgresql_migration():
    """Add trial columns to PostgreSQL production database"""
    try:
        import psycopg2
        print("✅ psycopg2 available")
    except ImportError:
        print("❌ psycopg2 not available - installing...")
        os.system("pip install psycopg2-binary")
        import psycopg2

    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    if not database_url:
        print("❌ No DATABASE_URL found in environment variables")
        print("🔧 Set DATABASE_URL environment variable or run in Railway environment")
        return False
    
    print(f"🔍 Connecting to database: {database_url[:30]}...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name LIKE 'trial_%'
            ORDER BY column_name;
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📊 Existing trial columns: {existing_columns}")
        
        # Add trial columns if they don't exist
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_companion TEXT", 
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used_permanently BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP"
        ]
        
        print("🔧 Running migrations...")
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"✅ {migration}")
            except Exception as e:
                print(f"ℹ️ {migration} - {e}")
        
        # Create performance index
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_trial_started_at 
                ON users(trial_started_at) 
                WHERE trial_started_at IS NOT NULL
            """)
            print("✅ Created trial performance index")
        except Exception as e:
            print(f"ℹ️ Index creation: {e}")
        
        # Commit changes
        conn.commit()
        print("✅ All migrations committed successfully")
        
        # Verify final state
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name LIKE 'trial_%'
            ORDER BY column_name;
        """)
        
        final_columns = cursor.fetchall()
        print(f"📋 Final trial columns in database:")
        for col in final_columns:
            print(f"   - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'} {col[3] if col[3] else ''}")
        
        cursor.close()
        conn.close()
        
        print("🎉 PostgreSQL migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"🔍 Error details: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print(f"🚀 Starting PostgreSQL migration at {datetime.now()}")
    success = run_postgresql_migration()
    
    if success:
        print("\n✅ MIGRATION SUCCESS - Trial system is now ready!")
        print("🔄 Restart your Flask app to use the new database schema")
    else:
        print("\n❌ MIGRATION FAILED - Check error messages above")
        sys.exit(1)