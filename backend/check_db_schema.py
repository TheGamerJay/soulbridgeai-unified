#!/usr/bin/env python3
"""
Check existing database schema
"""
import sqlite3
import os

def check_database_schema():
    db_path = "soulbridge.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables in {db_path}:")
        for table in tables:
            table_name = table[0]
            print(f"\n=== {table_name} ===")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                cid, name, type_, not_null, default_value, pk = col
                print(f"  {name}: {type_}")
                
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database_schema()