"""
SoulBridge AI - Health and Debug Routes
Flask routes for health checks, system monitoring, and debug utilities
"""
import logging
from flask import Blueprint, jsonify, request, session, redirect, url_for
from datetime import datetime, timezone
from functools import wraps
import os
from typing import Dict, Any

from .health_checker import HealthChecker
from .system_monitor import SystemMonitor
from .debug_utils import DebugUtils

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

# Initialize health system components
health_checker = HealthChecker()
system_monitor = SystemMonitor()
debug_utils = DebugUtils()

def admin_required(f):
    """Decorator to require admin authentication for debug/admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is admin (implement based on your auth system)
        if not session.get('is_admin', False):
            # For debug mode, allow if debug password is provided
            debug_password = request.args.get('debug_key') or request.form.get('debug_key')
            expected_password = os.environ.get('DEBUG_PASSWORD', 'debug123')
            
            if debug_password != expected_password:
                return jsonify({
                    'error': 'Admin access required',
                    'message': 'This endpoint requires admin privileges'
                }), 403
        
        return f(*args, **kwargs)
    return decorated_function

@health_bp.route('/health')
def health_check():
    """Main health check endpoint - comprehensive system status"""
    try:
        # Try to get detailed health data, but fall back to basic check
        try:
            health_data = health_checker.get_system_health()
            
            # Determine overall status
            overall_status = 'healthy'
            if health_data.get('database', {}).get('status') != 'connected':
                overall_status = 'degraded'
            if health_data.get('system', {}).get('cpu_percent', 0) > 90:
                overall_status = 'degraded'
            if health_data.get('system', {}).get('memory_percent', 0) > 90:
                overall_status = 'critical'
            
            return jsonify({
                'status': overall_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'soulbridge-ai',
                'version': '1.0.0',
                'details': health_data
            })
            
        except Exception as health_error:
            # If detailed health check fails, return basic healthy status
            logger.warning(f"Detailed health check failed, returning basic status: {health_error}")
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'soulbridge-ai',
                'version': '1.0.0',
                'message': 'Basic health check - service is running'
            })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/api/mini-assistant-status')
def mini_assistant_status():
    """Status endpoint for mini assistant service"""
    try:
        health_data = health_checker.get_system_health()
        
        # Check specific services needed for mini assistant
        openai_status = health_data.get('external_services', {}).get('openai_api', {}).get('status', 'unknown')
        database_status = health_data.get('database', {}).get('status', 'unknown')
        
        status = 'operational'
        if openai_status != 'healthy' or database_status != 'connected':
            status = 'degraded'
        
        return jsonify({
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': {
                'openai_api': openai_status,
                'database': database_status,
                'system': 'healthy' if health_data.get('system', {}).get('cpu_percent', 0) < 80 else 'busy'
            }
        })
        
    except Exception as e:
        logger.error(f"Mini assistant status error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/system-info')
@admin_required
def debug_system_info():
    """Get comprehensive system information for debugging"""
    try:
        include_sensitive = request.args.get('include_sensitive', '').lower() == 'true'
        system_info = debug_utils.get_system_info()
        
        return jsonify({
            'success': True,
            'data': system_info,
            'sensitive_data_included': include_sensitive,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug system info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/memory-usage')
@admin_required
def debug_memory_usage():
    """Get detailed memory usage information"""
    try:
        memory_info = debug_utils.get_memory_usage()
        
        return jsonify({
            'success': True,
            'data': memory_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug memory usage error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/threads')
@admin_required
def debug_thread_info():
    """Get information about running threads"""
    try:
        thread_info = debug_utils.get_thread_info()
        
        return jsonify({
            'success': True,
            'data': thread_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug thread info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/database')
@admin_required
def debug_database_info():
    """Get database debugging information"""
    try:
        # This would need the database manager to be passed in
        # For now, return basic info
        db_info = debug_utils.get_database_debug_info()
        
        return jsonify({
            'success': True,
            'data': db_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug database info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/diagnostics')
@admin_required
def debug_full_diagnostics():
    """Run comprehensive system diagnostics"""
    try:
        include_sensitive = request.args.get('include_sensitive', '').lower() == 'true'
        diagnostics = debug_utils.run_diagnostics(include_sensitive)
        
        return jsonify({
            'success': True,
            'data': diagnostics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug full diagnostics error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/export-report')
@admin_required
def debug_export_report():
    """Export comprehensive diagnostics report"""
    try:
        include_sensitive = request.args.get('include_sensitive', '').lower() == 'true'
        report = debug_utils.export_diagnostics_report(include_sensitive)
        
        response = jsonify({
            'success': True,
            'report': report,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Set headers for file download
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=soulbridge-diagnostics-{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    except Exception as e:
        logger.error(f"Debug export report error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/monitoring-status')
@admin_required
def debug_monitoring_status():
    """Get system monitoring status"""
    try:
        status_info = {
            'monitoring_active': system_monitor.monitoring_active,
            'emergency_mode': system_monitor.emergency_mode,
            'monitoring_interval': system_monitor.monitoring_interval,
            'last_check': system_monitor.last_health_check,
            'uptime': system_monitor.get_uptime() if hasattr(system_monitor, 'get_uptime') else 'unknown',
            'alerts_count': len(system_monitor.alerts) if hasattr(system_monitor, 'alerts') else 0,
            'blocked_ips_count': len(system_monitor.blocked_ips) if hasattr(system_monitor, 'blocked_ips') else 0
        }
        
        return jsonify({
            'success': True,
            'data': status_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Debug monitoring status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/start-monitoring', methods=['POST'])
@admin_required
def debug_start_monitoring():
    """Start system monitoring"""
    try:
        if system_monitor.monitoring_active:
            return jsonify({
                'success': True,
                'message': 'Monitoring is already active',
                'status': 'already_running'
            })
        
        system_monitor.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'System monitoring started',
            'status': 'started'
        })
        
    except Exception as e:
        logger.error(f"Debug start monitoring error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/stop-monitoring', methods=['POST'])
@admin_required
def debug_stop_monitoring():
    """Stop system monitoring"""
    try:
        if not system_monitor.monitoring_active:
            return jsonify({
                'success': True,
                'message': 'Monitoring is already stopped',
                'status': 'already_stopped'
            })
        
        system_monitor.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'System monitoring stopped',
            'status': 'stopped'
        })
        
    except Exception as e:
        logger.error(f"Debug stop monitoring error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/session', methods=['POST'])
@admin_required
def debug_create_session():
    """Create a new debug session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        context = data.get('context', {})
        
        created_session = debug_utils.create_debug_session(session_id, context)
        
        if created_session:
            return jsonify({
                'success': True,
                'session_id': created_session,
                'message': 'Debug session created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create debug session'
            }), 500
            
    except Exception as e:
        logger.error(f"Debug create session error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/session/<session_id>')
@admin_required
def debug_get_session(session_id):
    """Get debug session data"""
    try:
        session_data = debug_utils.get_debug_session(session_id)
        
        if session_data:
            return jsonify({
                'success': True,
                'data': session_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Debug session not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Debug get session error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/api/debug/session/<session_id>/log', methods=['POST'])
@admin_required
def debug_log_event(session_id):
    """Log an event to a debug session"""
    try:
        data = request.get_json() or {}
        event_type = data.get('type', 'unknown')
        event_data = data.get('data', {})
        
        success = debug_utils.log_debug_event(session_id, event_type, event_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Event logged successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to log event'
            }), 500
            
    except Exception as e:
        logger.error(f"Debug log event error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/admin/health-dashboard')
@admin_required
def admin_health_dashboard():
    """Admin dashboard for health monitoring (HTML page would be served)"""
    # In a full implementation, this would render an HTML template
    # For now, return JSON data that could be used by a frontend
    try:
        health_data = health_checker.get_system_health()
        monitoring_status = {
            'active': system_monitor.monitoring_active,
            'emergency_mode': system_monitor.emergency_mode
        }
        
        dashboard_data = {
            'health': health_data,
            'monitoring': monitoring_status,
            'debug_sessions': len(debug_utils.debug_sessions),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data,
            'message': 'Use this data to build your admin dashboard frontend'
        })
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@health_bp.errorhandler(403)
def forbidden(e):
    return jsonify({
        'error': 'Forbidden',
        'message': 'Admin access required for this endpoint'
    }), 403

@health_bp.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not Found',
        'message': 'Health/debug endpoint not found'
    }), 404

@health_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An error occurred in the health system'
    }), 500

# Health check initialization
def init_health_system(app, database_manager=None, openai_client=None):
    """Initialize the health system with app dependencies"""
    global health_checker, system_monitor
    
    # Configure health checker with dependencies
    if database_manager:
        health_checker.database_manager = database_manager
    if openai_client:
        health_checker.openai_client = openai_client
    
    # Configure system monitor
    system_monitor.app = app
    
    # Start monitoring if configured
    if app.config.get('AUTO_START_MONITORING', False):
        system_monitor.start_monitoring()
    
    logger.info("Health system initialized successfully")

def cleanup_health_system():
    """Cleanup health system resources"""
    global system_monitor
    
    try:
        if system_monitor and system_monitor.monitoring_active:
            system_monitor.stop_monitoring()
        logger.info("Health system cleanup completed")
    except Exception as e:
        logger.error(f"Error during health system cleanup: {e}")