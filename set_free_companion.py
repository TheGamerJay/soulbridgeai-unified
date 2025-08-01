#!/usr/bin/env python3
"""
Set a free companion as selected for testing
"""

import os
import psycopg2
import json

def main():
    print("Setting free companion (GamerJay) as selected...")
    
    # Use environment variable for database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Set it with your Railway database connection string")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Set GamerJay (free companion) as selected
        cursor.execute("""
            UPDATE users
            SET companion_data = jsonb_build_object(
                'selected_companion', 'companion_gamerjay'
            )
            WHERE id = 17;
        """)
        
        # Verify the update
        cursor.execute("SELECT companion_data FROM users WHERE id = 17;")
        result = cursor.fetchone()
        if result:
            print(f"Updated companion_data: {result[0]}")
        
        conn.commit()
        print("\n✅ Free companion (GamerJay) set as selected!")
        print("🔄 Refresh your companion selector page to test")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()