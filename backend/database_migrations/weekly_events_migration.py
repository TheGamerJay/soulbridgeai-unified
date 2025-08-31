"""
Weekly Events Database Migration
Adds tables and columns needed for "This Week's Most Liked Post" event system
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def migrate_weekly_events_tables(db_connection, use_postgres=True):
    """Add tables and columns for weekly events system"""
    try:
        logger.info("🏆 Starting weekly events database migration...")
        
        # 1. Create weekly_events table for event management
        if use_postgres:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS weekly_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('upcoming', 'active', 'ended', 'cancelled')),
                    winner_post_id INTEGER,
                    winner_user_id INTEGER,
                    winner_prize_type VARCHAR(50),
                    winner_prize_value TEXT,
                    total_participants INTEGER DEFAULT 0,
                    total_reactions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_dates ON weekly_events(start_date, end_date)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_status ON weekly_events(status)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_type ON weekly_events(event_type)")
        else:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS weekly_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active' CHECK (status IN ('upcoming', 'active', 'ended', 'cancelled')),
                    winner_post_id INTEGER,
                    winner_user_id INTEGER,
                    winner_prize_type TEXT,
                    winner_prize_value TEXT,
                    total_participants INTEGER DEFAULT 0,
                    total_reactions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_dates ON weekly_events(start_date, end_date)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_status ON weekly_events(status)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_events_type ON weekly_events(event_type)")
        
        # 2. Create weekly_post_metrics table for tracking post performance during events
        if use_postgres:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS weekly_post_metrics (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    post_created_at TIMESTAMP NOT NULL,
                    total_reactions INTEGER DEFAULT 0,
                    unique_reactors INTEGER DEFAULT 0,
                    reaction_breakdown JSONB DEFAULT '{}',
                    daily_reaction_counts JSONB DEFAULT '{}',
                    peak_reactions_day DATE,
                    peak_reactions_count INTEGER DEFAULT 0,
                    final_score DECIMAL(10,2) DEFAULT 0.00,
                    ranking_position INTEGER,
                    is_winner BOOLEAN DEFAULT FALSE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (event_id) REFERENCES weekly_events(id) ON DELETE CASCADE,
                    UNIQUE(event_id, post_id)
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_event ON weekly_post_metrics(event_id)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_score ON weekly_post_metrics(event_id, final_score DESC)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_reactions ON weekly_post_metrics(event_id, total_reactions DESC)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_user ON weekly_post_metrics(user_id)")
        else:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS weekly_post_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    post_created_at TIMESTAMP NOT NULL,
                    total_reactions INTEGER DEFAULT 0,
                    unique_reactors INTEGER DEFAULT 0,
                    reaction_breakdown TEXT DEFAULT '{}',
                    daily_reaction_counts TEXT DEFAULT '{}',
                    peak_reactions_day TEXT,
                    peak_reactions_count INTEGER DEFAULT 0,
                    final_score REAL DEFAULT 0.00,
                    ranking_position INTEGER,
                    is_winner INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (event_id) REFERENCES weekly_events(id) ON DELETE CASCADE,
                    UNIQUE(event_id, post_id)
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_event ON weekly_post_metrics(event_id)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_score ON weekly_post_metrics(event_id, final_score DESC)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_reactions ON weekly_post_metrics(event_id, total_reactions DESC)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_weekly_post_metrics_user ON weekly_post_metrics(user_id)")
        
        # 3. Create event_participants table for tracking who participated
        if use_postgres:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS event_participants (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    companion_id TEXT,
                    posts_submitted INTEGER DEFAULT 0,
                    total_reactions_received INTEGER DEFAULT 0,
                    best_post_id INTEGER,
                    best_post_score DECIMAL(10,2) DEFAULT 0.00,
                    participation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_eligible BOOLEAN DEFAULT TRUE,
                    
                    FOREIGN KEY (event_id) REFERENCES weekly_events(id) ON DELETE CASCADE,
                    UNIQUE(event_id, user_id)
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_event_participants_event ON event_participants(event_id)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_event_participants_score ON event_participants(event_id, best_post_score DESC)")
        else:
            db_connection.execute("""
                CREATE TABLE IF NOT EXISTS event_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    companion_id TEXT,
                    posts_submitted INTEGER DEFAULT 0,
                    total_reactions_received INTEGER DEFAULT 0,
                    best_post_id INTEGER,
                    best_post_score REAL DEFAULT 0.00,
                    participation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_eligible INTEGER DEFAULT 1,
                    
                    FOREIGN KEY (event_id) REFERENCES weekly_events(id) ON DELETE CASCADE,
                    UNIQUE(event_id, user_id)
                )
            """)
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_event_participants_event ON event_participants(event_id)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_event_participants_score ON event_participants(event_id, best_post_score DESC)")
        
        # 4. Add new columns to existing community_posts table for event tracking
        try:
            if use_postgres:
                db_connection.execute("""
                    ALTER TABLE community_posts 
                    ADD COLUMN IF NOT EXISTS weekly_event_id INTEGER,
                    ADD COLUMN IF NOT EXISTS total_reactions INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS unique_reactors INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS reaction_score DECIMAL(10,2) DEFAULT 0.00,
                    ADD COLUMN IF NOT EXISTS event_eligible BOOLEAN DEFAULT TRUE
                """)
                try:
                    db_connection.execute("""
                        ALTER TABLE community_posts 
                        ADD CONSTRAINT fk_community_posts_weekly_event 
                        FOREIGN KEY (weekly_event_id) REFERENCES weekly_events(id) ON DELETE SET NULL
                    """)
                except Exception:
                    # Constraint might already exist
                    pass
            else:
                # SQLite doesn't support adding multiple columns at once
                columns_to_add = [
                    "ALTER TABLE community_posts ADD COLUMN weekly_event_id INTEGER",
                    "ALTER TABLE community_posts ADD COLUMN total_reactions INTEGER DEFAULT 0",
                    "ALTER TABLE community_posts ADD COLUMN unique_reactors INTEGER DEFAULT 0", 
                    "ALTER TABLE community_posts ADD COLUMN reaction_score REAL DEFAULT 0.00",
                    "ALTER TABLE community_posts ADD COLUMN event_eligible INTEGER DEFAULT 1"
                ]
                
                for col_sql in columns_to_add:
                    try:
                        db_connection.execute(col_sql)
                    except Exception:
                        # Column might already exist, continue
                        pass
        except Exception as e:
            logger.warning(f"Some columns may already exist: {e}")
        
        # 5. Add indexes for performance
        try:
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_community_posts_event ON community_posts(weekly_event_id)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_community_posts_reactions ON community_posts(total_reactions DESC)")  
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_community_posts_score ON community_posts(reaction_score DESC)")
            db_connection.execute("CREATE INDEX IF NOT EXISTS idx_community_posts_created_event ON community_posts(created_at, weekly_event_id)")
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")
        
        # 6. Create initial "This Week's Most Liked Post" event
        now = datetime.now()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7) - timedelta(microseconds=1)
        
        if use_postgres:
            db_connection.execute("""
                INSERT INTO weekly_events (event_type, title, description, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                'most_appreciated_post',
                'Most Appreciated Post This Week 🏆',
                'Share your most meaningful content with the community! The post that receives the most genuine appreciation wins special recognition and rewards.',
                week_start,
                week_end,
                'active'
            ))
        else:
            db_connection.execute("""
                INSERT OR IGNORE INTO weekly_events (event_type, title, description, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'most_appreciated_post',
                'Most Appreciated Post This Week 🏆',
                'Share your most meaningful content with the community! The post that receives the most genuine appreciation wins special recognition and rewards.',
                week_start.isoformat(),
                week_end.isoformat(),
                'active'
            ))
        
        db_connection.commit()
        logger.info("✅ Weekly events migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Weekly events migration failed: {e}")
        db_connection.rollback()
        return False

def rollback_weekly_events_migration(db_connection):
    """Rollback the weekly events migration (for development/testing)"""
    try:
        logger.info("🔄 Rolling back weekly events migration...")
        
        # Drop tables in reverse order due to foreign keys
        tables_to_drop = [
            'event_participants',
            'weekly_post_metrics', 
            'weekly_events'
        ]
        
        for table in tables_to_drop:
            db_connection.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Remove added columns (SQLite doesn't support DROP COLUMN easily, so we'll skip this)
        logger.info("⚠️ Note: Added columns to community_posts table were not removed (SQLite limitation)")
        
        db_connection.commit()
        logger.info("✅ Weekly events migration rollback completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False