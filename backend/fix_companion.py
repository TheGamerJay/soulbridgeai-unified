#!/usr/bin/env python3
"""
Quick fix script to update companion persistence data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_utils import get_database
from display_name_helpers import get_companion_data, set_companion_data
import json

def main():
    print("Checking current companion data...")
    
    # Assuming user ID 1 - adjust if needed
    user_id = 1
    
    # Get current companion data
    current_data = get_companion_data(user_id)
    print(f"Current companion data: {current_data}")
    
    # Get database connection to check raw data
    db = get_database()
    if db:
        conn = db.get_connection()
        cur = conn.cursor()
        
        # Check both old and new systems
        cur.execute("SELECT selected_companion, companion_data FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()
        if result:
            print(f"Old system (selected_companion): {result[0]}")
            print(f"New system (companion_data): {result[1]}")
        
        # Update to Claude (as an example)
        claude_data = {
            'companion_id': 'claude',
            'name': 'Claude',
            'tier': 'bronze'
        }
        
        print(f"Updating companion data to: {claude_data}")
        success = set_companion_data(user_id, claude_data)
        
        if success:
            print("Companion data updated successfully!")
            
            # Verify the update
            updated_data = get_companion_data(user_id)
            print(f"New companion data: {updated_data}")
        else:
            print("Failed to update companion data")
    
    else:
        print("Could not connect to database")

if __name__ == "__main__":
    main()