#!/usr/bin/env python3
"""
Fix artistic time allocation for production database
Works with both SQLite and PostgreSQL databases
"""

import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_production_artistic_time():
    """Fix artistic time allocation in production database"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production PostgreSQL
        try:
            import psycopg2
            
            # Fix postgres:// URL format
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            logger.info("🐘 Connecting to PostgreSQL production database...")
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Get all users with their current status
            cursor.execute("""
                SELECT id, email, user_plan, artistic_time, trial_active 
                FROM users
            """)
            users = cursor.fetchall()
            
            updated_count = 0
            
            for user in users:
                user_id, email, user_plan, current_artistic, trial_active = user
                
                # Determine effective plan
                effective_plan = user_plan or 'bronze'
                
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
                        SET artistic_time = %s, last_credit_reset = %s
                        WHERE id = %s
                    """, (target_artistic, datetime.now().date(), user_id))
                    
                    logger.info(f"✅ Updated {email}: {effective_plan} tier → {target_artistic} artistic time")
                    updated_count += 1
            
            # Commit changes
            conn.commit()
            conn.close()
            
            logger.info(f"🎉 Production database: Updated {updated_count} users")
            return True
            
        except Exception as e:
            logger.error(f"❌ Production database error: {e}")
            return False
    
    else:
        # Local SQLite
        try:
            import sqlite3
            
            if not os.path.exists('soulbridge.db'):
                logger.error("❌ Local database not found")
                return False
            
            logger.info("🗄️ Updating local SQLite database...")
            conn = sqlite3.connect('soulbridge.db')
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
            
            # Commit changes
            conn.commit()
            conn.close()
            
            logger.info(f"🎉 Local database: Updated {updated_count} users")
            return True
            
        except Exception as e:
            logger.error(f"❌ Local database error: {e}")
            return False

if __name__ == "__main__":
    fix_production_artistic_time()