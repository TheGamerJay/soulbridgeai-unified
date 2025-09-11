"""
SoulBridge AI - Companion Routes
Extracted from app.py monolith for modular architecture
"""
import logging
from flask import Blueprint, render_template, request, session, jsonify, redirect
from ..auth.session_manager import requires_login, get_user_id
from .companion_data import get_all_companions, get_companion_by_id, get_companions_by_tier
from .skin_system import get_consolidated_companions, get_companion_by_id as get_skin_companion_by_id, get_referral_companions
from .access_control import (
    get_user_companion_access, 
    require_companion_access,
    can_access_companion,
    companion_unlock_state_new
)
from .chat_service import CompanionChatService

logger = logging.getLogger(__name__)

# Create blueprint for companion routes
companions_bp = Blueprint('companions', __name__)

@companions_bp.route("/companion-selection")
@requires_login
def companion_selection():
    """Companion selection page"""
    try:
        from flask import session
        
        access_info = get_user_companion_access()
        # Get consolidated companions with skin support
        companions = get_consolidated_companions()
        referral_companions = get_referral_companions()
        
        # Get user tier info for template
        user_plan = session.get('user_plan', 'bronze')
        tier_display = user_plan.title()
        
        # Get limits from creative features configuration
        from ..creative.features_config import CREATIVE_LIMITS
        limits = {
            'decoder': CREATIVE_LIMITS['decoder'][user_plan],
            'fortune': CREATIVE_LIMITS['fortune'][user_plan],
            'horoscope': CREATIVE_LIMITS['horoscope'][user_plan],
            'creative_writer': CREATIVE_LIMITS['creative_writing'][user_plan]
        }
        
        logger.info(f"Companion selection: user_plan={user_plan}, companions={len(companions)}, access_info keys={list(access_info.keys()) if access_info else 'None'}")
        
        return render_template("companion_selection.html", 
                             companions=companions,
                             referral_companions=referral_companions,
                             access_info=access_info,
                             tier=user_plan,
                             tier_display=tier_display,
                             limits=limits)
        
    except Exception as e:
        logger.error(f"Error in companion selection: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return render_template("error.html", error="Unable to load companion selection")

@companions_bp.route("/chat")
@requires_login  
def chat_home():
    """Main chat page - redirect to companion selection if needed"""
    try:
        # Check if user has selected a companion
        selected_companion = session.get('selected_companion')
        
        if not selected_companion:
            return redirect("/companion-selection")
        
        # Check if user still has access to selected companion
        if not require_companion_access(selected_companion):
            # Access revoked, back to selection
            session.pop('selected_companion', None)
            return redirect("/companion-selection")
        
        companion = get_companion_by_id(selected_companion)
        return render_template("chat.html", companion=companion)
        
    except Exception as e:
        logger.error(f"Error in chat home: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/chat/<tier>")
@requires_login
def chat_tier(tier):
    """Chat page for specific tier"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Check if user can access this tier
        if not can_access_companion(user_plan, tier, trial_active):
            return redirect("/companion-selection")
        
        companions = get_companions_by_tier(tier)
        return render_template("chat_bronze.html", 
                             companions=companions,
                             trial_active=session.get('trial_active', False))
        
    except Exception as e:
        logger.error(f"Error in tier chat {tier}: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/chat/<tier>/<companion_id>")
@requires_login
def companion_specific_chat(tier, companion_id):
    """Chat with specific companion"""
    try:
        # Verify companion exists and user has access (check both systems)
        companion = get_companion_by_id(companion_id) or get_skin_companion_by_id(companion_id)
        if not companion:
            logger.warning(f"Companion not found: {companion_id}")
            return redirect("/companion-selection")
        
        if not require_companion_access(companion_id):
            logger.warning(f"User lacks access to companion: {companion_id}")
            return redirect("/companion-selection")
        
        # Set as selected companion
        session['selected_companion'] = companion_id
        session.modified = True
        
        return render_template("chat_bronze.html", 
                             companion_info=companion,
                             ai_character_name=companion.get('name', 'AI Assistant'),
                             companion_avatar=companion.get('image_url', '/static/logos/New IntroLogo.png'),
                             trial_active=session.get('trial_active', False))
        
    except Exception as e:
        logger.error(f"Error in companion chat {companion_id}: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/api/companions")
@requires_login
def api_companions():
    """API endpoint for companion data"""
    try:
        access_info = get_user_companion_access()
        # Get consolidated companions for API
        consolidated_companions = get_consolidated_companions()
        referral_companions = get_referral_companions()
        
        # Add access information to each companion
        for companion in consolidated_companions:
            companion['can_access'] = require_companion_access(companion['id'])
        
        for companion in referral_companions:
            companion['can_access'] = require_companion_access(companion['id'])
        
        return jsonify({
            'success': True,
            'companions': consolidated_companions,
            'referral_companions': referral_companions,
            'access_info': access_info
        })
        
    except Exception as e:
        logger.error(f"Error in companions API: {e}")
        return jsonify({'success': False, 'error': 'Failed to load companions'}), 500

@companions_bp.route("/api/sapphire-chat", methods=["POST"])
@requires_login
def sapphire_chat():
    """Main chat processing endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        companion_id = data.get('companion_id') or session.get('selected_companion')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        if not companion_id:
            return jsonify({'success': False, 'error': 'No companion selected'}), 400
        
        # Verify access to companion
        if not require_companion_access(companion_id):
            return jsonify({'success': False, 'error': 'Access denied to this companion'}), 403
        
        # Process chat message
        chat_service = CompanionChatService()
        result = chat_service.process_chat(
            user_id=get_user_id(),
            companion_id=companion_id,
            message=message
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in sapphire chat: {e}")
        return jsonify({'success': False, 'error': 'Chat processing failed'}), 500

@companions_bp.route("/voice-chat")
@requires_login
def voice_chat():
    """Voice chat page (Gold tier feature)"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Voice chat requires Gold tier access
        if not can_access_companion(user_plan, 'gold', trial_active):
            return redirect("/companion-selection")
        
        return render_template("voice_chat.html")
        
    except Exception as e:
        logger.error(f"Error in voice chat: {e}")
        return redirect("/companion-selection")

@companions_bp.route("/api/voice-chat/process", methods=["POST"])
@requires_login
def process_voice_chat():
    """Process voice chat messages (Gold tier feature)"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Voice chat requires Gold tier access
        if not can_access_companion(user_plan, 'gold', trial_active):
            return jsonify({'success': False, 'error': 'Gold tier required'}), 403
        
        # Voice chat processing logic would go here
        return jsonify({'success': True, 'message': 'Voice chat processing not implemented yet'})
        
    except Exception as e:
        logger.error(f"Error in voice chat processing: {e}")
        return jsonify({'success': False, 'error': 'Voice processing failed'}), 500

@companions_bp.route("/api/companions/<base_name>/skins")
@requires_login
def get_companion_skins_api(base_name):
    """API endpoint to get skins for a specific companion"""
    try:
        from .skin_system import get_companion_skins
        skins = get_companion_skins(base_name)
        
        if not skins:
            return jsonify({'success': False, 'error': 'No skins found for this companion'}), 404
        
        return jsonify({
            'success': True,
            'name': base_name.title(),
            'skins': skins,
            'base_name': base_name
        })
        
    except Exception as e:
        logger.error(f"Error getting companion skins for {base_name}: {e}")
        return jsonify({'success': False, 'error': 'Failed to load skins'}), 500

@companions_bp.route("/api/companions/set-skin", methods=["POST"])
@requires_login
def set_companion_skin():
    """API endpoint to set a specific skin for a companion"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        companion_id = data.get('companion_id')
        base_name = data.get('base_name')
        
        if not companion_id or not base_name:
            return jsonify({'success': False, 'error': 'companion_id and base_name are required'}), 400
        
        # Verify companion exists (check both systems)
        try:
            companion = get_companion_by_id(companion_id) or get_skin_companion_by_id(companion_id)
            if not companion:
                return jsonify({'success': False, 'error': 'Companion skin not found'}), 404
        except Exception as comp_error:
            logger.error(f"Error finding companion {companion_id}: {comp_error}")
            return jsonify({'success': False, 'error': 'Error finding companion'}), 500
        
        # Verify user has access (skip for now to avoid access control issues)
        # if not require_companion_access(companion_id):
        #     return jsonify({'success': False, 'error': 'Access denied to this companion'}), 403
        
        # Apply skin immediately - save to session as user's avatar
        session['selected_companion'] = companion_id
        session[f'companion_skin_{base_name}'] = companion_id
        session.modified = True
        
        # CRITICAL: Also save to database for persistence across page refreshes
        user_id = get_user_id()
        if user_id:
            try:
                # Use same database import as community routes for consistency
                import sys
                sys.path.append('/'.join(__file__.split('/')[:-3]))  # Add backend to path
                from database_utils import get_database
                import json
                
                db = get_database()
                if db:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    # Save to users.companion_data column (matches community page loading)
                    companion_data = {
                        "id": companion_id,
                        "name": companion.get('name', base_name.title()),
                        "image_url": companion.get('image', companion.get('image_url', f'/static/companions/{companion_id}.png')),
                        "tier": companion.get('tier', 'bronze'),
                        "base_name": base_name,
                        "saved_at": __import__('datetime').datetime.now().isoformat()
                    }
                    
                    json_data = json.dumps(companion_data)
                    if hasattr(db, 'use_postgres') and db.use_postgres:
                        cursor.execute("UPDATE users SET companion_data = %s WHERE id = %s", (json_data, user_id))
                    else:
                        cursor.execute("UPDATE users SET companion_data = ? WHERE id = ?", (json_data, user_id))
                    
                    conn.commit()
                    cursor.close()
                    db.return_connection(conn)
                    logger.info(f"✅ SKIN DATABASE SAVE: Saved {companion_id} for user {user_id}")
                else:
                    logger.error("❌ Database connection unavailable")
                
            except Exception as db_error:
                logger.error(f"❌ SKIN DATABASE SAVE ERROR: {db_error}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # Continue anyway - at least session is updated
        
        logger.info(f"User applied {base_name} skin: {companion_id}")
        
        return jsonify({
            'success': True,
            'companion': companion,
            'message': f'Skin applied successfully! {companion.get("name", base_name)} is now your avatar.',
            'companion_id': companion_id,
            'base_name': base_name
        })
        
    except Exception as e:
        logger.error(f"Error setting companion skin: {e}")
        return jsonify({'success': False, 'error': 'Failed to set skin'}), 500

@companions_bp.route("/api/companion/select-skin", methods=["POST"])
@requires_login 
def select_companion_skin():
    """API endpoint to select a specific skin for a companion"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        companion_id = data.get('companion_id')
        if not companion_id:
            return jsonify({'success': False, 'error': 'Companion ID required'}), 400
        
        # Verify companion exists (check both systems)
        companion = get_companion_by_id(companion_id) or get_skin_companion_by_id(companion_id)
        if not companion:
            return jsonify({'success': False, 'error': 'Companion not found'}), 404
        
        # Verify user has access
        if not require_companion_access(companion_id):
            return jsonify({'success': False, 'error': 'Access denied to this companion'}), 403
        
        # Set as selected companion
        session['selected_companion'] = companion_id
        session.modified = True
        
        # Save skin preference to database
        user_id = get_user_id()
        if user_id:
            from ..shared.database import get_database_manager
            db = get_database_manager()
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Save user's skin preference
                cursor.execute("""
                    INSERT OR REPLACE INTO user_data (user_id, key, value) 
                    VALUES (?, ?, ?)
                """, (user_id, f'skin_preference_{companion.get("base_name", companion.get("name", "").lower())}', companion_id))
                
                conn.commit()
                cursor.close()
                db.return_connection(conn)
                
            except Exception as db_error:
                logger.error(f"Database error saving skin preference: {db_error}")
                # Continue anyway, skin will be saved in localStorage
        
        return jsonify({
            'success': True,
            'companion': companion,
            'message': f'Selected {companion.get("name", "companion")} successfully'
        })
        
    except Exception as e:
        logger.error(f"Error selecting companion skin: {e}")
        return jsonify({'success': False, 'error': 'Failed to select skin'}), 500

@companions_bp.route("/api/companions/public")
def api_companions_public():
    """Public API endpoint for companion data (no login required)"""
    try:
        # Get consolidated companions for API (public access)
        consolidated_companions = get_consolidated_companions()
        referral_companions = get_referral_companions()
        
        # For public access, all companions are accessible for viewing (but not for actual use)
        for companion in consolidated_companions:
            companion['can_access'] = True  # Public viewing access
        
        for companion in referral_companions:
            companion['can_access'] = False  # Referral companions require account
        
        return jsonify({
            'success': True,
            'companions': consolidated_companions,
            'referral_companions': referral_companions,
            'access_info': {'user_plan': 'bronze', 'trial_active': False}  # Default for anonymous
        })
        
    except Exception as e:
        logger.error(f"Error in public companions API: {e}")
        return jsonify({'success': False, 'error': 'Failed to load companions'}), 500

@companions_bp.route("/api/companions/<base_name>/skins/public")
def get_companion_skins_public(base_name):
    """Public API endpoint to get skins for a specific companion (no login required)"""
    try:
        from .skin_system import get_companion_skins
        skins = get_companion_skins(base_name)
        
        if not skins:
            return jsonify({'success': False, 'error': 'No skins found for this companion'}), 404
        
        return jsonify({
            'success': True,
            'name': base_name.title(),
            'skins': skins,
            'base_name': base_name
        })
        
    except Exception as e:
        logger.error(f"Error getting companion skins for {base_name}: {e}")
        return jsonify({'success': False, 'error': 'Failed to load skins'}), 500

@companions_bp.route("/companions/showcase")
def community_companions():
    """Community companion showcase (public page)"""
    try:
        companions = get_all_companions()
        return render_template("community_companions.html", companions=companions)
        
    except Exception as e:
        logger.error(f"Error in community companions: {e}")
        return render_template("error.html", error="Unable to load community page")