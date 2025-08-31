"""
SoulBridge AI - Complete Email Service
Multi-provider email service with fallback support
Extracted from backend/email_service.py with improvements
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from .templates import EmailTemplates

logger = logging.getLogger(__name__)

# Try to import SendGrid (optional)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.info("SendGrid not installed - using SMTP/Resend only")

# Try to import Resend (optional)
try:
    import requests
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.info("Requests not installed - Resend not available")

class EmailService:
    """Complete email service with multi-provider support"""
    
    def __init__(self):
        # SMTP Configuration (Gmail/custom)
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")

        # SendGrid Configuration
        self.sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")

        # Resend Configuration (preferred)
        self.resend_api_key = os.environ.get("RESEND_API_KEY")

        # Common Configuration
        self.from_email = os.environ.get("FROM_EMAIL", self.smtp_username or "support@soulbridgeai.com")
        self.from_name = os.environ.get("FROM_NAME", "SoulBridge AI")
        self.support_email = os.environ.get("SUPPORT_EMAIL", "soulbridgeai.contact@gmail.com")

        # Check what's available
        self.smtp_configured = bool(self.smtp_username and self.smtp_password)
        self.sendgrid_configured = bool(self.sendgrid_api_key and SENDGRID_AVAILABLE)
        self.resend_configured = bool(self.resend_api_key and RESEND_AVAILABLE)

        self.is_configured = self.smtp_configured or self.sendgrid_configured or self.resend_configured

        # Initialize email templates
        self.templates = EmailTemplates(self.from_name, self.from_email, self.support_email)

        if not self.is_configured:
            logger.warning("No email service configured. Email features will not work.")
        elif self.resend_configured:
            logger.info("✅ Resend email service configured (preferred)")
        elif self.sendgrid_configured:
            logger.info("✅ SendGrid email service configured")
        elif self.smtp_configured:
            logger.info("✅ SMTP email service configured")

    def send_email(self, to_email, subject, text_content, html_content=None):
        """Send email using best available provider (Resend > SendGrid > SMTP)"""
        if not self.is_configured:
            logger.error("Email service not configured")
            return {"success": False, "error": "Email service not configured"}

        # Try Resend first (most reliable and modern)
        if self.resend_configured:
            return self._send_via_resend(to_email, subject, text_content, html_content)

        # Try SendGrid next
        elif self.sendgrid_configured:
            return self._send_via_sendgrid(to_email, subject, text_content, html_content)

        # Fallback to SMTP
        elif self.smtp_configured:
            return self._send_via_smtp(to_email, subject, text_content, html_content)

        return {"success": False, "error": "No email service available"}

    def _send_via_resend(self, to_email, subject, text_content, html_content=None):
        """Send email via Resend API"""
        try:
            payload = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
            }
            
            # Add HTML or text content
            if html_content:
                payload["html"] = html_content
            else:
                payload["text"] = text_content

            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"✅ Resend email sent successfully to {to_email}")
                return {"success": True, "provider": "resend", "id": response.json().get("id")}
            else:
                error_msg = response.text
                logger.error(f"❌ Resend API error: {response.status_code} - {error_msg}")
                # Fallback to next provider
                if self.sendgrid_configured:
                    logger.info("⤵️ Falling back to SendGrid...")
                    return self._send_via_sendgrid(to_email, subject, text_content, html_content)
                elif self.smtp_configured:
                    logger.info("⤵️ Falling back to SMTP...")
                    return self._send_via_smtp(to_email, subject, text_content, html_content)
                return {"success": False, "error": error_msg, "provider": "resend"}

        except Exception as e:
            logger.error(f"❌ Resend failed to send email to {to_email}: {e}")
            # Fallback to next provider
            if self.sendgrid_configured:
                logger.info("⤵️ Falling back to SendGrid...")
                return self._send_via_sendgrid(to_email, subject, text_content, html_content)
            elif self.smtp_configured:
                logger.info("⤵️ Falling back to SMTP...")
                return self._send_via_smtp(to_email, subject, text_content, html_content)
            return {"success": False, "error": str(e), "provider": "resend"}

    def _send_via_sendgrid(self, to_email, subject, text_content, html_content=None):
        """Send email via SendGrid API"""
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content,
            )

            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)

            logger.info(f"✅ SendGrid email sent successfully to {to_email} (Status: {response.status_code})")
            return {"success": True, "provider": "sendgrid", "status_code": response.status_code}

        except Exception as e:
            logger.error(f"❌ SendGrid failed to send email to {to_email}: {e}")
            # Fallback to SMTP if available
            if self.smtp_configured:
                logger.info("⤵️ Falling back to SMTP...")
                return self._send_via_smtp(to_email, subject, text_content, html_content)
            return {"success": False, "error": str(e), "provider": "sendgrid"}

    def _send_via_smtp(self, to_email, subject, text_content, html_content=None):
        """Send email via SMTP (Gmail/custom server)"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text part
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_content:
                html_part = MIMEText(html_content, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ SMTP email sent successfully to {to_email}")
            return {"success": True, "provider": "smtp"}

        except Exception as e:
            logger.error(f"❌ SMTP failed to send email to {to_email}: {e}")
            return {"success": False, "error": str(e), "provider": "smtp"}

    def send_welcome_email(self, email, display_name):
        """Send welcome email to new users"""
        subject, text_content, html_content = self.templates.welcome_email(email, display_name)
        return self.send_email(email, subject, text_content, html_content)

    def send_verification_email(self, email, display_name, verification_token, base_url):
        """Send email verification email"""
        subject, text_content, html_content = self.templates.verification_email(
            email, display_name, verification_token, base_url
        )
        return self.send_email(email, subject, text_content, html_content)

    def send_password_reset_email(self, email, display_name, reset_token, base_url):
        """Send password reset email"""
        subject, text_content, html_content = self.templates.password_reset_email(
            email, display_name, reset_token, base_url
        )
        return self.send_email(email, subject, text_content, html_content)

    def handle_contact_form(self, user_email, user_message):
        """Handle contact form submission - send notification and auto-reply"""
        results = {}
        
        # Send notification to support team
        notification_result = self.send_contact_form_notification(user_email, user_message)
        results['notification'] = notification_result
        
        # Send auto-reply to user
        reply_result = self.send_contact_form_auto_reply(user_email)
        results['auto_reply'] = reply_result
        
        # Return combined success status
        overall_success = notification_result.get('success', False) and reply_result.get('success', False)
        
        return {
            'success': overall_success,
            'results': results,
            'message': 'Contact form processed and emails sent' if overall_success else 'Some emails failed to send'
        }

    def send_contact_form_notification(self, user_email, user_message):
        """Send contact form notification to support team"""
        subject, text_content, html_content = self.templates.contact_form_notification(
            user_email, user_message
        )
        return self.send_email(self.support_email, subject, text_content, html_content)

    def send_contact_form_auto_reply(self, user_email):
        """Send auto-reply to user who submitted contact form"""
        subject, text_content, html_content = self.templates.contact_form_auto_reply(user_email)
        return self.send_email(user_email, subject, text_content, html_content)

    def send_notification_email(self, to_email, subject, message, notification_type="info"):
        """Send generic notification email"""
        subject, text_content, html_content = self.templates.notification_email(
            to_email, subject, message, notification_type
        )
        return self.send_email(to_email, subject, text_content, html_content)

    def get_service_status(self):
        """Get status of all configured email services"""
        return {
            "configured": self.is_configured,
            "services": {
                "resend": {
                    "available": RESEND_AVAILABLE,
                    "configured": self.resend_configured,
                    "preferred": True
                },
                "sendgrid": {
                    "available": SENDGRID_AVAILABLE,
                    "configured": self.sendgrid_configured,
                    "preferred": False
                },
                "smtp": {
                    "available": True,
                    "configured": self.smtp_configured,
                    "preferred": False
                }
            },
            "from_email": self.from_email,
            "from_name": self.from_name,
            "support_email": self.support_email
        }