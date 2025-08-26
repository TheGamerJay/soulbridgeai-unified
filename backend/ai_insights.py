"""
AI-Powered Insights and Analytics Engine
Mood pattern analysis, personalized recommendations, and smart friend matching
"""
import logging
import json
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import uuid

logger = logging.getLogger(__name__)

@dataclass
class MoodPattern:
    user_id: str
    dominant_mood: str
    average_score: float
    mood_stability: float  # 0-1, higher = more stable
    common_times: List[str]  # Times when this mood is most common
    trends: Dict[str, float]  # weekly/monthly trends
    triggers: List[str]  # Common words/activities associated with mood

@dataclass
class MoodTrend:
    period: str  # daily, weekly, monthly
    trend_direction: str  # improving, declining, stable
    change_percentage: float
    peak_times: List[str]
    low_times: List[str]
    volatility: float

@dataclass
class PersonalityInsight:
    user_id: str
    personality_type: str  # emotional, analytical, social, introspective
    communication_style: str  # supportive, direct, empathetic, encouraging
    preferred_companions: List[str]
    activity_preferences: List[str]
    wellness_focus_areas: List[str]

@dataclass
class CompanionRecommendation:
    companion_name: str
    match_score: float  # 0-1
    reasons: List[str]
    best_times: List[str]
    interaction_style: str

@dataclass
class FriendMatch:
    user_id: str
    compatibility_score: float  # 0-1
    shared_interests: List[str]
    complementary_traits: List[str]
    interaction_potential: str  # high, medium, low
    recommended_activities: List[str]

@dataclass
class WellnessAlert:
    user_id: str
    alert_type: str  # mood_decline, isolation, stress_spike, positive_trend
    severity: str  # low, medium, high
    message: str
    recommendations: List[str]
    created_at: datetime

@dataclass
class UserInsights:
    user_id: str
    mood_patterns: List[MoodPattern]
    personality_insights: PersonalityInsight
    companion_recommendations: List[CompanionRecommendation]
    friend_matches: List[FriendMatch]
    wellness_alerts: List[WellnessAlert]
    last_updated: datetime

class AIInsightsEngine:
    def __init__(self, db_manager=None, social_manager=None):
        self.db = db_manager
        self.social_manager = social_manager
        
        # Companion personality profiles
        self.companion_profiles = {
            "Blayzo": {
                "personality": "calm_supportive",
                "best_for": ["anxiety", "stress", "overthinking"],
                "communication_style": "gentle_wisdom",
                "energy_level": "low_medium"
            },
            "Blayzica": {
                "personality": "energetic_positive",
                "best_for": ["depression", "loneliness", "motivation"],
                "communication_style": "enthusiastic_encouraging",
                "energy_level": "high"
            },
            "Crimson": {
                "personality": "protective_strong",
                "best_for": ["confidence", "goal_setting", "determination"],
                "communication_style": "direct_empowering",
                "energy_level": "high"
            },
            "Violet": {
                "personality": "mystical_introspective",
                "best_for": ["self_discovery", "spirituality", "creativity"],
                "communication_style": "intuitive_mysterious",
                "energy_level": "medium"
            },
            "Blayzion": {
                "personality": "intellectual_cosmic",
                "best_for": ["deep_thinking", "philosophy", "big_picture"],
                "communication_style": "profound_expansive",
                "energy_level": "medium"
            },
            "Blayzia": {
                "personality": "nurturing_healing",
                "best_for": ["emotional_healing", "self_love", "comfort"],
                "communication_style": "warm_compassionate",
                "energy_level": "low_medium"
            }
        }
        
        logger.info("AI Insights Engine initialized")
    
    def analyze_mood_patterns(self, user_id: str, days: int = 30) -> List[MoodPattern]:
        """Analyze user's mood patterns over specified period"""
        try:
            if not self.db:
                return []
            
            # Get mood data from the last N days
            start_date = datetime.now() - timedelta(days=days)
            
            # Query mood entries (adjust based on your mood tracking table structure)
            mood_query = """
            SELECT mood, score, created_at, notes 
            FROM mood_entries 
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at
            """
            
            mood_data = self.db.fetch_all(mood_query, (user_id, start_date))
            
            if not mood_data:
                return []
            
            # Group moods and analyze patterns
            mood_groups = defaultdict(list)
            mood_times = defaultdict(list)
            
            for mood, score, timestamp, notes in mood_data:
                mood_groups[mood].append({
                    'score': score,
                    'time': timestamp,
                    'notes': notes or ''
                })
                
                # Extract hour for time analysis
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp)
                    except:
                        dt = datetime.now()
                else:
                    dt = timestamp
                
                mood_times[mood].append(dt.hour)
            
            patterns = []
            
            for mood, entries in mood_groups.items():
                if len(entries) < 2:
                    continue
                
                scores = [entry['score'] for entry in entries]
                times = mood_times[mood]
                
                # Calculate statistics
                avg_score = statistics.mean(scores)
                stability = 1.0 - (statistics.stdev(scores) / max(scores)) if len(scores) > 1 else 1.0
                
                # Find common times
                time_counter = Counter(times)
                common_hours = [str(hour) for hour, _ in time_counter.most_common(3)]
                
                # Analyze trends (simplified)
                if len(entries) >= 7:
                    recent_scores = scores[-7:]
                    early_scores = scores[:7]
                    
                    recent_avg = statistics.mean(recent_scores)
                    early_avg = statistics.mean(early_scores)
                    
                    trend = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
                else:
                    trend = 0
                
                # Extract triggers from notes
                triggers = self._extract_triggers([entry['notes'] for entry in entries])
                
                pattern = MoodPattern(
                    user_id=user_id,
                    dominant_mood=mood,
                    average_score=avg_score,
                    mood_stability=max(0, min(1, stability)),
                    common_times=common_hours,
                    trends={'weekly': trend},
                    triggers=triggers[:5]  # Top 5 triggers
                )
                
                patterns.append(pattern)
            
            # Sort by frequency (most common moods first)
            patterns.sort(key=lambda p: len(mood_groups[p.dominant_mood]), reverse=True)
            
            return patterns[:10]  # Return top 10 patterns
            
        except Exception as e:
            logger.error(f"Error analyzing mood patterns: {e}")
            return []
    
    def analyze_personality(self, user_id: str) -> Optional[PersonalityInsight]:
        """Analyze user's personality based on their interactions and preferences"""
        try:
            if not self.db:
                return None
            
            # Get user's conversation history
            conversation_query = """
            SELECT content, created_at FROM messages 
            WHERE sender_id = ? 
            ORDER BY created_at DESC 
            LIMIT 100
            """
            
            messages = self.db.fetch_all(conversation_query, (user_id,))
            
            # Get mood entries
            mood_query = """
            SELECT mood, score, notes FROM mood_entries 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 50
            """
            
            moods = self.db.fetch_all(mood_query, (user_id,))
            
            # Analyze communication patterns
            communication_style = self._analyze_communication_style(messages)
            personality_type = self._determine_personality_type(messages, moods)
            
            # Get user preferences if available
            preferences = self._get_user_preferences(user_id)
            
            # Analyze companion usage
            preferred_companions = self._analyze_companion_usage(user_id)
            
            # Determine activity preferences
            activity_preferences = self._determine_activity_preferences(messages, moods)
            
            # Identify wellness focus areas
            wellness_areas = self._identify_wellness_focus(moods)
            
            return PersonalityInsight(
                user_id=user_id,
                personality_type=personality_type,
                communication_style=communication_style,
                preferred_companions=preferred_companions,
                activity_preferences=activity_preferences,
                wellness_focus_areas=wellness_areas
            )
            
        except Exception as e:
            logger.error(f"Error analyzing personality: {e}")
            return None
    
    def recommend_companions(self, user_id: str) -> List[CompanionRecommendation]:
        """Recommend AI companions based on user's needs and patterns"""
        try:
            # Get user's mood patterns and personality
            mood_patterns = self.analyze_mood_patterns(user_id)
            personality = self.analyze_personality(user_id)
            
            if not mood_patterns:
                # Default recommendations for new users
                return self._get_default_companion_recommendations()
            
            recommendations = []
            
            # Analyze current needs
            recent_moods = [p.dominant_mood for p in mood_patterns[:3]]
            avg_mood_score = statistics.mean([p.average_score for p in mood_patterns])
            
            for companion_name, profile in self.companion_profiles.items():
                match_score = self._calculate_companion_match(
                    recent_moods, avg_mood_score, profile, personality
                )
                
                reasons = self._generate_companion_reasons(
                    recent_moods, profile, personality
                )
                
                best_times = self._suggest_companion_times(mood_patterns, profile)
                
                recommendation = CompanionRecommendation(
                    companion_name=companion_name,
                    match_score=match_score,
                    reasons=reasons,
                    best_times=best_times,
                    interaction_style=profile['communication_style']
                )
                
                recommendations.append(recommendation)
            
            # Sort by match score
            recommendations.sort(key=lambda r: r.match_score, reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error recommending companions: {e}")
            return []
    
    def find_friend_matches(self, user_id: str) -> List[FriendMatch]:
        """Find compatible users for friend suggestions"""
        try:
            if not self.db or not self.social_manager:
                return []
            
            # Get user's personality and interests
            user_personality = self.analyze_personality(user_id)
            user_mood_patterns = self.analyze_mood_patterns(user_id)
            
            if not user_personality:
                return []
            
            # Get potential friends (users who aren't already friends)
            potential_friends_query = """
            SELECT DISTINCT user_id FROM user_profiles 
            WHERE user_id != ? 
            AND user_id NOT IN (
                SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END
                FROM friendships 
                WHERE user1_id = ? OR user2_id = ?
            )
            AND public_profile = 1
            LIMIT 50
            """
            
            potential_friends = self.db.fetch_all(potential_friends_query, 
                                                (user_id, user_id, user_id, user_id))
            
            matches = []
            
            for (friend_id,) in potential_friends:
                try:
                    friend_personality = self.analyze_personality(friend_id)
                    friend_mood_patterns = self.analyze_mood_patterns(friend_id)
                    
                    if not friend_personality:
                        continue
                    
                    compatibility = self._calculate_friend_compatibility(
                        user_personality, friend_personality,
                        user_mood_patterns, friend_mood_patterns
                    )
                    
                    if compatibility['score'] > 0.3:  # Minimum compatibility threshold
                        match = FriendMatch(
                            user_id=friend_id,
                            compatibility_score=compatibility['score'],
                            shared_interests=compatibility['shared_interests'],
                            complementary_traits=compatibility['complementary_traits'],
                            interaction_potential=compatibility['interaction_potential'],
                            recommended_activities=compatibility['activities']
                        )
                        matches.append(match)
                        
                except Exception as e:
                    logger.warning(f"Error analyzing friend {friend_id}: {e}")
                    continue
            
            # Sort by compatibility score
            matches.sort(key=lambda m: m.compatibility_score, reverse=True)
            
            return matches[:10]  # Return top 10 matches
            
        except Exception as e:
            logger.error(f"Error finding friend matches: {e}")
            return []
    
    def generate_wellness_alerts(self, user_id: str) -> List[WellnessAlert]:
        """Generate predictive wellness alerts based on patterns"""
        try:
            mood_patterns = self.analyze_mood_patterns(user_id, days=14)  # Last 2 weeks
            
            if not mood_patterns:
                return []
            
            alerts = []
            
            # Check for mood decline
            alerts.extend(self._check_mood_decline(user_id, mood_patterns))
            
            # Check for isolation patterns
            alerts.extend(self._check_isolation_patterns(user_id))
            
            # Check for stress spikes
            alerts.extend(self._check_stress_patterns(user_id, mood_patterns))
            
            # Check for positive trends (encouraging alerts)
            alerts.extend(self._check_positive_trends(user_id, mood_patterns))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating wellness alerts: {e}")
            return []
    
    def get_comprehensive_insights(self, user_id: str) -> Optional[UserInsights]:
        """Get comprehensive AI insights for a user"""
        try:
            mood_patterns = self.analyze_mood_patterns(user_id)
            personality = self.analyze_personality(user_id)
            companion_recommendations = self.recommend_companions(user_id)
            friend_matches = self.find_friend_matches(user_id)
            wellness_alerts = self.generate_wellness_alerts(user_id)
            
            if not personality:
                logger.warning(f"Could not generate personality insights for user {user_id}")
                return None
            
            insights = UserInsights(
                user_id=user_id,
                mood_patterns=mood_patterns,
                personality_insights=personality,
                companion_recommendations=companion_recommendations,
                friend_matches=friend_matches,
                wellness_alerts=wellness_alerts,
                last_updated=datetime.now()
            )
            
            # Cache insights for future use
            self._cache_insights(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting comprehensive insights: {e}")
            return None
    
    # Helper methods
    def _extract_triggers(self, notes_list: List[str]) -> List[str]:
        """Extract common triggers/themes from notes"""
        if not notes_list:
            return []
        
        # Simple keyword extraction (could be enhanced with NLP)
        common_triggers = [
            'work', 'stress', 'family', 'health', 'sleep', 'exercise',
            'social', 'money', 'relationship', 'weather', 'tired',
            'anxious', 'happy', 'sad', 'excited', 'overwhelmed'
        ]
        
        trigger_counts = Counter()
        
        for note in notes_list:
            if not note:
                continue
            
            note_lower = note.lower()
            for trigger in common_triggers:
                if trigger in note_lower:
                    trigger_counts[trigger] += 1
        
        return [trigger for trigger, _ in trigger_counts.most_common(5)]
    
    def _analyze_communication_style(self, messages: List[Tuple]) -> str:
        """Analyze user's communication style from messages"""
        if not messages:
            return "unknown"
        
        total_length = sum(len(msg[0]) for msg in messages if msg[0])
        avg_length = total_length / len(messages) if messages else 0
        
        # Simple heuristics
        if avg_length > 100:
            return "expressive"
        elif avg_length > 50:
            return "balanced"
        else:
            return "concise"
    
    def _determine_personality_type(self, messages: List[Tuple], moods: List[Tuple]) -> str:
        """Determine personality type based on data"""
        if not messages and not moods:
            return "unknown"
        
        # Simple personality detection based on mood variety and communication
        if moods:
            mood_variety = len(set(mood[0] for mood in moods))
            if mood_variety > 5:
                return "emotionally_expressive"
            elif mood_variety < 3:
                return "emotionally_stable"
        
        return "balanced"
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences from database"""
        try:
            if not self.db:
                return {}
            
            prefs_query = "SELECT preferences FROM user_preferences WHERE user_id = ?"
            result = self.db.fetch_one(prefs_query, (user_id,))
            
            if result and result[0]:
                return json.loads(result[0])
            
            return {}
            
        except Exception as e:
            logger.warning(f"Error getting user preferences: {e}")
            return {}
    
    def _analyze_companion_usage(self, user_id: str) -> List[str]:
        """Analyze which companions user interacts with most"""
        # This would analyze chat logs with different companions
        # For now, return default
        return ["Blayzo", "Blayzica"]
    
    def _determine_activity_preferences(self, messages: List[Tuple], moods: List[Tuple]) -> List[str]:
        """Determine user's activity preferences"""
        # Analyze messages and moods for activity mentions
        activities = ["journaling", "meditation", "socializing", "exercise"]
        return activities[:2]  # Return top 2
    
    def _identify_wellness_focus(self, moods: List[Tuple]) -> List[str]:
        """Identify areas where user needs wellness focus"""
        if not moods:
            return ["emotional_balance"]
        
        # Analyze mood patterns to identify focus areas
        low_mood_count = sum(1 for mood in moods if mood[1] < 0.4)
        
        focus_areas = []
        if low_mood_count > len(moods) * 0.3:
            focus_areas.append("mood_improvement")
        
        focus_areas.extend(["stress_management", "emotional_balance"])
        return focus_areas[:3]
    
    def _calculate_companion_match(self, recent_moods: List[str], avg_score: float, 
                                 profile: Dict, personality: Optional[PersonalityInsight]) -> float:
        """Calculate how well a companion matches user's current needs"""
        base_score = 0.5
        
        # Adjust based on recent moods and companion strengths
        if avg_score < 0.4:  # User seems to need support
            if any(mood in profile.get('best_for', []) for mood in ['depression', 'anxiety']):
                base_score += 0.3
        
        if avg_score > 0.7:  # User is doing well
            if 'motivation' in profile.get('best_for', []):
                base_score += 0.2
        
        return min(1.0, base_score)
    
    def _generate_companion_reasons(self, recent_moods: List[str], profile: Dict, 
                                  personality: Optional[PersonalityInsight]) -> List[str]:
        """Generate reasons why this companion is recommended"""
        reasons = []
        
        if any(strength in profile.get('best_for', []) for strength in ['anxiety', 'stress']):
            reasons.append("Great for emotional support during stressful times")
        
        if profile.get('energy_level') == 'high':
            reasons.append("High energy companion to boost motivation")
        
        reasons.append(f"Communication style matches your {profile.get('communication_style', 'needs')}")
        
        return reasons[:3]
    
    def _suggest_companion_times(self, mood_patterns: List[MoodPattern], profile: Dict) -> List[str]:
        """Suggest best times to interact with this companion"""
        # Analyze when user typically needs this type of support
        return ["morning", "evening"]  # Default suggestion
    
    def _get_default_companion_recommendations(self) -> List[CompanionRecommendation]:
        """Get default recommendations for new users"""
        return [
            CompanionRecommendation(
                companion_name="Blayzo",
                match_score=0.8,
                reasons=["Great starting companion", "Calm and supportive"],
                best_times=["morning", "evening"],
                interaction_style="gentle_wisdom"
            ),
            CompanionRecommendation(
                companion_name="Blayzica",
                match_score=0.7,
                reasons=["Energetic and motivating", "Good for building confidence"],
                best_times=["afternoon"],
                interaction_style="enthusiastic_encouraging"
            )
        ]
    
    def _calculate_friend_compatibility(self, user_personality: PersonalityInsight, 
                                      friend_personality: PersonalityInsight,
                                      user_moods: List[MoodPattern], 
                                      friend_moods: List[MoodPattern]) -> Dict:
        """Calculate compatibility between two users"""
        score = 0.5  # Base compatibility
        shared_interests = []
        complementary_traits = []
        activities = []
        
        # Check shared activity preferences
        user_activities = set(user_personality.activity_preferences)
        friend_activities = set(friend_personality.activity_preferences)
        shared_activities = user_activities.intersection(friend_activities)
        
        if shared_activities:
            score += 0.2
            shared_interests.extend(list(shared_activities))
        
        # Check complementary communication styles
        if user_personality.communication_style != friend_personality.communication_style:
            score += 0.1
            complementary_traits.append("different_communication_styles")
        
        # Determine interaction potential
        if score > 0.7:
            interaction_potential = "high"
        elif score > 0.5:
            interaction_potential = "medium"
        else:
            interaction_potential = "low"
        
        activities = ["chat", "mood_sharing", "wellness_challenges"]
        
        return {
            'score': min(1.0, score),
            'shared_interests': shared_interests,
            'complementary_traits': complementary_traits,
            'interaction_potential': interaction_potential,
            'activities': activities
        }
    
    def _check_mood_decline(self, user_id: str, patterns: List[MoodPattern]) -> List[WellnessAlert]:
        """Check for concerning mood decline patterns"""
        alerts = []
        
        for pattern in patterns:
            if pattern.average_score < 0.3 and pattern.mood_stability < 0.5:
                alert = WellnessAlert(
                    user_id=user_id,
                    alert_type="mood_decline",
                    severity="medium",
                    message=f"We've noticed your {pattern.dominant_mood} mood has been consistently low",
                    recommendations=[
                        "Consider speaking with a mental health professional",
                        "Try connecting with supportive friends",
                        "Engage in mood-boosting activities"
                    ],
                    created_at=datetime.now()
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_isolation_patterns(self, user_id: str) -> List[WellnessAlert]:
        """Check for social isolation patterns"""
        # Check recent social activity
        if not self.social_manager:
            return []
        
        # Simple check: if user hasn't sent messages recently
        try:
            recent_messages_query = """
            SELECT COUNT(*) FROM messages 
            WHERE sender_id = ? AND created_at >= ?
            """
            week_ago = datetime.now() - timedelta(days=7)
            result = self.db.fetch_one(recent_messages_query, (user_id, week_ago))
            
            if result and result[0] == 0:
                return [WellnessAlert(
                    user_id=user_id,
                    alert_type="isolation",
                    severity="low",
                    message="You haven't connected with friends recently",
                    recommendations=[
                        "Reach out to a friend you haven't talked to",
                        "Join a community or group activity",
                        "Consider scheduling social time"
                    ],
                    created_at=datetime.now()
                )]
        except Exception as e:
            logger.warning(f"Error checking isolation patterns: {e}")
        
        return []
    
    def _check_stress_patterns(self, user_id: str, patterns: List[MoodPattern]) -> List[WellnessAlert]:
        """Check for stress spike patterns"""
        alerts = []
        
        for pattern in patterns:
            if 'stress' in pattern.dominant_mood.lower() and pattern.average_score < 0.4:
                alert = WellnessAlert(
                    user_id=user_id,
                    alert_type="stress_spike",
                    severity="medium",
                    message="Your stress levels seem elevated lately",
                    recommendations=[
                        "Try deep breathing exercises",
                        "Take short breaks throughout the day",
                        "Consider talking to Blayzo for calming support"
                    ],
                    created_at=datetime.now()
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_positive_trends(self, user_id: str, patterns: List[MoodPattern]) -> List[WellnessAlert]:
        """Check for positive trends to encourage user"""
        alerts = []
        
        improving_patterns = [p for p in patterns if p.trends.get('weekly', 0) > 0.1]
        
        if improving_patterns:
            alert = WellnessAlert(
                user_id=user_id,
                alert_type="positive_trend",
                severity="low",
                message="Great news! Your mood has been improving recently",
                recommendations=[
                    "Keep doing what's working for you",
                    "Share your positive energy with friends",
                    "Celebrate your progress"
                ],
                created_at=datetime.now()
            )
            alerts.append(alert)
        
        return alerts
    
    def _cache_insights(self, insights: UserInsights):
        """Cache insights in database for future retrieval"""
        try:
            if not self.db:
                return
            
            # Store insights in database (create table if needed)
            cache_query = """
            INSERT OR REPLACE INTO user_insights_cache 
            (user_id, insights_data, created_at)
            VALUES (?, ?, ?)
            """
            
            insights_json = json.dumps(asdict(insights), default=str)
            self.db.execute_query(cache_query, (
                insights.user_id, insights_json, datetime.now()
            ))
            
        except Exception as e:
            logger.warning(f"Error caching insights: {e}")

# Database initialization
def init_insights_database(db_connection):
    """Initialize AI insights database tables"""
    try:
        # User insights cache table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS user_insights_cache (
                user_id TEXT PRIMARY KEY,
                insights_data TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                INDEX(created_at)
            )
        ''')
        
        # Mood entries table (if not exists)
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS mood_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                mood TEXT NOT NULL,
                score REAL NOT NULL,
                notes TEXT,
                created_at DATETIME NOT NULL,
                INDEX(user_id),
                INDEX(created_at),
                INDEX(mood)
            )
        ''')
        
        db_connection.commit()
        logger.info("AI insights database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing insights database: {e}")

# Global instance
ai_insights_engine = None

def init_ai_insights(db_manager=None, social_manager=None):
    """Initialize AI insights engine"""
    global ai_insights_engine
    try:
        ai_insights_engine = AIInsightsEngine(db_manager, social_manager)
        logger.info("AI insights engine initialized successfully")
        return ai_insights_engine
    except Exception as e:
        logger.error(f"Error initializing AI insights engine: {e}")
        return None

def get_ai_insights():
    """Get AI insights engine instance"""
    return ai_insights_engine