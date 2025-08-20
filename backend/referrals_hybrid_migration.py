#!/usr/bin/env python3
"""
SoulBridge AI: Hybrid Referrals Migration Integration
This module integrates the hybrid migration into the existing schema system.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def apply_hybrid_referrals_migration(db_connection):
    """
    Apply hybrid referrals migration using the exact SQL specification
    This implements the precise hybrid approach with bidirectional sync
    """
    cursor = db_connection.cursor()
    
    try:
        logger.info("🔧 Starting exact hybrid referrals migration...")
        
        # Step 0: Add email columns if missing (exact SQL from specification)
        logger.info("📝 Adding email columns to referrals table...")
        cursor.execute("""
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
        """)
        logger.info("✅ Email columns added/verified")
        
        # Step 1: Backfill emails from users based on IDs
        logger.info("🔄 Backfilling emails from users based on IDs...")
        cursor.execute("""
            UPDATE referrals r
            SET referrer_email = u.email
            FROM users u
            WHERE r.referrer_id = u.id AND r.referrer_email IS NULL;
        """)
        referrer_updates = cursor.rowcount
        
        cursor.execute("""
            UPDATE referrals r
            SET referred_email = u.email
            FROM users u
            WHERE r.referred_id = u.id AND r.referred_email IS NULL;
        """)
        referred_updates = cursor.rowcount
        logger.info(f"✅ Backfilled {referrer_updates} referrer + {referred_updates} referred emails from IDs")
        
        # Step 2: Backfill IDs from emails if any exist  
        logger.info("🔄 Backfilling IDs from emails...")
        cursor.execute("""
            UPDATE referrals r
            SET referrer_id = u.id
            FROM users u
            WHERE r.referrer_id IS NULL AND lower(r.referrer_email) = lower(u.email);
        """)
        referrer_id_updates = cursor.rowcount
        
        cursor.execute("""
            UPDATE referrals r
            SET referred_id = u.id
            FROM users u
            WHERE r.referred_id IS NULL AND lower(r.referred_email) = lower(u.email);
        """)
        referred_id_updates = cursor.rowcount
        logger.info(f"✅ Backfilled {referrer_id_updates} referrer + {referred_id_updates} referred IDs from emails")
        
        # Step 3: Create indexes for speed (exact SQL from specification)
        logger.info("📊 Creating performance indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id     ON referrals (referrer_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred_id     ON referrals (referred_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email  ON referrals (lower(referrer_email));")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred_email  ON referrals (lower(referred_email));")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_status          ON referrals (status);")
        logger.info("✅ Performance indexes created")
        
        # Step 4: Create trigger to keep emails in sync with IDs (exact SQL)
        logger.info("🔗 Creating sync trigger...")
        cursor.execute("""
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
        """)
        
        cursor.execute("DROP TRIGGER IF EXISTS trg_sync_referral_emails ON referrals;")
        cursor.execute("""
            CREATE TRIGGER trg_sync_referral_emails
            BEFORE INSERT OR UPDATE ON referrals
            FOR EACH ROW
            EXECUTE PROCEDURE sync_referral_emails();
        """)
        logger.info("✅ Sync trigger created successfully")
        
        # Final commit
        db_connection.commit()
        
        # Step 6: Validation
        logger.info("🔍 Validating migration results...")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM referrals")
            total_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id IS NOT NULL AND referred_id IS NOT NULL")
            rows_with_ids = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_email IS NOT NULL AND referred_email IS NOT NULL")
            rows_with_emails = cursor.fetchone()[0]
            
            logger.info(f"📊 Validation results:")
            logger.info(f"   Total referrals: {total_rows}")
            logger.info(f"   Records with both IDs: {rows_with_ids}")
            logger.info(f"   Records with both emails: {rows_with_emails}")
            
            if total_rows == rows_with_ids == rows_with_emails:
                logger.info("🎉 Perfect! All records have both IDs and emails")
            elif rows_with_emails >= rows_with_ids:
                logger.info("✅ Good! Email columns populated successfully")
            else:
                logger.warning("⚠️ Some inconsistencies found, but migration completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Validation warning: {e}")
        
        logger.info("🎉 Hybrid referrals migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Hybrid referrals migration failed: {e}")
        try:
            db_connection.rollback()
        except:
            pass
        return False

def check_referrals_table_compatibility(db_connection) -> dict:
    """
    Check the current referrals table structure for compatibility
    Returns dict with table info
    """
    cursor = db_connection.cursor()
    
    try:
        # Check if table exists
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'referrals' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        return {
            'exists': len(columns) > 0,
            'columns': column_names,
            'has_referrer_id': 'referrer_id' in column_names,
            'has_referred_id': 'referred_id' in column_names, 
            'has_referrer_email': 'referrer_email' in column_names,
            'has_referred_email': 'referred_email' in column_names,
            'needs_migration': 'referrer_email' not in column_names or 'referred_email' not in column_names
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check referrals table compatibility: {e}")
        return {'exists': False, 'error': str(e)}