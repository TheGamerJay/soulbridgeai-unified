"""
SoulBridge AI - Debug Utilities
Debug tools and utilities for system diagnostics and troubleshooting
"""
import logging
import traceback
import sys
import gc
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import psutil
import os

logger = logging.getLogger(__name__)

class DebugUtils:
    """Debug utilities and diagnostic tools"""
    
    def __init__(self):
        self.debug_sessions = {}
        self.performance_metrics = []
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information for debugging"""
        try:
            return {
                'python': {
                    'version': sys.version,
                    'version_info': sys.version_info,
                    'platform': sys.platform,
                    'executable': sys.executable,
                    'path': sys.path[:5]  # First 5 paths only
                },
                'process': {
                    'pid': os.getpid(),
                    'memory_usage': psutil.Process().memory_info()._asdict(),
                    'cpu_percent': psutil.Process().cpu_percent(),
                    'threads': threading.active_count(),
                    'thread_names': [t.name for t in threading.enumerate()]
                },
                'system': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total,
                    'memory_available': psutil.virtual_memory().available,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'boot_time': datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()
                },
                'environment': {
                    'debug_mode': os.environ.get('DEBUG_MODE', 'false'),
                    'environment': os.environ.get('ENVIRONMENT', 'unknown'),
                    'database_type': 'postgresql' if 'postgresql' in os.environ.get('DATABASE_URL', '').lower() else 'sqlite'
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Garbage collector stats
            gc_stats = {
                'objects': len(gc.get_objects()),
                'collections': gc.get_count(),
                'threshold': gc.get_threshold()
            }
            
            return {
                'process_memory': {
                    'rss': memory_info.rss,  # Resident Set Size
                    'vms': memory_info.vms,  # Virtual Memory Size
                    'percent': process.memory_percent(),
                    'readable': {
                        'rss': f"{memory_info.rss / 1024 / 1024:.2f} MB",
                        'vms': f"{memory_info.vms / 1024 / 1024:.2f} MB"
                    }
                },
                'system_memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                    'readable': {
                        'total': f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB",
                        'available': f"{psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB"
                    }
                },
                'garbage_collector': gc_stats
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {'error': str(e)}
    
    def get_thread_info(self) -> Dict[str, Any]:
        """Get information about running threads"""
        try:
            threads = []
            for thread in threading.enumerate():
                thread_info = {
                    'name': thread.name,
                    'ident': thread.ident,
                    'daemon': thread.daemon,
                    'alive': thread.is_alive()
                }
                
                # Add stack trace for active threads
                if thread.is_alive() and thread != threading.current_thread():
                    frame = sys._current_frames().get(thread.ident)
                    if frame:
                        thread_info['stack'] = traceback.format_stack(frame)[-3:]  # Last 3 stack frames
                
                threads.append(thread_info)
            
            return {
                'total_threads': threading.active_count(),
                'main_thread': threading.main_thread().name,
                'current_thread': threading.current_thread().name,
                'threads': threads
            }
        except Exception as e:
            logger.error(f"Error getting thread info: {e}")
            return {'error': str(e)}
    
    def get_database_debug_info(self, db_manager=None) -> Dict[str, Any]:
        """Get database debugging information"""
        try:
            if not db_manager:
                return {'error': 'No database manager provided'}
            
            debug_info = {
                'connection_status': 'unknown',
                'database_type': 'unknown',
                'tables': [],
                'connection_pool': {}
            }
            
            try:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                debug_info['connection_status'] = 'connected'
                
                # Detect database type
                if hasattr(conn, 'server_version'):
                    debug_info['database_type'] = 'postgresql'
                    debug_info['server_version'] = getattr(conn, 'server_version', 'unknown')
                else:
                    debug_info['database_type'] = 'sqlite'
                
                # Get table list
                if debug_info['database_type'] == 'postgresql':
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                else:  # SQLite
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                
                debug_info['tables'] = [row[0] for row in cursor.fetchall()]
                
                # Connection pool info (if available)
                if hasattr(db_manager, 'pool'):
                    pool = db_manager.pool
                    debug_info['connection_pool'] = {
                        'size': getattr(pool, 'size', 'unknown'),
                        'checked_in': getattr(pool, 'checkedin', 'unknown'),
                        'checked_out': getattr(pool, 'checkedout', 'unknown'),
                        'overflow': getattr(pool, 'overflow', 'unknown')
                    }
                
                conn.close()
                
            except Exception as db_error:
                debug_info['connection_status'] = 'error'
                debug_info['connection_error'] = str(db_error)
            
            return debug_info
            
        except Exception as e:
            logger.error(f"Error getting database debug info: {e}")
            return {'error': str(e)}
    
    def run_diagnostics(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        try:
            diagnostics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_info': self.get_system_info(),
                'memory_usage': self.get_memory_usage(),
                'thread_info': self.get_thread_info(),
                'disk_usage': self.get_disk_usage(),
                'network_info': self.get_network_info() if include_sensitive else 'excluded',
                'environment_check': self.check_environment_variables(include_sensitive)
            }
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk_info = {}
            
            # Get disk usage for current directory
            current_path = os.getcwd()
            usage = psutil.disk_usage(current_path)
            
            disk_info['current_directory'] = {
                'path': current_path,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100,
                'readable': {
                    'total': f"{usage.total / 1024 / 1024 / 1024:.2f} GB",
                    'used': f"{usage.used / 1024 / 1024 / 1024:.2f} GB",
                    'free': f"{usage.free / 1024 / 1024 / 1024:.2f} GB"
                }
            }
            
            # Get all disk partitions
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'percent': (partition_usage.used / partition_usage.total) * 100
                    })
                except PermissionError:
                    # Can't access this partition
                    pass
            
            disk_info['partitions'] = partitions
            return disk_info
            
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {'error': str(e)}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network interface information (be careful with sensitive data)"""
        try:
            network_info = {
                'interfaces': [],
                'connections': len(psutil.net_connections()),
                'io_counters': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
            
            # Get network interfaces (without IP addresses for security)
            for interface, addresses in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface,
                    'addresses': len(addresses),
                    'is_up': psutil.net_if_stats()[interface].isup if interface in psutil.net_if_stats() else False
                }
                network_info['interfaces'].append(interface_info)
            
            return network_info
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {'error': str(e)}
    
    def check_environment_variables(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Check important environment variables"""
        try:
            important_vars = [
                'DEBUG_MODE', 'ENVIRONMENT', 'DATABASE_URL', 'OPENAI_API_KEY',
                'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY', 'SECRET_KEY',
                'MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME'
            ]
            
            env_check = {
                'total_variables': len(os.environ),
                'important_variables': {}
            }
            
            for var in important_vars:
                value = os.environ.get(var)
                if value is not None:
                    if include_sensitive:
                        # Show first 10 chars for debugging
                        env_check['important_variables'][var] = f"{value[:10]}..." if len(value) > 10 else value
                    else:
                        # Just show that it exists
                        env_check['important_variables'][var] = "SET" if value else "EMPTY"
                else:
                    env_check['important_variables'][var] = "NOT_SET"
            
            return env_check
            
        except Exception as e:
            logger.error(f"Error checking environment variables: {e}")
            return {'error': str(e)}
    
    def create_debug_session(self, session_id: str, context: Dict[str, Any] = None) -> str:
        """Create a debug session for tracking issues"""
        try:
            self.debug_sessions[session_id] = {
                'created_at': datetime.now(timezone.utc).isoformat(),
                'context': context or {},
                'events': [],
                'status': 'active'
            }
            
            logger.info(f"Created debug session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating debug session: {e}")
            return None
    
    def log_debug_event(self, session_id: str, event_type: str, data: Any) -> bool:
        """Log an event to a debug session"""
        try:
            if session_id not in self.debug_sessions:
                logger.warning(f"Debug session not found: {session_id}")
                return False
            
            event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': event_type,
                'data': data
            }
            
            self.debug_sessions[session_id]['events'].append(event)
            logger.debug(f"Logged debug event to {session_id}: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging debug event: {e}")
            return False
    
    def get_debug_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get debug session data"""
        return self.debug_sessions.get(session_id)
    
    def close_debug_session(self, session_id: str) -> bool:
        """Close a debug session"""
        try:
            if session_id in self.debug_sessions:
                self.debug_sessions[session_id]['status'] = 'closed'
                self.debug_sessions[session_id]['closed_at'] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Closed debug session: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error closing debug session: {e}")
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old debug sessions"""
        try:
            cutoff_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - max_age_hours)
            
            old_sessions = []
            for session_id, session_data in self.debug_sessions.items():
                session_time = datetime.fromisoformat(session_data['created_at'].replace('Z', '+00:00'))
                if session_time < cutoff_time:
                    old_sessions.append(session_id)
            
            for session_id in old_sessions:
                del self.debug_sessions[session_id]
            
            logger.info(f"Cleaned up {len(old_sessions)} old debug sessions")
            return len(old_sessions)
            
        except Exception as e:
            logger.error(f"Error cleaning up debug sessions: {e}")
            return 0
    
    def export_diagnostics_report(self, include_sensitive: bool = False) -> str:
        """Export a comprehensive diagnostics report"""
        try:
            report = {
                'report_info': {
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'report_type': 'system_diagnostics',
                    'sensitive_data_included': include_sensitive
                },
                'diagnostics': self.run_diagnostics(include_sensitive),
                'active_debug_sessions': len([s for s in self.debug_sessions.values() if s['status'] == 'active']),
                'total_debug_sessions': len(self.debug_sessions)
            }
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error exporting diagnostics report: {e}")
            return json.dumps({
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, indent=2)