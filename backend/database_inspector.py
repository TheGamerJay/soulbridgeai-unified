#!/usr/bin/env python3
"""
Database Inspector - Check actual table structure and column names
"""

import os
import sys

def inspect_database():
    """Inspect the actual database schema to find column name mismatches"""
    print("🔍 DATABASE INSPECTOR STARTING...")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL found - not in Railway environment")
        return True
    
    try:
        import psycopg2
        print(f"📍 Connecting to Railway PostgreSQL...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Step 1: Check if feature_usage table exists...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'feature_usage'
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("  ✅ feature_usage table EXISTS")
            
            print("🔍 Step 2: Inspect feature_usage columns...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'feature_usage' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            print("  📊 ACTUAL COLUMNS:")
            for col in columns:
                print(f"    - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'} {col[3] or ''}")
        else:
            print("  ❌ feature_usage table DOES NOT EXIST")
        
        print("🔍 Step 3: Check all existing tables...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        all_tables = cursor.fetchall()
        print("  📊 ALL TABLES:")
        for table in all_tables:
            print(f"    - {table[0]}")
        
        print("🔍 Step 4: Check for any indexes on feature_usage...")
        cursor.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'feature_usage'
        """)
        indexes = cursor.fetchall()
        
        if indexes:
            print("  📊 EXISTING INDEXES:")
            for idx in indexes:
                print(f"    - {idx[0]}: {idx[1]}")
        else:
            print("  ❌ No indexes found on feature_usage")
        
        print("🔍 Step 5: Sample data from feature_usage (if exists)...")
        if table_exists:
            try:
                cursor.execute("SELECT * FROM feature_usage LIMIT 3")
                sample_data = cursor.fetchall()
                if sample_data:
                    print("  📊 SAMPLE DATA:")
                    for row in sample_data[:3]:
                        print(f"    {row}")
                else:
                    print("  📊 Table exists but is empty")
            except Exception as e:
                print(f"  ⚠️ Error reading sample data: {e}")
        
        cursor.close()
        conn.close()
        
        print("🎉 DATABASE INSPECTION COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ Database inspection failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    inspect_database()