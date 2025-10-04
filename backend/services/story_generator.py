"""
Story Generator Service
Advanced narrative generation and analysis
"""

import logging
import json
import re
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import random
from database_utils import format_query

logger = logging.getLogger(__name__)

class StoryGenre(Enum):
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    THRILLER = "thriller"
    HORROR = "horror"
    DRAMA = "drama"
    COMEDY = "comedy"
    ADVENTURE = "adventure"
    HISTORICAL = "historical"
    WESTERN = "western"
    LITERARY = "literary"

class StoryLength(Enum):
    FLASH_FICTION = "flash_fiction"  # 50-300 words
    SHORT_STORY = "short_story"      # 500-2000 words
    NOVELETTE = "novelette"          # 3000-7500 words
    NOVELLA = "novella"              # 10000-25000 words
    NOVEL_OUTLINE = "novel_outline"   # Chapter-by-chapter outline

class NarrativeStructure(Enum):
    THREE_ACT = "three_act"
    HEROS_JOURNEY = "heros_journey"
    FREYTAG_PYRAMID = "freytag_pyramid"
    SEVEN_POINT = "seven_point"
    SAVE_THE_CAT = "save_the_cat"
    FICHTEAN_CURVE = "fichtean_curve"

@dataclass
class Character:
    name: str
    role: str  # protagonist, antagonist, mentor, ally, etc.
    archetype: str
    motivation: str
    conflict: str
    background: str
    traits: List[str]
    age: Optional[int] = None
    occupation: Optional[str] = None

@dataclass
class PlotPoint:
    name: str
    description: str
    chapter: int
    word_position: float  # 0.0 to 1.0 position in story
    character_focus: List[str]
    conflict_type: str

@dataclass
class StoryStructure:
    structure_type: NarrativeStructure
    plot_points: List[PlotPoint]
    act_breaks: List[float]  # Position percentages for act breaks
    character_arcs: Dict[str, List[str]]  # Character development stages
    themes: List[str]
    subplots: List[str]

@dataclass
class StoryOutline:
    title: str
    genre: StoryGenre
    length: StoryLength
    premise: str
    characters: List[Character]
    structure: StoryStructure
    chapters: List[Dict[str, Any]]
    word_count_target: int
    themes: List[str]
    target_audience: str
    setting: Dict[str, str]  # time, place, world_building

@dataclass
class StoryAnalysis:
    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_sentence_length: float
    readability_score: float
    pov: str  # first, second, third_limited, third_omniscient
    tense: str  # past, present, future
    dialogue_percentage: float
    character_mentions: Dict[str, int]
    theme_indicators: List[str]
    plot_structure_analysis: Dict[str, Any]
    pacing_analysis: Dict[str, float]
    conflict_types: List[str]

class CharacterGenerator:
    """Generate and manage story characters"""
    
    def __init__(self):
        self.archetypes = {
            "hero": ["brave", "determined", "flawed", "growing"],
            "mentor": ["wise", "experienced", "guiding", "sacrificial"],
            "threshold_guardian": ["challenging", "testing", "protective", "loyal"],
            "herald": ["messenger", "catalyst", "announcing", "informative"],
            "shapeshifter": ["mysterious", "changing", "unpredictable", "complex"],
            "shadow": ["opposing", "dark", "threatening", "powerful"],
            "ally": ["supportive", "helpful", "loyal", "encouraging"],
            "trickster": ["humorous", "disruptive", "clever", "chaotic"]
        }
        
        self.motivations = [
            "seek revenge", "find love", "gain power", "discover truth",
            "protect family", "achieve fame", "escape fate", "find belonging",
            "overcome fear", "right a wrong", "discover identity", "save world"
        ]
        
        self.conflicts = [
            "internal struggle", "family pressure", "moral dilemma", "past trauma",
            "competing desires", "external threat", "betrayal", "loss of identity",
            "forbidden love", "impossible choice", "hidden secret", "destiny vs freedom"
        ]

    def generate_character(self, role: str, genre: StoryGenre, name: Optional[str] = None) -> Character:
        """Generate a character based on role and genre"""
        
        # Select archetype based on role
        archetype_map = {
            "protagonist": ["hero", "herald"],
            "antagonist": ["shadow", "shapeshifter"],
            "mentor": ["mentor", "threshold_guardian"],
            "ally": ["ally", "threshold_guardian"],
            "love_interest": ["shapeshifter", "ally"],
            "comic_relief": ["trickster", "ally"]
        }
        
        possible_archetypes = archetype_map.get(role, ["ally"])
        archetype = random.choice(possible_archetypes)
        
        # Generate name if not provided
        if not name:
            name = self._generate_name(genre)
        
        # Select traits based on archetype and genre
        base_traits = self.archetypes[archetype].copy()
        genre_traits = self._get_genre_traits(genre)
        traits = base_traits + random.sample(genre_traits, 2)
        
        return Character(
            name=name,
            role=role,
            archetype=archetype,
            motivation=random.choice(self.motivations),
            conflict=random.choice(self.conflicts),
            background=f"A {archetype} character driven by the need to {random.choice(self.motivations).lower()}",
            traits=traits[:5],
            age=random.randint(18, 65) if role != "mentor" else random.randint(40, 80),
            occupation=self._generate_occupation(genre, role)
        )

    def _generate_name(self, genre: StoryGenre) -> str:
        """Generate appropriate name for genre"""
        fantasy_names = ["Aria", "Thorne", "Lyra", "Kael", "Seren", "Darius", "Mira", "Orion"]
        sci_fi_names = ["Zara", "Nexus", "Echo", "Vex", "Nova", "Kai", "Lux", "Raven"]
        modern_names = ["Alex", "Jordan", "Sam", "Taylor", "Casey", "River", "Sage", "Blake"]
        historical_names = ["Eleanor", "Sebastian", "Victoria", "Edmund", "Charlotte", "Theodore"]
        
        genre_names = {
            StoryGenre.FANTASY: fantasy_names,
            StoryGenre.SCI_FI: sci_fi_names,
            StoryGenre.HISTORICAL: historical_names,
        }
        
        names = genre_names.get(genre, modern_names)
        return random.choice(names)

    def _get_genre_traits(self, genre: StoryGenre) -> List[str]:
        """Get traits specific to genre"""
        traits = {
            StoryGenre.FANTASY: ["magical", "mystical", "ancient", "prophetic"],
            StoryGenre.SCI_FI: ["technological", "analytical", "futuristic", "logical"],
            StoryGenre.MYSTERY: ["observant", "suspicious", "methodical", "intuitive"],
            StoryGenre.ROMANCE: ["passionate", "romantic", "emotional", "caring"],
            StoryGenre.HORROR: ["haunted", "fearful", "resilient", "traumatized"],
            StoryGenre.THRILLER: ["paranoid", "resourceful", "quick-thinking", "tense"]
        }
        return traits.get(genre, ["determined", "complex", "relatable", "flawed"])

    def _generate_occupation(self, genre: StoryGenre, role: str) -> str:
        """Generate appropriate occupation"""
        occupations = {
            StoryGenre.FANTASY: ["Knight", "Wizard", "Merchant", "Thief", "Scholar"],
            StoryGenre.SCI_FI: ["Engineer", "Pilot", "Scientist", "Trader", "Explorer"],
            StoryGenre.MYSTERY: ["Detective", "Journalist", "Lawyer", "Professor", "Doctor"],
            StoryGenre.ROMANCE: ["Teacher", "Artist", "Chef", "Musician", "Writer"]
        }
        
        options = occupations.get(genre, ["Professional", "Student", "Entrepreneur"])
        return random.choice(options)

class StructureAnalyzer:
    """Analyze and validate story structure"""
    
    def __init__(self):
        self.structure_templates = {
            NarrativeStructure.THREE_ACT: {
                "act_breaks": [0.25, 0.75],
                "plot_points": [
                    {"name": "Inciting Incident", "position": 0.125},
                    {"name": "First Plot Point", "position": 0.25},
                    {"name": "Midpoint", "position": 0.5},
                    {"name": "Second Plot Point", "position": 0.75},
                    {"name": "Climax", "position": 0.9}
                ]
            },
            NarrativeStructure.HEROS_JOURNEY: {
                "act_breaks": [0.2, 0.8],
                "plot_points": [
                    {"name": "Call to Adventure", "position": 0.1},
                    {"name": "Crossing Threshold", "position": 0.2},
                    {"name": "Tests & Trials", "position": 0.4},
                    {"name": "Ordeal", "position": 0.6},
                    {"name": "Reward", "position": 0.7},
                    {"name": "Resurrection", "position": 0.9}
                ]
            },
            NarrativeStructure.FREYTAG_PYRAMID: {
                "act_breaks": [0.2, 0.5, 0.8],
                "plot_points": [
                    {"name": "Exposition", "position": 0.1},
                    {"name": "Rising Action", "position": 0.35},
                    {"name": "Climax", "position": 0.5},
                    {"name": "Falling Action", "position": 0.65},
                    {"name": "Denouement", "position": 0.9}
                ]
            }
        }

    def create_structure(self, structure_type: NarrativeStructure, 
                        genre: StoryGenre, themes: List[str]) -> StoryStructure:
        """Create story structure template"""
        
        template = self.structure_templates[structure_type]
        
        # Generate plot points
        plot_points = []
        for i, point_template in enumerate(template["plot_points"]):
            plot_point = PlotPoint(
                name=point_template["name"],
                description=f"Key story moment: {point_template['name']}",
                chapter=max(1, int(point_template["position"] * 10)),  # Rough chapter estimate
                word_position=point_template["position"],
                character_focus=["protagonist"],
                conflict_type=self._get_conflict_type(point_template["name"], genre)
            )
            plot_points.append(plot_point)
        
        # Generate character arcs
        character_arcs = {
            "protagonist": ["introduction", "challenge", "growth", "transformation", "resolution"],
            "antagonist": ["opposition", "escalation", "confrontation", "defeat"],
            "mentor": ["guidance", "teaching", "sacrifice or departure"]
        }
        
        return StoryStructure(
            structure_type=structure_type,
            plot_points=plot_points,
            act_breaks=template["act_breaks"],
            character_arcs=character_arcs,
            themes=themes,
            subplots=self._generate_subplots(genre, len(themes))
        )

    def _get_conflict_type(self, plot_point_name: str, genre: StoryGenre) -> str:
        """Determine conflict type for plot point"""
        conflict_types = {
            "Inciting Incident": "external",
            "Call to Adventure": "internal",
            "Climax": "both",
            "Ordeal": "external",
            "Midpoint": "internal"
        }
        return conflict_types.get(plot_point_name, "both")

    def _generate_subplots(self, genre: StoryGenre, theme_count: int) -> List[str]:
        """Generate relevant subplots"""
        subplot_templates = {
            StoryGenre.ROMANCE: ["love triangle", "family approval", "past relationship"],
            StoryGenre.MYSTERY: ["red herring", "personal stakes", "witness protection"],
            StoryGenre.FANTASY: ["prophecy fulfillment", "magical training", "kingdom politics"],
            StoryGenre.SCI_FI: ["technology ethics", "alien contact", "time paradox"]
        }
        
        templates = subplot_templates.get(genre, ["personal growth", "relationship", "external challenge"])
        return random.sample(templates, min(theme_count, 3))

class StoryAnalyzer:
    """Analyze existing story text"""
    
    def __init__(self):
        self.pov_patterns = {
            "first": [r'\bI\b', r'\bme\b', r'\bmy\b', r'\bmine\b'],
            "second": [r'\byou\b', r'\byour\b', r'\byours\b'],
            "third_limited": [r'\bhe\b', r'\bshe\b', r'\bhis\b', r'\bher\b'],
            "third_omniscient": [r'\bhe\b.*thought', r'\bshe\b.*felt', r'\beveryone\b']
        }
        
        self.dialogue_pattern = r'"[^"]*"'
        self.sentence_pattern = r'[.!?]+\s*'
        
    def analyze_story(self, content: str, title: Optional[str] = None) -> StoryAnalysis:
        """Perform comprehensive story analysis"""
        
        # Basic metrics
        words = content.split()
        word_count = len(words)
        sentences = re.split(self.sentence_pattern, content)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraphs = content.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Calculate averages
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Readability (simplified Flesch score)
        avg_words_per_sentence = avg_sentence_length
        syllables = self._estimate_syllables(content)
        avg_syllables_per_word = syllables / max(word_count, 1)
        readability = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        readability = max(0, min(100, readability))
        
        # POV analysis
        pov = self._analyze_pov(content)
        
        # Tense analysis
        tense = self._analyze_tense(content)
        
        # Dialogue percentage
        dialogue_matches = re.findall(self.dialogue_pattern, content)
        dialogue_words = sum(len(match.split()) for match in dialogue_matches)
        dialogue_percentage = (dialogue_words / max(word_count, 1)) * 100
        
        # Character mentions
        character_mentions = self._find_character_mentions(content)
        
        # Theme indicators
        theme_indicators = self._identify_themes(content)
        
        # Plot structure analysis
        plot_analysis = self._analyze_plot_structure(content)
        
        # Pacing analysis
        pacing_analysis = self._analyze_pacing(content)
        
        # Conflict types
        conflict_types = self._identify_conflicts(content)
        
        return StoryAnalysis(
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            avg_sentence_length=round(avg_sentence_length, 2),
            readability_score=round(readability, 2),
            pov=pov,
            tense=tense,
            dialogue_percentage=round(dialogue_percentage, 2),
            character_mentions=character_mentions,
            theme_indicators=theme_indicators,
            plot_structure_analysis=plot_analysis,
            pacing_analysis=pacing_analysis,
            conflict_types=conflict_types
        )

    def _estimate_syllables(self, text: str) -> int:
        """Estimate syllable count using simple heuristics"""
        words = re.findall(r'\b\w+\b', text.lower())
        syllables = 0
        
        for word in words:
            # Count vowel groups
            vowel_groups = re.findall(r'[aeiouy]+', word)
            count = len(vowel_groups)
            
            # Adjust for silent e
            if word.endswith('e') and count > 1:
                count -= 1
            
            # Minimum 1 syllable per word
            syllables += max(1, count)
        
        return syllables

    def _analyze_pov(self, content: str) -> str:
        """Determine point of view"""
        content_lower = content.lower()
        pov_scores = {}
        
        for pov, patterns in self.pov_patterns.items():
            score = sum(len(re.findall(pattern, content_lower)) for pattern in patterns)
            pov_scores[pov] = score
        
        return max(pov_scores, key=pov_scores.get) if pov_scores else "unknown"

    def _analyze_tense(self, content: str) -> str:
        """Determine primary tense"""
        past_verbs = len(re.findall(r'\b\w+ed\b|\bwas\b|\bwere\b|\bhad\b', content.lower()))
        present_verbs = len(re.findall(r'\bis\b|\bare\b|\bam\b|\bhas\b|\bhave\b', content.lower()))
        
        return "past" if past_verbs > present_verbs else "present"

    def _find_character_mentions(self, content: str) -> Dict[str, int]:
        """Find character names and mention counts"""
        # Look for capitalized words that appear multiple times (likely names)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        word_counts = {}
        
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Filter for likely character names (mentioned 3+ times)
        return {name: count for name, count in word_counts.items() if count >= 3}

    def _identify_themes(self, content: str) -> List[str]:
        """Identify potential themes from content"""
        theme_keywords = {
            "love": ["love", "heart", "romance", "relationship", "kiss"],
            "death": ["death", "die", "kill", "murder", "grave", "funeral"],
            "power": ["power", "control", "authority", "rule", "command"],
            "family": ["family", "mother", "father", "son", "daughter", "parent"],
            "friendship": ["friend", "loyal", "trust", "companion", "ally"],
            "betrayal": ["betray", "lie", "deceive", "cheat", "false"],
            "redemption": ["forgive", "redeem", "atone", "sorry", "guilt"],
            "coming_of_age": ["grow", "mature", "adult", "childhood", "learn"]
        }
        
        content_lower = content.lower()
        themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        return themes

    def _analyze_plot_structure(self, content: str) -> Dict[str, Any]:
        """Analyze plot structure elements"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Rough structure analysis
        opening_strength = self._analyze_opening(paragraphs[0] if paragraphs else "")
        conflict_presence = self._detect_conflict_markers(content)
        resolution_present = self._detect_resolution_markers(content)
        
        return {
            "opening_strength": opening_strength,
            "conflict_markers": conflict_presence,
            "resolution_present": resolution_present,
            "paragraph_count": len(paragraphs),
            "estimated_acts": min(3, max(1, len(paragraphs) // 3))
        }

    def _analyze_pacing(self, content: str) -> Dict[str, float]:
        """Analyze story pacing"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return {"overall": 0.0, "variance": 0.0}
        
        # Analyze sentence lengths as pacing indicator
        paragraph_paces = []
        for paragraph in paragraphs:
            sentences = re.split(self.sentence_pattern, paragraph)
            avg_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
            paragraph_paces.append(avg_length)
        
        overall_pace = sum(paragraph_paces) / len(paragraph_paces)
        pace_variance = sum((p - overall_pace) ** 2 for p in paragraph_paces) / len(paragraph_paces)
        
        return {
            "overall": round(overall_pace, 2),
            "variance": round(pace_variance, 2),
            "sections": len(paragraphs)
        }

    def _analyze_opening(self, opening: str) -> float:
        """Analyze opening paragraph strength"""
        if not opening:
            return 0.0
        
        # Look for strong opening elements
        hooks = ["dialogue", "action", "question", "mystery"]
        score = 0.0
        
        if opening.startswith('"'):
            score += 0.3  # Dialogue opening
        if any(word in opening.lower() for word in ["suddenly", "crash", "run", "fight"]):
            score += 0.3  # Action opening
        if "?" in opening:
            score += 0.2  # Question
        if any(word in opening.lower() for word in ["strange", "weird", "mystery", "unknown"]):
            score += 0.2  # Mystery
        
        return min(1.0, score)

    def _detect_conflict_markers(self, content: str) -> List[str]:
        """Detect types of conflict present"""
        conflicts = []
        content_lower = content.lower()
        
        conflict_indicators = {
            "internal": ["thought", "wondered", "felt", "emotion", "decision"],
            "interpersonal": ["argue", "fight", "disagree", "conflict", "tension"],
            "external": ["enemy", "threat", "danger", "attack", "challenge"],
            "societal": ["society", "system", "law", "rule", "authority"]
        }
        
        for conflict_type, indicators in conflict_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                conflicts.append(conflict_type)
        
        return conflicts

    def _detect_resolution_markers(self, content: str) -> bool:
        """Detect if story has resolution"""
        resolution_words = ["resolved", "ended", "finally", "conclusion", "peace", "settled"]
        content_lower = content.lower()
        return any(word in content_lower for word in resolution_words)

    def _identify_conflicts(self, content: str) -> List[str]:
        """Identify conflict types in story"""
        return self._detect_conflict_markers(content)

class StoryDatabase:
    """Manage story data persistence"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                length_type TEXT NOT NULL,
                content TEXT NOT NULL,
                outline TEXT,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER,
                character_data TEXT NOT NULL,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                outline_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

    def save_story(self, user_id: str, title: str, genre: StoryGenre, 
                  length_type: StoryLength, content: str, 
                  outline: Optional[StoryOutline] = None,
                  analysis: Optional[StoryAnalysis] = None) -> int:
        """Save a story to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        outline_json = json.dumps(asdict(outline)) if outline else None
        analysis_json = json.dumps(asdict(analysis)) if analysis else None
        
        cursor.execute("""
            INSERT INTO stories (user_id, title, genre, length_type, content, outline, analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, genre.value, length_type.value, content, outline_json, analysis_json))
        
        story_id = cursor.lastrowid
        
        # Save characters if outline exists
        if outline and outline.characters:
            for character in outline.characters:
                character_json = json.dumps(asdict(character))
                cursor.execute(format_query("""
                    INSERT INTO story_characters (story_id, character_data)
                    VALUES (?, ?)
                """), (story_id, character_json))
        
        conn.commit()
        conn.close()
        
        return story_id

    def get_user_stories(self, user_id: str, genre: Optional[StoryGenre] = None, 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's stories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if genre:
            cursor.execute(format_query("""
                SELECT id, title, genre, length_type, created_at, 
                       LENGTH(content) as word_count
                FROM stories 
                WHERE user_id = ? AND genre = ?
                ORDER BY created_at DESC LIMIT ?
            """), (user_id, genre.value, limit))
        else:
            cursor.execute(format_query("""
                SELECT id, title, genre, length_type, created_at,
                       LENGTH(content) as word_count
                FROM stories 
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """), (user_id, limit))
        
        stories = []
        for row in cursor.fetchall():
            stories.append({
                'id': row[0],
                'title': row[1],
                'genre': row[2],
                'length_type': row[3],
                'created_at': row[4],
                'word_count': row[5]
            })
        
        conn.close()
        return stories

    def save_outline(self, user_id: str, outline: StoryOutline) -> int:
        """Save story outline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        outline_json = json.dumps(asdict(outline))
        
        cursor.execute(format_query("""
            INSERT INTO story_outlines (user_id, title, genre, outline_data)
            VALUES (?, ?, ?, ?)
        """), (user_id, outline.title, outline.genre.value, outline_json))
        
        outline_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return outline_id

class StoryGenerator:
    """Main story generation service"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.character_generator = CharacterGenerator()
        self.structure_analyzer = StructureAnalyzer()
        self.story_analyzer = StoryAnalyzer()
        self.database = StoryDatabase(db_path)
        
        # Story templates for generation
        self.story_templates = {
            StoryGenre.FANTASY: {
                "opening_templates": [
                    "In the realm of {setting}, {protagonist} discovered {magical_element}...",
                    "The ancient prophecy spoke of {protagonist}, who would {quest_goal}...",
                    "{protagonist} never believed in magic until {inciting_incident}..."
                ],
                "conflict_templates": [
                    "The dark force of {antagonist} threatened to {threat}",
                    "A curse upon {setting} could only be broken by {solution}",
                    "The {magical_item} held the key to {resolution}"
                ]
            },
            StoryGenre.SCI_FI: {
                "opening_templates": [
                    "In the year {year}, {protagonist} made a discovery that would change {scope}...",
                    "The first transmission from {alien_source} contained {mysterious_message}...",
                    "{protagonist} awoke from cryosleep to find {shocking_revelation}..."
                ],
                "conflict_templates": [
                    "The AI system {ai_name} had evolved beyond {original_purpose}",
                    "Time was running out before {catastrophic_event}",
                    "The alien artifact revealed {dangerous_truth}"
                ]
            }
        }

    def generate_outline(self, genre: StoryGenre, length: StoryLength, 
                        premise: str, themes: List[str], 
                        structure_type: NarrativeStructure = NarrativeStructure.THREE_ACT,
                        character_count: int = 3) -> StoryOutline:
        """Generate comprehensive story outline"""
        
        # Generate characters
        characters = []
        character_roles = ["protagonist", "antagonist", "mentor", "ally", "love_interest"][:character_count]
        
        for role in character_roles:
            character = self.character_generator.generate_character(role, genre)
            characters.append(character)
        
        # Create story structure
        structure = self.structure_analyzer.create_structure(structure_type, genre, themes)
        
        # Determine target word count
        word_count_targets = {
            StoryLength.FLASH_FICTION: 200,
            StoryLength.SHORT_STORY: 1500,
            StoryLength.NOVELETTE: 5000,
            StoryLength.NOVELLA: 17500,
            StoryLength.NOVEL_OUTLINE: 80000
        }
        
        target_words = word_count_targets[length]
        
        # Generate chapters based on structure
        chapters = self._generate_chapters(structure, target_words, characters)
        
        # Create setting
        setting = self._generate_setting(genre, premise)
        
        # Generate title
        title = self._generate_title(genre, premise, characters[0].name if characters else "Hero")
        
        return StoryOutline(
            title=title,
            genre=genre,
            length=length,
            premise=premise,
            characters=characters,
            structure=structure,
            chapters=chapters,
            word_count_target=target_words,
            themes=themes,
            target_audience=self._determine_target_audience(genre, themes),
            setting=setting
        )

    def generate_story_content(self, outline: StoryOutline, chapter_number: Optional[int] = None) -> str:
        """Generate story content from outline"""
        # This is a placeholder for actual LLM integration
        # In production, this would call your LLM service
        
        if chapter_number:
            # Generate specific chapter
            if chapter_number <= len(outline.chapters):
                chapter = outline.chapters[chapter_number - 1]
                return self._generate_chapter_content(chapter, outline)
            else:
                return "Chapter number out of range"
        else:
            # Generate full story
            content_parts = []
            for i, chapter in enumerate(outline.chapters):
                chapter_content = self._generate_chapter_content(chapter, outline)
                content_parts.append(f"## Chapter {i + 1}: {chapter['title']}\n\n{chapter_content}")
            
            return "\n\n---\n\n".join(content_parts)

    def analyze_story(self, content: str, title: Optional[str] = None) -> StoryAnalysis:
        """Analyze story content"""
        return self.story_analyzer.analyze_story(content, title)

    def get_user_stories(self, user_id: str, genre: Optional[StoryGenre] = None, 
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's stories"""
        return self.database.get_user_stories(user_id, genre, limit)

    def save_story(self, user_id: str, title: str, genre: StoryGenre, 
                  length_type: StoryLength, content: str, 
                  outline: Optional[StoryOutline] = None) -> int:
        """Save story with analysis"""
        analysis = self.analyze_story(content, title)
        return self.database.save_story(user_id, title, genre, length_type, 
                                      content, outline, analysis)

    def _generate_chapters(self, structure: StoryStructure, target_words: int, 
                          characters: List[Character]) -> List[Dict[str, Any]]:
        """Generate chapter outlines"""
        chapters = []
        words_per_chapter = target_words // max(len(structure.plot_points), 3)
        
        for i, plot_point in enumerate(structure.plot_points):
            chapter = {
                "number": i + 1,
                "title": plot_point.name,
                "plot_point": plot_point.name,
                "description": plot_point.description,
                "characters": plot_point.character_focus,
                "word_count_target": words_per_chapter,
                "scene_goal": f"Advance {plot_point.name} through {plot_point.conflict_type} conflict",
                "conflict_type": plot_point.conflict_type
            }
            chapters.append(chapter)
        
        return chapters

    def _generate_setting(self, genre: StoryGenre, premise: str) -> Dict[str, str]:
        """Generate story setting"""
        settings = {
            StoryGenre.FANTASY: {
                "time": "Medieval fantasy era",
                "place": "Mystical kingdom",
                "world_building": "Magic exists, multiple races, ancient prophecies"
            },
            StoryGenre.SCI_FI: {
                "time": "Far future",
                "place": "Space station/colony",
                "world_building": "Advanced technology, alien contact, space travel"
            },
            StoryGenre.MYSTERY: {
                "time": "Present day",
                "place": "Urban setting",
                "world_building": "Realistic modern world with hidden secrets"
            }
        }
        
        return settings.get(genre, {
            "time": "Present day",
            "place": "Contemporary setting", 
            "world_building": "Realistic modern world"
        })

    def _generate_title(self, genre: StoryGenre, premise: str, protagonist_name: str) -> str:
        """Generate story title"""
        title_patterns = {
            StoryGenre.FANTASY: [
                f"The {random.choice(['Quest', 'Journey', 'Chronicles'])} of {protagonist_name}",
                f"The {random.choice(['Lost', 'Ancient', 'Forgotten'])} {random.choice(['Kingdom', 'Prophecy', 'Magic'])}",
                f"{protagonist_name} and the {random.choice(['Crystal', 'Sword', 'Crown'])} of {random.choice(['Power', 'Destiny', 'Light'])}"
            ],
            StoryGenre.SCI_FI: [
                f"The {protagonist_name} Protocol",
                f"{random.choice(['Beyond', 'Across', 'Through'])} the {random.choice(['Stars', 'Void', 'Galaxy'])}",
                f"The {random.choice(['Last', 'First', 'Final'])} {random.choice(['Colony', 'Signal', 'Contact'])}"
            ]
        }
        
        patterns = title_patterns.get(genre, [f"The Story of {protagonist_name}"])
        return random.choice(patterns)

    def _determine_target_audience(self, genre: StoryGenre, themes: List[str]) -> str:
        """Determine target audience"""
        if any(theme in themes for theme in ["coming_of_age", "friendship", "school"]):
            return "Young Adult"
        elif any(theme in themes for theme in ["love", "romance", "relationship"]):
            return "Adult Romance"
        elif genre in [StoryGenre.HORROR, StoryGenre.THRILLER]:
            return "Adult"
        else:
            return "General Adult"

    def _generate_chapter_content(self, chapter: Dict[str, Any], outline: StoryOutline) -> str:
        """Generate content for a specific chapter"""
        # Placeholder content generation
        # In production, this would call your LLM service with the chapter outline
        
        content_template = f"""
        This chapter focuses on {chapter['plot_point']} where the story reaches a crucial turning point.
        
        {chapter['description']}
        
        Key characters in this chapter: {', '.join(chapter['characters'])}
        
        The {chapter['conflict_type']} conflict drives the narrative forward as our protagonist faces
        new challenges that will shape their journey.
        
        [This is placeholder content. In production, this would be generated by your LLM service
        based on the detailed chapter outline, character information, and story structure.]
        """
        
        return content_template.strip()

    def _reconstruct_outline_from_dict(self, outline_data: Dict[str, Any]) -> StoryOutline:
        """Reconstruct StoryOutline object from dictionary"""
        # Reconstruct characters
        characters = []
        for char_data in outline_data.get('characters', []):
            character = Character(
                name=char_data['name'],
                role=char_data['role'],
                archetype=char_data['archetype'],
                motivation=char_data['motivation'],
                conflict=char_data['conflict'],
                background=char_data.get('background', ''),
                traits=char_data.get('traits', []),
                age=char_data.get('age'),
                occupation=char_data.get('occupation')
            )
            characters.append(character)
        
        # Reconstruct plot points
        plot_points = []
        structure_data = outline_data.get('structure', {})
        for pp_data in structure_data.get('plot_points', []):
            plot_point = PlotPoint(
                name=pp_data['name'],
                description=pp_data['description'],
                chapter=pp_data['chapter'],
                word_position=pp_data['position'],
                character_focus=pp_data['characters'],
                conflict_type=pp_data['conflict_type']
            )
            plot_points.append(plot_point)
        
        # Reconstruct story structure
        structure = StoryStructure(
            structure_type=NarrativeStructure(structure_data.get('type', 'three_act')),
            plot_points=plot_points,
            act_breaks=[0.25, 0.75],  # Default
            character_arcs={'protagonist': ['introduction', 'growth', 'resolution']},  # Simplified
            themes=structure_data.get('themes', []),
            subplots=structure_data.get('subplots', [])
        )
        
        # Reconstruct full outline
        outline = StoryOutline(
            title=outline_data['title'],
            genre=StoryGenre(outline_data['genre']),
            length=StoryLength(outline_data['length']),
            premise=outline_data['premise'],
            characters=characters,
            structure=structure,
            chapters=outline_data['chapters'],
            word_count_target=outline_data['word_count_target'],
            themes=outline_data['themes'],
            target_audience=outline_data['target_audience'],
            setting=outline_data['setting']
        )
        
        return outline

def create_story_generator_service(db_path: str = "stories.db") -> StoryGenerator:
    """Factory function to create story generator service"""
    try:
        service = StoryGenerator(db_path)
        logger.info("✅ Story Generator service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize Story Generator service: {e}")
        raise