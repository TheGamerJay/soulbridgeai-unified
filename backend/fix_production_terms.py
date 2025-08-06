#!/usr/bin/env python3
"""
Fix terms acceptance schema in production PostgreSQL database
"""

import os
import psycopg2
from psycopg2 import sql

def fix_production_terms():
    """Add missing terms acceptance columns to production database"""
    
    # Check if we have DATABASE_URL (production)
    if 'DATABASE_URL' not in os.environ:
        print("❌ DATABASE_URL not found. Run this on production or set DATABASE_URL.")
        return False
    
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name LIKE '%terms%'
        """)
        existing_terms_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing terms columns: {existing_terms_columns}")
        
        # Add missing columns for terms acceptance
        columns_to_add = [
            ('terms_accepted', 'BOOLEAN DEFAULT FALSE'),
            ('terms_accepted_at', 'TIMESTAMP'),
            ('terms_version', 'VARCHAR(50) DEFAULT \'v1.0\''),
            ('terms_language', 'VARCHAR(10) DEFAULT \'en\'')
        ]
        
        added_columns = []
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_terms_columns:
                try:
                    cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
                    added_columns.append(column_name)
                    print(f'✅ Added {column_name} column')
                except Exception as e:
                    print(f'❌ Failed to add {column_name}: {e}')
            else:
                print(f'ℹ️  Column {column_name} already exists')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if added_columns:
            print(f'\n✅ Successfully added {len(added_columns)} columns: {", ".join(added_columns)}')
        else:
            print('\nℹ️  All terms acceptance columns already exist')
            
        print('✅ Production terms acceptance schema is ready!')
        return True
        
    except Exception as e:
        print(f'❌ Production database schema fix failed: {e}')
        return False

if __name__ == '__main__':
    fix_production_terms()