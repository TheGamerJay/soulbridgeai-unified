"""
SoulBridge AI - Relationship Profiles Routes
All relationship profile management endpoints extracted from backend/app.py
Flask Blueprint for modular architecture
"""
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template
from datetime import datetime
from .relationship_service import RelationshipService
from .profile_analyzer import ProfileAnalyzer

logger = logging.getLogger(__name__)

# Create Blueprint
relationship_bp = Blueprint('relationship_profiles', __name__, url_prefix='/relationship-profiles')

# Initialize services (to be configured in main app)
relationship_service = None
profile_analyzer = None

def init_relationship_routes(app, database, credits_manager, openai_client=None):
    """Initialize relationship profile routes with dependencies"""
    global relationship_service, profile_analyzer
    
    relationship_service = RelationshipService(database, credits_manager)
    profile_analyzer = ProfileAnalyzer(openai_client)
    
    # Blueprint already registered in main app - just initialize services
    logger.info("✅ Relationship profiles routes initialized")

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session and session.get('user_id') is not None

# ================================
# MAIN RELATIONSHIP PROFILES PAGE
# ================================

@relationship_bp.route("/")
def relationship_profiles_page():
    """Relationship profiles main page"""
    if not is_logged_in():
        return redirect("/login")
    
    # Check if user has relationship access (Silver/Gold tier, addon, or trial)
    user_plan = session.get('user_plan', 'bronze')
    user_addons = session.get('user_addons', [])
    trial_active = session.get('trial_active', False)
    
    if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
        return redirect("/subscription?feature=relationship")
    
    return render_template("relationship_profiles.html")

# ================================
# PROFILE MANAGEMENT API
# ================================

@relationship_bp.route("/api/add", methods=["POST"])
def add_relationship_profile():
    """Add a new relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not relationship_service:
            return jsonify({"success": False, "error": "Relationship service not available"}), 503
        
        # Check access and limits
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        access_check = relationship_service.check_access_and_limits(
            user_id, user_plan, trial_active, user_addons
        )
        
        if not access_check['has_access']:
            return jsonify({"success": False, "error": access_check['error']}), 403
        
        # Get profile data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Create profile
        result = relationship_service.create_profile(user_id, data)
        
        if result['success']:
            # For session-based storage (current implementation)
            if 'relationship_profiles' not in session:
                session['relationship_profiles'] = []
            
            # Convert internal profile format to session format for compatibility
            session_profile = {
                "id": result['profile']['id'],
                "name": result['profile']['name'],
                "type": result['profile']['type'],
                "connectionStrength": result['profile']['connection_strength'],
                "meetingFrequency": result['profile']['meeting_frequency'],
                "lastContact": result['profile']['last_contact'],
                "notes": result['profile']['notes'],
                "timestamp": result['profile']['created_at'],
                "user_id": user_id
            }
            
            session['relationship_profiles'].append(session_profile)
            session.modified = True
            
            logger.info(f"👥 Relationship profile added for user {session.get('user_email')}: {result['profile']['name']}")
            
            return jsonify({
                "success": True,
                "message": "Profile added successfully",
                "profile": session_profile
            })
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Relationship profile add error: {e}")
        return jsonify({"success": False, "error": "Failed to add profile. Your artistic time has been refunded."}), 500

@relationship_bp.route("/api/list", methods=["GET"])
def list_relationship_profiles():
    """Get user's relationship profiles"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get profiles from session (in production, get from database via service)
        profiles = session.get('relationship_profiles', [])
        
        return jsonify({
            "success": True,
            "profiles": profiles
        })
        
    except Exception as e:
        logger.error(f"Relationship profiles list error: {e}")
        return jsonify({"success": False, "error": "Failed to fetch profiles"}), 500

@relationship_bp.route("/api/delete/<profile_id>", methods=["DELETE"])
def delete_relationship_profile(profile_id):
    """Delete a relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get profiles from session
        profiles = session.get('relationship_profiles', [])
        
        # Find and remove the profile
        updated_profiles = [p for p in profiles if p.get('id') != profile_id]
        
        if len(updated_profiles) == len(profiles):
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        session['relationship_profiles'] = updated_profiles
        session.modified = True
        
        logger.info(f"🗑️ Relationship profile deleted for user {session.get('user_email')}: {profile_id}")
        
        return jsonify({
            "success": True,
            "message": "Profile deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Delete relationship profile error: {e}")
        return jsonify({"success": False, "error": "Failed to delete profile"}), 500

@relationship_bp.route("/api/update/<profile_id>", methods=["PUT"])
def update_relationship_profile(profile_id):
    """Update a relationship profile"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not relationship_service:
            return jsonify({"success": False, "error": "Relationship service not available"}), 503
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = session.get('user_id')
        
        # Update in session (for compatibility)
        profiles = session.get('relationship_profiles', [])
        updated_profiles = []
        profile_found = False
        
        for profile in profiles:
            if profile.get('id') == profile_id:
                # Update profile fields
                profile.update({
                    "name": data.get('name', profile.get('name')),
                    "type": data.get('type', profile.get('type')),
                    "connectionStrength": data.get('connectionStrength', profile.get('connectionStrength')),
                    "meetingFrequency": data.get('meetingFrequency', profile.get('meetingFrequency')),
                    "lastContact": data.get('lastContact', profile.get('lastContact')),
                    "notes": data.get('notes', profile.get('notes', ''))
                })
                profile_found = True
            
            updated_profiles.append(profile)
        
        if not profile_found:
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        session['relationship_profiles'] = updated_profiles
        session.modified = True
        
        logger.info(f"📝 Updated relationship profile {profile_id} for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Update relationship profile error: {e}")
        return jsonify({"success": False, "error": "Failed to update profile"}), 500

@relationship_bp.route("/api/get/<profile_id>", methods=["GET"])
def get_relationship_profile(profile_id):
    """Get specific relationship profile by ID"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Find profile in session
        profiles = session.get('relationship_profiles', [])
        
        for profile in profiles:
            if profile.get('id') == profile_id:
                return jsonify({
                    "success": True,
                    "profile": profile
                })
        
        return jsonify({"success": False, "error": "Profile not found"}), 404
        
    except Exception as e:
        logger.error(f"Get relationship profile error: {e}")
        return jsonify({"success": False, "error": "Failed to get profile"}), 500

# ================================
# PROFILE ANALYSIS API
# ================================

@relationship_bp.route("/api/analyze/<profile_id>", methods=["POST"])
def analyze_relationship_profile(profile_id):
    """Analyze a relationship profile using AI"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not profile_analyzer:
            return jsonify({"success": False, "error": "Analysis service not available"}), 503
        
        # Check access (Gold tier or trial required for AI analysis)
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['gold'] and not trial_active:
            return jsonify({"success": False, "error": "AI Analysis requires Gold tier or trial access"}), 403
        
        # Get analysis type from request
        data = request.get_json() or {}
        analysis_type = data.get('analysis_type', 'connection_health')
        
        # Find profile
        profiles = session.get('relationship_profiles', [])
        profile = None
        
        for p in profiles:
            if p.get('id') == profile_id:
                profile = p
                break
        
        if not profile:
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        # Perform analysis
        result = profile_analyzer.analyze_relationship(profile, analysis_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Analyze relationship profile error: {e}")
        return jsonify({"success": False, "error": "Failed to analyze profile"}), 500

@relationship_bp.route("/api/insights/<profile_id>", methods=["GET"])
def get_relationship_insights(profile_id):
    """Get quick insights about a relationship"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not profile_analyzer:
            return jsonify({"success": False, "error": "Analysis service not available"}), 503
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Find profile
        profiles = session.get('relationship_profiles', [])
        profile = None
        
        for p in profiles:
            if p.get('id') == profile_id:
                profile = p
                break
        
        if not profile:
            return jsonify({"success": False, "error": "Profile not found"}), 404
        
        # Get insights
        result = profile_analyzer.get_relationship_insights(profile)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get relationship insights error: {e}")
        return jsonify({"success": False, "error": "Failed to get insights"}), 500

@relationship_bp.route("/api/network-analysis", methods=["GET"])
def analyze_relationship_network():
    """Analyze user's entire relationship network"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not profile_analyzer:
            return jsonify({"success": False, "error": "Analysis service not available"}), 503
        
        # Check access (Gold tier or trial required for network analysis)
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['gold'] and not trial_active:
            return jsonify({"success": False, "error": "Network Analysis requires Gold tier or trial access"}), 403
        
        # Get all user profiles
        profiles = session.get('relationship_profiles', [])
        
        # Perform network analysis
        result = profile_analyzer.analyze_relationship_network(profiles)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Analyze relationship network error: {e}")
        return jsonify({"success": False, "error": "Failed to analyze network"}), 500

# ================================
# STATISTICS AND REPORTING API
# ================================

@relationship_bp.route("/api/statistics", methods=["GET"])
def get_relationship_statistics():
    """Get statistics about user's relationship profiles"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not relationship_service:
            return jsonify({"success": False, "error": "Relationship service not available"}), 503
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get statistics from session data (in production would use service)
        profiles = session.get('relationship_profiles', [])
        
        if not profiles:
            stats = {
                'total_profiles': 0,
                'by_type': {},
                'by_strength': {},
                'by_frequency': {},
                'recent_contacts': 0,
                'created_this_month': 0
            }
        else:
            # Calculate basic statistics
            stats = {
                'total_profiles': len(profiles),
                'by_type': {},
                'by_strength': {},
                'by_frequency': {},
                'recent_contacts': 0,
                'created_this_month': 0
            }
            
            current_month = datetime.now().strftime('%Y-%m')
            
            for profile in profiles:
                # Count by type
                profile_type = profile.get('type', 'other')
                stats['by_type'][profile_type] = stats['by_type'].get(profile_type, 0) + 1
                
                # Count by connection strength
                strength = profile.get('connectionStrength', 'moderate')
                stats['by_strength'][strength] = stats['by_strength'].get(strength, 0) + 1
                
                # Count by meeting frequency
                frequency = profile.get('meetingFrequency', 'rarely')
                stats['by_frequency'][frequency] = stats['by_frequency'].get(frequency, 0) + 1
                
                # Count created this month
                timestamp = profile.get('timestamp', '')
                if timestamp.startswith(current_month):
                    stats['created_this_month'] += 1
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Get relationship statistics error: {e}")
        return jsonify({"success": False, "error": "Failed to get statistics"}), 500

@relationship_bp.route("/api/search", methods=["GET"])
def search_relationship_profiles():
    """Search user's relationship profiles"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check access
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if user_plan not in ['silver', 'gold'] and not trial_active and 'relationship' not in user_addons:
            return jsonify({"success": False, "error": "Relationship Profiles requires Silver/Gold tier, addon, or trial"}), 403
        
        # Get search query
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({"success": False, "error": "Search query required"}), 400
        
        # Search in session profiles (in production would use service)
        profiles = session.get('relationship_profiles', [])
        
        if not query:
            matching_profiles = profiles
        else:
            query_lower = query.lower()
            matching_profiles = []
            
            for profile in profiles:
                # Search in name, notes, and type
                name = profile.get('name', '').lower()
                notes = profile.get('notes', '').lower()
                profile_type = profile.get('type', '').lower()
                
                if (query_lower in name or 
                    query_lower in notes or 
                    query_lower in profile_type):
                    matching_profiles.append(profile)
        
        return jsonify({
            "success": True,
            "profiles": matching_profiles,
            "query": query,
            "total_results": len(matching_profiles)
        })
        
    except Exception as e:
        logger.error(f"Search relationship profiles error: {e}")
        return jsonify({"success": False, "error": "Failed to search profiles"}), 500

# ================================
# UTILITY ENDPOINTS
# ================================

@relationship_bp.route("/api/options", methods=["GET"])
def get_relationship_options():
    """Get available options for relationship fields"""
    try:
        if not relationship_service:
            # Return hardcoded options if service not available
            options = {
                'types': ['romantic', 'family', 'friend', 'colleague', 'mentor', 'acquaintance', 'business', 'other'],
                'connection_strengths': ['very_weak', 'weak', 'moderate', 'strong', 'very_strong'],
                'meeting_frequencies': ['daily', 'weekly', 'bi_weekly', 'monthly', 'quarterly', 'bi_annually', 'annually', 'rarely', 'never']
            }
        else:
            options = {
                'types': relationship_service.get_relationship_types(),
                'connection_strengths': relationship_service.get_connection_strengths(),
                'meeting_frequencies': relationship_service.get_meeting_frequencies()
            }
        
        return jsonify({
            "success": True,
            "options": options
        })
        
    except Exception as e:
        logger.error(f"Get relationship options error: {e}")
        return jsonify({"success": False, "error": "Failed to get options"}), 500

@relationship_bp.route("/api/access-check", methods=["GET"])
def check_relationship_access():
    """Check user's access to relationship profiles"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        user_id = session.get('user_id')
        user_plan = session.get('user_plan', 'bronze')
        user_addons = session.get('user_addons', [])
        trial_active = session.get('trial_active', False)
        
        if relationship_service:
            access_result = relationship_service.check_access_and_limits(
                user_id, user_plan, trial_active, user_addons
            )
        else:
            # Fallback access check
            has_access = (user_plan in ['silver', 'gold'] or 
                         trial_active or 
                         'relationship' in user_addons)
            
            access_result = {
                'has_access': has_access,
                'error': 'Relationship Profiles requires Silver/Gold tier, addon, or trial' if not has_access else None
            }
        
        return jsonify({
            "success": True,
            "access": access_result
        })
        
    except Exception as e:
        logger.error(f"Check relationship access error: {e}")
        return jsonify({"success": False, "error": "Failed to check access"}), 500