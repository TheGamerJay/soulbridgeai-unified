"""
SoulBridge AI - Meditation Service
Core meditation system with session management and credit integration
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

class MeditationService:
    """Service for managing meditation sessions and user progress"""
    
    def __init__(self, database=None, session_tracker=None, meditation_generator=None):
        self.database = database
        self.session_tracker = session_tracker
        self.meditation_generator = meditation_generator
        
        # Meditation categories and types
        self.meditation_categories = {
            'stress': {
                'name': 'Stress Relief',
                'description': 'Meditations to help reduce stress and tension',
                'sessions': [
                    'stress-breathing-basic',
                    'stress-body-scan',
                    'stress-mindful-release',
                    'stress-peaceful-mind'
                ]
            },
            'anxiety': {
                'name': 'Anxiety Support',
                'description': 'Calming meditations for anxious thoughts',
                'sessions': [
                    'anxiety-grounding-54321',
                    'anxiety-safe-space',
                    'anxiety-breath-anchor',
                    'anxiety-worry-release'
                ]
            },
            'sleep': {
                'name': 'Sleep & Rest',
                'description': 'Meditations to prepare for restful sleep',
                'sessions': [
                    'sleep-body-relaxation',
                    'sleep-counting-meditation',
                    'sleep-peaceful-imagery',
                    'sleep-gratitude-rest'
                ]
            },
            'healing': {
                'name': 'Emotional Healing',
                'description': 'Meditations for processing and healing emotions',
                'sessions': [
                    'healing-inner-child',
                    'healing-forgiveness',
                    'healing-self-compassion',
                    'healing-heart-opening'
                ]
            },
            'confidence': {
                'name': 'Self-Confidence',
                'description': 'Meditations to build self-worth and confidence',
                'sessions': [
                    'confidence-affirmations',
                    'confidence-inner-strength',
                    'confidence-self-love',
                    'confidence-empowerment'
                ]
            },
            'breathing': {
                'name': 'Breathing Exercises',
                'description': 'Focus-based breathing techniques',
                'sessions': [
                    'breathing-box-breathing',
                    'breathing-4-7-8',
                    'breathing-alternate-nostril',
                    'breathing-belly-breath'
                ]
            }
        }
        
        # Default session durations (in seconds)
        self.session_durations = {
            'short': 300,    # 5 minutes
            'medium': 600,   # 10 minutes
            'long': 1200,    # 20 minutes
            'extended': 1800 # 30 minutes
        }
        
    def check_meditation_access(self, user_plan: str, trial_active: bool, user_addons: List[str] = None) -> Dict[str, Any]:
        """Check if user has access to emotional meditations"""
        try:
            user_addons = user_addons or []
            
            # Check access: Silver/Gold tier, trial, or specific addon
            has_access = (
                user_plan in ['silver', 'gold'] or
                trial_active or
                'emotional-meditations' in user_addons
            )
            
            access_reason = None
            if not has_access:
                if user_plan == 'bronze':
                    access_reason = 'Emotional Meditations requires Silver/Gold tier subscription'
                else:
                    access_reason = 'Access validation failed'
            
            return {
                'has_access': has_access,
                'reason': access_reason,
                'access_via': 'subscription' if user_plan in ['silver', 'gold'] else 
                              'trial' if trial_active else
                              'addon' if 'emotional-meditations' in user_addons else
                              'none'
            }
            
        except Exception as e:
            logger.error(f"Error checking meditation access: {e}")
            return {
                'has_access': False,
                'reason': 'Access check failed',
                'access_via': 'none'
            }
    
    def get_available_meditations(self, user_plan: str = 'bronze') -> Dict[str, Any]:
        """Get available meditation categories and sessions"""
        try:
            # All meditation categories are available to users with access
            # (access is checked separately)
            
            available_meditations = {}
            
            for category_id, category_data in self.meditation_categories.items():
                available_meditations[category_id] = {
                    'id': category_id,
                    'name': category_data['name'],
                    'description': category_data['description'],
                    'sessions': []
                }
                
                # Add session details
                for session_id in category_data['sessions']:
                    session_details = self._get_session_details(session_id)
                    available_meditations[category_id]['sessions'].append(session_details)
            
            return {
                'success': True,
                'categories': available_meditations,
                'total_categories': len(available_meditations),
                'total_sessions': sum(len(cat['sessions']) for cat in available_meditations.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting available meditations: {e}")
            return {
                'success': False,
                'error': 'Failed to load meditations'
            }
    
    def start_meditation_session(self, user_id: int, meditation_id: str, 
                                  duration: str = 'medium') -> Dict[str, Any]:
        """Start a new meditation session"""
        try:
            # Validate meditation ID
            if not self._validate_meditation_id(meditation_id):
                return {
                    'success': False,
                    'error': 'Invalid meditation ID'
                }
            
            # Get session duration
            session_duration = self.session_durations.get(duration, self.session_durations['medium'])
            
            # Create session data
            session_data = {
                'session_id': f"med_{user_id}_{int(datetime.now().timestamp())}",
                'user_id': user_id,
                'meditation_id': meditation_id,
                'title': self._get_meditation_title(meditation_id),
                'category': self._get_meditation_category(meditation_id),
                'duration': session_duration,
                'duration_label': duration,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'status': 'started',
                'completed': False
            }
            
            logger.info(f"🧘 Started meditation session for user {user_id}: {meditation_id}")
            
            return {
                'success': True,
                'session': session_data,
                'message': 'Meditation session started'
            }
            
        except Exception as e:
            logger.error(f"Error starting meditation session: {e}")
            return {
                'success': False,
                'error': 'Failed to start meditation session'
            }
    
    def complete_meditation_session(self, user_id: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a meditation session and save to database"""
        try:
            # Validate session data
            required_fields = ['meditationId', 'title', 'duration', 'timestamp']
            for field in required_fields:
                if field not in session_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Create session record
            session_record = {
                'id': self._generate_session_id(user_id),
                'user_id': user_id,
                'meditation_id': session_data['meditationId'],
                'title': session_data['title'],
                'category': self._get_meditation_category(session_data['meditationId']),
                'duration_seconds': int(session_data['duration']),
                'duration_minutes': int(session_data['duration']) // 60,
                'completed': bool(session_data.get('completed', True)),
                'started_at': session_data['timestamp'],
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'satisfaction_rating': session_data.get('rating'),
                'notes': session_data.get('notes', ''),
                'metadata': {
                    'meditation_type': self._get_meditation_category(session_data['meditationId']),
                    'session_quality': session_data.get('quality', 'completed'),
                    'user_feedback': session_data.get('feedback')
                }
            }
            
            # Save to database if available
            if self.database and self.session_tracker:
                save_result = self.session_tracker.save_session(session_record)
                if not save_result['success']:
                    logger.warning(f"Failed to save meditation session to database: {save_result.get('error')}")
            
            logger.info(f"🧘✅ Completed meditation session for user {user_id}: {session_data['title']}")
            
            return {
                'success': True,
                'session': session_record,
                'message': 'Meditation session completed and saved'
            }
            
        except Exception as e:
            logger.error(f"Error completing meditation session: {e}")
            return {
                'success': False,
                'error': 'Failed to complete meditation session'
            }
    
    def get_user_meditation_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's meditation statistics"""
        try:
            # Get session data from tracker or fallback to session storage
            stats_data = {
                'total_sessions': 0,
                'total_minutes': 0,
                'streak_days': 0,
                'favorite_type': 'Stress Relief',
                'categories_tried': 0,
                'longest_session_minutes': 0,
                'average_session_minutes': 0,
                'sessions_this_week': 0,
                'sessions_this_month': 0
            }
            
            if self.session_tracker:
                # Get from database
                db_stats = self.session_tracker.get_user_stats(user_id)
                if db_stats['success']:
                    stats_data.update(db_stats['stats'])
            
            # Add achievement data
            achievements = self._calculate_achievements(stats_data)
            
            return {
                'success': True,
                'stats': stats_data,
                'achievements': achievements,
                'next_goals': self._get_next_goals(stats_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting meditation stats for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to load meditation statistics'
            }
    
    def get_meditation_recommendations(self, user_id: int, context: str = '') -> Dict[str, Any]:
        """Get personalized meditation recommendations"""
        try:
            # Get user's meditation history if available
            user_stats = self.get_user_meditation_stats(user_id)
            
            recommendations = []
            
            # Base recommendations for new users
            if not user_stats['success'] or user_stats['stats']['total_sessions'] == 0:
                recommendations = [
                    {
                        'meditation_id': 'stress-breathing-basic',
                        'title': 'Basic Breathing for Stress Relief',
                        'category': 'Stress Relief',
                        'duration': 'short',
                        'reason': 'Perfect for beginners - simple and effective',
                        'difficulty': 'beginner'
                    },
                    {
                        'meditation_id': 'anxiety-grounding-54321',
                        'title': 'Grounding Technique (5-4-3-2-1)',
                        'category': 'Anxiety Support',
                        'duration': 'short',
                        'reason': 'Great for immediate anxiety relief',
                        'difficulty': 'beginner'
                    },
                    {
                        'meditation_id': 'sleep-body-relaxation',
                        'title': 'Progressive Muscle Relaxation',
                        'category': 'Sleep & Rest',
                        'duration': 'medium',
                        'reason': 'Helps prepare your body for rest',
                        'difficulty': 'beginner'
                    }
                ]
            else:
                # Personalized recommendations based on history
                recommendations = self._generate_personalized_recommendations(user_stats['stats'])
            
            return {
                'success': True,
                'recommendations': recommendations[:5],  # Limit to top 5
                'context': context,
                'personalized': user_stats['success'] and user_stats['stats']['total_sessions'] > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting meditation recommendations: {e}")
            return {
                'success': False,
                'error': 'Failed to generate recommendations'
            }
    
    def get_meditation_content(self, meditation_id: str, user_id: int = None) -> Dict[str, Any]:
        """Get meditation script/content for a specific meditation"""
        try:
            # Validate meditation ID
            if not self._validate_meditation_id(meditation_id):
                return {
                    'success': False,
                    'error': 'Invalid meditation ID'
                }
            
            # Get meditation details
            meditation_details = self._get_session_details(meditation_id)
            
            # Generate or retrieve meditation content
            if self.meditation_generator:
                content_result = self.meditation_generator.generate_meditation_script(
                    meditation_id, user_id
                )
                if content_result['success']:
                    meditation_details['script'] = content_result['script']
                    meditation_details['audio_cues'] = content_result.get('audio_cues', [])
            else:
                # Fallback to basic script
                meditation_details['script'] = self._get_basic_meditation_script(meditation_id)
            
            return {
                'success': True,
                'meditation': meditation_details
            }
            
        except Exception as e:
            logger.error(f"Error getting meditation content for {meditation_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to load meditation content'
            }
    
    # Helper methods
    
    def _validate_meditation_id(self, meditation_id: str) -> bool:
        """Validate if meditation ID exists"""
        for category_data in self.meditation_categories.values():
            if meditation_id in category_data['sessions']:
                return True
        return False
    
    def _get_meditation_category(self, meditation_id: str) -> str:
        """Get category for a meditation ID"""
        for category_id, category_data in self.meditation_categories.items():
            if meditation_id in category_data['sessions']:
                return category_data['name']
        return 'Unknown'
    
    def _get_meditation_title(self, meditation_id: str) -> str:
        """Get title for a meditation ID"""
        title_map = {
            # Stress Relief
            'stress-breathing-basic': 'Basic Breathing for Stress Relief',
            'stress-body-scan': 'Body Scan Meditation',
            'stress-mindful-release': 'Mindful Stress Release',
            'stress-peaceful-mind': 'Peaceful Mind Meditation',
            
            # Anxiety Support
            'anxiety-grounding-54321': 'Grounding Technique (5-4-3-2-1)',
            'anxiety-safe-space': 'Creating Your Safe Space',
            'anxiety-breath-anchor': 'Breath as Your Anchor',
            'anxiety-worry-release': 'Releasing Worried Thoughts',
            
            # Sleep & Rest
            'sleep-body-relaxation': 'Progressive Muscle Relaxation',
            'sleep-counting-meditation': 'Counting Meditation for Sleep',
            'sleep-peaceful-imagery': 'Peaceful Sleep Imagery',
            'sleep-gratitude-rest': 'Gratitude Before Rest',
            
            # Emotional Healing
            'healing-inner-child': 'Inner Child Healing',
            'healing-forgiveness': 'Forgiveness Meditation',
            'healing-self-compassion': 'Self-Compassion Practice',
            'healing-heart-opening': 'Heart Opening Meditation',
            
            # Self-Confidence
            'confidence-affirmations': 'Confidence Affirmations',
            'confidence-inner-strength': 'Connecting with Inner Strength',
            'confidence-self-love': 'Self-Love Meditation',
            'confidence-empowerment': 'Personal Empowerment',
            
            # Breathing Exercises
            'breathing-box-breathing': 'Box Breathing Exercise',
            'breathing-4-7-8': '4-7-8 Breathing Technique',
            'breathing-alternate-nostril': 'Alternate Nostril Breathing',
            'breathing-belly-breath': 'Deep Belly Breathing'
        }
        
        return title_map.get(meditation_id, meditation_id.replace('-', ' ').title())
    
    def _get_session_details(self, meditation_id: str) -> Dict[str, Any]:
        """Get detailed information for a meditation session"""
        return {
            'id': meditation_id,
            'title': self._get_meditation_title(meditation_id),
            'category': self._get_meditation_category(meditation_id),
            'description': f'A guided meditation for {self._get_meditation_category(meditation_id).lower()}',
            'durations': [
                {'id': 'short', 'label': '5 minutes', 'seconds': 300},
                {'id': 'medium', 'label': '10 minutes', 'seconds': 600},
                {'id': 'long', 'label': '20 minutes', 'seconds': 1200}
            ],
            'difficulty': 'beginner' if meditation_id.endswith('-basic') else 'intermediate',
            'tags': self._get_meditation_tags(meditation_id),
            'benefits': self._get_meditation_benefits(meditation_id)
        }
    
    def _get_meditation_tags(self, meditation_id: str) -> List[str]:
        """Get tags for a meditation"""
        tag_map = {
            'stress': ['stress relief', 'relaxation', 'calming'],
            'anxiety': ['anxiety', 'grounding', 'peace'],
            'sleep': ['sleep', 'rest', 'bedtime'],
            'healing': ['healing', 'emotional', 'self-care'],
            'confidence': ['confidence', 'self-esteem', 'empowerment'],
            'breathing': ['breathing', 'mindfulness', 'focus']
        }
        
        for category, tags in tag_map.items():
            if meditation_id.startswith(category):
                return tags
        
        return ['mindfulness', 'meditation']
    
    def _get_meditation_benefits(self, meditation_id: str) -> List[str]:
        """Get benefits for a meditation"""
        benefit_map = {
            'stress': ['Reduces stress hormones', 'Promotes relaxation', 'Improves mood'],
            'anxiety': ['Calms nervous system', 'Grounds anxious thoughts', 'Builds resilience'],
            'sleep': ['Improves sleep quality', 'Relaxes the body', 'Quiets the mind'],
            'healing': ['Processes emotions', 'Builds self-compassion', 'Promotes healing'],
            'confidence': ['Builds self-worth', 'Increases confidence', 'Empowers personal growth'],
            'breathing': ['Improves focus', 'Regulates nervous system', 'Enhances mindfulness']
        }
        
        for category, benefits in benefit_map.items():
            if meditation_id.startswith(category):
                return benefits
        
        return ['Promotes mindfulness', 'Reduces stress', 'Improves well-being']
    
    def _get_basic_meditation_script(self, meditation_id: str) -> Dict[str, Any]:
        """Get basic meditation script for fallback"""
        return {
            'introduction': f'Welcome to your {self._get_meditation_title(meditation_id)} session.',
            'preparation': 'Find a comfortable position and close your eyes or soften your gaze.',
            'main_practice': 'Focus on your breath and allow yourself to relax deeply.',
            'conclusion': 'Take a moment to appreciate this time you\'ve given yourself.',
            'segments': [
                {'time': 0, 'instruction': 'Begin by settling into your comfortable position'},
                {'time': 60, 'instruction': 'Focus on your natural breath'},
                {'time': 180, 'instruction': 'Notice the sensations in your body'},
                {'time': 240, 'instruction': 'Prepare to return to your day with renewed peace'}
            ]
        }
    
    def _generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID"""
        timestamp = int(datetime.now().timestamp())
        return f"session_{user_id}_{timestamp}"
    
    def _calculate_achievements(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate user achievements based on stats"""
        achievements = []
        
        # Session count achievements
        if stats['total_sessions'] >= 1:
            achievements.append({
                'id': 'first_session',
                'title': 'First Steps',
                'description': 'Completed your first meditation',
                'icon': '🧘‍♀️',
                'earned': True
            })
        
        if stats['total_sessions'] >= 5:
            achievements.append({
                'id': 'dedicated_beginner',
                'title': 'Dedicated Beginner',
                'description': 'Completed 5 meditation sessions',
                'icon': '⭐',
                'earned': True
            })
        
        if stats['total_sessions'] >= 20:
            achievements.append({
                'id': 'mindful_practitioner',
                'title': 'Mindful Practitioner',
                'description': 'Completed 20 meditation sessions',
                'icon': '🌟',
                'earned': True
            })
        
        # Streak achievements
        if stats['streak_days'] >= 3:
            achievements.append({
                'id': 'consistent_practice',
                'title': 'Consistent Practice',
                'description': '3-day meditation streak',
                'icon': '🔥',
                'earned': True
            })
        
        if stats['streak_days'] >= 7:
            achievements.append({
                'id': 'weekly_warrior',
                'title': 'Weekly Warrior',
                'description': '7-day meditation streak',
                'icon': '💪',
                'earned': True
            })
        
        return achievements
    
    def _get_next_goals(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get user's next goals based on current stats"""
        goals = []
        
        if stats['total_sessions'] < 5:
            goals.append({
                'id': 'reach_5_sessions',
                'title': 'Complete 5 Sessions',
                'description': f"{5 - stats['total_sessions']} sessions to go",
                'progress': stats['total_sessions'] / 5 * 100
            })
        
        if stats['streak_days'] < 3:
            goals.append({
                'id': 'build_streak',
                'title': 'Build a 3-Day Streak',
                'description': 'Meditate for 3 consecutive days',
                'progress': stats['streak_days'] / 3 * 100
            })
        
        if stats['total_minutes'] < 60:
            goals.append({
                'id': 'meditate_1_hour',
                'title': 'Meditate for 1 Hour Total',
                'description': f"{60 - stats['total_minutes']} minutes to go",
                'progress': stats['total_minutes'] / 60 * 100
            })
        
        return goals
    
    def _generate_personalized_recommendations(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on user's meditation history"""
        recommendations = []
        
        favorite_type = stats.get('favorite_type', 'Stress Relief')
        
        # Recommend similar meditations in favorite category
        if favorite_type == 'Stress Relief':
            recommendations.extend([
                {
                    'meditation_id': 'stress-body-scan',
                    'title': 'Body Scan Meditation',
                    'category': 'Stress Relief',
                    'duration': 'medium',
                    'reason': 'Great for deepening your stress relief practice',
                    'difficulty': 'intermediate'
                }
            ])
        
        # Recommend variety if user has limited category experience
        if stats.get('categories_tried', 0) < 3:
            recommendations.append({
                'meditation_id': 'confidence-affirmations',
                'title': 'Confidence Affirmations',
                'category': 'Self-Confidence',
                'duration': 'short',
                'reason': 'Try something new to build self-confidence',
                'difficulty': 'beginner'
            })
        
        # Recommend longer sessions if user is experienced
        if stats.get('total_sessions', 0) > 10:
            recommendations.append({
                'meditation_id': 'healing-self-compassion',
                'title': 'Self-Compassion Practice',
                'category': 'Emotional Healing',
                'duration': 'long',
                'reason': 'Ready for deeper, longer practices',
                'difficulty': 'intermediate'
            })
        
        return recommendations[:5]