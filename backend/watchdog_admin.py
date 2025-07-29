#!/usr/bin/env python3
"""
WatchDog Admin System - SoulBridge AI
Separate admin dashboard isolated from main user application
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import bcrypt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create WatchDog Admin App
watchdog = Flask(__name__)
watchdog.secret_key = os.environ.get('WATCHDOG_SECRET_KEY', 'watchdog-admin-secure-key-2025')

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@watchdog.route('/admin')
def admin_dashboard():
    """Main WatchDog Admin Dashboard"""
    return redirect(url_for('admin_login'))

@watchdog.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple admin authentication (enhance as needed)
        if username == 'admin' and password == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['admin_authenticated'] = True
            session['admin_username'] = username
            session['admin_login_time'] = datetime.now().isoformat()
            logger.info(f"🔐 WATCHDOG: Admin login successful for {username}")
            return redirect(url_for('admin_home'))
        else:
            logger.warning(f"🚫 WATCHDOG: Failed admin login attempt for {username}")
            return render_template('admin/login.html', error='Invalid credentials')
    
    return render_template('admin/login.html')

@watchdog.route('/admin/home')
@admin_required
def admin_home():
    """WatchDog Admin Home Dashboard"""
    try:
        # Get system stats
        stats = {
            'total_users': get_user_count(),
            'active_sessions': get_active_sessions(),
            'database_status': check_database_health(),
            'server_uptime': get_server_uptime(),
            'trial_users': get_trial_users_count(),
            'companion_selections': get_companion_stats()
        }
        
        logger.info("🔍 WATCHDOG: Admin dashboard accessed")
        return render_template('admin/dashboard.html', stats=stats)
    
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Dashboard error: {e}")
        return jsonify({'error': 'Dashboard error'}), 500

@watchdog.route('/admin/users')
@admin_required
def admin_users():
    """User management"""
    try:
        users = get_all_users()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: User management error: {e}")
        return jsonify({'error': 'User management error'}), 500

@watchdog.route('/admin/database')
@admin_required
def admin_database():
    """Database management"""
    try:
        db_info = {
            'tables': get_database_tables(),
            'size': get_database_size(),
            'last_backup': get_last_backup_time(),
            'health_status': check_database_health()
        }
        return render_template('admin/database.html', db_info=db_info)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Database management error: {e}")
        return jsonify({'error': 'Database error'}), 500

@watchdog.route('/admin/surveillance')
@admin_required
def admin_surveillance():
    """System monitoring and surveillance"""
    try:
        surveillance_data = {
            'active_users': get_active_users(),
            'recent_logins': get_recent_logins(),
            'failed_attempts': get_failed_login_attempts(),
            'system_alerts': get_system_alerts(),
            'performance_metrics': get_performance_metrics()
        }
        return render_template('admin/surveillance.html', data=surveillance_data)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Surveillance error: {e}")
        return jsonify({'error': 'Surveillance error'}), 500

@watchdog.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    admin_user = session.get('admin_username', 'unknown')
    session.clear()
    logger.info(f"🔓 WATCHDOG: Admin logout for {admin_user}")
    return redirect(url_for('admin_login'))

# Helper functions
def get_user_count():
    """Get total user count"""
    try:
        # Connect to main app database
        conn = sqlite3.connect('../soulbridge.db')  # Adjust path as needed
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_active_sessions():
    """Get active session count"""
    # This would integrate with your session management
    return 0  # Placeholder

def check_database_health():
    """Check database health status"""
    try:
        conn = sqlite3.connect('../soulbridge.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return "Healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "Error"

def get_server_uptime():
    """Get server uptime"""
    # Placeholder - implement based on your deployment
    return "Unknown"

def get_trial_users_count():
    """Get count of users currently on trial"""
    # Implement based on your trial tracking
    return 0

def get_companion_stats():
    """Get companion selection statistics"""
    # Implement based on your companion tracking
    return {}

def get_all_users():
    """Get all users for admin management"""
    try:
        conn = sqlite3.connect('../soulbridge.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, display_name, created_at FROM users ORDER BY created_at DESC LIMIT 100")
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

def get_database_tables():
    """Get database table information"""
    try:
        conn = sqlite3.connect('../soulbridge.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        return [table[0] for table in tables]
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

def get_database_size():
    """Get database size"""
    try:
        import os
        size = os.path.getsize('../soulbridge.db')
        return f"{size / 1024 / 1024:.2f} MB"
    except Exception as e:
        logger.error(f"Error getting database size: {e}")
        return "Unknown"

def get_last_backup_time():
    """Get last backup time"""
    # Implement based on your backup strategy
    return "Not configured"

def get_active_users():
    """Get currently active users"""
    # Implement based on your session tracking
    return []

def get_recent_logins():
    """Get recent login attempts"""
    # Implement based on your logging
    return []

def get_failed_login_attempts():
    """Get failed login attempts"""
    # Implement based on your security logging
    return []

def get_system_alerts():
    """Get system alerts"""
    # Implement based on your monitoring
    return []

def get_performance_metrics():
    """Get performance metrics"""
    # Implement based on your monitoring
    return {}

if __name__ == '__main__':
    print("🐕 WatchDog Admin System Starting...")
    print("🎯 Admin Dashboard: http://localhost:5001/admin")
    print("🔐 Default credentials: admin / admin123")
    
    watchdog.run(
        host='0.0.0.0',
        port=5001,  # Different port from main app
        debug=True
    )