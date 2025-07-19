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

class EmailService:
    def __init__(self):
        # SMTP Configuration (Gmail)
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        
        # SendGrid Configuration
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
        # Common Configuration
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'SoulBridge AI')
        
        # Check what's available
        self.smtp_configured = bool(self.smtp_username and self.smtp_password)
        self.sendgrid_configured = bool(self.sendgrid_api_key and SENDGRID_AVAILABLE)
        
        self.is_configured = self.smtp_configured or self.sendgrid_configured
        
        if not self.is_configured:
            logging.warning("⚠️  No email service configured. Email features will not work.")
        elif self.sendgrid_configured:
            logging.info("✅ SendGrid email service configured")
        elif self.smtp_configured:
            logging.info("✅ SMTP email service configured")
    
    def send_email(self, to_email, subject, text_content, html_content=None):
        """Send email using SendGrid or SMTP"""
        if not self.is_configured:
            logging.error("Email service not configured")
            return {'success': False, 'error': 'Email service not configured'}
        
        # Try SendGrid first (more reliable)
        if self.sendgrid_configured:
            return self._send_via_sendgrid(to_email, subject, text_content, html_content)
        
        # Fallback to SMTP
        elif self.smtp_configured:
            return self._send_via_smtp(to_email, subject, text_content, html_content)
        
        return {'success': False, 'error': 'No email service available'}
    
    def _send_via_sendgrid(self, to_email, subject, text_content, html_content=None):
        """Send email via SendGrid API"""
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)
            
            logging.info(f"SendGrid email sent successfully to {to_email} (Status: {response.status_code})")
            return {'success': True, 'provider': 'sendgrid'}
            
        except Exception as e:
            logging.error(f"SendGrid failed to send email to {to_email}: {e}")
            # Fallback to SMTP if available
            if self.smtp_configured:
                logging.info("Falling back to SMTP...")
                return self._send_via_smtp(to_email, subject, text_content, html_content)
            return {'success': False, 'error': str(e)}
    
    def _send_via_smtp(self, to_email, subject, text_content, html_content=None):
        """Send email via SMTP (Gmail)"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logging.info(f"SMTP email sent successfully to {to_email}")
            return {'success': True, 'provider': 'smtp'}
            
        except Exception as e:
            logging.error(f"SMTP failed to send email to {to_email}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_verification_email(self, email, display_name, verification_token, base_url):
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

• Have meaningful conversations with Blayzo and Blayzica
• Save and organize your personal diary entries
• Access your conversations from any device
• Experience AI-powered emotional support

Start your journey by visiting our chat interface and selecting your preferred AI companion.

If you have any questions or need help getting started, feel free to reach out to our support team.

Welcome aboard!

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
        }}
        .cta-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #22d3ee, #0891b2);
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
            text-align: center;
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
                <li><strong>Have meaningful conversations</strong> with Blayzo and Blayzica, our AI companions</li>
                <li><strong>Save and organize</strong> your personal diary entries securely</li>
                <li><strong>Access your conversations</strong> from any device, anywhere</li>
                <li><strong>Experience AI-powered emotional support</strong> tailored to your needs</li>
            </ul>
        </div>
        
        <p>Ready to start your journey? Begin by selecting your preferred AI companion and start your first conversation!</p>
        
        <div style="text-align: center;">
            <a href="#" class="cta-btn">Start Chatting Now</a>
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
