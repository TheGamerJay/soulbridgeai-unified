"""
Advanced Poem Generation Suite
Comprehensive poetry creation with multiple forms: haiku, sonnets, free verse, acrostics
"""

import logging
import json
import hashlib
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import random

logger = logging.getLogger(__name__)

class PoemType(Enum):
    """Supported poem types"""
    HAIKU = "haiku"
    SONNET = "sonnet"
    FREE_VERSE = "free_verse"
    ACROSTIC = "acrostic"
    LIMERICK = "limerick"
    CINQUAIN = "cinquain"
    TANKA = "tanka"
    VILLANELLE = "villanelle"

class RhymeScheme(Enum):
    """Rhyme scheme patterns"""
    SHAKESPEAREAN = "ABAB CDCD EFEF GG"  # Shakespearean sonnet
    PETRARCHAN = "ABBAABBA CDECDE"       # Petrarchan sonnet
    LIMERICK = "AABBA"                   # Limerick pattern
    BALLAD = "ABAB"                      # Ballad meter
    COUPLET = "AABB"                     # Heroic couplets
    ALTERNATE = "ABAB"                   # Alternating rhyme
    ENCLOSED = "ABBA"                    # Enclosed rhyme

@dataclass
class PoemStructure:
    """Defines the structure of a poem type"""
    poem_type: PoemType
    lines: int
    syllable_pattern: Optional[List[int]] = None
    rhyme_scheme: Optional[RhymeScheme] = None
    meter_pattern: Optional[str] = None
    stanza_structure: Optional[List[int]] = None
    special_rules: Optional[Dict[str, Any]] = None

@dataclass
class GeneratedPoem:
    """Container for a generated poem with metadata"""
    poem_id: str
    poem_type: PoemType
    title: str
    content: str
    structure: PoemStructure
    theme: str
    mood: str
    language: str
    syllable_count: List[int]
    rhyme_analysis: Dict[str, Any]
    created_date: datetime
    generation_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'poem_id': self.poem_id,
            'poem_type': self.poem_type.value,
            'title': self.title,
            'content': self.content,
            'structure': asdict(self.structure),
            'theme': self.theme,
            'mood': self.mood,
            'language': self.language,
            'syllable_count': self.syllable_count,
            'rhyme_analysis': self.rhyme_analysis,
            'created_date': self.created_date.isoformat(),
            'generation_metadata': self.generation_metadata
        }

class SyllableCounter:
    """Syllable counting utility for poetry meter"""
    
    # Common syllable patterns
    VOWEL_GROUPS = r'[aeiouyAEIOUY]+'
    SILENT_E = r'[^aeiouAEIOU]e\b'
    COMMON_ENDINGS = {
        'ed': -1,  # Usually silent in past tense
        'es': 0,   # Variable
        'le': 1,   # Usually one syllable
        'ing': 1,  # One syllable
        'ion': 2,  # Two syllables
        'tion': 2, # Two syllables
        'sion': 2, # Two syllables
    }
    
    @staticmethod
    def count_syllables(word: str) -> int:
        """Count syllables in a word using heuristic rules"""
        if not word:
            return 0
        
        word = word.lower().strip()
        
        # Handle common exceptions
        exceptions = {
            'the': 1, 'a': 1, 'an': 1, 'and': 1, 'or': 1, 'but': 1,
            'fire': 1, 'hour': 1, 'our': 1, 'your': 1, 'are': 1,
            'eye': 1, 'eyes': 1, 'isle': 1, 'aisle': 1,
            'orange': 2, 'people': 2, 'purple': 2, 'circle': 2,
            'simple': 2, 'little': 2, 'middle': 2, 'bottle': 2,
            'poem': 2, 'poems': 2, 'quiet': 2, 'create': 2,
            'beautiful': 3, 'family': 3, 'everything': 3,
            'different': 3, 'important': 3, 'interesting': 4,
            'generation': 4, 'information': 4, 'education': 4
        }
        
        if word in exceptions:
            return exceptions[word]
        
        # Count vowel groups
        vowel_groups = re.findall(SyllableCounter.VOWEL_GROUPS, word)
        syllable_count = len(vowel_groups)
        
        # Adjust for silent e
        if re.search(SyllableCounter.SILENT_E, word) and syllable_count > 1:
            syllable_count -= 1
        
        # Adjust for common endings
        for ending, adjustment in SyllableCounter.COMMON_ENDINGS.items():
            if word.endswith(ending):
                syllable_count += adjustment
                break
        
        return max(1, syllable_count)  # Every word has at least 1 syllable
    
    @staticmethod
    def count_line_syllables(line: str) -> int:
        """Count total syllables in a line"""
        words = re.findall(r'\b\w+\b', line)
        return sum(SyllableCounter.count_syllables(word) for word in words)

class RhymeAnalyzer:
    """Analyzes and generates rhyme schemes"""
    
    @staticmethod
    def get_rhyme_sound(word: str) -> str:
        """Get the rhyme sound of a word (simplified phonetic ending)"""
        word = word.lower().strip()
        
        # Remove punctuation
        word = re.sub(r'[^\w]', '', word)
        
        if not word:
            return ""
        
        # Simple rhyme sound approximation based on ending
        # This is a basic implementation - a full system would use phonetic analysis
        
        # Common rhyme endings
        rhyme_patterns = {
            r'ing\b': 'ing',
            r'tion\b': 'shun',
            r'sion\b': 'shun', 
            r'ed\b': 'ed',
            r'er\b': 'er',
            r'ly\b': 'lee',
            r'y\b': 'ee',
            r'ight\b': 'ite',
            r'ought\b': 'awt',
            r'ough\b': 'uff',
            r'ough\b': 'oh',  # through, though
            r'ough\b': 'aw',  # cough, trough
        }
        
        for pattern, sound in rhyme_patterns.items():
            if re.search(pattern, word):
                return sound
        
        # Default to last 2-3 characters
        if len(word) >= 3:
            return word[-3:]
        elif len(word) >= 2:
            return word[-2:]
        else:
            return word
    
    @staticmethod
    def analyze_rhyme_scheme(lines: List[str]) -> Dict[str, Any]:
        """Analyze the rhyme scheme of a poem"""
        if not lines:
            return {'scheme': '', 'rhyme_map': {}, 'quality_score': 0.0}
        
        # Get last word of each line
        line_endings = []
        for line in lines:
            words = re.findall(r'\b\w+\b', line.strip())
            if words:
                line_endings.append(words[-1])
            else:
                line_endings.append("")
        
        # Get rhyme sounds
        rhyme_sounds = [RhymeAnalyzer.get_rhyme_sound(word) for word in line_endings]
        
        # Create rhyme scheme
        scheme_letters = []
        sound_to_letter = {}
        current_letter = ord('A')
        
        for sound in rhyme_sounds:
            if not sound:
                scheme_letters.append('X')  # No rhyme
                continue
                
            if sound not in sound_to_letter:
                sound_to_letter[sound] = chr(current_letter)
                current_letter += 1
            
            scheme_letters.append(sound_to_letter[sound])
        
        scheme = ''.join(scheme_letters)
        
        # Calculate rhyme quality score
        unique_sounds = len(set(s for s in rhyme_sounds if s))
        total_lines = len(lines)
        rhyming_lines = sum(1 for s in rhyme_sounds if s and rhyme_sounds.count(s) > 1)
        
        quality_score = rhyming_lines / total_lines if total_lines > 0 else 0.0
        
        return {
            'scheme': scheme,
            'rhyme_map': {letter: sound for sound, letter in sound_to_letter.items()},
            'quality_score': quality_score,
            'line_endings': line_endings,
            'rhyme_sounds': rhyme_sounds
        }

class PoemStructureManager:
    """Manages poem structure definitions and validation"""
    
    STRUCTURES = {
        PoemType.HAIKU: PoemStructure(
            poem_type=PoemType.HAIKU,
            lines=3,
            syllable_pattern=[5, 7, 5],
            special_rules={
                'nature_theme': True,
                'present_tense': True,
                'seasonal_reference': 'preferred',
                'kigo': 'optional',  # seasonal word
                'cutting_word': 'optional'  # kireji
            }
        ),
        
        PoemType.SONNET: PoemStructure(
            poem_type=PoemType.SONNET,
            lines=14,
            syllable_pattern=[10] * 14,  # Iambic pentameter
            rhyme_scheme=RhymeScheme.SHAKESPEAREAN,
            stanza_structure=[4, 4, 4, 2],  # Three quatrains and a couplet
            meter_pattern="iambic_pentameter",
            special_rules={
                'volta': 9,  # Turn at line 9
                'theme_development': True,
                'couplet_resolution': True
            }
        ),
        
        PoemType.FREE_VERSE: PoemStructure(
            poem_type=PoemType.FREE_VERSE,
            lines=0,  # Variable
            special_rules={
                'no_rhyme_required': True,
                'no_meter_required': True,
                'focus_on_imagery': True,
                'line_breaks_meaningful': True,
                'white_space_important': True
            }
        ),
        
        PoemType.ACROSTIC: PoemStructure(
            poem_type=PoemType.ACROSTIC,
            lines=0,  # Variable based on word
            special_rules={
                'first_letter_pattern': True,
                'word_theme_connection': True,
                'each_line_complete_thought': True
            }
        ),
        
        PoemType.LIMERICK: PoemStructure(
            poem_type=PoemType.LIMERICK,
            lines=5,
            rhyme_scheme=RhymeScheme.LIMERICK,
            stanza_structure=[5],
            syllable_pattern=[8, 8, 5, 5, 8],  # Approximate
            special_rules={
                'humorous_tone': True,
                'narrative_structure': True,
                'surprise_ending': True,
                'bouncy_rhythm': True
            }
        ),
        
        PoemType.TANKA: PoemStructure(
            poem_type=PoemType.TANKA,
            lines=5,
            syllable_pattern=[5, 7, 5, 7, 7],
            special_rules={
                'japanese_origin': True,
                'pivot_line': 3,  # Line 3 often pivots the meaning
                'nature_or_emotion': True,
                'two_part_structure': True
            }
        ),
        
        PoemType.CINQUAIN: PoemStructure(
            poem_type=PoemType.CINQUAIN,
            lines=5,
            syllable_pattern=[2, 4, 6, 8, 2],
            special_rules={
                'diamond_shape': True,
                'building_intensity': True,
                'single_theme': True
            }
        )
    }
    
    @classmethod
    def get_structure(cls, poem_type: PoemType) -> PoemStructure:
        """Get the structure definition for a poem type"""
        return cls.STRUCTURES.get(poem_type, cls.STRUCTURES[PoemType.FREE_VERSE])
    
    @classmethod
    def validate_poem(cls, poem_type: PoemType, content: str) -> Dict[str, Any]:
        """Validate a poem against its structure requirements"""
        structure = cls.get_structure(poem_type)
        lines = content.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines
        
        validation = {
            'valid': True,
            'issues': [],
            'suggestions': [],
            'structure_analysis': {}
        }
        
        # Check line count
        if structure.lines > 0:
            if len(lines) != structure.lines:
                validation['valid'] = False
                validation['issues'].append(f"Expected {structure.lines} lines, got {len(lines)}")
        
        # Check syllable pattern
        if structure.syllable_pattern:
            syllable_counts = [SyllableCounter.count_line_syllables(line) for line in lines]
            validation['structure_analysis']['syllable_counts'] = syllable_counts
            
            for i, (actual, expected) in enumerate(zip(syllable_counts, structure.syllable_pattern)):
                if actual != expected:
                    validation['issues'].append(
                        f"Line {i+1}: Expected {expected} syllables, got {actual}"
                    )
                    if abs(actual - expected) <= 1:
                        validation['suggestions'].append(
                            f"Line {i+1} is close - try adjusting by {expected - actual} syllables"
                        )
        
        # Check rhyme scheme
        if structure.rhyme_scheme:
            rhyme_analysis = RhymeAnalyzer.analyze_rhyme_scheme(lines)
            validation['structure_analysis']['rhyme_analysis'] = rhyme_analysis
            
            expected_scheme = structure.rhyme_scheme.value.replace(' ', '')
            actual_scheme = rhyme_analysis['scheme']
            
            if actual_scheme != expected_scheme:
                validation['issues'].append(
                    f"Rhyme scheme mismatch: expected {expected_scheme}, got {actual_scheme}"
                )
        
        # Type-specific validations
        if poem_type == PoemType.ACROSTIC:
            validation.update(cls._validate_acrostic(lines, structure))
        elif poem_type == PoemType.HAIKU:
            validation.update(cls._validate_haiku(lines, structure))
        elif poem_type == PoemType.SONNET:
            validation.update(cls._validate_sonnet(lines, structure))
        
        return validation
    
    @classmethod
    def _validate_acrostic(cls, lines: List[str], structure: PoemStructure) -> Dict[str, Any]:
        """Validate acrostic-specific rules"""
        return {'acrostic_word': ''.join(line[0].upper() for line in lines if line)}
    
    @classmethod
    def _validate_haiku(cls, lines: List[str], structure: PoemStructure) -> Dict[str, Any]:
        """Validate haiku-specific rules"""
        analysis = {}
        
        # Check for nature imagery
        nature_words = ['sun', 'moon', 'tree', 'flower', 'rain', 'snow', 'wind', 'sea', 'mountain', 'river']
        content = ' '.join(lines).lower()
        nature_found = any(word in content for word in nature_words)
        analysis['nature_imagery'] = nature_found
        
        if not nature_found:
            analysis['suggestions'] = analysis.get('suggestions', [])
            analysis['suggestions'].append("Consider adding nature imagery for traditional haiku")
        
        return analysis
    
    @classmethod
    def _validate_sonnet(cls, lines: List[str], structure: PoemStructure) -> Dict[str, Any]:
        """Validate sonnet-specific rules"""
        analysis = {}
        
        # Check for volta (turn) around line 9
        if len(lines) >= 9:
            volta_indicators = ['but', 'yet', 'however', 'though', 'still', 'nevertheless']
            line_9 = lines[8].lower()  # Line 9 (0-indexed)
            volta_found = any(indicator in line_9 for indicator in volta_indicators)
            analysis['volta_present'] = volta_found
            
            if not volta_found:
                analysis['suggestions'] = analysis.get('suggestions', [])
                analysis['suggestions'].append("Consider adding a 'turn' or shift in argument around line 9")
        
        return analysis

class PoemGenerator:
    """Main poem generation engine"""
    
    def __init__(self, db_path: str = "soulbridge.db"):
        self.db_path = db_path
        self.structure_manager = PoemStructureManager()
        self.syllable_counter = SyllableCounter()
        self.rhyme_analyzer = RhymeAnalyzer()
        self.init_database()
    
    def init_database(self):
        """Initialize poem storage database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS generated_poems (
                        poem_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        poem_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        theme TEXT,
                        mood TEXT,
                        language TEXT DEFAULT 'en',
                        structure_data TEXT,
                        syllable_counts TEXT,
                        rhyme_analysis TEXT,
                        generation_metadata TEXT,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_poems_user ON generated_poems (user_id)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_poems_type ON generated_poems (poem_type)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_poems_theme ON generated_poems (theme)
                ''')
                
                conn.commit()
                logger.info("✅ Poem database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize poem database: {e}")
    
    def generate_poem(
        self,
        poem_type: PoemType,
        theme: str,
        mood: str = "neutral",
        language: str = "en",
        user_id: str = None,
        custom_word: str = None,  # For acrostics
        additional_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a poem of the specified type"""
        
        try:
            structure = self.structure_manager.get_structure(poem_type)
            
            # Generate poem content based on type
            if poem_type == PoemType.HAIKU:
                poem_content = self._generate_haiku(theme, mood, language)
            elif poem_type == PoemType.SONNET:
                poem_content = self._generate_sonnet(theme, mood, language)
            elif poem_type == PoemType.FREE_VERSE:
                poem_content = self._generate_free_verse(theme, mood, language)
            elif poem_type == PoemType.ACROSTIC:
                if not custom_word:
                    return {'success': False, 'error': 'Acrostic poems require a custom word'}
                poem_content = self._generate_acrostic(custom_word, theme, mood, language)
            elif poem_type == PoemType.LIMERICK:
                poem_content = self._generate_limerick(theme, mood, language)
            elif poem_type == PoemType.TANKA:
                poem_content = self._generate_tanka(theme, mood, language)
            elif poem_type == PoemType.CINQUAIN:
                poem_content = self._generate_cinquain(theme, mood, language)
            else:
                return {'success': False, 'error': f'Unsupported poem type: {poem_type.value}'}
            
            # Analyze the generated poem
            lines = poem_content.strip().split('\n')
            syllable_counts = [self.syllable_counter.count_line_syllables(line) for line in lines]
            rhyme_analysis = self.rhyme_analyzer.analyze_rhyme_scheme(lines)
            
            # Create poem object
            poem_id = hashlib.md5(f"{poem_content}{theme}{mood}{datetime.now()}".encode()).hexdigest()[:16]
            
            generated_poem = GeneratedPoem(
                poem_id=poem_id,
                poem_type=poem_type,
                title=self._generate_title(poem_type, theme, mood),
                content=poem_content,
                structure=structure,
                theme=theme,
                mood=mood,
                language=language,
                syllable_count=syllable_counts,
                rhyme_analysis=rhyme_analysis,
                created_date=datetime.now(timezone.utc),
                generation_metadata={
                    'custom_word': custom_word,
                    'additional_params': additional_params or {},
                    'generation_method': 'template_based'  # Would be 'ai_generated' with LLM
                }
            )
            
            # Validate the poem
            validation = self.structure_manager.validate_poem(poem_type, poem_content)
            
            # Store the poem
            if self._store_poem(generated_poem, user_id):
                return {
                    'success': True,
                    'poem': generated_poem.to_dict(),
                    'validation': validation
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to store generated poem'
                }
                
        except Exception as e:
            logger.error(f"❌ Poem generation failed: {e}")
            return {
                'success': False,
                'error': f'Generation failed: {str(e)}'
            }
    
    def _generate_haiku(self, theme: str, mood: str, language: str) -> str:
        """Generate a haiku (5-7-5 syllable pattern)"""
        
        # Theme-based word collections
        nature_themes = {
            'spring': ['cherry', 'blossom', 'gentle', 'breeze', 'awakening', 'fresh', 'bloom', 'green'],
            'summer': ['warm', 'sunshine', 'flowing', 'river', 'buzzing', 'bees', 'bright', 'golden'],
            'autumn': ['falling', 'leaves', 'crisp', 'air', 'harvest', 'orange', 'peaceful', 'wind'],
            'winter': ['snow', 'falls', 'silent', 'white', 'cold', 'bare', 'branches', 'frozen'],
            'ocean': ['waves', 'crash', 'endless', 'blue', 'seagulls', 'call', 'salty', 'breeze'],
            'mountain': ['peaks', 'rise', 'misty', 'clouds', 'eagle', 'soars', 'ancient', 'stone']
        }
        
        # Get theme words or default
        theme_words = nature_themes.get(theme.lower(), ['nature', 'peaceful', 'quiet', 'serene', 'moment', 'time', 'beauty', 'life'])
        
        # Template-based generation (in production, would use LLM)
        haiku_templates = [
            f"{random.choice(theme_words).title()} {random.choice(['blooms', 'flows', 'stands'])}\n"
            f"{random.choice(['Gentle', 'Silent', 'Peaceful'])} {random.choice(theme_words)} {random.choice(['dancing', 'singing', 'whispers'])}\n"
            f"{random.choice(['Life', 'Time', 'Beauty'])} {random.choice(['unfolds', 'passes', 'remains'])}",
            
            f"{random.choice(theme_words).title()} {random.choice(['morning', 'evening', 'moments'])}\n"
            f"{random.choice(['Soft', 'Warm', 'Cool'])} {random.choice(theme_words)} {random.choice(['embraces', 'surrounds', 'comforts'])}\n"
            f"{random.choice(['Peace', 'Joy', 'Wonder'])} {random.choice(['settles', 'awakens', 'grows'])}",
        ]
        
        return random.choice(haiku_templates)
    
    def _generate_sonnet(self, theme: str, mood: str, language: str) -> str:
        """Generate a Shakespearean sonnet (14 lines, ABAB CDCD EFEF GG)"""
        
        # This is a simplified template-based approach
        # In production, would use sophisticated LLM generation
        
        return f"""When {theme} does call to weary hearts that yearn (A)
And {mood} emotions stir within the soul (B)
The gentle lessons that we come to learn (A)
Help us to see and play our destined role (B)

Through seasons of our life we journey far (C)
With {theme} as our guide through joy and pain (D)
Like sailors following a distant star (C)
We find that love and loss are not in vain (D)

The {mood} moments that define our days (E)
Are woven in a tapestry of time (F)
Where {theme} illuminates our mortal ways (E)
And turns our simple stories into rhyme (F)

So let us cherish what this life can bring (G)
And find in {theme} the song our hearts can sing (G)"""
    
    def _generate_free_verse(self, theme: str, mood: str, language: str) -> str:
        """Generate free verse poetry (no strict form)"""
        
        mood_styles = {
            'happy': ['bright', 'dancing', 'laughter', 'soaring', 'golden', 'celebration'],
            'sad': ['falling', 'shadow', 'tears', 'empty', 'silence', 'longing'],
            'angry': ['storm', 'thunder', 'blazing', 'fierce', 'burning', 'rage'],
            'peaceful': ['gentle', 'flowing', 'quiet', 'still', 'soft', 'calm'],
            'mysterious': ['hidden', 'whisper', 'shadow', 'secret', 'midnight', 'unknown']
        }
        
        style_words = mood_styles.get(mood.lower(), ['flowing', 'moving', 'changing', 'growing'])
        
        return f"""{theme.title()}
{random.choice(style_words)} through the corridors of time
where memory and dream
    intertwine

Like {random.choice(style_words)} water
finding its way
through stone
    and silence

We are all
    {random.choice(['searching', 'wandering', 'discovering', 'becoming'])}
in the vast landscape
of {theme}

{random.choice(['Sometimes', 'Often', 'Always'])} 
the {mood} moments
    reveal themselves
in the space between
heartbeats

And we {random.choice(['understand', 'realize', 'discover', 'know'])}
that {theme}
is not just a word
    but a way
        of being"""
    
    def _generate_acrostic(self, word: str, theme: str, mood: str, language: str) -> str:
        """Generate an acrostic poem using the given word"""
        
        word = word.upper().strip()
        if not word:
            return "Please provide a word for the acrostic poem."
        
        # Theme-based word collections for each letter
        theme_words = {
            'love': ['affection', 'beauty', 'caring', 'devotion', 'eternal', 'forever'],
            'nature': ['amazing', 'beautiful', 'caring', 'divine', 'endless', 'flowing'],
            'hope': ['aspiring', 'believing', 'courage', 'dreams', 'enduring', 'faith'],
            'peace': ['acceptance', 'balance', 'calm', 'divine', 'eternal', 'flowing']
        }
        
        base_words = theme_words.get(theme.lower(), ['amazing', 'beautiful', 'creative', 'dynamic', 'exceptional', 'fantastic'])
        
        lines = []
        for i, letter in enumerate(word):
            # Generate line starting with this letter
            if i < len(base_words):
                start_word = base_words[i]
                if not start_word.startswith(letter.lower()):
                    # Find or create a word starting with the letter
                    letter_words = {
                        'A': ['Amazing', 'Awesome', 'Alive', 'Always'],
                        'B': ['Beautiful', 'Bright', 'Bold', 'Brave'],
                        'C': ['Creative', 'Calm', 'Caring', 'Clear'],
                        'D': ['Divine', 'Dancing', 'Deep', 'Dreams'],
                        'E': ['Eternal', 'Endless', 'Every', 'Earth'],
                        'F': ['Forever', 'Flowing', 'Free', 'Finding'],
                        'G': ['Growing', 'Grace', 'Gentle', 'Glory'],
                        'H': ['Hope', 'Heart', 'Harmony', 'Healing'],
                        'I': ['Infinite', 'Inspiring', 'Inner', 'Illuminated'],
                        'J': ['Joyful', 'Journey', 'Just', 'Jubilant'],
                        'K': ['Kind', 'Knowledge', 'Knowing', 'Keeping'],
                        'L': ['Love', 'Light', 'Life', 'Living'],
                        'M': ['Magical', 'Moments', 'Music', 'Mystery'],
                        'N': ['Nature', 'Never', 'New', 'Nurturing'],
                        'O': ['Ocean', 'Open', 'One', 'Overwhelming'],
                        'P': ['Peace', 'Pure', 'Power', 'Precious'],
                        'Q': ['Quiet', 'Quest', 'Quality', 'Quick'],
                        'R': ['Radiant', 'Rising', 'River', 'Real'],
                        'S': ['Serene', 'Strong', 'Sacred', 'Shining'],
                        'T': ['Timeless', 'True', 'Together', 'Trust'],
                        'U': ['Understanding', 'Universe', 'Unique', 'Unity'],
                        'V': ['Vibrant', 'Vision', 'Voice', 'Victory'],
                        'W': ['Wisdom', 'Wonder', 'Warm', 'Wholeness'],
                        'X': ['eXtraordinary', 'eXcellence', 'eXpression', 'eXploring'],
                        'Y': ['Yearning', 'Yes', 'Youth', 'Yesterday'],
                        'Z': ['Zen', 'Zeal', 'Zone', 'Zealous']
                    }
                    
                    start_word = random.choice(letter_words.get(letter, [f"{letter}..."]))
            
            # Create full line
            line_templates = [
                f"{start_word} in every moment of {theme}",
                f"{start_word} like the {mood} feeling inside",
                f"{start_word} through all of life's journey",
                f"{start_word} bringing {theme} to the world",
                f"{start_word} with {mood} energy and grace"
            ]
            
            lines.append(random.choice(line_templates))
        
        return '\n'.join(lines)
    
    def _generate_limerick(self, theme: str, mood: str, language: str) -> str:
        """Generate a humorous limerick (AABBA rhyme scheme)"""
        
        return f"""There once was a {theme} so {mood}
Who decided to dance in the mood
    They spun all around
    Without making a sound
And discovered that joy was the food"""
    
    def _generate_tanka(self, theme: str, mood: str, language: str) -> str:
        """Generate a tanka (5-7-5-7-7 syllable pattern)"""
        
        return f"""{theme.title()} calls softly
In the {mood} morning light
Peaceful moments
Dancing through time and space
Bringing wisdom to the heart"""
    
    def _generate_cinquain(self, theme: str, mood: str, language: str) -> str:
        """Generate a cinquain (2-4-6-8-2 syllable pattern)"""
        
        return f"""{theme.title()[:6]}
{mood.title()} and bright
{random.choice(['Growing', 'Flowing', 'Dancing'])} through life's journey
{random.choice(['Bringing', 'Creating', 'Sharing'])} {mood} {random.choice(['moments', 'feelings', 'memories'])} every day
Pure joy"""
    
    def _generate_title(self, poem_type: PoemType, theme: str, mood: str) -> str:
        """Generate an appropriate title for the poem"""
        
        type_titles = {
            PoemType.HAIKU: [f"{theme.title()} Haiku", f"{mood.title()} Moment", "Three Lines"],
            PoemType.SONNET: [f"Sonnet of {theme.title()}", f"{mood.title()} Reflections", "Fourteen Lines"],
            PoemType.FREE_VERSE: [f"{theme.title()} Unbound", f"{mood.title()} Freedom", "Without Walls"],
            PoemType.ACROSTIC: [f"{theme.title()} Spelled Out", "Letter by Letter", "Hidden Message"],
            PoemType.LIMERICK: [f"A {mood.title()} Tale", "Five Line Story", "Humorous Verse"],
            PoemType.TANKA: [f"{theme.title()} in Five", f"{mood.title()} Tanka", "Japanese Form"],
            PoemType.CINQUAIN: [f"{theme.title()} Diamond", "Five Line Gem", f"{mood.title()} Shape"]
        }
        
        titles = type_titles.get(poem_type, [f"{theme.title()}", f"{mood.title()} Poem", "Untitled"])
        return random.choice(titles)
    
    def _store_poem(self, poem: GeneratedPoem, user_id: str = None) -> bool:
        """Store generated poem in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO generated_poems (
                        poem_id, user_id, poem_type, title, content, theme, mood,
                        language, structure_data, syllable_counts, rhyme_analysis,
                        generation_metadata, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    poem.poem_id,
                    user_id,
                    poem.poem_type.value,
                    poem.title,
                    poem.content,
                    poem.theme,
                    poem.mood,
                    poem.language,
                    json.dumps(asdict(poem.structure)),
                    json.dumps(poem.syllable_count),
                    json.dumps(poem.rhyme_analysis),
                    json.dumps(poem.generation_metadata),
                    poem.created_date.isoformat()
                ))
                
                conn.commit()
                logger.info(f"✅ Stored poem: {poem.title}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store poem: {e}")
            return False
    
    def get_user_poems(self, user_id: str, poem_type: PoemType = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve user's generated poems"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if poem_type:
                    cursor = conn.execute('''
                        SELECT * FROM generated_poems 
                        WHERE user_id = ? AND poem_type = ?
                        ORDER BY created_date DESC LIMIT ?
                    ''', (user_id, poem_type.value, limit))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM generated_poems 
                        WHERE user_id = ?
                        ORDER BY created_date DESC LIMIT ?
                    ''', (user_id, limit))
                
                poems = []
                for row in cursor.fetchall():
                    poems.append({
                        'poem_id': row[0],
                        'poem_type': row[2],
                        'title': row[3],
                        'content': row[4],
                        'theme': row[5],
                        'mood': row[6],
                        'language': row[7],
                        'created_date': row[12]
                    })
                
                return poems
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve user poems: {e}")
            return []

# Service factory function
def create_poem_generator_service(db_path: str = "soulbridge.db") -> PoemGenerator:
    """Create and configure poem generator service"""
    try:
        service = PoemGenerator(db_path)
        logger.info("✅ Poem Generator Service initialized")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize poem generator service: {e}")
        raise