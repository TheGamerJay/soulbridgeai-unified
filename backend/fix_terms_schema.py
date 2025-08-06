#!/usr/bin/env python3
"""
Fix terms acceptance database schema
Adds missing columns for terms acceptance functionality
"""

import sqlite3
import os

def fix_terms_schema():
    """Add missing terms acceptance columns to users table"""
    db_path = 'soulbridge.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing columns for terms acceptance
        columns_to_add = [
            ('terms_accepted', 'INTEGER DEFAULT 0'),
            ('terms_accepted_at', 'TIMESTAMP'),
            ('terms_version', 'TEXT DEFAULT "v1.0"'),
            ('terms_language', 'TEXT DEFAULT "en"')
        ]
        
        added_columns = []
        
        for column_name, column_def in columns_to_add:
            if column_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    added_columns.append(column_name)
                    print(f'✅ Added {column_name} column')
                except Exception as e:
                    print(f'❌ Failed to add {column_name}: {e}')
            else:
                print(f'ℹ️  Column {column_name} already exists')
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f'\n✅ Successfully added {len(added_columns)} columns: {", ".join(added_columns)}')
        else:
            print('\nℹ️  All terms acceptance columns already exist')
            
        print('✅ Terms acceptance database schema is ready!')
        return True
        
    except Exception as e:
        print(f'❌ Database schema fix failed: {e}')
        return False

if __name__ == '__main__':
    fix_terms_schema()