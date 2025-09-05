"""
AI Lyric Writing Service with Consent Management and Embedding-based Similarity
Advanced lyric generation with artist consent tracking and semantic embeddings
"""

import logging
import json
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import sqlite3
import os

logger = logging.getLogger(__name__)

@dataclass
class ConsentRecord:
    """Artist consent tracking record"""
    artist_id: str
    artist_name: str
    consent_given: bool
    consent_date: datetime
    consent_expires: Optional[datetime]
    training_allowed: bool
    commercial_use: bool
    attribution_required: bool
    restrictions: Dict[str, Any]
    consent_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'artist_id': self.artist_id,
            'artist_name': self.artist_name,
            'consent_given': self.consent_given,
            'consent_date': self.consent_date.isoformat() if self.consent_date else None,
            'consent_expires': self.consent_expires.isoformat() if self.consent_expires else None,
            'training_allowed': self.training_allowed,
            'commercial_use': self.commercial_use,
            'attribution_required': self.attribution_required,
            'restrictions': self.restrictions,
            'consent_version': self.consent_version
        }

@dataclass
class LyricData:
    """Lyric data with metadata and embedding"""
    lyric_id: str
    artist_id: str
    title: str
    lyrics: str
    genre: str
    mood: str
    language: str
    embedding: Optional[np.ndarray]
    created_date: datetime
    consent_status: str
    similarity_threshold: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lyric_id': self.lyric_id,
            'artist_id': self.artist_id,
            'title': self.title,
            'lyrics': self.lyrics,
            'genre': self.genre,
            'mood': self.mood,
            'language': self.language,
            'embedding': self.embedding.tolist() if self.embedding is not None else None,
            'created_date': self.created_date.isoformat(),
            'consent_status': self.consent_status,
            'similarity_threshold': self.similarity_threshold
        }

class LyricEmbeddingService:
    """Service for generating and managing lyric embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize embedding service with specified model"""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"✅ Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.model = None
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text"""
        if not self.model or not text.strip():
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

class ConsentManager:
    """Manages artist consent for AI training and generation"""
    
    def __init__(self, db_path: str = "soulbridge.db"):
        self.db_path = db_path
        self.init_consent_tables()
    
    def init_consent_tables(self):
        """Initialize consent management tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS artist_consent (
                        artist_id TEXT PRIMARY KEY,
                        artist_name TEXT NOT NULL,
                        consent_given BOOLEAN DEFAULT FALSE,
                        consent_date TEXT,
                        consent_expires TEXT,
                        training_allowed BOOLEAN DEFAULT FALSE,
                        commercial_use BOOLEAN DEFAULT FALSE,
                        attribution_required BOOLEAN DEFAULT TRUE,
                        restrictions TEXT DEFAULT '{}',
                        consent_version TEXT DEFAULT '1.0',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS consent_audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        artist_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        previous_state TEXT,
                        new_state TEXT,
                        changed_by TEXT,
                        changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (artist_id) REFERENCES artist_consent (artist_id)
                    )
                ''')
                
                conn.commit()
                logger.info("✅ Consent tables initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize consent tables: {e}")
    
    def record_consent(self, consent_record: ConsentRecord) -> bool:
        """Record or update artist consent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get previous state for audit
                previous = self.get_consent(consent_record.artist_id)
                
                conn.execute('''
                    INSERT OR REPLACE INTO artist_consent (
                        artist_id, artist_name, consent_given, consent_date,
                        consent_expires, training_allowed, commercial_use,
                        attribution_required, restrictions, consent_version, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    consent_record.artist_id,
                    consent_record.artist_name,
                    consent_record.consent_given,
                    consent_record.consent_date.isoformat(),
                    consent_record.consent_expires.isoformat() if consent_record.consent_expires else None,
                    consent_record.training_allowed,
                    consent_record.commercial_use,
                    consent_record.attribution_required,
                    json.dumps(consent_record.restrictions),
                    consent_record.consent_version,
                    datetime.now(timezone.utc).isoformat()
                ))
                
                # Audit trail
                conn.execute('''
                    INSERT INTO consent_audit (artist_id, action, previous_state, new_state)
                    VALUES (?, ?, ?, ?)
                ''', (
                    consent_record.artist_id,
                    'UPDATE' if previous else 'CREATE',
                    json.dumps(previous.to_dict()) if previous else None,
                    json.dumps(consent_record.to_dict())
                ))
                
                conn.commit()
                logger.info(f"✅ Consent recorded for artist: {consent_record.artist_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to record consent: {e}")
            return False
    
    def get_consent(self, artist_id: str) -> Optional[ConsentRecord]:
        """Retrieve consent record for artist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT artist_id, artist_name, consent_given, consent_date,
                           consent_expires, training_allowed, commercial_use,
                           attribution_required, restrictions, consent_version
                    FROM artist_consent WHERE artist_id = ?
                ''', (artist_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return ConsentRecord(
                    artist_id=row[0],
                    artist_name=row[1],
                    consent_given=bool(row[2]),
                    consent_date=datetime.fromisoformat(row[3]) if row[3] else None,
                    consent_expires=datetime.fromisoformat(row[4]) if row[4] else None,
                    training_allowed=bool(row[5]),
                    commercial_use=bool(row[6]),
                    attribution_required=bool(row[7]),
                    restrictions=json.loads(row[8]) if row[8] else {},
                    consent_version=row[9] or "1.0"
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to get consent: {e}")
            return None
    
    def is_training_allowed(self, artist_id: str) -> bool:
        """Check if artist allows AI training on their lyrics"""
        consent = self.get_consent(artist_id)
        if not consent:
            return False
        
        # Check expiration
        if consent.consent_expires and datetime.now(timezone.utc) > consent.consent_expires:
            logger.warning(f"Consent expired for artist {artist_id}")
            return False
        
        return consent.consent_given and consent.training_allowed
    
    def is_commercial_use_allowed(self, artist_id: str) -> bool:
        """Check if commercial use is allowed"""
        consent = self.get_consent(artist_id)
        if not consent:
            return False
        
        return consent.consent_given and consent.commercial_use

class LyricDatabase:
    """Database for storing lyrics with embeddings"""
    
    def __init__(self, db_path: str = "soulbridge.db"):
        self.db_path = db_path
        self.embedding_service = LyricEmbeddingService()
        self.init_lyric_tables()
    
    def init_lyric_tables(self):
        """Initialize lyric storage tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS lyric_data (
                        lyric_id TEXT PRIMARY KEY,
                        artist_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        lyrics TEXT NOT NULL,
                        genre TEXT,
                        mood TEXT,
                        language TEXT DEFAULT 'en',
                        embedding_json TEXT,
                        consent_status TEXT DEFAULT 'pending',
                        similarity_threshold REAL DEFAULT 0.85,
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_artist_id ON lyric_data (artist_id)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_genre ON lyric_data (genre)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_consent_status ON lyric_data (consent_status)
                ''')
                
                conn.commit()
                logger.info("✅ Lyric tables initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize lyric tables: {e}")
    
    def store_lyric(self, lyric_data: LyricData) -> bool:
        """Store lyric with generated embedding"""
        try:
            # Generate embedding if not provided
            if lyric_data.embedding is None:
                lyric_data.embedding = self.embedding_service.generate_embedding(lyric_data.lyrics)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO lyric_data (
                        lyric_id, artist_id, title, lyrics, genre, mood,
                        language, embedding_json, consent_status, similarity_threshold, created_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lyric_data.lyric_id,
                    lyric_data.artist_id,
                    lyric_data.title,
                    lyric_data.lyrics,
                    lyric_data.genre,
                    lyric_data.mood,
                    lyric_data.language,
                    json.dumps(lyric_data.embedding.tolist()) if lyric_data.embedding is not None else None,
                    lyric_data.consent_status,
                    lyric_data.similarity_threshold,
                    lyric_data.created_date.isoformat()
                ))
                
                conn.commit()
                logger.info(f"✅ Stored lyric: {lyric_data.title}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store lyric: {e}")
            return False
    
    def find_similar_lyrics(self, query_text: str, threshold: float = 0.85, limit: int = 10) -> List[Tuple[LyricData, float]]:
        """Find similar lyrics using embedding similarity"""
        try:
            query_embedding = self.embedding_service.generate_embedding(query_text)
            if query_embedding is None:
                return []
            
            similar_lyrics = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT lyric_id, artist_id, title, lyrics, genre, mood,
                           language, embedding_json, consent_status, similarity_threshold, created_date
                    FROM lyric_data WHERE embedding_json IS NOT NULL
                ''')
                
                for row in cursor.fetchall():
                    try:
                        stored_embedding = np.array(json.loads(row[7]))
                        similarity = self.embedding_service.calculate_similarity(query_embedding, stored_embedding)
                        
                        if similarity >= threshold:
                            lyric_data = LyricData(
                                lyric_id=row[0],
                                artist_id=row[1],
                                title=row[2],
                                lyrics=row[3],
                                genre=row[4],
                                mood=row[5],
                                language=row[6],
                                embedding=stored_embedding,
                                created_date=datetime.fromisoformat(row[10]),
                                consent_status=row[8],
                                similarity_threshold=row[9]
                            )
                            similar_lyrics.append((lyric_data, similarity))
                    except Exception as e:
                        logger.warning(f"Error processing lyric {row[0]}: {e}")
                        continue
            
            # Sort by similarity score
            similar_lyrics.sort(key=lambda x: x[1], reverse=True)
            return similar_lyrics[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to find similar lyrics: {e}")
            return []

class AILyricWriter:
    """Main AI Lyric Writing Service with consent and similarity checks"""
    
    def __init__(self, db_path: str = "soulbridge.db"):
        self.consent_manager = ConsentManager(db_path)
        self.lyric_db = LyricDatabase(db_path)
        self.similarity_threshold = 0.85
    
    def generate_lyrics(
        self,
        prompt: str,
        genre: str = "pop",
        mood: str = "neutral",
        language: str = "en",
        user_id: str = None,
        check_similarity: bool = True
    ) -> Dict[str, Any]:
        """Generate lyrics with consent and similarity checks"""
        
        try:
            # Step 1: Check for similar existing lyrics if requested
            if check_similarity:
                similar_lyrics = self.lyric_db.find_similar_lyrics(prompt, self.similarity_threshold)
                if similar_lyrics:
                    logger.warning(f"Found {len(similar_lyrics)} similar lyrics above threshold")
                    return {
                        'success': False,
                        'error': 'Similar lyrics found',
                        'similar_count': len(similar_lyrics),
                        'similar_lyrics': [
                            {
                                'title': lyric.title,
                                'artist_id': lyric.artist_id,
                                'similarity_score': score,
                                'consent_status': lyric.consent_status
                            }
                            for lyric, score in similar_lyrics[:3]  # Show top 3
                        ]
                    }
            
            # Step 2: Generate new lyrics (placeholder - would integrate with LLM)
            generated_lyrics = self._generate_lyrics_with_ai(prompt, genre, mood, language)
            
            # Step 3: Create lyric record
            lyric_id = hashlib.md5(f"{prompt}{genre}{mood}{datetime.now()}".encode()).hexdigest()
            
            lyric_data = LyricData(
                lyric_id=lyric_id,
                artist_id=user_id or "ai_generated",
                title=f"AI Generated - {genre.title()} {mood.title()}",
                lyrics=generated_lyrics,
                genre=genre,
                mood=mood,
                language=language,
                embedding=None,  # Will be generated during storage
                created_date=datetime.now(timezone.utc),
                consent_status="ai_generated"
            )
            
            # Step 4: Store the generated lyric
            if self.lyric_db.store_lyric(lyric_data):
                return {
                    'success': True,
                    'lyric_id': lyric_id,
                    'lyrics': generated_lyrics,
                    'metadata': {
                        'genre': genre,
                        'mood': mood,
                        'language': language,
                        'generated_at': lyric_data.created_date.isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to store generated lyrics'
                }
                
        except Exception as e:
            logger.error(f"❌ Lyric generation failed: {e}")
            return {
                'success': False,
                'error': f'Generation failed: {str(e)}'
            }
    
    def _generate_lyrics_with_ai(self, prompt: str, genre: str, mood: str, language: str) -> str:
        """Generate lyrics using AI (placeholder for actual LLM integration)"""
        
        # This is a placeholder - in production, this would integrate with:
        # - OpenAI GPT models
        # - Anthropic Claude
        # - Local language models
        # - Custom fine-tuned models
        
        genre_styles = {
            'trap': "Street life, success, struggle, flexing, money, loyalty",
            'drill': "Raw reality, street stories, hard life, survival, respect",
            'reggaeton': "Party vibes, dancing, romance, Latin culture, celebration",
            'bachata-trap': "Love stories, heartbreak, fusion culture, emotional depth",
            'boom-bap': "Lyrical prowess, storytelling, classic hip-hop, consciousness",
            'rnb': "Love, relationships, smooth vibes, emotional connection, soulful"
        }
        
        mood_tones = {
            'happy': "uplifting, positive, energetic, celebratory",
            'sad': "melancholic, introspective, emotional, heartfelt",
            'angry': "aggressive, powerful, intense, confrontational",
            'romantic': "loving, passionate, intimate, tender",
            'confident': "assertive, strong, self-assured, empowering"
        }
        
        style_guide = genre_styles.get(genre, "general music themes")
        tone_guide = mood_tones.get(mood, "balanced emotional tone")
        
        # Simple template-based generation (would be replaced with actual AI)
        generated = f"""[Verse 1]
{prompt.capitalize()}, feeling the {mood} vibes
In this {genre} style, where the music thrives
Every line crafted with {tone_guide}
{style_guide}, that's how we survive

[Chorus]
This is the sound of {genre}
{mood.title()} melodies that we prefer
Generated lyrics with AI precision
Creating music with lyrical vision

[Verse 2]
Building on the theme of {prompt.lower()}
With {mood} energy, making it supreme
{genre.title()} beats with {tone_guide}
This is how we make the music dream

[Outro]
AI generated, but still authentic
{genre.title()} vibes, mood so magnetic
{prompt.capitalize()} inspiration, that's our way
Creating lyrics for another day"""

        return generated
    
    def check_consent_compliance(self, artist_id: str, use_case: str = "generation") -> Dict[str, Any]:
        """Check if artist consent allows the specified use case"""
        consent = self.consent_manager.get_consent(artist_id)
        
        if not consent:
            return {
                'compliant': False,
                'reason': 'No consent record found',
                'requires_consent': True
            }
        
        if use_case == "training" and not consent.training_allowed:
            return {
                'compliant': False,
                'reason': 'Training not allowed',
                'requires_consent': True
            }
        
        if use_case == "commercial" and not consent.commercial_use:
            return {
                'compliant': False,
                'reason': 'Commercial use not allowed',
                'attribution_required': consent.attribution_required
            }
        
        # Check expiration
        if consent.consent_expires and datetime.now(timezone.utc) > consent.consent_expires:
            return {
                'compliant': False,
                'reason': 'Consent expired',
                'expired_date': consent.consent_expires.isoformat()
            }
        
        return {
            'compliant': True,
            'artist_name': consent.artist_name,
            'attribution_required': consent.attribution_required,
            'restrictions': consent.restrictions
        }

# Service factory function
def create_lyric_writer_service(db_path: str = "soulbridge.db") -> AILyricWriter:
    """Create and configure lyric writer service"""
    try:
        service = AILyricWriter(db_path)
        logger.info("✅ AI Lyric Writer Service initialized")
        return service
    except Exception as e:
        logger.error(f"❌ Failed to initialize lyric writer service: {e}")
        raise