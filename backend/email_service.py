# Email Service for Authentication
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Try to import SendGrid (optional)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.info("SendGrid not installed - using SMTP only")

# Try to import Resend (optional)
try:
    import requests
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logging.info("Requests not installed - Resend not available")


class EmailService:
    def __init__(self):
        # SMTP Configuration (Gmail)
        self.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")

        # SendGrid Configuration
        self.sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")

        # Resend Configuration
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

        if not self.is_configured:
            logging.warning(
                "No email service configured. Email features will not work."
            )
        elif self.resend_configured:
            logging.info("Resend email service configured")
        elif self.sendgrid_configured:
            logging.info("SendGrid email service configured")
        elif self.smtp_configured:
            logging.info("SMTP email service configured")

    def send_email(self, to_email, subject, text_content, html_content=None):
        """Send email using Resend, SendGrid, or SMTP (in priority order)"""
        if not self.is_configured:
            logging.error("Email service not configured")
            return {"success": False, "error": "Email service not configured"}

        # Try Resend first (most reliable and modern)
        if self.resend_configured:
            return self._send_via_resend(
                to_email, subject, text_content, html_content
            )

        # Try SendGrid next
        elif self.sendgrid_configured:
            return self._send_via_sendgrid(
                to_email, subject, text_content, html_content
            )

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
                headers=headers
            )

            if response.status_code == 200:
                logging.info(f"Resend email sent successfully to {to_email}")
                return {"success": True, "provider": "resend"}
            else:
                error_msg = response.text
                logging.error(f"Resend API error: {response.status_code} - {error_msg}")
                # Fallback to next provider
                if self.sendgrid_configured:
                    logging.info("Falling back to SendGrid...")
                    return self._send_via_sendgrid(to_email, subject, text_content, html_content)
                elif self.smtp_configured:
                    logging.info("Falling back to SMTP...")
                    return self._send_via_smtp(to_email, subject, text_content, html_content)
                return {"success": False, "error": error_msg}

        except Exception as e:
            logging.error(f"Resend failed to send email to {to_email}: {e}")
            # Fallback to next provider
            if self.sendgrid_configured:
                logging.info("Falling back to SendGrid...")
                return self._send_via_sendgrid(to_email, subject, text_content, html_content)
            elif self.smtp_configured:
                logging.info("Falling back to SMTP...")
                return self._send_via_smtp(to_email, subject, text_content, html_content)
            return {"success": False, "error": str(e)}

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

            logging.info(
                f"SendGrid email sent successfully to {to_email} (Status: {response.status_code})"
            )
            return {"success": True, "provider": "sendgrid"}

        except Exception as e:
            logging.error(f"SendGrid failed to send email to {to_email}: {e}")
            # Fallback to SMTP if available
            if self.smtp_configured:
                logging.info("Falling back to SMTP...")
                return self._send_via_smtp(
                    to_email, subject, text_content, html_content
                )
            return {"success": False, "error": str(e)}

    def _send_via_smtp(self, to_email, subject, text_content, html_content=None):
        """Send email via SMTP (Gmail)"""
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

            logging.info(f"SMTP email sent successfully to {to_email}")
            return {"success": True, "provider": "smtp"}

        except Exception as e:
            logging.error(f"SMTP failed to send email to {to_email}: {e}")
            return {"success": False, "error": str(e)}

    def send_verification_email(
        self, email, display_name, verification_token, base_url
    ):
        """Send email verification email"""
        verification_url = f"{base_url}/auth/verify-email?token={verification_token}"

        subject = "Verify your SoulBridge AI account"

        text_content = f"""
Hello {display_name or 'there'},

Thank you for creating a SoulBridge AI account! To complete your registration, please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours. If you did not create this account, please ignore this email.

Best regards,
The SoulBridge AI Team

---
SoulBridge AI - Your AI-powered emotional companion
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your SoulBridge AI account</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #22d3ee;
            margin-bottom: 10px;
        }}
        .verify-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #22d3ee, #0891b2);
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .verify-btn:hover {{
            background: linear-gradient(135deg, #0891b2, #0e7490);
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 12px;
            margin: 20px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">SoulBridge AI</div>
            <h1>Verify your email address</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>Thank you for creating a SoulBridge AI account! To complete your registration and start having meaningful conversations with our AI companions, please verify your email address.</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="verify-btn">Verify Email Address</a>
        </div>
        
        <div class="warning">
            <strong>This link will expire in 24 hours.</strong> If you did not create this account, please ignore this email.
        </div>
        
        <p>If the button above doesn't work, you can copy and paste this link into your browser:</p>
        <p style="word-break: break-all; font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">{verification_url}</p>
        
        <div class="footer">
            <p>Best regards,<br>The SoulBridge AI Team</p>
            <p>SoulBridge AI - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(email, subject, text_content, html_content)

    def send_password_reset_email(self, email, display_name, reset_token, base_url):
        """Send password reset email"""
        reset_url = f"{base_url}/auth/reset-password?token={reset_token}"

        subject = "Reset your SoulBridge AI password"

        text_content = f"""
Hello {display_name or 'there'},

We received a request to reset the password for your SoulBridge AI account. If you made this request, click the link below to reset your password:

{reset_url}

This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

Best regards,
The SoulBridge AI Team

---
SoulBridge AI - Your AI-powered emotional companion
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset your SoulBridge AI password</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #22d3ee;
            margin-bottom: 10px;
        }}
        .reset-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .reset-btn:hover {{
            background: linear-gradient(135deg, #b91c1c, #991b1b);
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
        .warning {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 4px;
            padding: 12px;
            margin: 20px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">SoulBridge AI</div>
            <h1>Reset your password</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>We received a request to reset the password for your SoulBridge AI account. If you made this request, click the button below to reset your password:</p>
        
        <div style="text-align: center;">
            <a href="{reset_url}" class="reset-btn">Reset Password</a>
        </div>
        
        <div class="warning">
            <strong>This link will expire in 1 hour.</strong> If you did not request a password reset, please ignore this email and your password will remain unchanged.
        </div>
        
        <p>If the button above doesn't work, you can copy and paste this link into your browser:</p>
        <p style="word-break: break-all; font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">{reset_url}</p>
        
        <div class="footer">
            <p>Best regards,<br>The SoulBridge AI Team</p>
            <p>SoulBridge AI - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(email, subject, text_content, html_content)

    def send_welcome_email(self, email, display_name):
        """Send welcome email to new users"""
        subject = "Welcome to SoulBridge AI! 🌟"

        text_content = f"""
Hello {display_name or 'there'},

Welcome to SoulBridge AI! We're thrilled to have you join our community.

Your account has been successfully created and verified. You can now:

• Have meaningful conversations with our AI companions
• Save and organize your personal diary entries
• Access your conversations from any device
• Experience AI-powered emotional support

Start your journey by visiting our chat interface and selecting your preferred AI companion.

If you have any questions or need help getting started, feel free to reach out to our support team.

Welcome aboard!

The SoulBridge AI Team

----
SoulBridge AI - Your AI-powered emotional companion
Visit us: https://soulbridgeai.com
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to SoulBridge AI</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #22d3ee;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #22d3ee;
            margin-bottom: 10px;
        }}
        .welcome-emoji {{
            font-size: 48px;
            margin: 20px 0;
        }}
        .feature-list {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .feature-list ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .feature-list li {{
            margin: 8px 0;
            color: #555;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #22d3ee, #06b6d4);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">SoulBridge AI</div>
            <div class="welcome-emoji">🌟</div>
            <h1>Welcome to SoulBridge AI!</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>Welcome to SoulBridge AI! We're thrilled to have you join our community of users who are exploring meaningful conversations with AI companions.</p>
        
        <p>Your account has been successfully created and verified. You can now:</p>
        
        <div class="feature-list">
            <ul>
                <li>Have meaningful conversations with our AI companions</li>
                <li>Save and organize your personal diary entries</li>
                <li>Access your conversations from any device</li>
                <li>Experience AI-powered emotional support</li>
            </ul>
        </div>
        
        <div style="text-align: center;">
            <a href="https://soulbridgeai.com" class="cta-button">Start Your Journey</a>
        </div>
        
        <p>If you have any questions or need help getting started, feel free to reach out to our support team.</p>
        
        <div class="footer">
            <p>Welcome aboard!<br><strong>The SoulBridge AI Team</strong></p>
            <p>SoulBridge AI - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()

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
        subject = "📥 New Contact Form Message"
        
        text_content = f"""
New Contact Form Submission

From: {user_email}

Message:
{user_message}

Please respond to this user as soon as possible.
        """.strip()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: #22d3ee;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .message-box {{
            background: #f8fafc;
            border-left: 4px solid #22d3ee;
            padding: 15px;
            margin: 20px 0;
        }}
        .from-email {{
            font-weight: bold;
            color: #0891b2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📥 New Contact Form Message</h1>
        </div>
        
        <p><strong>From:</strong> <span class="from-email">{user_email}</span></p>
        
        <div class="message-box">
            <strong>Message:</strong><br>
            {user_message.replace(chr(10), '<br>')}
        </div>
        
        <p><em>Please respond to this user as soon as possible.</em></p>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(self.support_email, subject, text_content, html_content)

    def send_contact_form_auto_reply(self, user_email):
        """Send auto-reply to user who submitted contact form"""
        subject = "Thanks for contacting SoulBridge AI"
        
        text_content = """
Hi there,

Thank you for reaching out to SoulBridge AI. We received your message and will get back to you soon.

Our support team typically responds within 24-48 hours. If you have an urgent issue, please mention "URGENT" in your subject line.

In the meantime, feel free to explore our FAQ section or continue chatting with your AI companions.

Warm regards,
SoulBridge AI Support Team
        """.strip()

        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #22d3ee;
            margin-bottom: 10px;
        }
        .response-time {
            background: #e0f2fe;
            border: 1px solid #22d3ee;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">SoulBridge AI</div>
            <h1>Thanks for contacting us! 💌</h1>
        </div>
        
        <p>Hi there,</p>
        <p>Thank you for reaching out to SoulBridge AI. We received your message and will get back to you soon.</p>
        
        <div class="response-time">
            <strong>⏰ Response Time:</strong> 24-48 hours<br>
            <em>For urgent issues, please mention "URGENT" in your subject line</em>
        </div>
        
        <p>In the meantime, feel free to explore our FAQ section or continue chatting with your AI companions.</p>
        
        <div class="footer">
            <p>Warm regards,<br><strong>SoulBridge AI Support Team</strong></p>
            <p>SoulBridge AI - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(user_email, subject, text_content, html_content)