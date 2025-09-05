#!/usr/bin/env python3
"""
Fix tier_limits constraint violation - properly handle the id column
"""

import logging
from database_utils import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_tier_limits_constraint():
    """Fix the tier_limits constraint violation"""
    try:
        db = get_database()
        if not db:
            logger.error("Could not connect to database")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        logger.info("Fixing tier_limits constraint issue...")
        
        # First, clear any existing data that might be causing issues
        cursor.execute("DELETE FROM tier_limits")
        
        if db.use_postgres:
            # For PostgreSQL, make sure sequence is reset
            cursor.execute("ALTER SEQUENCE tier_limits_id_seq RESTART WITH 1")
            
            # Insert data one by one to ensure proper ID generation
            tier_limits_data = [
                ('bronze', 'decoder', 5),
                ('bronze', 'fortune', 5),
                ('bronze', 'horoscope', 5),
                ('bronze', 'creative_writer', 5),
                ('silver', 'decoder', 15),
                ('silver', 'fortune', 8),
                ('silver', 'horoscope', 10),
                ('silver', 'creative_writer', 20),
                ('gold', 'decoder', -1),  # -1 means unlimited
                ('gold', 'fortune', -1),
                ('gold', 'horoscope', -1),
                ('gold', 'creative_writer', -1),
            ]
            
            for tier, feature, limit in tier_limits_data:
                cursor.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (%s, %s, %s)
                """, (tier, feature, limit))
                
        else:
            # SQLite - similar approach
            tier_limits_data = [
                ('bronze', 'decoder', 5),
                ('bronze', 'fortune', 5),
                ('bronze', 'horoscope', 5),
                ('bronze', 'creative_writer', 5),
                ('silver', 'decoder', 15),
                ('silver', 'fortune', 8),
                ('silver', 'horoscope', 10),
                ('silver', 'creative_writer', 20),
                ('gold', 'decoder', -1),  # -1 means unlimited
                ('gold', 'fortune', -1),
                ('gold', 'horoscope', -1),
                ('gold', 'creative_writer', -1),
            ]
            
            for tier, feature, limit in tier_limits_data:
                cursor.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (?, ?, ?)
                """, (tier, feature, limit))
        
        # Commit changes
        conn.commit()
        
        # Verify the data was inserted correctly
        cursor.execute("SELECT COUNT(*) FROM tier_limits")
        count = cursor.fetchone()[0]
        logger.info(f"Successfully inserted {count} tier limit records")
        
        # Show sample data
        cursor.execute("SELECT * FROM tier_limits LIMIT 5")
        sample_data = cursor.fetchall()
        logger.info(f"Sample tier_limits data: {sample_data}")
        
        conn.close()
        logger.info("Tier limits constraint fix completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Tier limits constraint fix failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = fix_tier_limits_constraint()
    if success:
        print("✅ Tier limits constraint fixed successfully!")
    else:
        print("❌ Tier limits constraint fix failed!")
        exit(1)