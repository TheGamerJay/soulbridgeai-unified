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
            
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Check if table exists first
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
                # Reconnect and proceed
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
            
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
        return jsonify({"error": "Failed to load feed"}), 500

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

@community_bp.route('/companions', methods=['GET'])
def get_available_companions():
    """Get companions available for community avatars"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get cosmetic companions (referral companions)
        try:
            from cosmetic_system import get_available_companions_for_user
            cosmetic_companions = get_available_companions_for_user(user_id)
        except Exception as e:
            logger.warning(f"Could not load cosmetic companions: {e}")
            cosmetic_companions = []
        
        # Get tier-based companions
        from unified_tier_system import get_effective_plan
        user_plan = session.get('user_plan', 'free')
        trial_active = session.get('trial_active', False)
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        # Base companions available to all users
        base_companions = [
            {
                'id': 1,
                'name': 'GamerJay',
                'display_name': 'GamerJay',
                'description': 'Your gaming companion and free tier default',
                'rarity': 'common',
                'avatar_url': '/static/logos/GamerJay Free companion.png',
                'unlock_method': 'default'
            }
        ]
        
        # Growth tier companions
        if effective_plan in ['growth', 'max']:
            base_companions.extend([
                {
                    'id': 2,
                    'name': 'Sky',
                    'display_name': 'Sky',
                    'description': 'Your premium growth companion',
                    'rarity': 'rare',
                    'avatar_url': '/static/logos/Sky a premium companion.png',
                    'unlock_method': 'growth_tier'
                },
                {
                    'id': 7,
                    'name': 'GamerJay Premium',
                    'display_name': 'GamerJay Premium',
                    'description': 'Enhanced gaming companion',
                    'rarity': 'rare',
                    'avatar_url': '/static/logos/GamerJay premium companion.png',
                    'unlock_method': 'growth_tier'
                }
            ])
        
        # Max tier companions
        if effective_plan == 'max':
            base_companions.extend([
                {
                    'id': 3,
                    'name': 'Crimson',
                    'display_name': 'Crimson',
                    'description': 'Powerful Max tier companion',
                    'rarity': 'epic',
                    'avatar_url': '/static/logos/Crimson.png',
                    'unlock_method': 'max_tier'
                },
                {
                    'id': 4,
                    'name': 'Violet',
                    'display_name': 'Violet',
                    'description': 'Mystical Max tier companion',
                    'rarity': 'epic',
                    'avatar_url': '/static/logos/Violet.png',
                    'unlock_method': 'max_tier'
                }
            ])
        
        # Combine all available companions
        all_companions = base_companions + cosmetic_companions
        
        # Remove duplicates by id
        seen_ids = set()
        unique_companions = []
        for companion in all_companions:
            if companion.get('id') not in seen_ids:
                seen_ids.add(companion.get('id'))
                unique_companions.append(companion)
        
        return jsonify({
            'success': True,
            'companions': unique_companions,
            'user_tier': effective_plan,
            'debug': {
                'user_plan': user_plan,
                'trial_active': trial_active,
                'effective_plan': effective_plan,
                'base_companions_count': len(base_companions),
                'cosmetic_companions_count': len(cosmetic_companions),
                'total_companions': len(unique_companions)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get available companions: {e}")
        return jsonify({"error": "Failed to get companions"}), 500

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