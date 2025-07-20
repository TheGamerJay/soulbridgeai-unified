"""
Enhanced monitoring and metrics for SoulBridge AI
Provides Prometheus-style metrics and comprehensive health checks
"""

import time
import os
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from flask import jsonify
from collections import defaultdict

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect and expose system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.active_connections = 0
        
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record request metrics"""
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1
        self.response_times[key].append(response_time)
        
        if status_code >= 400:
            self.error_count[key] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        uptime = time.time() - self.start_time
        
        try:
            # System resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate average response times
            avg_response_times = {}
            for endpoint, times in self.response_times.items():
                if times:
                    # Keep only last 100 requests for moving average
                    recent_times = times[-100:]
                    avg_response_times[endpoint] = sum(recent_times) / len(recent_times)
            
            metrics = {
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available // (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free // (1024 * 1024 * 1024)
                },
                "requests": {
                    "total_count": sum(self.request_count.values()),
                    "error_count": sum(self.error_count.values()),
                    "by_endpoint": dict(self.request_count),
                    "error_rate": sum(self.error_count.values()) / max(sum(self.request_count.values()), 1)
                },
                "performance": {
                    "avg_response_times_ms": {k: v * 1000 for k, v in avg_response_times.items()},
                    "active_connections": self.active_connections
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {
                "uptime_seconds": uptime,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Failed to collect system metrics"
            }


class HealthChecker:
    """Comprehensive health checking"""
    
    def __init__(self, db=None, openai_client=None):
        self.db = db
        self.openai_client = openai_client
        
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            if not self.db:
                return {
                    "status": "unhealthy",
                    "error": "Database not initialized"
                }
            
            # Test basic connectivity
            if hasattr(self.db, 'users'):
                # Try a simple query
                user_count = len(self.db.data.get("users", [])) if hasattr(self.db, 'data') else 0
                
            query_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "status": "healthy",
                "query_time_ms": round(query_time, 2),
                "user_count": user_count if 'user_count' in locals() else 0,
                "connection_pool": "active"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_openai_health(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity"""
        try:
            if not self.openai_client:
                return {
                    "status": "unhealthy",
                    "error": "OpenAI client not initialized"
                }
            
            start_time = time.time()
            # Simple API call to test connectivity
            models = self.openai_client.models.list()
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "models_available": len(models.data)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        services = {}
        
        # Check Redis if available
        try:
            import redis
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                services['redis'] = {"status": "healthy"}
            else:
                services['redis'] = {"status": "not_configured"}
        except Exception as e:
            services['redis'] = {"status": "unhealthy", "error": str(e)}
        
        # Check Stripe
        try:
            import stripe
            if stripe.api_key:
                account = stripe.Account.retrieve()
                services['stripe'] = {"status": "healthy", "account_id": account.id}
            else:
                services['stripe'] = {"status": "not_configured"}
        except Exception as e:
            services['stripe'] = {"status": "unhealthy", "error": str(e)}
        
        return services
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health check"""
        health = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": self.check_database_health(),
                "openai": self.check_openai_health(),
                "external_services": self.check_external_services()
            }
        }
        
        # Determine overall health
        for check_name, check_result in health["checks"].items():
            if isinstance(check_result, dict):
                if check_result.get("status") == "unhealthy":
                    health["overall_status"] = "degraded"
                elif isinstance(check_result, dict):
                    for service, service_health in check_result.items():
                        if isinstance(service_health, dict) and service_health.get("status") == "unhealthy":
                            health["overall_status"] = "degraded"
        
        return health


# Global instances
system_metrics = SystemMetrics()
health_checker = None  # Will be initialized with app dependencies


def init_monitoring(app, db=None, openai_client=None):
    """Initialize monitoring for Flask app"""
    global health_checker
    health_checker = HealthChecker(db, openai_client)
    
    @app.before_request
    def start_timer():
        """Start timing request"""
        import flask
        flask.g.start_time = time.time()
    
    @app.after_request
    def record_metrics(response):
        """Record request metrics after each request"""
        try:
            import flask
            if hasattr(flask.g, 'start_time'):
                response_time = time.time() - flask.g.start_time
                system_metrics.record_request(
                    endpoint=flask.request.endpoint or 'unknown',
                    method=flask.request.method,
                    status_code=response.status_code,
                    response_time=response_time
                )
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
        
        return response
    
    # Add metrics endpoints
    @app.route('/metrics')
    def metrics_endpoint():
        """Prometheus-style metrics endpoint"""
        metrics = system_metrics.get_metrics()
        
        # Convert to Prometheus format
        prometheus_metrics = []
        
        # System metrics
        prometheus_metrics.append(f"soulbridge_uptime_seconds {metrics['uptime_seconds']}")
        prometheus_metrics.append(f"soulbridge_cpu_percent {metrics['system']['cpu_percent']}")
        prometheus_metrics.append(f"soulbridge_memory_percent {metrics['system']['memory_percent']}")
        prometheus_metrics.append(f"soulbridge_disk_percent {metrics['system']['disk_percent']}")
        
        # Request metrics
        prometheus_metrics.append(f"soulbridge_requests_total {metrics['requests']['total_count']}")
        prometheus_metrics.append(f"soulbridge_errors_total {metrics['requests']['error_count']}")
        prometheus_metrics.append(f"soulbridge_error_rate {metrics['requests']['error_rate']}")
        
        # Response time metrics
        for endpoint, avg_time in metrics['performance']['avg_response_times_ms'].items():
            safe_endpoint = endpoint.replace(':', '_').replace('/', '_')
            prometheus_metrics.append(f"soulbridge_response_time_ms{{endpoint=\"{safe_endpoint}\"}} {avg_time}")
        
        return "\\n".join(prometheus_metrics), 200, {'Content-Type': 'text/plain'}
    
    @app.route('/api/health/comprehensive')
    def comprehensive_health():
        """Comprehensive health check endpoint"""
        if not health_checker:
            return jsonify({"error": "Health checker not initialized"}), 500
        
        health = health_checker.get_comprehensive_health()
        status_code = 200 if health["overall_status"] == "healthy" else 503
        
        return jsonify(health), status_code
    
    logger.info("Monitoring initialized with metrics and health check endpoints")


def create_alert(alert_type: str, message: str, severity: str = "warning"):
    """Create system alert (can be extended to send to external systems)"""
    alert = {
        "type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
    
    # Here you could extend to send to:
    # - Slack webhooks
    # - Email alerts
    # - PagerDuty
    # - Discord webhooks
    
    return alert