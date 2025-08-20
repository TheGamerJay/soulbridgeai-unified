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
    Apply hybrid referrals migration to add email columns and sync triggers
    This function is designed to be called from the main schema initialization
    """
    cursor = db_connection.cursor()
    
    try:
        logger.info("🔧 Starting hybrid referrals migration...")
        
        # Step 1: Add email columns if missing
        logger.info("📝 Adding email columns to referrals table...")
        
        try:
            cursor.execute("""
                ALTER TABLE referrals 
                ADD COLUMN IF NOT EXISTS referrer_email VARCHAR(255)
            """)
            logger.info("✅ Added referrer_email column")
        except Exception as e:
            logger.warning(f"⚠️ referrer_email column may already exist: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE referrals 
                ADD COLUMN IF NOT EXISTS referred_email VARCHAR(255)
            """)
            logger.info("✅ Added referred_email column")
        except Exception as e:
            logger.warning(f"⚠️ referred_email column may already exist: {e}")
        
        # Commit column additions
        db_connection.commit()
        
        # Step 2: Backfill emails from users table
        logger.info("🔄 Backfilling emails from users table...")
        
        # Backfill referrer emails
        cursor.execute("""
            UPDATE referrals 
            SET referrer_email = (
                SELECT email FROM users WHERE id = referrals.referrer_id
            )
            WHERE referrer_email IS NULL AND referrer_id IS NOT NULL
        """)
        referrer_updates = cursor.rowcount
        logger.info(f"✅ Updated {referrer_updates} referrer_email records")
        
        # Backfill referred emails
        cursor.execute("""
            UPDATE referrals 
            SET referred_email = (
                SELECT email FROM users WHERE id = referrals.referred_id
            )
            WHERE referred_email IS NULL AND referred_id IS NOT NULL
        """)
        referred_updates = cursor.rowcount
        logger.info(f"✅ Updated {referred_updates} referred_email records")
        
        # Step 3: Backfill IDs from emails (if any exist)
        cursor.execute("""
            UPDATE referrals 
            SET referrer_id = (
                SELECT id FROM users WHERE LOWER(email) = LOWER(referrals.referrer_email)
            )
            WHERE referrer_id IS NULL AND referrer_email IS NOT NULL
        """)
        referrer_id_updates = cursor.rowcount
        logger.info(f"✅ Updated {referrer_id_updates} referrer_id records from emails")
        
        cursor.execute("""
            UPDATE referrals 
            SET referred_id = (
                SELECT id FROM users WHERE LOWER(email) = LOWER(referrals.referred_email)
            )
            WHERE referred_id IS NULL AND referred_email IS NOT NULL
        """)
        referred_id_updates = cursor.rowcount
        logger.info(f"✅ Updated {referred_id_updates} referred_id records from emails")
        
        # Step 4: Create additional indexes for email columns
        logger.info("📊 Creating performance indexes...")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email ON referrals (referrer_email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referred_email ON referrals (referred_email)")
            logger.info("✅ Email column indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
        
        # Step 5: Create trigger function and trigger
        logger.info("🔗 Creating sync trigger...")
        
        try:
            # Create or replace the trigger function
            cursor.execute("""
                CREATE OR REPLACE FUNCTION sync_referral_emails() RETURNS trigger AS $$
                BEGIN
                    -- If referrer_id is set/changed, update the corresponding email
                    IF NEW.referrer_id IS NOT NULL THEN
                        SELECT email INTO NEW.referrer_email FROM users WHERE id = NEW.referrer_id;
                    END IF;
                    
                    -- If referred_id is set/changed, update the corresponding email
                    IF NEW.referred_id IS NOT NULL THEN
                        SELECT email INTO NEW.referred_email FROM users WHERE id = NEW.referred_id;
                    END IF;
                    
                    RETURN NEW;
                END $$ LANGUAGE plpgsql;
            """)
            
            # Drop and recreate the trigger
            cursor.execute("DROP TRIGGER IF EXISTS trg_sync_referral_emails ON referrals")
            cursor.execute("""
                CREATE TRIGGER trg_sync_referral_emails
                    BEFORE INSERT OR UPDATE ON referrals
                    FOR EACH ROW
                    EXECUTE PROCEDURE sync_referral_emails()
            """)
            
            logger.info("✅ Sync trigger created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Trigger creation warning (PostgreSQL only): {e}")
        
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