"""
SoulBridge AI - System Monitor
Background monitoring, surveillance, and alerting system
Extracted from backend/app.py with improvements
"""
import logging
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Background system monitoring and surveillance with threat detection"""
    
    def __init__(self, health_checker=None):
        self.health_checker = health_checker
        self.system_start_time = datetime.now(timezone.utc)
        self.blocked_ips = set()
        self.security_threats = []
        self.maintenance_log = []
        self.emergency_mode = False
        self.critical_errors_count = 0
        self.watchdog_enabled = True
        self.last_health_check = datetime.now(timezone.utc)
        self.last_cleanup = datetime.now(timezone.utc)
        
        # Monitoring configuration
        self.config = {
            'health_check_interval': 300,     # 5 minutes
            'cleanup_interval': 21600,        # 6 hours
            'log_rotation_size': 100 * 1024,  # 100KB
            'max_log_lines': 1000,
            'threat_retention_hours': 24,
            'maintenance_retention_days': 7
        }
        
        # File paths
        self.log_files = {
            'maintenance': 'logs/maintenance_log.txt',
            'threats': 'logs/threat_log.txt',
            'traps': 'logs/trap_log.txt',
            'system': 'logs/system_monitor.txt'
        }
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Alert thresholds
        self.alert_thresholds = {
            'failed_logins_per_hour': 10,
            'error_rate_per_minute': 5,
            'response_time_threshold': 5.0,
            'memory_usage_critical': 90,
            'disk_usage_critical': 95
        }
        
        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_active = False
        
        self.log_maintenance("SYSTEM_START", "System monitor initialized")
        logger.info("👁️ System monitor initialized")
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        try:
            if self.monitoring_active:
                logger.warning("Monitoring already active")
                return False
            
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, 
                daemon=True,
                name="SystemMonitor"
            )
            self.monitoring_thread.start()
            
            self.log_maintenance("MONITOR_START", "Background monitoring started")
            logger.info("👁️ Background monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self.log_maintenance("MONITOR_START_ERROR", f"Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.log_maintenance("MONITOR_STOP", "Background monitoring stopped")
            logger.info("👁️ Background monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            self.log_maintenance("MONITOR_STOP_ERROR", f"Error stopping monitoring: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("👁️ Starting monitoring loop")
        
        while self.monitoring_active:
            try:
                # Perform health check
                if self.health_checker:
                    self._perform_health_check()
                else:
                    self._basic_health_check()
                
                # Clean up old data periodically
                current_time = datetime.now(timezone.utc)
                time_since_cleanup = (current_time - self.last_cleanup).total_seconds()
                
                if time_since_cleanup > self.config['cleanup_interval']:
                    self._perform_cleanup()
                    self.last_cleanup = current_time
                
                # Sleep before next check
                time.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                self.log_maintenance("MONITOR_ERROR", f"Monitoring loop error: {e}")
                # Sleep for shorter interval on error to prevent rapid failures
                time.sleep(60)
    
    def _perform_health_check(self):
        """Perform comprehensive health check using health checker"""
        try:
            health_status = self.health_checker.get_system_health()
            self.last_health_check = datetime.now(timezone.utc)
            
            # Log health status
            overall_status = health_status.get('overall_status', 'unknown')
            uptime = health_status.get('uptime_seconds', 0)
            
            self.log_maintenance(
                "HEALTH_CHECK", 
                f"Status: {overall_status}, Uptime: {uptime//3600:.1f}h"
            )
            
            # Check for alerts
            alerts = health_status.get('alerts', [])
            for alert in alerts:
                self._handle_alert(alert)
            
            # Log periodic status
            if uptime % 3600 == 0 and uptime > 0:  # Every hour
                self._log_periodic_status(health_status)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.log_maintenance("HEALTH_CHECK_ERROR", f"Health check failed: {e}")
    
    def _basic_health_check(self):
        """Basic health check when full health checker unavailable"""
        try:
            self.last_health_check = datetime.now(timezone.utc)
            uptime_hours = (datetime.now(timezone.utc) - self.system_start_time).total_seconds() / 3600
            
            # Log basic health status every hour
            if int(uptime_hours) % 1 == 0:
                self.log_maintenance("HEALTH_CHECK", f"Basic check: System running for {uptime_hours:.1f} hours")
            
        except Exception as e:
            logger.error(f"Basic health check error: {e}")
            self.log_maintenance("HEALTH_CHECK_ERROR", f"Basic health check failed: {e}")
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """Handle system alert"""
        try:
            service = alert.get('service', 'unknown')
            message = alert.get('message', 'Unknown alert')
            severity = alert.get('severity', 'info')
            
            # Log alert
            alert_entry = f"ALERT [{severity.upper()}] {service}: {message}"
            self.log_maintenance("ALERT", alert_entry)
            
            # Take action based on severity
            if severity == 'critical':
                self._handle_critical_alert(alert)
            elif severity == 'warning':
                self._handle_warning_alert(alert)
            
            # Record as threat if security-related
            if service in ['security', 'auth', 'admin']:
                self._record_security_threat(alert)
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
    
    def _handle_critical_alert(self, alert: Dict[str, Any]):
        """Handle critical system alert"""
        try:
            self.critical_errors_count += 1
            
            # Log critical alert
            self.log_threat(
                "CRITICAL_ALERT", 
                f"Service: {alert.get('service')}, Message: {alert.get('message')}"
            )
            
            # Enable emergency mode if too many critical errors
            if self.critical_errors_count > 5:
                self.emergency_mode = True
                self.log_maintenance("EMERGENCY_MODE", "Emergency mode activated due to critical errors")
            
        except Exception as e:
            logger.error(f"Error handling critical alert: {e}")
    
    def _handle_warning_alert(self, alert: Dict[str, Any]):
        """Handle warning alert"""
        try:
            # Log warning
            self.log_maintenance(
                "WARNING", 
                f"Service: {alert.get('service')}, Message: {alert.get('message')}"
            )
            
        except Exception as e:
            logger.error(f"Error handling warning alert: {e}")
    
    def _record_security_threat(self, threat: Dict[str, Any]):
        """Record security threat"""
        try:
            threat_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': threat.get('service', 'unknown'),
                'message': threat.get('message', 'Unknown threat'),
                'severity': threat.get('severity', 'info'),
                'source_ip': threat.get('source_ip', 'unknown')
            }
            
            self.security_threats.append(threat_record)
            
            # Log to threat file
            self.log_threat(
                "SECURITY_THREAT",
                f"{threat_record['service']}: {threat_record['message']}"
            )
            
            # Trim old threats
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.config['threat_retention_hours'])
            self.security_threats = [
                t for t in self.security_threats
                if datetime.fromisoformat(t['timestamp']) > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error recording security threat: {e}")
    
    def _log_periodic_status(self, health_status: Dict[str, Any]):
        """Log periodic system status summary"""
        try:
            services = health_status.get('services', {})
            healthy_services = sum(1 for s in services.values() if s.get('healthy', False))
            total_services = len(services)
            
            status_summary = (
                f"Periodic Status: {healthy_services}/{total_services} services healthy, "
                f"{len(health_status.get('alerts', []))} alerts, "
                f"Uptime: {health_status.get('uptime_seconds', 0)//3600}h"
            )
            
            self.log_maintenance("PERIODIC_STATUS", status_summary)
            
        except Exception as e:
            logger.error(f"Error logging periodic status: {e}")
    
    def _perform_cleanup(self):
        """Perform periodic cleanup of logs and old data"""
        try:
            self.log_maintenance("CLEANUP_START", "Starting periodic cleanup")
            
            # Rotate large log files
            for log_name, log_path in self.log_files.items():
                if os.path.exists(log_path):
                    file_size = os.path.getsize(log_path)
                    if file_size > self.config['log_rotation_size']:
                        self._rotate_log_file(log_path)
            
            # Clean old maintenance logs
            self._cleanup_maintenance_logs()
            
            # Clean old security threats (already done in _record_security_threat)
            
            self.log_maintenance("CLEANUP_COMPLETE", "Periodic cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            self.log_maintenance("CLEANUP_ERROR", f"Cleanup failed: {e}")
    
    def _rotate_log_file(self, filename: str):
        """Rotate log file to prevent excessive size"""
        try:
            if not os.path.exists(filename):
                return
            
            # Keep only the last N lines
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if len(lines) > self.config['max_log_lines']:
                # Keep last max_log_lines
                lines = lines[-self.config['max_log_lines']:]
                
                # Write back to file
                with open(filename, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                
                self.log_maintenance("LOG_ROTATED", f"Rotated log file: {filename}")
                
        except Exception as e:
            logger.error(f"Error rotating log file {filename}: {e}")
    
    def _cleanup_maintenance_logs(self):
        """Clean up old maintenance log entries"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config['maintenance_retention_days'])
            
            # Filter maintenance logs
            original_count = len(self.maintenance_log)
            self.maintenance_log = [
                entry for entry in self.maintenance_log
                if entry.get('timestamp') and 
                datetime.fromisoformat(entry['timestamp']) > cutoff_date
            ]
            
            cleaned_count = original_count - len(self.maintenance_log)
            if cleaned_count > 0:
                self.log_maintenance("LOG_CLEANUP", f"Removed {cleaned_count} old maintenance log entries")
            
        except Exception as e:
            logger.error(f"Error cleaning maintenance logs: {e}")
    
    def log_maintenance(self, event_type: str, message: str):
        """Log maintenance event"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            entry = f"[{timestamp}] {event_type}: {message}"
            
            # Add to memory log
            log_entry = {
                'timestamp': timestamp,
                'event_type': event_type,
                'message': message
            }
            self.maintenance_log.append(log_entry)
            
            # Write to file
            self._write_to_log_file(self.log_files['maintenance'], entry)
            
        except Exception as e:
            # Use basic logging for maintenance system errors
            logger.error(f"Failed to log maintenance event: {e}")
    
    def log_threat(self, threat_type: str, message: str):
        """Log security threat"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            entry = f"[{timestamp}] {threat_type}: {message}"
            
            # Write to threat log file
            self._write_to_log_file(self.log_files['threats'], entry)
            
        except Exception as e:
            logger.error(f"Failed to log threat: {e}")
    
    def _write_to_log_file(self, log_file: str, entry: str):
        """Write entry to log file with error handling"""
        try:
            # Check if file exists and its size
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                # Rotate log if it exceeds size limit
                if file_size > self.config['log_rotation_size']:
                    self._rotate_log_file(log_file)
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write to log {log_file}: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            uptime_seconds = (datetime.now(timezone.utc) - self.system_start_time).total_seconds()
            
            return {
                'uptime_seconds': int(uptime_seconds),
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'monitoring_active': self.monitoring_active,
                'blocked_ips_count': len(self.blocked_ips),
                'security_threats_count': len(self.security_threats),
                'maintenance_logs_count': len(self.maintenance_log),
                'critical_errors_count': self.critical_errors_count,
                'emergency_mode': self.emergency_mode,
                'watchdog_enabled': self.watchdog_enabled,
                'last_health_check': self.last_health_check.isoformat(),
                'last_cleanup': self.last_cleanup.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and recent threats"""
        try:
            # Recent threats (last 24 hours)
            recent_threats = self.security_threats[-10:] if self.security_threats else []
            
            # Threat counts by severity
            threat_counts = {'critical': 0, 'warning': 0, 'info': 0}
            for threat in self.security_threats:
                severity = threat.get('severity', 'info')
                if severity in threat_counts:
                    threat_counts[severity] += 1
            
            # Blocked IPs summary
            blocked_ips_list = list(self.blocked_ips)
            
            return {
                'total_threats': len(self.security_threats),
                'recent_threats': recent_threats,
                'threat_counts': threat_counts,
                'blocked_ips': blocked_ips_list,
                'blocked_ips_count': len(blocked_ips_list),
                'emergency_mode': self.emergency_mode,
                'critical_errors_count': self.critical_errors_count
            }
            
        except Exception as e:
            logger.error(f"Error getting security summary: {e}")
            return {'error': str(e)}
    
    def get_maintenance_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent maintenance logs"""
        try:
            return self.maintenance_log[-limit:] if self.maintenance_log else []
        except Exception as e:
            logger.error(f"Error getting maintenance logs: {e}")
            return []
    
    def block_ip(self, ip_address: str, reason: str = "Security violation"):
        """Block an IP address"""
        try:
            self.blocked_ips.add(ip_address)
            self.log_threat("IP_BLOCKED", f"Blocked IP {ip_address}: {reason}")
            logger.warning(f"🚫 Blocked IP {ip_address}: {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        try:
            if ip_address in self.blocked_ips:
                self.blocked_ips.remove(ip_address)
                self.log_maintenance("IP_UNBLOCKED", f"Unblocked IP {ip_address}")
                logger.info(f"✅ Unblocked IP {ip_address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unblocking IP {ip_address}: {e}")
            return False
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def enable_emergency_mode(self, reason: str = "Manual activation"):
        """Enable emergency mode"""
        try:
            self.emergency_mode = True
            self.log_threat("EMERGENCY_MODE_ENABLED", f"Emergency mode enabled: {reason}")
            logger.critical(f"🚨 Emergency mode enabled: {reason}")
            
        except Exception as e:
            logger.error(f"Error enabling emergency mode: {e}")
    
    def disable_emergency_mode(self):
        """Disable emergency mode"""
        try:
            self.emergency_mode = False
            self.critical_errors_count = 0  # Reset error count
            self.log_maintenance("EMERGENCY_MODE_DISABLED", "Emergency mode disabled")
            logger.info("✅ Emergency mode disabled")
            
        except Exception as e:
            logger.error(f"Error disabling emergency mode: {e}")
    
    def record_login_attempt(self, email: str, ip_address: str, success: bool, user_agent: str = ""):
        """Record login attempt for monitoring"""
        try:
            attempt_type = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
            message = f"User: {email}, IP: {ip_address}, UA: {user_agent[:100]}"
            
            if success:
                self.log_maintenance(attempt_type, message)
            else:
                self.log_threat(attempt_type, message)
            
            # Check for brute force attempts
            if not success:
                self._check_brute_force_attempts(ip_address)
            
        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
    
    def _check_brute_force_attempts(self, ip_address: str):
        """Check for brute force login attempts"""
        try:
            # Count recent failed attempts from this IP
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            # This is a simplified check - in production, you'd want to
            # maintain a more sophisticated tracking system
            recent_failures = sum(
                1 for threat in self.security_threats
                if (threat.get('source_ip') == ip_address and
                    'LOGIN_FAILED' in threat.get('message', '') and
                    datetime.fromisoformat(threat['timestamp']) > cutoff_time)
            )
            
            if recent_failures >= self.alert_thresholds['failed_logins_per_hour']:
                self.block_ip(ip_address, f"Brute force: {recent_failures} failed logins")
                
        except Exception as e:
            logger.error(f"Error checking brute force attempts: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        try:
            return {
                'monitoring_active': self.monitoring_active,
                'thread_alive': self.monitoring_thread.is_alive() if self.monitoring_thread else False,
                'last_health_check': self.last_health_check.isoformat(),
                'watchdog_enabled': self.watchdog_enabled,
                'emergency_mode': self.emergency_mode,
                'uptime_hours': round((datetime.now(timezone.utc) - self.system_start_time).total_seconds() / 3600, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {'error': str(e)}
    
    def reset_monitoring(self):
        """Reset monitoring state (for debugging)"""
        try:
            self.critical_errors_count = 0
            self.emergency_mode = False
            self.blocked_ips.clear()
            self.security_threats.clear()
            
            self.log_maintenance("MONITOR_RESET", "Monitoring state reset")
            logger.info("🔄 Monitoring state reset")
            
        except Exception as e:
            logger.error(f"Error resetting monitoring: {e}")