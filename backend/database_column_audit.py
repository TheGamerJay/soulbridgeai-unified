#!/usr/bin/env python3
"""
Comprehensive Database Column Audit for SoulBridge AI
Checks for missing columns that could cause errors throughout the website
"""

import logging
from database_utils import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def audit_database_columns():
    """Perform comprehensive audit of all database tables and columns"""
    try:
        db = get_database()
        if not db:
            logger.error("Could not connect to database")
            return False
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        logger.info("🔍 Starting comprehensive database column audit...")
        
        # Get all tables
        if db.use_postgres:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Found {len(tables)} tables: {tables}")
        
        # Check each table structure
        missing_columns = []
        
        for table in tables:
            logger.info(f"\n🔍 Auditing table: {table}")
            
            # Get current columns
            if db.use_postgres:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table,))
            else:
                cursor.execute(f"PRAGMA table_info({table})")
            
            columns = cursor.fetchall()
            current_columns = [col[0] if db.use_postgres else col[1] for col in columns]
            logger.info(f"   Current columns: {current_columns}")
            
            # Define expected columns for each table based on codebase analysis
            expected_columns = get_expected_columns(table)
            
            if expected_columns:
                missing = set(expected_columns) - set(current_columns)
                if missing:
                    missing_columns.append((table, list(missing)))
                    logger.warning(f"   ❌ Missing columns in {table}: {list(missing)}")
                else:
                    logger.info(f"   ✅ All expected columns present in {table}")
        
        # Check for commonly referenced columns across all queries
        logger.info(f"\n🔍 Checking for commonly referenced columns...")
        common_issues = check_common_column_issues(cursor, db)
        
        conn.close()
        
        # Summary
        logger.info(f"\n📋 AUDIT SUMMARY:")
        logger.info(f"   Tables audited: {len(tables)}")
        logger.info(f"   Tables with missing columns: {len(missing_columns)}")
        
        if missing_columns:
            logger.warning(f"\n❌ MISSING COLUMNS FOUND:")
            for table, cols in missing_columns:
                logger.warning(f"   {table}: {cols}")
        
        if common_issues:
            logger.warning(f"\n❌ COMMON COLUMN ISSUES:")
            for issue in common_issues:
                logger.warning(f"   {issue}")
        
        if not missing_columns and not common_issues:
            logger.info(f"   ✅ All expected columns are present!")
        
        return len(missing_columns) == 0 and len(common_issues) == 0
        
    except Exception as e:
        logger.error(f"Database column audit failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_expected_columns(table_name):
    """Return expected columns for each table based on codebase analysis"""
    expected = {
        'users': [
            'id', 'email', 'password', 'user_plan', 'trial_active', 'trial_expires_at',
            'trial_used_permanently', 'created_at', 'last_login', 'artistic_credits',
            'referrals', 'credits', 'companion_data', 'profile_image_url'
        ],
        'tier_limits': [
            'id', 'tier', 'feature', 'daily_limit'
        ],
        'feature_usage': [
            'id', 'user_id', 'feature', 'usage_date', 'usage_count', 'created_at'
        ],
        'user_activity': [
            'id', 'user_id', 'activity_time', 'activity_type'
        ],
        'community_posts': [
            'id', 'user_id', 'content', 'companion_id', 'is_anonymous', 'created_at'
        ],
        'post_reactions': [
            'id', 'post_id', 'user_id', 'reaction_type', 'created_at'
        ],
        'lyric_embeddings': [
            'id', 'lyric_text', 'embedding', 'metadata', 'created_at'
        ]
    }
    
    return expected.get(table_name, [])

def check_common_column_issues(cursor, db):
    """Check for common column issues that cause errors"""
    issues = []
    
    try:
        # Test common queries that have been causing issues
        test_queries = [
            ("users", "SELECT id, email, user_plan, trial_active, trial_expires_at, COALESCE(referrals, 0) as referrals, COALESCE(credits, 0) as credits FROM users LIMIT 1"),
            ("users", "SELECT artistic_credits FROM users LIMIT 1"),
            ("users", "SELECT companion_data FROM users LIMIT 1"),
            ("users", "SELECT profile_image_url FROM users LIMIT 1"),
            ("tier_limits", "SELECT tier, feature, daily_limit FROM tier_limits LIMIT 1"),
            ("feature_usage", "SELECT user_id, feature, usage_date FROM feature_usage LIMIT 1"),
        ]
        
        for table, query in test_queries:
            try:
                cursor.execute(query)
                cursor.fetchone()
            except Exception as e:
                if "does not exist" in str(e) or "no such column" in str(e):
                    issues.append(f"Query failed for {table}: {str(e)}")
    
    except Exception as e:
        issues.append(f"Error testing common queries: {str(e)}")
    
    return issues

if __name__ == "__main__":
    success = audit_database_columns()
    if success:
        print("✅ Database column audit passed - no missing columns found!")
    else:
        print("❌ Database column audit found issues that need to be fixed!")
        exit(1)