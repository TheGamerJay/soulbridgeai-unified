"""
Creator Portal API Endpoints
REST API for content creators, monetization, and marketplace features
"""
import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import asdict
import json
import decimal

from creator_portal import get_creator_portal_manager, MonetizationModel, ContentStatus, CreatorStatus

logger = logging.getLogger(__name__)

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

# Create creator portal API blueprint
creator_portal_api = Blueprint('creator_portal_api', __name__, url_prefix='/api/creator')

@creator_portal_api.route('/profile', methods=['POST'])
@require_auth
def create_creator_profile():
    """Create a new creator profile"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        business_name = data.get('business_name')
        specializations = data.get('specializations', [])
        bio = data.get('bio')
        website = data.get('website')
        
        if not business_name or not specializations or not bio:
            return jsonify({'error': 'Business name, specializations, and bio are required'}), 400
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        creator_id = creator_manager.create_creator_profile(
            user_id=user_id,
            business_name=business_name,
            specializations=specializations,
            bio=bio,
            website=website
        )
        
        if creator_id:
            return jsonify({
                'success': True,
                'creator_id': creator_id,
                'message': 'Creator profile created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create creator profile'}), 500
            
    except Exception as e:
        logger.error(f"Error creating creator profile: {e}")
        return jsonify({'error': 'Failed to create creator profile'}), 500

@creator_portal_api.route('/profile', methods=['GET'])
@require_auth
def get_creator_profile():
    """Get creator profile for authenticated user"""
    try:
        user_id = session.get('user_id')
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        query = """
            SELECT * FROM creator_profiles WHERE user_id = ?
        """
        
        result = creator_manager.db.fetch_one(query, (user_id,))
        
        if result:
            profile_data = {
                'creator_id': result[0],
                'user_id': result[1],
                'business_name': result[2],
                'creator_status': result[3],
                'specializations': json.loads(result[4]) if result[4] else [],
                'bio': result[5],
                'website': result[6],
                'social_links': json.loads(result[7]) if result[7] else {},
                'revenue_share': result[11],
                'total_earnings': float(result[12]),
                'total_sales': result[13],
                'rating': result[14],
                'created_at': result[15],
                'verified_at': result[16]
            }
            
            return jsonify({
                'success': True,
                'profile': profile_data
            })
        else:
            return jsonify({'error': 'Creator profile not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting creator profile: {e}")
        return jsonify({'error': 'Failed to get creator profile'}), 500

@creator_portal_api.route('/content', methods=['POST'])
@require_auth
def create_content():
    """Create new monetized content"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID from user ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found. Please create a profile first.'}), 400
        
        creator_id = creator_result[0]
        
        title = data.get('title')
        description = data.get('description')
        content_type = data.get('content_type')
        category = data.get('category')
        monetization_model = data.get('monetization_model')
        price = data.get('price')
        subscription_price_monthly = data.get('subscription_price_monthly')
        
        if not title or not description or not content_type or not category or not monetization_model:
            return jsonify({'error': 'Title, description, content_type, category, and monetization_model are required'}), 400
        
        # Validate monetization model
        try:
            monetization_enum = MonetizationModel(monetization_model)
        except ValueError:
            return jsonify({'error': 'Invalid monetization model'}), 400
        
        # Convert prices to Decimal if provided
        price_decimal = decimal.Decimal(str(price)) if price else None
        subscription_decimal = decimal.Decimal(str(subscription_price_monthly)) if subscription_price_monthly else None
        
        content_id = creator_manager.create_content(
            creator_id=creator_id,
            title=title,
            description=description,
            content_type=content_type,
            category=category,
            monetization_model=monetization_enum,
            price=price_decimal,
            subscription_price_monthly=subscription_decimal
        )
        
        if content_id:
            return jsonify({
                'success': True,
                'content_id': content_id,
                'message': 'Content created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create content'}), 500
            
    except Exception as e:
        logger.error(f"Error creating content: {e}")
        return jsonify({'error': 'Failed to create content'}), 500

@creator_portal_api.route('/content', methods=['GET'])
@require_auth
def get_creator_content():
    """Get all content for authenticated creator"""
    try:
        user_id = session.get('user_id')
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found'}), 400
        
        creator_id = creator_result[0]
        
        query = """
            SELECT * FROM creator_content 
            WHERE creator_id = ? 
            ORDER BY created_at DESC
        """
        
        results = creator_manager.db.fetch_all(query, (creator_id,))
        
        content_list = []
        for row in results:
            content_data = {
                'content_id': row[0],
                'creator_id': row[1],
                'title': row[2],
                'description': row[3],
                'content_type': row[4],
                'category': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'monetization_model': row[7],
                'price': float(row[8]) if row[8] else None,
                'subscription_price_monthly': float(row[9]) if row[9] else None,
                'content_status': row[10],
                'difficulty_level': row[14],
                'target_audience': row[15],
                'view_count': row[18],
                'purchase_count': row[19],
                'rating': row[20],
                'rating_count': row[21],
                'revenue_generated': float(row[22]),
                'created_at': row[23],
                'published_at': row[24],
                'updated_at': row[25]
            }
            content_list.append(content_data)
        
        return jsonify({
            'success': True,
            'content': content_list,
            'total': len(content_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting creator content: {e}")
        return jsonify({'error': 'Failed to get creator content'}), 500

@creator_portal_api.route('/content/<content_id>/submit', methods=['POST'])
@require_auth
def submit_content_for_review(content_id):
    """Submit content for platform review"""
    try:
        user_id = session.get('user_id')
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found'}), 400
        
        creator_id = creator_result[0]
        
        success = creator_manager.submit_content_for_review(content_id, creator_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Content submitted for review successfully'
            })
        else:
            return jsonify({'error': 'Failed to submit content for review'}), 500
            
    except Exception as e:
        logger.error(f"Error submitting content for review: {e}")
        return jsonify({'error': 'Failed to submit content for review'}), 500

@creator_portal_api.route('/analytics', methods=['GET'])
@require_auth
def get_creator_analytics():
    """Get comprehensive analytics for creator"""
    try:
        user_id = session.get('user_id')
        days = request.args.get('days', default=30, type=int)
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found'}), 400
        
        creator_id = creator_result[0]
        
        analytics = creator_manager.get_creator_analytics(creator_id, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting creator analytics: {e}")
        return jsonify({'error': 'Failed to get creator analytics'}), 500

@creator_portal_api.route('/marketplace', methods=['GET'])
def get_marketplace_content():
    """Get content for marketplace discovery"""
    try:
        category = request.args.get('category')
        monetization_model = request.args.get('monetization_model')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        limit = request.args.get('limit', default=20, type=int)
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Convert monetization model to enum if provided
        monetization_enum = None
        if monetization_model:
            try:
                monetization_enum = MonetizationModel(monetization_model)
            except ValueError:
                return jsonify({'error': 'Invalid monetization model'}), 400
        
        # Convert prices to Decimal if provided
        min_price_decimal = decimal.Decimal(str(min_price)) if min_price is not None else None
        max_price_decimal = decimal.Decimal(str(max_price)) if max_price is not None else None
        
        content = creator_manager.get_marketplace_content(
            category=category,
            monetization_model=monetization_enum,
            min_price=min_price_decimal,
            max_price=max_price_decimal,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'content': content,
            'total': len(content)
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace content: {e}")
        return jsonify({'error': 'Failed to get marketplace content'}), 500

@creator_portal_api.route('/content/<content_id>/purchase', methods=['POST'])
@require_auth
def purchase_content(content_id):
    """Purchase content from marketplace"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        payment_method = data.get('payment_method', 'card')
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        result = creator_manager.process_content_purchase(
            content_id=content_id,
            buyer_user_id=user_id,
            payment_method=payment_method
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error purchasing content: {e}")
        return jsonify({'error': 'Failed to purchase content'}), 500

@creator_portal_api.route('/earnings', methods=['GET'])
@require_auth
def get_creator_earnings():
    """Get detailed earnings for creator"""
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found'}), 400
        
        creator_id = creator_result[0]
        
        query = """
            SELECT ce.*, cc.title as content_title
            FROM creator_earnings ce
            LEFT JOIN creator_content cc ON ce.content_id = cc.content_id
            WHERE ce.creator_id = ?
            ORDER BY ce.created_at DESC
            LIMIT ? OFFSET ?
        """
        
        results = creator_manager.db.fetch_all(query, (creator_id, limit, offset))
        
        earnings = []
        for row in results:
            earning_data = {
                'earning_id': row[0],
                'creator_id': row[1],
                'content_id': row[2],
                'course_id': row[3],
                'user_id': row[4],
                'transaction_type': row[5],
                'gross_amount': float(row[6]),
                'platform_fee': float(row[7]),
                'creator_amount': float(row[8]),
                'payment_status': row[9],
                'payment_processor': row[10],
                'payment_reference': row[11],
                'created_at': row[12],
                'paid_out_at': row[13],
                'content_title': row[14] if row[14] else 'Unknown Content'
            }
            earnings.append(earning_data)
        
        return jsonify({
            'success': True,
            'earnings': earnings,
            'total': len(earnings),
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error getting creator earnings: {e}")
        return jsonify({'error': 'Failed to get creator earnings'}), 500

@creator_portal_api.route('/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get quick stats for creator dashboard"""
    try:
        user_id = session.get('user_id')
        
        creator_manager = get_creator_portal_manager()
        if not creator_manager:
            return jsonify({'error': 'Creator service unavailable'}), 503
        
        # Get creator ID
        creator_query = "SELECT creator_id FROM creator_profiles WHERE user_id = ?"
        creator_result = creator_manager.db.fetch_one(creator_query, (user_id,))
        
        if not creator_result:
            return jsonify({'error': 'Creator profile not found'}), 400
        
        creator_id = creator_result[0]
        
        # Get quick stats
        stats_query = """
            SELECT 
                COUNT(*) as total_content,
                SUM(view_count) as total_views,
                SUM(purchase_count) as total_purchases,
                SUM(revenue_generated) as total_revenue,
                AVG(rating) as avg_rating
            FROM creator_content 
            WHERE creator_id = ?
        """
        
        stats_result = creator_manager.db.fetch_one(stats_query, (creator_id,))
        
        # Get pending earnings
        pending_query = """
            SELECT SUM(creator_amount) as pending_earnings
            FROM creator_earnings 
            WHERE creator_id = ? AND payment_status = 'completed' AND paid_out_at IS NULL
        """
        
        pending_result = creator_manager.db.fetch_one(pending_query, (creator_id,))
        
        stats = {
            'total_content': stats_result[0] if stats_result else 0,
            'total_views': stats_result[1] if stats_result and stats_result[1] else 0,
            'total_purchases': stats_result[2] if stats_result and stats_result[2] else 0,
            'total_revenue': float(stats_result[3]) if stats_result and stats_result[3] else 0.0,
            'avg_rating': float(stats_result[4]) if stats_result and stats_result[4] else 0.0,
            'pending_earnings': float(pending_result[0]) if pending_result and pending_result[0] else 0.0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to get dashboard stats'}), 500

# Health check endpoint
@creator_portal_api.route('/health', methods=['GET'])
def health_check():
    """Health check for creator portal API"""
    try:
        creator_manager = get_creator_portal_manager()
        service_status = 'available' if creator_manager else 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'service': service_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"Creator portal health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def init_creator_portal_api():
    """Initialize creator portal API"""
    logger.info("Creator portal API initialized")
    return creator_portal_api