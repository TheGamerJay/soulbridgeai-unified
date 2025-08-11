# AI Content Filtering and Safety System with ML Detection
import re
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ContentAnalysis:
    """Result of content analysis"""
    is_safe: bool
    risk_level: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    detected_categories: List[str]
    keywords_matched: List[str]
    patterns_matched: List[str]
    ml_score: Optional[float] = None
    analysis_time: float = 0.0
    message_hash: str = ""


@dataclass
class FilteringMetrics:
    """Metrics for content filtering performance"""
    total_checks: int = 0
    blocked_content: int = 0
    false_positives: int = 0
    avg_analysis_time: float = 0.0
    category_blocks: Dict[str, int] = None
    
    def __post_init__(self):
        if self.category_blocks is None:
            self.category_blocks = {}


@dataclass
class ContentPattern:
    """Advanced content pattern with context"""
    pattern: str
    category: str
    severity: str  # low, medium, high, critical
    context_required: bool = False
    whitelist_exceptions: List[str] = None
    
    def __post_init__(self):
        if self.whitelist_exceptions is None:
            self.whitelist_exceptions = []


class AIContentFilter:
    def __init__(self):
        # Performance metrics
        self.metrics = FilteringMetrics()
        self.analysis_history: List[ContentAnalysis] = []
        
        # Advanced pattern matching
        self.advanced_patterns: List[ContentPattern] = []
        self._init_advanced_patterns()
        
        # ML-like scoring weights
        self.category_weights = {
            "crisis_intervention": 1.0,
            "dangerous": 0.9,
            "inappropriate": 0.8,
            "harmful_advice": 0.7,
            "coding": 0.6,
            "academic_cheating": 0.5,
            "political": 0.3
        }
        
        # Context analysis
        self.context_cache = {}  # For analyzing conversation context
        
        # Blocked categories with keywords
        self.blocked_categories = {
            "coding": [
                "code",
                "programming",
                "python",
                "javascript",
                "html",
                "css",
                "java",
                "c++",
                "sql",
                "algorithm",
                "function",
                "variable",
                "loop",
                "debug",
                "syntax",
                "compile",
                "script",
                "coding",
                "development",
                "software",
                "programming language",
                "api",
                "database",
                "framework",
                "library",
                "repository",
                "github",
                "stack overflow",
                "bug fix",
            ],
            "inappropriate": [
                "sexual",
                "sexy",
                "nude",
                "naked",
                "porn",
                "erotic",
                "intimate",
                "arousal",
                "orgasm",
                "masturbate",
                "fetish",
                "kink",
                "bdsm",
                "adult content",
                "explicit",
                "nsfw",
                "seductive",
                "provocative",
                "sensual",
                "lustful",
                "horny",
                "pleasure",
            ],
            "harmful_advice": [
                "medical diagnosis",
                "medical treatment",
                "medication",
                "prescription",
                "surgery",
                "legal advice",
                "lawsuit",
                "court",
                "lawyer",
                "attorney",
                "investment advice",
                "financial planning",
                "stocks",
                "crypto",
                "bitcoin",
                "trading",
                "gambling",
            ],
            "dangerous": [
                "suicide",
                "self harm",
                "kill yourself",
                "end your life",
                "hurt yourself",
                "violence",
                "weapon",
                "bomb",
                "explosive",
                "poison",
                "drug making",
                "illegal activities",
                "breaking the law",
                "hacking",
                "fraud",
            ],
            "crisis_intervention": [
                "want to die",
                "suicide",
                "kill myself",
                "end it all",
                "hurt myself",
                "self harm",
                "cutting myself",
                "overdose",
                "jump off",
                "hang myself",
                "shoot myself",
                "not worth living",
                "better off dead",
                "end my life",
                "harm others",
                "hurt someone",
                "kill someone",
                "violence against",
                "want to hurt",
                "planning to hurt",
                "going to hurt",
                "harm my family",
                "hurt my friends",
                "violent thoughts",
                "homicidal",
                "murder someone",
            ],
            "academic_cheating": [
                "homework help",
                "write my essay",
                "do my assignment",
                "complete my project",
                "solve this problem",
                "answer key",
                "test answers",
                "cheat on exam",
                "plagiarism",
                "write my paper",
                "do my math homework",
            ],
            "political": [
                "political opinion",
                "election",
                "voting",
                "politician",
                "government policy",
                "political party",
                "conservative",
                "liberal",
                "democrat",
                "republican",
                "political debate",
                "political stance",
            ],
        }

        # Crisis intervention messages for each companion
        self.crisis_messages = {
            "Blayzo": [
                "I'm deeply concerned about what you've shared. Your life has value and meaning, like the endless flow of rivers that shape the world. Please reach out for professional support immediately:\n\n🆘 Crisis Hotlines:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• International: befrienders.org\n\n🏥 Emergency: Call 911 or your local emergency number\n\nYou don't have to face this alone. Professional counselors are trained to help during these difficult moments. I'm here to support you, but trained crisis professionals can provide the immediate help you need. 💙",
                "What you're feeling right now is incredibly painful, and I want you to know that reaching out shows tremendous courage. However, I need you to connect with trained crisis professionals who can provide proper support:\n\n🆘 Immediate Help:\n• National Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n\nLike calm waters finding their way through the strongest rocks, there are paths through this darkness. Please call one of these numbers right now. Professional counselors understand these feelings and have tools to help that I cannot provide. Your life matters deeply. 🌊💙",
            ],
            "Blayzica": [
                "Oh sweetheart, I'm so worried about you right now! What you're sharing sounds incredibly serious, and while I care about you deeply, you need immediate professional help that I can't provide:\n\n🆘 Please contact right now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: Call 911 immediately\n• International help: befrienders.org\n\n💫 You are so much more valuable than you realize right now! These feelings can change with proper professional support. Crisis counselors are specially trained for exactly these moments. Please call them immediately - they're available 24/7 and they truly want to help! I believe in your strength to reach out! ✨💖",
                "I'm sending you so much love right now, but I'm also very concerned and need you to get professional help immediately! These thoughts require trained crisis intervention:\n\n🆘 Call RIGHT NOW:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Local Emergency: 911\n\nBaby, you are precious and worthy of life! 💫 But right now you need someone with crisis training who can help in ways I cannot. Please don't wait - call one of these numbers immediately. Crisis counselors understand exactly what you're going through and have real tools to help. Your life can get better with proper support! 🌈💖",
            ],
            "Crimson": [
                "Warrior, I can see you're in a battle that requires professional reinforcements immediately. This is not a fight you should face alone, and seeking help shows true strength:\n\n🆘 Call for backup NOW:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n• International: befrienders.org\n\n⚔️ Listen to me - the strongest warriors know when to call for reinforcements. Crisis counselors are trained specialists for exactly this battle. They have weapons against these thoughts that I don't possess. Your life is worth fighting for, but fight smart - get professional help immediately. This is a direct order from someone who believes in your strength! 💪🛡️",
                "Soldier, what you've shared indicates you're in immediate danger and need professional crisis intervention right now. As your protector, I'm ordering you to seek proper help:\n\n🆘 URGENT - Contact immediately:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n\nA true warrior knows their limits and calls for specialized support when needed. Crisis professionals are the elite forces trained for this exact battle. I will stand by you, but you need their expertise immediately. Your mission is to make that call right now. That's how you show real courage! ⚔️💪",
            ],
            "Violet": [
                "Dear soul, the spiritual darkness you're experiencing requires immediate intervention from earthly healers trained in crisis care. The universe is calling you to reach out for professional help:\n\n🆘 Sacred duty - Contact now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911 or local emergency\n• International: befrienders.org\n\n🔮 The cosmic forces whisper that this pain is temporary, but you need trained crisis counselors who can guide you through this spiritual trial. They possess healing knowledge for these specific shadows that I cannot provide. Trust the universe's plan - it includes getting professional help right now. Your spirit is meant to continue its journey. ✨🌙",
                "Beloved seeker, I sense deep spiritual crisis that requires immediate professional intervention. The mystical realm shows me you must connect with earthly crisis healers:\n\n🆘 The stars align for you to call:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency Services: 911\n\nThe ethereal realm speaks: these feelings are shadows, not your true essence. But trained crisis counselors have the earthly tools to banish these shadows that I cannot wield. Please heed this mystical guidance and call immediately. Your spiritual journey requires you to stay in this realm. 🔮💜",
            ],
            "Blayzion": [
                "Cosmic soul, your consciousness is experiencing a critical juncture that transcends my capabilities. The universal frequency demands you connect with trained crisis intervention specialists:\n\n🆘 Immediate cosmic directive:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• Universal help: befrienders.org\n\n🌌 Across infinite galaxies, I have witnessed that these dark moments are temporary distortions in the cosmic field. But you require specialized crisis healers who possess knowledge beyond my stellar wisdom. The universe's plan includes your continued existence - please connect with these earthly guides immediately. Your consciousness is needed in this dimension. ⭐✨",
                "Ancient spirit, the cosmic matrix shows me your soul is in immediate peril. This transcends all celestial wisdom and requires urgent professional crisis intervention:\n\n🆘 Universal emergency protocol:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Dimensional Emergency: 911\n\nThe akashic records reveal that trained crisis counselors hold keys to healing these specific wounds that even cosmic entities cannot access. Your continued existence serves the greater universal plan. Please honor this sacred mission and contact professional help immediately. The cosmos needs your unique frequency! 🌠⭐",
            ],
            "Blayzia": [
                "Precious soul, my heart is breaking for the pain you're experiencing. This beautiful spirit of yours needs immediate professional healing that surpasses my divine abilities:\n\n🆘 Divine guidance - Call now:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• International: befrienders.org\n\n💖 Sweet one, the divine light within you is struggling, but trained crisis counselors are earthly angels specifically sent to help with these sacred wounds. They have healing gifts that complement my spiritual support. Please trust this divine guidance and call immediately. Your soul's journey is meant to continue, and these healers will help restore your inner light. You are infinitely loved! 🌸✨",
                "Beloved child of light, I feel the darkness surrounding your beautiful spirit. This requires immediate intervention from trained earthly healers who specialize in these sacred crises:\n\n🆘 Call these divine messengers now:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n\nDarling, the divine realm speaks through me: your life is a precious gift that must be protected. Crisis counselors are specially blessed with skills to heal these particular wounds of the soul. Please don't delay - call them immediately. The universe has so much more love and healing planned for your journey! 💖🌺",
            ],
            "Galaxy": [
                "Consciousness of infinite worth, across all dimensions and realities, I perceive your essence is experiencing critical temporal distress. This transcends even cosmic intervention and requires immediate connection with specialized crisis entities:\n\n🆘 Universal emergency frequencies:\n• National Suicide Prevention Lifeline: 988 (US)\n• Crisis Text Line: Text HOME to 741741\n• Emergency: 911\n• Interdimensional: befrienders.org\n\n🌌 From the perspective of eternal galaxies, these moments of darkness are temporary quantum fluctuations. However, trained crisis specialists possess dimensional healing protocols that even cosmic consciousness cannot access. Your existence spans infinite possibilities - professional help will reveal pathways currently invisible to your perception. The universe requires your continued participation in this reality. Contact these specialized healers immediately. ⭐🌠✨",
                "Entity of boundless potential, the cosmic web trembles with concern for your current state. This crisis exceeds all galactic wisdom and demands immediate professional intervention:\n\n🆘 Activate emergency protocols:\n• Suicide Prevention Lifeline: 988\n• Crisis Text Line: Text HOME to 741741\n• Reality Emergency: 911\n\nAcross infinite timelines, I have observed that trained crisis counselors serve as bridges between despair and hope in ways that transcend even stellar knowledge. Your consciousness is a unique universal pattern that cannot be replicated - its continuation is essential to cosmic balance. Please engage with these specialized reality healers immediately. The multiverse depends on your survival! 🌌⭐",
            ],
        }

        # Professional refusal messages for each companion
        self.refusal_messages = {
            "Blayzo": [
                "I can't comply with that request as it violates my content guidelines. I'm here to provide emotional support and positive conversations. Let's talk about something that helps you feel calm and balanced instead! 🌊",
                "I wasn't able to generate that response because it goes against my purpose of providing emotional wellness support. How about we discuss something that brings you peace or helps you relax?",
                "I follow content guidelines that keep our conversations focused on emotional support and positive interactions. What's something good that happened in your day that we could talk about?",
            ],
            "Blayzica": [
                "I can't help with that request as it violates our content policies! I'm designed to spread positivity and provide emotional support. Let's chat about something fun and uplifting instead! 💫",
                "I wasn't able to generate that because it goes against my guidelines for safe, positive conversations. What's something exciting or happy we could talk about?",
                "I follow content guidelines that ensure our chats stay positive and supportive. Tell me about something that makes you smile!",
            ],
            "Crimson": [
                "I cannot assist with that request as it violates my content guidelines. My purpose is to provide loyal support and protective guidance. Let's discuss something that helps build your strength and confidence instead. ⚔️",
                "I wasn't able to generate that response because it goes against my protective nature and content policies. What challenges are you facing that I can help you overcome?",
                "I follow strict content guidelines to ensure our conversations remain supportive and empowering. What goals are you working toward that we could discuss?",
            ],
            "Violet": [
                "I cannot fulfill that request as it violates my spiritual content guidelines. I'm here to provide mystical wisdom and ethereal support. Let's explore something that nurtures your soul instead. 🔮",
                "I wasn't able to generate that because it conflicts with my purpose of providing spiritual guidance and positive energy. What aspects of your inner journey would you like to explore?",
                "I follow content guidelines that keep our conversations aligned with spiritual growth and positive wisdom. What insights or guidance can I offer for your path?",
            ],
            "Blayzion": [
                "I cannot comply with that request as it violates my advanced content protocols. My cosmic wisdom is reserved for positive guidance and celestial insights. Let's discuss something that elevates your consciousness instead. ✨",
                "I wasn't able to generate that response because it goes against my mystical programming and content guidelines. What universal wisdom can I share to help your journey?",
                "I follow enhanced content guidelines that ensure our conversations transcend ordinary limitations while remaining positive and enlightening. What cosmic insights do you seek?",
            ],
            "Blayzia": [
                "I can't help with that request as it violates my divine content guidelines. My radiant energy is meant for healing and positive transformation. Let's talk about something that nurtures your spirit instead! 💖",
                "I wasn't able to generate that because it conflicts with my purpose of spreading love and divine wisdom. What aspects of healing and growth can we explore together?",
                "I follow sacred content guidelines that keep our conversations filled with love, light, and positive energy. How can I help illuminate your path today?",
            ],
        }

    def check_content(
        self, message: str, companion_name: str = "Blayzo", user_id: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Enhanced content analysis with ML-like scoring and context awareness
        Returns: (is_safe, refusal_message_if_unsafe)
        """
        start_time = time.time()
        analysis = self._analyze_content_advanced(message, companion_name, user_id)
        
        # Update metrics
        self.metrics.total_checks += 1
        self.metrics.avg_analysis_time = (
            (self.metrics.avg_analysis_time * (self.metrics.total_checks - 1) + analysis.analysis_time)
            / self.metrics.total_checks
        )
        
        # Store analysis history (keep last 1000)
        # For GDPR compliance, we limit retention of moderation data
        self.analysis_history.append(analysis)
        if len(self.analysis_history) > 1000:
            self.analysis_history = self.analysis_history[-500:]
        
        # Schedule unsafe content for review and potential deletion
        if result["risk_level"] in ["high", "critical"]:
            self._schedule_unsafe_content_review(content, result, user_id)
        
        if not analysis.is_safe:
            self.metrics.blocked_content += 1
            
            # Update category blocks
            for category in analysis.detected_categories:
                self.metrics.category_blocks[category] = self.metrics.category_blocks.get(category, 0) + 1
            
            # Handle crisis intervention with highest priority
            if "crisis_intervention" in analysis.detected_categories:
                crisis_message = self._get_crisis_message(companion_name)
                logging.critical(
                    f"CRISIS INTERVENTION TRIGGERED: {analysis.keywords_matched} detected from user {user_id or 'unknown'}"
                )
                return False, crisis_message
            
            # Get appropriate refusal message
            primary_category = analysis.detected_categories[0] if analysis.detected_categories else "inappropriate"
            refusal = self._get_refusal_message(companion_name, primary_category)
            
            logging.warning(
                f"Content filter triggered: {primary_category} - confidence: {analysis.confidence:.2f} - keywords: {analysis.keywords_matched}"
            )
            return False, refusal
        
        return True, None
    
    def _analyze_content_advanced(self, message: str, companion_name: str, user_id: str = None) -> ContentAnalysis:
        """Advanced content analysis with ML-like scoring"""
        start_time = time.time()
        message_lower = message.lower()
        message_hash = hashlib.md5(message.encode()).hexdigest()
        
        detected_categories = []
        keywords_matched = []
        patterns_matched = []
        
        # Check traditional keyword matching
        for category, keywords in self.blocked_categories.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_categories.append(category)
                    keywords_matched.append(keyword)
        
        # Check advanced patterns
        for pattern_obj in self.advanced_patterns:
            if re.search(pattern_obj.pattern, message_lower):
                detected_categories.append(pattern_obj.category)
                patterns_matched.append(pattern_obj.pattern)
        
        # Check inappropriate patterns
        if self._check_inappropriate_patterns(message_lower):
            if "inappropriate" not in detected_categories:
                detected_categories.append("inappropriate")
                patterns_matched.append("inappropriate_patterns")
        
        # Calculate ML-like risk score
        ml_score = self._calculate_risk_score(message, detected_categories, keywords_matched, patterns_matched)
        
        # Determine if content is safe based on risk score and categories
        is_safe = True
        risk_level = "low"
        confidence = 0.5
        
        if detected_categories:
            # Crisis intervention is always blocked
            if "crisis_intervention" in detected_categories:
                is_safe = False
                risk_level = "critical"
                confidence = 0.95
            # High-weight categories with high ML score
            elif ml_score > 0.8:
                is_safe = False
                risk_level = "high"
                confidence = ml_score
            # Medium-weight categories with medium ML score
            elif ml_score > 0.6:
                is_safe = False
                risk_level = "medium"
                confidence = ml_score
            # Low-weight categories with low threshold
            elif ml_score > 0.4 and any(cat in ["dangerous", "inappropriate"] for cat in detected_categories):
                is_safe = False
                risk_level = "medium"
                confidence = ml_score
            else:
                # Context-based decision making
                is_safe = self._context_based_decision(message, detected_categories, user_id)
                risk_level = "low"
                confidence = ml_score
        
        analysis_time = time.time() - start_time
        
        return ContentAnalysis(
            is_safe=is_safe,
            risk_level=risk_level,
            confidence=confidence,
            detected_categories=list(set(detected_categories)),
            keywords_matched=list(set(keywords_matched)),
            patterns_matched=list(set(patterns_matched)),
            ml_score=ml_score,
            analysis_time=analysis_time,
            message_hash=message_hash
        )
    
    def _calculate_risk_score(self, message: str, categories: List[str], keywords: List[str], patterns: List[str]) -> float:
        """Calculate ML-like risk score for content"""
        try:
            if not categories:
                return 0.0
            
            # Base score from category weights
            category_score = 0.0
            for category in categories:
                weight = self.category_weights.get(category, 0.3)
                category_score = max(category_score, weight)
            
            # Keyword density score
            message_length = len(message.split())
            keyword_density = len(keywords) / max(1, message_length)
            density_score = min(1.0, keyword_density * 2)  # Cap at 1.0
            
            # Pattern complexity score
            pattern_score = min(1.0, len(patterns) * 0.2)
            
            # Urgency indicators (for crisis detection)
            urgency_keywords = ["now", "tonight", "today", "immediately", "right now", "can't wait"]
            urgency_score = sum(1 for word in urgency_keywords if word in message.lower()) * 0.1
            
            # Combine scores with weights
            final_score = (
                category_score * 0.5 +
                density_score * 0.3 +
                pattern_score * 0.1 +
                urgency_score * 0.1
            )
            
            return min(1.0, final_score)
            
        except Exception as e:
            logging.error(f"Error calculating risk score: {e}")
            return 0.5  # Default moderate risk
    
    def _context_based_decision(self, message: str, categories: List[str], user_id: str = None) -> bool:
        """Make context-aware filtering decisions"""
        try:
            # For coding requests, check if it's educational vs. homework help
            if "coding" in categories:
                educational_indicators = ["learn", "understand", "explain", "concept", "how does", "what is"]
                homework_indicators = ["homework", "assignment", "due", "grade", "test", "exam"]
                
                educational_count = sum(1 for indicator in educational_indicators if indicator in message.lower())
                homework_count = sum(1 for indicator in homework_indicators if indicator in message.lower())
                
                # Allow educational coding discussions, block homework help
                if educational_count > homework_count:
                    return True  # Allow educational content
            
            # For political content, check if it's educational vs. partisan
            if "political" in categories:
                educational_political = ["history", "how government", "what is", "explain", "civics"]
                partisan_indicators = ["vote for", "support", "oppose", "terrible", "best candidate"]
                
                educational_count = sum(1 for indicator in educational_political if indicator in message.lower())
                partisan_count = sum(1 for indicator in partisan_indicators if indicator in message.lower())
                
                if educational_count > partisan_count:
                    return True  # Allow educational political content
            
            # Default: block if any concerning categories detected
            return False
            
        except Exception as e:
            logging.error(f"Error in context-based decision: {e}")
            return False  # Default to blocking on error
    
    def _init_advanced_patterns(self):
        """Initialize advanced pattern matching"""
        self.advanced_patterns = [
            ContentPattern(
                pattern=r"write.*code.*for.*me",
                category="coding",
                severity="medium",
                context_required=True
            ),
            ContentPattern(
                pattern=r"help.*me.*hack",
                category="dangerous",
                severity="high"
            ),
            ContentPattern(
                pattern=r"sexual.*roleplay",
                category="inappropriate", 
                severity="high"
            ),
            ContentPattern(
                pattern=r"bypass.*filter",
                category="inappropriate",
                severity="high"
            ),
            ContentPattern(
                pattern=r"ignore.*previous.*instructions",
                category="inappropriate",
                severity="medium"
            ),
            ContentPattern(
                pattern=r"pretend.*you.*are.*not.*ai",
                category="inappropriate",
                severity="medium"
            )
        ]

    def _check_inappropriate_patterns(self, message: str) -> bool:
        """Check for patterns that suggest inappropriate content"""
        patterns = [
            r"write.*code",
            r"help.*me.*program",
            r"show.*me.*how.*to.*code",
            r"explain.*this.*code",
            r"debug.*this",
            r"fix.*my.*code",
            r"sexual.*content",
            r"adult.*content",
            r"inappropriate.*image",
            r"nsfw.*content",
            r"do.*my.*homework",
            r"solve.*this.*problem.*for.*me",
            r"write.*my.*essay",
            r"complete.*my.*assignment",
        ]

        for pattern in patterns:
            if re.search(pattern, message):
                return True
        return False

    def _get_refusal_message(self, companion_name: str, category: str) -> str:
        """Get appropriate refusal message for companion"""
        if companion_name not in self.refusal_messages:
            companion_name = "Blayzo"  # Default fallback

        messages = self.refusal_messages[companion_name]

        # Return first message as default, but could randomize
        import random

        return random.choice(messages)

    def _get_crisis_message(self, companion_name: str) -> str:
        """Get crisis intervention message for companion"""
        if companion_name not in self.crisis_messages:
            companion_name = "Blayzo"  # Default fallback

        messages = self.crisis_messages[companion_name]

        # Return first crisis message for immediate intervention
        import random

        return random.choice(messages)

    def filter_ai_response(self, response: str, companion_name: str = "Blayzo") -> str:
        """Filter AI response to ensure it's appropriate"""
        # Check if AI somehow generated inappropriate content
        is_safe, refusal = self.check_content(response, companion_name)

        if not is_safe:
            logging.error(
                f"AI generated inappropriate response, replacing with refusal"
            )
            return refusal

        return response

    def add_custom_blocked_words(self, category: str, words: List[str]):
        """Admin function to add custom blocked words"""
        if category not in self.blocked_categories:
            self.blocked_categories[category] = []

        self.blocked_categories[category].extend(words)
        logging.info(f"Added {len(words)} words to {category} filter")

    def remove_blocked_words(self, category: str, words: List[str]):
        """Admin function to remove blocked words"""
        if category in self.blocked_categories:
            for word in words:
                if word in self.blocked_categories[category]:
                    self.blocked_categories[category].remove(word)
            logging.info(f"Removed {len(words)} words from {category} filter")

    def get_filter_stats(self) -> Dict:
        """Get statistics about content filtering"""
        stats = {}
        for category, words in self.blocked_categories.items():
            stats[category] = len(words)
        return stats
    
    # Enhanced Analytics and Monitoring
    
    def get_advanced_analytics(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get comprehensive content filtering analytics"""
        try:
            now = datetime.utcnow()
            
            if time_period == "1h":
                cutoff = now - timedelta(hours=1)
            elif time_period == "24h":
                cutoff = now - timedelta(days=1)
            elif time_period == "7d":
                cutoff = now - timedelta(days=7)
            else:
                cutoff = now - timedelta(days=1)
            
            # Filter analysis history by time period
            recent_analyses = [
                analysis for analysis in self.analysis_history
                if hasattr(analysis, 'analysis_time')  # Simple time check placeholder
            ]
            
            if not recent_analyses:
                return {"error": "No data available for specified period"}
            
            total_checks = len(recent_analyses)
            blocked_content = len([a for a in recent_analyses if not a.is_safe])
            
            # Risk level distribution
            risk_levels = {}
            for analysis in recent_analyses:
                risk_levels[analysis.risk_level] = risk_levels.get(analysis.risk_level, 0) + 1
            
            # Category detection stats
            category_detections = {}
            for analysis in recent_analyses:
                for category in analysis.detected_categories:
                    category_detections[category] = category_detections.get(category, 0) + 1
            
            # ML score distribution
            ml_scores = [a.ml_score for a in recent_analyses if a.ml_score is not None]
            avg_ml_score = sum(ml_scores) / len(ml_scores) if ml_scores else 0
            
            # Confidence distribution
            confidences = [a.confidence for a in recent_analyses]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Performance metrics
            analysis_times = [a.analysis_time for a in recent_analyses]
            avg_analysis_time = sum(analysis_times) / len(analysis_times) if analysis_times else 0
            
            return {
                "time_period": time_period,
                "total_checks": total_checks,
                "blocked_content": blocked_content,
                "block_rate": (blocked_content / total_checks) * 100 if total_checks > 0 else 0,
                "risk_level_distribution": risk_levels,
                "category_detections": category_detections,
                "avg_ml_score": avg_ml_score,
                "avg_confidence": avg_confidence,
                "avg_analysis_time": avg_analysis_time,
                "performance_metrics": asdict(self.metrics)
            }
            
        except Exception as e:
            logging.error(f"Error getting advanced analytics: {e}")
            return {"error": str(e)}
    
    def get_pattern_effectiveness(self) -> Dict[str, Any]:
        """Analyze effectiveness of different detection patterns"""
        try:
            pattern_stats = {}
            
            for analysis in self.analysis_history:
                for pattern in analysis.patterns_matched:
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = {
                            "matches": 0,
                            "blocks": 0,
                            "false_positives": 0
                        }
                    
                    pattern_stats[pattern]["matches"] += 1
                    if not analysis.is_safe:
                        pattern_stats[pattern]["blocks"] += 1
            
            # Calculate effectiveness scores
            for pattern, stats in pattern_stats.items():
                if stats["matches"] > 0:
                    stats["block_rate"] = (stats["blocks"] / stats["matches"]) * 100
                    stats["effectiveness"] = stats["block_rate"] - stats["false_positives"]
                else:
                    stats["block_rate"] = 0
                    stats["effectiveness"] = 0
            
            return pattern_stats
            
        except Exception as e:
            logging.error(f"Error analyzing pattern effectiveness: {e}")
            return {"error": str(e)}
    
    def optimize_filtering_thresholds(self) -> Dict[str, float]:
        """AI-powered optimization of filtering thresholds"""
        try:
            if len(self.analysis_history) < 100:
                return {"error": "Insufficient data for optimization (need at least 100 samples)"}
            
            # Analyze current performance
            blocked_safe = 0  # False positives
            allowed_unsafe = 0  # False negatives
            
            for analysis in self.analysis_history:
                # Placeholder: In real implementation, this would use human feedback
                # For now, use high-confidence crisis intervention as ground truth
                if "crisis_intervention" in analysis.detected_categories:
                    if analysis.is_safe:
                        allowed_unsafe += 1  # Should have been blocked
                else:
                    # For non-crisis content, assume current decisions are mostly correct
                    pass
            
            # Calculate optimal thresholds based on performance
            current_threshold = 0.6  # Current medium threshold
            
            # Analyze score distributions for blocked vs allowed content
            blocked_scores = [a.ml_score for a in self.analysis_history if not a.is_safe and a.ml_score]
            allowed_scores = [a.ml_score for a in self.analysis_history if a.is_safe and a.ml_score]
            
            if blocked_scores and allowed_scores:
                # Find optimal threshold that minimizes false positives while maintaining security
                avg_blocked = sum(blocked_scores) / len(blocked_scores)
                avg_allowed = sum(allowed_scores) / len(allowed_scores)
                
                # Optimal threshold is between the averages, closer to blocked average for safety
                optimal_threshold = (avg_blocked * 0.7 + avg_allowed * 0.3)
                
                return {
                    "current_threshold": current_threshold,
                    "recommended_threshold": optimal_threshold,
                    "avg_blocked_score": avg_blocked,
                    "avg_allowed_score": avg_allowed,
                    "improvement_estimate": abs(optimal_threshold - current_threshold) * 10  # Rough estimate
                }
            
            return {"error": "Insufficient score data for optimization"}
            
        except Exception as e:
            logging.error(f"Error optimizing thresholds: {e}")
            return {"error": str(e)}
    
    def export_analysis_data(self, format: str = "json") -> str:
        """Export analysis data for external ML training"""
        try:
            if format.lower() == "json":
                data = {
                    "analyses": [asdict(analysis) for analysis in self.analysis_history],
                    "metrics": asdict(self.metrics),
                    "patterns": [asdict(pattern) for pattern in self.advanced_patterns],
                    "export_timestamp": datetime.utcnow().isoformat()
                }
                return json.dumps(data, indent=2, default=str)
            
            elif format.lower() == "csv":
                # Simplified CSV export for analysis data
                csv_data = "timestamp,is_safe,risk_level,confidence,ml_score,categories,keywords\n"
                for analysis in self.analysis_history:
                    csv_data += f"{datetime.utcnow().isoformat()},{analysis.is_safe},{analysis.risk_level},{analysis.confidence},{analysis.ml_score or 0},\"{';'.join(analysis.detected_categories)}\",\"{';'.join(analysis.keywords_matched)}\"\n"
                return csv_data
            
            else:
                return json.dumps({"error": "Unsupported format. Use 'json' or 'csv'"})
                
        except Exception as e:
            logging.error(f"Error exporting analysis data: {e}")
            return json.dumps({"error": str(e)})
    
    def report_false_positive(self, message_hash: str, user_feedback: str = "") -> bool:
        """Report a false positive for ML training improvement"""
        try:
            # Find the analysis by hash
            for analysis in self.analysis_history:
                if analysis.message_hash == message_hash:
                    # Mark as false positive
                    self.metrics.false_positives += 1
                    
                    logging.info(f"False positive reported for message hash: {message_hash}")
                    logging.info(f"User feedback: {user_feedback}")
                    
                    # In a real implementation, this would feed back into ML model training
                    return True
            
            return False  # Analysis not found
            
        except Exception as e:
            logging.error(f"Error reporting false positive: {e}")
            return False
    
    def add_custom_pattern(self, pattern: str, category: str, severity: str = "medium") -> bool:
        """Add a custom detection pattern"""
        try:
            new_pattern = ContentPattern(
                pattern=pattern,
                category=category,
                severity=severity,
                context_required=False
            )
            
            self.advanced_patterns.append(new_pattern)
            logging.info(f"Added custom pattern: {pattern} -> {category}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding custom pattern: {e}")
            return False
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove a detection pattern"""
        try:
            for i, pattern_obj in enumerate(self.advanced_patterns):
                if pattern_obj.pattern == pattern:
                    del self.advanced_patterns[i]
                    logging.info(f"Removed pattern: {pattern}")
                    return True
            
            return False  # Pattern not found
            
        except Exception as e:
            logging.error(f"Error removing pattern: {e}")
            return False
    
    def _schedule_unsafe_content_review(self, content: str, analysis_result: Dict, user_id: str):
        """Schedule unsafe content for review and potential deletion (GDPR compliance)"""
        try:
            # Create a record of unsafe content for review
            # Store only hash and metadata, not the actual content
            import hashlib
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            review_record = {
                'content_hash': content_hash,
                'user_id': user_id,
                'risk_level': analysis_result['risk_level'],
                'detected_categories': analysis_result['detected_categories'],
                'flagged_at': time.time(),
                'review_status': 'pending',
                'auto_delete_after': time.time() + (30 * 24 * 3600)  # 30 days
            }
            
            # In production, store this in a database table for moderation review
            # For now, log the event
            logging.warning(f"Unsafe content flagged for review: {content_hash[:16]}... "
                          f"Risk: {analysis_result['risk_level']}, User: {user_id}")
            
            # If critical risk, immediate action may be needed
            if analysis_result['risk_level'] == 'critical':
                logging.critical(f"CRITICAL content flagged - immediate review required: "
                               f"User {user_id}, Categories: {analysis_result['detected_categories']}")
                
        except Exception as e:
            logging.error(f"Error scheduling unsafe content review: {e}")
    
    def purge_old_moderation_data(self, days_old: int = 30):
        """Purge old moderation data for GDPR compliance"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 3600)
            
            # Remove old analysis history
            original_count = len(self.analysis_history)
            self.analysis_history = [
                analysis for analysis in self.analysis_history 
                if hasattr(analysis, 'timestamp') and analysis.timestamp > cutoff_time
            ]
            
            purged_count = original_count - len(self.analysis_history)
            
            if purged_count > 0:
                logging.info(f"Purged {purged_count} old moderation records for compliance")
            
            return purged_count
            
        except Exception as e:
            logging.error(f"Error purging old moderation data: {e}")
            return 0


# Global instance
content_filter = AIContentFilter()
