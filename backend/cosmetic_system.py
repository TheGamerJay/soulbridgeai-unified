#!/usr/bin/env python3
"""
Cosmetic System - SoulBridge AI
Manages cosmetic companions, unlocks, and equipment

Features:
1. Cosmetic companion unlock management
2. Equip/unequip system with validation
3. Integration with referral rewards
4. Cosmetic companion metadata and display
5. Progress tracking and collection system
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from flask import Blueprint, jsonify, request, session
from database_utils import format_query

logger = logging.getLogger(__name__)

# Create cosmetic system blueprint
cosmetics_bp = Blueprint('cosmetics', __name__, url_prefix='/cosmetics')

# ===============================
# COSMETIC MANAGEMENT ENDPOINTS
# ===============================

@cosmetics_bp.route('/me', methods=['GET'])
def get_my_cosmetics():
    """Get user's cosmetic collection and equipped items"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    user_id = session.get('user_id')
    
    try:
        # Get user's cosmetics
        from subscriptions_referrals_cosmetics_schema import get_user_cosmetics
        cosmetics_data = get_user_cosmetics(user_id)
        
        # Get available cosmetics for comparison
        available_cosmetics = get_all_cosmetics()
        
        # Calculate collection progress
        collection_stats = calculate_collection_progress(cosmetics_data['unlocked'], available_cosmetics)
        
        return jsonify({
            'unlocked_cosmetics': cosmetics_data['unlocked'],
            'equipped_cosmetics': cosmetics_data['equipped'],
            'collection_stats': collection_stats,
            'available_cosmetics': available_cosmetics
        })
        
    except Exception as e:
        logger.error(f"Failed to get user cosmetics: {e}")
        return jsonify({"error": "Failed to load cosmetics"}), 500

@cosmetics_bp.route('/equip', methods=['POST'])
def equip_cosmetic():
    """Equip a cosmetic item"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data or 'cosmetic_id' not in data:
        return jsonify({"error": "cosmetic_id required"}), 400
    
    user_id = session.get('user_id')
    cosmetic_id = data['cosmetic_id']
    
    try:
        # Validate user owns this cosmetic
        if not user_owns_cosmetic(user_id, cosmetic_id):
            return jsonify({"error": "Cosmetic not owned"}), 403
        
        # Get cosmetic details
        cosmetic = get_cosmetic_by_id(cosmetic_id)
        if not cosmetic:
            return jsonify({"error": "Cosmetic not found"}), 404
        
        # Equip the cosmetic
        success = equip_cosmetic_for_user(user_id, cosmetic_id, cosmetic['type'])
        
        if not success:
            return jsonify({"error": "Failed to equip cosmetic"}), 500
        
        logger.info(f"🎨 User {user_id} equipped cosmetic {cosmetic['name']}")
        
        return jsonify({
            'equipped': True,
            'cosmetic': cosmetic,
            'message': f"Equipped {cosmetic['display_name']} successfully"
        })
        
    except Exception as e:
        logger.error(f"Failed to equip cosmetic: {e}")
        return jsonify({"error": "Equip failed"}), 500

@cosmetics_bp.route('/unequip', methods=['POST'])
def unequip_cosmetic():
    """Unequip a cosmetic item"""
    if not session.get('user_id'):
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data or 'cosmetic_type' not in data:
        return jsonify({"error": "cosmetic_type required"}), 400
    
    user_id = session.get('user_id')
    cosmetic_type = data['cosmetic_type']
    
    try:
        # Unequip the cosmetic type
        success = unequip_cosmetic_for_user(user_id, cosmetic_type)
        
        if not success:
            return jsonify({"error": "Failed to unequip cosmetic"}), 500
        
        logger.info(f"🎨 User {user_id} unequipped {cosmetic_type} cosmetic")
        
        return jsonify({
            'unequipped': True,
            'cosmetic_type': cosmetic_type,
            'message': f"Unequipped {cosmetic_type} successfully"
        })
        
    except Exception as e:
        logger.error(f"Failed to unequip cosmetic: {e}")
        return jsonify({"error": "Unequip failed"}), 500

@cosmetics_bp.route('/available', methods=['GET'])
def get_available_cosmetics():
    """Get all available cosmetics with unlock requirements"""
    try:
        cosmetics = get_all_cosmetics()
        
        # Group by unlock method for easier browsing
        grouped_cosmetics = {
            'referral': [],
            'purchase': [],
            'achievement': [],
            'trial': []
        }
        
        for cosmetic in cosmetics:
            unlock_method = cosmetic.get('unlock_method', 'achievement')
            if unlock_method in grouped_cosmetics:
                grouped_cosmetics[unlock_method].append(cosmetic)
        
        return jsonify({
            'cosmetics_by_method': grouped_cosmetics,
            'total_cosmetics': len(cosmetics)
        })
        
    except Exception as e:
        logger.error(f"Failed to get available cosmetics: {e}")
        return jsonify({"error": "Failed to load cosmetics"}), 500

@cosmetics_bp.route('/<int:cosmetic_id>', methods=['GET'])
def get_cosmetic_details(cosmetic_id: int):
    """Get detailed information about a specific cosmetic"""
    try:
        cosmetic = get_cosmetic_by_id(cosmetic_id)
        if not cosmetic:
            return jsonify({"error": "Cosmetic not found"}), 404
        
        # Add unlock requirement details
        unlock_requirement = json.loads(cosmetic.get('unlock_requirement', '{}'))
        
        cosmetic_details = {
            **cosmetic,
            'unlock_requirement_parsed': unlock_requirement,
            'unlock_description': generate_unlock_description(cosmetic)
        }
        
        return jsonify(cosmetic_details)
        
    except Exception as e:
        logger.error(f"Failed to get cosmetic details: {e}")
        return jsonify({"error": "Failed to load cosmetic details"}), 500

# ===============================
# COSMETIC MANAGEMENT FUNCTIONS
# ===============================

def unlock_cosmetic_for_user(user_id: int, cosmetic_id: int, unlock_source: str) -> bool:
    """Unlock a cosmetic for a user"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if already unlocked
        cursor.execute(format_query("""
            SELECT id FROM user_cosmetics 
            WHERE user_id = ? AND cosmetic_id = ?
        """), (user_id, cosmetic_id))
        
        if cursor.fetchone():
            conn.close()
            return True  # Already unlocked
        
        # Unlock the cosmetic
        cursor.execute(format_query("""
            INSERT INTO user_cosmetics (user_id, cosmetic_id, unlock_source)
            VALUES (?, ?, ?)
        """), (user_id, cosmetic_id, unlock_source))
        
        conn.commit()
        conn.close()
        
        # Get cosmetic name for logging
        cosmetic = get_cosmetic_by_id(cosmetic_id)
        cosmetic_name = cosmetic['name'] if cosmetic else f"ID:{cosmetic_id}"
        
        logger.info(f"🎁 Unlocked cosmetic {cosmetic_name} for user {user_id} via {unlock_source}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to unlock cosmetic: {e}")
        return False

def equip_cosmetic_for_user(user_id: int, cosmetic_id: int, cosmetic_type: str) -> bool:
    """Equip a cosmetic for a user"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Remove any currently equipped item of this type
        cursor.execute(format_query("""
            DELETE FROM user_equipped_cosmetics 
            WHERE user_id = ? AND cosmetic_type = ?
        """), (user_id, cosmetic_type))
        
        # Equip the new cosmetic
        cursor.execute(format_query("""
            INSERT INTO user_equipped_cosmetics (user_id, cosmetic_type, cosmetic_id)
            VALUES (?, ?, ?)
        """), (user_id, cosmetic_type, cosmetic_id))
        
        # Update user_cosmetics to mark as equipped
        cursor.execute(format_query("""
            UPDATE user_cosmetics 
            SET is_equipped = FALSE 
            WHERE user_id = ? AND cosmetic_id IN (
                SELECT cosmetic_id FROM user_cosmetics uc
                JOIN cosmetics c ON uc.cosmetic_id = c.id
                WHERE uc.user_id = ? AND c.type = ?
            )
        """), (user_id, user_id, cosmetic_type))
        
        cursor.execute(format_query("""
            UPDATE user_cosmetics 
            SET is_equipped = TRUE 
            WHERE user_id = ? AND cosmetic_id = ?
        """), (user_id, cosmetic_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to equip cosmetic: {e}")
        return False

def unequip_cosmetic_for_user(user_id: int, cosmetic_type: str) -> bool:
    """Unequip a cosmetic type for a user"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Remove equipped cosmetic of this type
        cursor.execute(format_query("""
            DELETE FROM user_equipped_cosmetics 
            WHERE user_id = ? AND cosmetic_type = ?
        """), (user_id, cosmetic_type))
        
        # Update user_cosmetics to mark as not equipped
        cursor.execute(format_query("""
            UPDATE user_cosmetics 
            SET is_equipped = FALSE 
            WHERE user_id = ? AND cosmetic_id IN (
                SELECT cosmetic_id FROM user_cosmetics uc
                JOIN cosmetics c ON uc.cosmetic_id = c.id
                WHERE uc.user_id = ? AND c.type = ?
            )
        """), (user_id, user_id, cosmetic_type))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to unequip cosmetic: {e}")
        return False

def user_owns_cosmetic(user_id: int, cosmetic_id: int) -> bool:
    """Check if user owns a specific cosmetic"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            SELECT id FROM user_cosmetics 
            WHERE user_id = ? AND cosmetic_id = ?
        """), (user_id, cosmetic_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Failed to check cosmetic ownership: {e}")
        return False

def get_cosmetic_by_id(cosmetic_id: int) -> Optional[Dict[str, Any]]:
    """Get cosmetic details by ID"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return None
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            SELECT id, name, display_name, description, type, rarity, 
                   unlock_method, unlock_requirement, image_url, is_active
            FROM cosmetics 
            WHERE id = ? AND is_active = TRUE
        """), (cosmetic_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'display_name': row[2],
            'description': row[3],
            'type': row[4],
            'rarity': row[5],
            'unlock_method': row[6],
            'unlock_requirement': row[7],
            'image_url': row[8],
            'is_active': row[9]
        }
        
    except Exception as e:
        logger.error(f"Failed to get cosmetic by ID: {e}")
        return None

def get_all_cosmetics() -> List[Dict[str, Any]]:
    """Get all available cosmetics"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return []
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            SELECT id, name, display_name, description, type, rarity,
                   unlock_method, unlock_requirement, image_url, is_active
            FROM cosmetics
            WHERE is_active = TRUE
            ORDER BY unlock_method, rarity, name
        """))
        
        cosmetics = []
        for row in cursor.fetchall():
            cosmetics.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'type': row[4],
                'rarity': row[5],
                'unlock_method': row[6],
                'unlock_requirement': row[7],
                'image_url': row[8],
                'is_active': row[9]
            })
        
        conn.close()
        return cosmetics
        
    except Exception as e:
        logger.error(f"Failed to get all cosmetics: {e}")
        return []

def get_user_equipped_companions(user_id: int) -> List[Dict[str, Any]]:
    """Get user's currently equipped companion cosmetics for chat"""
    try:
        from database_utils import get_database
        
        db = get_database()
        if not db:
            return []
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.name, c.display_name, c.description, c.rarity, c.image_url
            FROM user_equipped_cosmetics uec
            JOIN cosmetics c ON uec.cosmetic_id = c.id
            WHERE uec.user_id = ? AND c.type = 'companion'
        """, (user_id,))
        
        companions = []
        for row in cursor.fetchall():
            companions.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'rarity': row[4],
                'image_url': row[5],
                'equipped': True
            })
        
        conn.close()
        return companions
        
    except Exception as e:
        logger.error(f"Failed to get equipped companions: {e}")
        return []

def calculate_collection_progress(unlocked_cosmetics: List[Dict], available_cosmetics: List[Dict]) -> Dict[str, Any]:
    """Calculate user's collection progress statistics"""
    try:
        total_available = len(available_cosmetics)
        total_unlocked = len(unlocked_cosmetics)
        
        # Progress by rarity
        rarity_progress = {}
        for rarity in ['common', 'rare', 'epic', 'legendary']:
            available_count = len([c for c in available_cosmetics if c['rarity'] == rarity])
            unlocked_count = len([c for c in unlocked_cosmetics if c['rarity'] == rarity])
            
            rarity_progress[rarity] = {
                'unlocked': unlocked_count,
                'total': available_count,
                'percentage': int((unlocked_count / available_count) * 100) if available_count > 0 else 0
            }
        
        # Progress by unlock method
        method_progress = {}
        for method in ['referral', 'purchase', 'achievement', 'trial']:
            available_count = len([c for c in available_cosmetics if c['unlock_method'] == method])
            unlocked_count = len([c for c in unlocked_cosmetics if c.get('unlock_source', '').startswith(method)])
            
            method_progress[method] = {
                'unlocked': unlocked_count,
                'total': available_count,
                'percentage': int((unlocked_count / available_count) * 100) if available_count > 0 else 0
            }
        
        overall_percentage = int((total_unlocked / total_available) * 100) if total_available > 0 else 0
        
        return {
            'overall': {
                'unlocked': total_unlocked,
                'total': total_available,
                'percentage': overall_percentage
            },
            'by_rarity': rarity_progress,
            'by_method': method_progress,
            'completion_level': get_completion_level(overall_percentage)
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate collection progress: {e}")
        return {
            'overall': {'unlocked': 0, 'total': 0, 'percentage': 0},
            'by_rarity': {},
            'by_method': {},
            'completion_level': 'Beginner'
        }

def get_completion_level(percentage: int) -> str:
    """Get collection completion level based on percentage"""
    if percentage >= 90:
        return 'Master Collector'
    elif percentage >= 75:
        return 'Expert Collector'
    elif percentage >= 50:
        return 'Dedicated Collector'
    elif percentage >= 25:
        return 'Active Collector'
    elif percentage >= 10:
        return 'Novice Collector'
    else:
        return 'Beginner'

def generate_unlock_description(cosmetic: Dict[str, Any]) -> str:
    """Generate human-readable unlock description"""
    unlock_method = cosmetic.get('unlock_method', 'unknown')
    unlock_requirement = cosmetic.get('unlock_requirement', '{}')
    
    try:
        requirement_data = json.loads(unlock_requirement) if unlock_requirement else {}
    except:
        requirement_data = {}
    
    if unlock_method == 'referral':
        threshold = requirement_data.get('referral_threshold', 1)
        return f"Refer {threshold} friends to SoulBridge AI"
    elif unlock_method == 'purchase':
        price = requirement_data.get('price', 'TBD')
        return f"Purchase for ${price}"
    elif unlock_method == 'achievement':
        achievement = requirement_data.get('achievement_name', 'Complete achievement')
        return f"Unlock by: {achievement}"
    elif unlock_method == 'trial':
        return "Available during 5-hour trial"
    else:
        return "Special unlock method"

# ===============================
# INTEGRATION FUNCTIONS
# ===============================

def get_available_companions_for_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all companions available to user (owned + tier-accessible)
    Used by companion selector to show available options
    """
    try:
        # Get user's unlocked cosmetic companions
        from subscriptions_referrals_cosmetics_schema import get_user_cosmetics
        user_cosmetics = get_user_cosmetics(user_id)
        
        # Get cosmetic companions
        cosmetic_companions = [c for c in user_cosmetics['unlocked'] if c.get('type') == 'companion']
        
        # Get tier-based companions (existing system)
        from unified_tier_system import get_effective_plan
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # This would integrate with existing companion system
        # For now, return cosmetic companions
        return cosmetic_companions
        
    except Exception as e:
        logger.error(f"Failed to get available companions: {e}")
        return []

# Export blueprint for app registration
def register_cosmetic_system(app):
    """Register cosmetic system blueprint with Flask app"""
    app.register_blueprint(cosmetics_bp)
    logger.info("🎨 Cosmetic system registered successfully")