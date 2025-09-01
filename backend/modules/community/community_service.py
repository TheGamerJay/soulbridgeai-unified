"""
SoulBridge AI - Community Service
Manages community features, avatar selection, and user interactions
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class CommunityService:
    """Service for managing community features and interactions"""
    
    def __init__(self, database=None, companion_manager=None):
        self.database = database
        self.companion_manager = companion_manager
        self.community_themes = [
            'wellness', 'gratitude', 'growth', 'creativity', 'support', 
            'inspiration', 'meditation', 'healing', 'relationships', 'mindfulness'
        ]
        self.content_types = [
            'creative_writing', 'poetry', 'artwork', 'reflection', 
            'affirmation', 'story', 'journal_entry', 'meditation'
        ]
    
    def get_user_avatar(self, user_id: int) -> Dict[str, Any]:
        """Get user's current community avatar/companion"""
        try:
            from flask import session
            
            # Get companion info from session first
            companion_info = session.get('companion_info')
            logger.info(f"👤 Session companion_info: {companion_info}")
            
            if companion_info and 'id' in companion_info:
                logger.info(f"👤 Using session companion: {companion_info['id']}")
                # Return companion info from session
                return {
                    'success': True,
                    'companion': {
                        'name': companion_info.get('name', 'Soul'),
                        'companion_id': companion_info.get('id', 'soul'),
                        'avatar_url': companion_info.get('image_url', '/static/logos/New IntroLogo.png'),
                        'image_url': companion_info.get('image_url', '/static/logos/New IntroLogo.png'),
                        'tier': companion_info.get('tier', 'bronze')
                    }
                }
            
            # Try to get from database if available
            if self.database:
                try:
                    conn = self.database.get_connection()
                    cursor = conn.cursor()
                    
                    # Check if user has companion data stored
                    if self.database.use_postgres:
                        cursor.execute("SELECT companion_data FROM users WHERE id = %s", (user_id,))
                    else:
                        cursor.execute("SELECT companion_data FROM users WHERE id = ?", (user_id,))
                    
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result and result[0]:
                        import json
                        logger.info(f"👤 Found database companion_data: {result[0]}")
                        try:
                            companion_info = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                            logger.info(f"👤 Parsed companion_info: {companion_info}")
                            if companion_info and isinstance(companion_info, dict) and 'id' in companion_info:
                                # Get fresh companion data from companion manager for up-to-date info
                                if self.companion_manager:
                                    companion_data = self.companion_manager.get_companion_by_id(companion_info['id'])
                                    if companion_data:
                                        logger.info(f"👤 Using database companion: {companion_info['id']}")
                                        return {
                                            'success': True,
                                            'companion': {
                                                'name': companion_info.get('name', companion_data.get('name', 'Soul')),
                                                'companion_id': companion_info['id'],
                                                'avatar_url': companion_data.get('image_url', '/static/logos/New IntroLogo.png'),
                                                'image_url': companion_data.get('image_url', '/static/logos/New IntroLogo.png'),
                                                'tier': companion_data.get('tier', 'bronze')
                                            }
                                        }
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Failed to parse companion_data from database: {e}")
                    else:
                        logger.info("👤 No companion_data found in database")
                        
                except Exception as db_error:
                    logger.warning(f"Database lookup failed for avatar: {db_error}")
            
            # Default companion if none set
            default_companion = {
                'name': 'Soul',
                'companion_id': 'soul',
                'avatar_url': '/static/logos/New IntroLogo.png',
                'image_url': '/static/logos/New IntroLogo.png',
                'tier': 'bronze'
            }
            
            return {
                'success': True,
                'companion': default_companion
            }
            
        except Exception as e:
            logger.error(f"Failed to get user avatar: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_user_avatar(self, user_id: int, companion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set user's community avatar/companion"""
        try:
            # Validate required fields
            required_fields = ['companion_id', 'name', 'avatar_url']
            for field in required_fields:
                if field not in companion_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            companion_id = companion_data['companion_id']
            
            # Validate companion access if companion manager available
            if self.companion_manager:
                from flask import session
                # Get user's plan and trial status from session
                user_plan = session.get('user_plan', 'bronze')
                trial_active = session.get('trial_active', False)
                referrals = session.get('referrals', 0)
                
                if not self.companion_manager.can_user_access_companion(
                    user_plan, trial_active, referrals, companion_id
                ):
                    return {
                        'success': False,
                        'error': 'You do not have access to this companion'
                    }
            
            # Save avatar selection to session
            from flask import session
            
            companion_info = {
                'id': companion_id,
                'name': companion_data['name'], 
                'image_url': companion_data['avatar_url'],
                'tier': companion_data.get('tier', 'bronze')
            }
            
            session['companion_info'] = companion_info
            session.modified = True
            logger.info(f"👤 Saved companion to session: {companion_info}")
            
            # Also save to database if available
            if self.database:
                try:
                    conn = self.database.get_connection()
                    cursor = conn.cursor()
                    
                    # Save companion info as JSON in companion_data column
                    import json
                    companion_json = json.dumps(companion_info)
                    
                    if self.database.use_postgres:
                        cursor.execute("""
                            UPDATE users 
                            SET companion_data = %s 
                            WHERE id = %s
                        """, (companion_json, user_id))
                    else:
                        cursor.execute("""
                            UPDATE users 
                            SET companion_data = ? 
                            WHERE id = ?
                        """, (companion_json, user_id))
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"👤 Saved avatar to database for user {user_id}")
                    
                except Exception as db_error:
                    logger.warning(f"Failed to save avatar to database: {db_error}")
            
            avatar_data = {
                'user_id': user_id,
                'companion_id': companion_id,
                'name': companion_data['name'],
                'avatar_url': companion_data['avatar_url'],
                'selected_at': datetime.now().isoformat()
            }
            
            logger.info(f"👤 Set community avatar for user {user_id}: {companion_id}")
            
            return {
                'success': True,
                'message': 'Avatar updated successfully',
                'companion': avatar_data
            }
            
        except Exception as e:
            logger.error(f"Failed to set user avatar: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def can_change_avatar(self, user_id: int) -> Dict[str, Any]:
        """Check if user can change avatar (no cooldown for community)"""
        try:
            # No cooldown restrictions for community avatar changes
            # This allows users to freely express themselves
            
            return {
                'success': True,
                'can_change': True,
                'cooldown_remaining': 0,
                'next_change_available': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check avatar cooldown: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_community_stats(self, user_id: int = None) -> Dict[str, Any]:
        """Get community statistics"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'stats': {
                        'total_content': 0,
                        'active_users': 0,
                        'content_by_theme': {},
                        'content_by_type': {},
                        'recent_activity': 0
                    }
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get total approved content
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = TRUE")
            else:
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = 1")
            
            total_content = cursor.fetchone()[0] or 0
            
            # Get content by theme
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT theme, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    GROUP BY theme
                """)
            else:
                cursor.execute("""
                    SELECT theme, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    GROUP BY theme
                """)
            
            theme_counts = dict(cursor.fetchall())
            
            # Get content by type
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT content_type, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    GROUP BY content_type
                """)
            else:
                cursor.execute("""
                    SELECT content_type, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    GROUP BY content_type
                """)
            
            type_counts = dict(cursor.fetchall())
            
            # Get recent activity (last 7 days)
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    AND created_at >= NOW() - INTERVAL '7 days'
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    AND created_at >= date('now', '-7 days')
                """)
            
            recent_activity = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats = {
                'total_content': total_content,
                'active_users': 0,  # TODO: Calculate unique contributors
                'content_by_theme': theme_counts,
                'content_by_type': type_counts,
                'recent_activity': recent_activity,
                'themes_available': self.community_themes,
                'content_types_available': self.content_types
            }
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get community stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_community_activity(self, user_id: int) -> Dict[str, Any]:
        """Get user's community activity summary"""
        try:
            # Since content is shared anonymously, we can't track individual contributions
            # But we can provide general participation stats
            
            activity = {
                'participates_in_community': True,  # If they're calling this API
                'avatar_set': True,  # TODO: Check if avatar is set
                'community_access_level': 'basic',  # Based on their tier
                'available_features': [
                    'anonymous_sharing',
                    'content_viewing', 
                    'heart_reactions',
                    'avatar_customization'
                ],
                'last_activity': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'activity': activity
            }
            
        except Exception as e:
            logger.error(f"Failed to get user community activity: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_community_access(self, user_plan: str, trial_active: bool) -> Dict[str, Any]:
        """Validate user's access to community features"""
        try:
            # Community access rules
            access = {
                'can_view_content': True,  # All users can view
                'can_share_content': False,  # Silver/Gold or trial required
                'can_use_avatars': True,  # All users can select avatars
                'can_heart_content': True,  # All users can heart content
                'access_level': 'basic'
            }
            
            # Determine effective plan for sharing
            if user_plan in ['silver', 'gold'] or trial_active:
                access['can_share_content'] = True
                access['access_level'] = 'premium'
            
            access['restrictions'] = []
            if not access['can_share_content']:
                access['restrictions'].append(
                    'Content sharing requires Silver/Gold tier or trial access'
                )
            
            return {
                'success': True,
                'access': access
            }
            
        except Exception as e:
            logger.error(f"Failed to validate community access: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_community_themes(self) -> List[str]:
        """Get available community themes"""
        return self.community_themes
    
    def get_content_types(self) -> List[str]:
        """Get available content types"""
        return self.content_types
    
    def format_community_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """Format community content for display"""
        try:
            formatted = {
                'id': content_item.get('id'),
                'content_type': content_item.get('content_type', 'creative_writing'),
                'content': content_item.get('content', ''),
                'theme': content_item.get('theme', 'wellness'),
                'mood': content_item.get('mood', ''),
                'hearts_count': content_item.get('hearts_count', 0),
                'created_at': content_item.get('created_at'),
                'metadata': {}
            }
            
            # Parse metadata if it exists
            metadata_str = content_item.get('metadata', '{}')
            if metadata_str:
                try:
                    formatted['metadata'] = json.loads(metadata_str)
                except:
                    formatted['metadata'] = {}
            
            # Add display formatting
            formatted['display'] = {
                'theme_label': formatted['theme'].replace('_', ' ').title(),
                'content_type_label': formatted['content_type'].replace('_', ' ').title(),
                'hearts_display': self._format_hearts_count(formatted['hearts_count']),
                'time_ago': self._format_time_ago(formatted['created_at'])
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format community content: {e}")
            return content_item
    
    def _format_hearts_count(self, count: int) -> str:
        """Format hearts count for display"""
        if count == 0:
            return "No hearts yet"
        elif count == 1:
            return "1 heart"
        elif count < 1000:
            return f"{count} hearts"
        else:
            return f"{count//1000}k hearts"
    
    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as time ago"""
        try:
            if not timestamp:
                return "Recently"
            
            # Parse timestamp
            if isinstance(timestamp, str):
                created_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                created_time = timestamp
            
            # Calculate time difference
            now = datetime.now()
            if created_time.tzinfo:
                created_time = created_time.replace(tzinfo=None)
            
            diff = now - created_time
            
            if diff.days > 30:
                return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
            elif diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
                
        except Exception as e:
            logger.error(f"Failed to format time ago: {e}")
            return "Recently"