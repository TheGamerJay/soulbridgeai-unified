#!/usr/bin/env python3
"""
WatchDog Admin System - SoulBridge AI
Comprehensive admin dashboard with trial system management
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import bcrypt
import json

# Add backend directory to path to import Database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import Database

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
        if username == 'GamerJay' and password == os.environ.get('ADMIN_PASSWORD', 'Yariel13'):
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
    """WatchDog Admin Home Dashboard - Comprehensive System"""
    try:
        # Get comprehensive system stats
        stats = {
            'total_users': get_user_count(),
            'active_trials': get_active_trial_count(),
            'trial_used_permanently': get_permanent_trial_count(),
            'free_users': get_plan_count('free'),
            'growth_users': get_plan_count('growth'),
            'max_users': get_plan_count('max'),
            'admin_users': get_admin_count(),
            'daily_decoder_usage': get_daily_feature_usage('decoder'),
            'daily_fortune_usage': get_daily_feature_usage('fortune'),
            'daily_horoscope_usage': get_daily_feature_usage('horoscope'),
            'recent_actions': get_recent_actions(10),
            'database_status': check_database_health(),
            'total_actions_today': get_actions_today(),
            'trial_conversions': get_trial_conversion_rate()
        }
        
        logger.info("🔍 WATCHDOG: Comprehensive admin dashboard accessed")
        return render_template('admin/dashboard.html', stats=stats)
    
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Dashboard error: {e}")
        return jsonify({'error': 'Dashboard error'}), 500

@watchdog.route('/admin/users')
@admin_required
def admin_users():
    """Comprehensive User Management"""
    try:
        # Get all users with comprehensive data
        users = get_all_users_comprehensive()
        
        # Get filter parameters
        plan_filter = request.args.get('plan', 'all')
        trial_filter = request.args.get('trial', 'all')
        admin_filter = request.args.get('admin', 'all')
        
        # Apply filters
        if plan_filter != 'all':
            users = [u for u in users if u.get('user_plan') == plan_filter]
        if trial_filter == 'active':
            users = [u for u in users if u.get('trial_active')]
        elif trial_filter == 'used':
            users = [u for u in users if u.get('trial_used_permanently')]
        if admin_filter == 'true':
            users = [u for u in users if u.get('is_admin')]
        elif admin_filter == 'false':
            users = [u for u in users if not u.get('is_admin')]
        
        return render_template('admin/users.html', 
                             users=users, 
                             plan_filter=plan_filter,
                             trial_filter=trial_filter,
                             admin_filter=admin_filter)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: User management error: {e}")
        return jsonify({'error': 'User management error'}), 500

@watchdog.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    """Edit specific user"""
    try:
        if request.method == 'POST':
            # Update user data
            user_plan = request.form.get('user_plan')
            is_admin = request.form.get('is_admin') == 'on'
            trial_active = request.form.get('trial_active') == 'on'
            trial_used_permanently = request.form.get('trial_used_permanently') == 'on'
            
            update_user_admin(user_id, {
                'user_plan': user_plan,
                'is_admin': is_admin,
                'trial_active': trial_active,
                'trial_used_permanently': trial_used_permanently
            })
            
            logger.info(f"🔧 WATCHDOG: User {user_id} updated by admin")
            return redirect(url_for('admin_users'))
        
        # Get user data for editing
        user = get_user_by_id(user_id)
        return render_template('admin/edit_user.html', user=user)
        
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Edit user error: {e}")
        return jsonify({'error': 'Edit user error'}), 500

@watchdog.route('/admin/trials')
@admin_required
def admin_trials():
    """Trial System Management"""
    try:
        trial_data = {
            'active_trials': get_active_trials_detailed(),
            'expired_trials': get_expired_trials(50),
            'trial_stats': {
                'total_started': get_total_trials_started(),
                'conversion_rate': get_trial_conversion_rate(),
                'average_duration_before_upgrade': get_avg_trial_duration(),
                'most_active_trial_hour': get_peak_trial_hour()
            },
            'recent_trial_activity': get_recent_trial_activity(20)
        }
        
        return render_template('admin/trials.html', data=trial_data)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Trial management error: {e}")
        return jsonify({'error': 'Trial management error'}), 500

@watchdog.route('/admin/analytics')
@admin_required
def admin_analytics():
    """User Analytics and Action Logs"""
    try:
        analytics_data = {
            'daily_actions': get_daily_action_stats(30),
            'feature_usage': get_feature_usage_stats(),
            'user_journey': get_user_journey_stats(),
            'top_actions': get_top_actions(10),
            'recent_logs': get_recent_action_logs(100),
            'hourly_activity': get_hourly_activity_stats()
        }
        
        return render_template('admin/analytics.html', data=analytics_data)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: Analytics error: {e}")
        return jsonify({'error': 'Analytics error'}), 500

@watchdog.route('/admin/system')
@admin_required
def admin_system():
    """System Management and Controls"""
    try:
        system_data = {
            'database_info': get_database_info(),
            'system_health': get_system_health(),
            'recent_errors': get_recent_errors(20),
            'performance_metrics': get_performance_metrics(),
            'maintenance_tasks': get_maintenance_tasks()
        }
        
        return render_template('admin/system.html', data=system_data)
    except Exception as e:
        logger.error(f"❌ WATCHDOG: System management error: {e}")
        return jsonify({'error': 'System management error'}), 500

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

# Comprehensive Helper Functions
def get_db():
    """Get database instance"""
    try:
        return Database()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_user_count():
    """Get total user count"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def get_active_trial_count():
    """Get count of users with active trials"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_active = TRUE")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_active = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting active trial count: {e}")
        return 0

def get_permanent_trial_count():
    """Get count of users who have used their trial permanently"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = TRUE")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting permanent trial count: {e}")
        return 0

def get_plan_count(plan):
    """Get count of users by plan"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = %s", (plan,))
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = ?", (plan,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting plan count: {e}")
        return 0

def get_admin_count():
    """Get count of admin users"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting admin count: {e}")
        return 0

def get_daily_feature_usage(feature):
    """Get daily usage count for a feature"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        column = f"{feature}_used"
        cursor.execute(f"SELECT SUM({column}) FROM users WHERE {column} IS NOT NULL")
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0
    except Exception as e:
        logger.error(f"Error getting daily feature usage: {e}")
        return 0

def get_recent_actions(limit=10):
    """Get recent user actions"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if action_logs table exists
        try:
            cursor.execute("SELECT user_id, action, timestamp FROM action_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            actions = cursor.fetchall()
            conn.close()
            return [{'user_id': a[0], 'action': a[1], 'timestamp': a[2]} for a in actions]
        except:
            # Table doesn't exist yet
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Error getting recent actions: {e}")
        return []

def get_actions_today():
    """Get total actions today"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection() 
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            if db.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM action_logs WHERE DATE(timestamp) = %s", (today,))
            else:
                cursor.execute("SELECT COUNT(*) FROM action_logs WHERE DATE(timestamp) = ?", (today,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            conn.close()
            return 0
    except Exception as e:
        logger.error(f"Error getting actions today: {e}")
        return 0

def get_trial_conversion_rate():
    """Calculate trial to paid conversion rate"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get users who used trial
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = TRUE")
            total_trials = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = TRUE AND user_plan IN ('growth', 'max')")
            converted = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1")
            total_trials = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1 AND user_plan IN ('growth', 'max')")
            converted = cursor.fetchone()[0]
        
        conn.close()
        if total_trials > 0:
            return round((converted / total_trials) * 100, 1)
        return 0
    except Exception as e:
        logger.error(f"Error calculating conversion rate: {e}")
        return 0

def get_all_users_comprehensive():
    """Get all users with comprehensive trial system data"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, display_name, user_plan, trial_active, trial_started_at,
                   trial_used_permanently, is_admin, decoder_used, fortune_used, 
                   horoscope_used, created_at, last_login
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 200
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'display_name': row[2],
                'user_plan': row[3] or 'free',
                'trial_active': bool(row[4]) if row[4] is not None else False,
                'trial_started_at': row[5],
                'trial_used_permanently': bool(row[6]) if row[6] is not None else False,
                'is_admin': bool(row[7]) if row[7] is not None else False,
                'decoder_used': row[8] or 0,
                'fortune_used': row[9] or 0,
                'horoscope_used': row[10] or 0,
                'created_at': row[11],
                'last_login': row[12]
            })
        
        conn.close()
        return users
    except Exception as e:
        logger.error(f"Error getting comprehensive users: {e}")
        return []

def get_user_by_id(user_id):
    """Get specific user by ID"""
    try:
        db = get_db()
        if not db:
            return None
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("""
                SELECT id, email, display_name, user_plan, trial_active, trial_started_at,
                       trial_used_permanently, is_admin, decoder_used, fortune_used, 
                       horoscope_used, created_at, last_login
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, email, display_name, user_plan, trial_active, trial_started_at,
                       trial_used_permanently, is_admin, decoder_used, fortune_used, 
                       horoscope_used, created_at, last_login
                FROM users WHERE id = ?
            """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'display_name': row[2],
                'user_plan': row[3] or 'free',
                'trial_active': bool(row[4]) if row[4] is not None else False,
                'trial_started_at': row[5],
                'trial_used_permanently': bool(row[6]) if row[6] is not None else False,
                'is_admin': bool(row[7]) if row[7] is not None else False,
                'decoder_used': row[8] or 0,
                'fortune_used': row[9] or 0,
                'horoscope_used': row[10] or 0,
                'created_at': row[11],
                'last_login': row[12]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

def update_user_admin(user_id, updates):
    """Update user data from admin panel"""
    try:
        db = get_db()
        if not db:
            return False
        conn = db.get_connection()
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in ['user_plan', 'is_admin', 'trial_active', 'trial_used_permanently']:
                set_clauses.append(f"{field} = {'%s' if db.use_postgres else '?'}")
                values.append(value)
        
        if set_clauses:
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = {'%s' if db.use_postgres else '?'}"
            values.append(user_id)
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return False

# Additional Analytics Functions
def get_active_trials_detailed():
    """Get detailed information about active trials"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("""
                SELECT id, email, display_name, trial_started_at, 
                       EXTRACT(EPOCH FROM (NOW() - trial_started_at::timestamp)) as elapsed_seconds
                FROM users 
                WHERE trial_active = TRUE 
                ORDER BY trial_started_at DESC
            """)
        else:
            cursor.execute("""
                SELECT id, email, display_name, trial_started_at
                FROM users 
                WHERE trial_active = 1 
                ORDER BY trial_started_at DESC
            """)
        
        trials = []
        for row in cursor.fetchall():
            trial_data = {
                'user_id': row[0],
                'email': row[1],
                'display_name': row[2],
                'started_at': row[3]
            }
            
            # Calculate elapsed time for SQLite
            if not db.use_postgres and row[3]:
                try:
                    started = datetime.fromisoformat(row[3])
                    elapsed = (datetime.now() - started).total_seconds()
                    remaining = max(0, 18000 - elapsed)  # 5 hours = 18000 seconds
                    trial_data['elapsed'] = elapsed
                    trial_data['remaining'] = remaining
                except:
                    trial_data['elapsed'] = 0
                    trial_data['remaining'] = 18000
            elif db.use_postgres:
                elapsed = row[4] if len(row) > 4 else 0
                trial_data['elapsed'] = elapsed
                trial_data['remaining'] = max(0, 18000 - elapsed)
            
            trials.append(trial_data)
        
        conn.close()
        return trials
    except Exception as e:
        logger.error(f"Error getting active trials: {e}")
        return []

def get_expired_trials(limit=50):
    """Get recently expired trials"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("""
                SELECT id, email, display_name, trial_started_at, user_plan
                FROM users 
                WHERE trial_used_permanently = TRUE
                ORDER BY trial_started_at DESC 
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT id, email, display_name, trial_started_at, user_plan
                FROM users 
                WHERE trial_used_permanently = 1
                ORDER BY trial_started_at DESC 
                LIMIT ?
            """, (limit,))
        
        expired = []
        for row in cursor.fetchall():
            expired.append({
                'user_id': row[0],
                'email': row[1],
                'display_name': row[2],
                'started_at': row[3],
                'current_plan': row[4] or 'free'
            })
        
        conn.close()
        return expired
    except Exception as e:
        logger.error(f"Error getting expired trials: {e}")
        return []

def get_total_trials_started():
    """Get total number of trials ever started"""
    try:
        db = get_db()
        if not db:
            return 0
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_started_at IS NOT NULL")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_started_at IS NOT NULL")
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting total trials: {e}")
        return 0

def get_avg_trial_duration():
    """Get average trial duration before conversion"""
    # This would need more complex tracking
    return "Not available"

def get_peak_trial_hour():
    """Get the hour of day when most trials start"""
    # This would need timestamp analysis
    return "Not available"

def get_recent_trial_activity(limit=20):
    """Get recent trial-related activities"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get recent trial starts and expirations
        activities = []
        
        # Recent trial starts
        if db.use_postgres:
            cursor.execute("""
                SELECT email, display_name, trial_started_at, 'started' as activity
                FROM users 
                WHERE trial_started_at IS NOT NULL
                ORDER BY trial_started_at DESC 
                LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT email, display_name, trial_started_at, 'started' as activity
                FROM users 
                WHERE trial_started_at IS NOT NULL
                ORDER BY trial_started_at DESC 
                LIMIT ?
            """, (limit,))
        
        for row in cursor.fetchall():
            activities.append({
                'email': row[0],
                'display_name': row[1],
                'timestamp': row[2],
                'activity': row[3]
            })
        
        conn.close()
        return activities
    except Exception as e:
        logger.error(f"Error getting trial activity: {e}")
        return []

def check_database_health():
    """Check database health status"""
    try:
        db = get_db()
        if not db:
            return "Error - No connection"
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return "Healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return f"Error: {str(e)}"

def get_daily_action_stats(days=30):
    """Get daily action statistics"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM action_logs 
                    WHERE timestamp >= NOW() - INTERVAL '%s days'
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (days,))
            else:
                cursor.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM action_logs 
                    WHERE timestamp >= datetime('now', '-%s days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (days,))
            
            stats = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
            return stats
        except:
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Error getting daily action stats: {e}")
        return []

def get_feature_usage_stats():
    """Get feature usage statistics"""
    try:
        db = get_db()
        if not db:
            return {}
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        for feature in ['decoder', 'fortune', 'horoscope']:
            cursor.execute(f"SELECT SUM({feature}_used), AVG({feature}_used), MAX({feature}_used) FROM users WHERE {feature}_used > 0")
            result = cursor.fetchone()
            stats[feature] = {
                'total': result[0] or 0,
                'average': round(result[1] or 0, 2),
                'max': result[2] or 0
            }
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error getting feature usage stats: {e}")
        return {}

def get_user_journey_stats():
    """Get user journey statistics"""
    try:
        db = get_db()
        if not db:
            return {}
        conn = db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Free to Growth conversions
        if db.use_postgres:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'growth'")
            stats['growth_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'max'")
            stats['max_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = TRUE AND user_plan IN ('growth', 'max')")
            stats['trial_conversions'] = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'growth'")
            stats['growth_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_plan = 'max'")
            stats['max_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used_permanently = 1 AND user_plan IN ('growth', 'max')")
            stats['trial_conversions'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error getting user journey stats: {e}")
        return {}

def get_top_actions(limit=10):
    """Get most popular actions"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM action_logs 
                GROUP BY action
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))
            
            actions = [{'action': row[0], 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
            return actions
        except:
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Error getting top actions: {e}")
        return []

def get_recent_action_logs(limit=100):
    """Get recent action logs"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT al.user_id, u.email, al.action, al.timestamp, al.ip_address
                FROM action_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT ?
            """, (limit,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'user_id': row[0],
                    'email': row[1] or 'Unknown',
                    'action': row[2],
                    'timestamp': row[3],
                    'ip_address': row[4]
                })
            
            conn.close()
            return logs
        except:
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Error getting recent action logs: {e}")
        return []

def get_hourly_activity_stats():
    """Get hourly activity statistics"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute("""
                    SELECT EXTRACT(HOUR FROM timestamp) as hour, COUNT(*) as count
                    FROM action_logs 
                    WHERE timestamp >= NOW() - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM timestamp)
                    ORDER BY hour
                """)
            else:
                cursor.execute("""
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM action_logs 
                    WHERE timestamp >= datetime('now', '-7 days')
                    GROUP BY strftime('%H', timestamp)
                    ORDER BY hour
                """)
            
            stats = [{'hour': int(row[0]), 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
            return stats
        except:
            conn.close()
            return []
    except Exception as e:
        logger.error(f"Error getting hourly activity stats: {e}")
        return []

def get_database_info():
    """Get comprehensive database information"""
    try:
        db = get_db()
        if not db:
            return {}
        
        info = {
            'type': 'PostgreSQL' if db.use_postgres else 'SQLite',
            'health': check_database_health(),
            'tables': get_database_tables(),
            'user_count': get_user_count()
        }
        
        if not db.use_postgres:
            try:
                import os
                size = os.path.getsize('soulbridge.db')
                info['size'] = f"{size / 1024 / 1024:.2f} MB"
            except:
                info['size'] = "Unknown"
        
        return info
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {}

def get_database_tables():
    """Get database table information"""
    try:
        db = get_db()
        if not db:
            return []
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

def get_system_health():
    """Get system health metrics"""
    return {
        'database': check_database_health(),
        'status': 'Running'
    }

def get_recent_errors(limit=20):
    """Get recent system errors"""
    # This would integrate with your logging system
    return []

def get_performance_metrics():
    """Get performance metrics"""
    return {
        'response_time': 'Good',
        'cpu_usage': 'Unknown',
        'memory_usage': 'Unknown'
    }

def get_maintenance_tasks():
    """Get maintenance tasks"""
    return [
        {'task': 'Database backup', 'status': 'Pending', 'last_run': 'Never'},
        {'task': 'Log cleanup', 'status': 'Pending', 'last_run': 'Never'},
        {'task': 'User data cleanup', 'status': 'Pending', 'last_run': 'Never'}
    ]

if __name__ == '__main__':
    print("WatchDog Admin System Starting...")
    print("Admin Dashboard: http://localhost:5001/admin")
    print("Default credentials: GamerJay / Yariel13")
    
    watchdog.run(
        host='0.0.0.0',
        port=5001,  # Different port from main app
        debug=True
    )