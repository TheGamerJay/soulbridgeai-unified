"""
Production Email Sender for Password Reset
Uses SMTP for universal email delivery (Gmail/Outlook/any host)
"""
import os
import logging
import smtplib
import ssl
from email.message import EmailMessage
import html as _html

logger = logging.getLogger(__name__)

# SMTP Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "support@soulbridgeai.com")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
SITE_URL = os.getenv("SITE_URL", "https://www.soulbridgeai.com")

def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int = 60) -> bool:
    """Send password reset email using SMTP (Gmail/Outlook/any host)"""
    try:
        # Dev fallback if SMTP not configured
        if not SMTP_HOST or not SMTP_FROM:
            logger.warning("SMTP not configured (missing SMTP_HOST or SMTP_FROM) - showing link on page")
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
        
        # Send via SMTP
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = "Reset Your SoulBridge AI Password"
        
        # Set content (text first, then HTML alternative)
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")
        
        # Send email using appropriate SMTP method
        if SMTP_USE_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as server:
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                if SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        
        logger.info(f"✅ Password reset email sent successfully to: {to_email}")
        return True
            
    except Exception as e:
        logger.error(f"❌ Email sending error: {e}")
        return False

def test_email_config():
    """Test if SMTP email configuration is working"""
    if not SMTP_HOST:
        return {"status": "error", "message": "SMTP_HOST not configured"}
    
    if not SMTP_FROM:
        return {"status": "error", "message": "SMTP_FROM not configured"}
    
    try:
        # Test SMTP connection
        if SMTP_USE_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                # If we get here, connection is working
                return {
                    "status": "success", 
                    "message": f"SMTP configuration working (SSL: {SMTP_HOST}:{SMTP_PORT})",
                    "details": {
                        "host": SMTP_HOST,
                        "port": SMTP_PORT,
                        "user": SMTP_USER,
                        "from": SMTP_FROM,
                        "ssl": SMTP_USE_SSL,
                        "tls": SMTP_USE_TLS
                    }
                }
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                # If we get here, connection is working
                return {
                    "status": "success", 
                    "message": f"SMTP configuration working (TLS: {SMTP_HOST}:{SMTP_PORT})",
                    "details": {
                        "host": SMTP_HOST,
                        "port": SMTP_PORT,
                        "user": SMTP_USER,
                        "from": SMTP_FROM,
                        "ssl": SMTP_USE_SSL,
                        "tls": SMTP_USE_TLS
                    }
                }
            
    except Exception as e:
        return {"status": "error", "message": f"SMTP connection failed: {e}"}