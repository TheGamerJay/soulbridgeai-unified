# migrations_bronze_silver_gold.py
# Safe, idempotent migrations for Bronze/Silver/Gold tier system

import logging

logger = logging.getLogger(__name__)

def run_bsg_migrations(get_database):
    """
    Run Bronze/Silver/Gold schema migrations.
    Idempotent - safe to run multiple times.
    Supports both PostgreSQL and SQLite.
    """
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for BSG migrations")
            return False
            
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            
            if db.use_postgres:
                logger.info("Running PostgreSQL BSG migrations...")
                
                # Add columns with IF NOT EXISTS (PostgreSQL)
                cur.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'bronze';
                """)
                cur.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
                """)
                cur.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_active BOOLEAN DEFAULT FALSE;
                """)
                cur.execute("""
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ;
                """)
                
                # Create index if not exists
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users (stripe_customer_id);
                """)
                
                conn.commit()
                logger.info("✅ PostgreSQL BSG migrations completed successfully")
                
            else:
                logger.info("Running SQLite BSG migrations...")
                
                # SQLite: additive ALTERs, each in try/except (older SQLite lacks IF NOT EXISTS on columns)
                migration_statements = [
                    "ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'bronze';",
                    "ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;",
                    "ALTER TABLE users ADD COLUMN trial_active INTEGER DEFAULT 0;",  # boolean as 0/1
                    "ALTER TABLE users ADD COLUMN trial_expires_at TEXT;"  # ISO8601 string
                ]
                
                for stmt in migration_statements:
                    try:
                        cur.execute(stmt)
                        conn.commit()
                        logger.info(f"✅ Executed: {stmt}")
                    except Exception as e:
                        # Column might already exist - this is expected
                        conn.rollback()
                        logger.info(f"ℹ️ Skipped (already exists): {stmt} - {e}")
                
                # Index (SQLite auto-ignores if exists in newer versions)
                try:
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users (stripe_customer_id);")
                    conn.commit()
                    logger.info("✅ Created index idx_users_stripe_customer_id")
                except Exception as e:
                    conn.rollback()
                    logger.info(f"ℹ️ Index creation skipped: {e}")
                
                logger.info("✅ SQLite BSG migrations completed successfully")
            
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ BSG migrations failed: {e}")
        return False

def verify_bsg_schema(get_database):
    """
    Verify that BSG schema columns exist.
    Returns dict with column availability status.
    """
    try:
        db = get_database()
        if not db:
            return {"error": "Database not available"}
            
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            
            if db.use_postgres:
                # Check column existence in PostgreSQL
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name IN ('plan', 'stripe_customer_id', 'trial_active', 'trial_expires_at')
                """)
                existing_columns = [row[0] for row in cur.fetchall()]
            else:
                # Check column existence in SQLite
                cur.execute("PRAGMA table_info(users)")
                existing_columns = [row[1] for row in cur.fetchall() if row[1] in ['plan', 'stripe_customer_id', 'trial_active', 'trial_expires_at']]
            
            required_columns = ['plan', 'stripe_customer_id', 'trial_active', 'trial_expires_at']
            status = {col: col in existing_columns for col in required_columns}
            status['all_present'] = all(status.values())
            
            return status
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ BSG schema verification failed: {e}")
        return {"error": str(e)}