"""
Health Monitoring Endpoints
System health, monitoring, and diagnostic endpoints
"""

import logging
import psutil
import sqlite3
import json
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from typing import Dict, Any, List
import traceback
import os
import sys

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')

def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    try:
        # CPU information
        cpu_info = {
            'usage_percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'usage_percent': memory.percent
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'usage_percent': (disk.used / disk.total) * 100
        }
        
        return {
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'boot_time': psutil.boot_time(),
            'python_version': sys.version,
            'platform': sys.platform
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {'error': str(e)}

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and health"""
    health_status = {
        'databases': {},
        'overall_healthy': True
    }
    
    # Check main database files
    db_files = [
        'soulbridge.db',
        'poems.db',
        'stories.db',
        'writing_suite.db',
        'lyrics.db'
    ]
    
    for db_file in db_files:
        db_path = f"backend/{db_file}"
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Test connection with a simple query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                # Get database size
                db_size = os.path.getsize(db_path)
                
                health_status['databases'][db_file] = {
                    'status': 'healthy',
                    'tables_count': len(tables),
                    'size_bytes': db_size,
                    'tables': [table[0] for table in tables]
                }
                
                conn.close()
            else:
                health_status['databases'][db_file] = {
                    'status': 'not_found',
                    'error': 'Database file not found'
                }
                health_status['overall_healthy'] = False
                
        except Exception as e:
            health_status['databases'][db_file] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['overall_healthy'] = False
    
    return health_status

def check_service_health() -> Dict[str, Any]:
    """Check health of various services"""
    services_status = {}
    
    # Check poem generator service
    try:
        from services.poem_generator import create_poem_generator_service
        poem_service = create_poem_generator_service()
        services_status['poem_generator'] = {
            'status': 'healthy',
            'available_types': len(poem_service.structure_manager.structures) if hasattr(poem_service, 'structure_manager') else 0
        }
    except Exception as e:
        services_status['poem_generator'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Check story generator service
    try:
        from services.story_generator import create_story_generator_service
        story_service = create_story_generator_service()
        services_status['story_generator'] = {
            'status': 'healthy',
            'initialized': story_service is not None
        }
    except Exception as e:
        services_status['story_generator'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Check writing suite service
    try:
        from services.writing_suite import create_writing_suite_service
        writing_service = create_writing_suite_service()
        services_status['writing_suite'] = {
            'status': 'healthy',
            'initialized': writing_service is not None
        }
    except Exception as e:
        services_status['writing_suite'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Check export system
    try:
        from services.export_system import create_export_system
        export_service = create_export_system()
        services_status['export_system'] = {
            'status': 'healthy',
            'supported_formats': export_service.get_supported_formats()
        }
    except Exception as e:
        services_status['export_system'] = {
            'status': 'error',
            'error': str(e)
        }
    
    return services_status

@health_bp.route('/status', methods=['GET'])
def health_status():
    """Basic health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'SoulBridge AI',
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health status error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@health_bp.route('/detailed', methods=['GET'])
def detailed_health():
    """Comprehensive health check with system metrics"""
    try:
        # Get system information
        system_info = get_system_info()
        
        # Check database health
        db_health = check_database_health()
        
        # Check service health
        service_health = check_service_health()
        
        # Determine overall health
        overall_healthy = (
            db_health.get('overall_healthy', False) and
            not any(service.get('status') == 'error' for service in service_health.values()) and
            'error' not in system_info
        )
        
        health_report = {
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': system_info,
            'databases': db_health,
            'services': service_health,
            'checks': {
                'system_resources': 'healthy' if 'error' not in system_info else 'error',
                'database_connectivity': 'healthy' if db_health.get('overall_healthy') else 'error',
                'service_availability': 'healthy' if not any(s.get('status') == 'error' for s in service_health.values()) else 'error'
            }
        }
        
        status_code = 200 if overall_healthy else 503
        return jsonify(health_report), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check error: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/metrics', methods=['GET'])
def system_metrics():
    """Get system performance metrics"""
    try:
        # Get current metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network statistics
        network = psutil.net_io_counters()
        
        # Process information
        current_process = psutil.Process()
        process_info = {
            'pid': current_process.pid,
            'memory_mb': current_process.memory_info().rss / 1024 / 1024,
            'cpu_percent': current_process.cpu_percent(),
            'num_threads': current_process.num_threads(),
            'create_time': current_process.create_time()
        }
        
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cpu': {
                'usage_percent': cpu_percent,
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'memory': {
                'total_mb': memory.total / 1024 / 1024,
                'used_mb': memory.used / 1024 / 1024,
                'available_mb': memory.available / 1024 / 1024,
                'usage_percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024 / 1024 / 1024,
                'used_gb': disk.used / 1024 / 1024 / 1024,
                'free_gb': disk.free / 1024 / 1024 / 1024,
                'usage_percent': (disk.used / disk.total) * 100
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'process': process_info
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"System metrics error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/services', methods=['GET'])
def service_status():
    """Get status of all services"""
    try:
        service_health = check_service_health()
        
        # Count healthy vs error services
        total_services = len(service_health)
        healthy_services = sum(1 for s in service_health.values() if s.get('status') == 'healthy')
        error_services = total_services - healthy_services
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'error_services': error_services,
                'overall_status': 'healthy' if error_services == 0 else 'degraded'
            },
            'services': service_health
        })
        
    except Exception as e:
        logger.error(f"Service status error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/database', methods=['GET'])
def database_health():
    """Get database health information"""
    try:
        db_health = check_database_health()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database_health': db_health
        })
        
    except Exception as e:
        logger.error(f"Database health error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/logs', methods=['GET'])
def get_recent_logs():
    """Get recent application logs"""
    try:
        # Get parameters
        lines = min(int(request.args.get('lines', 100)), 1000)  # Max 1000 lines
        level = request.args.get('level', 'INFO').upper()
        
        # Read log file if it exists
        log_file = 'backend/app.log'
        logs = []
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    # Get last N lines
                    recent_lines = all_lines[-lines:] if lines < len(all_lines) else all_lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if level in line or level == 'ALL':
                            logs.append(line)
            except Exception as e:
                logs.append(f"Error reading log file: {str(e)}")
        else:
            logs.append("Log file not found")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'logs': logs,
            'total_lines': len(logs),
            'filter_level': level
        })
        
    except Exception as e:
        logger.error(f"Get logs error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for load balancers"""
    return jsonify({
        'pong': True,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Kubernetes-style readiness probe"""
    try:
        # Check if essential services are ready
        essential_checks = []
        
        # Check database connectivity
        try:
            conn = sqlite3.connect('backend/soulbridge.db')
            conn.execute('SELECT 1')
            conn.close()
            essential_checks.append(('database', True))
        except:
            essential_checks.append(('database', False))
        
        # Check if core services load
        try:
            from services.poem_generator import create_poem_generator_service
            create_poem_generator_service()
            essential_checks.append(('poem_service', True))
        except:
            essential_checks.append(('poem_service', False))
        
        # Determine readiness
        all_ready = all(check[1] for check in essential_checks)
        
        response_data = {
            'ready': all_ready,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': dict(essential_checks)
        }
        
        status_code = 200 if all_ready else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Readiness check error: {traceback.format_exc()}")
        return jsonify({
            'ready': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Kubernetes-style liveness probe"""
    try:
        # Basic liveness - if we can respond, we're alive
        return jsonify({
            'alive': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': psutil.time.time() - psutil.boot_time()
        })
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        return jsonify({
            'alive': False,
            'error': str(e)
        }), 503