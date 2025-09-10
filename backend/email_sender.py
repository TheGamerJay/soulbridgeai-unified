"""
Production Email Sender for Password Reset
Uses Resend API for reliable email delivery
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

# Email configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "support@soulbridgeai.com")
SITE_URL = os.getenv("SITE_URL", "https://www.soulbridgeai.com")

def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int = 60) -> bool:
    """Send password reset email using Resend API"""
    try:
        if not RESEND_API_KEY:
            logger.warning("No RESEND_API_KEY configured - cannot send emails")
            return False
            
        # Create professional email HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your SoulBridge AI Password</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #22d3ee, #0891b2); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: bold;">SoulBridge AI</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 16px;">Password Reset Request</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #1f2937; margin: 0 0 20px 0; font-size: 24px;">Reset Your Password</h2>
                    <p style="color: #6b7280; line-height: 1.6; margin-bottom: 25px; font-size: 16px;">
                        We received a request to reset your password for your SoulBridge AI account. 
                        Click the button below to set a new password.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #22d3ee, #0891b2); color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(34, 211, 238, 0.3);">
                            Reset My Password
                        </a>
                    </div>
                    
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 25px 0;">
                        <p style="color: #6b7280; margin: 0; font-size: 14px; line-height: 1.5;">
                            <strong>⏰ This link expires in {expires_minutes} minutes</strong><br>
                            For security, password reset links are only valid for a limited time.
                        </p>
                    </div>
                    
                    <p style="color: #9ca3af; font-size: 14px; line-height: 1.5; margin-bottom: 15px;">
                        If the button doesn't work, copy and paste this link into your browser:
                    </p>
                    <p style="background: #f3f4f6; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; word-break: break-all; color: #374151;">
                        {reset_url}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    
                    <p style="color: #9ca3af; font-size: 14px; line-height: 1.5; margin: 0;">
                        If you didn't request this password reset, you can safely ignore this email. 
                        Your password won't be changed unless you click the link above.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; margin: 0; font-size: 14px;">
                        This email was sent by <strong>SoulBridge AI</strong><br>
                        Your personal AI companion platform
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        SoulBridge AI - Password Reset Request
        
        We received a request to reset your password for your SoulBridge AI account.
        
        Reset your password: {reset_url}
        
        This link expires in {expires_minutes} minutes.
        
        If you didn't request this password reset, you can safely ignore this email.
        Your password won't be changed unless you use the link above.
        
        ---
        SoulBridge AI
        Your personal AI companion platform
        """
        
        # Send via Resend API
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": RESEND_FROM,
                "to": [to_email],
                "subject": "Reset Your SoulBridge AI Password",
                "html": html_content,
                "text": text_content
            },
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            logger.info(f"✅ Password reset email sent successfully to: {to_email}")
            return True
        else:
            logger.error(f"❌ Failed to send email. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Email sending error: {e}")
        return False

def test_email_config():
    """Test if email configuration is working"""
    if not RESEND_API_KEY:
        return {"status": "error", "message": "RESEND_API_KEY not configured"}
    
    try:
        # Test API key by making a simple request
        response = requests.get(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": "Email configuration is working"}
        else:
            return {"status": "error", "message": f"API key invalid or expired (Status: {response.status_code})"}
            
    except Exception as e:
        return {"status": "error", "message": f"Connection error: {e}"}