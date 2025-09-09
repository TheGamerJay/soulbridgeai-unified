"""
SoulBridge AI - Analytics Routes
Analytics dashboard and usage tracking endpoints
Extracted from routes_analytics.py and app.py with improvements
"""
import logging
from flask import Blueprint, jsonify, request, render_template, session
from datetime import datetime, timezone

from ..auth.session_manager import requires_login, get_user_id
from .analytics_service import AnalyticsService
from .usage_tracker import UsageTracker
from .dashboard_service import DashboardService

logger = logging.getLogger(__name__)

# Create analytics blueprint
analytics_bp = Blueprint('analytics', __name__)

# Initialize analytics services
analytics_service = AnalyticsService()
usage_tracker = UsageTracker()
dashboard_service = DashboardService()

def _check_analytics_access(user_plan: str, trial_active: bool = False) -> bool:
    """Check if user has access to analytics (Silver/Gold only)"""
    return user_plan in ['silver', 'gold'] or trial_active

@analytics_bp.route('/analytics')
@requires_login
def analytics_page():
    """Render the analytics dashboard page (All tiers - with different feature levels)"""
    try:
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # All users can access analytics, but with different feature levels
        # Bronze: Basic stats, Silver/Gold: Advanced analytics
        
        return render_template('analytics.html',
                             user_plan=user_plan,
                             trial_active=trial_active)
        
    except Exception as e:
        logger.error(f"Error rendering analytics page: {e}")
        return render_template('error.html', error="Failed to load analytics"), 500

@analytics_bp.route('/api/analytics/dashboard')
@requires_login
def get_dashboard_data():
    """Get dashboard data for analytics page"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # All users can access their analytics data
        # Bronze users get basic analytics, Silver/Gold get enhanced features
        
        period_days = request.args.get('period', 7, type=int)
        include_details = request.args.get('details', 'false').lower() == 'true'
        
        # Get dashboard data
        dashboard_data = dashboard_service.get_dashboard_data(user_id, period_days)
        
        return jsonify({
            "success": True,
            "data": dashboard_data,
            "user_tier": user_plan,
            "trial_active": trial_active
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to load dashboard data"
        }), 500

@analytics_bp.route('/api/analytics/usage')
@requires_login
def get_usage_analytics():
    """Get detailed usage analytics"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # All users can access their analytics data
        # Bronze users get basic analytics, Silver/Gold get enhanced features
        
        period_days = request.args.get('period', 7, type=int)
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        # Validate period
        if period_days not in [1, 7, 14, 30, 60, 90]:
            period_days = 7
        
        # Get analytics data
        analytics_data = analytics_service.get_user_usage_analytics(
            user_id, period_days, include_details
        )
        
        return jsonify({
            "success": True,
            "data": analytics_data,
            "period_days": period_days,
            "include_details": include_details
        })
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get usage analytics"
        }), 500

@analytics_bp.route('/api/analytics/engagement')
@requires_login
def get_engagement_insights():
    """Get user engagement insights"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # All users can access their analytics data
        # Bronze users get basic analytics, Silver/Gold get enhanced features
        
        period_days = request.args.get('period', 30, type=int)
        
        # Get engagement data
        dashboard_data = dashboard_service.get_dashboard_data(user_id, period_days)
        engagement_insights = dashboard_data.get('engagement_insights', {})
        
        return jsonify({
            "success": True,
            "engagement": engagement_insights,
            "recommendations": dashboard_data.get('recommendations', []),
            "period_days": period_days
        })
        
    except Exception as e:
        logger.error(f"Error getting engagement insights: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get engagement insights"
        }), 500

@analytics_bp.route('/api/analytics/track', methods=['POST'])
@requires_login
def track_activity():
    """Track user activity (called by frontend)"""
    try:
        user_id = get_user_id()
        data = request.get_json() or {}
        
        feature_type = data.get('feature_type')
        session_data = data.get('session_data', {})
        
        if not feature_type:
            return jsonify({
                "success": False,
                "error": "Feature type required"
            }), 400
        
        # Track the activity
        success = usage_tracker.track_feature_usage(user_id, feature_type, session_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Activity tracked successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to track activity"
            }), 500
        
    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to track activity"
        }), 500

@analytics_bp.route('/api/analytics/export')
@requires_login
def export_analytics():
    """Export user analytics data"""
    try:
        user_id = get_user_id()
        user_plan = session.get('user_plan', 'bronze')
        trial_active = session.get('trial_active', False)
        
        # Check access - Gold tier only for exports
        if user_plan != 'gold' and not trial_active:
            return jsonify({
                "success": False,
                "error": "Analytics export requires Gold tier"
            }), 403
        
        period_days = request.args.get('period', 30, type=int)
        format_type = request.args.get('format', 'json')
        
        # Get comprehensive analytics
        analytics_data = analytics_service.get_user_usage_analytics(
            user_id, period_days, include_details=True
        )
        
        if format_type == 'json':
            response = jsonify({
                "success": True,
                "export_data": analytics_data,
                "export_info": {
                    "user_id": user_id,
                    "period_days": period_days,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "format": "json"
                }
            })
            
            # Set download headers
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=soulbridge-analytics-{user_id}-{period_days}days.json'
            
            return response
        else:
            return jsonify({
                "success": False,
                "error": "Only JSON format supported currently"
            }), 400
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to export analytics"
        }), 500

# Admin analytics endpoints
@analytics_bp.route('/api/admin/analytics/overview')
@requires_login
def admin_analytics_overview():
    """Get system-wide analytics overview (admin only)"""
    try:
        # Check admin access
        if not session.get('is_admin', False):
            return jsonify({
                "success": False,
                "error": "Admin access required"
            }), 403
        
        period_days = request.args.get('period', 7, type=int)
        
        # Get admin analytics
        admin_data = dashboard_service.get_admin_analytics(period_days)
        
        return jsonify({
            "success": True,
            "admin_analytics": admin_data,
            "period_days": period_days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting admin analytics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get admin analytics"
        }), 500

def init_analytics_system(app):
    """Initialize analytics system"""
    global usage_tracker
    
    # Set up periodic cleanup of old activity logs
    if app.config.get('AUTO_CLEANUP_ANALYTICS', True):
        import threading
        import time
        
        def cleanup_worker():
            while True:
                try:
                    time.sleep(86400)  # Run daily
                    cleaned = usage_tracker.cleanup_old_logs(90)  # Keep 90 days
                    logger.info(f"Analytics cleanup: removed {cleaned} old log entries")
                except Exception as e:
                    logger.error(f"Error in analytics cleanup worker: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Analytics cleanup worker started")
    
    logger.info("Analytics system initialized successfully")