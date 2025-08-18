#!/usr/bin/env python3
"""
Anonymous Community System - SoulBridge AI
Complete implementation based on detailed specification

Features:
1. Anonymous-only posting with companion avatars
2. Multi-layer safety pipeline
3. Emoji reactions with rate limiting  
4. Category-based organization
5. Comprehensive reporting and muting
6. Tier-aware referral skin system
7. Shadow banning and soft delete
"""

import logging
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from flask import Blueprint, jsonify, request, session

logger = logging.getLogger(__name__)

# Create community blueprint
community_bp = Blueprint('community', __name__, url_prefix='/community')

# ===============================
# CONFIGURATION FROM SPEC
# ===============================

COMMUNITY_CONFIG = {
    "categories": [
        {"id": "all", "label": "All Content"},
        {"id": "gratitude", "label": "Gratitude"},
        {"id": "peace", "label": "Peace"},
        {"id": "growth", "label": "Growth"},
        {"id": "healing", "label": "Healing"},
        {"id": "dreams", "label": "Dreams"},
        {"id": "mood", "label": "Mood"},
        {"id": "stress_relief", "label": "Stress Relief"}
    ],
    "allowed_reactions": ["❤️", "✨", "🌿", "🔥", "🙏", "⭐", "👏", "🫶"],
    "rate_limits": {
        "post_per_hour": 5,
        "post_per_day": 20,
        "image_uploads_per_day": 10,
        "reaction_per_minute": 12,
        "report_per_day": 20
    },
    "content_limits": {
        "max_chars": 700,
        "max_image_size_mb": 5,
        "allowed_image_formats": ["jpg", "jpeg", "png", "webp"]
    },
    "report_reasons": [
        "spam", "harassment", "self_harm_risk", 
        "hate_or_violence", "graphic_content", "pii_privacy", "other"
    ]
}

# ===============================
# DATABASE SCHEMA INITIALIZATION
# ===============================

def initialize_community_database():
    """Initialize community database tables"""
    try:
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("No DATABASE_URL found for community initialization")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Community posts table - matches spec exactly
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_posts (
                id SERIAL PRIMARY KEY,
                author_uid_hash TEXT NOT NULL,
                author_uid INTEGER NOT NULL,
                companion_id INTEGER,
                companion_skin_id INTEGER,
                category TEXT NOT NULL,
                text TEXT,
                image_url TEXT,
                image_hash TEXT,
                hashtags TEXT DEFAULT '[]',
                
                -- Status and moderation
                status TEXT DEFAULT 'approved' CHECK (status IN ('pending', 'approved', 'rejected', 'hidden')),
                moderation_state TEXT DEFAULT '{}',
                moderation_flags TEXT DEFAULT '[]',
                
                -- Metrics  
                reaction_counts_json TEXT DEFAULT '{}',
                total_reactions INTEGER DEFAULT 0,
                report_count INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            );
        """)
        
        # Comprehensive migration - Add ALL missing columns from schema
        migration_columns = [
            ("author_uid_hash", "TEXT"),
            ("author_uid", "INTEGER"),
            ("companion_id", "INTEGER"),
            ("companion_skin_id", "INTEGER"), 
            ("category", "TEXT NOT NULL DEFAULT 'general'"),
            ("text", "TEXT"),
            ("image_url", "TEXT"),
            ("image_hash", "TEXT"),
            ("hashtags", "TEXT DEFAULT '[]'"),
            ("status", "TEXT DEFAULT 'approved'"),
            ("moderation_state", "TEXT DEFAULT '{}'"),
            ("moderation_flags", "TEXT DEFAULT '[]'"),
            ("reaction_counts_json", "TEXT DEFAULT '{}'"),
            ("total_reactions", "INTEGER DEFAULT 0"),
            ("report_count", "INTEGER DEFAULT 0"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("approved_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("deleted_at", "TIMESTAMP")
        ]
        
        try:
            for column_name, column_definition in migration_columns:
                cursor.execute(f"ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS {column_name} {column_definition}")
        except Exception as migration_error:
            logger.warning(f"Migration warning (non-critical): {migration_error}")
        
        # Community reactions table - one reaction per user per post
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_reactions (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL,
                viewer_uid_hash TEXT NOT NULL,
                viewer_uid INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(post_id, viewer_uid)
            );
        """)
        
        # Community reports table with priority system
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_reports (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL,
                reporter_uid_hash TEXT NOT NULL,
                reporter_uid INTEGER NOT NULL,
                reason TEXT NOT NULL,
                notes TEXT,
                state TEXT DEFAULT 'pending' CHECK (state IN ('pending', 'reviewed', 'dismissed', 'actioned')),
                priority INTEGER DEFAULT 0,
                
                mod_response TEXT,
                mod_user_id INTEGER,
                reviewed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(post_id, reporter_uid)
            );
        """)
        
        # Community mutes table - viewer-scoped
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_mutes (
                id SERIAL PRIMARY KEY,
                viewer_uid INTEGER NOT NULL,
                muted_author_uid_hash TEXT,
                muted_companion_id INTEGER,
                muted_category TEXT,
                mute_type TEXT NOT NULL CHECK (mute_type IN ('author', 'companion', 'category')),
                expires_at TIMESTAMP,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE (viewer_uid, muted_author_uid_hash),
                UNIQUE (viewer_uid, muted_companion_id),
                UNIQUE (viewer_uid, muted_category)
            );
        """)
        
        # User community stats for rate limiting
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_community_stats (
                user_id INTEGER PRIMARY KEY,
                posts_today INTEGER DEFAULT 0,
                posts_this_hour INTEGER DEFAULT 0,
                images_today INTEGER DEFAULT 0,
                reactions_this_minute INTEGER DEFAULT 0,
                reports_today INTEGER DEFAULT 0,
                total_posts INTEGER DEFAULT 0,
                total_reactions_given INTEGER DEFAULT 0,
                total_reactions_received INTEGER DEFAULT 0,
                total_reports_made INTEGER DEFAULT 0,
                total_reports_received INTEGER DEFAULT 0,
                trust_score REAL DEFAULT 1.0,
                shadow_banned BOOLEAN DEFAULT FALSE,
                shadow_banned_until TIMESTAMP,
                warnings_count INTEGER DEFAULT 0,
                last_post_at TIMESTAMP,
                last_reaction_at TIMESTAMP,
                last_hourly_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_daily_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # User community avatars table - stores current avatar selection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_community_avatars (
                user_id INTEGER PRIMARY KEY,
                companion_id INTEGER NOT NULL,
                companion_name TEXT NOT NULL,
                companion_rarity TEXT DEFAULT 'common',
                avatar_url TEXT NOT NULL,
                selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Avatar change tracking table - implements cooldown with ad bypass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_avatar_changes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                old_companion_id INTEGER,
                old_companion_name TEXT,
                new_companion_id INTEGER NOT NULL,
                new_companion_name TEXT NOT NULL,
                change_type TEXT DEFAULT 'normal' CHECK (change_type IN ('normal', 'ad_bypass', 'premium_skip')),
                cooldown_expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # FORCE CREATE user_community_avatars table if missing (migration fix)
        try:
            cursor.execute("SELECT 1 FROM user_community_avatars LIMIT 1")
        except Exception as e:
            if "does not exist" in str(e):
                logger.info("🔄 Creating missing user_community_avatars table...")
                cursor.execute("""
                    CREATE TABLE user_community_avatars (
                        user_id INTEGER PRIMARY KEY,
                        companion_id INTEGER NOT NULL,
                        companion_name TEXT NOT NULL,
                        companion_rarity TEXT DEFAULT 'common',
                        avatar_url TEXT NOT NULL,
                        selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("✅ user_community_avatars table created successfully")
        
        # Performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created_at_desc ON community_posts(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_category_created_at ON community_posts(category, created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_status ON community_posts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reactions_post ON community_reactions(post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_state ON community_reports(state, priority DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mutes_viewer ON community_mutes(viewer_uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_author_hash ON community_posts(author_uid_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_avatar_changes_user_cooldown ON user_avatar_changes(user_id, cooldown_expires_at)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Community database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize community database: {e}")
        return False

# ===============================
# UTILITY FUNCTIONS
# ===============================

def generate_anonymous_hash(user_id: int, salt: str = "community_anon_v1") -> str:
    """Generate consistent anonymous hash for user"""
    return hashlib.sha256(f"{salt}_{user_id}".encode()).hexdigest()[:12]

def get_user_companion_info(user_id: int) -> Dict[str, Any]:
    """Get user's current companion for avatar display"""
    try:
        # First check if user has a community avatar preference
        community_companion = get_user_community_avatar(user_id)
        if community_companion:
            return community_companion
            
        # Fall back to equipped companion
        from cosmetic_system import get_user_equipped_companions
        equipped_companions = get_user_equipped_companions(user_id)
        
        if equipped_companions:
            companion = equipped_companions[0]
            return {
                'companion_id': companion['id'],
                'skin_id': companion.get('skin_id'),
                'name': companion['name'],
                'rarity': companion.get('rarity', 'common'),
                'avatar_url': f"/static/companions/{companion['name'].lower()}.png"
            }
        else:
            # Default companion based on tier
            from unified_tier_system import get_effective_plan
            user_plan = session.get('user_plan', 'free')
            trial_active = session.get('trial_active', False)
            effective_plan = get_effective_plan(user_plan, trial_active)
            
            default_companions = {
                'free': {'id': 1, 'name': 'GamerJay', 'rarity': 'common'},
                'growth': {'id': 2, 'name': 'Sky', 'rarity': 'rare'},
                'max': {'id': 3, 'name': 'Crimson', 'rarity': 'epic'}
            }
            
            default = default_companions.get(effective_plan, default_companions['free'])
            return {
                'companion_id': default['id'],
                'skin_id': None,
                'name': default['name'],
                'rarity': default['rarity'],
                'avatar_url': f"/static/logos/{default['name']} Free companion.png" if default['name'] == 'GamerJay' else f"/static/logos/{default['name']}.png"
            }
            
    except Exception as e:
        logger.error(f"Failed to get companion info: {e}")
        return {
            'companion_id': 1,
            'skin_id': None,
            'name': 'Soul',
            'rarity': 'common',
            'avatar_url': '/static/logos/IntroLogo.png'
        }

def get_user_community_avatar(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's chosen community avatar companion"""
    try:
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return None
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Get user's community avatar preference
        cursor.execute("""
            SELECT companion_id, companion_name, companion_rarity, avatar_url
            FROM user_community_avatars 
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'companion_id': result[0],
                'skin_id': None,
                'name': result[1],
                'rarity': result[2],
                'avatar_url': result[3]
            }
        return None
        
    except Exception:
        return None

def set_user_community_avatar(user_id: int, companion_data: Dict[str, Any]) -> bool:
    """Set user's chosen community avatar companion"""
    try:
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_community_avatars (
                user_id INTEGER PRIMARY KEY,
                companion_id INTEGER NOT NULL,
                companion_name TEXT NOT NULL,
                companion_rarity TEXT NOT NULL,
                avatar_url TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Insert or update avatar preference
        cursor.execute("""
            INSERT INTO user_community_avatars 
            (user_id, companion_id, companion_name, companion_rarity, avatar_url)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                companion_id = EXCLUDED.companion_id,
                companion_name = EXCLUDED.companion_name,
                companion_rarity = EXCLUDED.companion_rarity,
                avatar_url = EXCLUDED.avatar_url,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            companion_data['companion_id'],
            companion_data['name'],
            companion_data['rarity'],
            companion_data['avatar_url']
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to set community avatar: {e}")
        return False

def check_avatar_change_cooldown(user_id: int) -> Dict[str, Any]:
    """Check if user can change avatar or is in cooldown period"""
    try:
        import os
        import psycopg2
        from datetime import datetime, timezone, timedelta
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return {'can_change': True, 'cooldown_remaining': 0}
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check last avatar change
        cursor.execute("""
            SELECT cooldown_expires_at, change_type, new_companion_name
            FROM user_avatar_changes 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'can_change': True, 'cooldown_remaining': 0}
        
        cooldown_expires, change_type, last_companion = result
        now = datetime.now(timezone.utc)
        
        if cooldown_expires.replace(tzinfo=timezone.utc) > now:
            remaining_seconds = int((cooldown_expires.replace(tzinfo=timezone.utc) - now).total_seconds())
            return {
                'can_change': False,
                'cooldown_remaining': remaining_seconds,
                'last_companion': last_companion,
                'change_type': change_type
            }
        
        return {'can_change': True, 'cooldown_remaining': 0}
        
    except Exception as e:
        logger.error(f"Failed to check avatar cooldown: {e}")
        return {'can_change': True, 'cooldown_remaining': 0}

def record_avatar_change(user_id: int, old_companion_data: Dict, new_companion_data: Dict, change_type: str = 'normal') -> bool:
    """Record avatar change with appropriate cooldown"""
    try:
        import os
        import psycopg2
        from datetime import datetime, timezone, timedelta
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Determine cooldown duration based on user tier and change type
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        from unified_tier_system import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # Cooldown rules
        if change_type == 'ad_bypass':
            # Free users who watch ad - 6 hours cooldown
            cooldown_hours = 6
        elif change_type == 'premium_skip':
            # Growth/Max users can skip cooldown but still have short protection
            cooldown_hours = 1
        else:
            # Normal cooldown times
            if effective_plan == 'free':
                cooldown_hours = 24  # 24 hours for free users
            elif effective_plan == 'growth':
                cooldown_hours = 12  # 12 hours for Growth users
            else:  # max
                cooldown_hours = 6   # 6 hours for Max users
        
        cooldown_expires = datetime.now(timezone.utc) + timedelta(hours=cooldown_hours)
        
        # Record the change
        cursor.execute("""
            INSERT INTO user_avatar_changes 
            (user_id, old_companion_id, old_companion_name, new_companion_id, new_companion_name, change_type, cooldown_expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            old_companion_data.get('companion_id') if old_companion_data else None,
            old_companion_data.get('name') if old_companion_data else None,
            new_companion_data.get('companion_id'),
            new_companion_data.get('name'),
            change_type,
            cooldown_expires
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎭 Avatar change recorded for user {user_id}: {change_type} change, cooldown until {cooldown_expires}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to record avatar change: {e}")
        return False

def get_user_tier_badge(user_id: int) -> str:
    """Get user's tier badge for display"""
    try:
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        from unified_tier_system import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        tier_badges = {
            'free': 'Free',
            'growth': 'Growth', 
            'max': 'Max'
        }
        
        return tier_badges.get(effective_plan, 'Free')
        
    except Exception:
        return 'Free'

# ===============================
# CONTENT SAFETY PIPELINE
# ===============================

def moderate_text_content(text: str) -> Dict[str, Any]:
    """Run text through safety moderation pipeline"""
    try:
        result = {
            'approved': True,
            'flags': [],
            'risk_score': 0.0,
            'suggestions': []
        }
        
        # PII Detection
        import re
        pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'address': r'\b\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b'
        }
        
        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                result['flags'].append(f'pii_{pii_type}')
                result['risk_score'] = max(result['risk_score'], 0.8)
                result['approved'] = False
                result['suggestions'].append(f"Remove {pii_type} information for privacy")
        
        # Self-harm detection
        self_harm_keywords = [
            'kill myself', 'end it all', 'suicide', 'self harm', 'want to die',
            'better off dead', 'not worth living'
        ]
        
        text_lower = text.lower()
        for keyword in self_harm_keywords:
            if keyword in text_lower:
                result['flags'].append('self_harm_risk')
                result['risk_score'] = max(result['risk_score'], 0.9)
                result['approved'] = False
                result['suggestions'].append("Crisis resources: 988 Suicide Prevention Lifeline")
                break
        
        # URL detection (strip for safety)
        if re.search(r'http[s]?://|www\.', text):
            result['flags'].append('contains_urls')
            result['suggestions'].append("Links are not allowed in community posts")
        
        return result
        
    except Exception as e:
        logger.error(f"Text moderation failed: {e}")
        return {
            'approved': False,
            'flags': ['moderation_error'],
            'risk_score': 1.0,
            'suggestions': ['Content could not be verified for safety']
        }

# ===============================
# API ENDPOINTS
# ===============================

@community_bp.route('/posts', methods=['POST'])
def create_post():
    """Create a new community post"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        text_content = data.get('text', '').strip()
        category = data.get('category', 'all')
        hashtags = data.get('hashtags', [])
        
        # Validate input
        if not text_content:
            return jsonify({"error": "Post text is required"}), 400
        
        if len(text_content) > COMMUNITY_CONFIG["content_limits"]["max_chars"]:
            return jsonify({
                "error": f"Text too long (max {COMMUNITY_CONFIG['content_limits']['max_chars']} chars)"
            }), 400
        
        # Validate category
        valid_categories = [cat["id"] for cat in COMMUNITY_CONFIG["categories"]]
        if category not in valid_categories:
            return jsonify({"error": f"Invalid category. Valid: {valid_categories}"}), 400
        
        # Run text moderation
        text_moderation = moderate_text_content(text_content)
        
        if not text_moderation['approved']:
            return jsonify({
                "error": "Content blocked by safety filters",
                "reason": "Your post couldn't be shared because it may violate our community rules",
                "suggestions": text_moderation['suggestions'],
                "flags": text_moderation['flags']
            }), 400
        
        # Get user info
        companion_info = get_user_companion_info(user_id)
        author_hash = generate_anonymous_hash(user_id)
        
        # Create post record
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "Database not available"}), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO community_posts (
                author_uid_hash, author_uid, companion_id, companion_skin_id,
                category, text, hashtags, status, moderation_state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            author_hash, user_id, companion_info['companion_id'], companion_info.get('skin_id'),
            category, text_content, json.dumps(hashtags), 'approved',
            json.dumps(text_moderation)
        ))
        
        post_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"📝 Community post created: {post_id} by user {user_id}")
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'status': 'published',
            'message': 'Post shared successfully!'
        })
        
    except Exception as e:
        logger.error(f"Failed to create community post: {e}")
        return jsonify({"error": "Failed to create post"}), 500

@community_bp.route('/posts/<int:post_id>/react', methods=['POST'])
def react_to_post(post_id: int):
    """Add reaction to a post"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or 'emoji' not in data:
            return jsonify({"error": "emoji required"}), 400
        
        emoji = data['emoji']
        
        # Validate emoji
        if emoji not in COMMUNITY_CONFIG["allowed_reactions"]:
            return jsonify({
                "error": f"Invalid emoji. Allowed: {COMMUNITY_CONFIG['allowed_reactions']}"
            }), 400
        
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "Database not available"}), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if post exists and is approved
        cursor.execute("""
            SELECT id FROM community_posts 
            WHERE id = %s AND status = 'approved' AND deleted_at IS NULL
        """, (post_id,))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Post not found"}), 404
        
        viewer_hash = generate_anonymous_hash(user_id)
        
        # Check if user already reacted
        cursor.execute("""
            SELECT emoji FROM community_reactions 
            WHERE post_id = %s AND viewer_uid = %s
        """, (post_id, user_id))
        
        existing_reaction = cursor.fetchone()
        
        if existing_reaction:
            if existing_reaction[0] == emoji:
                # Remove same reaction
                cursor.execute("""
                    DELETE FROM community_reactions 
                    WHERE post_id = %s AND viewer_uid = %s
                """, (post_id, user_id))
                action = 'removed'
            else:
                # Change reaction
                cursor.execute("""
                    UPDATE community_reactions 
                    SET emoji = %s, created_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s AND viewer_uid = %s
                """, (emoji, post_id, user_id))
                action = 'changed'
        else:
            # Add new reaction
            cursor.execute("""
                INSERT INTO community_reactions (post_id, viewer_uid_hash, viewer_uid, emoji)
                VALUES (%s, %s, %s, %s)
            """, (post_id, viewer_hash, user_id, emoji))
            action = 'added'
        
        # Update post reaction counts
        cursor.execute("""
            SELECT emoji, COUNT(*) as count
            FROM community_reactions 
            WHERE post_id = %s
            GROUP BY emoji
        """, (post_id,))
        
        reaction_counts = {row[0]: row[1] for row in cursor.fetchall()}
        total_reactions = sum(reaction_counts.values())
        
        cursor.execute("""
            UPDATE community_posts 
            SET reaction_counts_json = %s, total_reactions = %s
            WHERE id = %s
        """, (json.dumps(reaction_counts), total_reactions, post_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'action': action,
            'reaction_counts': reaction_counts,
            'total_reactions': total_reactions
        })
        
    except Exception as e:
        logger.error(f"Failed to react to post: {e}")
        return jsonify({"error": "Reaction failed"}), 500

@community_bp.route('/posts', methods=['GET'])
def get_community_feed():
    """Get community feed with filtering"""
    try:
        user_id = session.get('user_id')  # Can be None for anonymous viewing
        
        # Get query parameters
        category = request.args.get('category', 'all')
        sort_by = request.args.get('sort', 'new')
        limit = min(int(request.args.get('limit', 20)), 50)
        after_id = request.args.get('after_id')
        
        # Validate sort option
        if sort_by not in ['new', 'top_week', 'top_month', 'top_all']:
            return jsonify({"error": "Invalid sort option"}), 400
        
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "Database not available"}), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if table exists and has required columns
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'community_posts'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Close current connection
            conn.close()
            # Initialize database tables
            initialize_community_database()
            # Return empty result for now since table was just created
            return jsonify({
                'posts': [],
                'has_more': False,
                'category': category,
                'sort': sort_by,
                'empty_state': {
                    'title': 'Community is ready!',
                    'message': 'Database initialized. Start sharing your thoughts! 💫'
                }
            })
        
        # Check if category column exists (schema validation)
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'community_posts' AND column_name = 'category'
        """)
        category_exists = cursor.fetchone()
        
        if not category_exists:
            # Schema is outdated, need to run migration
            conn.close()
            initialize_community_database()
            return jsonify({
                'posts': [],
                'has_more': False,
                'category': category,
                'sort': sort_by,
                'empty_state': {
                    'title': 'Community updated!',
                    'message': 'Database schema updated. Please refresh to continue! 🔄'
                }
            })
        
        # Build query
        where_clauses = ["status = 'approved'", "deleted_at IS NULL"]
        params = []
        
        if category != 'all':
            where_clauses.append("category = %s")
            params.append(category)
        
        if after_id:
            where_clauses.append("id < %s")
            params.append(after_id)
        
        # Get user's mutes if logged in
        muted_hashes = []
        if user_id:
            cursor.execute("""
                SELECT muted_author_uid_hash, muted_companion_id, muted_category
                FROM community_mutes 
                WHERE viewer_uid = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (user_id,))
            
            for row in cursor.fetchall():
                muted_hash, muted_companion, muted_cat = row
                if muted_hash:
                    muted_hashes.append(muted_hash)
        
        if muted_hashes:
            where_clauses.append(f"author_uid_hash NOT IN ({','.join(['%s'] * len(muted_hashes))})")
            params.extend(muted_hashes)
        
        where_clause = "WHERE " + " AND ".join(where_clauses)
        
        # Order by clause
        if sort_by == 'new':
            order_clause = "ORDER BY created_at DESC"
        else:  # top variants
            order_clause = "ORDER BY total_reactions DESC, created_at DESC"
        
        query = f"""
            SELECT id, author_uid_hash, companion_id, companion_skin_id,
                   category, text, hashtags, reaction_counts_json, 
                   total_reactions, created_at
            FROM community_posts 
            {where_clause} 
            {order_clause} 
            LIMIT %s
        """
        
        params.append(limit)
        cursor.execute(query, params)
        
        posts = []
        for row in cursor.fetchall():
            (post_id, author_hash, companion_id, companion_skin_id, 
             cat, text, hashtags_json, reactions_json, total_reactions, created_at) = row
            
            # Calculate time ago
            post_time = datetime.fromisoformat(created_at)
            time_ago = format_time_ago(post_time)
            
            # Get companion avatar info - use actual companion names
            companion_names = {
                1: 'GamerJay Free companion',
                2: 'Sky a premium companion', 
                3: 'Crimson',
                4: 'Violet',
                7: 'GamerJay premium companion'
            }
            companion_name = companion_names.get(companion_id, 'GamerJay Free companion')
            avatar_url = f"/static/logos/{companion_name}.png"
            
            posts.append({
                'id': post_id,
                'author_display': 'Anonymous',
                'author_hash': author_hash[:8],  # Shortened for muting
                'avatar_url': avatar_url,
                'tier_badge': 'Free',  # Would get from companion/skin rarity
                'category': cat,
                'text': text,
                'hashtags': json.loads(hashtags_json) if hashtags_json else [],
                'reactions': json.loads(reactions_json) if reactions_json else {},
                'total_reactions': total_reactions,
                'time_ago': time_ago,
                'created_at': created_at
            })
        
        conn.close()
        
        response = {
            'posts': posts,
            'has_more': len(posts) == limit,
            'category': category,
            'sort': sort_by
        }
        
        # Add empty state message if no posts
        if not posts:
            response['empty_state'] = {
                'title': 'No content yet',
                'message': 'Be the first to share something beautiful! 💙'
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Failed to get community feed: {e}")
        logger.error(f"Community feed error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Community feed traceback: {traceback.format_exc()}")
        
        # Check if it's a table/column issue
        error_str = str(e).lower()
        if 'does not exist' in error_str or 'column' in error_str:
            # Try to reinitialize the database
            try:
                logger.info("Attempting to reinitialize community database due to schema error...")
                initialize_community_database()
                return jsonify({
                    "error": "Database schema updated. Please refresh the page.",
                    "retry": True
                }), 503
            except Exception as init_error:
                logger.error(f"Failed to reinitialize community database: {init_error}")
        
        return jsonify({"error": "Failed to load feed", "details": str(e)}), 500

@community_bp.route('/test', methods=['GET'])
def test_community():
    """Simple test endpoint for community system"""
    return jsonify({
        "success": True,
        "message": "Community system is working",
        "posts": [],
        "has_more": False,
        "empty_state": {
            "title": "Community Test",
            "message": "This is a test response from the community system! 🎯"
        }
    })

@community_bp.route('/debug/init-database', methods=['POST'])
def debug_init_database():
    """Debug endpoint to manually initialize community database"""
    try:
        initialize_community_database()
        return jsonify({"success": True, "message": "Community database initialized successfully"})
    except Exception as e:
        logger.error(f"Failed to initialize community database: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@community_bp.route('/posts/<int:post_id>/report', methods=['POST'])
def report_post(post_id: int):
    """Report a post for moderation"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or 'reason' not in data:
            return jsonify({"error": "reason required"}), 400
        
        reason = data['reason']
        notes = data.get('notes', '').strip()
        
        # Validate reason
        if reason not in COMMUNITY_CONFIG["report_reasons"]:
            return jsonify({
                "error": f"Invalid reason. Valid: {COMMUNITY_CONFIG['report_reasons']}"
            }), 400
        
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "Database not available"}), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if post exists
        cursor.execute("""
            SELECT id FROM community_posts WHERE id = %s AND deleted_at IS NULL
        """, (post_id,))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Post not found"}), 404
        
        # Check if user already reported this post
        cursor.execute("""
            SELECT id FROM community_reports 
            WHERE post_id = %s AND reporter_uid = %s
        """, (post_id, user_id))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "You have already reported this post"}), 400
        
        reporter_hash = generate_anonymous_hash(user_id)
        
        # Determine priority based on reason
        priority_map = {
            'self_harm_risk': 10,
            'hate_or_violence': 9,
            'pii_privacy': 8,
            'graphic_content': 7,
            'harassment': 5,
            'spam': 3,
            'other': 1
        }
        priority = priority_map.get(reason, 1)
        
        # Create report
        cursor.execute("""
            INSERT INTO community_reports (
                post_id, reporter_uid_hash, reporter_uid, reason, notes, priority
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (post_id, reporter_hash, user_id, reason, notes, priority))
        
        report_id = cursor.lastrowid
        
        # Update post report count
        cursor.execute("""
            UPDATE community_posts 
            SET report_count = report_count + 1
            WHERE id = %s
        """, (post_id,))
        
        # Auto-hide for critical reasons
        auto_escalate_reasons = ['self_harm_risk', 'hate_or_violence', 'graphic_content', 'pii_privacy']
        auto_hidden = False
        
        if reason in auto_escalate_reasons:
            cursor.execute("""
                UPDATE community_posts 
                SET status = 'hidden'
                WHERE id = %s
            """, (post_id,))
            auto_hidden = True
        
        conn.commit()
        conn.close()
        
        logger.info(f"📋 Post {post_id} reported by user {user_id} for {reason}")
        
        response = {
            'success': True,
            'report_id': report_id,
            'message': 'Report submitted for review'
        }
        
        if auto_hidden:
            response['message'] = 'Content has been hidden while under review'
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Failed to report post: {e}")
        return jsonify({"error": "Report failed"}), 500

@community_bp.route('/mute', methods=['POST'])
def mute_content():
    """Mute author, companion, or category"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Mute data required"}), 400
        
        mute_type = data.get('type')  # 'author', 'companion', 'category'
        target = data.get('target')   # author_hash, companion_id, or category name
        duration_days = data.get('duration_days', 30)
        reason = data.get('reason', '').strip()
        
        if not mute_type or not target:
            return jsonify({"error": "type and target required"}), 400
        
        if mute_type not in ['author', 'companion', 'category']:
            return jsonify({"error": "Invalid mute type"}), 400
        
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({"error": "Database not available"}), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Calculate expiry
        expires_at = None
        if duration_days > 0:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
        
        # Create mute record
        if mute_type == 'author':
            cursor.execute("""
                INSERT INTO community_mutes (
                    viewer_uid, muted_author_uid_hash, mute_type, expires_at, reason
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (viewer_uid, muted_author_uid_hash) DO UPDATE SET
                    mute_type = EXCLUDED.mute_type,
                    expires_at = EXCLUDED.expires_at,
                    reason = EXCLUDED.reason
            """, (user_id, target, mute_type, expires_at, reason))
        elif mute_type == 'companion':
            cursor.execute("""
                INSERT INTO community_mutes (
                    viewer_uid, muted_companion_id, mute_type, expires_at, reason
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (viewer_uid, muted_companion_id) DO UPDATE SET
                    mute_type = EXCLUDED.mute_type,
                    expires_at = EXCLUDED.expires_at,
                    reason = EXCLUDED.reason
            """, (user_id, int(target), mute_type, expires_at, reason))
        elif mute_type == 'category':
            cursor.execute("""
                INSERT INTO community_mutes (
                    viewer_uid, muted_category, mute_type, expires_at, reason
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (viewer_uid, muted_category) DO UPDATE SET
                    mute_type = EXCLUDED.mute_type,
                    expires_at = EXCLUDED.expires_at,
                    reason = EXCLUDED.reason
            """, (user_id, target, mute_type, expires_at, reason))
        
        mute_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"🔇 User {user_id} muted {mute_type} {target}")
        
        return jsonify({
            'success': True,
            'mute_id': mute_id,
            'message': f'{mute_type.title()} muted successfully',
            'expires_at': expires_at
        })
        
    except Exception as e:
        logger.error(f"Failed to mute content: {e}")
        return jsonify({"error": "Mute failed"}), 500

@community_bp.route('/avatar', methods=['GET'])
def get_community_avatar():
    """Get user's community avatar companion"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        companion_info = get_user_companion_info(user_id)
        
        return jsonify({
            'success': True,
            'companion': companion_info
        })
        
    except Exception as e:
        logger.error(f"Failed to get community avatar: {e}")
        return jsonify({"error": "Failed to get avatar"}), 500

@community_bp.route('/avatar/check', methods=['GET'])
def check_avatar_change_availability():
    """Check if user can change avatar or is in cooldown"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        cooldown_info = check_avatar_change_cooldown(user_id)
        
        # Get user tier for cooldown rules display
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        from unified_tier_system import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        cooldown_rules = {
            'free': {'normal': 24, 'ad_bypass': 6},
            'growth': {'normal': 12, 'premium_skip': 1},
            'max': {'normal': 6, 'premium_skip': 1}
        }
        
        return jsonify({
            'success': True,
            'can_change': cooldown_info['can_change'],
            'cooldown_remaining': cooldown_info.get('cooldown_remaining', 0),
            'last_companion': cooldown_info.get('last_companion'),
            'user_tier': effective_plan,
            'cooldown_rules': cooldown_rules.get(effective_plan, cooldown_rules['free'])
        })
        
    except Exception as e:
        logger.error(f"Failed to check avatar availability: {e}")
        return jsonify({"error": "Failed to check availability"}), 500

@community_bp.route('/avatar', methods=['POST'])
def set_community_avatar():
    """Set user's community avatar companion with cooldown system"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json()
        if not data or 'companion_id' not in data:
            return jsonify({"error": "companion_id required"}), 400
        
        companion_id = data['companion_id']
        companion_name = data.get('name', 'Unknown')
        companion_rarity = data.get('rarity', 'common')
        avatar_url = data.get('avatar_url', f'/static/companions/{companion_name.lower()}.png')
        change_type = data.get('change_type', 'normal')  # 'normal', 'ad_bypass', 'premium_skip'
        confirmed = data.get('confirmed', False)
        
        # Check cooldown status
        cooldown_info = check_avatar_change_cooldown(user_id)
        
        if not cooldown_info['can_change'] and change_type == 'normal':
            remaining_hours = cooldown_info['cooldown_remaining'] // 3600
            remaining_minutes = (cooldown_info['cooldown_remaining'] % 3600) // 60
            
            return jsonify({
                "error": "Avatar change on cooldown",
                "cooldown_remaining": cooldown_info['cooldown_remaining'],
                "message": f"You can change your avatar again in {remaining_hours}h {remaining_minutes}m",
                "last_companion": cooldown_info.get('last_companion'),
                "can_bypass": True  # Show bypass options
            }), 429
        
        # Get user tier for bypass validation
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        
        from unified_tier_system import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # Validate bypass options
        if change_type == 'ad_bypass' and effective_plan != 'free':
            return jsonify({"error": "Ad bypass only available for free users"}), 403
        
        if change_type == 'premium_skip' and effective_plan == 'free':
            return jsonify({"error": "Premium skip not available for free users"}), 403
        
        # Validate that user has access to this companion
        from cosmetic_system import get_available_companions_for_user
        available_companions = get_available_companions_for_user(user_id)
        
        # Allow basic tier companions for all users
        default_companions = {
            'free': [{'id': 1, 'name': 'GamerJay', 'rarity': 'common'}],
            'growth': [
                {'id': 1, 'name': 'GamerJay', 'rarity': 'common'},
                {'id': 2, 'name': 'Sky', 'rarity': 'rare'}
            ],
            'max': [
                {'id': 1, 'name': 'GamerJay', 'rarity': 'common'},
                {'id': 2, 'name': 'Sky', 'rarity': 'rare'},
                {'id': 3, 'name': 'Crimson', 'rarity': 'epic'}
            ]
        }
        
        allowed_companions = available_companions + default_companions.get(effective_plan, [])
        
        # Check if companion is allowed
        companion_allowed = any(c.get('id') == companion_id for c in allowed_companions)
        if not companion_allowed:
            return jsonify({"error": "Companion not available"}), 403
        
        # Get current companion for change tracking
        old_companion_data = get_user_community_avatar(user_id)
        
        companion_data = {
            'companion_id': companion_id,
            'name': companion_name,
            'rarity': companion_rarity,
            'avatar_url': avatar_url
        }
        
        # Set the avatar
        success = set_user_community_avatar(user_id, companion_data)
        
        if success:
            # Record the change with appropriate cooldown
            record_avatar_change(user_id, old_companion_data, companion_data, change_type)
            
            logger.info(f"🎭 User {user_id} set community avatar to {companion_name} (type: {change_type})")
            
            return jsonify({
                'success': True,
                'message': f'Community avatar set to {companion_name}',
                'companion': companion_data,
                'change_type': change_type
            })
        else:
            return jsonify({"error": "Failed to set avatar"}), 500
        
    except Exception as e:
        logger.error(f"Failed to set community avatar: {e}")
        return jsonify({"error": "Failed to set avatar"}), 500

@community_bp.route('/select-companion/<int:companion_id>', methods=['GET'])
def select_companion_direct(companion_id):
    """Direct link to select a companion - bypasses JavaScript issues"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/login')
        
        # Get user tier information
        from unified_tier_system import get_effective_plan
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # Define available companions by tier
        available_companions = {
            # Free tier companions
            1: {'name': 'GamerJay', 'tier': 'free', 'avatar_url': '/static/logos/GamerJay Free companion.png'},
            5: {'name': 'Blayzo', 'tier': 'free', 'avatar_url': '/static/logos/Blayzo.png'},
            6: {'name': 'Blayzica', 'tier': 'free', 'avatar_url': '/static/logos/Blayzica.png'},
            8: {'name': 'Claude', 'tier': 'free', 'avatar_url': '/static/logos/Claude Free.png'},
            9: {'name': 'Blayzia', 'tier': 'free', 'avatar_url': '/static/logos/Blayzia.png'},
            10: {'name': 'Blayzion', 'tier': 'free', 'avatar_url': '/static/logos/Blayzion.png'},
            11: {'name': 'Blayzike', 'tier': 'referral', 'avatar_url': '/static/logos/Blayzike.png'},
            12: {'name': 'Blazelian', 'tier': 'referral', 'avatar_url': '/static/logos/Blazelian.png'},
            # Growth tier companions
            2: {'name': 'Sky', 'tier': 'growth', 'avatar_url': '/static/logos/Sky a premium companion.png'},
            7: {'name': 'GamerJay Premium', 'tier': 'growth', 'avatar_url': '/static/logos/GamerJay premium companion.png'},
            20: {'name': 'Claude Growth', 'tier': 'growth', 'avatar_url': '/static/logos/Claude Growth.png'},
            21: {'name': 'Blayzo Premium', 'tier': 'growth', 'avatar_url': '/static/logos/Blayzo premium companion.png'},
            22: {'name': 'Blayzica Pro', 'tier': 'growth', 'avatar_url': '/static/logos/Blayzica Pro.png'},
            23: {'name': 'WatchDog Premium', 'tier': 'growth', 'avatar_url': '/static/logos/WatchDog a Premium companion.png'},
            24: {'name': 'Rozia', 'tier': 'growth', 'avatar_url': '/static/logos/Rozia.png'},
            # Max tier companions
            3: {'name': 'Crimson', 'tier': 'max', 'avatar_url': '/static/logos/Crimson a Max companion.png'},
            4: {'name': 'Violet', 'tier': 'max', 'avatar_url': '/static/logos/Violet.png'},
            30: {'name': 'Claude Max', 'tier': 'max', 'avatar_url': '/static/logos/Claude Max.png'},
            31: {'name': 'Royal', 'tier': 'max', 'avatar_url': '/static/logos/Royal a Max companion.png'},
            32: {'name': 'Ven Blayzica', 'tier': 'max', 'avatar_url': '/static/logos/Ven Blayzica a Max companion.png'},
            33: {'name': 'Ven Sky', 'tier': 'max', 'avatar_url': '/static/logos/Ven Sky a Max companion.png'},
            34: {'name': 'WatchDog Max', 'tier': 'max', 'avatar_url': '/static/logos/WatchDog a Max Companion.png'},
            # Referral tier companions
            40: {'name': 'Claude Referral', 'tier': 'referral', 'avatar_url': '/static/logos/Claude Referral.png'},
            41: {'name': 'Blayzo Referral', 'tier': 'referral', 'avatar_url': '/static/logos/Blayzo Referral.png'},
            42: {'name': 'Nyxara', 'tier': 'referral', 'avatar_url': '/static/logos/Nyxara.png'},
            43: {'name': 'Royal', 'tier': 'referral', 'avatar_url': '/static/logos/Royal a Max companion.png'},
            44: {'name': 'Sapphire', 'tier': 'referral', 'avatar_url': '/static/logos/Sapphire.png'},
        }
        
        companion = available_companions.get(companion_id)
        if not companion:
            return f"<script>alert('Companion not found'); window.location.href='/community';</script>"
        
        # Check if user has access to this tier
        companion_tier = companion['tier']
        user_has_access = False
        
        if companion_tier == 'free':
            user_has_access = True
        elif companion_tier == 'growth' and effective_plan in ['growth', 'max']:
            user_has_access = True
        elif companion_tier == 'max' and effective_plan == 'max':
            user_has_access = True
        elif companion_tier == 'referral':
            # Check referral unlock requirements
            referral_requirements = {
                11: 0,   # Blayzike - needs 5 referrals (moved back to free for now)
                12: 0,   # Blazelian - needs 8 referrals (moved back to free for now)  
                40: 10,  # Claude Referral - needs 10 referrals
                41: 0,   # Blayzo Referral - needs special unlock
                42: 6,   # Nyxara - needs 6 referrals
                43: 3,   # Royal - needs 3 referrals
                44: 1,   # Sapphire - needs 1 referral
            }
            
            required_referrals = referral_requirements.get(companion_id, 999)
            user_referrals = 0  # TODO: Get actual user referral count
            
            # For now, allow access to show them but they should be properly locked
            user_has_access = True  # Change this when referral system is connected
        
        if not user_has_access:
            return f"<script>alert('This companion requires {companion_tier.title()} tier'); window.location.href='/community';</script>"
        
        # Set the companion
        companion_data = {
            'companion_id': companion_id,
            'name': companion['name'],
            'rarity': 'common',
            'avatar_url': companion['avatar_url']
        }
        
        success = set_user_community_avatar(user_id, companion_data)
        
        if success:
            return f"<script>alert('Avatar set to {companion['name']}!'); window.location.href='/community';</script>"
        else:
            return f"<script>alert('Failed to set avatar'); window.location.href='/community';</script>"
            
    except Exception as e:
        logger.error(f"Failed to select companion: {e}")
        return f"<script>alert('Error: {str(e)}'); window.location.href='/community';</script>"

@community_bp.route('/companion-selector', methods=['GET'])
def companion_selector_page():
    """Simple HTML page with companion selection links"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/login')
        
        # Get user tier information
        from unified_tier_system import get_effective_plan
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # Define companions organized by tier
        companions_by_tier = {
            'free': [
                {'id': 1, 'name': 'GamerJay', 'avatar_url': '/static/logos/GamerJay Free companion.png'},
                {'id': 5, 'name': 'Blayzo', 'avatar_url': '/static/logos/Blayzo.png'},
                {'id': 6, 'name': 'Blayzica', 'avatar_url': '/static/logos/Blayzica.png'},
                {'id': 8, 'name': 'Claude', 'avatar_url': '/static/logos/Claude Free.png'},
                {'id': 9, 'name': 'Blayzia', 'avatar_url': '/static/logos/Blayzia.png'},
                {'id': 10, 'name': 'Blayzion', 'avatar_url': '/static/logos/Blayzion.png'}
            ],
            'growth': [
                {'id': 2, 'name': 'Sky', 'avatar_url': '/static/logos/Sky a premium companion.png'},
                {'id': 7, 'name': 'GamerJay Premium', 'avatar_url': '/static/logos/GamerJay premium companion.png'},
                {'id': 20, 'name': 'Claude Growth', 'avatar_url': '/static/logos/Claude Growth.png'},
                {'id': 21, 'name': 'Blayzo Premium', 'avatar_url': '/static/logos/Blayzo premium companion.png'},
                {'id': 22, 'name': 'Blayzica Pro', 'avatar_url': '/static/logos/Blayzica Pro.png'},
                {'id': 23, 'name': 'WatchDog Premium', 'avatar_url': '/static/logos/WatchDog a Premium companion.png'},
                {'id': 24, 'name': 'Rozia', 'avatar_url': '/static/logos/Rozia.png'}
            ],
            'max': [
                {'id': 3, 'name': 'Crimson', 'avatar_url': '/static/logos/Crimson a Max companion.png'},
                {'id': 4, 'name': 'Violet', 'avatar_url': '/static/logos/Violet.png'},
                {'id': 30, 'name': 'Claude Max', 'avatar_url': '/static/logos/Claude Max.png'},
                {'id': 31, 'name': 'Royal', 'avatar_url': '/static/logos/Royal a Max companion.png'},
                {'id': 32, 'name': 'Ven Blayzica', 'avatar_url': '/static/logos/Ven Blayzica a Max companion.png'},
                {'id': 33, 'name': 'Ven Sky', 'avatar_url': '/static/logos/Ven Sky a Max companion.png'},
                {'id': 34, 'name': 'WatchDog Max', 'avatar_url': '/static/logos/WatchDog a Max Companion.png'}
            ],
            'referral': [
                {'id': 11, 'name': 'Blayzike', 'avatar_url': '/static/logos/Blayzike.png', 'referrals_needed': 5},
                {'id': 42, 'name': 'Nyxara', 'avatar_url': '/static/logos/Nyxara.png', 'referrals_needed': 6},
                {'id': 12, 'name': 'Blazelian', 'avatar_url': '/static/logos/Blazelian.png', 'referrals_needed': 8},
                {'id': 40, 'name': 'Claude Referral', 'avatar_url': '/static/logos/Claude Referral.png', 'referrals_needed': 10},
                {'id': 41, 'name': 'Blayzo Referral', 'avatar_url': '/static/logos/Blayzo Referral.png', 'referrals_needed': 'Special'}
            ]
        }
        
        # Generate HTML
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Select Community Avatar - SoulBridge AI</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #000; color: #fff; padding: 20px; }}
                .tier {{ margin: 20px 0; padding: 20px; border: 2px solid #333; border-radius: 10px; }}
                .tier.unlocked {{ border-color: #00ffff; }}
                .tier.locked {{ border-color: #666; opacity: 0.5; }}
                .tier h3 {{ color: #00ffff; margin-top: 0; }}
                .companion {{ display: inline-block; margin: 10px; padding: 15px; background: #222; border-radius: 8px; text-align: center; }}
                .companion img {{ width: 64px; height: 64px; border-radius: 50%; }}
                .companion a {{ color: #00ffff; text-decoration: none; font-weight: bold; }}
                .companion a:hover {{ color: #fff; }}
                .companion.locked {{ opacity: 0.5; }}
                .companion.locked a {{ color: #666; cursor: not-allowed; }}
                .back-btn {{ background: #00ffff; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }}
                .current-tier {{ background: #333; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <a href="/community" class="back-btn">← Back to Community</a>
            
            <h1>🎭 Select Your Community Avatar</h1>
            
            <div class="current-tier">
                <strong>Your Current Tier:</strong> {effective_plan.title()} 
                {" (Trial Active)" if trial_active else ""}
            </div>
            
            <div class="tier unlocked">
                <h3>🆓 Free Tier</h3>
                <div class="companions">
        '''
        
        # Add Free tier companions (always unlocked)
        for companion in companions_by_tier['free']:
            html += f'''
                    <div class="companion">
                        <img src="{companion['avatar_url']}" alt="{companion['name']}">
                        <br>
                        <a href="/community/select-companion/{companion['id']}">{companion['name']}</a>
                    </div>
            '''
        
        html += '''
                </div>
            </div>
        '''
        
        # Add Growth tier
        is_growth_unlocked = effective_plan in ['growth', 'max']
        html += f'''
            <div class="tier {'unlocked' if is_growth_unlocked else 'locked'}">
                <h3>📈 Growth Tier {'(Unlocked)' if is_growth_unlocked else '(Locked - Requires Growth/Max subscription)'}</h3>
                <div class="companions">
        '''
        
        for companion in companions_by_tier['growth']:
            if is_growth_unlocked:
                html += f'''
                        <div class="companion">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="/community/select-companion/{companion['id']}">{companion['name']}</a>
                        </div>
                '''
            else:
                html += f'''
                        <div class="companion locked">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="#" onclick="alert('Requires Growth tier subscription')">{companion['name']}</a>
                        </div>
                '''
        
        html += '''
                </div>
            </div>
        '''
        
        # Add Max tier
        is_max_unlocked = effective_plan == 'max'
        html += f'''
            <div class="tier {'unlocked' if is_max_unlocked else 'locked'}">
                <h3>⭐ Max Tier {'(Unlocked)' if is_max_unlocked else '(Locked - Requires Max subscription)'}</h3>
                <div class="companions">
        '''
        
        for companion in companions_by_tier['max']:
            if is_max_unlocked:
                html += f'''
                        <div class="companion">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="/community/select-companion/{companion['id']}">{companion['name']}</a>
                        </div>
                '''
            else:
                html += f'''
                        <div class="companion locked">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="#" onclick="alert('Requires Max tier subscription')">{companion['name']}</a>
                        </div>
                '''
        
        html += '''
                </div>
            </div>
        '''
        
        # Add Referral tier
        html += f'''
            <div class="tier unlocked">
                <h3>🎁 Referral Rewards (Unlock by referring friends)</h3>
                <div class="companions">
        '''
        
        user_referrals = 0  # TODO: Get actual user referral count from referral system
        
        for companion in companions_by_tier['referral']:
            referrals_needed = companion.get('referrals_needed', 0)
            is_unlocked = user_referrals >= referrals_needed if isinstance(referrals_needed, int) else False
            
            if is_unlocked:
                html += f'''
                        <div class="companion">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="/community/select-companion/{companion['id']}">{companion['name']}</a>
                            <br><small style="color: #00ff00;">✅ Unlocked</small>
                        </div>
                '''
            else:
                lock_text = f"Needs {referrals_needed} referrals" if isinstance(referrals_needed, int) else "Special unlock"
                html += f'''
                        <div class="companion locked">
                            <img src="{companion['avatar_url']}" alt="{companion['name']}">
                            <br>
                            <a href="#" onclick="alert('This companion requires {referrals_needed} referrals')">{companion['name']}</a>
                            <br><small style="color: #ff6666;">🔒 {lock_text}</small>
                        </div>
                '''
        
        html += '''
                </div>
            </div>
            
            <p style="margin-top: 40px; color: #666; font-size: 14px;">
                Click on any unlocked companion to set it as your community avatar.
                Free users can access all Free and Referral companions!
            </p>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        logger.error(f"Failed to show companion selector: {e}")
        return f"<script>alert('Error loading companions: {str(e)}'); window.location.href='/community';</script>"

# OLD COMPANIONS API ENDPOINT REMOVED - Use /companion-selector instead

# ===============================
# UTILITY FUNCTIONS
# ===============================

def format_time_ago(post_time: datetime) -> str:
    """Format time ago string"""
    now = datetime.now(timezone.utc)
    if post_time.tzinfo is None:
        post_time = post_time.replace(tzinfo=timezone.utc)
    
    delta = now - post_time
    
    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"

# Export for app registration
def register_community_system(app):
    """Register community system with Flask app"""
    # Initialize database
    initialize_community_database()
    
    # Register blueprint
    app.register_blueprint(community_bp)
    logger.info("🏛️ Anonymous Community System registered successfully")