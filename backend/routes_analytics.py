# routes_analytics.py
# Analytics API endpoints for usage tracking and dashboard data

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime, timezone, timedelta
from app_core import current_user
from db_users import db_get_user_plan, db_fetch_user_row
from access import get_effective_access

logger = logging.getLogger(__name__)

bp_analytics = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@bp_analytics.route("/dashboard", methods=["GET"])
def analytics_dashboard():
    """
    Render the analytics dashboard page.
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return render_template('login.html', error="Please log in to view analytics"), 401
        
        return render_template('analytics.html')
        
    except Exception as e:
        logger.error(f"Error rendering analytics dashboard: {e}")
        return render_template('error.html', error="Failed to load analytics"), 500

@bp_analytics.route("/usage", methods=["GET"])
def get_usage_analytics():
    """
    Get usage analytics for the current user.
    
    Query Parameters:
        - period: Number of days to analyze (default: 7, max: 90)
        - include_details: Whether to include detailed breakdowns (default: false)
    
    Returns:
        - User usage statistics
        - Feature usage breakdown
        - Companion interaction data
        - Time-based trends
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Parse query parameters
        period = min(int(request.args.get('period', 7)), 90)  # Max 90 days
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        # Get user plan and access info
        plan = db_get_user_plan(uid)
        user_data = db_fetch_user_row(uid)
        
        if not user_data:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Get effective access for feature limits
        from db_users import db_get_trial_state
        trial_active, trial_expires_at = db_get_trial_state(uid)
        access = get_effective_access(plan, trial_active, trial_expires_at)
        
        # Generate analytics data (simulated for now - in production would query actual usage logs)
        analytics_data = generate_usage_analytics(uid, period, plan, access, include_details)
        
        return jsonify({
            "success": True,
            "user": {
                "id": uid,
                "plan": plan,
                "email": user_data.get('email'),
                "display_name": user_data.get('display_name', 'User')
            },
            "period_days": period,
            "analytics": analytics_data
        })
        
    except Exception as e:
        logger.error(f"Error getting usage analytics for user {uid}: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@bp_analytics.route("/insights", methods=["GET"])
def get_ai_insights():
    """
    Get AI-generated insights about user behavior and recommendations.
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        # Get user plan for context
        plan = db_get_user_plan(uid)
        
        # Generate AI insights (simulated for now)
        insights = generate_ai_insights(uid, plan)
        
        return jsonify({
            "success": True,
            "insights": insights
        })
        
    except Exception as e:
        logger.error(f"Error generating insights for user {uid}: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

@bp_analytics.route("/export", methods=["POST"])
def export_analytics():
    """
    Export user analytics data in various formats.
    
    Request Body:
        - format: 'json', 'csv', or 'pdf' (default: json)
        - period: Number of days to include (default: 30)
        - include_raw_data: Whether to include raw interaction logs (default: false)
    """
    try:
        cu = current_user()
        uid = cu.get("id")
        
        if not uid:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        data = request.get_json() or {}
        export_format = data.get('format', 'json').lower()
        period = min(int(data.get('period', 30)), 90)
        include_raw = data.get('include_raw_data', False)
        
        if export_format not in ['json', 'csv', 'pdf']:
            return jsonify({
                "success": False,
                "error": "Invalid export format. Use 'json', 'csv', or 'pdf'"
            }), 400
        
        # Get user plan
        plan = db_get_user_plan(uid)
        
        # Check if user can export (feature restriction)
        if plan == 'bronze' and export_format != 'json':
            return jsonify({
                "success": False,
                "error": "Advanced export formats require Silver or Gold plan"
            }), 403
        
        # Generate export data
        export_data = generate_export_data(uid, period, export_format, include_raw)
        
        return jsonify({
            "success": True,
            "export": export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting analytics for user {uid}: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

def generate_usage_analytics(user_id, period_days, plan, access, include_details=False):
    """
    Generate comprehensive usage analytics for a user.
    
    In production, this would query actual usage logs from the database.
    For now, we'll generate realistic simulated data.
    """
    import random
    from datetime import datetime, timedelta
    
    # Base stats influenced by plan
    plan_multipliers = {
        'bronze': 1.0,
        'silver': 2.5,
        'gold': 4.0
    }
    multiplier = plan_multipliers.get(plan, 1.0)
    
    # Generate daily activity data
    daily_activity = []
    for i in range(period_days):
        date = datetime.now() - timedelta(days=i)
        conversations = max(0, int(random.gauss(3 * multiplier, 2)))
        time_spent = max(0, int(random.gauss(15 * multiplier, 10)))  # minutes
        
        daily_activity.append({
            "date": date.strftime("%Y-%m-%d"),
            "conversations": conversations,
            "time_spent_minutes": time_spent,
            "features_used": random.randint(1, 4)
        })
    
    # Feature usage based on access limits
    limits = access.get('limits', {})
    feature_usage = {}
    
    for feature, limit in limits.items():
        if limit == float('inf'):
            used = random.randint(15, 50)  # Unlimited usage simulation
        else:
            used = random.randint(0, min(limit, int(limit * 0.8)))  # Realistic usage
        
        feature_usage[feature] = {
            "used_today": used,
            "limit_daily": limit if limit != float('inf') else None,
            "used_this_period": used * period_days,
            "average_daily": round(used * period_days / period_days, 1)
        }
    
    # Companion interaction data
    available_companions = get_available_companions(access.get('accessible_companion_tiers', ['bronze']))
    companion_usage = {}
    
    for companion in available_companions:
        interactions = random.randint(0, 20)
        companion_usage[companion] = {
            "interactions": interactions,
            "avg_session_length": random.randint(5, 25),  # minutes
            "last_interaction": (datetime.now() - timedelta(days=random.randint(0, period_days))).isoformat()
        }
    
    # Calculate totals
    total_conversations = sum(day["conversations"] for day in daily_activity)
    total_time = sum(day["time_spent_minutes"] for day in daily_activity)
    
    # Streak calculation (simulated)
    current_streak = random.randint(1, min(period_days, 15))
    
    # Most used companion
    favorite_companion = max(companion_usage.keys(), key=lambda x: companion_usage[x]["interactions"]) if companion_usage else "None"
    
    analytics = {
        "summary": {
            "total_conversations": total_conversations,
            "total_time_minutes": total_time,
            "total_time_hours": round(total_time / 60, 1),
            "average_daily_conversations": round(total_conversations / period_days, 1),
            "average_session_length": round(total_time / max(total_conversations, 1), 1),
            "current_streak_days": current_streak,
            "favorite_companion": favorite_companion
        },
        "feature_usage": feature_usage,
        "companion_usage": companion_usage,
        "daily_activity": daily_activity[:7] if not include_details else daily_activity,  # Limit for performance
        "period_analysis": {
            "most_active_day": max(daily_activity, key=lambda x: x["conversations"])["date"],
            "least_active_day": min(daily_activity, key=lambda x: x["conversations"])["date"],
            "total_features_used": sum(day["features_used"] for day in daily_activity),
            "consistency_score": calculate_consistency_score(daily_activity)
        }
    }
    
    if include_details:
        analytics["detailed_breakdown"] = generate_detailed_breakdown(user_id, period_days)
    
    return analytics

def generate_ai_insights(user_id, plan):
    """
    Generate AI-powered insights and recommendations.
    """
    import random
    
    # Simulated insights based on user behavior patterns
    usage_patterns = [
        "You're most active in the evening hours, showing consistent engagement",
        "Your conversation length has increased by 25% over the past month",
        "You show strong preference for emotional support conversations",
        "Your usage pattern indicates a focus on personal growth and reflection"
    ]
    
    recommendations = {
        'bronze': [
            "Consider upgrading to Silver for access to more advanced features",
            "Try exploring the Creative Writer feature to enhance your expression",
            "Your usage suggests you'd benefit from higher daily limits"
        ],
        'silver': [
            "You're maximizing your Silver plan benefits effectively",
            "Consider trying voice journaling for deeper self-reflection",
            "Your engagement level suggests Gold plan might be worthwhile"
        ],
        'gold': [
            "You're making excellent use of unlimited features",
            "Try the Mini Studio for creative expression",
            "Your consistent usage shows great commitment to personal growth"
        ]
    }
    
    wellness_insights = [
        "Your conversation patterns show increasing emotional awareness",
        "You've maintained consistent engagement, indicating strong motivation",
        "Your diverse feature usage suggests a holistic approach to wellness",
        "Your streak shows excellent habit formation and commitment"
    ]
    
    return {
        "usage_pattern": random.choice(usage_patterns),
        "recommendation": random.choice(recommendations.get(plan, recommendations['bronze'])),
        "wellness_insight": random.choice(wellness_insights),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "confidence_score": round(random.uniform(0.75, 0.95), 2)
    }

def generate_detailed_breakdown(user_id, period_days):
    """
    Generate detailed usage breakdown for power users.
    """
    import random
    
    return {
        "hourly_distribution": {str(hour): random.randint(0, 10) for hour in range(24)},
        "feature_correlation": {
            "decoder_fortune": random.uniform(0.3, 0.8),
            "horoscope_creative": random.uniform(0.2, 0.7),
            "companion_consistency": random.uniform(0.5, 0.9)
        },
        "engagement_metrics": {
            "average_response_time": random.randint(30, 180),  # seconds
            "conversation_depth_score": random.uniform(0.6, 0.95),
            "feature_exploration_score": random.uniform(0.4, 0.85)
        }
    }

def generate_export_data(user_id, period, format_type, include_raw):
    """
    Generate export data in the requested format.
    """
    # This would generate actual export files in production
    export_info = {
        "format": format_type,
        "period_days": period,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_size_estimate": f"{random.randint(10, 100)}KB",
        "download_url": f"/api/analytics/download/{user_id}/{format_type}",  # Would be actual file URL
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    }
    
    if format_type == 'json':
        export_info["preview"] = {
            "total_records": random.randint(50, 500),
            "data_types": ["conversations", "feature_usage", "time_tracking"]
        }
    elif format_type == 'csv':
        export_info["columns"] = ["date", "conversations", "time_spent", "features_used", "companion"]
    elif format_type == 'pdf':
        export_info["pages"] = random.randint(5, 15)
        export_info["includes_charts"] = True
    
    return export_info

def get_available_companions(accessible_tiers):
    """
    Get list of available companions based on accessible tiers.
    """
    companion_tiers = {
        'bronze': ['Blayzo', 'Blayzica', 'GamerJay'],
        'silver': ['Sky', 'Blayzo Premium', 'Blayzica Growth'],
        'gold': ['Companion Crimson', 'Companion Violet', 'Royal Max']
    }
    
    available = []
    for tier in accessible_tiers:
        available.extend(companion_tiers.get(tier, []))
    
    return list(set(available))  # Remove duplicates

def calculate_consistency_score(daily_activity):
    """
    Calculate a consistency score based on daily activity variance.
    """
    if not daily_activity:
        return 0.0
    
    conversations = [day["conversations"] for day in daily_activity]
    if not conversations:
        return 0.0
    
    avg = sum(conversations) / len(conversations)
    if avg == 0:
        return 0.0
    
    variance = sum((x - avg) ** 2 for x in conversations) / len(conversations)
    coefficient_of_variation = (variance ** 0.5) / avg
    
    # Convert to 0-1 score (lower variance = higher consistency)
    consistency = max(0, 1 - coefficient_of_variation)
    return round(consistency, 2)