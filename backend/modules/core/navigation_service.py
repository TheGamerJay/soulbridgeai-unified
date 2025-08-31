"""
SoulBridge AI - Navigation Service
Core navigation logic and route handling
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any, Optional, List
from flask import session, request

logger = logging.getLogger(__name__)

class NavigationService:
    """Handles application navigation and routing logic"""
    
    def __init__(self):
        self.protected_routes = {
            '/intro', '/chat', '/analytics', '/voice-chat', '/voice-journaling',
            '/ai-images', '/creative-writer', '/decoder', '/fortune', '/horoscope',
            '/meditations', '/relationships', '/mini-studio', '/library', '/profile'
        }
        
        self.tier_restricted_routes = {
            'silver': ['/analytics', '/voice-journaling', '/ai-images', '/meditations', '/relationships'],
            'gold': ['/voice-chat', '/mini-studio']
        }
    
    def determine_home_redirect(self) -> str:
        """Determine where to redirect user from home route - always login first"""
        try:
            # ALWAYS send users to login first when they type the URL directly
            # This ensures proper authentication flow and prevents any session confusion
            logger.info("🏠 HOME: Directing user to login page (standard flow)")
            return "/login"
            
        except Exception as e:
            logger.error(f"Error determining home redirect: {e}")
            return "/login"
    
    def check_route_access(self, route_path: str) -> Dict[str, Any]:
        """Check if user can access a specific route"""
        try:
            # Public routes (no authentication required)
            public_routes = {
                '/', '/login', '/register', '/auth/login', '/auth/register',
                '/terms-acceptance', '/privacy-policy', '/terms-of-service',
                '/health', '/api/user-status'
            }
            
            if route_path in public_routes or route_path.startswith('/static/'):
                return {"allowed": True, "reason": "public_route"}
            
            # Check authentication for protected routes
            if route_path in self.protected_routes:
                if not self._is_logged_in():
                    return {
                        "allowed": False, 
                        "reason": "authentication_required",
                        "redirect": f"/login?return_to={route_path.lstrip('/')}"
                    }
                
                # Check terms acceptance
                if not self._has_accepted_terms():
                    return {
                        "allowed": False,
                        "reason": "terms_required",
                        "redirect": "/terms-acceptance"
                    }
                
                # Check tier restrictions
                tier_check = self._check_tier_access(route_path)
                if not tier_check["allowed"]:
                    return tier_check
            
            return {"allowed": True, "reason": "access_granted"}
            
        except Exception as e:
            logger.error(f"Error checking route access: {e}")
            return {"allowed": False, "reason": "error", "error": str(e)}
    
    def _check_tier_access(self, route_path: str) -> Dict[str, Any]:
        """Check tier-based access to routes"""
        try:
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            # Check silver tier routes
            if route_path in self.tier_restricted_routes.get('silver', []):
                if not (effective_access.get('access_silver') or effective_access.get('access_gold')):
                    return {
                        "allowed": False,
                        "reason": "tier_restriction", 
                        "required_tier": "silver",
                        "current_tier": user_plan,
                        "redirect": "/subscription?feature=" + route_path.lstrip('/').replace('-', '_')
                    }
            
            # Check gold tier routes
            if route_path in self.tier_restricted_routes.get('gold', []):
                if not effective_access.get('access_gold'):
                    return {
                        "allowed": False,
                        "reason": "tier_restriction",
                        "required_tier": "gold", 
                        "current_tier": user_plan,
                        "redirect": "/subscription?feature=" + route_path.lstrip('/').replace('-', '_')
                    }
            
            return {"allowed": True, "reason": "tier_access_granted"}
            
        except Exception as e:
            logger.error(f"Error checking tier access: {e}")
            return {"allowed": False, "reason": "error", "error": str(e)}
    
    def _is_logged_in(self) -> bool:
        """Check if user is authenticated - strict validation"""
        try:
            # Check basic session data
            logged_in = session.get('logged_in', False)
            user_id = session.get('user_id')
            email = session.get('email')
            
            # Must have all required session data
            if not (logged_in and user_id and email):
                logger.debug(f"🔍 AUTH: Missing session data - logged_in={logged_in}, user_id={user_id}, email={email}")
                return False
            
            # Session looks valid
            logger.debug(f"🔍 AUTH: Valid session for user {user_id} ({email})")
            return True
            
        except Exception as e:
            logger.error(f"🔍 AUTH: Error checking authentication: {e}")
            return False
    
    def _has_accepted_terms(self) -> bool:
        """Check if user has accepted terms"""
        from ..auth.session_manager import has_accepted_terms
        return has_accepted_terms()
    
    def get_navigation_menu(self) -> Dict[str, Any]:
        """Get navigation menu items based on user's access"""
        try:
            if not self._is_logged_in():
                return {"items": [], "authenticated": False}
            
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            # Base menu items (available to all authenticated users)
            menu_items = [
                {"name": "Chat", "path": "/chat", "icon": "💬", "tier": "bronze"},
                {"name": "Decoder", "path": "/decoder", "icon": "🔮", "tier": "bronze"},
                {"name": "Fortune", "path": "/fortune", "icon": "🌟", "tier": "bronze"},
                {"name": "Horoscope", "path": "/horoscope", "icon": "🌙", "tier": "bronze"},
                {"name": "Creative Writer", "path": "/creative-writer", "icon": "✍️", "tier": "bronze"},
                {"name": "Library", "path": "/library", "icon": "📚", "tier": "bronze"}
            ]
            
            # Silver tier items
            if effective_access.get('access_silver') or effective_access.get('access_gold'):
                menu_items.extend([
                    {"name": "Analytics", "path": "/analytics", "icon": "📊", "tier": "silver"},
                    {"name": "Voice Journaling", "path": "/voice-journaling", "icon": "🎤", "tier": "silver"},
                    {"name": "AI Images", "path": "/ai-images", "icon": "🎨", "tier": "silver"},
                    {"name": "Meditations", "path": "/meditations", "icon": "🧘", "tier": "silver"},
                    {"name": "Relationships", "path": "/relationships", "icon": "💕", "tier": "silver"}
                ])
            
            # Gold tier items  
            if effective_access.get('access_gold'):
                menu_items.extend([
                    {"name": "Voice Chat", "path": "/voice-chat", "icon": "🗣️", "tier": "gold"},
                    {"name": "Mini Studio", "path": "/mini-studio", "icon": "🎵", "tier": "gold"}
                ])
            
            # Profile and account items (always available)
            menu_items.extend([
                {"name": "Profile", "path": "/profile", "icon": "👤", "tier": "bronze"},
                {"name": "Subscription", "path": "/subscription", "icon": "💎", "tier": "bronze"}
            ])
            
            return {
                "items": menu_items,
                "authenticated": True,
                "user_plan": user_plan,
                "trial_active": trial_active,
                "effective_access": effective_access
            }
            
        except Exception as e:
            logger.error(f"Error getting navigation menu: {e}")
            return {"items": [], "authenticated": False, "error": str(e)}
    
    def get_breadcrumbs(self, current_path: str) -> List[Dict[str, str]]:
        """Generate breadcrumbs for current path"""
        try:
            breadcrumb_map = {
                '/': [{"name": "Home", "path": "/"}],
                '/intro': [{"name": "Home", "path": "/"}, {"name": "Welcome", "path": "/intro"}],
                '/chat': [{"name": "Home", "path": "/"}, {"name": "Chat", "path": "/chat"}],
                '/analytics': [{"name": "Home", "path": "/"}, {"name": "Analytics", "path": "/analytics"}],
                '/profile': [{"name": "Home", "path": "/"}, {"name": "Profile", "path": "/profile"}],
                '/subscription': [{"name": "Home", "path": "/"}, {"name": "Subscription", "path": "/subscription"}],
                '/library': [{"name": "Home", "path": "/"}, {"name": "Library", "path": "/library"}]
            }
            
            return breadcrumb_map.get(current_path, [{"name": "Home", "path": "/"}])
            
        except Exception as e:
            logger.error(f"Error getting breadcrumbs: {e}")
            return [{"name": "Home", "path": "/"}]
    
    def get_user_dashboard_data(self) -> Dict[str, Any]:
        """Get data for user dashboard/intro page"""
        try:
            if not self._is_logged_in():
                return {}
            
            user_id = session.get('user_id')
            user_plan = session.get('user_plan', 'bronze')
            trial_active = session.get('trial_active', False)
            
            # Get user's recent activity and recommendations
            dashboard_data = {
                "user_id": user_id,
                "user_plan": user_plan,
                "trial_active": trial_active,
                "quick_actions": self._get_quick_actions(),
                "recent_activity": self._get_recent_activity(user_id),
                "feature_highlights": self._get_feature_highlights(user_plan, trial_active)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def _get_quick_actions(self) -> List[Dict[str, str]]:
        """Get quick action items for dashboard"""
        return [
            {"name": "Start Chatting", "path": "/chat", "icon": "💬", "description": "Connect with AI companions"},
            {"name": "Get Reading", "path": "/decoder", "icon": "🔮", "description": "Spiritual insights and guidance"},
            {"name": "Create Art", "path": "/creative-writer", "icon": "✍️", "description": "Express your creativity"},
            {"name": "View Library", "path": "/library", "icon": "📚", "description": "Your saved content"}
        ]
    
    def _get_recent_activity(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's recent activity for dashboard"""
        try:
            from ..shared.database import get_database
            from datetime import timedelta
            
            db = get_database()
            if not db:
                return []
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get recent activity
            three_days_ago = datetime.now() - timedelta(days=3)
            
            if db.db_type == 'postgresql':
                cursor.execute("""
                    SELECT feature_type, created_at, metadata
                    FROM user_activity_log 
                    WHERE user_id = %s AND created_at >= %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (user_id, three_days_ago))
            else:
                cursor.execute("""
                    SELECT feature_type, created_at, COALESCE(metadata, '{}')
                    FROM user_activity_log 
                    WHERE user_id = ? AND created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (user_id, three_days_ago.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            activities = []
            for row in rows:
                feature_type, created_at, metadata = row
                activities.append({
                    "feature": feature_type,
                    "timestamp": str(created_at),
                    "description": self._get_activity_description(feature_type)
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_feature_highlights(self, user_plan: str, trial_active: bool) -> List[Dict[str, Any]]:
        """Get feature highlights based on user's tier"""
        try:
            highlights = []
            
            # Base features for all users
            highlights.extend([
                {"name": "AI Companions", "description": "Chat with spiritual guides", "available": True},
                {"name": "Spiritual Decoder", "description": "Get mystical insights", "available": True},
                {"name": "Fortune Readings", "description": "Discover your path", "available": True}
            ])
            
            # Get effective access
            from ..tiers.artistic_time import get_effective_access
            effective_access = get_effective_access(user_plan, trial_active, session.get('user_addons', []))
            
            # Silver/Gold features
            if effective_access.get('access_silver') or effective_access.get('access_gold'):
                highlights.extend([
                    {"name": "Analytics Dashboard", "description": "Track your spiritual journey", "available": True},
                    {"name": "AI Image Creation", "description": "Visualize your dreams", "available": True},
                    {"name": "Guided Meditations", "description": "Find inner peace", "available": True}
                ])
            else:
                highlights.extend([
                    {"name": "Analytics Dashboard", "description": "Track your journey (Silver+)", "available": False},
                    {"name": "AI Image Creation", "description": "Visualize dreams (Silver+)", "available": False},
                    {"name": "Guided Meditations", "description": "Inner peace (Silver+)", "available": False}
                ])
            
            # Gold exclusive features
            if effective_access.get('access_gold'):
                highlights.extend([
                    {"name": "Voice Chat", "description": "Speak with AI companions", "available": True},
                    {"name": "Mini Studio", "description": "Create music and content", "available": True}
                ])
            else:
                highlights.extend([
                    {"name": "Voice Chat", "description": "Speak with AI (Gold)", "available": False},
                    {"name": "Mini Studio", "description": "Music creation (Gold)", "available": False}
                ])
            
            return highlights
            
        except Exception as e:
            logger.error(f"Error getting feature highlights: {e}")
            return []
    
    def _get_activity_description(self, feature_type: str) -> str:
        """Get human-readable description for activity type"""
        descriptions = {
            'chat': 'Had a conversation with AI companion',
            'voice_chat': 'Voice chat session',
            'voice_journaling': 'Created voice journal entry',
            'ai_images': 'Generated AI artwork',
            'creative_writing': 'Used creative writer',
            'decoder': 'Got spiritual decoder reading',
            'fortune': 'Received fortune reading',
            'horoscope': 'Read personalized horoscope',
            'meditations': 'Completed meditation session',
            'relationships': 'Explored relationship insights',
            'mini_studio': 'Created content in Mini Studio',
            'library': 'Accessed saved content'
        }
        
        return descriptions.get(feature_type, f"Used {feature_type}")
    
    def _is_logged_in(self) -> bool:
        """Check if user is authenticated - strict validation"""
        try:
            # Check basic session data
            logged_in = session.get('logged_in', False)
            user_id = session.get('user_id')
            email = session.get('email')
            
            # Must have all required session data
            if not (logged_in and user_id and email):
                logger.debug(f"🔍 AUTH: Missing session data - logged_in={logged_in}, user_id={user_id}, email={email}")
                return False
            
            # Session looks valid
            logger.debug(f"🔍 AUTH: Valid session for user {user_id} ({email})")
            return True
            
        except Exception as e:
            logger.error(f"🔍 AUTH: Error checking authentication: {e}")
            return False
    
    def _has_accepted_terms(self) -> bool:
        """Check if user has accepted terms"""
        try:
            from ..auth.session_manager import has_accepted_terms
            return has_accepted_terms()
        except Exception as e:
            logger.error(f"Error checking terms acceptance: {e}")
            return False
    
    def get_return_url(self, default: str = "/intro") -> str:
        """Get return URL from request or session"""
        try:
            # Check URL parameter first
            return_to = request.args.get('return_to')
            if return_to:
                # Validate return URL for security
                if self._is_safe_redirect_url(return_to):
                    return "/" + return_to.lstrip('/')
            
            # Check session
            return_url = session.get('return_url')
            if return_url and self._is_safe_redirect_url(return_url):
                session.pop('return_url', None)  # Clear after use
                return return_url
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting return URL: {e}")
            return default
    
    def set_return_url(self, url: str) -> bool:
        """Set return URL in session"""
        try:
            if self._is_safe_redirect_url(url):
                session['return_url'] = url
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting return URL: {e}")
            return False
    
    def _is_safe_redirect_url(self, url: str) -> bool:
        """Validate redirect URL for security"""
        try:
            # Basic security checks
            if not url:
                return False
            
            # Must be relative URL (no external redirects)
            if url.startswith('http://') or url.startswith('https://'):
                return False
            
            # No protocol-relative URLs
            if url.startswith('//'):
                return False
            
            # No dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&']
            if any(char in url for char in dangerous_chars):
                return False
            
            # Must start with /
            if not url.startswith('/'):
                url = '/' + url
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating redirect URL: {e}")
            return False
    
    def get_page_metadata(self, route_path: str) -> Dict[str, str]:
        """Get metadata for page rendering"""
        page_metadata = {
            '/': {"title": "SoulBridge AI", "description": "Your spiritual AI companion"},
            '/intro': {"title": "Welcome - SoulBridge AI", "description": "Begin your spiritual journey"},
            '/chat': {"title": "Chat - SoulBridge AI", "description": "Connect with AI companions"},
            '/analytics': {"title": "Analytics - SoulBridge AI", "description": "Track your spiritual growth"},
            '/profile': {"title": "Profile - SoulBridge AI", "description": "Manage your account"},
            '/subscription': {"title": "Subscription - SoulBridge AI", "description": "Upgrade your experience"},
            '/library': {"title": "Library - SoulBridge AI", "description": "Your saved spiritual content"}
        }
        
        return page_metadata.get(route_path, {
            "title": "SoulBridge AI",
            "description": "Your spiritual AI companion"
        })