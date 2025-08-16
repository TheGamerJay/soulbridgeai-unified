#!/usr/bin/env python3
"""
Unified Library Migration
Extends the existing Song table to support both regular music and mini studio tracks
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime

def migrate_sqlite():
    """Migrate SQLite database (local development)"""
    db_path = "soulbridge.db"
    if not os.path.exists(db_path):
        print("❌ SQLite database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(song)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations = []
        
        # Add new columns for unified library
        if 'source_type' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN source_type VARCHAR(20) DEFAULT 'music'")
        
        if 'track_type' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN track_type VARCHAR(20) DEFAULT 'generated'")
        
        if 'duration_seconds' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN duration_seconds INTEGER DEFAULT 0")
        
        if 'file_size_bytes' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN file_size_bytes INTEGER DEFAULT 0")
        
        if 'metadata_json' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN metadata_json TEXT DEFAULT '{}'")
        
        if 'is_favorite' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE")
        
        if 'last_played' not in columns:
            migrations.append("ALTER TABLE song ADD COLUMN last_played TIMESTAMP")
        
        # Execute migrations
        for migration in migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
        
        # Update existing records to have proper source_type
        cursor.execute("UPDATE song SET source_type = 'music' WHERE source_type IS NULL")
        cursor.execute("UPDATE song SET track_type = 'generated' WHERE track_type IS NULL")
        
        conn.commit()
        print(f"SQLite migration completed - {len(migrations)} changes applied")
        return True
        
    except Exception as e:
        print(f"SQLite migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def migrate_postgresql():
    """Migrate PostgreSQL database (production)"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found for PostgreSQL migration")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'songs' AND table_schema = 'public'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        migrations = []
        
        # Add new columns for unified library
        if 'source_type' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN source_type VARCHAR(20) DEFAULT 'music'")
        
        if 'track_type' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN track_type VARCHAR(20) DEFAULT 'generated'")
        
        if 'duration_seconds' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN duration_seconds INTEGER DEFAULT 0")
        
        if 'file_size_bytes' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN file_size_bytes INTEGER DEFAULT 0")
        
        if 'metadata_json' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN metadata_json TEXT DEFAULT '{}'")
        
        if 'is_favorite' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN is_favorite BOOLEAN DEFAULT FALSE")
        
        if 'last_played' not in columns:
            migrations.append("ALTER TABLE songs ADD COLUMN last_played TIMESTAMP")
        
        # Execute migrations
        for migration in migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
        
        # Update existing records
        cursor.execute("UPDATE songs SET source_type = 'music' WHERE source_type IS NULL")
        cursor.execute("UPDATE songs SET track_type = 'generated' WHERE track_type IS NULL")
        
        conn.commit()
        print(f"PostgreSQL migration completed - {len(migrations)} changes applied")
        return True
        
    except Exception as e:
        print(f"PostgreSQL migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Run unified library migration"""
    print("Starting Unified Library Migration...")
    print("=" * 50)
    
    # Try SQLite first (local development)
    if migrate_sqlite():
        print("Local SQLite migration successful")
    
    # Try PostgreSQL (production)
    if migrate_postgresql():
        print("Production PostgreSQL migration successful")
    
    print("=" * 50)
    print("Unified Library Migration Complete!")
    print()
    print("New columns added:")
    print("- source_type: 'music' or 'mini_studio'")
    print("- track_type: 'generated', 'vocals', 'instrumental', 'mixed', 'cover_art'")
    print("- duration_seconds: Track length in seconds")
    print("- file_size_bytes: File size for storage management")
    print("- metadata_json: Additional track metadata")
    print("- is_favorite: User favorites")
    print("- last_played: Last play timestamp")

if __name__ == "__main__":
    main()