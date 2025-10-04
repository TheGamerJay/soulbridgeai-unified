"""
Comprehensive Writing Suite Service
Advanced document generation for scripts, articles, letters, and creative fiction
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

class WritingType(Enum):
    SCREENPLAY = "screenplay"
    STAGE_PLAY = "stage_play"
    TV_SCRIPT = "tv_script"
    RADIO_SCRIPT = "radio_script"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    ACADEMIC_ARTICLE = "academic_article"
    OPINION_PIECE = "opinion_piece"
    BUSINESS_LETTER = "business_letter"
    PERSONAL_LETTER = "personal_letter"
    COVER_LETTER = "cover_letter"
    RESIGNATION_LETTER = "resignation_letter"
    SHORT_FICTION = "short_fiction"
    FLASH_FICTION = "flash_fiction"
    CREATIVE_ESSAY = "creative_essay"
    MEMOIR_EXCERPT = "memoir_excerpt"

class ToneStyle(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"
    CREATIVE = "creative"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    EMPATHETIC = "empathetic"

@dataclass
class WritingPrompt:
    writing_type: WritingType
    topic: str
    tone: ToneStyle
    length: str  # "short", "medium", "long"
    target_audience: str
    key_points: List[str]
    additional_requirements: str
    format_specifications: Dict[str, Any]

@dataclass
class ScriptFormat:
    character_names_caps: bool = True
    action_lines_caps: bool = False
    dialogue_indentation: int = 4
    character_indentation: int = 2
    parenthetical_indentation: int = 3
    transition_alignment: str = "right"  # "left", "center", "right"
    scene_header_caps: bool = True
    
@dataclass
class ArticleStructure:
    has_headline: bool = True
    has_byline: bool = True
    has_lead_paragraph: bool = True
    has_subheadings: bool = True
    paragraph_count: int = 5
    citation_style: str = "none"  # "apa", "mla", "chicago", "none"
    
@dataclass
class LetterFormat:
    has_date: bool = True
    has_sender_address: bool = True
    has_recipient_address: bool = True
    has_salutation: bool = True
    has_closing: bool = True
    has_signature_line: bool = True
    formal_language: bool = True

@dataclass
class WritingOutput:
    content: str
    word_count: int
    character_count: int
    estimated_reading_time: int  # minutes
    format_analysis: Dict[str, Any]
    style_score: float
    readability_score: float
    suggestions: List[str]

class ScriptGenerator:
    """Generate various types of scripts"""
    
    def __init__(self):
        self.scene_transitions = [
            "FADE IN:", "FADE OUT:", "CUT TO:", "DISSOLVE TO:", 
            "FADE TO BLACK", "SMASH CUT TO:", "MATCH CUT TO:"
        ]
        
        self.character_directions = [
            "(beat)", "(pause)", "(quietly)", "(loudly)", "(whispering)",
            "(shouting)", "(to himself)", "(aside)", "(sarcastically)"
        ]

    def generate_screenplay(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate a screenplay format script"""
        
        # Extract format specifications
        format_spec = prompt.format_specifications.get('script', ScriptFormat())
        
        # Generate screenplay content
        content_parts = []
        
        # Title page elements
        content_parts.append(f"TITLE: {prompt.topic.upper()}")
        content_parts.append(f"GENRE: Drama/Screenplay")
        content_parts.append("")
        content_parts.append("FADE IN:")
        content_parts.append("")
        
        # Generate scenes based on key points
        scene_count = min(len(prompt.key_points), 3)  # Limit for demo
        
        for i, key_point in enumerate(prompt.key_points[:scene_count]):
            scene_header = f"{'EXT.' if i % 2 == 0 else 'INT.'} {self._generate_location()} - {'DAY' if i % 2 == 0 else 'NIGHT'}"
            content_parts.append(scene_header)
            content_parts.append("")
            
            # Action line
            action = f"We see {self._generate_action_description(key_point)}."
            content_parts.append(action)
            content_parts.append("")
            
            # Character dialogue
            character1 = "ALEX"
            character2 = "JORDAN"
            
            content_parts.append(f"{' ' * format_spec.character_indentation}{character1}")
            dialogue1 = self._generate_dialogue(key_point, prompt.tone)
            content_parts.append(f"{' ' * format_spec.dialogue_indentation}{dialogue1}")
            content_parts.append("")
            
            # Response
            content_parts.append(f"{' ' * format_spec.character_indentation}{character2}")
            content_parts.append(f"{' ' * format_spec.parenthetical_indentation}(thoughtfully)")
            dialogue2 = self._generate_response_dialogue(key_point, prompt.tone)
            content_parts.append(f"{' ' * format_spec.dialogue_indentation}{dialogue2}")
            content_parts.append("")
            
            # Scene transition
            if i < scene_count - 1:
                transition = random.choice(self.scene_transitions[2:5])  # CUT TO, DISSOLVE TO, etc.
                content_parts.append(f"{transition:>50}")
                content_parts.append("")
        
        content_parts.append("FADE OUT.")
        content_parts.append("")
        content_parts.append("THE END")
        
        content = "\n".join(content_parts)
        
        return self._analyze_writing_output(content, prompt.writing_type)

    def generate_stage_play(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate a stage play format script"""
        
        content_parts = []
        
        # Play header
        content_parts.append(f"{prompt.topic.upper()}")
        content_parts.append(f"A {prompt.tone.value} stage play")
        content_parts.append("")
        content_parts.append("CHARACTERS:")
        
        # Generate character list
        characters = ["ALEX", "JORDAN", "TAYLOR"]
        for char in characters:
            content_parts.append(f"  {char} - {self._generate_character_description()}")
        
        content_parts.append("")
        content_parts.append("SETTING:")
        content_parts.append(f"  {self._generate_stage_setting(prompt.topic)}")
        content_parts.append("")
        content_parts.append("ACT I")
        content_parts.append("")
        
        # Generate scenes
        for i, key_point in enumerate(prompt.key_points[:2]):
            content_parts.append(f"Scene {i + 1}")
            content_parts.append("")
            content_parts.append(f"(Lights up. {self._generate_stage_direction(key_point)})")
            content_parts.append("")
            
            # Character dialogue
            content_parts.append(f"ALEX: {self._generate_dialogue(key_point, prompt.tone)}")
            content_parts.append("")
            content_parts.append(f"JORDAN: {self._generate_response_dialogue(key_point, prompt.tone)}")
            content_parts.append("")
            content_parts.append("(Lights fade)")
            content_parts.append("")
        
        content = "\n".join(content_parts)
        return self._analyze_writing_output(content, prompt.writing_type)

    def _generate_location(self) -> str:
        """Generate random location"""
        locations = [
            "COFFEE SHOP", "OFFICE BUILDING", "PARK BENCH", 
            "CAR", "APARTMENT LIVING ROOM", "RESTAURANT"
        ]
        return random.choice(locations)

    def _generate_action_description(self, key_point: str) -> str:
        """Generate action description based on key point"""
        return f"a character contemplating {key_point.lower()}"

    def _generate_dialogue(self, key_point: str, tone: ToneStyle) -> str:
        """Generate dialogue based on key point and tone"""
        if tone == ToneStyle.FORMAL:
            return f"I believe we must consider {key_point.lower()} carefully."
        elif tone == ToneStyle.CASUAL:
            return f"So, what do you think about {key_point.lower()}?"
        elif tone == ToneStyle.HUMOROUS:
            return f"You know, {key_point.lower()} reminds me of a funny story..."
        else:
            return f"This whole situation with {key_point.lower()} is really something."

    def _generate_response_dialogue(self, key_point: str, tone: ToneStyle) -> str:
        """Generate response dialogue"""
        responses = {
            ToneStyle.FORMAL: f"Indeed, {key_point.lower()} requires our utmost attention.",
            ToneStyle.CASUAL: f"Yeah, {key_point.lower()} is pretty interesting.",
            ToneStyle.HUMOROUS: "Ha! That's actually hilarious when you put it that way.",
            ToneStyle.SERIOUS: f"The implications of {key_point.lower()} are significant."
        }
        return responses.get(tone, f"I see what you mean about {key_point.lower()}.")

    def _generate_character_description(self) -> str:
        """Generate character description"""
        descriptions = [
            "A thoughtful individual in their 30s",
            "An energetic person with strong opinions",
            "A wise character who offers guidance"
        ]
        return random.choice(descriptions)

    def _generate_stage_setting(self, topic: str) -> str:
        """Generate stage setting description"""
        return f"A simple set representing the world of {topic.lower()}"

    def _generate_stage_direction(self, key_point: str) -> str:
        """Generate stage direction"""
        return f"Characters are engaged in a discussion about {key_point.lower()}"

    def _analyze_writing_output(self, content: str, writing_type: WritingType) -> WritingOutput:
        """Analyze the generated writing output"""
        word_count = len(content.split())
        character_count = len(content)
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        # Simple format analysis
        format_analysis = {
            "has_proper_formatting": True,
            "scene_count": content.count("EXT.") + content.count("INT."),
            "character_count": len(re.findall(r'^[A-Z]{3,}:', content, re.MULTILINE)),
            "dialogue_lines": len(re.findall(r'^\s{4,}[^(]', content, re.MULTILINE))
        }
        
        # Style and readability scores (simplified)
        style_score = 0.75  # Placeholder
        readability_score = 65.0  # Placeholder Flesch score
        
        suggestions = [
            "Consider adding more descriptive action lines",
            "Vary dialogue length for natural flow",
            "Add character-specific speech patterns"
        ]
        
        return WritingOutput(
            content=content,
            word_count=word_count,
            character_count=character_count,
            estimated_reading_time=reading_time,
            format_analysis=format_analysis,
            style_score=style_score,
            readability_score=readability_score,
            suggestions=suggestions
        )

class ArticleGenerator:
    """Generate various types of articles"""
    
    def __init__(self):
        self.headline_styles = {
            WritingType.NEWS_ARTICLE: "Breaking: {topic} Impacts Local Community",
            WritingType.BLOG_POST: "The Ultimate Guide to {topic}",
            WritingType.ACADEMIC_ARTICLE: "An Analysis of {topic} in Contemporary Context",
            WritingType.OPINION_PIECE: "Why {topic} Matters More Than You Think"
        }

    def generate_article(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate article based on type"""
        
        structure = prompt.format_specifications.get('article', ArticleStructure())
        content_parts = []
        
        # Headline
        if structure.has_headline:
            headline_template = self.headline_styles.get(
                prompt.writing_type, 
                "Understanding {topic}"
            )
            headline = headline_template.format(topic=prompt.topic)
            content_parts.append(headline.upper())
            content_parts.append("")
        
        # Byline
        if structure.has_byline:
            content_parts.append("By Staff Writer")
            content_parts.append(f"Published: {datetime.now().strftime('%B %d, %Y')}")
            content_parts.append("")
        
        # Lead paragraph
        if structure.has_lead_paragraph:
            lead = self._generate_lead_paragraph(prompt)
            content_parts.append(lead)
            content_parts.append("")
        
        # Body paragraphs
        for i, key_point in enumerate(prompt.key_points[:structure.paragraph_count-1]):
            if structure.has_subheadings and i > 0:
                subheading = self._generate_subheading(key_point)
                content_parts.append(subheading)
                content_parts.append("")
            
            paragraph = self._generate_article_paragraph(key_point, prompt.tone, prompt.writing_type)
            content_parts.append(paragraph)
            content_parts.append("")
        
        # Conclusion paragraph
        conclusion = self._generate_conclusion_paragraph(prompt)
        content_parts.append(conclusion)
        
        content = "\n".join(content_parts)
        return self._analyze_article_output(content, prompt.writing_type)

    def _generate_lead_paragraph(self, prompt: WritingPrompt) -> str:
        """Generate compelling lead paragraph"""
        if prompt.writing_type == WritingType.NEWS_ARTICLE:
            return f"Recent developments in {prompt.topic.lower()} have captured the attention of {prompt.target_audience.lower()}, raising important questions about {prompt.key_points[0].lower() if prompt.key_points else 'the future'}."
        
        elif prompt.writing_type == WritingType.BLOG_POST:
            return f"If you've ever wondered about {prompt.topic.lower()}, you're not alone. In this comprehensive guide, we'll explore {', '.join(point.lower() for point in prompt.key_points[:2])} and much more."
        
        elif prompt.writing_type == WritingType.ACADEMIC_ARTICLE:
            return f"The study of {prompt.topic.lower()} has become increasingly relevant in contemporary discourse. This article examines {prompt.key_points[0].lower() if prompt.key_points else 'key aspects'} through a critical lens."
        
        else:  # OPINION_PIECE
            return f"It's time we had an honest conversation about {prompt.topic.lower()}. Despite what many believe, {prompt.key_points[0].lower() if prompt.key_points else 'the reality'} tells a different story."

    def _generate_subheading(self, key_point: str) -> str:
        """Generate subheading from key point"""
        return f"## {key_point.title()}"

    def _generate_article_paragraph(self, key_point: str, tone: ToneStyle, article_type: WritingType) -> str:
        """Generate article paragraph"""
        if tone == ToneStyle.FORMAL:
            return f"Furthermore, it is essential to consider {key_point.lower()} within the broader context of current developments. Research indicates that this aspect plays a crucial role in understanding the overall implications of the subject matter."
        
        elif tone == ToneStyle.CASUAL:
            return f"Now, let's talk about {key_point.lower()}. This is actually pretty interesting when you think about it. Most people don't realize how much this impacts their daily lives."
        
        elif tone == ToneStyle.PERSUASIVE:
            return f"Consider this: {key_point.lower()} represents a fundamental shift in how we approach this issue. The evidence is clear, and the time for action is now."
        
        else:
            return f"When examining {key_point.lower()}, several important factors emerge. These considerations help illuminate the complexity of the subject and provide valuable insights for readers."

    def _generate_conclusion_paragraph(self, prompt: WritingPrompt) -> str:
        """Generate conclusion paragraph"""
        return f"In conclusion, {prompt.topic.lower()} remains a topic of significant importance to {prompt.target_audience.lower()}. As we move forward, understanding these key aspects will be crucial for making informed decisions."

    def _analyze_article_output(self, content: str, writing_type: WritingType) -> WritingOutput:
        """Analyze article output"""
        word_count = len(content.split())
        character_count = len(content)
        reading_time = max(1, word_count // 200)
        
        format_analysis = {
            "has_headline": content.split('\n')[0].isupper(),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "subheading_count": content.count('##'),
            "avg_paragraph_length": word_count / max(1, len(content.split('\n\n')))
        }
        
        suggestions = [
            "Add more specific examples and data",
            "Include quotes from relevant sources",
            "Consider adding bullet points for key information"
        ]
        
        return WritingOutput(
            content=content,
            word_count=word_count,
            character_count=character_count,
            estimated_reading_time=reading_time,
            format_analysis=format_analysis,
            style_score=0.8,
            readability_score=70.0,
            suggestions=suggestions
        )

class LetterGenerator:
    """Generate various types of letters"""
    
    def __init__(self):
        self.salutations = {
            "formal": ["Dear Sir/Madam", "Dear Mr./Ms. [Name]", "To Whom It May Concern"],
            "business": ["Dear [Name]", "Dear Mr./Ms. [Name]"],
            "personal": ["Dear [Name]", "Hello [Name]", "Hi [Name]"]
        }
        
        self.closings = {
            "formal": ["Sincerely", "Respectfully", "Yours truly"],
            "business": ["Best regards", "Sincerely", "Kind regards"],
            "personal": ["Best wishes", "Warmly", "With love"]
        }

    def generate_letter(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate letter based on type"""
        
        format_spec = prompt.format_specifications.get('letter', LetterFormat())
        content_parts = []
        
        # Date
        if format_spec.has_date:
            content_parts.append(datetime.now().strftime("%B %d, %Y"))
            content_parts.append("")
        
        # Sender address (placeholder)
        if format_spec.has_sender_address:
            content_parts.append("[Your Name]")
            content_parts.append("[Your Address]")
            content_parts.append("[City, State ZIP]")
            content_parts.append("")
        
        # Recipient address (placeholder)
        if format_spec.has_recipient_address and prompt.writing_type != WritingType.PERSONAL_LETTER:
            content_parts.append("[Recipient Name]")
            content_parts.append("[Company/Organization]")
            content_parts.append("[Address]")
            content_parts.append("[City, State ZIP]")
            content_parts.append("")
        
        # Salutation
        if format_spec.has_salutation:
            letter_style = "formal" if format_spec.formal_language else "personal"
            if prompt.writing_type in [WritingType.BUSINESS_LETTER, WritingType.COVER_LETTER]:
                letter_style = "business"
            
            salutation = random.choice(self.salutations[letter_style])
            content_parts.append(f"{salutation},")
            content_parts.append("")
        
        # Letter body
        body = self._generate_letter_body(prompt)
        content_parts.extend(body)
        content_parts.append("")
        
        # Closing
        if format_spec.has_closing:
            letter_style = "formal" if format_spec.formal_language else "personal"
            if prompt.writing_type in [WritingType.BUSINESS_LETTER, WritingType.COVER_LETTER]:
                letter_style = "business"
            
            closing = random.choice(self.closings[letter_style])
            content_parts.append(f"{closing},")
            content_parts.append("")
        
        # Signature line
        if format_spec.has_signature_line:
            content_parts.append("[Your Signature]")
            content_parts.append("[Your Typed Name]")
        
        content = "\n".join(content_parts)
        return self._analyze_letter_output(content, prompt.writing_type)

    def _generate_letter_body(self, prompt: WritingPrompt) -> List[str]:
        """Generate letter body paragraphs"""
        body_parts = []
        
        if prompt.writing_type == WritingType.COVER_LETTER:
            body_parts.append(f"I am writing to express my interest in {prompt.topic.lower()}. With my background and skills, I believe I would be a valuable addition to your team.")
            body_parts.append("")
            
            for key_point in prompt.key_points[:2]:
                body_parts.append(f"My experience with {key_point.lower()} has prepared me well for this opportunity. I am confident that I can contribute effectively to your organization.")
                body_parts.append("")
            
            body_parts.append("I would welcome the opportunity to discuss my qualifications further. Thank you for your time and consideration.")
        
        elif prompt.writing_type == WritingType.BUSINESS_LETTER:
            body_parts.append(f"I am writing regarding {prompt.topic.lower()}. Please allow me to outline the key points for your consideration.")
            body_parts.append("")
            
            for key_point in prompt.key_points:
                body_parts.append(f"• {key_point}")
            body_parts.append("")
            
            body_parts.append("I look forward to your response on this matter.")
        
        elif prompt.writing_type == WritingType.RESIGNATION_LETTER:
            body_parts.append(f"Please accept this letter as my formal notification of resignation from my position as {prompt.topic}.")
            body_parts.append("")
            body_parts.append("My last day of work will be [Date - typically two weeks from today].")
            body_parts.append("")
            body_parts.append("I am grateful for the opportunities I have had here and will do everything possible to ensure a smooth transition.")
        
        else:  # PERSONAL_LETTER
            body_parts.append(f"I wanted to write to you about {prompt.topic.lower()}. It's been on my mind lately, and I thought you'd be interested to hear about it.")
            body_parts.append("")
            
            for key_point in prompt.key_points[:3]:
                body_parts.append(f"I've been thinking about {key_point.lower()}, and I wanted to share my thoughts with you.")
                body_parts.append("")
            
            body_parts.append("I'd love to hear what you think about all this. Looking forward to your response!")
        
        return body_parts

    def _analyze_letter_output(self, content: str, writing_type: WritingType) -> WritingOutput:
        """Analyze letter output"""
        word_count = len(content.split())
        character_count = len(content)
        reading_time = max(1, word_count // 200)
        
        format_analysis = {
            "has_date": content.split('\n')[0].count(',') > 0,
            "has_salutation": 'Dear' in content or 'Hello' in content,
            "has_closing": any(closing in content for closing in ['Sincerely', 'Best regards', 'Warmly']),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "formality_level": "high" if "Sir/Madam" in content else "medium"
        }
        
        suggestions = [
            "Personalize the greeting with specific names when possible",
            "Be more specific about dates and details",
            "Consider adding a call to action in the closing"
        ]
        
        return WritingOutput(
            content=content,
            word_count=word_count,
            character_count=character_count,
            estimated_reading_time=reading_time,
            format_analysis=format_analysis,
            style_score=0.85,
            readability_score=75.0,
            suggestions=suggestions
        )

class CreativeGenerator:
    """Generate creative fiction and essays"""
    
    def generate_creative_writing(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate creative writing based on type"""
        
        if prompt.writing_type == WritingType.SHORT_FICTION:
            return self._generate_short_fiction(prompt)
        elif prompt.writing_type == WritingType.FLASH_FICTION:
            return self._generate_flash_fiction(prompt)
        elif prompt.writing_type == WritingType.CREATIVE_ESSAY:
            return self._generate_creative_essay(prompt)
        else:  # MEMOIR_EXCERPT
            return self._generate_memoir_excerpt(prompt)

    def _generate_short_fiction(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate short fiction story"""
        content_parts = []
        
        # Title
        content_parts.append(f"{prompt.topic.title()}")
        content_parts.append("")
        
        # Opening
        opening = f"The day everything changed began like any other. {self._generate_opening_sentence(prompt.topic, prompt.tone)}."
        content_parts.append(opening)
        content_parts.append("")
        
        # Development paragraphs
        for key_point in prompt.key_points[:3]:
            paragraph = self._generate_fiction_paragraph(key_point, prompt.tone)
            content_parts.append(paragraph)
            content_parts.append("")
        
        # Conclusion
        conclusion = f"As the sun set that evening, everything had indeed changed. The truth about {prompt.topic.lower()} would never be the same."
        content_parts.append(conclusion)
        
        content = "\n".join(content_parts)
        return self._analyze_creative_output(content, prompt.writing_type)

    def _generate_flash_fiction(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate flash fiction (very short story)"""
        content_parts = []
        
        # Single impactful paragraph
        story = f"She opened the letter about {prompt.topic.lower()}, expecting routine correspondence. Instead, she found {prompt.key_points[0].lower() if prompt.key_points else 'something unexpected'}. Her hands trembled as she read the words that would change everything. Outside, the world continued unchanged, but inside this small room, everything had shifted. She set the letter down and smiled—finally, she knew what she had to do."
        
        content_parts.append(story)
        
        content = "\n".join(content_parts)
        return self._analyze_creative_output(content, prompt.writing_type)

    def _generate_creative_essay(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate creative essay"""
        content_parts = []
        
        # Title
        content_parts.append(f"Reflections on {prompt.topic.title()}")
        content_parts.append("")
        
        # Opening reflection
        opening = f"I have always been fascinated by {prompt.topic.lower()}. There is something about it that speaks to the deepest parts of the human experience."
        content_parts.append(opening)
        content_parts.append("")
        
        # Body paragraphs with personal reflection
        for key_point in prompt.key_points[:3]:
            paragraph = f"Consider {key_point.lower()}—it reminds me of a moment when I truly understood what it means to be human. The way it unfolds in our lives is both mysterious and profound."
            content_parts.append(paragraph)
            content_parts.append("")
        
        # Philosophical conclusion
        conclusion = f"In the end, {prompt.topic.lower()} teaches us that life is not about finding answers, but about learning to ask better questions."
        content_parts.append(conclusion)
        
        content = "\n".join(content_parts)
        return self._analyze_creative_output(content, prompt.writing_type)

    def _generate_memoir_excerpt(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate memoir-style writing"""
        content_parts = []
        
        # Personal opening
        opening = f"I was twelve when I first encountered {prompt.topic.lower()}. Looking back now, I can see how that moment shaped everything that followed."
        content_parts.append(opening)
        content_parts.append("")
        
        # Memory development
        for i, key_point in enumerate(prompt.key_points[:2]):
            if i == 0:
                paragraph = f"My mother used to say that {key_point.lower()} was like a mirror—it showed you what you needed to see, not what you wanted to see. I didn't understand then what she meant."
            else:
                paragraph = f"Years later, when {key_point.lower()} became part of my daily reality, I finally grasped the wisdom in her words. Some lessons can only be learned through living them."
            
            content_parts.append(paragraph)
            content_parts.append("")
        
        # Reflective conclusion
        conclusion = f"Now, with the benefit of hindsight, I understand that {prompt.topic.lower()} was never just about the events themselves—it was about who I became because of them."
        content_parts.append(conclusion)
        
        content = "\n".join(content_parts)
        return self._analyze_creative_output(content, prompt.writing_type)

    def _generate_opening_sentence(self, topic: str, tone: ToneStyle) -> str:
        """Generate compelling opening sentence"""
        if tone == ToneStyle.SERIOUS:
            return f"The implications of {topic.lower()} weighed heavily on everyone involved"
        elif tone == ToneStyle.HUMOROUS:
            return f"Nobody expected {topic.lower()} to be quite so complicated—or quite so amusing"
        else:
            return f"The story of {topic.lower()} begins in the most ordinary of places"

    def _generate_fiction_paragraph(self, key_point: str, tone: ToneStyle) -> str:
        """Generate fiction paragraph"""
        return f"As the situation with {key_point.lower()} unfolded, the characters found themselves facing choices they never imagined they would have to make. Each decision carried weight, and each consequence rippled outward in ways both seen and unseen."

    def _analyze_creative_output(self, content: str, writing_type: WritingType) -> WritingOutput:
        """Analyze creative writing output"""
        word_count = len(content.split())
        character_count = len(content)
        reading_time = max(1, word_count // 200)
        
        format_analysis = {
            "narrative_voice": "first_person" if " I " in content else "third_person",
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "dialogue_present": '"' in content,
            "descriptive_language": len(re.findall(r'\b(beautiful|mysterious|profound|fascinating)\b', content.lower()))
        }
        
        suggestions = [
            "Add more sensory details to enhance immersion",
            "Consider varying sentence structure for better flow",
            "Develop character emotions more deeply"
        ]
        
        return WritingOutput(
            content=content,
            word_count=word_count,
            character_count=character_count,
            estimated_reading_time=reading_time,
            format_analysis=format_analysis,
            style_score=0.75,
            readability_score=65.0,
            suggestions=suggestions
        )

class WritingSuiteDatabase:
    """Manage writing suite data persistence"""
    
    def __init__(self, db_path: str = "writing_suite.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(format_query("""
            CREATE TABLE IF NOT EXISTS writings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                writing_type TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                tone TEXT,
                target_audience TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS writing_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                writing_id INTEGER,
                style_score REAL,
                readability_score REAL,
                suggestions TEXT,
                format_analysis TEXT,
                FOREIGN KEY (writing_id) REFERENCES writings (id)
            )
        """)
        
        conn.commit()
        conn.close()

    def save_writing(self, user_id: str, title: str, writing_output: WritingOutput, 
                    prompt: WritingPrompt) -> int:
        """Save writing with analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO writings (user_id, title, writing_type, content, word_count, tone, target_audience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """), (user_id, title, prompt.writing_type.value, writing_output.content, 
              writing_output.word_count, prompt.tone.value, prompt.target_audience))
        
        writing_id = cursor.lastrowid
        
        # Save analytics
        cursor.execute(format_query("""
            INSERT INTO writing_analytics (writing_id, style_score, readability_score, suggestions, format_analysis)
            VALUES (?, ?, ?, ?, ?)
        """), (writing_id, writing_output.style_score, writing_output.readability_score,
              json.dumps(writing_output.suggestions), json.dumps(writing_output.format_analysis)))
        
        conn.commit()
        conn.close()
        
        return writing_id

    def get_user_writings(self, user_id: str, writing_type: Optional[WritingType] = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's writings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if writing_type:
            cursor.execute(format_query("""
                SELECT id, title, writing_type, word_count, created_at
                FROM writings 
                WHERE user_id = ? AND writing_type = ?
                ORDER BY created_at DESC LIMIT ?
            """), (user_id, writing_type.value, limit))
        else:
            cursor.execute(format_query("""
                SELECT id, title, writing_type, word_count, created_at
                FROM writings 
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """), (user_id, limit))
        
        writings = []
        for row in cursor.fetchall():
            writings.append({
                'id': row[0],
                'title': row[1],
                'writing_type': row[2],
                'word_count': row[3],
                'created_at': row[4]
            })
        
        conn.close()
        return writings

class WritingSuite:
    """Main writing suite service"""
    
    def __init__(self, db_path: str = "writing_suite.db"):
        self.script_generator = ScriptGenerator()
        self.article_generator = ArticleGenerator()
        self.letter_generator = LetterGenerator()
        self.creative_generator = CreativeGenerator()
        self.database = WritingSuiteDatabase(db_path)

    def generate_writing(self, prompt: WritingPrompt) -> WritingOutput:
        """Generate writing based on prompt type"""
        
        if prompt.writing_type in [WritingType.SCREENPLAY, WritingType.STAGE_PLAY, 
                                  WritingType.TV_SCRIPT, WritingType.RADIO_SCRIPT]:
            return self.script_generator.generate_screenplay(prompt) if prompt.writing_type == WritingType.SCREENPLAY else self.script_generator.generate_stage_play(prompt)
        
        elif prompt.writing_type in [WritingType.NEWS_ARTICLE, WritingType.BLOG_POST, 
                                   WritingType.ACADEMIC_ARTICLE, WritingType.OPINION_PIECE]:
            return self.article_generator.generate_article(prompt)
        
        elif prompt.writing_type in [WritingType.BUSINESS_LETTER, WritingType.PERSONAL_LETTER, 
                                   WritingType.COVER_LETTER, WritingType.RESIGNATION_LETTER]:
            return self.letter_generator.generate_letter(prompt)
        
        else:  # Creative writing types
            return self.creative_generator.generate_creative_writing(prompt)

    def save_writing(self, user_id: str, title: str, writing_output: WritingOutput, 
                    prompt: WritingPrompt) -> int:
        """Save writing to database"""
        return self.database.save_writing(user_id, title, writing_output, prompt)

    def get_user_writings(self, user_id: str, writing_type: Optional[WritingType] = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's writings"""
        return self.database.get_user_writings(user_id, writing_type, limit)

def create_writing_suite_service(db_path: str = "writing_suite.db") -> WritingSuite:
    """Factory function to create writing suite service"""
    try:
        service = WritingSuite(db_path)
        logger.info("✅ Writing Suite service initialized successfully")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize Writing Suite service: {e}")
        raise