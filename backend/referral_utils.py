#!/usr/bin/env python3
"""
Referral System Utilities for SoulBridge AI
Implements fraud protection, duplicate handling, and trial management
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from datetime_utils import iso_z, utc_now

logger = logging.getLogger(__name__)

class ReferralError(Exception):
    """Custom exception for referral-related errors"""
    pass

class DuplicateReferralError(ReferralError):
    """Raised when attempting to create duplicate referral"""
    pass

class FraudReferralError(ReferralError):
    """Raised when referral fails fraud checks"""
    pass

def create_referral_safe(db_connection, referrer_email: str, referred_email: str, 
                        referral_code: str, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """
    Create referral with fraud protection and duplicate handling
    
    Args:
        db_connection: Database connection
        referrer_email: Email of person making referral
        referred_email: Email of person being referred
        referral_code: Referral code used
        client_ip: IP address of request
        user_agent: User agent of request
        
    Returns:
        Dict with referral info or raises ReferralError
        
    Raises:
        FraudReferralError: If referral fails fraud checks
        DuplicateReferralError: If referred user already has a referrer
    """
    cursor = db_connection.cursor()
    
    try:
        # Fraud check 1: Self-referral protection
        if referrer_email.lower().strip() == referred_email.lower().strip():
            raise FraudReferralError("Cannot refer yourself")
        
        # Fraud check 2: Check if referrer and referred are same user by ID
        cursor.execute("""
            SELECT r.id as referrer_id, f.id as referred_id
            FROM users r, users f  
            WHERE lower(r.email) = lower(%s) 
            AND lower(f.email) = lower(%s)
        """, (referrer_email, referred_email))
        
        user_check = cursor.fetchone()
        if user_check and user_check[0] == user_check[1]:
            raise FraudReferralError("Cannot refer the same user account")
        
        # Fraud check 3: Daily referral limit per referrer (optional)
        cursor.execute("""
            SELECT COUNT(*) FROM referrals r
            JOIN users u ON lower(u.email) = lower(r.referrer_email)
            WHERE lower(r.referrer_email) = lower(%s)
            AND r.created_at >= CURRENT_DATE
        """, (referrer_email,))
        
        daily_count = cursor.fetchone()[0]
        if daily_count >= 20:  # Configurable limit
            raise FraudReferralError(f"Daily referral limit exceeded ({daily_count}/20)")
        
        # Check for existing referral by referred user
        cursor.execute("""
            SELECT referrer_email, referrer_id, status, created_at
            FROM referrals 
            WHERE (lower(referred_email) = lower(%s))
            OR (referred_id = (SELECT id FROM users WHERE lower(email) = lower(%s)))
        """, (referred_email, referred_email))
        
        existing = cursor.fetchone()
        if existing:
            raise DuplicateReferralError(
                f"User {referred_email} already has a referrer: {existing[0]} (status: {existing[2]})"
            )
        
        # Insert new referral (triggers will populate IDs)
        cursor.execute("""
            INSERT INTO referrals (
                referrer_email, referred_email, referral_code, 
                created_ip, created_ua, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, 'pending', %s)
            RETURNING id, referrer_id, referred_id, created_at
        """, (
            referrer_email.lower().strip(),
            referred_email.lower().strip(), 
            referral_code,
            client_ip,
            user_agent[:500],  # Truncate long user agents
            utc_now()
        ))
        
        result = cursor.fetchone()
        db_connection.commit()
        
        logger.info(f"✅ Created referral: {referrer_email} → {referred_email} (ID: {result[0]})")
        
        return {
            'id': result[0],
            'referrer_id': result[1],
            'referred_id': result[2],
            'referrer_email': referrer_email,
            'referred_email': referred_email,
            'referral_code': referral_code,
            'status': 'pending',
            'created_at': iso_z(result[3]),
            'created_ip': client_ip,
            'created_ua': user_agent
        }
        
    except (DuplicateReferralError, FraudReferralError):
        db_connection.rollback()
        raise
    except Exception as e:
        db_connection.rollback()
        
        # Check if it's a unique constraint violation (duplicate referral)
        error_msg = str(e).lower()
        if 'unique_referred_user' in error_msg or 'duplicate key' in error_msg:
            raise DuplicateReferralError("That user is already invited by someone else")
        
        logger.error(f"❌ Failed to create referral: {e}")
        raise ReferralError(f"Failed to create referral: {e}")

def reset_user_trial(db_connection, user_id: int, hours: int = 5, credits: int = 60) -> Dict[str, Any]:
    """
    Reset user's trial using delete-then-insert approach (idempotent)
    
    Args:
        db_connection: Database connection
        user_id: User ID to reset trial for
        hours: Trial duration in hours (default 5)
        credits: Credits to grant (default 60)
        
    Returns:
        Dict with trial info
    """
    cursor = db_connection.cursor()
    
    try:
        # Delete existing trial record
        cursor.execute("DELETE FROM max_trials WHERE user_id = %s", (user_id,))
        deleted_count = cursor.rowcount
        
        # Calculate expiry time
        expires_at = utc_now() + timedelta(hours=hours)
        
        # Insert new trial record
        cursor.execute("""
            INSERT INTO max_trials (user_id, expires_at, credits_granted, active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id, created_at
        """, (user_id, expires_at, credits))
        
        result = cursor.fetchone()
        db_connection.commit()
        
        logger.info(f"✅ Reset trial for user {user_id}: {hours}h, {credits} credits (deleted {deleted_count} old records)")
        
        return {
            'id': result[0],
            'user_id': user_id,
            'expires_at': iso_z(expires_at),
            'created_at': iso_z(result[1]),
            'credits_granted': credits,
            'active': True,
            'hours_duration': hours
        }
        
    except Exception as e:
        db_connection.rollback()
        logger.error(f"❌ Failed to reset trial for user {user_id}: {e}")
        raise

def get_referral_stats(db_connection, user_id: int) -> Dict[str, Any]:
    """
    Get referral statistics for a user
    
    Args:
        db_connection: Database connection
        user_id: User ID to get stats for
        
    Returns:
        Dict with referral statistics
    """
    cursor = db_connection.cursor()
    
    try:
        # Get user's email for reference
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user_result = cursor.fetchone()
        if not user_result:
            return {'error': 'User not found'}
        
        user_email = user_result[0]
        
        # Get referral statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_referrals,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN status = 'rewarded' THEN 1 ELSE 0 END) as rewarded,
                MIN(created_at) as first_referral,
                MAX(created_at) as latest_referral
            FROM referrals 
            WHERE referrer_id = %s OR lower(referrer_email) = lower(%s)
        """, (user_id, user_email))
        
        stats = cursor.fetchone()
        
        # Get recent referrals
        cursor.execute("""
            SELECT referred_email, status, created_at, created_ip
            FROM referrals 
            WHERE referrer_id = %s OR lower(referrer_email) = lower(%s)
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id, user_email))
        
        recent_referrals = []
        for row in cursor.fetchall():
            recent_referrals.append({
                'referred_email': row[0],
                'status': row[1],
                'created_at': iso_z(row[2]),
                'created_ip': str(row[3]) if row[3] else None
            })
        
        return {
            'user_id': user_id,
            'user_email': user_email,
            'total_referrals': stats[0] or 0,
            'pending_referrals': stats[1] or 0,
            'verified_referrals': stats[2] or 0,
            'rewarded_referrals': stats[3] or 0,
            'first_referral_at': iso_z(stats[4]),
            'latest_referral_at': iso_z(stats[5]),
            'recent_referrals': recent_referrals
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get referral stats for user {user_id}: {e}")
        return {'error': str(e)}

def get_user_trial_status(db_connection, user_id: int) -> Dict[str, Any]:
    """
    Get user's current trial status with proper ISO Z formatting
    
    Args:
        db_connection: Database connection  
        user_id: User ID to check
        
    Returns:
        Dict with trial status and properly formatted timestamps
    """
    cursor = db_connection.cursor()
    
    try:
        cursor.execute("""
            SELECT id, expires_at, credits_granted, active, created_at
            FROM max_trials 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return {
                'trial_active': False,
                'trial_started_at': None,
                'trial_expires_at': None,
                'credits_granted': 0,
                'credits_remaining': 0
            }
        
        # Check if trial is still active (not expired)
        expires_at = row[1]
        now = utc_now()
        trial_active = row[3] and expires_at > now
        
        return {
            'trial_active': trial_active,
            'trial_started_at': iso_z(row[4]),
            'trial_expires_at': iso_z(row[1]),
            'credits_granted': row[2],
            'credits_remaining': row[2] if trial_active else 0,  # Simplified - could track usage
            'trial_id': row[0]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get trial status for user {user_id}: {e}")
        return {
            'trial_active': False,
            'error': str(e)
        }