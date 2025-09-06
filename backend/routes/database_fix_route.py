"""
Database Fix Route - Fix Railway PostgreSQL Schema Issues
"""

import logging
from flask import Blueprint, jsonify, request
import psycopg2
import os

# Create blueprint
db_fix_bp = Blueprint('db_fix', __name__)
logger = logging.getLogger(__name__)

@db_fix_bp.route('/api/admin/fix-database', methods=['POST'])
def fix_database_schema():
    """Fix database schema issues causing deployment failures"""
    
    # Simple protection - require secret key
    secret = request.headers.get('X-Fix-Secret')
    if secret != 'soulbridge-emergency-fix-2025':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            return jsonify({'error': 'DATABASE_URL not found'}), 500
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        fixes_applied = []
        
        # 1. Fix missing referrals column in users table
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS referrals INTEGER DEFAULT 0
            """)
            conn.commit()
            fixes_applied.append("Added referrals column to users table")
        except Exception as e:
            conn.rollback()
            fixes_applied.append(f"Referrals column issue: {str(e)}")
        
        # 2. Fix tier_limits table - ensure proper ID column
        try:
            # Check if table exists and structure
            cursor.execute("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'tier_limits'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # Check if id column is auto-increment
            has_serial_id = any(col for col in columns if col[0] == 'id' and 'nextval' in str(col[2]) if col[2] else False)
            
            if not has_serial_id:
                # Recreate table with proper ID
                cursor.execute("DROP TABLE IF EXISTS tier_limits CASCADE")
                cursor.execute("""
                    CREATE TABLE tier_limits (
                        id SERIAL PRIMARY KEY,
                        tier VARCHAR(20) NOT NULL,
                        feature VARCHAR(50) NOT NULL,
                        daily_limit INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(tier, feature)
                    )
                """)
                fixes_applied.append("Recreated tier_limits table with proper ID column")
            else:
                fixes_applied.append("tier_limits table structure is correct")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            fixes_applied.append(f"tier_limits fix issue: {str(e)}")
        
        # 3. Fix feature_usage table - standardize structure
        try:
            # Drop and recreate for consistent structure
            cursor.execute("DROP TABLE IF EXISTS feature_usage CASCADE")
            
            cursor.execute("""
                CREATE TABLE feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature VARCHAR(50) NOT NULL,
                    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    usage_count INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature, usage_date)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_feature_usage_user_feature_date 
                ON feature_usage(user_id, feature, usage_date)
            """)
            
            fixes_applied.append("Recreated feature_usage table with standardized structure")
            conn.commit()
        except Exception as e:
            conn.rollback()
            fixes_applied.append(f"feature_usage fix issue: {str(e)}")
        
        # 4. Ensure user_activity_log exists
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_type VARCHAR(50) NOT NULL,
                    session_duration_seconds INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_log_user_created
                ON user_activity_log(user_id, created_at)
            """)
            
            fixes_applied.append("Ensured user_activity_log table exists")
            conn.commit()
        except Exception as e:
            conn.rollback()
            fixes_applied.append(f"user_activity_log issue: {str(e)}")
        
        # 5. Populate tier_limits with default data
        try:
            default_limits = [
                ('bronze', 'decoder', 5),
                ('bronze', 'fortune', 5),
                ('bronze', 'horoscope', 5),
                ('bronze', 'creative_writer', 5),
                ('bronze', 'soul_riddle', 3),
                ('silver', 'decoder', 15),
                ('silver', 'fortune', 8),
                ('silver', 'horoscope', 10),
                ('silver', 'creative_writer', 20),
                ('silver', 'soul_riddle', 20),
                ('gold', 'decoder', 999),
                ('gold', 'fortune', 999),
                ('gold', 'horoscope', 999),
                ('gold', 'creative_writer', 999),
                ('gold', 'soul_riddle', 999)
            ]
            
            for tier, feature, limit in default_limits:
                cursor.execute("""
                    INSERT INTO tier_limits (tier, feature, daily_limit)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tier, feature) DO UPDATE SET 
                    daily_limit = EXCLUDED.daily_limit
                """, (tier, feature, limit))
            
            fixes_applied.append("Populated tier_limits with default data")
            conn.commit()
        except Exception as e:
            conn.rollback()
            fixes_applied.append(f"tier_limits population issue: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Database schema fixes applied',
            'fixes_applied': fixes_applied
        })
        
    except Exception as e:
        logger.error(f"Database fix route failed: {e}")
        return jsonify({'error': str(e)}), 500