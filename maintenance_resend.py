#!/usr/bin/env python3
"""
SoulBridge AI Enhanced Self-Maintenance System with Resend Email
- Health monitoring every 30 minutes
- Intelligent restart logic with backoff
- GPT-4 log analysis and recommendations
- Professional email alerts via Resend
- Prevents restart loops and excessive API calls
"""

import os
import time
import requests
import subprocess
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuration
CONFIG = {
    "railway": {
        "project_name": "soulbridgeai-unified",
        "api_token": os.getenv("RAILWAY_API_TOKEN"),
        "service_name": "backend"
    },
    "monitoring": {
        "site_url": "https://soulbridgeai-unified-production.up.railway.app/health",
        "check_interval": 1800,  # 30 minutes
        "timeout": 15,
        "max_consecutive_failures": 3,
        "restart_cooldown": 3600  # 1 hour between restarts
    },
    "ai": {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o-mini",  # Cost-effective
        "max_tokens": 500
    },
    "email": {
        "resend_api_key": os.getenv("RESEND_API_KEY"),
        "from_email": os.getenv("MONITOR_FROM_EMAIL", "monitor@soulbridgeai.com"),
        "to_email": os.getenv("MONITOR_TO_EMAIL", "soulbridgeai.contact@gmail.com"),
        "quiet_hours": (23, 7)  # No alerts between 11PM-7AM
    }
}

class SoulBridgeMonitor:
    def __init__(self):
        self.consecutive_failures = 0
        self.last_restart_time = None
        self.startup_time = datetime.utcnow()
        self.total_checks = 0
        self.total_failures = 0
        
    def is_site_healthy(self) -> tuple[bool, str]:
        """Enhanced health check with detailed status"""
        try:
            response = requests.get(
                CONFIG["monitoring"]["site_url"], 
                timeout=CONFIG["monitoring"]["timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                unhealthy_services = [name for name, status in services.items() if not status]
                
                if unhealthy_services:
                    return False, f"Services down: {', '.join(unhealthy_services)}"
                return True, "All services operational"
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"Connection failed: {str(e)[:100]}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)[:100]}"
    
    def should_restart(self) -> bool:
        """Intelligent restart logic with cooldown"""
        if self.consecutive_failures < CONFIG["monitoring"]["max_consecutive_failures"]:
            return False
            
        if self.last_restart_time:
            time_since_restart = datetime.utcnow() - self.last_restart_time
            if time_since_restart.total_seconds() < CONFIG["monitoring"]["restart_cooldown"]:
                return False
                
        return True
    
    def restart_railway(self) -> str:
        """Restart Railway service with improved error handling"""
        try:
            project = CONFIG["railway"]["project_name"]
            service = CONFIG["railway"]["service_name"]
            
            # Use Railway CLI if available
            cmd = f"railway restart --service {service}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.last_restart_time = datetime.utcnow()
                self.consecutive_failures = 0  # Reset failure counter
                return "✅ Restart successful"
            else:
                return f"❌ Restart failed: {result.stderr[:200]}"
                
        except subprocess.TimeoutExpired:
            return "❌ Restart command timed out"
        except Exception as e:
            return f"❌ Restart error: {str(e)[:200]}"
    
    def get_railway_logs(self, lines: int = 100) -> str:
        """Get recent Railway logs"""
        try:
            cmd = f"railway logs --lines {lines}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout[-2000:]  # Last 2KB of logs
            else:
                return f"Failed to fetch logs: {result.stderr[:200]}"
                
        except Exception as e:
            return f"Log fetch error: {str(e)[:200]}"
    
    def analyze_with_gpt(self, logs: str, error_context: str) -> str:
        """GPT-4 analysis with better prompting"""
        try:
            import openai
            client = openai.OpenAI(api_key=CONFIG["ai"]["openai_api_key"])
            
            system_prompt = """You are a DevOps expert analyzing SoulBridge AI application logs. 
            Provide a brief analysis focusing on:
            1. Root cause of the issue
            2. Severity level (Critical/High/Medium/Low)  
            3. Recommended actions
            4. Whether manual intervention is needed
            
            Keep response professional and under 400 words."""
            
            user_prompt = f"""
            Context: {error_context}
            
            Recent logs:
            {logs[-1500:]}
            
            What's wrong and how to fix it?
            """
            
            response = client.chat.completions.create(
                model=CONFIG["ai"]["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=CONFIG["ai"]["max_tokens"],
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"GPT analysis failed: {str(e)[:100]}"
    
    def is_quiet_hours(self) -> bool:
        """Check if we're in quiet hours"""
        current_hour = datetime.utcnow().hour
        start, end = CONFIG["email"]["quiet_hours"]
        
        if start <= end:
            return start <= current_hour < end
        else:  # Crosses midnight
            return current_hour >= start or current_hour < end
    
    def send_email_alert(self, subject: str, message: str, severity: str = "INFO") -> None:
        """Send professional email alerts via Resend"""
        resend_api_key = CONFIG["email"]["resend_api_key"]
        if not resend_api_key:
            print(f"[{severity}] {subject}: {message}")
            return
            
        # Skip non-critical alerts during quiet hours
        if self.is_quiet_hours() and severity in ["INFO", "LOW"]:
            return
        
        # Severity emoji mapping
        severity_icons = {
            "CRITICAL": "🔴",
            "HIGH": "🟠", 
            "MEDIUM": "🟡",
            "LOW": "🔵",
            "INFO": "🟢"
        }
        
        icon = severity_icons.get(severity, "⚪")
        
        # Create HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SoulBridge AI Monitor Alert</title>
            <style>
                body {{
                    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
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
                    padding: 30px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #22d3ee, #0891b2);
                    border-radius: 8px;
                    color: white;
                }}
                .alert-box {{
                    background: #f8fafc;
                    border-left: 4px solid #22d3ee;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .severity-{severity.lower()} {{
                    border-left-color: {'#dc2626' if severity == 'CRITICAL' else '#f59e0b' if severity == 'HIGH' else '#10b981'};
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-item {{
                    background: #f8fafc;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #22d3ee;
                    display: block;
                }}
                .stat-label {{
                    font-size: 0.85rem;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e2e8f0;
                    font-size: 0.85rem;
                    color: #64748b;
                    text-align: center;
                }}
                .timestamp {{
                    color: #64748b;
                    font-size: 0.9rem;
                    margin-bottom: 20px;
                }}
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 6px;
                    overflow-x: auto;
                    font-size: 0.85rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{icon} SoulBridge AI Monitor</h1>
                    <p style="margin: 0; opacity: 0.9;">{subject}</p>
                </div>
                
                <div class="timestamp">
                    <strong>Timestamp:</strong> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                    <br><strong>Severity:</strong> {severity}
                </div>
                
                <div class="alert-box severity-{severity.lower()}">
                    <div style="white-space: pre-wrap;">{message}</div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-number">{self.get_uptime()}</span>
                        <span class="stat-label">Monitor Uptime</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{self.total_checks}</span>
                        <span class="stat-label">Total Checks</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{self.total_failures}</span>
                        <span class="stat-label">Total Failures</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">{self.consecutive_failures}</span>
                        <span class="stat-label">Consecutive Failures</span>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>SoulBridge AI Automated Monitoring System</strong></p>
                    <p>This alert was generated automatically. For complex issues, please involve Claude for deep analysis.</p>
                    <p><em>Monitor configured to check every {CONFIG['monitoring']['check_interval']//60} minutes</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        SoulBridge AI Monitor Alert - {subject}
        
        Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
        Severity: {severity}
        
        {message}
        
        Statistics:
        - Monitor Uptime: {self.get_uptime()}
        - Total Checks: {self.total_checks}
        - Total Failures: {self.total_failures}
        - Consecutive Failures: {self.consecutive_failures}
        
        ---
        SoulBridge AI Automated Monitoring System
        Check interval: {CONFIG['monitoring']['check_interval']//60} minutes
        """
        
        # Send via Resend API
        payload = {
            "from": f"SoulBridge AI Monitor <{CONFIG['email']['from_email']}>",
            "to": [CONFIG["email"]["to_email"]],
            "subject": f"[{severity}] SoulBridge AI: {subject}",
            "html": html_content,
            "text": text_content
        }
        
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Email alert sent: {subject}")
            else:
                print(f"❌ Email failed ({response.status_code}): {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Email send error: {e}")
    
    def get_uptime(self) -> str:
        """Get monitor uptime"""
        uptime = datetime.utcnow() - self.startup_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def run_check(self) -> None:
        """Main monitoring logic"""
        self.total_checks += 1
        
        # Health check
        is_healthy, status_msg = self.is_site_healthy()
        
        if is_healthy:
            if self.consecutive_failures > 0:
                self.send_email_alert(
                    "Site Recovery Confirmed", 
                    f"✅ SoulBridge AI is back online!\n\nStatus: {status_msg}\n\nDowntime resolved after {self.consecutive_failures} failed checks.",
                    "INFO"
                )
            elif self.total_checks % 48 == 1:  # Daily status (every 24 hours)
                self.send_email_alert(
                    "Daily Status Report",
                    f"✅ SoulBridge AI operating normally\n\nStatus: {status_msg}\n\nLast 24 hours: {48 - (self.total_failures % 48)} successful checks",
                    "INFO"
                )
            self.consecutive_failures = 0
            return
        
        # Site is down
        self.consecutive_failures += 1
        self.total_failures += 1
        
        if self.consecutive_failures == 1:
            self.send_email_alert(
                "Site Health Check Failed",
                f"❌ Initial health check failure detected\n\nError: {status_msg}\n\nMonitoring for additional failures before restart...",
                "MEDIUM"
            )
            return
        
        # Multiple failures - consider restart
        if self.should_restart():
            self.send_email_alert(
                "Auto-Restart Initiated",
                f"🔄 Initiating automatic restart after {self.consecutive_failures} consecutive failures\n\nError: {status_msg}\n\nRestart process starting now...",
                "HIGH"
            )
            
            restart_result = self.restart_railway()
            logs = self.get_railway_logs()
            gpt_analysis = self.analyze_with_gpt(logs, status_msg)
            
            # Post-restart analysis email
            analysis_message = f"""
{restart_result}

🧠 AI Analysis:
{gpt_analysis}

📋 Recent Logs:
{logs[-800:] if logs else 'No logs available'}

Next Steps:
- Monitor will continue checking every 30 minutes
- If restart failed, manual intervention may be required
- Complex issues should be escalated to Claude for deep analysis
            """.strip()
            
            severity = "CRITICAL" if "failed" in restart_result.lower() else "HIGH"
            self.send_email_alert(
                "Restart Complete - Analysis Report",
                analysis_message,
                severity
            )
        else:
            # Still failing but not ready to restart
            reason = "Recently restarted" if self.last_restart_time else "Not enough consecutive failures yet"
            self.send_email_alert(
                "Continued Health Check Failures",
                f"❌ Failure #{self.consecutive_failures}: {status_msg}\n\nRestart Status: {reason}\n\nWill attempt restart after {CONFIG['monitoring']['max_consecutive_failures']} consecutive failures.",
                "MEDIUM"
            )
    
    def start_monitoring(self) -> None:
        """Start the monitoring loop"""
        self.send_email_alert(
            "Monitoring System Started",
            f"""🚀 SoulBridge AI monitoring system is now active

Configuration:
- Check interval: {CONFIG['monitoring']['check_interval']//60} minutes  
- Health endpoint: {CONFIG['monitoring']['site_url']}
- Auto-restart threshold: {CONFIG['monitoring']['max_consecutive_failures']} failures
- Restart cooldown: {CONFIG['monitoring']['restart_cooldown']//60} minutes

The system will:
✅ Monitor site health every 30 minutes
🔄 Auto-restart after 3 consecutive failures  
🧠 Analyze logs with GPT-4 when issues occur
📧 Send alerts via professional email notifications
⏰ Respect quiet hours ({CONFIG['email']['quiet_hours'][0]}:00-{CONFIG['email']['quiet_hours'][1]}:00 UTC)

Monitoring begins now...""",
            "INFO"
        )
        
        while True:
            try:
                self.run_check()
                time.sleep(CONFIG["monitoring"]["check_interval"])
            except KeyboardInterrupt:
                self.send_email_alert(
                    "Monitoring System Stopped",
                    f"⏹️ SoulBridge AI monitoring was stopped manually\n\nUptime: {self.get_uptime()}\nTotal checks performed: {self.total_checks}",
                    "INFO"
                )
                break
            except Exception as e:
                self.send_email_alert(
                    "Monitor System Error",
                    f"⚠️ The monitoring system encountered an error: {str(e)[:300]}\n\nThe monitor will restart automatically in 60 seconds...",
                    "MEDIUM"
                )
                time.sleep(60)  # Wait 1 minute before continuing

if __name__ == "__main__":
    # Validate configuration
    required_env_vars = ["RAILWAY_API_TOKEN", "RESEND_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    print("🤖 Starting SoulBridge AI Enhanced Monitor with Resend Email...")
    monitor = SoulBridgeMonitor()
    monitor.start_monitoring()