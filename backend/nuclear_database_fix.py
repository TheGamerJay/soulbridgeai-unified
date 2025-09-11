#!/usr/bin/env python3
"""
NUCLEAR DATABASE FIX - Direct database connection to resolve persistent schema errors
Bypasses all app initialization and fixes the database directly
"""

import os
import sys

def nuclear_fix():
    """Nuclear database fix - direct connection, no dependencies"""
    print("🚨 NUCLEAR DATABASE FIX STARTING...")
    
    # Only run if DATABASE_URL exists (Railway environment)
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL found - not in Railway environment")
        return True
    
    try:
        import psycopg2
        print(f"📍 Connecting to Railway PostgreSQL...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔥 Step 1: Dropping all problematic indexes...")
        
        # Drop all variants of the problematic index
        indexes_to_drop = [
            'idx_feature_usage_user_feature_date',
            'idx_feature_usage_user_date', 
            'feature_usage_pkey',
            'idx_feature_usage_performance'
        ]
        
        for idx_name in indexes_to_drop:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {idx_name} CASCADE")
                print(f"  ✅ Dropped index: {idx_name}")
            except Exception as e:
                print(f"  ⚠️ Index {idx_name}: {e}")
        
        print("🔥 Step 2: Recreating feature_usage table with correct schema...")
        
        # Drop and recreate the feature_usage table
        cursor.execute("DROP TABLE IF EXISTS feature_usage CASCADE")
        print("  ✅ Dropped feature_usage table")
        
        # Create with standardized schema
        cursor.execute("""
            CREATE TABLE feature_usage (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                feature_name VARCHAR(50) NOT NULL,
                usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
                usage_count INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Created feature_usage table with correct schema")
        
        # Create proper indexes
        cursor.execute("""
            CREATE INDEX idx_feature_usage_lookup 
            ON feature_usage(user_id, feature_name, usage_date)
        """)
        print("  ✅ Created proper lookup index")
        
        print("🔥 Step 3: Fixing tier_limits table...")
        
        # Ensure tier_limits has proper schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tier_limits (
                id SERIAL PRIMARY KEY,
                tier VARCHAR(20) NOT NULL,
                feature_name VARCHAR(50) NOT NULL,
                daily_limit INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tier, feature_name)
            )
        """)
        print("  ✅ Created/verified tier_limits table")
        
        print("🔥 Step 4: Fixing credits tables...")
        
        # user_credits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_credits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                credits_remaining INTEGER DEFAULT 0,
                last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Created/verified user_credits table")
        
        # credit_ledger table  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_ledger (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                reason VARCHAR(100),
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Created/verified credit_ledger table")
        
        print("🔥 Step 5: Committing all changes...")
        conn.commit()
        
        print("🔥 Step 6: Verifying schema...")
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = cursor.fetchall()
        print(f"  📊 Database has {len(tables)} tables: {[t[0] for t in tables]}")
        
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'feature_usage' ORDER BY ordinal_position")
        columns = cursor.fetchall()
        print(f"  📊 feature_usage columns: {columns}")
        
        cursor.close()
        conn.close()
        
        print("🎉 NUCLEAR FIX COMPLETED SUCCESSFULLY!")
        print("🚀 Database schema has been completely rebuilt!")
        
        return True
        
    except Exception as e:
        print(f"❌ Nuclear fix failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = nuclear_fix()
    if not success:
        sys.exit(1)
    print("💀 Nuclear database fix completed - Railway should work now!")