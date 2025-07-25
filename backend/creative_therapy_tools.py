"""
Creative Therapy Tools for SoulBridge AI
Art therapy, music therapy, journaling, and expressive arts tools
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import base64

logger = logging.getLogger(__name__)

class CreativeToolType(Enum):
    ART_THERAPY = "art_therapy"
    MUSIC_THERAPY = "music_therapy"
    JOURNALING = "journaling"
    POETRY = "poetry"
    COLLAGE = "collage"
    MEDITATION_ART = "meditation_art"
    EMOTION_MAPPING = "emotion_mapping"

class MoodCategory(Enum):
    PEACEFUL = {"name": "Peaceful", "color": "#87CEEB", "music": "ambient"}
    ENERGETIC = {"name": "Energetic", "color": "#FFD700", "music": "upbeat"}
    MELANCHOLY = {"name": "Melancholy", "color": "#9370DB", "music": "calm"}
    ANXIOUS = {"name": "Anxious", "color": "#FF6347", "music": "grounding"}
    HOPEFUL = {"name": "Hopeful", "color": "#32CD32", "music": "inspiring"}
    REFLECTIVE = {"name": "Reflective", "color": "#4682B4", "music": "contemplative"}

@dataclass
class CreativeWork:
    """Individual creative therapy work"""
    work_id: str
    user_id: str
    title: str
    tool_type: CreativeToolType
    content: Dict[str, Any]  # Canvas data, text, music selections, etc.
    mood_before: str
    mood_after: str
    emotion_tags: List[str]
    session_notes: str
    created_at: datetime
    updated_at: datetime
    is_private: bool = True
    share_with_therapist: bool = False

@dataclass
class JournalEntry:
    """Structured journaling entry"""
    entry_id: str
    user_id: str
    title: str
    content: str
    prompts_used: List[str]
    mood_rating: int  # 1-10 scale
    gratitude_items: List[str]
    challenges: List[str]
    achievements: List[str]
    goals: List[str]
    created_at: datetime
    is_private: bool = True

@dataclass
class ArtworkAnalysis:
    """AI analysis of artwork for therapeutic insights"""
    analysis_id: str
    work_id: str
    color_analysis: Dict[str, Any]
    composition_insights: Dict[str, Any]
    emotional_indicators: List[str]
    therapeutic_suggestions: List[str]
    progress_markers: Dict[str, Any]
    created_at: datetime

class CreativeTherapySystem:
    """Comprehensive creative therapy tools system"""
    
    def __init__(self):
        self.creative_works = defaultdict(list)  # user_id -> works
        self.journal_entries = defaultdict(list)  # user_id -> entries
        self.artwork_analyses = {}
        self.music_playlists = {}
        self.therapeutic_prompts = {}
        
        # Initialize therapeutic resources
        self._initialize_journaling_prompts()
        self._initialize_art_therapy_guides()
        self._initialize_music_therapy_playlists()
        
        logger.info("Creative Therapy System initialized")
    
    def _initialize_journaling_prompts(self):
        """Initialize therapeutic journaling prompts"""
        self.therapeutic_prompts = {
            "daily_reflection": [
                "What am I feeling right now, and what might be causing these emotions?",
                "What was the most meaningful moment of my day?",
                "What challenges did I face today, and how did I respond?",
                "What am I grateful for in this moment?",
                "How did I take care of myself today?"
            ],
            "anxiety_management": [
                "What thoughts are contributing to my anxiety right now?",
                "What evidence do I have that contradicts my worried thoughts?",
                "What would I tell a good friend who was feeling this way?",
                "What breathing or grounding techniques helped me today?",
                "What small step can I take to feel more in control?"
            ],
            "depression_support": [
                "Even in darkness, what small light can I find today?",
                "What would taking care of myself look like right now?",
                "What activities used to bring me joy? Can I try one today?",
                "Who in my life makes me feel valued and supported?",
                "What is one thing I can do to be kind to myself today?"
            ],
            "trauma_healing": [
                "What does safety feel like in my body right now?",
                "What boundaries do I need to set or maintain?",
                "How can I honor my healing journey today?",
                "What support do I need and deserve?",
                "What would I tell my younger self about surviving difficult times?"
            ],
            "self_discovery": [
                "What are my core values, and how did I honor them today?",
                "What patterns do I notice in my thoughts and behaviors?",
                "What would my authentic self do in this situation?",
                "What dreams or goals am I afraid to pursue, and why?",
                "How have I grown in the past month?"
            ]
        }
    
    def _initialize_art_therapy_guides(self):
        """Initialize art therapy exercise guides"""
        self.art_therapy_guides = {
            "emotion_mandala": {
                "title": "Emotion Mandala",
                "description": "Create a circular mandala representing your current emotional state",
                "instructions": [
                    "Start with a circle in the center representing your core emotion",
                    "Add colors that represent how you're feeling",
                    "Use patterns, shapes, or symbols that feel meaningful",
                    "Work from the center outward, letting emotions guide your choices",
                    "There's no right or wrong way - trust your instincts"
                ],
                "materials": ["Digital canvas", "Color palette", "Basic shapes"],
                "duration": "20-30 minutes"
            },
            "safe_place": {
                "title": "Safe Place Art",
                "description": "Draw or paint your ideal safe space",
                "instructions": [
                    "Close your eyes and imagine a place where you feel completely safe",
                    "What do you see, hear, smell, or feel in this space?",
                    "Begin sketching or painting this safe place",
                    "Include details that make it feel protective and nurturing",
                    "This is your sanctuary - make it uniquely yours"
                ],
                "materials": ["Canvas", "Full color palette", "Textures"],
                "duration": "30-45 minutes"
            },
            "anger_release": {
                "title": "Anger Release Art",
                "description": "Express and release anger through bold, dynamic art",
                "instructions": [
                    "Choose bold, intense colors that match your anger",
                    "Use strong, decisive strokes or marks",
                    "Let the anger flow through your hands onto the canvas",
                    "Don't worry about making it 'pretty' - focus on release",
                    "When finished, take deep breaths and notice how you feel"
                ],
                "materials": ["Large canvas", "Bold colors", "Large brushes"],
                "duration": "15-25 minutes"
            },
            "gratitude_garden": {
                "title": "Gratitude Garden",
                "description": "Create a garden of things you're grateful for",
                "instructions": [
                    "Think of things you're grateful for, big and small",
                    "Represent each one as a flower, tree, or plant",
                    "Use colors that feel warm and positive to you",
                    "Add details that represent why you're grateful",
                    "Let your garden grow as you think of more gratitudes"
                ],
                "materials": ["Canvas", "Warm colors", "Nature brushes"],
                "duration": "25-35 minutes"
            }
        }
    
    def _initialize_music_therapy_playlists(self):
        """Initialize curated music therapy playlists"""
        self.music_playlists = {
            "grounding": {
                "title": "Grounding & Centering",
                "description": "Music to help you feel present and grounded",
                "tracks": [
                    {"title": "Deep Breathing", "duration": 300, "type": "guided"},
                    {"title": "Forest Sounds", "duration": 600, "type": "nature"},
                    {"title": "Tibetan Bowls", "duration": 480, "type": "instrumental"},
                    {"title": "Ocean Waves", "duration": 720, "type": "nature"},
                    {"title": "Gentle Piano", "duration": 420, "type": "instrumental"}
                ],
                "mood": "calm",
                "purpose": "anxiety_relief"
            },
            "energy_boost": {
                "title": "Uplifting Energy",
                "description": "Music to lift your spirits and boost energy",
                "tracks": [
                    {"title": "Morning Sunshine", "duration": 240, "type": "uplifting"},
                    {"title": "Positive Vibrations", "duration": 280, "type": "upbeat"},
                    {"title": "Confident Steps", "duration": 260, "type": "motivational"},
                    {"title": "Joyful Heart", "duration": 300, "type": "happy"},
                    {"title": "Strength Within", "duration": 320, "type": "empowering"}
                ],
                "mood": "energetic",
                "purpose": "mood_boost"
            },
            "emotional_release": {
                "title": "Emotional Release",
                "description": "Music to support processing and releasing emotions",
                "tracks": [
                    {"title": "Safe to Feel", "duration": 360, "type": "supportive"},
                    {"title": "Tears of Healing", "duration": 420, "type": "cathartic"},
                    {"title": "Letting Go", "duration": 480, "type": "release"},
                    {"title": "Inner Strength", "duration": 380, "type": "empowering"},
                    {"title": "New Beginning", "duration": 340, "type": "hopeful"}
                ],
                "mood": "reflective",
                "purpose": "emotional_processing"
            },
            "sleep_peace": {
                "title": "Peaceful Sleep",
                "description": "Gentle music for relaxation and sleep",
                "tracks": [
                    {"title": "Twilight Calm", "duration": 900, "type": "ambient"},
                    {"title": "Gentle Lullaby", "duration": 600, "type": "soft"},
                    {"title": "Night Sounds", "duration": 1200, "type": "nature"},
                    {"title": "Dream Journey", "duration": 780, "type": "meditative"},
                    {"title": "Deep Rest", "duration": 1500, "type": "sleep"}
                ],
                "mood": "peaceful",
                "purpose": "sleep_aid"
            }
        }
    
    def create_artwork(self, user_id: str, artwork_data: Dict[str, Any]) -> str:
        """Create new digital artwork"""
        work_id = str(uuid.uuid4())
        
        artwork = CreativeWork(
            work_id=work_id,
            user_id=user_id,
            title=artwork_data.get("title", "Untitled Artwork"),
            tool_type=CreativeToolType(artwork_data.get("tool_type", "art_therapy")),
            content={
                "canvas_data": artwork_data.get("canvas_data"),
                "colors_used": artwork_data.get("colors_used", []),
                "tools_used": artwork_data.get("tools_used", []),
                "time_spent": artwork_data.get("time_spent", 0)
            },
            mood_before=artwork_data.get("mood_before", ""),
            mood_after=artwork_data.get("mood_after", ""),
            emotion_tags=artwork_data.get("emotion_tags", []),
            session_notes=artwork_data.get("session_notes", ""),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_private=artwork_data.get("is_private", True),
            share_with_therapist=artwork_data.get("share_with_therapist", False)
        )
        
        self.creative_works[user_id].append(artwork)
        
        # Generate AI analysis if requested
        if artwork_data.get("analyze", False):
            self._analyze_artwork(artwork)
        
        logger.info(f"Created artwork {work_id} for user {user_id}")
        return work_id
    
    def create_journal_entry(self, user_id: str, entry_data: Dict[str, Any]) -> str:
        """Create new journal entry"""
        entry_id = str(uuid.uuid4())
        
        entry = JournalEntry(
            entry_id=entry_id,
            user_id=user_id,
            title=entry_data.get("title", f"Journal Entry - {datetime.now().strftime('%Y-%m-%d')}"),
            content=entry_data.get("content", ""),
            prompts_used=entry_data.get("prompts_used", []),
            mood_rating=entry_data.get("mood_rating", 5),
            gratitude_items=entry_data.get("gratitude_items", []),
            challenges=entry_data.get("challenges", []),
            achievements=entry_data.get("achievements", []),
            goals=entry_data.get("goals", []),
            created_at=datetime.now(),
            is_private=entry_data.get("is_private", True)
        )
        
        self.journal_entries[user_id].append(entry)
        
        logger.info(f"Created journal entry {entry_id} for user {user_id}")
        return entry_id
    
    def _analyze_artwork(self, artwork: CreativeWork) -> str:
        """Generate AI analysis of artwork for therapeutic insights"""
        analysis_id = str(uuid.uuid4())
        
        # Simplified analysis - would use AI vision models in production
        colors_used = artwork.content.get("colors_used", [])
        
        # Color psychology insights
        color_insights = []
        if "red" in colors_used:
            color_insights.append("Red may indicate strong emotions, passion, or energy")
        if "blue" in colors_used:
            color_insights.append("Blue often represents calm, sadness, or introspection")
        if "yellow" in colors_used:
            color_insights.append("Yellow can represent joy, optimism, or anxiety")
        if "green" in colors_used:
            color_insights.append("Green may indicate growth, harmony, or healing")
        if "purple" in colors_used:
            color_insights.append("Purple often represents creativity, spirituality, or mystery")
        
        # Therapeutic suggestions based on patterns
        suggestions = [
            "Consider exploring the emotions behind your color choices",
            "Notice how your mood shifted during the creative process",
            "Art can be a safe way to express difficult feelings"
        ]
        
        if artwork.mood_before != artwork.mood_after:
            suggestions.append("The change in your mood suggests this was a transformative creative experience")
        
        analysis = ArtworkAnalysis(
            analysis_id=analysis_id,
            work_id=artwork.work_id,
            color_analysis={"dominant_colors": colors_used, "insights": color_insights},
            composition_insights={"style": "expressive", "energy": "medium"},
            emotional_indicators=artwork.emotion_tags,
            therapeutic_suggestions=suggestions,
            progress_markers={"creativity_level": "developing", "emotional_expression": "strong"},
            created_at=datetime.now()
        )
        
        self.artwork_analyses[analysis_id] = analysis
        return analysis_id
    
    def get_journaling_prompts(self, category: str = None) -> Dict[str, List[str]]:
        """Get therapeutic journaling prompts"""
        if category and category in self.therapeutic_prompts:
            return {category: self.therapeutic_prompts[category]}
        return self.therapeutic_prompts
    
    def get_art_therapy_guides(self) -> Dict[str, Any]:
        """Get art therapy exercise guides"""
        return self.art_therapy_guides
    
    def get_music_playlists(self, mood: str = None, purpose: str = None) -> Dict[str, Any]:
        """Get music therapy playlists"""
        if not mood and not purpose:
            return self.music_playlists
        
        filtered_playlists = {}
        for playlist_id, playlist in self.music_playlists.items():
            if mood and playlist.get("mood") == mood:
                filtered_playlists[playlist_id] = playlist
            elif purpose and playlist.get("purpose") == purpose:
                filtered_playlists[playlist_id] = playlist
        
        return filtered_playlists
    
    def get_user_creative_works(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's creative works"""
        works = self.creative_works.get(user_id, [])
        recent_works = sorted(works, key=lambda x: x.created_at, reverse=True)[:limit]
        
        return [asdict(work) for work in recent_works]
    
    def get_user_journal_entries(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's journal entries"""
        entries = self.journal_entries.get(user_id, [])
        recent_entries = sorted(entries, key=lambda x: x.created_at, reverse=True)[:limit]
        
        return [asdict(entry) for entry in recent_entries]
    
    def get_creative_insights(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get creative therapy insights for user"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Analyze recent creative works
        recent_works = [
            work for work in self.creative_works.get(user_id, [])
            if work.created_at > cutoff_date
        ]
        
        recent_entries = [
            entry for entry in self.journal_entries.get(user_id, [])
            if entry.created_at > cutoff_date
        ]
        
        insights = {
            "total_creative_works": len(recent_works),
            "total_journal_entries": len(recent_entries),
            "most_used_tools": self._get_most_used_tools(recent_works),
            "mood_trends": self._analyze_mood_trends(recent_works, recent_entries),
            "creative_frequency": len(recent_works + recent_entries) / max(days, 1),
            "progress_indicators": self._get_progress_indicators(recent_works, recent_entries)
        }
        
        return insights
    
    def _get_most_used_tools(self, works: List[CreativeWork]) -> Dict[str, int]:
        """Get most frequently used creative tools"""
        tool_counts = defaultdict(int)
        for work in works:
            tool_counts[work.tool_type.value] += 1
        return dict(tool_counts)
    
    def _analyze_mood_trends(self, works: List[CreativeWork], entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze mood trends across creative activities"""
        mood_improvements = 0
        total_mood_comparisons = 0
        
        # Analyze artwork mood changes
        for work in works:
            if work.mood_before and work.mood_after:
                # Simplified mood comparison - would use more sophisticated analysis
                if work.mood_after != work.mood_before:
                    mood_improvements += 1
                total_mood_comparisons += 1
        
        # Analyze journal mood ratings
        journal_moods = [entry.mood_rating for entry in entries if entry.mood_rating]
        avg_mood = sum(journal_moods) / len(journal_moods) if journal_moods else 5
        
        return {
            "mood_improvement_rate": mood_improvements / max(total_mood_comparisons, 1),
            "average_journal_mood": avg_mood,
            "mood_trend": "improving" if avg_mood > 5 else "stable" if avg_mood == 5 else "needs_attention"
        }
    
    def _get_progress_indicators(self, works: List[CreativeWork], entries: List[JournalEntry]) -> Dict[str, str]:
        """Get therapeutic progress indicators"""
        indicators = {}
        
        # Creative expression frequency
        if len(works) > 10:
            indicators["creative_expression"] = "highly_active"
        elif len(works) > 5:
            indicators["creative_expression"] = "active"
        else:
            indicators["creative_expression"] = "developing"
        
        # Emotional processing through journaling
        if len(entries) > 15:
            indicators["emotional_processing"] = "consistent"
        elif len(entries) > 5:
            indicators["emotional_processing"] = "regular"
        else:
            indicators["emotional_processing"] = "occasional"
        
        # Variety in creative tools
        unique_tools = len(set(work.tool_type for work in works))
        if unique_tools > 3:
            indicators["creative_exploration"] = "diverse"
        elif unique_tools > 1:
            indicators["creative_exploration"] = "expanding"
        else:
            indicators["creative_exploration"] = "focused"
        
        return indicators
    
    def suggest_creative_activity(self, user_id: str, current_mood: str) -> Dict[str, Any]:
        """Suggest creative activity based on user's current mood"""
        mood_activities = {
            "anxious": {
                "primary": "grounding_art",
                "secondary": "guided_journaling",
                "music": "grounding",
                "prompt": "What would help you feel more grounded right now?"
            },
            "sad": {
                "primary": "emotion_expression",
                "secondary": "gratitude_journaling", 
                "music": "emotional_release",
                "prompt": "How can you honor what you're feeling while nurturing yourself?"
            },
            "angry": {
                "primary": "anger_release_art",
                "secondary": "strength_journaling",
                "music": "energy_boost",
                "prompt": "What is your anger trying to tell you?"
            },
            "overwhelmed": {
                "primary": "simple_mandala",
                "secondary": "brain_dump_journaling",
                "music": "grounding",
                "prompt": "What's one small step you can take right now?"
            },
            "peaceful": {
                "primary": "gratitude_art",
                "secondary": "reflection_journaling",
                "music": "sleep_peace",
                "prompt": "How can you carry this peace with you?"
            }
        }
        
        return mood_activities.get(current_mood.lower(), {
            "primary": "free_expression",
            "secondary": "daily_reflection",
            "music": "grounding",
            "prompt": "What does your heart want to express today?"
        })
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics for admin view"""
        total_works = sum(len(works) for works in self.creative_works.values())
        total_entries = sum(len(entries) for entries in self.journal_entries.values())
        
        return {
            "total_users": len(self.creative_works) + len(self.journal_entries),
            "total_artworks": total_works,
            "total_journal_entries": total_entries,
            "total_analyses": len(self.artwork_analyses),
            "active_users_today": self._count_active_users_today(),
            "popular_tools": self._get_popular_creative_tools()
        }
    
    def _count_active_users_today(self) -> int:
        """Count users active in creative therapy today"""
        today = datetime.now().date()
        active_users = set()
        
        # Check artwork creation
        for user_id, works in self.creative_works.items():
            if any(work.created_at.date() == today for work in works):
                active_users.add(user_id)
        
        # Check journal entries
        for user_id, entries in self.journal_entries.items():
            if any(entry.created_at.date() == today for entry in entries):
                active_users.add(user_id)
        
        return len(active_users)
    
    def _get_popular_creative_tools(self) -> Dict[str, int]:
        """Get most popular creative tools"""
        tool_counts = defaultdict(int)
        
        for works in self.creative_works.values():
            for work in works:
                tool_counts[work.tool_type.value] += 1
        
        return dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5])