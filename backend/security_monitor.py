"""
Advanced Security Monitoring System for SoulBridge AI
Detects and blocks malicious requests, attack patterns, and bot traffic
"""

import os
import time
import json
import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from flask import request, jsonify, g
from dataclasses import dataclass, asdict

# Make Redis optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import security alerts with lazy loading to avoid circular imports
def _get_alert_functions():
    """Lazy load alert functions to avoid circular imports"""
    try:
        from security_alerts import send_security_alert, send_ip_blocked_alert, send_attack_pattern_alert
        return send_security_alert, send_ip_blocked_alert, send_attack_pattern_alert
    except ImportError:
        # Fallback functions if security_alerts not available
        def noop(*args, **kwargs): pass
        return noop, noop, noop

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: datetime
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    threat_type: str
    severity: str  # low, medium, high, critical
    details: Dict
    blocked: bool = False
    
    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

class ThreatDetector:
    """Detects various types of threats and attacks"""
    
    # WordPress vulnerability scan patterns
    WORDPRESS_PATTERNS = [
        r'/wp-admin/',
        r'/wp-content/',
        r'/wp-includes/',
        r'/wordpress/',
        r'wp-config\.php',
        r'wp-login\.php',
        r'setup-config\.php'
    ]
    
    # Common attack patterns
    ATTACK_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'<script',  # XSS attempts
        r'union.*select',  # SQL injection
        r'exec\(',  # Command injection
        r'base64_decode',  # Malicious PHP
        r'eval\(',  # Code execution
        r'/etc/passwd',  # File inclusion
        r'cmd\.exe',  # Windows command execution
        r'powershell',  # PowerShell execution
    ]
    
    # Bot user agent patterns
    BOT_PATTERNS = [
        r'bot',
        r'crawler',
        r'spider',
        r'scraper',
        r'curl',
        r'wget',
        r'python-requests',
        r'go-http-client',
        r'Scanner',
        r'Nmap',
        r'sqlmap',
        r'Nikto'
    ]
    
    # Suspicious file extensions
    SUSPICIOUS_EXTENSIONS = [
        '.php', '.asp', '.aspx', '.jsp', '.cgi', '.pl', '.py',
        '.exe', '.bat', '.sh', '.cmd'
    ]
    
    def __init__(self):
        self.wordpress_regex = re.compile('|'.join(self.WORDPRESS_PATTERNS), re.IGNORECASE)
        self.attack_regex = re.compile('|'.join(self.ATTACK_PATTERNS), re.IGNORECASE)
        self.bot_regex = re.compile('|'.join(self.BOT_PATTERNS), re.IGNORECASE)
    
    def detect_wordpress_scan(self, path: str) -> bool:
        """Detect WordPress vulnerability scans"""
        return bool(self.wordpress_regex.search(path))
    
    def detect_attack_pattern(self, path: str, query: str = "") -> bool:
        """Detect common attack patterns in URL"""
        full_url = f"{path}?{query}"
        return bool(self.attack_regex.search(full_url))
    
    def detect_bot_user_agent(self, user_agent: str) -> bool:
        """Detect bot user agents"""
        return bool(self.bot_regex.search(user_agent))
    
    def detect_suspicious_extension(self, path: str) -> bool:
        """Detect suspicious file extensions"""
        return any(path.lower().endswith(ext) for ext in self.SUSPICIOUS_EXTENSIONS)
    
    def analyze_request(self, request_data: Dict) -> List[str]:
        """Analyze request and return list of detected threats"""
        threats = []
        
        path = request_data.get('path', '')
        query = request_data.get('query', '')
        user_agent = request_data.get('user_agent', '')
        
        if self.detect_wordpress_scan(path):
            threats.append('wordpress_scan')
        
        if self.detect_attack_pattern(path, query):
            threats.append('attack_pattern')
        
        if self.detect_bot_user_agent(user_agent):
            threats.append('bot_detected')
        
        if self.detect_suspicious_extension(path):
            threats.append('suspicious_file')
        
        return threats

class SecurityMonitor:
    """Main security monitoring system"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_store = defaultdict(lambda: defaultdict(list))
        self.blocked_ips = set()
        self.threat_detector = ThreatDetector()
        
        # Rate limiting windows
        self.ip_request_windows = defaultdict(lambda: deque())
        self.ip_threat_counts = defaultdict(int)
        
        # Configuration
        self.max_requests_per_minute = 60
        self.max_threats_before_block = 3
        self.block_duration = 3600  # 1 hour
        self.enable_auto_blocking = True
        
        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                logger.info("Security monitor using Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory backend: {e}")
                self.redis_client = None
        else:
            if not REDIS_AVAILABLE:
                logger.info("Redis not available, using memory backend for security monitoring")
            else:
                logger.info("No Redis URL provided, using memory backend for security monitoring")
    
    def _get_client_ip(self) -> str:
        """Get real client IP address"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def _get_request_data(self) -> Dict:
        """Extract request data for analysis"""
        return {
            'timestamp': datetime.utcnow(),
            'ip_address': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'method': request.method,
            'path': request.path,
            'query': request.query_string.decode('utf-8'),
            'referrer': request.headers.get('Referer', ''),
            'content_type': request.headers.get('Content-Type', '')
        }
    
    def _is_whitelisted_ip(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        # Add your whitelist logic here
        whitelist = [
            '127.0.0.1',
            '::1',
            # Add your server IPs, CDN IPs, etc.
        ]
        return ip in whitelist
    
    def _should_block_ip(self, ip: str) -> bool:
        """Determine if IP should be blocked"""
        if self._is_whitelisted_ip(ip):
            return False
        
        # Check if already blocked
        if ip in self.blocked_ips:
            return True
        
        # Check threat count
        if self.ip_threat_counts[ip] >= self.max_threats_before_block:
            return True
        
        # Check request rate
        now = time.time()
        window = self.ip_request_windows[ip]
        
        # Remove old requests (older than 1 minute)
        while window and window[0] < now - 60:
            window.popleft()
        
        # Check if too many requests
        if len(window) >= self.max_requests_per_minute:
            return True
        
        return False
    
    def _block_ip(self, ip: str, reason: str):
        """Block an IP address"""
        if not self.enable_auto_blocking or self._is_whitelisted_ip(ip):
            return
        
        self.blocked_ips.add(ip)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"blocked_ip:{ip}", 
                    self.block_duration, 
                    json.dumps({
                        'reason': reason,
                        'blocked_at': datetime.utcnow().isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"Failed to store blocked IP in Redis: {e}")
        
        logger.warning(f"Blocked IP {ip} for {reason}")
        
        # Send security alert
        threat_count = self.ip_threat_counts.get(ip, 0)
        send_security_alert, send_ip_blocked_alert, send_attack_pattern_alert = _get_alert_functions()
        send_ip_blocked_alert(ip, reason, threat_count)
    
    def _send_security_alert(self, title: str, details: Dict):
        """Send security alert notification"""
        try:
            # You can integrate with email, Slack, Discord, etc.
            logger.critical(f"SECURITY ALERT: {title} - {details}")
            
            # If you have email service configured
            # email_service = EmailService()
            # email_service.send_security_alert(title, details)
            
        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")
    
    def analyze_request(self) -> Optional[SecurityEvent]:
        """Analyze current request for threats"""
        request_data = self._get_request_data()
        ip = request_data['ip_address']
        
        # Track request timing
        now = time.time()
        self.ip_request_windows[ip].append(now)
        
        # Check if IP is blocked
        if self._should_block_ip(ip):
            if ip not in self.blocked_ips:
                self._block_ip(ip, "Rate limiting or threat threshold exceeded")
            
            return SecurityEvent(
                timestamp=request_data['timestamp'],
                ip_address=ip,
                user_agent=request_data['user_agent'],
                endpoint=request_data['path'],
                method=request_data['method'],
                threat_type='blocked_ip',
                severity='high',
                details=request_data,
                blocked=True
            )
        
        # Detect threats
        threats = self.threat_detector.analyze_request(request_data)
        
        if threats:
            # Increment threat count for this IP
            self.ip_threat_counts[ip] += len(threats)
            
            # Determine severity
            severity = 'low'
            if 'attack_pattern' in threats:
                severity = 'high'
            elif 'wordpress_scan' in threats:
                severity = 'medium'
            elif len(threats) > 1:
                severity = 'medium'
            
            # Create security event
            event = SecurityEvent(
                timestamp=request_data['timestamp'],
                ip_address=ip,
                user_agent=request_data['user_agent'],
                endpoint=request_data['path'],
                method=request_data['method'],
                threat_type=','.join(threats),
                severity=severity,
                details={**request_data, 'threats_detected': threats},
                blocked=False
            )
            
            # Log security event
            logger.warning(f"Security threat detected from {ip}: {threats}")
            
            # Check if we should block this IP
            if (severity in ['high', 'critical'] or 
                self.ip_threat_counts[ip] >= self.max_threats_before_block):
                self._block_ip(ip, f"Multiple threats: {threats}")
                event.blocked = True
            
            # Send alert for high/critical threats
            if severity in ['high', 'critical']:
                send_security_alert, send_ip_blocked_alert, send_attack_pattern_alert = _get_alert_functions()
                if 'attack_pattern' in threats:
                    send_attack_pattern_alert(
                        ip, 
                        'attack_pattern', 
                        request_data['path'],
                        request_data['user_agent']
                    )
                else:
                    send_security_alert(
                        f"Security Threat: {','.join(threats)}",
                        event.to_dict(),
                        severity
                    )
            
            return event
        
        return None
    
    def is_request_blocked(self) -> bool:
        """Check if current request should be blocked"""
        ip = self._get_client_ip()
        return self._should_block_ip(ip)
    
    def get_security_stats(self) -> Dict:
        """Get security monitoring statistics"""
        total_blocked = len(self.blocked_ips)
        total_threats = sum(self.ip_threat_counts.values())
        
        # Top threat IPs
        top_threat_ips = sorted(
            self.ip_threat_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_blocked_ips': total_blocked,
            'total_threats_detected': total_threats,
            'blocked_ips': list(self.blocked_ips),
            'top_threat_ips': top_threat_ips,
            'monitoring_active': True,
            'auto_blocking_enabled': self.enable_auto_blocking
        }

# Global security monitor instance
security_monitor = SecurityMonitor(os.environ.get('REDIS_URL'))

def security_middleware():
    """Security middleware to analyze requests"""
    if not security_monitor:
        return
    
    # Skip security checks for whitelisted paths
    whitelist_paths = ['/health', '/static/', '/favicon.ico']
    if any(request.path.startswith(path) for path in whitelist_paths):
        return
    
    # Check if request is blocked
    if security_monitor.is_request_blocked():
        logger.warning(f"Blocked request from {security_monitor._get_client_ip()}: {request.path}")
        return jsonify({
            'error': 'Access denied',
            'message': 'Your IP has been blocked due to suspicious activity'
        }), 403
    
    # Analyze request for threats
    event = security_monitor.analyze_request()
    if event and event.blocked:
        logger.warning(f"Blocking malicious request: {event.to_dict()}")
        return jsonify({
            'error': 'Access denied',
            'message': 'Request blocked due to security policy'
        }), 403
    
    # Store event in request context for logging
    g.security_event = event

def init_security_monitoring(app):
    """Initialize security monitoring for Flask app"""
    
    @app.before_request
    def before_request_security():
        """Run security checks before each request"""
        result = security_middleware()
        if result:
            return result
    
    @app.route("/api/admin/security/stats")
    def security_stats():
        """Get security monitoring statistics (admin only)"""
        # Add admin authentication check here
        stats = security_monitor.get_security_stats()
        return jsonify(stats)
    
    @app.route("/api/admin/security/events")
    def security_events():
        """Get recent security events (admin only)"""
        # Add admin authentication check here
        # This would return recent security events from storage
        return jsonify({
            'events': [],
            'message': 'Security events logged to application logs'
        })
    
    @app.route("/api/admin/security/unblock/<ip>", methods=["POST"])
    def unblock_ip(ip):
        """Unblock an IP address (admin only)"""
        # Add admin authentication check here
        if ip in security_monitor.blocked_ips:
            security_monitor.blocked_ips.remove(ip)
            
            # Remove from Redis
            if security_monitor.redis_client:
                try:
                    security_monitor.redis_client.delete(f"blocked_ip:{ip}")
                except Exception as e:
                    logger.error(f"Failed to remove IP from Redis: {e}")
            
            logger.info(f"Manually unblocked IP: {ip}")
            return jsonify({'success': True, 'message': f'IP {ip} unblocked'})
        else:
            return jsonify({'success': False, 'message': 'IP not found in blocklist'})
    
    logger.info("Security monitoring initialized")