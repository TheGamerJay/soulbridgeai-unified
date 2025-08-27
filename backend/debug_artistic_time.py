#!/usr/bin/env python3
"""
DEBUG SCRIPT: Artistic Time System
Comprehensive check for why artistic time shows 0
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from database_utils import get_database
from artistic_time_system import get_artistic_time, get_database_connection, ensure_user_artistic_time_data
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_artistic_time(user_id=104):
    """Debug artistic time for specific user"""
    print(f"\n🔍 DEBUGGING ARTISTIC TIME FOR USER {user_id}")
    print("=" * 60)
    
    # Test 1: Database Connection
    print("\n1. Testing Database Connections:")
    print("-" * 40)
    
    # Method 1: database_utils
    try:
        db = get_database()
        if db:
            conn = db.get_connection()
            print(f"✅ database_utils connection: SUCCESS ({type(db)})")
            print(f"   PostgreSQL mode: {getattr(db, 'use_postgres', 'Unknown')}")
            conn.close()
        else:
            print("❌ database_utils connection: FAILED")
    except Exception as e:
        print(f"❌ database_utils connection: ERROR - {e}")
    
    # Method 2: artistic_time_system connection
    try:
        conn = get_database_connection()
        if conn:
            print("✅ artistic_time_system connection: SUCCESS")
            conn.close()
        else:
            print("❌ artistic_time_system connection: FAILED")
    except Exception as e:
        print(f"❌ artistic_time_system connection: ERROR - {e}")
    
    # Test 2: Check User Data
    print(f"\n2. Checking User {user_id} Data:")
    print("-" * 40)
    
    try:
        db = get_database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get raw user data
        if db.use_postgres:
            cursor.execute("""
                SELECT id, email, user_plan, trial_active, trial_expires_at,
                       artistic_time, trial_credits, last_credit_reset,
                       created_at
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, email, user_plan, trial_active, trial_expires_at,
                       artistic_time, trial_credits, last_credit_reset,
                       created_at
                FROM users WHERE id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            print("✅ User found in database")
            user_id, email, plan, trial_active, trial_expires, artistic_time, trial_credits, last_reset, created = result
            print(f"   Email: {email}")
            print(f"   Plan: {plan}")
            print(f"   Trial Active: {trial_active}")
            print(f"   Trial Expires: {trial_expires}")
            print(f"   Artistic Time: {artistic_time}")
            print(f"   Trial Credits: {trial_credits}")
            print(f"   Last Reset: {last_reset}")
            print(f"   Created: {created}")
        else:
            print(f"❌ User {user_id} not found in database")
            return
        
        conn.close()
    except Exception as e:
        print(f"❌ Error checking user data: {e}")
        return
    
    # Test 3: Initialize User Data
    print(f"\n3. Ensuring User Data Initialization:")
    print("-" * 40)
    
    try:
        conn = get_database_connection()
        success = ensure_user_artistic_time_data(user_id, conn)
        conn.close()
        if success:
            print("✅ User data initialization: SUCCESS")
        else:
            print("❌ User data initialization: FAILED")
    except Exception as e:
        print(f"❌ User data initialization: ERROR - {e}")
    
    # Test 4: Get Artistic Time Balance
    print(f"\n4. Getting Artistic Time Balance:")
    print("-" * 40)
    
    try:
        balance = get_artistic_time(user_id)
        print(f"✅ Artistic Time Balance: {balance}")
        
        # Explain the balance
        if balance == 0:
            print("\n🔍 ZERO BALANCE ANALYSIS:")
            if plan == 'bronze' and not trial_active:
                print("   Bronze users get 0 monthly artistic time (expected)")
                print("   Trial required for Bronze users to get 60 credits")
            elif plan == 'bronze' and trial_active:
                print("   Bronze trial user should have 60 credits - something is wrong!")
            elif plan in ['silver', 'gold'] and artistic_time == 0:
                print(f"   {plan.title()} user should have monthly allowance - needs reset")
        else:
            print(f"   Balance looks good for {plan} user")
            
    except Exception as e:
        print(f"❌ Getting artistic time: ERROR - {e}")
    
    # Test 5: Check AI Image Generation Costs
    print(f"\n5. AI Image Generation Cost Check:")
    print("-" * 40)
    
    from artistic_time_system import get_feature_cost
    ai_image_cost = get_feature_cost("ai_images")
    print(f"   AI Images Cost: {ai_image_cost} credits")
    print(f"   User Balance: {balance} credits")
    if balance >= ai_image_cost:
        print("✅ User can afford AI image generation")
    else:
        needed = ai_image_cost - balance
        print(f"❌ User needs {needed} more credits for AI image generation")
    
    print(f"\n🎯 SUMMARY:")
    print("=" * 60)
    if balance > 0:
        print(f"✅ User {user_id} has {balance} artistic time credits")
    else:
        print(f"❌ User {user_id} has {balance} artistic time credits")
        if plan == 'bronze' and not trial_active:
            print("   💡 Solution: Start trial to get 60 credits")
        elif plan == 'bronze' and trial_active:
            print("   💡 Solution: Check trial_credits database field")
        else:
            print("   💡 Solution: Check monthly credit reset logic")

if __name__ == "__main__":
    # Default to user 104 or accept command line argument
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 104
    debug_artistic_time(user_id)