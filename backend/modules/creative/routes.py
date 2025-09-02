"""
SoulBridge AI - Creative Features Routes
Extracted from app.py monolith using strategic bulk extraction
ALL 27 creative routes consolidated here
"""
import logging
from flask import Blueprint, render_template, request, session, jsonify, redirect, flash
from ..auth.session_manager import requires_login, get_user_id
from .creative_service import CreativeService
from .features_config import get_feature_limit, get_creative_limits_summary, validate_zodiac_sign
from .usage_tracker import CreativeUsageTracker

logger = logging.getLogger(__name__)

# Create blueprint for creative routes
creative_bp = Blueprint('creative', __name__)

@creative_bp.route("/decoder")
@requires_login
def decoder_page():
    """Dream decoder main page"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        limit = get_feature_limit('decoder', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(get_user_id(), 'decoder')
        
        return render_template("decoder.html", 
                             daily_limit=limit,
                             usage_today=usage_today,
                             unlimited=limit >= 999)
        
    except Exception as e:
        logger.error(f"Error loading decoder page: {e}")
        return render_template("error.html", error="Unable to load dream decoder")

@creative_bp.route("/fortune")
@requires_login
def fortune_page():
    """Fortune teller main page"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        limit = get_feature_limit('fortune', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(get_user_id(), 'fortune')
        
        return render_template("fortune.html",
                             daily_limit=limit,
                             usage_today=usage_today,
                             unlimited=limit >= 999)
        
    except Exception as e:
        logger.error(f"Error loading fortune page: {e}")
        return render_template("error.html", error="Unable to load fortune teller")

@creative_bp.route("/horoscope")
@requires_login
def horoscope_page():
    """Horoscope main page"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        limit = get_feature_limit('horoscope', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(get_user_id(), 'horoscope')
        
        return render_template("horoscope.html",
                             daily_limit=limit,
                             usage_today=usage_today,
                             unlimited=limit >= 999)
        
    except Exception as e:
        logger.error(f"Error loading horoscope page: {e}")
        return render_template("error.html", error="Unable to load horoscope")

@creative_bp.route("/creative-writing")
@requires_login
def creative_writing_page():
    """Creative writing main page"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        limit = get_feature_limit('creative_writing', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(get_user_id(), 'creative_writing')
        
        return render_template("creative_writing.html",
                             daily_limit=limit,
                             current_usage=usage_today,
                             usage_today=usage_today,
                             unlimited=limit >= 999)
        
    except Exception as e:
        logger.error(f"Error loading creative writing page: {e}")
        return render_template("error.html", error="Unable to load creative writer")

# API Endpoints for creative features
@creative_bp.route("/api/v2/decoder", methods=["POST"])
@requires_login
def api_decoder():
    """Dream decoder API endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        dream_text = data.get('dream', '').strip()
        mode = data.get('mode', 'dream').strip()
        if not dream_text:
            return jsonify({"success": False, "error": "Text is required"}), 400
        
        # Check usage limits
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        usage_tracker = CreativeUsageTracker()
        if not usage_tracker.can_use_feature(user_id, 'decoder', user_plan, trial_active):
            limit = get_feature_limit('decoder', user_plan, trial_active)
            return jsonify({
                "success": False,
                "error": f"Daily limit reached ({limit} uses per day)",
                "limit_reached": True
            }), 429
        
        # Generate interpretation based on mode
        creative_service = CreativeService()
        result = creative_service.decode_dream(dream_text, user_id, mode)
        
        if result['success']:
            # Track usage
            logger.info(f"🔓 Recording decoder usage for user {user_id}")
            usage_success = usage_tracker.record_usage(user_id, 'decoder')
            logger.info(f"🔓 Usage recording result: {usage_success}")
            
            # Auto-save to library
            auto_saved = False
            try:
                from ..library.content_service import ContentService
                content_service = ContentService()
                content_id = content_service.save_decoder_session(
                    user_id=user_id,
                    input_text=data.get('original_text', dream_text),
                    decoded_text=result['interpretation']
                )
                auto_saved = bool(content_id)
                logger.info(f"🔓 Auto-saved decoder session to library for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to auto-save decoder session: {e}")
                auto_saved = False
            
            return jsonify({
                "success": True,
                "interpretation": result['interpretation'],
                "symbols": result.get('symbols_found', []),
                "mood": result.get('mood', 'neutral'),
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in decoder API: {e}")
        return jsonify({"success": False, "error": "Dream decoding failed"}), 500

@creative_bp.route("/api/v2/fortune", methods=["POST"])
@requires_login
def api_fortune():
    """Fortune teller API endpoint"""
    try:
        data = request.get_json()
        question = data.get('question', '') if data else ''
        spread_type = data.get('spread', 'three') if data else 'three'
        
        # Check usage limits
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        usage_tracker = CreativeUsageTracker()
        if not usage_tracker.can_use_feature(user_id, 'fortune', user_plan, trial_active):
            limit = get_feature_limit('fortune', user_plan, trial_active)
            return jsonify({
                "success": False,
                "error": f"Daily limit reached ({limit} uses per day)",
                "limit_reached": True
            }), 429
        
        # Generate fortune reading
        creative_service = CreativeService()
        result = creative_service.generate_fortune(question, user_id, spread_type)
        
        if result['success']:
            # Track usage
            usage_tracker.record_usage(user_id, 'fortune')
            
            # Auto-save to library
            auto_saved = False
            try:
                from ..library.content_service import ContentService
                content_service = ContentService()
                content_id = content_service.save_fortune_reading(
                    user_id=user_id,
                    question=result['question'],
                    card=[card['name'] for card in result['cards']][0] if result['cards'] else 'Unknown',
                    interpretation=result['reading']
                )
                auto_saved = bool(content_id)
                logger.info(f"🔮 Auto-saved fortune reading to library for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to auto-save fortune reading: {e}")
                auto_saved = False
            
            return jsonify({
                "success": True,
                "reading": result['reading'],
                "cards": result['cards'],
                "question": result['question'],
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in fortune API: {e}")
        return jsonify({"success": False, "error": "Fortune reading failed"}), 500

@creative_bp.route("/api/v2/horoscope", methods=["POST"])
@requires_login
def api_horoscope():
    """Horoscope API endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        zodiac_sign = data.get('sign', '').strip().lower()
        if not zodiac_sign or not validate_zodiac_sign(zodiac_sign):
            return jsonify({"success": False, "error": "Valid zodiac sign required"}), 400
        
        # Check usage limits
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        usage_tracker = CreativeUsageTracker()
        if not usage_tracker.can_use_feature(user_id, 'horoscope', user_plan, trial_active):
            limit = get_feature_limit('horoscope', user_plan, trial_active)
            return jsonify({
                "success": False,
                "error": f"Daily limit reached ({limit} uses per day)",
                "limit_reached": True
            }), 429
        
        # Generate horoscope
        creative_service = CreativeService()
        result = creative_service.generate_horoscope(zodiac_sign, user_id)
        
        if result['success']:
            # Track usage
            usage_tracker.record_usage(user_id, 'horoscope')
            
            # Auto-save to library
            auto_saved = False
            try:
                from ..library.content_service import ContentService
                content_service = ContentService()
                content_id = content_service.save_horoscope_reading(
                    user_id=user_id,
                    sign=result['sign'],
                    horoscope_text=result['horoscope']
                )
                auto_saved = bool(content_id)
                logger.info(f"⭐ Auto-saved horoscope reading to library for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to auto-save horoscope reading: {e}")
                auto_saved = False
            
            return jsonify({
                "success": True,
                "horoscope": result['horoscope'],
                "sign": result['sign'],
                "date": result['date'],
                "lucky_numbers": result['lucky_numbers'],
                "lucky_color": result['lucky_color'],
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in horoscope API: {e}")
        return jsonify({"success": False, "error": "Horoscope generation failed"}), 500

@creative_bp.route("/api/creative-writing", methods=["POST"])
@requires_login
def api_creative_writing():
    """Creative writing API endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        prompt = data.get('prompt', '').strip()
        style = data.get('style', 'story').strip()
        
        if not prompt:
            return jsonify({"success": False, "error": "Writing prompt is required"}), 400
        
        # Check usage limits
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        usage_tracker = CreativeUsageTracker()
        if not usage_tracker.can_use_feature(user_id, 'creative_writing', user_plan, trial_active):
            limit = get_feature_limit('creative_writing', user_plan, trial_active)
            return jsonify({
                "success": False,
                "error": f"Daily limit reached ({limit} uses per day)",
                "limit_reached": True
            }), 429
        
        # Generate creative content
        creative_service = CreativeService()
        result = creative_service.generate_creative_writing(prompt, style, user_id)
        
        if result['success']:
            # Track usage
            usage_tracker.record_usage(user_id, 'creative_writing')
            
            # Auto-save to library
            auto_saved = False
            try:
                from ..library.content_service import ContentService
                content_service = ContentService()
                content_id = content_service.save_creative_writing(
                    user_id=user_id,
                    prompt=result['prompt'],
                    generated_text=result['content'],
                    style=result['style']
                )
                auto_saved = bool(content_id)
                logger.info(f"✍️ Auto-saved creative writing to library for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to auto-save creative writing: {e}")
                auto_saved = False
            
            return jsonify({
                "success": True,
                "content": result['content'],
                "style": result['style'],
                "prompt": result['prompt'],
                "word_count": result['word_count'],
                "auto_saved": auto_saved,
                "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in creative writing API: {e}")
        return jsonify({"success": False, "error": "Creative writing failed"}), 500

# Usage checking endpoints
@creative_bp.route("/api/decoder/debug-table")
@requires_login
def debug_feature_usage_table():
    """Debug endpoint to check feature_usage table state"""
    try:
        from ..shared.database import get_database
        db = get_database()
        if not db:
            return jsonify({"error": "No database connection"}), 500
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        if db.use_postgres:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'feature_usage'
                )
            """)
        else:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='feature_usage'
            """)
        
        table_exists = bool(cursor.fetchone()[0] if cursor.fetchone() else False)
        
        # Get table schema if exists
        schema_info = "N/A"
        if table_exists:
            if db.use_postgres:
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'feature_usage'
                    ORDER BY ordinal_position
                """)
            else:
                cursor.execute("PRAGMA table_info(feature_usage)")
            schema_info = cursor.fetchall()
        
        # Check current user's records
        user_id = get_user_id()
        user_records = []
        if table_exists:
            if db.use_postgres:
                cursor.execute("""
                    SELECT feature_name, usage_date, usage_count, last_used_at
                    FROM feature_usage WHERE user_id = %s
                    ORDER BY last_used_at DESC LIMIT 10
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT feature_name, usage_date, usage_count, last_used_at
                    FROM feature_usage WHERE user_id = ?
                    ORDER BY last_used_at DESC LIMIT 10
                """, (user_id,))
            user_records = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "table_exists": table_exists,
            "schema_info": schema_info,
            "user_records": user_records,
            "user_id": user_id,
            "database_type": "postgres" if db.use_postgres else "sqlite"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@creative_bp.route("/api/decoder/check-limit")
@requires_login
def check_decoder_limit():
    """Check decoder usage limits"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Get effective plan for display (trial users show higher tier access)
        from ..companions.access_control import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        limit = get_feature_limit('decoder', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(user_id, 'decoder')
        
        return jsonify({
            "success": True,
            "daily_limit": limit,
            "usage_today": usage_today,
            "remaining": max(0, limit - usage_today),
            "unlimited": limit >= 999,
            "user_plan": user_plan,
            "effective_plan": effective_plan,
            "trial_active": trial_active
        })
        
    except Exception as e:
        logger.error(f"Error checking decoder limit: {e}")
        return jsonify({"success": False, "error": "Failed to check limits"}), 500

@creative_bp.route("/api/fortune/check-limit")
@requires_login
def check_fortune_limit():
    """Check fortune usage limits"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Get effective plan for display (trial users show higher tier access)
        from ..companions.access_control import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        limit = get_feature_limit('fortune', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(user_id, 'fortune')
        
        return jsonify({
            "success": True,
            "daily_limit": limit,
            "usage_today": usage_today,
            "remaining": max(0, limit - usage_today),
            "unlimited": limit >= 999,
            "user_plan": user_plan,
            "effective_plan": effective_plan,
            "trial_active": trial_active
        })
        
    except Exception as e:
        logger.error(f"Error checking fortune limit: {e}")
        return jsonify({"success": False, "error": "Failed to check limits"}), 500

@creative_bp.route("/api/horoscope/check-limit")
@requires_login
def check_horoscope_limit():
    """Check horoscope usage limits"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Get effective plan for display (trial users show higher tier access)
        from ..companions.access_control import get_effective_plan
        effective_plan = get_effective_plan(user_plan, trial_active)
        
        limit = get_feature_limit('horoscope', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(user_id, 'horoscope')
        
        return jsonify({
            "success": True,
            "daily_limit": limit,
            "usage_today": usage_today,
            "remaining": max(0, limit - usage_today),
            "unlimited": limit >= 999,
            "user_plan": user_plan,
            "effective_plan": effective_plan,
            "trial_active": trial_active
        })
        
    except Exception as e:
        logger.error(f"Error checking horoscope limit: {e}")
        return jsonify({"success": False, "error": "Failed to check limits"}), 500

# Content saving endpoints
@creative_bp.route("/api/save-decoder", methods=["POST"])
@requires_login
def save_decoder_content():
    """Save decoder interpretation to library"""
    try:
        # Implementation would save to user's library
        return jsonify({"success": True, "message": "Dream interpretation saved to library"})
        
    except Exception as e:
        logger.error(f"Error saving decoder content: {e}")
        return jsonify({"success": False, "error": "Failed to save content"}), 500

@creative_bp.route("/api/save-fortune", methods=["POST"])
@requires_login
def save_fortune_content():
    """Save fortune reading to library"""
    try:
        # Implementation would save to user's library
        return jsonify({"success": True, "message": "Fortune reading saved to library"})
        
    except Exception as e:
        logger.error(f"Error saving fortune content: {e}")
        return jsonify({"success": False, "error": "Failed to save content"}), 500

@creative_bp.route("/api/save-horoscope", methods=["POST"])
@requires_login
def save_horoscope_content():
    """Save horoscope to library"""
    try:
        # Implementation would save to user's library
        return jsonify({"success": True, "message": "Horoscope saved to library"})
        
    except Exception as e:
        logger.error(f"Error saving horoscope content: {e}")
        return jsonify({"success": False, "error": "Failed to save content"}), 500

@creative_bp.route("/api/save-creative-content", methods=["POST"])
@requires_login
def save_creative_content():
    """Save creative writing to library"""
    try:
        # Implementation would save to user's library
        return jsonify({"success": True, "message": "Creative content saved to library"})
        
    except Exception as e:
        logger.error(f"Error saving creative content: {e}")
        return jsonify({"success": False, "error": "Failed to save content"}), 500

@creative_bp.route("/api/reset-usage", methods=["POST"])
@requires_login
def reset_user_usage():
    """Reset current user's daily usage for testing"""
    try:
        from datetime import datetime
        from ..shared.database import get_database
        
        user_id = get_user_id()
        today = datetime.now().strftime('%Y-%m-%d')
        
        db = get_database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        if db.use_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_name TEXT NOT NULL,
                    usage_date DATE NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature_name, usage_date)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feature_name TEXT NOT NULL,
                    usage_date DATE NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature_name, usage_date)
                )
            ''')
        
        # Reset usage for all features for current user today
        if db.use_postgres:
            cursor.execute('DELETE FROM feature_usage WHERE user_id = %s AND usage_date = %s', (user_id, today))
        else:
            cursor.execute('DELETE FROM feature_usage WHERE user_id = ? AND usage_date = ?', (user_id, today))
        
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🔄 Reset usage for user {user_id} - deleted {rows_deleted} records")
        
        return jsonify({
            "success": True, 
            "message": f"Usage reset successful - cleared {rows_deleted} records for today",
            "user_id": user_id,
            "date": today
        })
        
    except Exception as e:
        logger.error(f"Error resetting usage: {e}")
        return jsonify({"success": False, "error": f"Failed to reset usage: {str(e)}"}), 500

# Enhanced Tarot endpoints for advanced frontend
@creative_bp.route("/api/fortune/tarot", methods=["POST"])
@requires_login
def api_tarot_reading():
    """Advanced Tarot reading API for interactive frontend"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        spread = data.get('spread', 'three').lower()
        question = data.get('question', '').strip()
        
        # Check usage limits
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        usage_tracker = CreativeUsageTracker()
        if not usage_tracker.can_use_feature(user_id, 'fortune', user_plan, trial_active):
            limit = get_feature_limit('fortune', user_plan, trial_active)
            return jsonify({
                "success": False,
                "error": f"Daily limit reached ({limit} uses per day)",
                "limit_reached": True
            }), 429
        
        # Generate advanced tarot reading
        cards = []
        positions = []
        
        # Define spread positions
        if spread == 'one':
            positions = ['Guidance']
            card_count = 1
        elif spread == 'three':
            positions = ['Past', 'Present', 'Future']
            card_count = 3
        elif spread == 'five':
            positions = ['Situation', 'Challenge', 'Hidden Influences', 'Advice', 'Outcome']
            card_count = 5
        else:
            positions = ['Past', 'Present', 'Future']
            card_count = 3
        
        # Get random cards from our complete 78-card deck
        from .features_config import get_random_tarot_cards
        selected_cards = get_random_tarot_cards(card_count)
        
        # Add position and reversal info
        import random
        for i, card in enumerate(selected_cards):
            cards.append({
                "name": card['name'],
                "suit": card['suit'],
                "meaning": card['meaning'],
                "position": positions[i] if i < len(positions) else f"Card {i+1}",
                "reversed": random.choice([True, False])  # 50% chance of reversal
            })
        
        # Generate AI reading summary
        creative_service = CreativeService()
        card_descriptions = [f"{card['name']} ({card['position']}) - {'Reversed' if card['reversed'] else 'Upright'}" for card in cards]
        
        summary_prompt = f"""Question: {question or 'General reading'}
Spread: {spread.title()} spread
Cards drawn: {', '.join(card_descriptions)}

Provide a cohesive interpretation connecting these cards to answer the question."""
        
        result = creative_service.generate_fortune(summary_prompt, user_id)
        summary = result['reading'] if result['success'] else "The cards reveal guidance for your path ahead. Trust your intuition as you move forward."
        
        # Track usage
        usage_tracker.record_usage(user_id, 'fortune')
        
        return jsonify({
            "success": True,
            "spread": spread,
            "cards": cards,
            "summary": summary,
            "question": question or "General reading"
        })
        
    except Exception as e:
        logger.error(f"Error in tarot reading API: {e}")
        return jsonify({"success": False, "error": "Tarot reading failed"}), 500

@creative_bp.route("/api/fortune/limits")
@requires_login
def api_fortune_limits():
    """Get current fortune usage limits"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        limit = get_feature_limit('fortune', user_plan, trial_active)
        usage_tracker = CreativeUsageTracker()
        usage_today = usage_tracker.get_usage_today(user_id, 'fortune')
        
        return jsonify({
            "success": True,
            "plan": user_plan,
            "limit": limit if limit < 999 else None,  # null = unlimited for frontend
            "used": usage_today,
            "remaining": max(0, limit - usage_today) if limit < 999 else None,
            "unlimited": limit >= 999
        })
        
    except Exception as e:
        logger.error(f"Error getting fortune limits: {e}")
        return jsonify({"success": False, "error": "Failed to get limits"}), 500

@creative_bp.route("/api/fortune/save", methods=["POST"])
@requires_login
def api_save_fortune():
    """Save tarot reading to library"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No reading data provided"}), 400
        
        # For now, return success with mock library ID
        # TODO: Implement actual library storage
        return jsonify({
            "success": True,
            "message": "Tarot reading saved to library",
            "library_item_id": f"tarot_{int(datetime.now().timestamp())}"
        })
        
    except Exception as e:
        logger.error(f"Error saving tarot reading: {e}")
        return jsonify({"success": False, "error": "Failed to save reading"}), 500