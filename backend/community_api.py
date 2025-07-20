"""
Community API Endpoints
REST API for wellness communities, peer support, and challenges
"""
import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import asdict
import json

from community_system import get_community_manager, CommunityType, CommunityVisibility, MembershipRole

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

# Create community API blueprint
community_api = Blueprint('community_api', __name__, url_prefix='/api/community')

@community_api.route('/communities', methods=['GET'])
@require_auth
def get_communities():
    """Get available wellness communities"""
    try:
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        # Get query parameters
        community_type = request.args.get('type')
        visibility = request.args.get('visibility', 'public')
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Build query
        query = "SELECT * FROM wellness_communities WHERE visibility = ?"
        params = [visibility]
        
        if community_type:
            query += " AND community_type = ?"
            params.append(community_type)
        
        query += " ORDER BY member_count DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = community_manager.db.fetch_all(query, tuple(params))
        
        communities = []
        for row in results:
            community_data = {
                'community_id': row[0],
                'name': row[1],
                'description': row[2],
                'community_type': row[3],
                'visibility': row[4],
                'creator_id': row[5],
                'member_count': row[6],
                'max_members': row[7],
                'guidelines': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'created_at': row[10],
                'updated_at': row[11],
                'is_verified': bool(row[12]),
                'weekly_challenge': row[15]
            }
            communities.append(community_data)
        
        return jsonify({
            'success': True,
            'communities': communities,
            'total': len(communities),
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error getting communities: {e}")
        return jsonify({'error': 'Failed to get communities'}), 500

@community_api.route('/communities', methods=['POST'])
@require_auth
def create_community():
    """Create a new wellness community"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description')
        community_type = data.get('community_type')
        visibility = data.get('visibility', 'public')
        max_members = data.get('max_members')
        
        if not name or not description or not community_type:
            return jsonify({'error': 'Name, description, and community_type are required'}), 400
        
        # Validate community type
        try:
            community_type_enum = CommunityType(community_type)
            visibility_enum = CommunityVisibility(visibility)
        except ValueError:
            return jsonify({'error': 'Invalid community_type or visibility'}), 400
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        community_id = community_manager.create_community(
            creator_id=user_id,
            name=name,
            description=description,
            community_type=community_type_enum,
            visibility=visibility_enum,
            max_members=max_members
        )
        
        if community_id:
            return jsonify({
                'success': True,
                'community_id': community_id,
                'message': 'Community created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create community'}), 500
            
    except Exception as e:
        logger.error(f"Error creating community: {e}")
        return jsonify({'error': 'Failed to create community'}), 500

@community_api.route('/communities/<community_id>/join', methods=['POST'])
@require_auth
def join_community(community_id):
    """Join a wellness community"""
    try:
        user_id = session.get('user_id')
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        success = community_manager.join_community(community_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully joined community'
            })
        else:
            return jsonify({'error': 'Failed to join community'}), 500
            
    except Exception as e:
        logger.error(f"Error joining community: {e}")
        return jsonify({'error': 'Failed to join community'}), 500

@community_api.route('/communities/<community_id>/leave', methods=['POST'])
@require_auth
def leave_community(community_id):
    """Leave a wellness community"""
    try:
        user_id = session.get('user_id')
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        # Update membership to inactive
        query = """
            UPDATE community_memberships 
            SET is_active = 0, last_active = ?
            WHERE community_id = ? AND user_id = ?
        """
        
        result = community_manager.db.execute_query(query, (datetime.now(), community_id, user_id))
        
        if result and result > 0:
            # Update community member count
            community_manager.db.execute_query(
                "UPDATE wellness_communities SET member_count = member_count - 1 WHERE community_id = ?",
                (community_id,)
            )
            
            return jsonify({
                'success': True,
                'message': 'Successfully left community'
            })
        else:
            return jsonify({'error': 'You are not a member of this community'}), 400
            
    except Exception as e:
        logger.error(f"Error leaving community: {e}")
        return jsonify({'error': 'Failed to leave community'}), 500

@community_api.route('/recommendations', methods=['GET'])
@require_auth
def get_community_recommendations():
    """Get personalized community recommendations"""
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', default=10, type=int)
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        recommendations = community_manager.get_community_recommendations(user_id, limit)
        
        recommendations_data = [asdict(rec) for rec in recommendations]
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_data,
            'total': len(recommendations_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting community recommendations: {e}")
        return jsonify({'error': 'Failed to get recommendations'}), 500

@community_api.route('/peer-support/matches', methods=['GET'])
@require_auth
def get_peer_support_matches():
    """Get peer support matches for the user"""
    try:
        user_id = session.get('user_id')
        max_matches = request.args.get('max_matches', default=5, type=int)
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        matches = community_manager.find_peer_support_matches(user_id, max_matches)
        
        matches_data = []
        for match in matches:
            match_dict = asdict(match)
            # Convert datetime objects to ISO strings
            match_dict['matched_at'] = match.matched_at.isoformat()
            if match.last_interaction:
                match_dict['last_interaction'] = match.last_interaction.isoformat()
            matches_data.append(match_dict)
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'total': len(matches_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting peer support matches: {e}")
        return jsonify({'error': 'Failed to get peer support matches'}), 500

@community_api.route('/peer-support/matches/<match_id>/accept', methods=['POST'])
@require_auth
def accept_peer_match(match_id):
    """Accept a peer support match"""
    try:
        user_id = session.get('user_id')
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        # Update match status to active
        query = """
            UPDATE peer_support_matches 
            SET status = 'active', last_interaction = ?
            WHERE match_id = ? AND (user1_id = ? OR user2_id = ?)
        """
        
        result = community_manager.db.execute_query(query, 
                                                  (datetime.now(), match_id, user_id, user_id))
        
        if result and result > 0:
            return jsonify({
                'success': True,
                'message': 'Peer support match accepted'
            })
        else:
            return jsonify({'error': 'Match not found or unauthorized'}), 404
            
    except Exception as e:
        logger.error(f"Error accepting peer match: {e}")
        return jsonify({'error': 'Failed to accept peer match'}), 500

@community_api.route('/challenges', methods=['GET'])
@require_auth
def get_wellness_challenges():
    """Get available wellness challenges"""
    try:
        challenge_type = request.args.get('type')
        category = request.args.get('category')
        community_id = request.args.get('community_id')
        active_only = request.args.get('active_only', default='true').lower() == 'true'
        limit = request.args.get('limit', default=20, type=int)
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        # Build query
        query = "SELECT * FROM wellness_challenges WHERE 1=1"
        params = []
        
        if challenge_type:
            query += " AND challenge_type = ?"
            params.append(challenge_type)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if community_id:
            query += " AND community_id = ?"
            params.append(community_id)
        
        if active_only:
            query += " AND start_date <= ? AND end_date >= ?"
            now = datetime.now()
            params.extend([now, now])
        
        query += " ORDER BY start_date DESC LIMIT ?"
        params.append(limit)
        
        results = community_manager.db.fetch_all(query, tuple(params))
        
        challenges = []
        for row in results:
            challenge_data = {
                'challenge_id': row[0],
                'title': row[1],
                'description': row[2],
                'challenge_type': row[3],
                'category': row[4],
                'duration_days': row[5],
                'difficulty_level': row[6],
                'participant_count': row[7],
                'max_participants': row[8],
                'start_date': row[9],
                'end_date': row[10],
                'creator_id': row[11],
                'reward_points': row[12],
                'is_community_challenge': bool(row[13]),
                'community_id': row[14]
            }
            challenges.append(challenge_data)
        
        return jsonify({
            'success': True,
            'challenges': challenges,
            'total': len(challenges)
        })
        
    except Exception as e:
        logger.error(f"Error getting wellness challenges: {e}")
        return jsonify({'error': 'Failed to get wellness challenges'}), 500

@community_api.route('/challenges', methods=['POST'])
@require_auth
def create_wellness_challenge():
    """Create a new wellness challenge"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        title = data.get('title')
        description = data.get('description')
        challenge_type = data.get('challenge_type')
        category = data.get('category')
        duration_days = data.get('duration_days', 7)
        difficulty_level = data.get('difficulty_level', 'beginner')
        community_id = data.get('community_id')
        
        if not title or not description or not challenge_type or not category:
            return jsonify({'error': 'Title, description, challenge_type, and category are required'}), 400
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        challenge_id = community_manager.create_wellness_challenge(
            creator_id=user_id,
            title=title,
            description=description,
            challenge_type=challenge_type,
            category=category,
            duration_days=duration_days,
            difficulty_level=difficulty_level,
            community_id=community_id
        )
        
        if challenge_id:
            return jsonify({
                'success': True,
                'challenge_id': challenge_id,
                'message': 'Wellness challenge created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create wellness challenge'}), 500
            
    except Exception as e:
        logger.error(f"Error creating wellness challenge: {e}")
        return jsonify({'error': 'Failed to create wellness challenge'}), 500

@community_api.route('/challenges/<challenge_id>/join', methods=['POST'])
@require_auth
def join_wellness_challenge(challenge_id):
    """Join a wellness challenge"""
    try:
        user_id = session.get('user_id')
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        # Check if user is already participating
        existing_query = """
            SELECT participation_id FROM challenge_participation 
            WHERE challenge_id = ? AND user_id = ?
        """
        existing = community_manager.db.fetch_one(existing_query, (challenge_id, user_id))
        
        if existing:
            return jsonify({'error': 'Already participating in this challenge'}), 400
        
        # Create participation record
        participation_id = str(__import__('uuid').uuid4())
        query = """
            INSERT INTO challenge_participation
            (participation_id, challenge_id, user_id, joined_at, progress, 
             current_streak, best_streak, completed, points_earned)
            VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0)
        """
        
        result = community_manager.db.execute_query(query, 
                                                  (participation_id, challenge_id, user_id, datetime.now()))
        
        if result:
            # Update challenge participant count
            community_manager.db.execute_query(
                "UPDATE wellness_challenges SET participant_count = participant_count + 1 WHERE challenge_id = ?",
                (challenge_id,)
            )
            
            return jsonify({
                'success': True,
                'participation_id': participation_id,
                'message': 'Successfully joined wellness challenge'
            })
        else:
            return jsonify({'error': 'Failed to join wellness challenge'}), 500
            
    except Exception as e:
        logger.error(f"Error joining wellness challenge: {e}")
        return jsonify({'error': 'Failed to join wellness challenge'}), 500

@community_api.route('/my-communities', methods=['GET'])
@require_auth
def get_user_communities():
    """Get communities the user is a member of"""
    try:
        user_id = session.get('user_id')
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        query = """
            SELECT wc.*, cm.role, cm.joined_at, cm.contribution_score
            FROM wellness_communities wc
            JOIN community_memberships cm ON wc.community_id = cm.community_id
            WHERE cm.user_id = ? AND cm.is_active = 1
            ORDER BY cm.joined_at DESC
        """
        
        results = community_manager.db.fetch_all(query, (user_id,))
        
        communities = []
        for row in results:
            community_data = {
                'community_id': row[0],
                'name': row[1],
                'description': row[2],
                'community_type': row[3],
                'visibility': row[4],
                'member_count': row[6],
                'tags': json.loads(row[9]) if row[9] else [],
                'my_role': row[16],  # role from join
                'joined_at': row[17],
                'contribution_score': row[18]
            }
            communities.append(community_data)
        
        return jsonify({
            'success': True,
            'communities': communities,
            'total': len(communities)
        })
        
    except Exception as e:
        logger.error(f"Error getting user communities: {e}")
        return jsonify({'error': 'Failed to get user communities'}), 500

@community_api.route('/my-challenges', methods=['GET'])
@require_auth
def get_user_challenges():
    """Get challenges the user is participating in"""
    try:
        user_id = session.get('user_id')
        active_only = request.args.get('active_only', default='true').lower() == 'true'
        
        community_manager = get_community_manager()
        if not community_manager:
            return jsonify({'error': 'Community service unavailable'}), 503
        
        query = """
            SELECT wc.*, cp.progress, cp.current_streak, cp.best_streak, 
                   cp.completed, cp.completed_at, cp.points_earned, cp.joined_at
            FROM wellness_challenges wc
            JOIN challenge_participation cp ON wc.challenge_id = cp.challenge_id
            WHERE cp.user_id = ?
        """
        
        params = [user_id]
        
        if active_only:
            query += " AND wc.end_date >= ? AND cp.completed = 0"
            params.append(datetime.now())
        
        query += " ORDER BY cp.joined_at DESC"
        
        results = community_manager.db.fetch_all(query, tuple(params))
        
        challenges = []
        for row in results:
            challenge_data = {
                'challenge_id': row[0],
                'title': row[1],
                'description': row[2],
                'challenge_type': row[3],
                'category': row[4],
                'duration_days': row[5],
                'difficulty_level': row[6],
                'start_date': row[9],
                'end_date': row[10],
                'reward_points': row[12],
                'my_progress': row[15],
                'current_streak': row[16],
                'best_streak': row[17],
                'completed': bool(row[18]),
                'completed_at': row[19],
                'points_earned': row[20],
                'joined_at': row[21]
            }
            challenges.append(challenge_data)
        
        return jsonify({
            'success': True,
            'challenges': challenges,
            'total': len(challenges)
        })
        
    except Exception as e:
        logger.error(f"Error getting user challenges: {e}")
        return jsonify({'error': 'Failed to get user challenges'}), 500

# Health check endpoint
@community_api.route('/health', methods=['GET'])
def health_check():
    """Health check for community API"""
    try:
        community_manager = get_community_manager()
        service_status = 'available' if community_manager else 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'service': service_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"Community health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def init_community_api():
    """Initialize community API"""
    logger.info("Community API initialized")
    return community_api