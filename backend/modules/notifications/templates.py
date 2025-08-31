"""
SoulBridge AI - Email Templates
Professional email templates for all notification types
Extracted from backend/email_service.py with improvements
"""

class EmailTemplates:
    """Email template manager for all notification types"""
    
    def __init__(self, from_name="SoulBridge AI", from_email="support@soulbridgeai.com", support_email="soulbridgeai.contact@gmail.com"):
        self.from_name = from_name
        self.from_email = from_email
        self.support_email = support_email
    
    def _get_base_style(self):
        """Common CSS styles for all email templates"""
        return """
        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            background: white;
            border-radius: 8px;
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
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 14px;
            color: #666;
            text-align: center;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 12px;
            margin: 20px 0;
            font-size: 14px;
        }
        .btn {
            display: inline-block;
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: bold;
            margin: 20px 0;
        }
        .btn-primary {
            background: linear-gradient(135deg, #22d3ee, #0891b2);
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #0891b2, #0e7490);
        }
        .btn-danger {
            background: linear-gradient(135deg, #dc2626, #b91c1c);
        }
        .btn-danger:hover {
            background: linear-gradient(135deg, #b91c1c, #991b1b);
        }
        """
    
    def welcome_email(self, email, display_name):
        """Generate welcome email for new users"""
        subject = f"Welcome to {self.from_name}!"
        
        text_content = f"""
Hello {display_name or 'there'},

Welcome to {self.from_name}! We're excited to have you join our community of users exploring meaningful conversations with AI companions.

Here's what you can do with your new account:

✨ Chat with diverse AI companions, each with unique personalities
🔮 Explore fortune telling and horoscope features  
📝 Use our decoder and creative writing tools
🎨 Access premium features with Silver and Gold tiers

To get started, simply log in to your account and begin exploring our features. If you're on the Bronze tier, don't forget you can try our 5-hour trial to experience premium features!

If you have any questions or need assistance, feel free to reach out to our support team at {self.support_email}.

Best regards,
The {self.from_name} Team

---
{self.from_name} - Your AI-powered emotional companion
        """.strip()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {self.from_name}!</title>
    <style>{self._get_base_style()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>Welcome to our community!</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>Welcome to {self.from_name}! We're excited to have you join our community of users exploring meaningful conversations with AI companions.</p>
        
        <h3>Here's what you can do with your new account:</h3>
        <ul>
            <li>✨ Chat with diverse AI companions, each with unique personalities</li>
            <li>🔮 Explore fortune telling and horoscope features</li>
            <li>📝 Use our decoder and creative writing tools</li>
            <li>🎨 Access premium features with Silver and Gold tiers</li>
        </ul>
        
        <p>To get started, simply log in to your account and begin exploring our features. If you're on the Bronze tier, don't forget you can try our 5-hour trial to experience premium features!</p>
        
        <p>If you have any questions or need assistance, feel free to reach out to our support team at <a href="mailto:{self.support_email}">{self.support_email}</a>.</p>
        
        <div class="footer">
            <p>Best regards,<br>The {self.from_name} Team</p>
            <p>{self.from_name} - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content
    
    def verification_email(self, email, display_name, verification_token, base_url):
        """Generate email verification email"""
        verification_url = f"{base_url}/auth/verify-email?token={verification_token}"
        subject = f"Verify your {self.from_name} account"
        
        text_content = f"""
Hello {display_name or 'there'},

Thank you for creating a {self.from_name} account! To complete your registration, please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours. If you did not create this account, please ignore this email.

Best regards,
The {self.from_name} Team

---
{self.from_name} - Your AI-powered emotional companion
        """.strip()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your {self.from_name} account</title>
    <style>{self._get_base_style()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>Verify your email address</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>Thank you for creating a {self.from_name} account! To complete your registration and start having meaningful conversations with our AI companions, please verify your email address.</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="btn btn-primary">Verify Email Address</a>
        </div>
        
        <div class="warning">
            <strong>This link will expire in 24 hours.</strong> If you did not create this account, please ignore this email.
        </div>
        
        <p>If the button above doesn't work, you can copy and paste this link into your browser:</p>
        <p style="word-break: break-all; font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">{verification_url}</p>
        
        <div class="footer">
            <p>Best regards,<br>The {self.from_name} Team</p>
            <p>{self.from_name} - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content
    
    def password_reset_email(self, email, display_name, reset_token, base_url):
        """Generate password reset email"""
        reset_url = f"{base_url}/auth/reset-password?token={reset_token}"
        subject = f"Reset your {self.from_name} password"
        
        text_content = f"""
Hello {display_name or 'there'},

We received a request to reset the password for your {self.from_name} account. If you made this request, click the link below to reset your password:

{reset_url}

This link will expire in 1 hour. If you did not request a password reset, please ignore this email.

Best regards,
The {self.from_name} Team

---
{self.from_name} - Your AI-powered emotional companion
        """.strip()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset your {self.from_name} password</title>
    <style>{self._get_base_style()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>Reset your password</h1>
        </div>
        
        <p>Hello {display_name or 'there'},</p>
        
        <p>We received a request to reset the password for your {self.from_name} account. If you made this request, click the button below to reset your password.</p>
        
        <div style="text-align: center;">
            <a href="{reset_url}" class="btn btn-danger">Reset Password</a>
        </div>
        
        <div class="warning">
            <strong>This link will expire in 1 hour.</strong> If you did not request a password reset, please ignore this email and your password will remain unchanged.
        </div>
        
        <p>If the button above doesn't work, you can copy and paste this link into your browser:</p>
        <p style="word-break: break-all; font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px;">{reset_url}</p>
        
        <div class="footer">
            <p>Best regards,<br>The {self.from_name} Team</p>
            <p>{self.from_name} - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content
    
    def contact_form_notification(self, user_email, user_message):
        """Generate contact form notification email to support team"""
        subject = f"New Contact Form Submission from {user_email}"
        
        text_content = f"""
New contact form submission received:

From: {user_email}
Message:
{user_message}

---
{self.from_name} Contact Form System
        """.strip()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Contact Form Submission</title>
    <style>{self._get_base_style()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>New Contact Form Submission</h1>
        </div>
        
        <p><strong>From:</strong> {user_email}</p>
        
        <p><strong>Message:</strong></p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #22d3ee;">
            {user_message.replace('\n', '<br>')}
        </div>
        
        <div class="footer">
            <p>{self.from_name} Contact Form System</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content
    
    def contact_form_auto_reply(self, user_email):
        """Generate auto-reply for contact form submissions"""
        subject = f"We received your message - {self.from_name}"
        
        text_content = f"""
Hello,

Thank you for contacting {self.from_name}! We have received your message and will get back to you as soon as possible.

Our team typically responds within 24-48 hours during business days. For urgent matters, you can also reach us directly at {self.support_email}.

We appreciate your patience and look forward to assisting you.

Best regards,
The {self.from_name} Team

---
{self.from_name} - Your AI-powered emotional companion
        """.strip()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>We received your message</title>
    <style>{self._get_base_style()}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>Thank you for contacting us!</h1>
        </div>
        
        <p>Hello,</p>
        
        <p>Thank you for contacting {self.from_name}! We have received your message and will get back to you as soon as possible.</p>
        
        <div style="background: #e6f7ff; padding: 15px; border-radius: 4px; border-left: 4px solid #22d3ee;">
            <p><strong>Response Time:</strong> Our team typically responds within 24-48 hours during business days.</p>
            <p><strong>Urgent Matters:</strong> For urgent issues, you can reach us directly at <a href="mailto:{self.support_email}">{self.support_email}</a>.</p>
        </div>
        
        <p>We appreciate your patience and look forward to assisting you.</p>
        
        <div class="footer">
            <p>Best regards,<br>The {self.from_name} Team</p>
            <p>{self.from_name} - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content
    
    def notification_email(self, email, subject, message, notification_type="info"):
        """Generate generic notification email"""
        # Use provided subject directly
        
        text_content = f"""
Hello,

{message}

Best regards,
The {self.from_name} Team

---
{self.from_name} - Your AI-powered emotional companion
        """.strip()
        
        # Color scheme based on notification type
        type_colors = {
            "info": "#22d3ee",
            "success": "#10b981", 
            "warning": "#f59e0b",
            "error": "#dc2626"
        }
        color = type_colors.get(notification_type, "#22d3ee")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        {self._get_base_style()}
        .notification-{notification_type} {{
            background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
            border: 1px solid {color};
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid {color};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{self.from_name}</div>
            <h1>{subject}</h1>
        </div>
        
        <div class="notification-{notification_type}">
            {message.replace('\n', '<br>')}
        </div>
        
        <div class="footer">
            <p>Best regards,<br>The {self.from_name} Team</p>
            <p>{self.from_name} - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, text_content, html_content