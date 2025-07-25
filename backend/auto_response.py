# Auto-response email functionality
from email_service import EmailService
import logging


def send_contact_auto_response(email, name=None):
    """Send automated response for contact form submissions"""
    email_service = EmailService()

    if not email_service.is_configured:
        logging.warning("Email service not configured - auto-response skipped")
        return {"success": False, "error": "Email service not configured"}

    subject = "Thanks for Reaching Out to SoulBridgeAI"

    text_content = f"""
Hey there{f', {name}' if name else ''},

We've received your message and our team will get back to you as soon as possible. In the meantime, feel free to explore our Help Center for quick answers to common questions:
https://soulbridgeai.com/help

Thank you for choosing SoulBridgeAI!

— The SoulBridgeAI Team

---
IMPORTANT: This is an automated response. Please do not reply to this email.
For urgent matters, please visit our support page at https://soulbridgeai.com/support
    """.strip()

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thanks for Reaching Out to SoulBridgeAI</title>
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
        .help-btn {{
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
        .important-notice {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
            font-size: 14px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">SoulBridgeAI</div>
            <h1>Thanks for Reaching Out!</h1>
        </div>
        
        <p>Hey there{f', {name}' if name else ''},</p>
        
        <p>We've received your message and our team will get back to you as soon as possible. We appreciate you taking the time to contact us!</p>
        
        <p>In the meantime, feel free to explore our Help Center for quick answers to common questions:</p>
        
        <div style="text-align: center;">
            <a href="https://soulbridgeai.com/help" class="help-btn">Visit Help Center</a>
        </div>
        
        <p>Thank you for choosing SoulBridgeAI!</p>
        
        <div class="important-notice">
            <strong>⚠️ IMPORTANT:</strong> This is an automated response. Please do not reply to this email.<br>
            For urgent matters, please visit our <a href="https://soulbridgeai.com/support" style="color: #0891b2;">support page</a>.
        </div>
        
        <div class="footer">
            <p><strong>— The SoulBridgeAI Team</strong></p>
            <p>SoulBridgeAI - Your AI-powered emotional companion</p>
        </div>
    </div>
</body>
</html>
    """.strip()

    return email_service.send_email(email, subject, text_content, html_content)
