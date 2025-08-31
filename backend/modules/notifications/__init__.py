"""
SoulBridge AI - Notifications Module
Complete email and notification system extracted from monolith
Handles welcome emails, password resets, contact forms, and notifications
"""

from .email_service import EmailService
from .resend_service import ResendService
from .templates import EmailTemplates
from .routes import notifications_bp, send_trial_warning_email, send_simple_email

__all__ = [
    'EmailService',
    'ResendService', 
    'EmailTemplates',
    'notifications_bp',
    'send_trial_warning_email',
    'send_simple_email'
]