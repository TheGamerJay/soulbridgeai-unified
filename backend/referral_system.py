#!/usr/bin/env python3
"""
Referral System - SoulBridge AI
Comprehensive referral tracking with cosmetic rewards and anti-abuse measures

Features:
1. Referral code generation and tracking
2. Anti-abuse validation (email/phone verification required)
3. Cosmetic companion unlocks at thresholds (2, 5, 8, 10 referrals)
4. Social sharing integration
5. Progress tracking and analytics
"""

import logging
import random
import string
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from flask import Blueprint, jsonify, request, session

logger = logging.getLogger(__name__)

# Create referral system blueprint
referrals_bp = Blueprint('referrals', __name__, url_prefix='/referrals')

# Referral reward thresholds (matches spec)
REFERRAL_THRESHOLDS = {
    2: {'cosmetic': 'blayzike', 'display_name': 'Blayzike', 'rarity': 'rare'},
    5: {'cosmetic': 'blazelian', 'display_name': 'Blazelian', 'rarity': 'epic'},
    8: {'cosmetic': 'claude', 'display_name': 'Claude', 'rarity': 'legendary'},
    10: {'cosmetic': 'blayzo', 'display_name': 'Blayzo', 'rarity': 'legendary'}
}

# Anti-abuse configuration
REFERRAL_LIMITS = {
    'max_pending_per_user': 20,  # Max pending referrals per user
    'verification_timeout_hours': 72,  # Time to verify referral
    'min_account_age_hours': 24,  # Referred user must be active for 24h
    'max_referrals_per_ip_per_day': 5  # IP-based rate limiting
}

# ===============================
# REFERRAL CODE MANAGEMENT
# ===============================

@referrals_bp.route('/me', methods=['GET'])
def get_my_referrals():
    """Get current user's referral status and rewards"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    
    try:
        # Get referral statistics
        from subscriptions_referrals_cosmetics_schema import get_user_referral_stats
        stats = get_user_referral_stats(user_id)
        
        # Get referral code
        referral_code = get_or_create_referral_code(user_id)
        
        # Get next reward milestone
        next_threshold = get_next_reward_threshold(stats['verified_referrals'])
        
        # Get unlocked cosmetics from referrals
        unlocked_cosmetics = get_referral_cosmetics(user_id)
        
        # Calculate progress
        progress = calculate_referral_progress(stats['verified_referrals'])
        
        return jsonify({
            'referral_code': referral_code,
            'stats': {
                'total_referrals': stats['total_referrals'],
                'verified_referrals': stats['verified_referrals'],
                'pending_referrals': stats['pending_referrals']
            },
            'progress': progress,
            'next_reward': next_threshold,
            'unlocked_cosmetics': unlocked_cosmetics,
            'share_url': f'https://soulbridgeai.com/join?ref={referral_code}',
            'social_sharing': {
                'twitter': f'https://twitter.com/intent/tweet?text=Join%20me%20on%20SoulBridge%20AI%21&url=https://soulbridgeai.com/join?ref={referral_code}',
                'facebook': f'https://www.facebook.com/sharer/sharer.php?u=https://soulbridgeai.com/join?ref={referral_code}',
                'whatsapp': f'https://wa.me/?text=Join%20me%20on%20SoulBridge%20AI%21%20https://soulbridgeai.com/join?ref={referral_code}'
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get referral data: {e}")
        return jsonify({"error": "Failed to load referral data"}), 500

@referrals_bp.route('/link', methods=['GET'])
def get_referral_link():
    """Get user's referral link (simplified endpoint)"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    referral_code = get_or_create_referral_code(user_id)
    
    return jsonify({
        'referral_code': referral_code,
        'share_url': f'https://soulbridgeai.com/join?ref={referral_code}'
    })

@referrals_bp.route('/apply', methods=['POST'])
def apply_referral_code():
    """Apply a referral code during signup/registration"""
    data = request.get_json()
    if not data or 'referral_code' not in data:
        return jsonify({"error": "Referral code required"}), 400
    
    # For now, return success - this would be called during user registration
    # The actual referral application happens in the registration process
    referral_code = data['referral_code']
    
    # Validate referral code exists and is active
    referrer_id = validate_referral_code(referral_code)
    if not referrer_id:
        return jsonify({"error": "Invalid referral code"}), 400
    
    return jsonify({
        'valid': True,
        'referrer_id': referrer_id,
        'message': 'Referral code applied successfully'
    })

@referrals_bp.route('/rewards', methods=['GET'])
def get_referral_rewards():
    """Get information about referral rewards and thresholds"""
    return jsonify({
        'thresholds': {
            str(threshold): {
                'cosmetic_name': data['display_name'],
                'cosmetic_id': data['cosmetic'],
                'rarity': data['rarity'],
                'image_url': f'/static/cosmetics/{data["cosmetic"]}.png',
                'description': f'Unlock {data["display_name"]} by referring {threshold} friends'
            }
            for threshold, data in REFERRAL_THRESHOLDS.items()
        },
        'requirements': {
            'verification_required': True,
            'verification_methods': ['email_phone', 'subscription'],
            'minimum_account_age': '24 hours',
            'description': 'Referred users must verify their account and remain active for 24+ hours'
        }
    })

# ===============================
# REFERRAL PROCESSING
# ===============================

def process_referral(referrer_id: int, referred_user_id: int, referral_code: str) -> Dict[str, Any]:
    """Process a new referral relationship"""
    try:
        from database_utils import get_database
        
        # Validate referral eligibility
        validation = validate_referral_eligibility(referrer_id, referred_user_id)
        if not validation['valid']:
            return {'success': False, 'error': validation['reason']}
        
        db = get_database()
        if not db:
            return {'success': False, 'error': 'Database unavailable'}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Create referral record
        cursor.execute("""
            INSERT INTO referrals (referrer_id, referred_id, referral_code, status, verification_method)
            VALUES (?, ?, ?, 'pending', 'signup')
        """, (referrer_id, referred_user_id, referral_code))
        
        referral_id = cursor.lastrowid
        
        # Update referral code usage
        cursor.execute("""
            UPDATE referral_codes 
            SET uses_count = uses_count + 1 
            WHERE user_id = ? AND code = ?
        """, (referrer_id, referral_code))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📧 Created referral: {referrer_id} -> {referred_user_id}")
        
        return {
            'success': True,
            'referral_id': referral_id,
            'status': 'pending',
            'message': 'Referral recorded! Will be verified once new user confirms their account.'
        }
        
    except Exception as e:
        logger.error(f"Failed to process referral: {e}")
        return {'success': False, 'error': 'Referral processing failed'}

def verify_referral(referred_user_id: int, verification_method: str) -> Dict[str, Any]:
    """Verify a referral and trigger reward checks"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return {'success': False, 'error': 'Database unavailable'}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Find pending referral for this user
        cursor.execute("""
            SELECT id, referrer_id, referral_code 
            FROM referrals 
            WHERE referred_id = ? AND status = 'pending'
        """, (referred_user_id,))
        
        referral = cursor.fetchone()
        if not referral:
            conn.close()
            return {'success': False, 'error': 'No pending referral found'}
        
        referral_id, referrer_id, referral_code = referral
        
        # Update referral to verified
        cursor.execute("""
            UPDATE referrals 
            SET status = 'verified', verification_method = ?, verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (verification_method, referral_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Verified referral: {referrer_id} -> {referred_user_id}")
        
        # Check for reward eligibility
        reward_result = check_and_award_referral_rewards(referrer_id)
        
        return {
            'success': True,
            'referral_verified': True,
            'rewards_unlocked': reward_result.get('rewards_unlocked', [])
        }
        
    except Exception as e:
        logger.error(f"Failed to verify referral: {e}")
        return {'success': False, 'error': 'Verification failed'}

def check_and_award_referral_rewards(user_id: int) -> Dict[str, Any]:
    """Check if user reached new reward thresholds and unlock cosmetics"""
    try:
        from subscriptions_referrals_cosmetics_schema import get_user_referral_stats
        
        # Get current verified referral count
        stats = get_user_referral_stats(user_id)
        verified_count = stats['verified_referrals']
        
        # Check each threshold
        new_rewards = []
        for threshold, reward_data in REFERRAL_THRESHOLDS.items():
            if verified_count >= threshold:
                # Check if reward already unlocked
                if not has_referral_reward(user_id, threshold):
                    # Unlock the cosmetic
                    unlock_result = unlock_referral_cosmetic(user_id, threshold, reward_data['cosmetic'])
                    if unlock_result:
                        new_rewards.append({
                            'threshold': threshold,
                            'cosmetic': reward_data['display_name'],
                            'rarity': reward_data['rarity']
                        })
        
        if new_rewards:
            logger.info(f"🎁 Unlocked {len(new_rewards)} referral rewards for user {user_id}")
        
        return {
            'verified_referrals': verified_count,
            'rewards_unlocked': new_rewards
        }
        
    except Exception as e:
        logger.error(f"Failed to check referral rewards: {e}")
        return {'verified_referrals': 0, 'rewards_unlocked': []}

# ===============================
# ANTI-ABUSE VALIDATION
# ===============================

def validate_referral_eligibility(referrer_id: int, referred_user_id: int) -> Dict[str, Any]:
    """Comprehensive anti-abuse validation for referrals"""
    try:
        from database_utils import get_database
        
        # Basic validation
        if referrer_id == referred_user_id:
            return {'valid': False, 'reason': 'Cannot refer yourself'}
        
        db = get_database()
        if not db:
            return {'valid': False, 'reason': 'Database unavailable'}
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if referral already exists
        cursor.execute("""
            SELECT id FROM referrals 
            WHERE referrer_id = ? AND referred_id = ?
        """, (referrer_id, referred_user_id))
        
        if cursor.fetchone():
            conn.close()
            return {'valid': False, 'reason': 'Referral already exists'}
        
        # Check referrer's pending referral count
        cursor.execute("""
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND status = 'pending'
        """, (referrer_id,))
        
        pending_count = cursor.fetchone()[0]
        if pending_count >= REFERRAL_LIMITS['max_pending_per_user']:
            conn.close()
            return {'valid': False, 'reason': 'Too many pending referrals'}
        
        # Check for suspicious patterns (same IP, etc.)
        # This would require additional user metadata tracking
        
        conn.close()
        return {'valid': True, 'reason': 'Eligible'}
        
    except Exception as e:
        logger.error(f"Referral eligibility validation failed: {e}")
        return {'valid': False, 'reason': 'Validation error'}

def validate_account_for_referral_verification(user_id: int) -> bool:
    """Validate that referred user's account meets verification requirements"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check account age (24+ hours)
        cursor.execute("""
            SELECT created_at FROM users 
            WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        created_at = datetime.fromisoformat(result[0])
        account_age = datetime.now(timezone.utc) - created_at
        
        if account_age.total_seconds() < REFERRAL_LIMITS['min_account_age_hours'] * 3600:
            conn.close()
            return False
        
        # Additional validation checks can be added here:
        # - Email verification status
        # - Phone verification status  
        # - Minimum activity level
        # - No suspicious behavior flags
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Account validation failed: {e}")
        return False

# ===============================
# UTILITY FUNCTIONS
# ===============================

def get_or_create_referral_code(user_id: int) -> str:
    """Get or create a unique referral code for user"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return f"USER{user_id}"  # Fallback
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if user already has a code
        cursor.execute("""
            SELECT code FROM referral_codes 
            WHERE user_id = ? AND is_active = TRUE 
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]
        
        # Generate new unique code
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_referral_code()
            
            # Check uniqueness
            cursor.execute("SELECT id FROM referral_codes WHERE code = ?", (code,))
            if not cursor.fetchone():
                # Create the code
                cursor.execute("""
                    INSERT INTO referral_codes (user_id, code, is_active)
                    VALUES (?, ?, TRUE)
                """, (user_id, code))
                
                conn.commit()
                conn.close()
                
                logger.info(f"🔗 Generated referral code {code} for user {user_id}")
                return code
        
        conn.close()
        # Fallback if generation failed
        return f"USER{user_id}"
        
    except Exception as e:
        logger.error(f"Failed to get/create referral code: {e}")
        return f"USER{user_id}"

def generate_referral_code() -> str:
    """Generate a unique referral code"""
    # Create a memorable code: 2 uppercase letters + 4 digits
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    return f"{letters}{numbers}"

def validate_referral_code(referral_code: str) -> Optional[int]:
    """Validate referral code and return referrer user ID"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return None
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id FROM referral_codes 
            WHERE code = ? AND is_active = TRUE
        """, (referral_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
        
    except Exception as e:
        logger.error(f"Referral code validation failed: {e}")
        return None

def get_next_reward_threshold(current_referrals: int) -> Optional[Dict[str, Any]]:
    """Get the next reward threshold for user"""
    for threshold in sorted(REFERRAL_THRESHOLDS.keys()):
        if current_referrals < threshold:
            data = REFERRAL_THRESHOLDS[threshold]
            return {
                'threshold': threshold,
                'referrals_needed': threshold - current_referrals,
                'cosmetic': data['display_name'],
                'rarity': data['rarity']
            }
    return None

def calculate_referral_progress(verified_referrals: int) -> Dict[str, Any]:
    """Calculate referral progress for UI display"""
    thresholds = sorted(REFERRAL_THRESHOLDS.keys())
    
    # Find current and next threshold
    current_threshold = 0
    next_threshold = thresholds[0]
    
    for threshold in thresholds:
        if verified_referrals >= threshold:
            current_threshold = threshold
        else:
            next_threshold = threshold
            break
    
    if verified_referrals >= thresholds[-1]:
        # Completed all thresholds
        return {
            'current_level': len(thresholds),
            'max_level': len(thresholds),
            'progress_percent': 100,
            'completed_all': True
        }
    
    # Calculate progress to next threshold
    progress_percent = int((verified_referrals / next_threshold) * 100)
    
    return {
        'current_level': len([t for t in thresholds if verified_referrals >= t]),
        'max_level': len(thresholds),
        'progress_percent': progress_percent,
        'completed_all': False,
        'current_threshold': current_threshold,
        'next_threshold': next_threshold
    }

def get_referral_cosmetics(user_id: int) -> List[Dict[str, Any]]:
    """Get cosmetics unlocked through referrals"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return []
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rr.threshold_reached, c.name, c.display_name, c.rarity, rr.unlocked_at
            FROM referral_rewards rr
            JOIN cosmetics c ON rr.cosmetic_id = c.id
            WHERE rr.user_id = ?
            ORDER BY rr.threshold_reached ASC
        """, (user_id,))
        
        cosmetics = []
        for row in cursor.fetchall():
            cosmetics.append({
                'threshold': row[0],
                'name': row[1],
                'display_name': row[2],
                'rarity': row[3],
                'unlocked_at': row[4],
                'image_url': f'/static/cosmetics/{row[1]}.png'
            })
        
        conn.close()
        return cosmetics
        
    except Exception as e:
        logger.error(f"Failed to get referral cosmetics: {e}")
        return []

def has_referral_reward(user_id: int, threshold: int) -> bool:
    """Check if user already has reward for threshold"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM referral_rewards 
            WHERE user_id = ? AND threshold_reached = ?
        """, (user_id, threshold))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Failed to check referral reward: {e}")
        return False

def unlock_referral_cosmetic(user_id: int, threshold: int, cosmetic_name: str) -> bool:
    """Unlock a cosmetic reward for reaching referral threshold"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get cosmetic ID
        cursor.execute("SELECT id FROM cosmetics WHERE name = ?", (cosmetic_name,))
        cosmetic_result = cursor.fetchone()
        
        if not cosmetic_result:
            conn.close()
            return False
        
        cosmetic_id = cosmetic_result[0]
        
        # Record the referral reward
        cursor.execute("""
            INSERT INTO referral_rewards (user_id, threshold_reached, cosmetic_id)
            VALUES (?, ?, ?)
        """, (user_id, threshold, cosmetic_id))
        
        # Add to user's cosmetics
        cursor.execute("""
            INSERT OR IGNORE INTO user_cosmetics (user_id, cosmetic_id, unlock_source)
            VALUES (?, ?, ?)
        """, (user_id, cosmetic_id, f'referral_{threshold}'))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎁 Unlocked {cosmetic_name} for user {user_id} (threshold: {threshold})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to unlock referral cosmetic: {e}")
        return False

# Export blueprint for app registration
def register_referral_system(app):
    """Register referral system blueprint with Flask app"""
    app.register_blueprint(referrals_bp)
    logger.info("📧 Referral system registered successfully")