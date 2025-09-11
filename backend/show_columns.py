#!/usr/bin/env python3
"""
Show Database Columns - Simple script to display all table structures
"""

import os
import sys

def show_columns():
    """Show all database tables and their columns"""
    print("📋 SHOWING DATABASE COLUMNS...")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL found - not in Railway environment")
        return True
    
    try:
        import psycopg2
        print(f"🔗 Connecting to database...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 Found {len(tables)} tables:\n")
        
        for table in tables:
            table_name = table[0]
            print(f"🔸 TABLE: {table_name}")
            
            # Get columns for this table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            for col in columns:
                nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"   ├─ {col[0]} ({col[1]}) {nullable}{default}")
            
            print()
        
        cursor.close()
        conn.close()
        
        print("✅ Database column inspection completed!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to show columns: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    show_columns()