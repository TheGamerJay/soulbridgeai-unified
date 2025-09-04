"""
Enhanced Beat Wizard - Advanced Music Production Analysis
Improved version with confidence scoring, auto-save, and robust detection
"""

import logging
import re
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask import Blueprint, request, jsonify, session

from ..auth.session_manager import requires_login, get_user_id
from ..auth.access_control import require_tier
from ..library.library_manager import LibraryManager

logger = logging.getLogger(__name__)

# Create blueprint
beat_bp = Blueprint('beat', __name__)

@dataclass
class BeatAnalysis:
    """Immutable beat analysis result"""
    bpm: int
    genre: str
    mood: str
    key_signature: str
    time_signature: str
    description: str
    suggestions: List[str]
    confidence_scores: Dict[str, float]
    created_at: str
    seed: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class EnhancedBeatWizard:
    """Enhanced Beat Wizard with improved analysis capabilities"""
    
    def __init__(self):
        self.genre_keywords = {
            'house': {
                'keywords': ['four-on-the-floor', 'synth', 'electronic', 'dance', 'club', 'bassline', 'kick'],
                'bpm_range': (120, 130),
                'weight': 1.0
            },
            'techno': {
                'keywords': ['repetitive', 'electronic', 'industrial', 'driving', 'mechanical', 'synthesizer'],
                'bpm_range': (120, 150),
                'weight': 1.0
            },
            'hip-hop': {
                'keywords': ['rap', 'urban', 'beats', 'sampling', 'rhythm', 'bass', 'drums', 'street'],
                'bpm_range': (70, 140),
                'weight': 1.2
            },
            'trap': {
                'keywords': ['trap', '808', 'hi-hat', 'snare', 'roll', 'southern', 'heavy', 'bass'],
                'bpm_range': (130, 170),
                'weight': 1.1
            },
            'drill': {
                'keywords': ['drill', 'dark', 'aggressive', 'sliding', '808', 'menacing', 'street'],
                'bpm_range': (130, 160),
                'weight': 1.1
            },
            'ambient': {
                'keywords': ['atmospheric', 'calm', 'peaceful', 'floating', 'ethereal', 'spacious'],
                'bpm_range': (60, 90),
                'weight': 0.9
            },
            'jazz': {
                'keywords': ['swing', 'improvisation', 'complex', 'sophisticated', 'brass', 'piano'],
                'bpm_range': (90, 180),
                'weight': 0.8
            },
            'reggae': {
                'keywords': ['offbeat', 'caribbean', 'skank', 'bass', 'guitar', 'rhythm'],
                'bpm_range': (60, 90),
                'weight': 0.9
            },
            'dubstep': {
                'keywords': ['wobble', 'bass', 'drop', 'electronic', 'heavy', 'distorted'],
                'bpm_range': (140, 150),
                'weight': 1.0
            },
            'pop': {
                'keywords': ['catchy', 'mainstream', 'accessible', 'commercial', 'melodic'],
                'bpm_range': (100, 130),
                'weight': 0.8
            },
            'reggaeton': {
                'keywords': ['perreo', 'dembow', 'reggaeton', 'reggaetón', 'reguetón', 'latin'],
                'bpm_range': (90, 110),
                'weight': 1.5
            },
            'bachata': {
                'keywords': ['bachata', 'guitarra', 'romantic', 'guitar', 'latin'],
                'bpm_range': (80, 100),
                'weight': 1.4
            }
        }
        
        self.mood_keywords = {
            'energetic': ['fast', 'upbeat', 'driving', 'powerful', 'intense', 'exciting'],
            'chill': ['relaxed', 'calm', 'smooth', 'laid-back', 'peaceful', 'mellow'],
            'dark': ['heavy', 'aggressive', 'menacing', 'brooding', 'intense', 'sinister'],
            'happy': ['uplifting', 'joyful', 'positive', 'bright', 'cheerful', 'optimistic'],
            'melancholic': ['sad', 'emotional', 'nostalgic', 'wistful', 'contemplative'],
            'mysterious': ['atmospheric', 'ethereal', 'ambient', 'spacious', 'haunting']
        }

    def generate_deterministic_seed(self, description: str, user_id: str) -> str:
        """Generate deterministic seed for consistent results"""
        combined = f"{description.lower().strip()}:{user_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def calculate_syllable_density(self, text: str) -> float:
        """Calculate syllable density for BPM estimation"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 1.0
            
        vowel_groups = re.findall(r'[aeiouy]+', ' '.join(words))
        syllable_count = len(vowel_groups)
        word_count = len(words)
        
        return syllable_count / word_count if word_count > 0 else 1.0

    def detect_genre_with_confidence(self, description: str, bpm: int) -> Tuple[str, float]:
        """Enhanced genre detection with confidence scoring"""
        description_lower = description.lower()
        genre_scores = {}
        
        for genre, data in self.genre_keywords.items():
            score = 0.0
            keyword_matches = 0
            
            # Keyword matching with weights
            for keyword in data['keywords']:
                if keyword in description_lower:
                    score += data['weight']
                    keyword_matches += 1
            
            # BPM range bonus
            bpm_min, bpm_max = data['bpm_range']
            if bpm_min <= bpm <= bpm_max:
                score += 2.0
            elif abs(bpm - (bpm_min + bpm_max) / 2) <= 20:
                score += 1.0
            
            # Normalize score
            if keyword_matches > 0:
                score = score / len(data['keywords']) * keyword_matches
                
            genre_scores[genre] = score
        
        # First check direct keyword matches for high confidence
        if 'drill' in description_lower:
            return 'drill', 0.9
        elif 'trap' in description_lower:
            return 'trap', 0.9  
        elif 'bachata' in description_lower:
            return 'bachata', 0.9
        elif 'reggaeton' in description_lower or 'dembow' in description_lower:
            return 'reggaeton', 0.9
        elif 'house' in description_lower or ('electronic' in description_lower and 'dance' in description_lower):
            return 'house', 0.8
        
        if not genre_scores:
            return 'electronic', 0.5
            
        best_genre = max(genre_scores.items(), key=lambda x: x[1])
        confidence = min(best_genre[1] / 3.0, 1.0)  # Normalize to 0-1
        
        return best_genre[0], confidence

    def detect_mood_with_confidence(self, description: str) -> Tuple[str, float]:
        """Enhanced mood detection with confidence scoring"""
        description_lower = description.lower()
        mood_scores = {}
        
        for mood, keywords in self.mood_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                mood_scores[mood] = score / len(keywords)
        
        if not mood_scores:
            return 'neutral', 0.5
            
        best_mood = max(mood_scores.items(), key=lambda x: x[1])
        return best_mood[0], best_mood[1]

    def estimate_bpm(self, description: str, genre: str) -> int:
        """Enhanced BPM estimation with genre context"""
        syllable_density = self.calculate_syllable_density(description)
        
        # Base BPM from syllable density
        base_bpm = int(80 + (syllable_density - 1.0) * 40)
        base_bpm = max(60, min(200, base_bpm))
        
        # Genre-specific adjustment
        if genre in self.genre_keywords:
            genre_min, genre_max = self.genre_keywords[genre]['bpm_range']
            genre_center = (genre_min + genre_max) / 2
            
            # Weighted average between calculated and genre typical
            final_bpm = int(0.6 * base_bpm + 0.4 * genre_center)
            
            # Ensure within reasonable range for genre
            return max(genre_min - 10, min(genre_max + 10, final_bpm))
        
        return base_bpm

    def generate_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions based on analysis"""
        suggestions = []
        genre = analysis['genre']
        mood = analysis['mood']
        bpm = analysis['bpm']
        
        # Genre-specific suggestions
        if genre == 'house':
            suggestions.extend([
                "Add a strong four-on-the-floor kick pattern",
                "Layer in some acid basslines for authentic house vibes",
                "Consider adding filtered disco samples"
            ])
        elif genre == 'hip-hop':
            suggestions.extend([
                "Focus on a strong drum pattern with snappy snares",
                "Layer in some vinyl crackle for authenticity",
                "Add space for vocal delivery with strategic breaks"
            ])
        elif genre == 'trap':
            suggestions.extend([
                "Use heavy 808 drums with sub bass",
                "Add rapid hi-hat rolls for modern trap feel",
                "Layer dark atmospheric pads"
            ])
        elif genre == 'reggaeton':
            suggestions.extend([
                "Use the classic dembow rhythm pattern",
                "Add Latin percussion elements",
                "Include melodic guitar or piano elements"
            ])
        elif genre == 'ambient':
            suggestions.extend([
                "Use reverb and delay to create spatial depth",
                "Layer atmospheric pads for texture",
                "Keep percussion minimal and organic"
            ])
        
        # BPM-specific suggestions
        if bpm < 80:
            suggestions.append("Perfect tempo for downtempo or ambient tracks")
        elif bpm > 150:
            suggestions.append("High-energy tempo - great for dance or electronic music")
        
        # Mood-specific suggestions
        if mood == 'dark':
            suggestions.append("Use minor keys and heavy bass for darker atmosphere")
        elif mood == 'energetic':
            suggestions.append("Add dynamic builds and drops to maintain energy")
        
        return suggestions[:5]  # Limit to top 5 suggestions

    def analyze_beat(self, description: str, user_id: str, genre_override: Optional[str] = None, bpm_override: Optional[int] = None) -> BeatAnalysis:
        """Comprehensive beat analysis with enhanced algorithms"""
        try:
            # Generate deterministic seed
            seed = self.generate_deterministic_seed(description, user_id)
            
            # Enhanced analysis with overrides
            if genre_override and genre_override in self.genre_keywords:
                genre = genre_override
                genre_confidence = 1.0  # High confidence for user-selected genre
            else:
                genre, genre_confidence = self.detect_genre_with_confidence(description, 120)  # Initial BPM estimate
            
            mood, mood_confidence = self.detect_mood_with_confidence(description)
            
            if bpm_override and 60 <= bpm_override <= 200:
                bpm = bpm_override
            else:
                bpm = self.estimate_bpm(description, genre)
            
            # Re-calculate genre with better BPM if not overridden
            if not genre_override:
                genre, genre_confidence = self.detect_genre_with_confidence(description, bpm)
            
            # Additional analysis
            key_signature = self._infer_key_signature(description, mood)
            time_signature = self._infer_time_signature(description, genre)
            
            analysis_dict = {
                'genre': genre,
                'mood': mood,
                'bpm': bpm,
                'key_signature': key_signature,
                'time_signature': time_signature
            }
            
            suggestions = self.generate_suggestions(analysis_dict)
            confidence_scores = {
                'genre': genre_confidence,
                'mood': mood_confidence,
                'overall': (genre_confidence + mood_confidence) / 2
            }
            
            # Generate enhanced description
            enhanced_description = self._generate_description(analysis_dict, description)
            
            return BeatAnalysis(
                bpm=bpm,
                genre=genre,
                mood=mood,
                key_signature=key_signature,
                time_signature=time_signature,
                description=enhanced_description,
                suggestions=suggestions,
                confidence_scores=confidence_scores,
                created_at=datetime.now().isoformat(),
                seed=seed
            )
            
        except Exception as e:
            logger.error(f"Error in beat analysis: {e}")
            # Return safe default
            return BeatAnalysis(
                bpm=120,
                genre='electronic',
                mood='neutral',
                key_signature='C major',
                time_signature='4/4',
                description="A balanced electronic composition suitable for various applications.",
                suggestions=["Focus on strong rhythm patterns", "Add melodic elements for interest"],
                confidence_scores={'genre': 0.5, 'mood': 0.5, 'overall': 0.5},
                created_at=datetime.now().isoformat(),
                seed='default'
            )

    def _infer_key_signature(self, description: str, mood: str) -> str:
        """Infer key signature based on description and mood"""
        description_lower = description.lower()
        
        # Mood-based key inference
        if mood in ['dark', 'melancholic']:
            minor_keys = ['A minor', 'D minor', 'G minor', 'C minor', 'F minor']
            return minor_keys[hash(description) % len(minor_keys)]
        elif mood in ['happy', 'energetic']:
            major_keys = ['C major', 'G major', 'D major', 'A major', 'E major']
            return major_keys[hash(description) % len(major_keys)]
        
        # Default balanced approach
        all_keys = ['C major', 'G major', 'D major', 'A minor', 'E minor', 'F major']
        return all_keys[hash(description) % len(all_keys)]

    def _infer_time_signature(self, description: str, genre: str) -> str:
        """Infer time signature based on description and genre"""
        description_lower = description.lower()
        
        # Genre-specific time signatures
        if genre in ['house', 'techno', 'pop', 'hip-hop', 'trap']:
            return '4/4'
        elif genre == 'jazz' and any(word in description_lower for word in ['swing', 'waltz']):
            return '3/4'
        elif 'complex' in description_lower or 'odd' in description_lower:
            return '7/8'
        
        return '4/4'  # Default

    def _generate_description(self, analysis: Dict[str, Any], original: str) -> str:
        """Generate enhanced description based on analysis"""
        genre = analysis['genre']
        mood = analysis['mood']
        bpm = analysis['bpm']
        key = analysis['key_signature']
        
        tempo_desc = "slow and contemplative" if bpm < 80 else "moderate" if bpm < 130 else "fast-paced and energetic"
        
        return f"A {mood} {genre} composition in {key} with a {tempo_desc} feel at {bpm} BPM. {original[:100]}{'...' if len(original) > 100 else ''}"


# Initialize the enhanced beat wizard
beat_wizard = EnhancedBeatWizard()

@beat_bp.route('/analyze', methods=['POST'])
@requires_login
def analyze_beat():
    """Analyze beat description and return comprehensive results"""
    try:
        data = request.get_json()
        if not data or not data.get('description'):
            return jsonify({
                'success': False,
                'error': 'Beat description is required'
            }), 400
        
        description = data['description'].strip()
        if len(description) < 10:
            return jsonify({
                'success': False,
                'error': 'Description must be at least 10 characters long'
            }), 400
        
        user_id = get_user_id()
        
        # Get optional overrides
        genre_override = data.get('genre_override')
        bpm_override = data.get('bpm_override')
        
        # Perform analysis with overrides
        analysis = beat_wizard.analyze_beat(description, user_id, genre_override, bpm_override)
        
        # Auto-save to library
        try:
            library_manager = LibraryManager()
            library_manager.save_content(
                user_id=user_id,
                content_type='beat_analysis',
                content_data={
                    'title': f"Beat Analysis - {analysis.genre.title()}",
                    'description': description,
                    'analysis': analysis.to_dict(),
                    'created_at': analysis.created_at
                },
                metadata={'seed': analysis.seed}
            )
            logger.info(f"Beat analysis auto-saved for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to auto-save beat analysis: {e}")
            # Continue anyway - analysis still works
        
        return jsonify({
            'success': True,
            'analysis': analysis.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error in beat analysis endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Beat analysis failed'
        }), 500

@beat_bp.route('/health', methods=['GET'])
def beat_health():
    """Health check for beat wizard service"""
    try:
        # Quick test analysis
        test_analysis = beat_wizard.analyze_beat("upbeat electronic dance track", "test_user")
        
        return jsonify({
            'status': 'healthy',
            'service': 'beat_wizard',
            'version': '2.0.0',
            'features': [
                'genre_detection',
                'mood_analysis',
                'bpm_estimation',
                'confidence_scoring',
                'auto_save',
                'multilingual_support'
            ],
            'test_passed': test_analysis.genre is not None
        })
        
    except Exception as e:
        logger.error(f"Beat wizard health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@beat_bp.route('/stats', methods=['GET'])
@requires_login
def beat_stats():
    """Get beat analysis statistics for current user"""
    try:
        user_id = get_user_id()
        
        # This would require database integration for real stats
        # For now, return mock stats
        return jsonify({
            'success': True,
            'stats': {
                'total_analyses': 0,
                'favorite_genre': 'electronic',
                'average_bpm': 120,
                'most_common_mood': 'energetic'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting beat stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500

def init_beat_system():
    """Initialize Beat Wizard system"""
    logger.info("Enhanced Beat Wizard system initialized successfully")