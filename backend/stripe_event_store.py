# stripe_event_store.py
# Event deduplication store for Stripe webhooks

import logging
from datetime import datetime, timezone
from app import get_database
from sql_utils import adapt_placeholders, to_db_ts

logger = logging.getLogger(__name__)

def ensure_stripe_events_table():
    """
    Create stripe_events table for deduplication if it doesn't exist.
    Idempotent - safe to call multiple times.
    """
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for stripe_events table creation")
            return False
            
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            
            if db.use_postgres:
                # PostgreSQL
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stripe_events (
                        id TEXT PRIMARY KEY,
                        received_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT,
                        processed BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Create index for cleanup queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stripe_events_received_at 
                    ON stripe_events (received_at)
                """)
            else:
                # SQLite
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stripe_events (
                        id TEXT PRIMARY KEY,
                        received_at TEXT DEFAULT (datetime('now')),
                        event_type TEXT,
                        processed INTEGER DEFAULT 1
                    )
                """)
                
                # Create index for cleanup queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stripe_events_received_at 
                    ON stripe_events (received_at)
                """)
            
            conn.commit()
            logger.info("✅ stripe_events table ensured")
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to create stripe_events table: {e}")
        return False

def has_processed(event_id: str) -> bool:
    """
    Check if we've already processed this Stripe event.
    Returns True if event has been processed before.
    """
    if not event_id:
        return False
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for event deduplication")
            return False
            
        conn = db.get_connection()
        try:
            q = "SELECT 1 FROM stripe_events WHERE id = %s"
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (event_id,))
            result = cur.fetchone()
            
            already_processed = result is not None
            if already_processed:
                logger.info(f"⚠️ Stripe event {event_id} already processed, skipping")
            
            return already_processed
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Error checking event deduplication for {event_id}: {e}")
        # On error, assume not processed to avoid missing events
        return False

def mark_processed(event_id: str, event_type: str = None) -> bool:
    """
    Mark a Stripe event as processed to prevent duplicate handling.
    Returns True if successfully marked.
    """
    if not event_id:
        return False
        
    try:
        db = get_database()
        if not db:
            logger.warning("Database not available for event marking")
            return False
            
        # Ensure table exists
        ensure_stripe_events_table()
        
        conn = db.get_connection()
        try:
            q = """
                INSERT INTO stripe_events (id, event_type, received_at, processed) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """
            
            if not db.use_postgres:
                # SQLite uses INSERT OR IGNORE
                q = """
                    INSERT OR IGNORE INTO stripe_events (id, event_type, received_at, processed) 
                    VALUES (%s, %s, %s, %s)
                """
            
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            
            now = to_db_ts(db, datetime.now(timezone.utc))
            processed_flag = 1 if not db.use_postgres else True
            
            cur.execute(q, (event_id, event_type, now, processed_flag))
            conn.commit()
            
            logger.info(f"✅ Marked Stripe event {event_id} as processed")
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Error marking event {event_id} as processed: {e}")
        return False

def cleanup_old_events(days_old: int = 30) -> int:
    """
    Clean up stripe_events older than specified days.
    Returns number of events deleted.
    """
    try:
        db = get_database()
        if not db:
            return 0
            
        conn = db.get_connection()
        try:
            if db.use_postgres:
                q = "DELETE FROM stripe_events WHERE received_at < NOW() - INTERVAL '%s days'"
            else:
                q = "DELETE FROM stripe_events WHERE received_at < datetime('now', '-%s days')"
            
            q = adapt_placeholders(db, q)
            cur = conn.cursor()
            cur.execute(q, (days_old,))
            
            deleted_count = cur.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old Stripe events")
            
            return deleted_count
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Error cleaning up old Stripe events: {e}")
        return 0