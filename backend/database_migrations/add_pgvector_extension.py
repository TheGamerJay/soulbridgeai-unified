"""
pgvector Extension Migration for Embedding-based Lyric Retrieval
Enables vector similarity search using PostgreSQL pgvector extension
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def run_pgvector_migration():
    """Add pgvector extension and create vector tables for lyric embeddings"""
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment")
        return False
    
    # Handle postgres:// vs postgresql:// URL format
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        logger.info("🔗 Connected to PostgreSQL database")
        
        # Check if pgvector extension is available
        cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector';")
        pgvector_available = cur.fetchone()
        
        if not pgvector_available:
            logger.warning("⚠️  pgvector extension not available on this PostgreSQL instance")
            logger.info("💡 You may need to install pgvector or use a PostgreSQL provider that supports it")
            return False
        
        # Create pgvector extension
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("✅ pgvector extension enabled")
        except Exception as e:
            logger.error(f"❌ Failed to create pgvector extension: {e}")
            return False
        
        # Create lyric_embeddings table for vector similarity search
        create_embeddings_table = """
        CREATE TABLE IF NOT EXISTS lyric_embeddings (
            id SERIAL PRIMARY KEY,
            lyric_id VARCHAR(100) UNIQUE NOT NULL,
            artist_id VARCHAR(100) NOT NULL,
            title TEXT NOT NULL,
            lyrics_excerpt TEXT NOT NULL,
            full_lyrics TEXT,
            genre VARCHAR(50),
            mood VARCHAR(50),
            language VARCHAR(10) DEFAULT 'en',
            embedding vector(384),  -- 384 dimensions for all-MiniLM-L6-v2
            consent_status VARCHAR(20) DEFAULT 'pending',
            similarity_threshold FLOAT DEFAULT 0.85,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT valid_consent_status CHECK (consent_status IN ('granted', 'denied', 'pending', 'expired'))
        );
        """
        cur.execute(create_embeddings_table)
        logger.info("✅ Created lyric_embeddings table")
        
        # Create index on embedding column for faster similarity searches
        create_embedding_index = """
        CREATE INDEX IF NOT EXISTS lyric_embeddings_embedding_idx 
        ON lyric_embeddings 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
        cur.execute(create_embedding_index)
        logger.info("✅ Created vector similarity search index")
        
        # Create artist_consent table for consent management
        create_consent_table = """
        CREATE TABLE IF NOT EXISTS artist_consent (
            id SERIAL PRIMARY KEY,
            artist_id VARCHAR(100) UNIQUE NOT NULL,
            artist_name VARCHAR(200) NOT NULL,
            consent_given BOOLEAN DEFAULT FALSE,
            consent_date TIMESTAMP,
            consent_expires TIMESTAMP,
            training_allowed BOOLEAN DEFAULT FALSE,
            commercial_use BOOLEAN DEFAULT FALSE,
            attribution_required BOOLEAN DEFAULT TRUE,
            restrictions JSONB DEFAULT '{}',
            consent_version VARCHAR(10) DEFAULT '1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(create_consent_table)
        logger.info("✅ Created artist_consent table")
        
        # Create function to update updated_at timestamp
        create_update_function = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
        cur.execute(create_update_function)
        
        # Create triggers for updated_at
        create_triggers = """
        DROP TRIGGER IF EXISTS update_lyric_embeddings_updated_at ON lyric_embeddings;
        CREATE TRIGGER update_lyric_embeddings_updated_at
            BEFORE UPDATE ON lyric_embeddings
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_artist_consent_updated_at ON artist_consent;
        CREATE TRIGGER update_artist_consent_updated_at
            BEFORE UPDATE ON artist_consent
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        cur.execute(create_triggers)
        logger.info("✅ Created update triggers")
        
        # Create similarity search function
        create_similarity_function = """
        CREATE OR REPLACE FUNCTION find_similar_lyrics(
            query_embedding vector(384),
            similarity_threshold FLOAT DEFAULT 0.7,
            max_results INT DEFAULT 10
        )
        RETURNS TABLE (
            lyric_id VARCHAR(100),
            artist_id VARCHAR(100),
            title TEXT,
            lyrics_excerpt TEXT,
            genre VARCHAR(50),
            mood VARCHAR(50),
            similarity FLOAT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                le.lyric_id,
                le.artist_id,
                le.title,
                le.lyrics_excerpt,
                le.genre,
                le.mood,
                (1 - (le.embedding <=> query_embedding)) as similarity
            FROM lyric_embeddings le
            JOIN artist_consent ac ON le.artist_id = ac.artist_id
            WHERE 
                ac.consent_given = TRUE
                AND ac.training_allowed = TRUE
                AND (1 - (le.embedding <=> query_embedding)) >= similarity_threshold
            ORDER BY le.embedding <=> query_embedding
            LIMIT max_results;
        END;
        $$ LANGUAGE plpgsql;
        """
        cur.execute(create_similarity_function)
        logger.info("✅ Created similarity search function")
        
        # Insert some sample consent data
        sample_consent = """
        INSERT INTO artist_consent (
            artist_id, artist_name, consent_given, consent_date,
            training_allowed, commercial_use, attribution_required
        ) VALUES 
        ('sample_artist_1', 'Sample Artist One', TRUE, CURRENT_TIMESTAMP, TRUE, TRUE, TRUE),
        ('sample_artist_2', 'Sample Artist Two', TRUE, CURRENT_TIMESTAMP, TRUE, FALSE, TRUE),
        ('sample_artist_3', 'Sample Artist Three', FALSE, NULL, FALSE, FALSE, TRUE)
        ON CONFLICT (artist_id) DO NOTHING;
        """
        cur.execute(sample_consent)
        logger.info("✅ Added sample consent records")
        
        cur.close()
        conn.close()
        
        logger.info("🎯 pgvector migration completed successfully!")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ PostgreSQL error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def check_pgvector_status():
    """Check if pgvector extension is properly installed"""
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        return {"status": "error", "message": "DATABASE_URL not configured"}
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check extension
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        extension_installed = cur.fetchone()
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('lyric_embeddings', 'artist_consent')
            AND table_schema = 'public';
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        # Check function
        cur.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name = 'find_similar_lyrics'
            AND routine_schema = 'public';
        """)
        function_exists = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "extension_installed": bool(extension_installed),
            "tables_created": sorted(tables),
            "similarity_function": bool(function_exists),
            "ready": bool(extension_installed and len(tables) == 2 and function_exists)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Running pgvector migration...")
    success = run_pgvector_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        
        # Check status
        status = check_pgvector_status()
        print(f"\n📊 Status: {json.dumps(status, indent=2)}")
    else:
        print("\n❌ Migration failed!")