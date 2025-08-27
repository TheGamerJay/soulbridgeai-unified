#!/usr/bin/env python3
"""
Fix artistic time allocation based on user tier system
Allocates proper monthly artistic time credits to Silver and Gold users
"""

import os
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_artistic_time_allocation():
    """Allocate artistic time based on user tiers"""
    db_path = "soulbridge.db"
    
    if not os.path.exists(db_path):
        logger.error(f"❌ Database file {db_path} not found")
        return False
    
    try:
        logger.info("🎨 Fixing artistic time allocation based on user tiers...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users with their current status
        cursor.execute("""
            SELECT id, email, user_plan, plan, artistic_time, trial_active 
            FROM users
        """)
        users = cursor.fetchall()
        
        updated_count = 0
        
        for user in users:
            user_id, email, user_plan, plan, current_artistic, trial_active = user
            
            # Determine effective plan (prioritize user_plan, fallback to plan)
            effective_plan = user_plan or plan or 'bronze'
            
            # Map old tier names to new ones
            plan_mapping = {
                'free': 'bronze',
                'growth': 'silver', 
                'max': 'gold',
                'foundation': 'bronze'
            }
            
            effective_plan = plan_mapping.get(effective_plan, effective_plan)
            
            # Determine artistic time allocation
            if effective_plan == 'silver':
                target_artistic = 200
            elif effective_plan == 'gold':
                target_artistic = 500
            else:  # bronze or any other
                target_artistic = 0
            
            # Update if needed
            if current_artistic != target_artistic:
                cursor.execute("""
                    UPDATE users 
                    SET artistic_time = ?, last_credit_reset = ?
                    WHERE id = ?
                """, (target_artistic, datetime.now().date(), user_id))
                
                logger.info(f"✅ Updated {email}: {effective_plan} tier → {target_artistic} artistic time")
                updated_count += 1
            else:
                logger.info(f"✓ {email}: {effective_plan} tier already has correct {target_artistic} artistic time")
        
        # Commit changes
        conn.commit()
        
        # Show final results
        cursor.execute("""
            SELECT user_plan, plan, COUNT(*) as count, AVG(artistic_time) as avg_artistic
            FROM users 
            GROUP BY user_plan, plan
        """)
        results = cursor.fetchall()
        
        logger.info("📊 Final allocation summary:")
        for row in results:
            user_plan, plan, count, avg_artistic = row
            effective = user_plan or plan
            logger.info(f"  {effective}: {count} users, avg {avg_artistic:.0f} artistic time")
        
        conn.close()
        
        logger.info(f"🎉 Updated {updated_count} users with correct artistic time allocation")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing artistic time allocation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_artistic_time_allocation()