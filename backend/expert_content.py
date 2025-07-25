"""
Expert Content Management System
Professional wellness content, guided resources, and expert articles
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    ARTICLE = "article"
    GUIDED_MEDITATION = "guided_meditation"
    EXERCISE_ROUTINE = "exercise_routine"
    BREATHING_EXERCISE = "breathing_exercise"
    SLEEP_STORY = "sleep_story"
    WELLNESS_COURSE = "wellness_course"
    EXPERT_VIDEO = "expert_video"
    AUDIO_SESSION = "audio_session"

class ExpertiseLevel(Enum):
    LICENSED_THERAPIST = "licensed_therapist"
    CERTIFIED_COACH = "certified_coach"
    MEDICAL_PROFESSIONAL = "medical_professional"
    WELLNESS_EXPERT = "wellness_expert"
    CERTIFIED_INSTRUCTOR = "certified_instructor"

class ContentCategory(Enum):
    ANXIETY_MANAGEMENT = "anxiety_management"
    DEPRESSION_SUPPORT = "depression_support"
    STRESS_RELIEF = "stress_relief"
    SLEEP_HYGIENE = "sleep_hygiene"
    MINDFULNESS = "mindfulness"
    SELF_COMPASSION = "self_compassion"
    RELATIONSHIPS = "relationships"
    WORK_LIFE_BALANCE = "work_life_balance"
    TRAUMA_HEALING = "trauma_healing"
    ADDICTION_RECOVERY = "addiction_recovery"

@dataclass
class ExpertProfile:
    expert_id: str
    name: str
    title: str
    expertise_level: ExpertiseLevel
    specializations: List[ContentCategory]
    bio: str
    credentials: List[str]
    years_experience: int
    rating: float
    total_content: int
    verified: bool
    avatar_url: Optional[str]
    website: Optional[str]
    linkedin: Optional[str]
    created_at: datetime

@dataclass
class ExpertContent:
    content_id: str
    expert_id: str
    title: str
    description: str
    content_type: ContentType
    category: ContentCategory
    difficulty_level: str  # beginner, intermediate, advanced
    duration_minutes: Optional[int]
    tags: List[str]
    content_url: Optional[str]  # URL to audio/video content
    content_text: Optional[str]  # Text content for articles
    transcript: Optional[str]  # Transcript for audio/video
    thumbnail_url: Optional[str]
    is_premium: bool
    is_featured: bool
    view_count: int
    rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ContentProgress:
    progress_id: str
    user_id: str
    content_id: str
    progress_percentage: float
    last_position: Optional[int]  # For audio/video content
    completed: bool
    completed_at: Optional[datetime]
    notes: Optional[str]
    rating: Optional[float]
    started_at: datetime
    last_accessed: datetime

@dataclass
class WellnessCourse:
    course_id: str
    expert_id: str
    title: str
    description: str
    category: ContentCategory
    difficulty_level: str
    total_sessions: int
    duration_weeks: int
    enrollment_count: int
    rating: float
    is_premium: bool
    price: Optional[float]
    curriculum: List[Dict[str, Any]]  # Session details
    prerequisites: List[str]
    learning_objectives: List[str]
    certificate_available: bool
    created_at: datetime

@dataclass
class LiveEvent:
    event_id: str
    expert_id: str
    title: str
    description: str
    event_type: str  # workshop, webinar, q_and_a, meditation_session
    category: ContentCategory
    start_time: datetime
    duration_minutes: int
    max_participants: Optional[int]
    current_participants: int
    is_premium: bool
    price: Optional[float]
    meeting_url: Optional[str]
    recording_url: Optional[str]
    status: str  # scheduled, live, completed, cancelled
    created_at: datetime

class ExpertContentManager:
    """Manages expert content, courses, and live events"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        
        # Sample expert content for initial seeding
        self.sample_content = {
            ContentType.GUIDED_MEDITATION: [
                {
                    'title': '10-Minute Morning Mindfulness',
                    'description': 'Start your day with intention and clarity through guided mindfulness meditation.',
                    'category': ContentCategory.MINDFULNESS,
                    'duration_minutes': 10,
                    'difficulty_level': 'beginner'
                },
                {
                    'title': 'Anxiety Relief Breathing Session',
                    'description': 'Specialized breathing techniques designed to reduce anxiety and promote calm.',
                    'category': ContentCategory.ANXIETY_MANAGEMENT,
                    'duration_minutes': 15,
                    'difficulty_level': 'beginner'
                }
            ],
            ContentType.ARTICLE: [
                {
                    'title': 'Understanding Sleep Hygiene: A Complete Guide',
                    'description': 'Evidence-based strategies for improving sleep quality and establishing healthy sleep habits.',
                    'category': ContentCategory.SLEEP_HYGIENE,
                    'difficulty_level': 'beginner'
                },
                {
                    'title': 'Building Resilience: Coping with Life\'s Challenges',
                    'description': 'Practical techniques for developing emotional resilience and managing stress.',
                    'category': ContentCategory.STRESS_RELIEF,
                    'difficulty_level': 'intermediate'
                }
            ]
        }
        
        logger.info("Expert Content Manager initialized")
    
    def create_expert_profile(self, name: str, title: str, expertise_level: ExpertiseLevel,
                            specializations: List[ContentCategory], bio: str, 
                            credentials: List[str], years_experience: int) -> Optional[str]:
        """Create a new expert profile"""
        try:
            if not self.db:
                return None
            
            expert_id = str(uuid.uuid4())
            
            expert = ExpertProfile(
                expert_id=expert_id,
                name=name,
                title=title,
                expertise_level=expertise_level,
                specializations=specializations,
                bio=bio,
                credentials=credentials,
                years_experience=years_experience,
                rating=0.0,
                total_content=0,
                verified=False,  # Requires manual verification
                avatar_url=None,
                website=None,
                linkedin=None,
                created_at=datetime.now()
            )
            
            # Store expert profile
            query = """
                INSERT INTO expert_profiles
                (expert_id, name, title, expertise_level, specializations, bio, 
                 credentials, years_experience, rating, total_content, verified,
                 avatar_url, website, linkedin, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                expert.expert_id, expert.name, expert.title,
                expert.expertise_level.value, json.dumps([s.value for s in expert.specializations]),
                expert.bio, json.dumps(expert.credentials), expert.years_experience,
                expert.rating, expert.total_content, expert.verified,
                expert.avatar_url, expert.website, expert.linkedin, expert.created_at
            ))
            
            logger.info(f"Expert profile created: {expert_id} ({name})")
            return expert_id
            
        except Exception as e:
            logger.error(f"Error creating expert profile: {e}")
            return None
    
    def create_expert_content(self, expert_id: str, title: str, description: str,
                            content_type: ContentType, category: ContentCategory,
                            difficulty_level: str = "beginner", duration_minutes: Optional[int] = None,
                            content_text: Optional[str] = None, is_premium: bool = False) -> Optional[str]:
        """Create new expert content"""
        try:
            if not self.db:
                return None
            
            content_id = str(uuid.uuid4())
            
            content = ExpertContent(
                content_id=content_id,
                expert_id=expert_id,
                title=title,
                description=description,
                content_type=content_type,
                category=category,
                difficulty_level=difficulty_level,
                duration_minutes=duration_minutes,
                tags=self._generate_content_tags(category, content_type),
                content_url=None,
                content_text=content_text,
                transcript=None,
                thumbnail_url=None,
                is_premium=is_premium,
                is_featured=False,
                view_count=0,
                rating=0.0,
                rating_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={}
            )
            
            # Store content
            query = """
                INSERT INTO expert_content
                (content_id, expert_id, title, description, content_type, category,
                 difficulty_level, duration_minutes, tags, content_url, content_text,
                 transcript, thumbnail_url, is_premium, is_featured, view_count,
                 rating, rating_count, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                content.content_id, content.expert_id, content.title, content.description,
                content.content_type.value, content.category.value, content.difficulty_level,
                content.duration_minutes, json.dumps(content.tags), content.content_url,
                content.content_text, content.transcript, content.thumbnail_url,
                content.is_premium, content.is_featured, content.view_count,
                content.rating, content.rating_count, content.created_at,
                content.updated_at, json.dumps(content.metadata)
            ))
            
            # Update expert total content count
            self.db.execute_query(
                "UPDATE expert_profiles SET total_content = total_content + 1 WHERE expert_id = ?",
                (expert_id,)
            )
            
            logger.info(f"Expert content created: {content_id} ({title})")
            return content_id
            
        except Exception as e:
            logger.error(f"Error creating expert content: {e}")
            return None
    
    def get_featured_content(self, limit: int = 10) -> List[ExpertContent]:
        """Get featured expert content"""
        try:
            if not self.db:
                return []
            
            query = """
                SELECT ec.*, ep.name as expert_name, ep.title as expert_title
                FROM expert_content ec
                JOIN expert_profiles ep ON ec.expert_id = ep.expert_id
                WHERE ec.is_featured = 1 OR ec.rating >= 4.5
                ORDER BY ec.is_featured DESC, ec.rating DESC, ec.view_count DESC
                LIMIT ?
            """
            
            results = self.db.fetch_all(query, (limit,))
            return self._parse_content_results(results)
            
        except Exception as e:
            logger.error(f"Error getting featured content: {e}")
            return []
    
    def get_content_by_category(self, category: ContentCategory, limit: int = 20) -> List[ExpertContent]:
        """Get content by category"""
        try:
            if not self.db:
                return []
            
            query = """
                SELECT ec.*, ep.name as expert_name, ep.title as expert_title
                FROM expert_content ec
                JOIN expert_profiles ep ON ec.expert_id = ep.expert_id
                WHERE ec.category = ?
                ORDER BY ec.rating DESC, ec.view_count DESC
                LIMIT ?
            """
            
            results = self.db.fetch_all(query, (category.value, limit))
            return self._parse_content_results(results)
            
        except Exception as e:
            logger.error(f"Error getting content by category: {e}")
            return []
    
    def search_content(self, query: str, content_type: Optional[ContentType] = None,
                      category: Optional[ContentCategory] = None, limit: int = 20) -> List[ExpertContent]:
        """Search expert content"""
        try:
            if not self.db:
                return []
            
            search_query = """
                SELECT ec.*, ep.name as expert_name, ep.title as expert_title
                FROM expert_content ec
                JOIN expert_profiles ep ON ec.expert_id = ep.expert_id
                WHERE (ec.title LIKE ? OR ec.description LIKE ? OR ec.tags LIKE ?)
            """
            
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
            
            if content_type:
                search_query += " AND ec.content_type = ?"
                params.append(content_type.value)
            
            if category:
                search_query += " AND ec.category = ?"
                params.append(category.value)
            
            search_query += " ORDER BY ec.rating DESC, ec.view_count DESC LIMIT ?"
            params.append(limit)
            
            results = self.db.fetch_all(search_query, tuple(params))
            return self._parse_content_results(results)
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    def track_content_progress(self, user_id: str, content_id: str, 
                             progress_percentage: float, last_position: Optional[int] = None) -> bool:
        """Track user progress on content"""
        try:
            if not self.db:
                return False
            
            # Check if progress record exists
            existing_query = "SELECT progress_id FROM content_progress WHERE user_id = ? AND content_id = ?"
            existing = self.db.fetch_one(existing_query, (user_id, content_id))
            
            completed = progress_percentage >= 100.0
            now = datetime.now()
            
            if existing:
                # Update existing progress
                query = """
                    UPDATE content_progress 
                    SET progress_percentage = ?, last_position = ?, completed = ?,
                        completed_at = ?, last_accessed = ?
                    WHERE user_id = ? AND content_id = ?
                """
                
                self.db.execute_query(query, (
                    progress_percentage, last_position, completed,
                    now if completed else None, now, user_id, content_id
                ))
            else:
                # Create new progress record
                progress_id = str(uuid.uuid4())
                query = """
                    INSERT INTO content_progress
                    (progress_id, user_id, content_id, progress_percentage, last_position,
                     completed, completed_at, started_at, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db.execute_query(query, (
                    progress_id, user_id, content_id, progress_percentage, last_position,
                    completed, now if completed else None, now, now
                ))
            
            # Update content view count on first access
            if not existing:
                self.db.execute_query(
                    "UPDATE expert_content SET view_count = view_count + 1 WHERE content_id = ?",
                    (content_id,)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking content progress: {e}")
            return False
    
    def create_wellness_course(self, expert_id: str, title: str, description: str,
                             category: ContentCategory, difficulty_level: str,
                             duration_weeks: int, curriculum: List[Dict[str, Any]],
                             is_premium: bool = False, price: Optional[float] = None) -> Optional[str]:
        """Create a wellness course"""
        try:
            if not self.db:
                return None
            
            course_id = str(uuid.uuid4())
            
            course = WellnessCourse(
                course_id=course_id,
                expert_id=expert_id,
                title=title,
                description=description,
                category=category,
                difficulty_level=difficulty_level,
                total_sessions=len(curriculum),
                duration_weeks=duration_weeks,
                enrollment_count=0,
                rating=0.0,
                is_premium=is_premium,
                price=price,
                curriculum=curriculum,
                prerequisites=[],
                learning_objectives=[],
                certificate_available=True,
                created_at=datetime.now()
            )
            
            # Store course
            query = """
                INSERT INTO wellness_courses
                (course_id, expert_id, title, description, category, difficulty_level,
                 total_sessions, duration_weeks, enrollment_count, rating, is_premium,
                 price, curriculum, prerequisites, learning_objectives, certificate_available,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                course.course_id, course.expert_id, course.title, course.description,
                course.category.value, course.difficulty_level, course.total_sessions,
                course.duration_weeks, course.enrollment_count, course.rating,
                course.is_premium, course.price, json.dumps(course.curriculum),
                json.dumps(course.prerequisites), json.dumps(course.learning_objectives),
                course.certificate_available, course.created_at
            ))
            
            logger.info(f"Wellness course created: {course_id} ({title})")
            return course_id
            
        except Exception as e:
            logger.error(f"Error creating wellness course: {e}")
            return None
    
    def schedule_live_event(self, expert_id: str, title: str, description: str,
                          event_type: str, category: ContentCategory, start_time: datetime,
                          duration_minutes: int, max_participants: Optional[int] = None,
                          is_premium: bool = False, price: Optional[float] = None) -> Optional[str]:
        """Schedule a live event"""
        try:
            if not self.db:
                return None
            
            event_id = str(uuid.uuid4())
            
            event = LiveEvent(
                event_id=event_id,
                expert_id=expert_id,
                title=title,
                description=description,
                event_type=event_type,
                category=category,
                start_time=start_time,
                duration_minutes=duration_minutes,
                max_participants=max_participants,
                current_participants=0,
                is_premium=is_premium,
                price=price,
                meeting_url=None,  # Will be set when event goes live
                recording_url=None,
                status='scheduled',
                created_at=datetime.now()
            )
            
            # Store event
            query = """
                INSERT INTO live_events
                (event_id, expert_id, title, description, event_type, category,
                 start_time, duration_minutes, max_participants, current_participants,
                 is_premium, price, meeting_url, recording_url, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                event.event_id, event.expert_id, event.title, event.description,
                event.event_type, event.category.value, event.start_time,
                event.duration_minutes, event.max_participants, event.current_participants,
                event.is_premium, event.price, event.meeting_url, event.recording_url,
                event.status, event.created_at
            ))
            
            logger.info(f"Live event scheduled: {event_id} ({title})")
            return event_id
            
        except Exception as e:
            logger.error(f"Error scheduling live event: {e}")
            return None
    
    def get_personalized_content_recommendations(self, user_id: str, limit: int = 10) -> List[ExpertContent]:
        """Get personalized content recommendations based on user interests"""
        try:
            if not self.db:
                return []
            
            # Get user's mood patterns and community interests
            user_moods_query = """
                SELECT mood, COUNT(*) as frequency 
                FROM mood_entries 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY mood 
                ORDER BY frequency DESC 
                LIMIT 3
            """
            
            week_ago = datetime.now() - timedelta(days=7)
            user_moods = self.db.fetch_all(user_moods_query, (user_id, week_ago))
            
            # Map moods to content categories
            mood_to_category = {
                'anxious': ContentCategory.ANXIETY_MANAGEMENT,
                'stressed': ContentCategory.STRESS_RELIEF,
                'sad': ContentCategory.DEPRESSION_SUPPORT,
                'tired': ContentCategory.SLEEP_HYGIENE,
                'overwhelmed': ContentCategory.WORK_LIFE_BALANCE
            }
            
            recommended_categories = []
            for mood, frequency in user_moods:
                if mood in mood_to_category:
                    recommended_categories.append(mood_to_category[mood].value)
            
            # If no mood patterns, recommend popular content
            if not recommended_categories:
                recommended_categories = [
                    ContentCategory.MINDFULNESS.value,
                    ContentCategory.STRESS_RELIEF.value
                ]
            
            # Get recommendations
            category_placeholders = ','.join(['?' for _ in recommended_categories])
            query = f"""
                SELECT ec.*, ep.name as expert_name, ep.title as expert_title
                FROM expert_content ec
                JOIN expert_profiles ep ON ec.expert_id = ep.expert_id
                WHERE ec.category IN ({category_placeholders})
                AND ec.content_id NOT IN (
                    SELECT content_id FROM content_progress WHERE user_id = ? AND completed = 1
                )
                ORDER BY ec.rating DESC, ec.view_count DESC
                LIMIT ?
            """
            
            params = recommended_categories + [user_id, limit]
            results = self.db.fetch_all(query, tuple(params))
            
            return self._parse_content_results(results)
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {e}")
            return []
    
    def _parse_content_results(self, results: List[tuple]) -> List[ExpertContent]:
        """Parse database results into ExpertContent objects"""
        content_list = []
        
        for row in results:
            try:
                content = ExpertContent(
                    content_id=row[0],
                    expert_id=row[1],
                    title=row[2],
                    description=row[3],
                    content_type=ContentType(row[4]),
                    category=ContentCategory(row[5]),
                    difficulty_level=row[6],
                    duration_minutes=row[7],
                    tags=json.loads(row[8]) if row[8] else [],
                    content_url=row[9],
                    content_text=row[10],
                    transcript=row[11],
                    thumbnail_url=row[12],
                    is_premium=bool(row[13]),
                    is_featured=bool(row[14]),
                    view_count=row[15],
                    rating=row[16],
                    rating_count=row[17],
                    created_at=row[18] if isinstance(row[18], datetime) else datetime.fromisoformat(row[18]),
                    updated_at=row[19] if isinstance(row[19], datetime) else datetime.fromisoformat(row[19]),
                    metadata=json.loads(row[20]) if row[20] else {}
                )
                content_list.append(content)
            except Exception as e:
                logger.warning(f"Error parsing content result: {e}")
                continue
        
        return content_list
    
    def _generate_content_tags(self, category: ContentCategory, content_type: ContentType) -> List[str]:
        """Generate relevant tags for content"""
        category_tags = {
            ContentCategory.ANXIETY_MANAGEMENT: ['anxiety', 'calm', 'breathing', 'relaxation'],
            ContentCategory.DEPRESSION_SUPPORT: ['mood', 'hope', 'support', 'healing'],
            ContentCategory.STRESS_RELIEF: ['stress', 'relief', 'peace', 'balance'],
            ContentCategory.SLEEP_HYGIENE: ['sleep', 'rest', 'bedtime', 'insomnia'],
            ContentCategory.MINDFULNESS: ['present', 'awareness', 'meditation', 'focus'],
            ContentCategory.SELF_COMPASSION: ['kindness', 'self-love', 'acceptance', 'forgiveness']
        }
        
        type_tags = {
            ContentType.GUIDED_MEDITATION: ['meditation', 'guided', 'practice'],
            ContentType.ARTICLE: ['education', 'tips', 'guide'],
            ContentType.BREATHING_EXERCISE: ['breathing', 'exercise', 'technique'],
            ContentType.SLEEP_STORY: ['sleep', 'story', 'bedtime'],
            ContentType.EXERCISE_ROUTINE: ['exercise', 'movement', 'routine']
        }
        
        tags = category_tags.get(category, []) + type_tags.get(content_type, [])
        return list(set(tags))  # Remove duplicates
    
    def seed_sample_content(self):
        """Seed database with sample expert content"""
        try:
            # Create sample expert
            expert_id = self.create_expert_profile(
                name="Dr. Sarah Chen",
                title="Licensed Clinical Psychologist",
                expertise_level=ExpertiseLevel.LICENSED_THERAPIST,
                specializations=[ContentCategory.ANXIETY_MANAGEMENT, ContentCategory.MINDFULNESS],
                bio="Dr. Chen specializes in mindfulness-based therapy with over 15 years of experience.",
                credentials=["Ph.D. in Clinical Psychology", "Licensed Therapist", "Mindfulness Instructor"],
                years_experience=15
            )
            
            if expert_id:
                # Create sample content
                for content_type, content_list in self.sample_content.items():
                    for content_data in content_list:
                        self.create_expert_content(
                            expert_id=expert_id,
                            title=content_data['title'],
                            description=content_data['description'],
                            content_type=content_type,
                            category=content_data['category'],
                            difficulty_level=content_data['difficulty_level'],
                            duration_minutes=content_data.get('duration_minutes'),
                            content_text="Sample content text would go here..." if content_type == ContentType.ARTICLE else None
                        )
            
            logger.info("Sample expert content seeded successfully")
            
        except Exception as e:
            logger.error(f"Error seeding sample content: {e}")

# Database initialization
def init_expert_content_database(db_connection):
    """Initialize expert content database tables"""
    try:
        # Expert profiles table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS expert_profiles (
                expert_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                expertise_level TEXT NOT NULL,
                specializations TEXT NOT NULL,
                bio TEXT NOT NULL,
                credentials TEXT NOT NULL,
                years_experience INTEGER NOT NULL,
                rating REAL DEFAULT 0.0,
                total_content INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT 0,
                avatar_url TEXT,
                website TEXT,
                linkedin TEXT,
                created_at DATETIME NOT NULL,
                INDEX(expertise_level),
                INDEX(verified),
                INDEX(rating)
            )
        ''')
        
        # Expert content table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS expert_content (
                content_id TEXT PRIMARY KEY,
                expert_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                content_type TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                duration_minutes INTEGER,
                tags TEXT,
                content_url TEXT,
                content_text TEXT,
                transcript TEXT,
                thumbnail_url TEXT,
                is_premium BOOLEAN DEFAULT 0,
                is_featured BOOLEAN DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                metadata TEXT,
                INDEX(expert_id),
                INDEX(content_type),
                INDEX(category),
                INDEX(is_featured),
                INDEX(rating),
                INDEX(created_at)
            )
        ''')
        
        # Content progress table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS content_progress (
                progress_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content_id TEXT NOT NULL,
                progress_percentage REAL DEFAULT 0.0,
                last_position INTEGER,
                completed BOOLEAN DEFAULT 0,
                completed_at DATETIME,
                notes TEXT,
                rating REAL,
                started_at DATETIME NOT NULL,
                last_accessed DATETIME NOT NULL,
                INDEX(user_id),
                INDEX(content_id),
                INDEX(completed),
                UNIQUE(user_id, content_id)
            )
        ''')
        
        # Wellness courses table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS wellness_courses (
                course_id TEXT PRIMARY KEY,
                expert_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                total_sessions INTEGER NOT NULL,
                duration_weeks INTEGER NOT NULL,
                enrollment_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                is_premium BOOLEAN DEFAULT 0,
                price REAL,
                curriculum TEXT NOT NULL,
                prerequisites TEXT,
                learning_objectives TEXT,
                certificate_available BOOLEAN DEFAULT 1,
                created_at DATETIME NOT NULL,
                INDEX(expert_id),
                INDEX(category),
                INDEX(rating),
                INDEX(created_at)
            )
        ''')
        
        # Live events table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS live_events (
                event_id TEXT PRIMARY KEY,
                expert_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                event_type TEXT NOT NULL,
                category TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                duration_minutes INTEGER NOT NULL,
                max_participants INTEGER,
                current_participants INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                price REAL,
                meeting_url TEXT,
                recording_url TEXT,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                INDEX(expert_id),
                INDEX(start_time),
                INDEX(status),
                INDEX(category)
            )
        ''')
        
        db_connection.commit()
        logger.info("Expert content database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing expert content database: {e}")

# Global instance
expert_content_manager = None

def init_expert_content_manager(db_manager=None):
    """Initialize expert content manager"""
    global expert_content_manager
    try:
        expert_content_manager = ExpertContentManager(db_manager)
        logger.info("Expert content manager initialized successfully")
        return expert_content_manager
    except Exception as e:
        logger.error(f"Error initializing expert content manager: {e}")
        return None

def get_expert_content_manager():
    """Get expert content manager instance"""
    return expert_content_manager