#!/usr/bin/env python3
"""
Run Weekly Events Database Migration
Execute this script to add the weekly events tables and columns
"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.shared.database import get_database
from database_migrations.weekly_events_migration import migrate_weekly_events_tables

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Run the weekly events migration"""
    try:
        logger.info("🚀 Starting Weekly Events Migration...")
        
        # Get database connection
        db = get_database()
        if not db:
            logger.error("❌ Failed to get database connection")
            return False
        
        # Run the migration
        success = migrate_weekly_events_tables(
            db.get_connection(),
            use_postgres=db.use_postgres
        )
        
        if success:
            logger.info("✅ Weekly Events Migration completed successfully!")
            logger.info("🏆 'Most Appreciated Post This Week' event system is now ready!")
            logger.info("📊 Database tables created:")
            logger.info("   - weekly_events (event management)")
            logger.info("   - weekly_post_metrics (post performance tracking)")
            logger.info("   - event_participants (user participation)")
            logger.info("📈 Added columns to community_posts:")
            logger.info("   - weekly_event_id (event association)")
            logger.info("   - total_reactions (reaction count)")
            logger.info("   - unique_reactors (unique user count)")
            logger.info("   - reaction_score (calculated score)")
            logger.info("   - event_eligible (eligibility flag)")
            return True
        else:
            logger.error("❌ Migration failed!")
            return False
        
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)