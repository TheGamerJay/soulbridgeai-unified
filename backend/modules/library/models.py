"""
SoulBridge AI - Library Data Models
Structured data classes for content management
Inspired by clean SDK patterns
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional, Any
from enum import Enum

# Content types supported by the library
ContentType = Literal[
    "chat", "fortune", "horoscope", "decoder", 
    "creative", "ai_image", "mini_studio", "voice_journal"
]

class ShareStatus(Enum):
    PRIVATE = "private"
    SHARED_ANONYMOUS = "shared_anonymous"
    SHARED_PUBLIC = "shared_public"

@dataclass(frozen=True)
class LibraryItem:
    """Immutable library content item with full metadata"""
    id: int
    user_id: int
    content_type: ContentType
    title: str
    content: str  # JSON string or text content
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_favorite: bool = False
    share_status: ShareStatus = ShareStatus.PRIVATE
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_favorite": self.is_favorite,
            "share_status": self.share_status.value,
            "metadata": self.metadata
        }

@dataclass(frozen=True)
class FortuneReading:
    """Structured fortune reading data"""
    question: str
    spread_type: str
    cards: List[Dict[str, Any]]
    interpretation: str
    reading_date: datetime
    user_tier: str
    reversals_enabled: bool = True
    clarifiers_count: int = 0

@dataclass(frozen=True)
class HoroscopeReading:
    """Structured horoscope reading data"""
    sign: str
    reading_type: str  # daily, weekly, monthly
    horoscope_text: str
    lucky_numbers: List[int]
    lucky_color: str
    reading_date: datetime
    user_tier: str

@dataclass(frozen=True)
class DecoderSession:
    """Structured decoder session data"""
    input_text: str
    decoded_text: str
    mode: str  # dream, lyrics, tone, etc.
    symbols_found: List[str]
    mood_analysis: str
    session_date: datetime
    user_tier: str

@dataclass(frozen=True)
class CreativeWriting:
    """Structured creative writing data"""
    prompt: str
    style: str  # story, poem, lyrics, script, etc.
    generated_text: str
    word_count: int
    mood: Optional[str]
    creation_date: datetime
    user_tier: str

@dataclass(frozen=True)
class AIImageGeneration:
    """Structured AI image data"""
    prompt: str
    enhanced_prompt: str
    image_url: str
    style: str
    size: str
    quality: str
    generation_time: float
    creation_date: datetime
    user_tier: str

@dataclass(frozen=True)
class MiniStudioTrack:
    """Structured mini studio track data"""
    project_id: str
    asset_id: str
    track_type: str  # lyrics, beat, vocals
    parameters: Dict[str, Any]
    cost: int
    creation_date: datetime
    user_tier: str = "gold"  # Mini studio is Gold-only

# Factory functions for creating structured content
def create_library_item(
    user_id: int,
    content_type: ContentType,
    title: str,
    structured_content: Any,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a library item with proper structure"""
    import json
    
    return {
        "user_id": user_id,
        "content_type": content_type,
        "title": title,
        "content": json.dumps(structured_content.to_dict()) if hasattr(structured_content, 'to_dict') else str(structured_content),
        "metadata": metadata or {},
        "created_at": datetime.now(),
        "is_favorite": False,
        "share_status": ShareStatus.PRIVATE.value
    }

def parse_library_content(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse library item content back to structured format"""
    import json
    
    try:
        content = json.loads(item["content"])
        return content
    except (json.JSONDecodeError, KeyError):
        return {"raw_content": item.get("content", "")}