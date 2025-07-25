"""
AI Insights API Endpoints
REST API for accessing mood analytics, personality insights, and recommendations
"""
import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import asdict
import json

from ai_insights import get_ai_insights

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

logger = logging.getLogger(__name__)

# Create insights API blueprint
insights_api = Blueprint('insights_api', __name__, url_prefix='/api/insights')

@insights_api.route('/mood-patterns', methods=['GET'])
@require_auth
def get_mood_patterns():
    """Get user's mood patterns and analysis"""
    try:
        user_id = session.get('user_id')
        days = request.args.get('days', default=30, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            return jsonify({'error': 'Days must be between 1 and 365'}), 400
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        patterns = ai_insights.analyze_mood_patterns(user_id, days)
        
        # Convert patterns to dict format
        patterns_data = [asdict(pattern) for pattern in patterns]
        
        return jsonify({
            'success': True,
            'patterns': patterns_data,
            'analysis_period_days': days,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting mood patterns: {e}")
        return jsonify({'error': 'Failed to analyze mood patterns'}), 500

@insights_api.route('/personality', methods=['GET'])
@require_auth
def get_personality_insights():
    """Get user's personality analysis"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        personality = ai_insights.analyze_personality(user_id)
        
        if not personality:
            return jsonify({
                'success': False,
                'message': 'Not enough data to generate personality insights',
                'suggestion': 'Continue using the app to build your personality profile'
            }), 200
        
        personality_data = asdict(personality)
        
        return jsonify({
            'success': True,
            'personality': personality_data,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting personality insights: {e}")
        return jsonify({'error': 'Failed to analyze personality'}), 500

@insights_api.route('/companion-recommendations', methods=['GET'])
@require_auth
def get_companion_recommendations():
    """Get personalized AI companion recommendations"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        recommendations = ai_insights.recommend_companions(user_id)
        
        # Convert recommendations to dict format
        recommendations_data = [asdict(rec) for rec in recommendations]
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_data,
            'total_companions': len(recommendations_data),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting companion recommendations: {e}")
        return jsonify({'error': 'Failed to generate recommendations'}), 500

@insights_api.route('/friend-matches', methods=['GET'])
@require_auth
def get_friend_matches():
    """Get smart friend matching suggestions"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        matches = ai_insights.find_friend_matches(user_id)
        
        # Convert matches to dict format
        matches_data = [asdict(match) for match in matches]
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'total_matches': len(matches_data),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting friend matches: {e}")
        return jsonify({'error': 'Failed to find friend matches'}), 500

@insights_api.route('/wellness-alerts', methods=['GET'])
@require_auth
def get_wellness_alerts():
    """Get predictive wellness alerts"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        alerts = ai_insights.generate_wellness_alerts(user_id)
        
        # Convert alerts to dict format
        alerts_data = [asdict(alert) for alert in alerts]
        
        # Sort by severity and creation time
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        alerts_data.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['created_at']), reverse=True)
        
        return jsonify({
            'success': True,
            'alerts': alerts_data,
            'total_alerts': len(alerts_data),
            'high_priority_count': len([a for a in alerts_data if a['severity'] == 'high']),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting wellness alerts: {e}")
        return jsonify({'error': 'Failed to generate wellness alerts'}), 500

@insights_api.route('/comprehensive', methods=['GET'])
@require_auth
def get_comprehensive_insights():
    """Get all user insights in one comprehensive report"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        comprehensive = ai_insights.get_comprehensive_insights(user_id)
        
        if not comprehensive:
            return jsonify({
                'success': False,
                'message': 'Not enough data to generate comprehensive insights',
                'suggestion': 'Continue using the app to build your profile'
            }), 200
        
        # Convert to dict format
        insights_data = asdict(comprehensive)
        
        return jsonify({
            'success': True,
            'insights': insights_data,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive insights: {e}")
        return jsonify({'error': 'Failed to generate comprehensive insights'}), 500

@insights_api.route('/dashboard-data', methods=['GET'])
@require_auth
def get_dashboard_data():
    """Get summary data for insights dashboard"""
    try:
        user_id = session.get('user_id')
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        # Get recent mood patterns (last 7 days)
        recent_patterns = ai_insights.analyze_mood_patterns(user_id, days=7)
        
        # Get wellness alerts
        alerts = ai_insights.generate_wellness_alerts(user_id)
        
        # Get top companion recommendations (top 3)
        companions = ai_insights.recommend_companions(user_id)[:3]
        
        # Get friend matches (top 5)
        friends = ai_insights.find_friend_matches(user_id)[:5]
        
        # Calculate summary statistics
        total_moods = len(recent_patterns)
        avg_mood_score = sum(p.average_score for p in recent_patterns) / total_moods if total_moods > 0 else 0
        
        high_priority_alerts = [a for a in alerts if a.severity == 'high']
        
        dashboard_data = {
            'summary': {
                'total_mood_patterns': total_moods,
                'average_mood_score': round(avg_mood_score, 2),
                'total_alerts': len(alerts),
                'high_priority_alerts': len(high_priority_alerts),
                'top_companions': len(companions),
                'friend_matches': len(friends)
            },
            'recent_patterns': [asdict(p) for p in recent_patterns[:5]],
            'active_alerts': [asdict(a) for a in alerts[:3]],
            'recommended_companions': [asdict(c) for c in companions],
            'suggested_friends': [asdict(f) for f in friends],
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@insights_api.route('/mood-trends', methods=['GET'])
@require_auth
def get_mood_trends():
    """Get detailed mood trends and analytics"""
    try:
        user_id = session.get('user_id')
        period = request.args.get('period', default='week')  # week, month, quarter
        
        if period not in ['week', 'month', 'quarter']:
            return jsonify({'error': 'Invalid period. Use week, month, or quarter'}), 400
        
        # Map period to days
        period_days = {
            'week': 7,
            'month': 30,
            'quarter': 90
        }
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        patterns = ai_insights.analyze_mood_patterns(user_id, days=period_days[period])
        
        # Calculate trend data
        trends = []
        for pattern in patterns:
            trend_data = {
                'mood': pattern.dominant_mood,
                'average_score': pattern.average_score,
                'stability': pattern.mood_stability,
                'trend_direction': 'improving' if pattern.trends.get('weekly', 0) > 0.05 else 
                                'declining' if pattern.trends.get('weekly', 0) < -0.05 else 'stable',
                'change_percentage': pattern.trends.get('weekly', 0) * 100,
                'common_times': pattern.common_times,
                'triggers': pattern.triggers
            }
            trends.append(trend_data)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'period': period,
            'analysis_days': period_days[period],
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting mood trends: {e}")
        return jsonify({'error': 'Failed to analyze mood trends'}), 500

@insights_api.route('/export', methods=['GET'])
@require_auth
def export_insights():
    """Export comprehensive insights data"""
    try:
        user_id = session.get('user_id')
        format_type = request.args.get('format', default='json')  # json, csv future
        
        if format_type != 'json':
            return jsonify({'error': 'Only JSON export currently supported'}), 400
        
        ai_insights = get_ai_insights()
        if not ai_insights:
            return jsonify({'error': 'AI insights service unavailable'}), 503
        
        comprehensive = ai_insights.get_comprehensive_insights(user_id)
        
        if not comprehensive:
            return jsonify({'error': 'No insights data available for export'}), 404
        
        # Create export package
        export_data = {
            'user_id': user_id,
            'export_timestamp': datetime.now().isoformat(),
            'insights': asdict(comprehensive),
            'metadata': {
                'version': '1.0',
                'format': format_type,
                'description': 'SoulBridge AI Comprehensive Insights Export'
            }
        }
        
        return jsonify({
            'success': True,
            'export': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting insights: {e}")
        return jsonify({'error': 'Failed to export insights'}), 500

# Health check endpoint
@insights_api.route('/health', methods=['GET'])
def health_check():
    """Health check for insights API"""
    try:
        ai_insights = get_ai_insights()
        service_status = 'available' if ai_insights else 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'service': service_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def init_insights_api():
    """Initialize insights API"""
    logger.info("AI Insights API initialized")
    return insights_api