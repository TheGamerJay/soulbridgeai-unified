"""
SoulBridge AI - Referral Rewards System
Automatically grants companions and skins when referral thresholds are reached
"""
import logging
from database_utils import get_database
from ..companions.companion_data import COMPANIONS
from database_utils import format_query

logger = logging.getLogger(__name__)

# Referral threshold to companion mapping (matching CLAUDE.md thresholds)
REFERRAL_REWARDS = {
    2: {
        "companions": ["blayzike"],  # First referral companion at 2 referrals
        "message": "🎉 You've unlocked Blayzike! Your first referral companion is now available."
    },
    5: {
        "companions": ["nyxara"],  # Silver tier companion at 5 referrals 
        "message": "🌟 Amazing! Nyxara has joined your companion roster!"
    },
    8: {
        "companions": ["claude_referral"],  # Gold tier referral companion at 8 referrals
        "message": "👑 Incredible! Claude Referral is now unlocked - a premium companion just for you!"
    }
}

def get_companion_unlocks_for_referrals(referral_count: int) -> dict:
    """
    Get all companions that should be unlocked for a given referral count
    Returns dict with companion IDs and their details
    """
    unlocked = {}
    
    for threshold, rewards in REFERRAL_REWARDS.items():
        if referral_count >= threshold:
            for companion_id in rewards["companions"]:
                # Find the companion details
                companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
                if companion:
                    unlocked[companion_id] = {
                        "id": companion_id,
                        "name": companion["name"],
                        "tier": companion["tier"], 
                        "image_url": companion["image_url"],
                        "threshold": threshold,
                        "min_referrals": companion.get("min_referrals", 0)
                    }
    
    return unlocked

def check_and_grant_referral_rewards(user_id: int, new_referral_count: int, old_referral_count: int = 0) -> list:
    """
    Check if user has crossed any referral thresholds and grant rewards
    Returns list of newly unlocked rewards
    """
    newly_unlocked = []
    
    # Check each threshold to see if we've crossed it
    for threshold, rewards in REFERRAL_REWARDS.items():
        # If we've crossed this threshold (old count was below, new count is at/above)
        if old_referral_count < threshold <= new_referral_count:
            
            # Grant companion access
            for companion_id in rewards["companions"]:
                try:
                    # Record the unlock in user_companion_unlocks table (if it exists)
                    record_companion_unlock(user_id, companion_id, threshold)
                    
                    companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
                    if companion:
                        newly_unlocked.append({
                            "type": "companion",
                            "id": companion_id,
                            "name": companion["name"],
                            "tier": companion["tier"],
                            "image_url": companion["image_url"],
                            "threshold": threshold,
                            "message": rewards["message"]
                        })
                        
                        logger.info(f"✅ Granted companion {companion_id} to user {user_id} at {threshold} referrals")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to grant companion {companion_id} to user {user_id}: {e}")
    
    return newly_unlocked

def record_companion_unlock(user_id: int, companion_id: str, referral_threshold: int):
    """
    Record that a user has unlocked a companion via referrals
    Creates the table if it doesn't exist
    """
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        cursor.execute(format_query("""
            CREATE TABLE IF NOT EXISTS user_companion_unlocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                companion_id TEXT NOT NULL,
                unlock_type TEXT DEFAULT 'referral',
                unlock_threshold INTEGER,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, companion_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Insert the unlock record (ignore if already exists)
        cursor.execute("""
            INSERT OR IGNORE INTO user_companion_unlocks 
            (user_id, companion_id, unlock_type, unlock_threshold, unlocked_at)
            VALUES (?, ?, 'referral', ?, datetime('now'))
        """), (user_id, companion_id, referral_threshold))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error recording companion unlock: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_user_unlocked_companions(user_id: int) -> list:
    """
    Get list of companions unlocked by user via referrals
    """
    db = get_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(format_query("""
            SELECT companion_id, unlock_type, unlock_threshold, unlocked_at
            FROM user_companion_unlocks 
            WHERE user_id = ?
        """), (user_id,))
        
        results = cursor.fetchall()
        
        unlocked = []
        for row in results:
            companion_id, unlock_type, threshold, unlocked_at = row
            companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
            
            if companion:
                unlocked.append({
                    "id": companion_id,
                    "name": companion["name"],
                    "tier": companion["tier"],
                    "image_url": companion["image_url"],
                    "unlock_type": unlock_type,
                    "threshold": threshold,
                    "unlocked_at": unlocked_at
                })
        
        return unlocked
        
    except Exception as e:
        logger.error(f"Error getting user unlocked companions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def user_has_companion_access(user_id: int, companion_id: str, referral_count: int) -> bool:
    """
    Check if user has access to a specific companion
    Considers both tier-based access and referral unlocks
    """
    # Find the companion
    companion = next((c for c in COMPANIONS if c["id"] == companion_id), None)
    if not companion:
        return False
    
    # If it's a referral companion, check referral count
    if companion.get("min_referrals", 0) > 0:
        return referral_count >= companion["min_referrals"]
    
    # For regular companions, this would integrate with the existing tier system
    # For now, just return True for non-referral companions
    return True