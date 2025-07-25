#!/usr/bin/env python3
"""
SoulBridgeAI Enhanced Self-Maintenance System
- Health monitoring every 30 minutes
- Intelligent restart logic with backoff
- GPT-4 log analysis and recommendations
- Discord alerts with severity levels
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
        "model": "gpt-4o-mini",  # More cost-effective
        "max_tokens": 500
    },
    "alerts": {
        "discord_webhook": os.getenv("DISCORD_WEBHOOK"),
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
            
            Keep response under 400 characters for Discord."""
            
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
        start, end = CONFIG["alerts"]["quiet_hours"]
        
        if start <= end:
            return start <= current_hour < end
        else:  # Crosses midnight
            return current_hour >= start or current_hour < end
    
    def send_discord_alert(self, title: str, message: str, severity: str = "INFO") -> None:
        """Enhanced Discord notifications"""
        webhook_url = CONFIG["alerts"]["discord_webhook"]
        if not webhook_url:
            print(f"[{severity}] {title}: {message}")
            return
            
        # Skip non-critical alerts during quiet hours
        if self.is_quiet_hours() and severity in ["INFO", "LOW"]:
            return
            
        # Color coding
        colors = {
            "CRITICAL": 0xFF0000,  # Red
            "HIGH": 0xFF6600,      # Orange  
            "MEDIUM": 0xFFCC00,    # Yellow
            "LOW": 0x0099FF,       # Blue
            "INFO": 0x00FF00       # Green
        }
        
        embed = {
            "title": f"🤖 SoulBridge AI Monitor - {title}",
            "description": message,
            "color": colors.get(severity, 0x808080),
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Stats",
                    "value": f"Uptime: {self.get_uptime()}\nChecks: {self.total_checks}\nFailures: {self.total_failures}",
                    "inline": True
                }
            ]
        }
        
        payload = {"embeds": [embed]}
        
        try:
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Discord notification failed: {e}")
    
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
                self.send_discord_alert(
                    "Recovery Confirmed", 
                    f"✅ Site is back online! {status_msg}",
                    "INFO"
                )
            self.consecutive_failures = 0
            return
        
        # Site is down
        self.consecutive_failures += 1
        self.total_failures += 1
        
        if self.consecutive_failures == 1:
            self.send_discord_alert(
                "Site Down Detected",
                f"❌ Health check failed: {status_msg}\nMonitoring...",
                "MEDIUM"
            )
            return
        
        # Multiple failures - consider restart
        if self.should_restart():
            self.send_discord_alert(
                "Auto-Restart Initiated",
                f"🔄 {self.consecutive_failures} consecutive failures. Restarting service...",
                "HIGH"
            )
            
            restart_result = self.restart_railway()
            logs = self.get_railway_logs()
            gpt_analysis = self.analyze_with_gpt(logs, status_msg)
            
            self.send_discord_alert(
                "Restart Complete + Analysis",
                f"{restart_result}\n\n🧠 **AI Analysis:**\n{gpt_analysis}",
                "CRITICAL" if "failed" in restart_result.lower() else "HIGH"
            )
        else:
            # Still failing but not ready to restart
            reason = "Recently restarted" if self.last_restart_time else "Not enough failures yet"
            self.send_discord_alert(
                "Continued Failure",
                f"❌ Failure #{self.consecutive_failures}: {status_msg}\n({reason})",
                "MEDIUM"
            )
    
    def start_monitoring(self) -> None:
        """Start the monitoring loop"""
        self.send_discord_alert(
            "Monitor Started",
            f"🚀 SoulBridge AI monitoring started\nCheck interval: {CONFIG['monitoring']['check_interval']//60} minutes",
            "INFO"
        )
        
        while True:
            try:
                self.run_check()
                time.sleep(CONFIG["monitoring"]["check_interval"])
            except KeyboardInterrupt:
                self.send_discord_alert(
                    "Monitor Stopped",
                    f"⏹️ Monitoring stopped manually\nUptime: {self.get_uptime()}",
                    "INFO"
                )
                break
            except Exception as e:
                self.send_discord_alert(
                    "Monitor Error",
                    f"⚠️ Monitor encountered error: {str(e)[:200]}\nRestarting monitor...",
                    "MEDIUM"
                )
                time.sleep(60)  # Wait 1 minute before continuing

if __name__ == "__main__":
    # Validate configuration
    required_env_vars = ["RAILWAY_API_TOKEN", "DISCORD_WEBHOOK", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    print("🤖 Starting SoulBridge AI Enhanced Monitor...")
    monitor = SoulBridgeMonitor()
    monitor.start_monitoring()