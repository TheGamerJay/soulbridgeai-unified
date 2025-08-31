"""
SoulBridge AI - Simple Resend Email Service
Extracted from backend/resend_email.py with improvements
"""
import os
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResendService:
    """Simple Resend email service wrapper"""
    
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY")
        self.from_email = os.environ.get("FROM_EMAIL", "SoulBridge AI <soulbridgeai.contact@gmail.com>")
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("Resend API key not configured")
        else:
            logger.info("✅ Resend service configured")
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email via Resend API - simple implementation"""
        if not self.is_configured:
            return {"success": False, "error": "Resend not configured"}
        
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ Resend email sent successfully to {to_email}")
                return {"success": True, "id": response.json().get("id")}
            else:
                error_msg = response.text
                logger.error(f"❌ Resend API error: {response.status_code} - {error_msg}")
                return {"success": False, "error": f"Failed to send: {response.status_code}"}

        except Exception as e:
            logger.error(f"❌ Resend failed to send email to {to_email}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get service configuration status"""
        return {
            "configured": self.is_configured,
            "from_email": self.from_email,
            "api_key_set": bool(self.api_key)
        }