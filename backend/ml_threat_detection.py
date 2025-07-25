"""
ML-Based Advanced Threat Detection System for SoulBridge AI
Uses machine learning for behavioral analysis, anomaly detection, and predictive threat modeling
"""
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import hashlib
import re
import ipaddress

# Try to import ML libraries, fall back to basic detection if not available
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML libraries not available, using rule-based detection only")

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = {"score": 1, "color": "#4CAF50", "action": "log"}
    MEDIUM = {"score": 2, "color": "#FF9800", "action": "alert"}
    HIGH = {"score": 3, "color": "#F44336", "action": "block"}
    CRITICAL = {"score": 4, "color": "#9C27B0", "action": "ban"}

class ThreatType(Enum):
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    BRUTE_FORCE = "brute_force" 
    BOT_ACTIVITY = "bot_activity"
    CONTENT_ABUSE = "content_abuse"
    CREDENTIAL_STUFFING = "credential_stuffing"
    DDoS = "ddos"
    SCRAPING = "scraping"
    SOCIAL_ENGINEERING = "social_engineering"
    SPAM = "spam"
    SUSPICIOUS_PATTERN = "suspicious_pattern"

@dataclass
class ThreatEvent:
    """Individual threat detection event"""
    event_id: str
    ip_address: str
    user_id: Optional[str]
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence_score: float
    evidence: Dict[str, Any]
    timestamp: datetime
    features: Dict[str, float]
    ml_prediction: Optional[Dict] = None

@dataclass
class UserBehaviorProfile:
    """User behavioral profile for anomaly detection"""
    user_id: str
    session_patterns: Dict[str, List[float]]
    request_patterns: Dict[str, List[float]]
    content_patterns: Dict[str, List[float]]
    temporal_patterns: Dict[str, List[float]]
    location_patterns: List[str]
    device_patterns: List[str]
    last_updated: datetime

class MLThreatDetector:
    """Advanced ML-based threat detection system"""
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
        self.threat_events = deque(maxlen=10000)
        self.user_profiles = {}
        self.ip_reputation = defaultdict(lambda: {"score": 0, "events": []})
        self.models = {}
        self.feature_scalers = {}
        
        # Behavioral baseline models
        if self.ml_available:
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.threat_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.cluster_analyzer = DBSCAN(eps=0.5, min_samples=5)
            
        # Pattern databases
        self.known_attack_patterns = self._load_attack_patterns()
        self.bot_signatures = self._load_bot_signatures()
        
        # Real-time feature tracking
        self.request_windows = defaultdict(lambda: deque(maxlen=100))
        self.session_metrics = defaultdict(dict)
        
        logger.info("ML Threat Detection System initialized")
    
    def _load_attack_patterns(self) -> Dict[str, List[str]]:
        """Load known attack patterns and signatures"""
        return {
            "sql_injection": [
                r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
                r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
                r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>"
            ],
            "directory_traversal": [
                r"(\.\./|\.\.\%2F)",
                r"(\%2E\%2E\%2F|\%2E\%2E/)",
                r"(\.\.\\|\.\.\%5C)"
            ],
            "command_injection": [
                r"(\||&&|;|\$\(|\`)",
                r"(nc|netcat|wget|curl)\s",
                r"/bin/(bash|sh|csh|tcsh|zsh)"
            ]
        }
    
    def _load_bot_signatures(self) -> Dict[str, Any]:
        """Load bot detection signatures"""
        return {
            "user_agents": [
                "bot", "crawler", "spider", "scraper", "curl", "wget",
                "python-requests", "httpx", "axios", "node-fetch"
            ],
            "request_patterns": {
                "too_fast": {"requests_per_second": 10, "window": 60},
                "no_js": {"js_enabled": False, "suspicious_score": 0.7},
                "linear_browsing": {"page_sequence_score": 0.9}
            },
            "behavioral_flags": [
                "no_mouse_movement", "no_scroll", "perfect_timing",
                "missing_headers", "suspicious_referrer"
            ]
        }
    
    def analyze_request(self, request_data: Dict[str, Any]) -> ThreatEvent:
        """Analyze incoming request for threats"""
        ip_address = request_data.get("ip_address", "unknown")
        user_id = request_data.get("user_id")
        timestamp = datetime.now()
        
        # Extract features
        features = self._extract_features(request_data)
        
        # Run detection algorithms
        threat_scores = {}
        
        # 1. Pattern-based detection
        pattern_score = self._detect_attack_patterns(request_data)
        threat_scores["pattern"] = pattern_score
        
        # 2. Bot detection
        bot_score = self._detect_bot_behavior(request_data, ip_address)
        threat_scores["bot"] = bot_score
        
        # 3. Rate limiting analysis
        rate_score = self._analyze_rate_patterns(ip_address, user_id)
        threat_scores["rate"] = rate_score
        
        # 4. Behavioral anomaly detection (ML)
        if self.ml_available and user_id:
            anomaly_score = self._detect_behavioral_anomaly(user_id, features)
            threat_scores["anomaly"] = anomaly_score
        
        # 5. IP reputation analysis
        reputation_score = self._analyze_ip_reputation(ip_address)
        threat_scores["reputation"] = reputation_score
        
        # Combine scores with weighted ensemble
        combined_score = self._combine_threat_scores(threat_scores)
        threat_level = self._score_to_threat_level(combined_score)
        threat_type = self._determine_threat_type(threat_scores, request_data)
        
        # Create threat event
        event_id = hashlib.md5(f"{ip_address}{timestamp.isoformat()}".encode()).hexdigest()[:8]
        
        threat_event = ThreatEvent(
            event_id=event_id,
            ip_address=ip_address,
            user_id=user_id,
            threat_type=threat_type,
            threat_level=threat_level,
            confidence_score=combined_score,
            evidence={"scores": threat_scores, "features": features},
            timestamp=timestamp,
            features=features,
            ml_prediction=None
        )
        
        # Add ML prediction if available
        if self.ml_available:
            ml_prediction = self._get_ml_prediction(features)
            threat_event.ml_prediction = ml_prediction
        
        # Store event
        self.threat_events.append(threat_event)
        
        # Update IP reputation
        self._update_ip_reputation(ip_address, threat_event)
        
        # Update user profile
        if user_id:
            self._update_user_profile(user_id, features, request_data)
        
        return threat_event
    
    def _extract_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from request data"""
        features = {}
        
        # Request characteristics
        features["request_size"] = len(str(request_data.get("content", "")))
        features["header_count"] = len(request_data.get("headers", {}))
        features["param_count"] = len(request_data.get("parameters", {}))
        features["path_length"] = len(request_data.get("path", ""))
        
        # Timing features
        features["hour_of_day"] = datetime.now().hour
        features["day_of_week"] = datetime.now().weekday()
        
        # Content analysis
        content = str(request_data.get("content", ""))
        features["special_char_ratio"] = len(re.findall(r'[^a-zA-Z0-9\s]', content)) / max(len(content), 1)
        features["numeric_ratio"] = len(re.findall(r'\d', content)) / max(len(content), 1)
        features["uppercase_ratio"] = len(re.findall(r'[A-Z]', content)) / max(len(content), 1)
        
        # User agent analysis
        user_agent = request_data.get("user_agent", "")
        features["user_agent_length"] = len(user_agent)
        features["user_agent_entropy"] = self._calculate_entropy(user_agent)
        
        # Geolocation (if available)
        location = request_data.get("location", {})
        features["lat"] = location.get("latitude", 0.0)
        features["lon"] = location.get("longitude", 0.0)
        
        return features
    
    def _detect_attack_patterns(self, request_data: Dict[str, Any]) -> float:
        """Detect known attack patterns"""
        content = str(request_data.get("content", ""))
        url = str(request_data.get("url", ""))
        headers = str(request_data.get("headers", {}))
        
        combined_text = f"{content} {url} {headers}".lower()
        
        max_score = 0.0
        for attack_type, patterns in self.known_attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    max_score = max(max_score, 0.8)
        
        return max_score
    
    def _detect_bot_behavior(self, request_data: Dict[str, Any], ip_address: str) -> float:
        """Detect bot-like behavior patterns"""
        score = 0.0
        
        # User agent analysis
        user_agent = request_data.get("user_agent", "").lower()
        for bot_ua in self.bot_signatures["user_agents"]:
            if bot_ua in user_agent:
                score += 0.3
        
        # Request frequency analysis
        current_time = datetime.now()
        self.request_windows[ip_address].append(current_time)
        
        # Check recent request rate
        recent_requests = [
            req_time for req_time in self.request_windows[ip_address]
            if current_time - req_time < timedelta(seconds=60)
        ]
        
        requests_per_minute = len(recent_requests)
        if requests_per_minute > 30:
            score += 0.4
        elif requests_per_minute > 15:
            score += 0.2
        
        # Missing common headers
        headers = request_data.get("headers", {})
        common_headers = ["accept", "accept-language", "accept-encoding"]
        missing_headers = sum(1 for h in common_headers if h not in headers.keys())
        score += missing_headers * 0.1
        
        return min(score, 1.0)
    
    def _analyze_rate_patterns(self, ip_address: str, user_id: Optional[str]) -> float:
        """Analyze request rate patterns for anomalies"""
        current_time = datetime.now()
        
        # IP-based rate analysis
        ip_requests = self.request_windows[ip_address]
        
        # Check for burst patterns
        last_minute = [req for req in ip_requests if current_time - req < timedelta(minutes=1)]
        last_hour = [req for req in ip_requests if current_time - req < timedelta(hours=1)]
        
        score = 0.0
        
        # Burst detection
        if len(last_minute) > 20:
            score += 0.5
        if len(last_hour) > 100:
            score += 0.3
        
        # Regular interval detection (bot behavior)
        if len(last_minute) >= 3:
            intervals = []
            sorted_requests = sorted(last_minute)
            for i in range(1, len(sorted_requests)):
                interval = (sorted_requests[i] - sorted_requests[i-1]).total_seconds()
                intervals.append(interval)
            
            if intervals:
                avg_interval = np.mean(intervals)
                std_interval = np.std(intervals)
                if std_interval < 0.5 and avg_interval < 10:  # Very regular, fast requests
                    score += 0.4
        
        return min(score, 1.0)
    
    def _detect_behavioral_anomaly(self, user_id: str, features: Dict[str, float]) -> float:
        """Use ML to detect behavioral anomalies"""
        if not self.ml_available:
            return 0.0
        
        # Get or create user profile
        if user_id not in self.user_profiles:
            return 0.0  # Can't detect anomaly without baseline
        
        profile = self.user_profiles[user_id]
        
        # Convert features to array
        feature_vector = np.array(list(features.values())).reshape(1, -1)
        
        # Use isolation forest for anomaly detection
        try:
            anomaly_score = self.anomaly_detector.decision_function(feature_vector)[0]
            # Convert to 0-1 range (lower is more anomalous)
            normalized_score = 1.0 - max(0, min(1, (anomaly_score + 0.5) / 1.0))
            return normalized_score
        except Exception as e:
            logger.warning(f"ML anomaly detection failed: {e}")
            return 0.0
    
    def _analyze_ip_reputation(self, ip_address: str) -> float:
        """Analyze IP reputation based on historical behavior"""
        reputation = self.ip_reputation[ip_address]
        
        # Base score on historical events
        base_score = min(reputation["score"] / 100.0, 1.0)
        
        # Check for recent suspicious activity
        recent_events = [
            event for event in reputation["events"]
            if datetime.now() - event["timestamp"] < timedelta(hours=24)
        ]
        
        recent_score = len(recent_events) * 0.1
        
        return min(base_score + recent_score, 1.0)
    
    def _combine_threat_scores(self, scores: Dict[str, float]) -> float:
        """Combine individual threat scores using weighted ensemble"""
        weights = {
            "pattern": 0.3,
            "bot": 0.2,
            "rate": 0.2,
            "anomaly": 0.2,
            "reputation": 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for score_type, score in scores.items():
            if score_type in weights:
                weight = weights[score_type]
                weighted_score += score * weight
                total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _score_to_threat_level(self, score: float) -> ThreatLevel:
        """Convert threat score to threat level"""
        if score >= 0.8:
            return ThreatLevel.CRITICAL
        elif score >= 0.6:
            return ThreatLevel.HIGH
        elif score >= 0.3:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _determine_threat_type(self, scores: Dict[str, float], request_data: Dict[str, Any]) -> ThreatType:
        """Determine the primary threat type based on scores and data"""
        max_score_type = max(scores.items(), key=lambda x: x[1])[0]
        
        if max_score_type == "pattern":
            return ThreatType.SUSPICIOUS_PATTERN
        elif max_score_type == "bot":
            return ThreatType.BOT_ACTIVITY
        elif max_score_type == "rate":
            return ThreatType.BRUTE_FORCE
        elif max_score_type == "anomaly":
            return ThreatType.BEHAVIORAL_ANOMALY
        else:
            return ThreatType.SUSPICIOUS_PATTERN
    
    def _get_ml_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Get ML model predictions"""
        if not self.ml_available:
            return {}
        
        try:
            feature_vector = np.array(list(features.values())).reshape(1, -1)
            
            # Get predictions from ensemble
            predictions = {}
            
            # Anomaly detection
            if hasattr(self.anomaly_detector, 'predict'):
                anomaly_pred = self.anomaly_detector.predict(feature_vector)[0]
                predictions["is_anomaly"] = anomaly_pred == -1
            
            return predictions
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            return {}
    
    def _update_ip_reputation(self, ip_address: str, threat_event: ThreatEvent):
        """Update IP reputation based on threat event"""
        reputation = self.ip_reputation[ip_address]
        
        # Increase score based on threat level
        score_increase = threat_event.threat_level.value["score"] * 10
        reputation["score"] += score_increase
        
        # Add event to history
        reputation["events"].append({
            "timestamp": threat_event.timestamp,
            "threat_level": threat_event.threat_level.name,
            "threat_type": threat_event.threat_type.name
        })
        
        # Keep only recent events
        reputation["events"] = [
            event for event in reputation["events"]
            if datetime.now() - event["timestamp"] < timedelta(days=7)
        ]
    
    def _update_user_profile(self, user_id: str, features: Dict[str, float], request_data: Dict[str, Any]):
        """Update user behavioral profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(
                user_id=user_id,
                session_patterns=defaultdict(list),
                request_patterns=defaultdict(list),
                content_patterns=defaultdict(list),
                temporal_patterns=defaultdict(list),
                location_patterns=[],
                device_patterns=[],
                last_updated=datetime.now()
            )
        
        profile = self.user_profiles[user_id]
        
        # Update patterns
        for feature_name, feature_value in features.items():
            if feature_name.startswith("request_"):
                profile.request_patterns[feature_name].append(feature_value)
            elif feature_name.startswith("content_"):
                profile.content_patterns[feature_name].append(feature_value)
            elif feature_name in ["hour_of_day", "day_of_week"]:
                profile.temporal_patterns[feature_name].append(feature_value)
        
        # Limit history size
        for pattern_dict in [profile.session_patterns, profile.request_patterns, 
                           profile.content_patterns, profile.temporal_patterns]:
            for key, values in pattern_dict.items():
                if len(values) > 1000:
                    pattern_dict[key] = values[-1000:]
        
        profile.last_updated = datetime.now()
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        char_counts = defaultdict(int)
        for char in text:
            char_counts[char] += 1
        
        entropy = 0.0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            entropy -= probability * np.log2(probability)
        
        return entropy
    
    def get_threat_intelligence(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat intelligence summary"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event for event in self.threat_events
            if event.timestamp > cutoff_time
        ]
        
        # Analyze patterns
        threat_types = defaultdict(int)
        threat_levels = defaultdict(int)
        top_ips = defaultdict(int)
        
        for event in recent_events:
            threat_types[event.threat_type.name] += 1
            threat_levels[event.threat_level.name] += 1
            top_ips[event.ip_address] += 1
        
        return {
            "summary": {
                "total_events": len(recent_events),
                "critical_events": threat_levels.get("CRITICAL", 0),
                "high_events": threat_levels.get("HIGH", 0),
                "unique_ips": len(top_ips)
            },
            "threat_types": dict(threat_types),
            "threat_levels": dict(threat_levels),
            "top_threat_ips": dict(sorted(top_ips.items(), key=lambda x: x[1], reverse=True)[:10]),
            "ml_status": "enabled" if self.ml_available else "disabled"
        }
    
    def should_block_request(self, threat_event: ThreatEvent) -> bool:
        """Determine if request should be blocked based on threat assessment"""
        return threat_event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
    
    def get_user_risk_score(self, user_id: str) -> float:
        """Get current risk score for a user"""
        if user_id not in self.user_profiles:
            return 0.0
        
        # Analyze recent activity
        user_events = [
            event for event in self.threat_events
            if event.user_id == user_id and 
            datetime.now() - event.timestamp < timedelta(hours=24)
        ]
        
        if not user_events:
            return 0.0
        
        # Calculate average risk score
        risk_scores = [event.confidence_score for event in user_events]
        return np.mean(risk_scores)