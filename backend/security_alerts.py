"""
Security Alert System for SoulBridge AI
Sends automated notifications for security events
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from email_service import EmailService

logger = logging.getLogger(__name__)


class SecurityAlertManager:
    """Manages security alerts and notifications"""

    def __init__(self):
        self.email_service = None
        self.alert_thresholds = {
            "critical": 1,  # Send alert immediately
            "high": 3,  # Send alert after 3 events
            "medium": 10,  # Send alert after 10 events
            "low": 50,  # Send alert after 50 events
        }
        self.alert_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        self.last_alert_time = {}
        self.min_alert_interval = 300  # 5 minutes between alerts of same type

        # Initialize email service if available
        try:
            self.email_service = EmailService()
            logger.info("Security alert manager initialized with email service")
        except Exception as e:
            logger.warning(f"Email service not available for security alerts: {e}")

    def should_send_alert(self, severity: str) -> bool:
        """Determine if an alert should be sent based on severity and frequency"""
        self.alert_counts[severity] += 1

        # Check if we've reached the threshold
        if self.alert_counts[severity] < self.alert_thresholds[severity]:
            return False

        # Check minimum interval
        last_alert = self.last_alert_time.get(severity, 0)
        current_time = datetime.utcnow().timestamp()

        if current_time - last_alert < self.min_alert_interval:
            return False

        # Reset counter and update last alert time
        self.alert_counts[severity] = 0
        self.last_alert_time[severity] = current_time

        return True

    def send_security_alert(self, title: str, details: Dict, severity: str = "medium"):
        """Send security alert notification"""
        if not self.should_send_alert(severity):
            return

        try:
            # Format alert message
            alert_message = self._format_alert_message(title, details, severity)

            # Send email alert
            if self.email_service:
                self._send_email_alert(title, alert_message, severity)

            # Log the alert
            logger.critical(f"SECURITY ALERT SENT: {title}")

            # You could add more notification channels here:
            # - Slack webhook
            # - Discord webhook
            # - SMS alerts
            # - Push notifications

        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")

    def _format_alert_message(self, title: str, details: Dict, severity: str) -> str:
        """Format security alert message"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        message = f"""
🛡️ SOULBRIDGE AI SECURITY ALERT

Severity: {severity.upper()}
Time: {timestamp}
Alert: {title}

Details:
"""

        for key, value in details.items():
            if key not in ["user_agent", "referrer"]:  # Skip potentially long fields
                message += f"  {key}: {value}\n"

        message += f"""
This is an automated security alert from SoulBridge AI.
Please investigate this activity immediately.

Security Dashboard: https://your-domain.com/admin/security
        """

        return message

    def _send_email_alert(self, title: str, message: str, severity: str):
        """Send email security alert"""
        if not self.email_service:
            return

        # Determine email subject based on severity
        severity_icons = {"critical": "🚨", "high": "⚠️", "medium": "🔍", "low": "ℹ️"}

        icon = severity_icons.get(severity, "🔍")
        subject = f"{icon} Security Alert: {title}"

        # Get admin email from environment
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@yourdomain.com")

        try:
            # Send alert email
            success = self.email_service.send_email(
                to_email=admin_email,
                subject=subject,
                html_content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px;">
                    <div style="background: #f44336; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                        <h1 style="margin: 0;">{icon} Security Alert</h1>
                        <p style="margin: 10px 0 0 0;">SoulBridge AI Security System</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px;">
                        <h2>Alert: {title}</h2>
                        <p><strong>Severity:</strong> <span style="color: #f44336; font-weight: bold;">{severity.upper()}</span></p>
                        <p><strong>Time:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
                        
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <pre style="white-space: pre-wrap; margin: 0;">{message}</pre>
                        </div>
                        
                        <div style="margin-top: 20px;">
                            <a href="https://your-domain.com/admin/security" 
                               style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                                View Security Dashboard
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content=message,
            )

            if success:
                logger.info(f"Security alert email sent to {admin_email}")
            else:
                logger.error("Failed to send security alert email")

        except Exception as e:
            logger.error(f"Error sending security alert email: {e}")

    def send_ip_blocked_alert(self, ip: str, reason: str, threat_count: int):
        """Send alert when an IP is blocked"""
        details = {
            "blocked_ip": ip,
            "reason": reason,
            "threat_count": threat_count,
            "action_taken": "IP automatically blocked",
            "block_duration": "1 hour",
        }

        self.send_security_alert(
            title=f"IP Address Blocked: {ip}", details=details, severity="high"
        )

    def send_attack_pattern_alert(
        self, ip: str, attack_type: str, endpoint: str, user_agent: str
    ):
        """Send alert for detected attack patterns"""
        details = {
            "source_ip": ip,
            "attack_type": attack_type,
            "target_endpoint": endpoint,
            "user_agent": (
                user_agent[:100] + "..." if len(user_agent) > 100 else user_agent
            ),
            "recommended_action": "Review and consider blocking IP",
        }

        self.send_security_alert(
            title=f"Attack Pattern Detected: {attack_type}",
            details=details,
            severity="high",
        )

    def send_mass_scan_alert(self, ip: str, scan_count: int, scan_type: str):
        """Send alert for mass scanning activity"""
        details = {
            "source_ip": ip,
            "scan_type": scan_type,
            "scan_count": scan_count,
            "time_window": "5 minutes",
            "recommended_action": "IP will be auto-blocked if scanning continues",
        }

        severity = "critical" if scan_count > 20 else "high"

        self.send_security_alert(
            title=f"Mass {scan_type} Detected", details=details, severity=severity
        )

    def send_daily_security_summary(self, stats: Dict):
        """Send daily security summary email"""
        if not self.email_service:
            return

        try:
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@yourdomain.com")
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

            summary_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px;">
                <div style="background: #2196F3; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h1 style="margin: 0;">🛡️ Daily Security Summary</h1>
                    <p style="margin: 10px 0 0 0;">SoulBridge AI - {date_str}</p>
                </div>
                
                <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px;">
                    <h2>Security Statistics</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                            <div style="font-size: 2em; font-weight: bold; color: #f44336;">{stats.get('total_blocked_ips', 0)}</div>
                            <div>Blocked IPs</div>
                        </div>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                            <div style="font-size: 2em; font-weight: bold; color: #ff9800;">{stats.get('total_threats_detected', 0)}</div>
                            <div>Threats Detected</div>
                        </div>
                    </div>
                    
                    <h3>Top Threat Sources</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            """

            top_threats = stats.get("top_threat_ips", [])[:5]
            if top_threats:
                for ip, count in top_threats:
                    summary_html += f"<div>{ip}: {count} threats</div>"
            else:
                summary_html += "<div>No significant threat activity</div>"

            summary_html += """
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <a href="https://your-domain.com/admin/security" 
                           style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            View Full Security Dashboard
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """

            success = self.email_service.send_email(
                to_email=admin_email,
                subject=f"🛡️ Daily Security Summary - {date_str}",
                html_content=summary_html,
                text_content=f"Daily Security Summary for {date_str}\n\nBlocked IPs: {stats.get('total_blocked_ips', 0)}\nThreats Detected: {stats.get('total_threats_detected', 0)}",
            )

            if success:
                logger.info("Daily security summary sent")

        except Exception as e:
            logger.error(f"Failed to send daily security summary: {e}")


# Global security alert manager
security_alert_manager = SecurityAlertManager()


def send_security_alert(title: str, details: Dict, severity: str = "medium"):
    """Send security alert (convenience function)"""
    security_alert_manager.send_security_alert(title, details, severity)


def send_ip_blocked_alert(ip: str, reason: str, threat_count: int = 0):
    """Send IP blocked alert (convenience function)"""
    security_alert_manager.send_ip_blocked_alert(ip, reason, threat_count)


def send_attack_pattern_alert(
    ip: str, attack_type: str, endpoint: str, user_agent: str = ""
):
    """Send attack pattern alert (convenience function)"""
    security_alert_manager.send_attack_pattern_alert(
        ip, attack_type, endpoint, user_agent
    )
