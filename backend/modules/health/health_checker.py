"""
SoulBridge AI - Health Checker
System health monitoring and status checks
Extracted from backend/app.py with improvements
"""
import logging
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import psutil

logger = logging.getLogger(__name__)

class HealthChecker:
    """System health monitoring and diagnostics"""
    
    def __init__(self, database=None, openai_client=None):
        self.database = database
        self.openai_client = openai_client
        self.system_start_time = datetime.now(timezone.utc)
        self.last_health_check = datetime.now(timezone.utc)
        self.health_history = []
        self.max_history_size = 100
        
        # Health check configuration
        self.check_intervals = {
            'database': 30,      # 30 seconds
            'openai': 60,        # 1 minute
            'system': 300,       # 5 minutes
            'storage': 600       # 10 minutes
        }
        
        # Thresholds
        self.thresholds = {
            'cpu_usage': 80,        # CPU usage percentage
            'memory_usage': 85,     # Memory usage percentage
            'disk_usage': 90,       # Disk usage percentage
            'response_time': 5.0,   # Max response time in seconds
            'error_rate': 10        # Max error rate percentage
        }
        
        logger.info("🏥 Health checker initialized")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            health_status = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'healthy',
                'uptime_seconds': self.get_uptime_seconds(),
                'services': {},
                'system_metrics': {},
                'alerts': []
            }
            
            # Check individual services
            services_to_check = [
                ('database', self._check_database_health),
                ('openai', self._check_openai_health),
                ('storage', self._check_storage_health),
                ('system', self._check_system_metrics)
            ]
            
            overall_healthy = True
            
            for service_name, check_func in services_to_check:
                try:
                    service_status = check_func()
                    health_status['services'][service_name] = service_status
                    
                    if not service_status.get('healthy', False):
                        overall_healthy = False
                        if service_status.get('alert'):
                            health_status['alerts'].append({
                                'service': service_name,
                                'message': service_status.get('message', 'Service unhealthy'),
                                'severity': service_status.get('severity', 'warning')
                            })
                            
                except Exception as e:
                    logger.error(f"Health check failed for {service_name}: {e}")
                    health_status['services'][service_name] = {
                        'healthy': False,
                        'error': str(e),
                        'alert': True,
                        'message': f'{service_name} health check failed'
                    }
                    overall_healthy = False
            
            # Set overall status
            if overall_healthy:
                health_status['overall_status'] = 'healthy'
            elif any(alert.get('severity') == 'critical' for alert in health_status['alerts']):
                health_status['overall_status'] = 'critical'
            else:
                health_status['overall_status'] = 'warning'
            
            # Store in history
            self._add_to_history(health_status)
            
            # Update last check time
            self.last_health_check = datetime.now(timezone.utc)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'error',
                'error': str(e),
                'services': {},
                'system_metrics': {},
                'alerts': [{
                    'service': 'health_checker',
                    'message': 'Health check system error',
                    'severity': 'critical'
                }]
            }
    
    def get_quick_health_status(self) -> Dict[str, Any]:
        """Get quick health status for API endpoints"""
        try:
            status = {
                'online': True,
                'status': 'ok',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'uptime': self.get_uptime_seconds(),
                'services': {
                    'database': self._quick_database_check(),
                    'storage': self._quick_storage_check()
                }
            }
            
            # Check if any service is down
            if not all(service.get('available', True) for service in status['services'].values()):
                status['status'] = 'degraded'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting quick health status: {e}")
            return {
                'online': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connection and performance"""
        try:
            if not self.database:
                return {
                    'healthy': False,
                    'available': False,
                    'message': 'Database service not configured',
                    'severity': 'critical',
                    'alert': True
                }
            
            start_time = time.time()
            
            # Test connection
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Test user table
            if self.database.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM users")
            else:
                cursor.execute("SELECT COUNT(*) FROM users")
            
            user_count = cursor.fetchone()[0] or 0
            
            conn.close()
            
            response_time = time.time() - start_time
            
            # Check response time
            slow_query = response_time > self.thresholds['response_time']
            
            return {
                'healthy': True,
                'available': True,
                'response_time_ms': round(response_time * 1000, 2),
                'user_count': user_count,
                'database_type': 'PostgreSQL' if self.database.use_postgres else 'SQLite',
                'slow_query': slow_query,
                'alert': slow_query,
                'message': f'Database responding in {response_time:.2f}s' + 
                          (' (slow)' if slow_query else ''),
                'severity': 'warning' if slow_query else 'info'
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'healthy': False,
                'available': False,
                'error': str(e),
                'message': 'Database connection failed',
                'severity': 'critical',
                'alert': True
            }
    
    def _check_openai_health(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity and limits"""
        try:
            if not self.openai_client:
                return {
                    'healthy': True,  # Not critical if not configured
                    'available': False,
                    'message': 'OpenAI client not configured',
                    'severity': 'info'
                }
            
            start_time = time.time()
            
            # Test simple completion
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            response_time = time.time() - start_time
            
            # Check response
            if response and response.choices:
                return {
                    'healthy': True,
                    'available': True,
                    'response_time_ms': round(response_time * 1000, 2),
                    'model_used': 'gpt-3.5-turbo',
                    'message': f'OpenAI responding in {response_time:.2f}s',
                    'severity': 'info'
                }
            else:
                return {
                    'healthy': False,
                    'available': False,
                    'message': 'OpenAI returned invalid response',
                    'severity': 'warning',
                    'alert': True
                }
                
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            # Don't mark as critical since app can run without AI
            return {
                'healthy': False,
                'available': False,
                'error': str(e),
                'message': 'OpenAI API unavailable',
                'severity': 'warning',
                'alert': True
            }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check disk storage and file system health"""
        try:
            # Get disk usage
            disk_usage = psutil.disk_usage('/')
            
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check logs directory
            logs_dir = 'logs'
            logs_size_mb = 0
            if os.path.exists(logs_dir):
                try:
                    logs_size_mb = sum(
                        os.path.getsize(os.path.join(logs_dir, f))
                        for f in os.listdir(logs_dir)
                        if os.path.isfile(os.path.join(logs_dir, f))
                    ) / (1024**2)
                except:
                    pass
            
            # Check if disk usage is critical
            disk_critical = usage_percent > self.thresholds['disk_usage']
            disk_warning = usage_percent > (self.thresholds['disk_usage'] - 10)
            
            storage_status = {
                'healthy': not disk_critical,
                'available': True,
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'usage_percent': round(usage_percent, 2),
                'logs_size_mb': round(logs_size_mb, 2),
                'alert': disk_critical or disk_warning,
                'severity': 'critical' if disk_critical else 'warning' if disk_warning else 'info'
            }
            
            if disk_critical:
                storage_status['message'] = f'Disk usage critical: {usage_percent:.1f}%'
            elif disk_warning:
                storage_status['message'] = f'Disk usage high: {usage_percent:.1f}%'
            else:
                storage_status['message'] = f'Storage healthy: {usage_percent:.1f}% used'
            
            return storage_status
            
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                'healthy': False,
                'available': False,
                'error': str(e),
                'message': 'Storage health check failed',
                'severity': 'warning',
                'alert': True
            }
    
    def _check_system_metrics(self) -> Dict[str, Any]:
        """Check system CPU, memory, and performance metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
                load_1min, load_5min, load_15min = load_avg
            except:
                # Windows or other systems without load average
                load_1min = load_5min = load_15min = 0
            
            # Check for issues
            cpu_high = cpu_percent > self.thresholds['cpu_usage']
            memory_high = memory_percent > self.thresholds['memory_usage']
            
            system_status = {
                'healthy': not (cpu_high or memory_high),
                'available': True,
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'load_1min': round(load_1min, 2) if load_1min else None,
                'load_5min': round(load_5min, 2) if load_5min else None,
                'load_15min': round(load_15min, 2) if load_15min else None,
                'alert': cpu_high or memory_high
            }
            
            # Set severity and message
            if cpu_high and memory_high:
                system_status['severity'] = 'critical'
                system_status['message'] = f'High CPU ({cpu_percent:.1f}%) and memory ({memory_percent:.1f}%) usage'
            elif cpu_high:
                system_status['severity'] = 'warning'
                system_status['message'] = f'High CPU usage: {cpu_percent:.1f}%'
            elif memory_high:
                system_status['severity'] = 'warning'
                system_status['message'] = f'High memory usage: {memory_percent:.1f}%'
            else:
                system_status['severity'] = 'info'
                system_status['message'] = f'System metrics normal: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%'
            
            return system_status
            
        except Exception as e:
            logger.error(f"System metrics check failed: {e}")
            return {
                'healthy': False,
                'available': False,
                'error': str(e),
                'message': 'System metrics check failed',
                'severity': 'warning',
                'alert': True
            }
    
    def _quick_database_check(self) -> Dict[str, Any]:
        """Quick database availability check"""
        try:
            if not self.database:
                return {'available': False, 'reason': 'not_configured'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return {'available': True}
            
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def _quick_storage_check(self) -> Dict[str, Any]:
        """Quick storage availability check"""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            return {
                'available': usage_percent < self.thresholds['disk_usage'],
                'usage_percent': round(usage_percent, 2)
            }
            
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def get_uptime_seconds(self) -> int:
        """Get system uptime in seconds"""
        return int((datetime.now(timezone.utc) - self.system_start_time).total_seconds())
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history"""
        return self.health_history[-limit:] if self.health_history else []
    
    def _add_to_history(self, health_status: Dict[str, Any]):
        """Add health status to history"""
        try:
            # Create simplified history entry
            history_entry = {
                'timestamp': health_status['timestamp'],
                'overall_status': health_status['overall_status'],
                'uptime_seconds': health_status['uptime_seconds'],
                'alert_count': len(health_status.get('alerts', [])),
                'service_count': len(health_status.get('services', {})),
                'healthy_services': sum(
                    1 for service in health_status.get('services', {}).values()
                    if service.get('healthy', False)
                )
            }
            
            self.health_history.append(history_entry)
            
            # Trim history if too long
            if len(self.health_history) > self.max_history_size:
                self.health_history = self.health_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"Error adding to health history: {e}")
    
    def get_service_availability(self, hours: int = 24) -> Dict[str, Any]:
        """Calculate service availability over time period"""
        try:
            if not self.health_history:
                return {
                    'availability_percent': 0,
                    'total_checks': 0,
                    'healthy_checks': 0,
                    'period_hours': hours
                }
            
            # Filter history for time period
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_history = [
                entry for entry in self.health_history
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
            
            if not recent_history:
                return {
                    'availability_percent': 0,
                    'total_checks': 0,
                    'healthy_checks': 0,
                    'period_hours': hours
                }
            
            total_checks = len(recent_history)
            healthy_checks = sum(
                1 for entry in recent_history
                if entry['overall_status'] == 'healthy'
            )
            
            availability_percent = (healthy_checks / total_checks) * 100
            
            return {
                'availability_percent': round(availability_percent, 2),
                'total_checks': total_checks,
                'healthy_checks': healthy_checks,
                'period_hours': hours,
                'first_check': recent_history[0]['timestamp'] if recent_history else None,
                'last_check': recent_history[-1]['timestamp'] if recent_history else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating service availability: {e}")
            return {
                'availability_percent': 0,
                'error': str(e),
                'period_hours': hours
            }
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostic"""
        try:
            diagnostic = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_info': self._get_system_info(),
                'health_status': self.get_system_health(),
                'availability': self.get_service_availability(),
                'recommendations': []
            }
            
            # Generate recommendations based on health status
            diagnostic['recommendations'] = self._generate_recommendations(diagnostic)
            
            return diagnostic
            
        except Exception as e:
            logger.error(f"Error running diagnostic: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'system_info': {},
                'health_status': {},
                'availability': {},
                'recommendations': []
            }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            import platform
            
            return {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                'uptime_hours': round(self.get_uptime_seconds() / 3600, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, diagnostic: Dict[str, Any]) -> List[str]:
        """Generate system recommendations based on diagnostic results"""
        recommendations = []
        
        try:
            health_status = diagnostic.get('health_status', {})
            services = health_status.get('services', {})
            
            # Database recommendations
            db_service = services.get('database', {})
            if not db_service.get('healthy', True):
                recommendations.append("Database connection issues detected. Check database server status.")
            elif db_service.get('slow_query', False):
                recommendations.append("Database queries are slow. Consider optimizing queries or increasing resources.")
            
            # System recommendations
            system_service = services.get('system', {})
            if system_service.get('cpu_percent', 0) > self.thresholds['cpu_usage']:
                recommendations.append("High CPU usage detected. Monitor application performance and consider scaling.")
            
            if system_service.get('memory_percent', 0) > self.thresholds['memory_usage']:
                recommendations.append("High memory usage detected. Check for memory leaks or increase available memory.")
            
            # Storage recommendations
            storage_service = services.get('storage', {})
            if storage_service.get('usage_percent', 0) > self.thresholds['disk_usage']:
                recommendations.append("Disk space is running low. Clean up logs and temporary files.")
            
            if storage_service.get('logs_size_mb', 0) > 100:
                recommendations.append("Log files are large. Implement log rotation to save disk space.")
            
            # Availability recommendations
            availability = diagnostic.get('availability', {})
            if availability.get('availability_percent', 100) < 95:
                recommendations.append("System availability is below 95%. Investigate recurring issues.")
            
            # General recommendations
            uptime_hours = diagnostic.get('system_info', {}).get('uptime_hours', 0)
            if uptime_hours > 720:  # 30 days
                recommendations.append("System has been running for over 30 days. Consider scheduled maintenance restart.")
            
            if not recommendations:
                recommendations.append("System is running optimally. Continue monitoring.")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to diagnostic error.")
        
        return recommendations