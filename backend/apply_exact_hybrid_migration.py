#!/usr/bin/env python3
"""
Apply the exact hybrid referrals migration SQL provided
This uses the precise SQL statements from the user specification
"""

import os
import logging
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# The exact migration SQL as specified
MIGRATION_SQL = """
-- 0) Add email columns if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='referrals' AND column_name='referrer_email') THEN
        ALTER TABLE referrals ADD COLUMN referrer_email VARCHAR(255);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='referrals' AND column_name='referred_email') THEN
        ALTER TABLE referrals ADD COLUMN referred_email VARCHAR(255);
    END IF;
END $$;

-- 1) Backfill emails from users based on IDs
UPDATE referrals r
SET referrer_email = u.email
FROM users u
WHERE r.referrer_id = u.id AND r.referrer_email IS NULL;

UPDATE referrals r
SET referred_email = u.email
FROM users u
WHERE r.referred_id = u.id AND r.referred_email IS NULL;

-- 2) Backfill IDs from emails if any exist
UPDATE referrals r
SET referrer_id = u.id
FROM users u
WHERE r.referrer_id IS NULL AND lower(r.referrer_email) = lower(u.email);

UPDATE referrals r
SET referred_id = u.id
FROM users u
WHERE r.referred_id IS NULL AND lower(r.referred_email) = lower(u.email);

-- 3) Indexes for speed
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id     ON referrals (referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id     ON referrals (referred_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email  ON referrals (lower(referrer_email));
CREATE INDEX IF NOT EXISTS idx_referrals_referred_email  ON referrals (lower(referred_email));
CREATE INDEX IF NOT EXISTS idx_referrals_status          ON referrals (status);

-- 4) Trigger to keep emails in sync with IDs
CREATE OR REPLACE FUNCTION sync_referral_emails() RETURNS trigger AS $$
BEGIN
  IF NEW.referrer_id IS NOT NULL THEN
    SELECT email INTO NEW.referrer_email FROM users WHERE id = NEW.referrer_id;
  END IF;
  IF NEW.referred_id IS NOT NULL THEN
    SELECT email INTO NEW.referred_email FROM users WHERE id = NEW.referred_id;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_referral_emails ON referrals;
CREATE TRIGGER trg_sync_referral_emails
BEFORE INSERT OR UPDATE ON referrals
FOR EACH ROW
EXECUTE PROCEDURE sync_referral_emails();
"""

def apply_migration_directly():
    """Apply migration using direct PostgreSQL connection"""
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("💡 Set DATABASE_URL to your PostgreSQL connection string")
        return False
    
    try:
        logger.info("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        
        logger.info("🚀 Starting hybrid referrals migration...")
        
        with conn.cursor() as cursor:
            # Execute the complete migration
            cursor.execute(MIGRATION_SQL)
            
        # Commit the transaction
        conn.commit()
        logger.info("✅ Migration committed successfully")
        
        # Validate results
        logger.info("🔍 Validating migration...")
        with conn.cursor() as cursor:
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'referrals' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            logger.info("📋 Referrals table columns:")
            for col_name, data_type in columns:
                logger.info(f"   - {col_name}: {data_type}")
            
            # Check indexes
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'referrals' 
                ORDER BY indexname
            """)
            indexes = cursor.fetchall()
            logger.info("📊 Referrals table indexes:")
            for (idx_name,) in indexes:
                logger.info(f"   - {idx_name}")
            
            # Check row counts
            cursor.execute("SELECT COUNT(*) FROM referrals")
            total_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_email IS NOT NULL")
            email_rows = cursor.fetchone()[0]
            
            logger.info(f"📊 Data validation:")
            logger.info(f"   - Total referrals: {total_rows}")
            logger.info(f"   - With referrer_email: {email_rows}")
            
        conn.close()
        logger.info("🎉 Hybrid referrals migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 SoulBridge AI - Exact Hybrid Referrals Migration")
    print("=" * 60)
    print()
    print("This will apply the exact hybrid migration SQL you provided:")
    print("✅ Add referrer_email/referred_email columns")  
    print("✅ Backfill data bidirectionally (IDs ↔ emails)")
    print("✅ Create performance indexes")
    print("✅ Install sync trigger")
    print()
    
    # Check for DATABASE_URL
    if not os.environ.get('DATABASE_URL'):
        print("❌ DATABASE_URL not found in environment")
        print("💡 This migration requires a direct PostgreSQL connection")
        print("   Set DATABASE_URL=postgresql://user:pass@host:port/db")
        return 1
    
    success = apply_migration_directly()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: Hybrid migration completed!")
        print("=" * 60)
        print("\n✅ What's now available:")
        print("   - referrer_id/referred_id (FKs to users.id)")
        print("   - referrer_email/referred_email (for app compatibility)")  
        print("   - Automatic sync via PostgreSQL trigger")
        print("   - Optimized indexes for both query patterns")
        print("\n🚀 Your app code should work immediately!")
        print("   - Legacy queries: WHERE referrer_email = '...'")
        print("   - Future queries: JOIN users ON referrer_id")
        print("\n📈 Next: Deploy and test referrals functionality")
        return 0
    else:
        print("\n❌ FAILED: Migration encountered errors")
        print("   Check the logs above for details")
        return 1

if __name__ == "__main__":
    exit(main())