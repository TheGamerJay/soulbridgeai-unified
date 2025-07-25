"""
Real-time Group Therapy System for SoulBridge AI
Live therapy sessions, moderation, AI facilitation, and therapeutic tools
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import asyncio
import threading

logger = logging.getLogger(__name__)

class SessionType(Enum):
    GUIDED_THERAPY = "guided_therapy"
    PEER_SUPPORT = "peer_support"
    MEDITATION = "meditation"
    GRIEF_SUPPORT = "grief_support"
    ANXIETY_SUPPORT = "anxiety_support"
    DEPRESSION_SUPPORT = "depression_support"
    ADDICTION_RECOVERY = "addiction_recovery"
    TRAUMA_HEALING = "trauma_healing"
    MINDFULNESS = "mindfulness"
    CRISIS_SUPPORT = "crisis_support"

class SessionStatus(Enum):
    SCHEDULED = "scheduled"
    STARTING = "starting"
    ACTIVE = "active" 
    BREAK = "break"
    ENDING = "ending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ParticipantRole(Enum):
    FACILITATOR = "facilitator"
    THERAPIST = "therapist"
    PARTICIPANT = "participant"
    OBSERVER = "observer"
    MODERATOR = "moderator"

class MessageType(Enum):
    CHAT = "chat"
    EMOTION_CHECK = "emotion_check"
    BREATHING_EXERCISE = "breathing_exercise"
    AFFIRMATION = "affirmation"
    REFLECTION = "reflection"
    CRISIS_ALERT = "crisis_alert"
    SYSTEM = "system"

@dataclass
class GroupTherapySession:
    """Individual group therapy session"""
    session_id: str
    title: str
    description: str
    session_type: SessionType
    facilitator_id: str
    scheduled_start: datetime
    scheduled_end: datetime
    max_participants: int
    status: SessionStatus
    participants: Dict[str, Dict]
    messages: List[Dict]
    therapeutic_tools: List[str]
    session_notes: str
    created_at: datetime
    is_anonymous: bool = True
    requires_approval: bool = False
    ai_facilitated: bool = False

@dataclass
class TherapeuticActivity:
    """Therapeutic activities for sessions"""
    activity_id: str
    name: str
    description: str
    duration_minutes: int
    instructions: List[str]
    materials_needed: List[str]
    suitable_for: List[SessionType]
    difficulty_level: str

@dataclass
class EmotionCheckIn:
    """Emotional check-in data"""
    user_id: str
    session_id: str
    emotion_before: str
    emotion_after: str
    intensity_before: int  # 1-10 scale
    intensity_after: int
    notes: str
    timestamp: datetime

class GroupTherapySystem:
    """Comprehensive group therapy system with real-time sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_history = deque(maxlen=1000)
        self.scheduled_sessions = {}
        self.therapeutic_activities = {}
        self.user_session_history = defaultdict(list)
        self.emotion_check_ins = defaultdict(list)
        
        # Initialize therapeutic activities
        self._initialize_therapeutic_activities()
        
        # AI facilitator responses
        self.ai_facilitator_prompts = self._initialize_ai_prompts()
        
        # Crisis intervention protocols
        self.crisis_keywords = [
            "suicide", "kill myself", "end it", "can't go on", "hopeless",
            "worthless", "better off dead", "hurt myself", "self harm"
        ]
        
        logger.info("Group Therapy System initialized")
    
    def _initialize_therapeutic_activities(self):
        """Initialize therapeutic activities and exercises"""
        activities = [
            {
                "name": "Mindful Breathing Circle",
                "description": "Guided breathing exercise for group relaxation",
                "duration": 10,
                "instructions": [
                    "Sit comfortably with your back straight",
                    "Close your eyes or soften your gaze",
                    "Breathe in slowly through your nose for 4 counts",
                    "Hold your breath for 4 counts",
                    "Exhale slowly through your mouth for 6 counts",
                    "Repeat this cycle 5 times"
                ],
                "materials": [],
                "suitable_for": [SessionType.ANXIETY_SUPPORT, SessionType.MINDFULNESS],
                "difficulty": "beginner"
            },
            {
                "name": "Gratitude Sharing",
                "description": "Structured gratitude sharing exercise",
                "duration": 15,
                "instructions": [
                    "Each participant shares three things they're grateful for",
                    "Start with 'I am grateful for...'",
                    "Listen actively to others without judgment",
                    "Thank each person after they share"
                ],
                "materials": [],
                "suitable_for": [SessionType.DEPRESSION_SUPPORT, SessionType.PEER_SUPPORT],
                "difficulty": "beginner"
            },
            {
                "name": "Progressive Muscle Relaxation",
                "description": "Guided muscle relaxation technique",
                "duration": 20,
                "instructions": [
                    "Tense your toes for 5 seconds, then relax",
                    "Move up to your calves, thighs, abdomen",
                    "Continue with arms, shoulders, face",
                    "Notice the difference between tension and relaxation",
                    "End with full body relaxation"
                ],
                "materials": ["Comfortable seating"],
                "suitable_for": [SessionType.ANXIETY_SUPPORT, SessionType.TRAUMA_HEALING],
                "difficulty": "intermediate"
            },
            {
                "name": "Emotion Wheel Check-in",
                "description": "Using emotion wheel to identify and share feelings",
                "duration": 12,
                "instructions": [
                    "Look at the emotion wheel displayed",
                    "Identify your current primary emotion",
                    "Find 2-3 secondary emotions",
                    "Share what triggered these emotions",
                    "Listen to others with empathy"
                ],
                "materials": ["Emotion wheel visual"],
                "suitable_for": [SessionType.GUIDED_THERAPY, SessionType.PEER_SUPPORT],
                "difficulty": "intermediate"
            },
            {
                "name": "Safe Space Visualization",
                "description": "Guided visualization for creating inner safety",
                "duration": 15,
                "instructions": [
                    "Close your eyes and take deep breaths",
                    "Imagine a place where you feel completely safe",
                    "Notice the colors, sounds, smells, textures",
                    "Who or what makes this space safe?",
                    "Remember you can return here anytime"
                ],
                "materials": [],
                "suitable_for": [SessionType.TRAUMA_HEALING, SessionType.ANXIETY_SUPPORT],
                "difficulty": "intermediate"
            }
        ]
        
        for activity_data in activities:
            activity = TherapeuticActivity(
                activity_id=str(uuid.uuid4()),
                name=activity_data["name"],
                description=activity_data["description"],
                duration_minutes=activity_data["duration"],
                instructions=activity_data["instructions"],
                materials_needed=activity_data["materials"],
                suitable_for=activity_data["suitable_for"],
                difficulty_level=activity_data["difficulty"]
            )
            self.therapeutic_activities[activity.activity_id] = activity
    
    def _initialize_ai_prompts(self) -> Dict[str, List[str]]:
        """Initialize AI facilitator response templates"""
        return {
            "welcome": [
                "Welcome everyone to our group therapy session. Let's create a safe space together.",
                "Thank you all for being here. Remember, this is a judgment-free zone.",
                "Let's begin by taking a moment to center ourselves and set our intentions."
            ],
            "check_in": [
                "How is everyone feeling right now? Remember, all emotions are valid.",
                "Let's do a quick emotional check-in. What's one word that describes how you're feeling?",
                "Before we begin, let's take a moment to notice what we're bringing into this space."
            ],
            "encouragement": [
                "Thank you for sharing that. Your courage helps create safety for others.",
                "I hear the strength in your vulnerability. That takes real courage.",
                "What you're feeling is completely valid and understandable."
            ],
            "reflection": [
                "What I'm hearing is... Does that resonate with you?",
                "It sounds like you're experiencing... How does that land with you?",
                "I notice some common themes emerging. What do others think?"
            ],
            "crisis_response": [
                "I'm concerned about what you've shared. Your safety is our priority.",
                "Thank you for trusting us with these difficult feelings. You're not alone.",
                "Let's pause and focus on your immediate safety and support."
            ]
        }
    
    def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new group therapy session"""
        session_id = str(uuid.uuid4())
        
        session = GroupTherapySession(
            session_id=session_id,
            title=session_data.get("title", "Group Therapy Session"),
            description=session_data.get("description", ""),
            session_type=SessionType(session_data.get("session_type", "peer_support")),
            facilitator_id=session_data.get("facilitator_id"),
            scheduled_start=datetime.fromisoformat(session_data.get("scheduled_start")),
            scheduled_end=datetime.fromisoformat(session_data.get("scheduled_end")),
            max_participants=session_data.get("max_participants", 8),
            status=SessionStatus.SCHEDULED,
            participants={},
            messages=[],
            therapeutic_tools=session_data.get("therapeutic_tools", []),
            session_notes="",
            created_at=datetime.now(),
            is_anonymous=session_data.get("is_anonymous", True),
            requires_approval=session_data.get("requires_approval", False),
            ai_facilitated=session_data.get("ai_facilitated", False)
        )
        
        self.scheduled_sessions[session_id] = session
        logger.info(f"Created group therapy session: {session_id}")
        return session_id
    
    def join_session(self, session_id: str, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Add user to therapy session"""
        session = self.scheduled_sessions.get(session_id) or self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Check capacity
        if len(session.participants) >= session.max_participants:
            return False
        
        # Check approval requirements
        if session.requires_approval and user_data.get("role") == "participant":
            # In a real implementation, this would queue for approval
            pass
        
        # Add participant
        participant_data = {
            "user_id": user_id,
            "display_name": user_data.get("display_name", f"Anonymous{len(session.participants) + 1}"),
            "role": ParticipantRole(user_data.get("role", "participant")),
            "joined_at": datetime.now(),
            "is_active": True,
            "emotion_check_ins": [],
            "participation_score": 0
        }
        
        session.participants[user_id] = participant_data
        self.user_session_history[user_id].append(session_id)
        
        # Add system message
        self._add_system_message(session, f"{participant_data['display_name']} joined the session")
        
        logger.info(f"User {user_id} joined session {session_id}")
        return True
    
    def start_session(self, session_id: str) -> bool:
        """Start a scheduled therapy session"""
        if session_id not in self.scheduled_sessions:
            return False
        
        session = self.scheduled_sessions.pop(session_id)
        session.status = SessionStatus.ACTIVE
        self.active_sessions[session_id] = session
        
        # Add welcome message
        if session.ai_facilitated:
            welcome_msg = self.ai_facilitator_prompts["welcome"][0]
            self._add_ai_message(session, welcome_msg)
        
        logger.info(f"Started group therapy session: {session_id}")
        return True
    
    def send_message(self, session_id: str, user_id: str, message_data: Dict[str, Any]) -> bool:
        """Send message to therapy session"""
        session = self.active_sessions.get(session_id)
        if not session or user_id not in session.participants:
            return False
        
        # Check for crisis language
        message_content = message_data.get("content", "")
        if self._detect_crisis_language(message_content):
            self._handle_crisis_intervention(session, user_id, message_content)
        
        # Create message
        message = {
            "message_id": str(uuid.uuid4()),
            "user_id": user_id,
            "display_name": session.participants[user_id]["display_name"],
            "content": message_content,
            "message_type": MessageType(message_data.get("message_type", "chat")),
            "timestamp": datetime.now(),
            "reactions": {},
            "is_flagged": False
        }
        
        session.messages.append(message)
        
        # Update participation score
        session.participants[user_id]["participation_score"] += 1
        
        # Generate AI response if AI-facilitated
        if session.ai_facilitated and len(session.messages) % 5 == 0:  # Every 5 messages
            self._generate_ai_response(session)
        
        return True
    
    def start_therapeutic_activity(self, session_id: str, activity_id: str, facilitator_id: str) -> bool:
        """Start a therapeutic activity in the session"""
        session = self.active_sessions.get(session_id)
        activity = self.therapeutic_activities.get(activity_id)
        
        if not session or not activity:
            return False
        
        # Check if user is facilitator
        participant = session.participants.get(facilitator_id)
        if not participant or participant["role"] not in [ParticipantRole.FACILITATOR, ParticipantRole.THERAPIST]:
            return False
        
        # Add activity start message
        activity_msg = {
            "message_id": str(uuid.uuid4()),
            "user_id": "system",
            "display_name": "Therapeutic Guide",
            "content": f"Starting activity: {activity.name}",
            "message_type": MessageType.SYSTEM,
            "timestamp": datetime.now(),
            "activity_data": {
                "activity_id": activity_id,
                "name": activity.name,
                "description": activity.description,
                "duration_minutes": activity.duration_minutes,
                "instructions": activity.instructions
            }
        }
        
        session.messages.append(activity_msg)
        
        # Schedule activity completion
        self._schedule_activity_completion(session_id, activity_id, activity.duration_minutes)
        
        logger.info(f"Started therapeutic activity {activity.name} in session {session_id}")
        return True
    
    def emotion_check_in(self, session_id: str, user_id: str, emotion_data: Dict[str, Any]) -> bool:
        """Record emotional check-in for participant"""
        session = self.active_sessions.get(session_id)
        if not session or user_id not in session.participants:
            return False
        
        check_in = EmotionCheckIn(
            user_id=user_id,
            session_id=session_id,
            emotion_before=emotion_data.get("emotion_before", ""),
            emotion_after=emotion_data.get("emotion_after", ""),
            intensity_before=emotion_data.get("intensity_before", 5),
            intensity_after=emotion_data.get("intensity_after", 5),
            notes=emotion_data.get("notes", ""),
            timestamp=datetime.now()
        )
        
        self.emotion_check_ins[user_id].append(check_in)
        session.participants[user_id]["emotion_check_ins"].append(check_in)
        
        # Add check-in message to session
        check_in_msg = {
            "message_id": str(uuid.uuid4()),
            "user_id": user_id,
            "display_name": session.participants[user_id]["display_name"],
            "content": f"Emotional check-in: {emotion_data.get('emotion_before', 'Unknown')} → {emotion_data.get('emotion_after', 'Unknown')}",
            "message_type": MessageType.EMOTION_CHECK,
            "timestamp": datetime.now(),
            "emotion_data": emotion_data
        }
        
        session.messages.append(check_in_msg)
        logger.info(f"Emotion check-in recorded for user {user_id} in session {session_id}")
        return True
    
    def end_session(self, session_id: str, facilitator_id: str) -> bool:
        """End an active therapy session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        # Check facilitator permissions
        participant = session.participants.get(facilitator_id)
        if not participant or participant["role"] not in [ParticipantRole.FACILITATOR, ParticipantRole.THERAPIST]:
            return False
        
        session.status = SessionStatus.COMPLETED
        
        # Add closing message
        if session.ai_facilitated:
            closing_msg = "Thank you all for participating. Take care of yourselves and remember our shared support."
            self._add_ai_message(session, closing_msg)
        
        # Move to history
        self.session_history.append(session)
        del self.active_sessions[session_id]
        
        logger.info(f"Ended group therapy session: {session_id}")
        return True
    
    def _detect_crisis_language(self, message: str) -> bool:
        """Detect crisis language in messages"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.crisis_keywords)
    
    def _handle_crisis_intervention(self, session: GroupTherapySession, user_id: str, message: str):
        """Handle crisis intervention protocol"""
        # Log crisis alert
        logger.warning(f"CRISIS ALERT in session {session.session_id} from user {user_id}")
        
        # Add crisis response message
        crisis_response = self.ai_facilitator_prompts["crisis_response"][0]
        self._add_ai_message(session, crisis_response, MessageType.CRISIS_ALERT)
        
        # In a real implementation, this would:
        # 1. Alert session moderators
        # 2. Provide crisis resources
        # 3. Potentially pause the session
        # 4. Connect user with crisis counselor
    
    def _add_system_message(self, session: GroupTherapySession, content: str):
        """Add system message to session"""
        message = {
            "message_id": str(uuid.uuid4()),
            "user_id": "system",
            "display_name": "System",
            "content": content,
            "message_type": MessageType.SYSTEM,
            "timestamp": datetime.now()
        }
        session.messages.append(message)
    
    def _add_ai_message(self, session: GroupTherapySession, content: str, 
                       message_type: MessageType = MessageType.CHAT):
        """Add AI facilitator message to session"""
        message = {
            "message_id": str(uuid.uuid4()),
            "user_id": "ai_facilitator",
            "display_name": "AI Facilitator",
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now()
        }
        session.messages.append(message)
    
    def _generate_ai_response(self, session: GroupTherapySession):
        """Generate contextual AI facilitator response"""
        # Simple implementation - would use AI model in production
        recent_messages = session.messages[-5:]
        
        # Check if anyone shared something vulnerable
        has_vulnerability = any("feel" in msg.get("content", "").lower() or 
                              "difficult" in msg.get("content", "").lower() 
                              for msg in recent_messages)
        
        if has_vulnerability:
            response = self.ai_facilitator_prompts["encouragement"][0]
        else:
            response = self.ai_facilitator_prompts["reflection"][0]
        
        self._add_ai_message(session, response)
    
    def _schedule_activity_completion(self, session_id: str, activity_id: str, duration_minutes: int):
        """Schedule activity completion notification"""
        # In a real implementation, this would use a task scheduler
        def complete_activity():
            session = self.active_sessions.get(session_id)
            if session:
                activity = self.therapeutic_activities.get(activity_id)
                if activity:
                    completion_msg = f"Activity '{activity.name}' completed. How did that feel for everyone?"
                    self._add_ai_message(session, completion_msg)
        
        # Simple timer implementation
        timer = threading.Timer(duration_minutes * 60, complete_activity)
        timer.start()
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session information"""
        session = (self.active_sessions.get(session_id) or 
                  self.scheduled_sessions.get(session_id))
        
        if not session:
            return {}
        
        return {
            "session": asdict(session),
            "participant_count": len(session.participants),
            "message_count": len(session.messages),
            "duration_minutes": (datetime.now() - session.created_at).total_seconds() // 60 if session.status == SessionStatus.ACTIVE else 0
        }
    
    def get_user_session_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's session participation history"""
        user_sessions = []
        
        for session_id in self.user_session_history.get(user_id, []):
            # Check active sessions
            session = self.active_sessions.get(session_id)
            if not session:
                # Check completed sessions
                for completed_session in self.session_history:
                    if completed_session.session_id == session_id:
                        session = completed_session
                        break
            
            if session:
                user_sessions.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "session_type": session.session_type.value,
                    "date": session.scheduled_start.isoformat(),
                    "status": session.status.value,
                    "participation_score": session.participants.get(user_id, {}).get("participation_score", 0)
                })
        
        return user_sessions
    
    def get_available_activities(self, session_type: SessionType = None) -> List[Dict[str, Any]]:
        """Get therapeutic activities suitable for session type"""
        activities = []
        
        for activity in self.therapeutic_activities.values():
            if session_type is None or session_type in activity.suitable_for:
                activities.append(asdict(activity))
        
        return activities
    
    def get_emotion_insights(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get emotional insights from check-ins"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        user_check_ins = [
            check_in for check_in in self.emotion_check_ins.get(user_id, [])
            if check_in.timestamp > cutoff_date
        ]
        
        if not user_check_ins:
            return {"message": "No emotion check-ins found"}
        
        # Calculate trends
        emotions_before = [check_in.emotion_before for check_in in user_check_ins]
        emotions_after = [check_in.emotion_after for check_in in user_check_ins]
        intensity_before = [check_in.intensity_before for check_in in user_check_ins]
        intensity_after = [check_in.intensity_after for check_in in user_check_ins]
        
        return {
            "total_check_ins": len(user_check_ins),
            "common_emotions_before": self._get_most_common(emotions_before),
            "common_emotions_after": self._get_most_common(emotions_after),
            "average_intensity_before": sum(intensity_before) / len(intensity_before),
            "average_intensity_after": sum(intensity_after) / len(intensity_after),
            "improvement_trend": sum(intensity_after) / len(intensity_after) - sum(intensity_before) / len(intensity_before)
        }
    
    def _get_most_common(self, items: List[str]) -> Dict[str, int]:
        """Get most common items in list"""
        from collections import Counter
        return dict(Counter(items).most_common(5))
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics for admin view"""
        return {
            "active_sessions": len(self.active_sessions),
            "scheduled_sessions": len(self.scheduled_sessions),
            "completed_sessions": len(self.session_history),
            "total_participants": sum(len(session.participants) for session in self.active_sessions.values()),
            "session_types": {
                session_type.value: sum(1 for session in self.active_sessions.values() 
                                      if session.session_type == session_type)
                for session_type in SessionType
            }
        }