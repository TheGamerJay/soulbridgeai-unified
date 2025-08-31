"""
SoulBridge AI - Notifications Routes
Email and notification endpoints extracted from monolith
"""
import os
import logging
from flask import Blueprint, request, jsonify, session
from .email_service import EmailService
from .resend_service import ResendService

logger = logging.getLogger(__name__)

# Create notifications blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# Initialize services
email_service = EmailService()
resend_service = ResendService()

@notifications_bp.route('/status', methods=['GET'])
def get_notification_status():
    """Get status of all notification services"""
    return jsonify({
        "services": {
            "email_service": email_service.get_service_status(),
            "resend_service": resend_service.get_status()
        }
    })

@notifications_bp.route('/test-email', methods=['POST']) 
def test_email():
    """Test email functionality (admin only)"""
    try:
        # Basic auth check - only for testing
        if not session.get('user_authenticated'):
            return jsonify({"success": False, "error": "Authentication required"}), 401
            
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        to_email = data.get('to_email')
        if not to_email:
            return jsonify({"success": False, "error": "to_email required"}), 400
        
        # Send test email
        result = email_service.send_notification_email(
            to_email,
            "Test Email from SoulBridge AI", 
            "This is a test email to verify the notification system is working correctly.",
            "info"
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Test email error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@notifications_bp.route('/contact-form', methods=['POST'])
def handle_contact_form():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        user_email = data.get('email')
        user_message = data.get('message')
        
        if not user_email or not user_message:
            return jsonify({
                "success": False, 
                "error": "Email and message are required"
            }), 400
        
        # Process contact form with email service
        result = email_service.handle_contact_form(user_email, user_message)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "Your message has been sent successfully. We'll get back to you soon!"
            })
        else:
            return jsonify({
                "success": False,
                "message": "There was an issue sending your message. Please try again later."
            }), 500
            
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        return jsonify({
            "success": False, 
            "error": "An error occurred processing your request"
        }), 500

def send_trial_warning_email(user_email, minutes_left):
    """Send trial warning email using comprehensive system
    
    Extracted from monolith app.py - used by trial system
    """
    if not user_email:
        logger.warning("No email provided for trial warning")
        return
    
    templates = {
        10: "⏳ 10 Minutes Left on Your Trial!",
        5: "🚨 5 Minutes Left - Don't Lose Access!",
        1: "⚠️ Trial Ending in 1 Minute!"
    }
    subject = templates.get(minutes_left, "Trial Ending Soon")
    
    message = f"""
Your SoulBridge AI trial will expire in {minutes_left} minute{'s' if minutes_left != 1 else ''}!

Don't lose access to:
• AI Images & Voice Journaling
• Relationship Profiles & Meditations  
• Premium Companions & Features

Upgrade now to keep your premium access:
→ Silver Plan: $12.99/month
→ Gold Plan: $19.99/month

Visit your account settings to upgrade and continue your SoulBridge AI journey!

Thank you for trying SoulBridge AI!
    """.strip()
    
    # Send using email service
    result = email_service.send_notification_email(
        user_email, subject, message, "warning"
    )
    
    if result.get('success'):
        logger.info(f"✅ Trial warning email sent to {user_email} ({minutes_left} min)")
    else:
        logger.error(f"❌ Failed to send trial warning to {user_email}: {result.get('error')}")
    
    return result

def send_simple_email(to_email, subject, message):
    """Simple email sender for legacy compatibility
    
    Extracted from monolith app.py - maintains backwards compatibility
    """
    try:
        # Use the comprehensive email service
        result = email_service.send_email(to_email, subject, message)
        
        if result.get('success'):
            logger.info(f"✅ Simple email sent successfully to {to_email}")
        else:
            logger.error(f"❌ Failed to send simple email: {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Simple email failed: {e}")
        return {"success": False, "error": str(e)}