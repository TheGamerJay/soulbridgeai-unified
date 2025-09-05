"""
Vector-Enhanced Lyric Service
Integrates pgvector for semantic similarity search in lyric generation
"""

import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import os

logger = logging.getLogger(__name__)

class VectorLyricService:
    """Service for vector-based lyric similarity and retrieval"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize vector lyric service"""
        self.model_name = model_name
        self.model = None
        self.db_url = os.environ.get('DATABASE_URL')
        
        if self.db_url and self.db_url.startswith('postgres://'):
            self.db_url = self.db_url.replace('postgres://', 'postgresql://', 1)
        
        self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.model = None
    
    def _get_db_connection(self):
        """Get database connection"""
        if not self.db_url:
            raise Exception("DATABASE_URL not configured")
        return psycopg2.connect(self.db_url)
    
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
    
    def store_lyric_embedding(
        self,
        lyric_id: str,
        artist_id: str,
        title: str,
        lyrics: str,
        genre: str = "unknown",
        mood: str = "neutral",
        language: str = "en"
    ) -> bool:
        """Store lyric with its embedding in the vector database"""
        
        # Generate embedding
        embedding = self.generate_embedding(lyrics)
        if embedding is None:
            logger.error("Failed to generate embedding for lyrics")
            return False
        
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # Extract excerpt (first 200 chars)
            lyrics_excerpt = lyrics[:200] + "..." if len(lyrics) > 200 else lyrics
            
            # Insert lyric embedding
            insert_query = """
            INSERT INTO lyric_embeddings (
                lyric_id, artist_id, title, lyrics_excerpt, full_lyrics,
                genre, mood, language, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (lyric_id) 
            DO UPDATE SET
                title = EXCLUDED.title,
                lyrics_excerpt = EXCLUDED.lyrics_excerpt,
                full_lyrics = EXCLUDED.full_lyrics,
                genre = EXCLUDED.genre,
                mood = EXCLUDED.mood,
                language = EXCLUDED.language,
                embedding = EXCLUDED.embedding,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            cur.execute(insert_query, (
                lyric_id, artist_id, title, lyrics_excerpt, lyrics,
                genre, mood, language, embedding.tolist()
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Stored embedding for lyric: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing lyric embedding: {e}")
            return False
    
    def find_similar_lyrics(
        self,
        query_text: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        genre_filter: Optional[str] = None,
        mood_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find similar lyrics using vector similarity search"""
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)
        if query_embedding is None:
            logger.error("Failed to generate query embedding")
            return []
        
        try:
            conn = self._get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query with optional filters
            base_query = """
            SELECT 
                le.lyric_id,
                le.artist_id,
                ac.artist_name,
                le.title,
                le.lyrics_excerpt,
                le.full_lyrics,
                le.genre,
                le.mood,
                le.language,
                (1 - (le.embedding <=> %s::vector)) as similarity
            FROM lyric_embeddings le
            JOIN artist_consent ac ON le.artist_id = ac.artist_id
            WHERE 
                ac.consent_given = TRUE
                AND ac.training_allowed = TRUE
                AND (1 - (le.embedding <=> %s::vector)) >= %s
            """
            
            params = [query_embedding.tolist(), query_embedding.tolist(), similarity_threshold]
            
            # Add optional filters
            if genre_filter:
                base_query += " AND le.genre = %s"
                params.append(genre_filter)
            
            if mood_filter:
                base_query += " AND le.mood = %s"
                params.append(mood_filter)
            
            base_query += """
            ORDER BY le.embedding <=> %s::vector
            LIMIT %s;
            """
            params.extend([query_embedding.tolist(), max_results])
            
            cur.execute(base_query, params)
            results = cur.fetchall()
            
            cur.close()
            conn.close()
            
            # Convert to list of dicts
            similar_lyrics = []
            for row in results:
                similar_lyrics.append({
                    'lyric_id': row['lyric_id'],
                    'artist_id': row['artist_id'],
                    'artist_name': row['artist_name'],
                    'title': row['title'],
                    'lyrics_excerpt': row['lyrics_excerpt'],
                    'full_lyrics': row['full_lyrics'],
                    'genre': row['genre'],
                    'mood': row['mood'],
                    'language': row['language'],
                    'similarity': float(row['similarity'])
                })
            
            logger.info(f"✅ Found {len(similar_lyrics)} similar lyrics")
            return similar_lyrics
            
        except Exception as e:
            logger.error(f"❌ Error finding similar lyrics: {e}")
            return []
    
    def get_artist_consent(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """Get artist consent information"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM artist_consent 
                WHERE artist_id = %s
            """, (artist_id,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting artist consent: {e}")
            return None
    
    def update_artist_consent(
        self,
        artist_id: str,
        artist_name: str,
        consent_given: bool,
        training_allowed: bool = False,
        commercial_use: bool = False,
        attribution_required: bool = True,
        restrictions: Dict[str, Any] = None
    ) -> bool:
        """Update artist consent record"""
        
        if restrictions is None:
            restrictions = {}
        
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            consent_date = datetime.now(timezone.utc) if consent_given else None
            
            insert_query = """
            INSERT INTO artist_consent (
                artist_id, artist_name, consent_given, consent_date,
                training_allowed, commercial_use, attribution_required, restrictions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (artist_id)
            DO UPDATE SET
                artist_name = EXCLUDED.artist_name,
                consent_given = EXCLUDED.consent_given,
                consent_date = EXCLUDED.consent_date,
                training_allowed = EXCLUDED.training_allowed,
                commercial_use = EXCLUDED.commercial_use,
                attribution_required = EXCLUDED.attribution_required,
                restrictions = EXCLUDED.restrictions,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            cur.execute(insert_query, (
                artist_id, artist_name, consent_given, consent_date,
                training_allowed, commercial_use, attribution_required,
                json.dumps(restrictions)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Updated consent for artist: {artist_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating artist consent: {e}")
            return False
    
    def get_lyric_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored lyrics and embeddings"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get basic counts
            cur.execute("SELECT COUNT(*) as total_lyrics FROM lyric_embeddings;")
            total_lyrics = cur.fetchone()['total_lyrics']
            
            cur.execute("SELECT COUNT(*) as total_artists FROM artist_consent;")
            total_artists = cur.fetchone()['total_artists']
            
            cur.execute("""
                SELECT COUNT(*) as consenting_artists 
                FROM artist_consent 
                WHERE consent_given = TRUE AND training_allowed = TRUE;
            """)
            consenting_artists = cur.fetchone()['consenting_artists']
            
            # Get genre distribution
            cur.execute("""
                SELECT genre, COUNT(*) as count 
                FROM lyric_embeddings 
                GROUP BY genre 
                ORDER BY count DESC 
                LIMIT 10;
            """)
            genre_stats = [dict(row) for row in cur.fetchall()]
            
            # Get mood distribution
            cur.execute("""
                SELECT mood, COUNT(*) as count 
                FROM lyric_embeddings 
                GROUP BY mood 
                ORDER BY count DESC 
                LIMIT 10;
            """)
            mood_stats = [dict(row) for row in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            return {
                'total_lyrics': total_lyrics,
                'total_artists': total_artists,
                'consenting_artists': consenting_artists,
                'consent_rate': (consenting_artists / total_artists * 100) if total_artists > 0 else 0,
                'genre_distribution': genre_stats,
                'mood_distribution': mood_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting lyric statistics: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of vector lyric service"""
        health = {
            'model_loaded': self.model is not None,
            'database_connected': False,
            'pgvector_enabled': False,
            'tables_exist': False,
            'embedding_dimensions': 384 if self.model else None
        }
        
        try:
            # Test database connection
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # Check pgvector extension
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            health['pgvector_enabled'] = cur.fetchone() is not None
            
            # Check tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('lyric_embeddings', 'artist_consent')
                AND table_schema = 'public';
            """)
            tables = [row[0] for row in cur.fetchall()]
            health['tables_exist'] = len(tables) == 2
            health['database_connected'] = True
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            health['error'] = str(e)
        
        health['service_ready'] = all([
            health['model_loaded'],
            health['database_connected'],
            health['pgvector_enabled'],
            health['tables_exist']
        ])
        
        return health

# Factory function
def create_vector_lyric_service() -> VectorLyricService:
    """Create vector lyric service instance"""
    return VectorLyricService()