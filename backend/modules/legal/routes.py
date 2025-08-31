"""
SoulBridge AI - Legal Routes
Flask Blueprint for all legal/compliance-related endpoints
Extracted from backend/app.py
"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect
from database_utils import get_database
from .terms_service import TermsService
from .privacy_manager import PrivacyManager
from .legal_documents import LegalDocuments

logger = logging.getLogger(__name__)

# Create Blueprint
legal_bp = Blueprint('legal', __name__)

# Initialize services (will be set by the main app)
terms_service = None
privacy_manager = None
legal_documents = None

def init_legal_services(database=None):
    """Initialize legal services with dependencies"""
    global terms_service, privacy_manager, legal_documents
    
    try:
        terms_service = TermsService(database)
        privacy_manager = PrivacyManager(database)
        legal_documents = LegalDocuments()
        
        # Ensure database schemas exist
        if database:
            terms_service.ensure_database_schema()
            privacy_manager.ensure_database_schema()
        
        logger.info("⚖️ Legal services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize legal services: {e}")
        return False

def is_logged_in():
    """Check if user is logged in"""
    return session.get('logged_in', False) and session.get('user_id') is not None

def has_accepted_terms():
    """Check if user has accepted terms (with emergency auto-accept)"""
    # EMERGENCY DISABLE: Always return True to prevent redirect loops
    if is_logged_in() and session.get('user_id'):
        session['terms_accepted'] = True
        session.modified = True
    return True

def load_terms_acceptance_status(user_id: int):
    """Load terms acceptance status from database into session"""
    try:
        if not terms_service:
            logger.warning("Terms service unavailable when loading status")
            return
        
        status = terms_service.get_terms_status(user_id)
        
        # Update session with database values
        session['terms_accepted'] = status.get('accepted', False)
        session['terms_accepted_at'] = status.get('accepted_at')
        session['terms_version'] = status.get('version', 'v1.0')
        session['terms_language'] = status.get('language', 'en')
        session.modified = True
        
        logger.info(f"📋 Terms status loaded for user {user_id}: accepted={status.get('accepted')}")
        
    except Exception as e:
        logger.error(f"Failed to load terms status for user {user_id}: {e}")
        # Set safe defaults
        session['terms_accepted'] = False
        session['terms_accepted_at'] = None
        session['terms_version'] = 'v1.0'
        session['terms_language'] = 'en'
        session.modified = True

# =============================================================================
# LEGAL DOCUMENT PAGES
# =============================================================================

@legal_bp.route("/terms")
def terms_page():
    """Terms of service and privacy policy page"""
    try:
        language = request.args.get('lang', 'en')
        
        if legal_documents:
            # Get combined legal document
            doc_result = legal_documents.get_combined_legal_document(language)
            if doc_result['success']:
                return render_template("terms.html", 
                                       legal_document=doc_result['document'],
                                       language=language)
        
        # Fallback to simple terms content
        return render_template("terms.html", fallback_mode=True)
        
    except Exception as e:
        logger.error(f"Terms page error: {e}")
        # Emergency fallback
        return f"""
        <html>
        <head><title>Terms & Privacy - SoulBridge AI</title></head>
        <body style="font-family: Arial; padding: 20px; background: #0f172a; color: #e2e8f0;">
            <h1 style="color: #22d3ee;">Terms of Service & Privacy Policy</h1>
            <h2>Terms of Service</h2>
            <p>By using SoulBridge AI, you agree to use our service responsibly and in accordance with applicable laws.</p>
            <h2>Privacy Policy</h2>
            <p>We respect your privacy. Your conversations are private and we don't share your personal data with third parties.</p>
            <a href="/register" style="color: #22d3ee;">← Back to Registration</a>
        </body>
        </html>
        """

@legal_bp.route("/terms-acceptance")
def terms_acceptance_page():
    """Terms acceptance page - required for new users"""
    try:
        if not is_logged_in():
            return redirect("/login")
        
        # Check if user already accepted terms
        if has_accepted_terms():
            logger.info(f"Terms already accepted by {session.get('user_email')}, redirecting to intro")
            return redirect("/intro")
        
        # Get user's preferred language
        language = session.get('language_preference', 'en')
        
        # Get legal documents for acceptance
        legal_content = None
        if legal_documents:
            doc_result = legal_documents.get_combined_legal_document(language)
            if doc_result['success']:
                legal_content = doc_result['document']
        
        return render_template("terms_acceptance.html", 
                               legal_content=legal_content,
                               language=language)
        
    except Exception as e:
        logger.error(f"Terms acceptance page error: {e}")
        return redirect("/login")

@legal_bp.route("/privacy")
def privacy_page():
    """Standalone privacy policy page"""
    try:
        language = request.args.get('lang', 'en')
        
        if legal_documents:
            privacy_result = legal_documents.get_privacy_policy(language)
            if privacy_result['success']:
                return render_template("privacy.html", 
                                       privacy_document=privacy_result['document'],
                                       language=language)
        
        return render_template("privacy.html", fallback_mode=True)
        
    except Exception as e:
        logger.error(f"Privacy page error: {e}")
        return redirect("/terms")

@legal_bp.route("/ai-disclosure")
def ai_disclosure_page():
    """AI service disclosure page"""
    try:
        language = request.args.get('lang', 'en')
        
        if legal_documents:
            ai_result = legal_documents.get_ai_disclosure(language)
            if ai_result['success']:
                return render_template("ai_disclosure.html",
                                       ai_document=ai_result['document'],
                                       language=language)
        
        return render_template("ai_disclosure.html", fallback_mode=True)
        
    except Exception as e:
        logger.error(f"AI disclosure page error: {e}")
        return redirect("/terms")

# =============================================================================
# TERMS API ENDPOINTS
# =============================================================================

@legal_bp.route('/api/accept-terms', methods=['POST'])
def accept_terms():
    """Accept terms and conditions"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Login required"}), 401
        
        if not terms_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        user_id = session.get('user_id')
        language = data.get('language', session.get('language_preference', 'en'))
        
        # Validate and accept terms
        accept_result = terms_service.accept_terms(
            user_id=user_id,
            acceptances=data,
            language=language
        )
        
        if not accept_result['success']:
            return jsonify({
                "success": False, 
                "error": accept_result.get('error', 'Failed to accept terms'),
                "field": accept_result.get('field')
            }), 400
        
        # Update session to reflect terms acceptance
        session['terms_accepted'] = True
        session['terms_accepted_at'] = accept_result['accepted_at']
        session['terms_version'] = accept_result['version']
        session['terms_language'] = accept_result['language']
        session.modified = True
        
        logger.info(f"✅ Terms accepted by user {user_id} in language {language}")
        
        return jsonify({
            "success": True,
            "message": "Terms accepted successfully",
            "redirect": "/intro"
        })
        
    except Exception as e:
        logger.error(f"Terms acceptance error: {e}")
        return jsonify({"success": False, "error": "Failed to accept terms"}), 500

@legal_bp.route('/api/terms-status')
def get_terms_status():
    """Get user's terms acceptance status"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not terms_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        status = terms_service.get_terms_status(user_id)
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting terms status: {e}")
        return jsonify({"success": False, "error": "Failed to load terms status"}), 500

@legal_bp.route('/api/revoke-terms', methods=['POST'])
def revoke_terms():
    """Revoke terms acceptance (GDPR compliance)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not terms_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        reason = data.get('reason', 'user_request') if data else 'user_request'
        
        user_id = session.get('user_id')
        revoke_result = terms_service.revoke_terms_acceptance(user_id, reason)
        
        if not revoke_result['success']:
            return jsonify({"success": False, "error": revoke_result['error']}), 500
        
        # Update session
        session['terms_accepted'] = False
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Terms acceptance revoked",
            "redirect": "/terms-acceptance"
        })
        
    except Exception as e:
        logger.error(f"Error revoking terms: {e}")
        return jsonify({"success": False, "error": "Failed to revoke terms"}), 500

# =============================================================================
# PRIVACY API ENDPOINTS
# =============================================================================

@legal_bp.route('/api/privacy-settings')
def get_privacy_settings():
    """Get user's privacy settings"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        settings_result = privacy_manager.get_privacy_settings(user_id)
        
        if not settings_result['success']:
            return jsonify({"success": False, "error": settings_result['error']}), 500
        
        return jsonify({
            "success": True,
            "settings": settings_result['privacy_settings'],
            "retention_periods": settings_result.get('retention_periods', {})
        })
        
    except Exception as e:
        logger.error(f"Error getting privacy settings: {e}")
        return jsonify({"success": False, "error": "Failed to load privacy settings"}), 500

@legal_bp.route('/api/privacy-settings', methods=['POST'])
def update_privacy_settings():
    """Update user's privacy settings"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
        
        user_id = session.get('user_id')
        update_result = privacy_manager.update_privacy_settings(user_id, data)
        
        if not update_result['success']:
            return jsonify({"success": False, "error": update_result['error']}), 500
        
        return jsonify({
            "success": True,
            "message": "Privacy settings updated successfully",
            "updated_at": update_result['updated_at']
        })
        
    except Exception as e:
        logger.error(f"Error updating privacy settings: {e}")
        return jsonify({"success": False, "error": "Failed to update privacy settings"}), 500

@legal_bp.route('/api/export-data')
def export_user_data():
    """Export user's data for GDPR compliance"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        user_id = session.get('user_id')
        export_result = privacy_manager.get_user_data_export(user_id)
        
        if not export_result['success']:
            return jsonify({"success": False, "error": export_result['error']}), 500
        
        logger.info(f"📊 Data export requested by user {user_id}")
        
        return jsonify({
            "success": True,
            "export_data": export_result['data'],
            "export_size": export_result.get('export_size', 0)
        })
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        return jsonify({"success": False, "error": "Failed to export data"}), 500

@legal_bp.route('/api/delete-account', methods=['POST'])
def delete_user_account():
    """Delete user account and all data (GDPR Right to Erasure)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        confirmation = data.get('confirmation') if data else None
        reason = data.get('reason', 'user_request') if data else 'user_request'
        
        # Require explicit confirmation
        if confirmation != 'DELETE_MY_ACCOUNT':
            return jsonify({
                "success": False, 
                "error": "Account deletion requires explicit confirmation"
            }), 400
        
        user_id = session.get('user_id')
        user_email = session.get('user_email', 'unknown')
        
        # Delete all user data
        deletion_result = privacy_manager.delete_user_data(user_id, reason)
        
        if not deletion_result['success']:
            return jsonify({"success": False, "error": deletion_result['error']}), 500
        
        # Clear session
        session.clear()
        
        logger.info(f"🗑️ Account deleted for user {user_id} ({user_email}) - reason: {reason}")
        
        return jsonify({
            "success": True,
            "message": "Account and all data deleted successfully",
            "deletion_timestamp": deletion_result['deletion_timestamp'],
            "redirect": "/login"
        })
        
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        return jsonify({"success": False, "error": "Failed to delete account"}), 500

@legal_bp.route('/api/anonymize-account', methods=['POST'])
def anonymize_user_account():
    """Anonymize user account (alternative to deletion)"""
    try:
        if not is_logged_in():
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        data = request.get_json()
        reason = data.get('reason', 'user_request') if data else 'user_request'
        
        user_id = session.get('user_id')
        anonymize_result = privacy_manager.anonymize_user_data(user_id, reason)
        
        if not anonymize_result['success']:
            return jsonify({"success": False, "error": anonymize_result['error']}), 500
        
        # Update session with anonymous info
        session['user_email'] = anonymize_result['anonymous_id']
        session['display_name'] = 'Anonymous User'
        session.modified = True
        
        logger.info(f"🔒 Account anonymized for user {user_id} - reason: {reason}")
        
        return jsonify({
            "success": True,
            "message": "Account anonymized successfully",
            "anonymous_id": anonymize_result['anonymous_id'],
            "anonymization_timestamp": anonymize_result['anonymization_timestamp']
        })
        
    except Exception as e:
        logger.error(f"Error anonymizing user account: {e}")
        return jsonify({"success": False, "error": "Failed to anonymize account"}), 500

# =============================================================================
# LEGAL DOCUMENTS API ENDPOINTS
# =============================================================================

@legal_bp.route('/api/legal-documents/<document_type>')
def get_legal_document(document_type):
    """Get specific legal document"""
    try:
        if not legal_documents:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        language = request.args.get('lang', 'en')
        version = request.args.get('version', None)
        
        if document_type == 'terms':
            result = legal_documents.get_terms_of_service(language, version)
        elif document_type == 'privacy':
            result = legal_documents.get_privacy_policy(language, version)
        elif document_type == 'ai-disclosure':
            result = legal_documents.get_ai_disclosure(language)
        elif document_type == 'combined':
            result = legal_documents.get_combined_legal_document(language)
        else:
            return jsonify({"success": False, "error": "Unknown document type"}), 400
        
        if not result['success']:
            return jsonify({"success": False, "error": result['error']}), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting legal document {document_type}: {e}")
        return jsonify({"success": False, "error": "Failed to load document"}), 500

@legal_bp.route('/api/legal-changelog')
def get_legal_changelog():
    """Get legal documents changelog"""
    try:
        if not legal_documents:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        changelog_result = legal_documents.get_document_changelog()
        
        if not changelog_result['success']:
            return jsonify({"success": False, "error": changelog_result['error']}), 500
        
        return jsonify(changelog_result)
        
    except Exception as e:
        logger.error(f"Error getting legal changelog: {e}")
        return jsonify({"success": False, "error": "Failed to load changelog"}), 500

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@legal_bp.route('/api/admin/terms-statistics')
def get_terms_statistics():
    """Get terms acceptance statistics (admin only)"""
    try:
        # TODO: Add proper admin authentication
        admin_key = request.args.get('key')
        if not admin_key:  # or not validate_admin_key(admin_key)
            return jsonify({"success": False, "error": "Unauthorized"}), 403
        
        if not terms_service:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        stats_result = terms_service.get_acceptance_statistics()
        
        if not stats_result['success']:
            return jsonify({"success": False, "error": stats_result['error']}), 500
        
        return jsonify(stats_result)
        
    except Exception as e:
        logger.error(f"Error getting terms statistics: {e}")
        return jsonify({"success": False, "error": "Failed to load statistics"}), 500

@legal_bp.route('/api/admin/cleanup-expired-data', methods=['POST'])
def cleanup_expired_data():
    """Clean up expired data (admin only)"""
    try:
        # TODO: Add proper admin authentication
        admin_key = request.args.get('key')
        if not admin_key:  # or not validate_admin_key(admin_key)
            return jsonify({"success": False, "error": "Unauthorized"}), 403
        
        if not privacy_manager:
            return jsonify({"success": False, "error": "Service unavailable"}), 503
        
        cleanup_result = privacy_manager.cleanup_expired_data()
        
        if not cleanup_result['success']:
            return jsonify({"success": False, "error": cleanup_result['error']}), 500
        
        return jsonify(cleanup_result)
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        return jsonify({"success": False, "error": "Failed to cleanup data"}), 500

# =============================================================================
# BLUEPRINT REGISTRATION HELPER
# =============================================================================

def register_legal_routes(app, database=None):
    """Register legal routes with the Flask app"""
    try:
        # Initialize services
        if not init_legal_services(database):
            logger.error("Failed to initialize legal services")
            return False
        
        # Register blueprint
        app.register_blueprint(legal_bp)
        
        logger.info("⚖️ Legal routes registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register legal routes: {e}")
        return False