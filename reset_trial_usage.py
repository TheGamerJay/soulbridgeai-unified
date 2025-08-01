#!/usr/bin/env python3
"""
Reset trial usage flags to allow 5-hour trial again
"""

import os
import psycopg2
import json

def main():
    print("Resetting trial usage flags...")
    
    # Use environment variable for database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Set it with your Railway database connection string")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check current data
        print("Current companion_data:")
        cursor.execute("SELECT companion_data FROM users WHERE id = 17;")
        result = cursor.fetchone()
        if result:
            print(f"Before: {result[0]}")
        
        # Reset trial usage flags - allow trial again
        cursor.execute("""
            UPDATE users
            SET companion_data = jsonb_build_object(
                'trial_active', false,
                'trial_companion', null,
                'trial_expires', null,
                'selected_companion', 'companion_gamerjay',
                'trial_used_permanently', false
            )
            WHERE id = 17;
        """)
        
        # Verify the reset
        cursor.execute("SELECT companion_data FROM users WHERE id = 17;")
        result = cursor.fetchone()
        if result:
            print(f"After: {result[0]}")
        
        conn.commit()
        print("\n✅ Trial usage flags reset successfully!")
        print("💡 You should also clear browser localStorage by opening DevTools > Application > Local Storage > Clear All")
        print("🔄 Then refresh the page and try the 5-hour trial again")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()