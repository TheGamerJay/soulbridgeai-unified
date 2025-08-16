#!/usr/bin/env python3
"""
Unified Library System
Smart library that handles tracks from both regular music and mini studio
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)

class UnifiedLibraryManager:
    """Manages the unified music library for both regular music and mini studio"""
    
    def __init__(self, db, Song):
        self.db = db
        self.Song = Song
    
    def add_track(self, user_id: int, title: str, file_path: str, 
                  source_type: str = 'music', track_type: str = 'generated', 
                  tags: str = '', metadata: Dict = None) -> Optional[int]:
        """
        Add a track to the unified library
        
        Args:
            user_id: User ID
            title: Track title
            file_path: Path to audio file
            source_type: 'music' or 'mini_studio'
            track_type: 'generated', 'vocals', 'instrumental', 'mixed', 'cover_art'
            tags: Track tags/genres
            metadata: Additional metadata (dict)
        
        Returns:
            Track ID if successful, None if failed
        """
        try:
            # Calculate file info if file exists
            duration_seconds = 0
            file_size_bytes = 0
            
            if file_path and os.path.exists(file_path):
                try:
                    file_size_bytes = os.path.getsize(file_path)
                    # TODO: Add audio duration calculation when audio packages available
                except:
                    pass
            
            # Create new track record
            track = self.Song(
                user_id=user_id,
                title=title,
                tags=tags,
                file_path=file_path,
                source_type=source_type,
                track_type=track_type,
                duration_seconds=duration_seconds,
                file_size_bytes=file_size_bytes,
                metadata_json=json.dumps(metadata or {}),
                is_favorite=False,
                likes=0,
                play_count=0,
                created_at=datetime.utcnow()
            )
            
            self.db.session.add(track)
            self.db.session.commit()
            
            logger.info(f"📀 Added {source_type} track '{title}' for user {user_id}")
            return track.id
            
        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            self.db.session.rollback()
            return None
    
    def get_user_library(self, user_id: int, source_type: str = None, 
                        track_type: str = None, favorites_only: bool = False) -> List[Dict]:
        """
        Get user's library with optional filtering
        
        Args:
            user_id: User ID
            source_type: Filter by 'music' or 'mini_studio' (optional)
            track_type: Filter by track type (optional)
            favorites_only: Only return favorites (optional)
        
        Returns:
            List of track dictionaries
        """
        try:
            query = self.Song.query.filter_by(user_id=user_id)
            
            if source_type:
                query = query.filter_by(source_type=source_type)
            
            if track_type:
                query = query.filter_by(track_type=track_type)
            
            if favorites_only:
                query = query.filter_by(is_favorite=True)
            
            tracks = query.order_by(self.Song.created_at.desc()).all()
            
            return [self._track_to_dict(track) for track in tracks]
            
        except Exception as e:
            logger.error(f"Failed to get library: {e}")
            return []
    
    def get_track(self, track_id: int, user_id: int) -> Optional[Dict]:
        """Get specific track if owned by user"""
        try:
            track = self.Song.query.filter_by(id=track_id, user_id=user_id).first()
            return self._track_to_dict(track) if track else None
        except Exception as e:
            logger.error(f"Failed to get track: {e}")
            return None
    
    def update_track(self, track_id: int, user_id: int, updates: Dict) -> bool:
        """Update track details"""
        try:
            track = self.Song.query.filter_by(id=track_id, user_id=user_id).first()
            if not track:
                return False
            
            # Update allowed fields
            allowed_fields = ['title', 'tags', 'is_favorite', 'metadata_json']
            for field, value in updates.items():
                if field in allowed_fields and hasattr(track, field):
                    if field == 'metadata_json' and isinstance(value, dict):
                        setattr(track, field, json.dumps(value))
                    else:
                        setattr(track, field, value)
            
            self.db.session.commit()
            logger.info(f"📝 Updated track {track_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update track: {e}")
            self.db.session.rollback()
            return False
    
    def delete_track(self, track_id: int, user_id: int) -> bool:
        """Delete track and optionally remove file"""
        try:
            track = self.Song.query.filter_by(id=track_id, user_id=user_id).first()
            if not track:
                return False
            
            # Store file path before deletion
            file_path = track.file_path
            
            # Delete from database
            self.db.session.delete(track)
            self.db.session.commit()
            
            # Optionally delete file (be careful!)
            if file_path and os.path.exists(file_path):
                try:
                    # Only delete files in safe directories
                    safe_dirs = ['static/uploads', 'static/library', 'temp', 'output']
                    if any(safe_dir in file_path for safe_dir in safe_dirs):
                        os.remove(file_path)
                        logger.info(f"🗑️ Deleted file: {file_path}")
                except Exception as file_error:
                    logger.warning(f"Could not delete file {file_path}: {file_error}")
            
            logger.info(f"🗑️ Deleted track {track_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete track: {e}")
            self.db.session.rollback()
            return False
    
    def record_play(self, track_id: int, user_id: int) -> bool:
        """Record a play/listen event"""
        try:
            track = self.Song.query.filter_by(id=track_id, user_id=user_id).first()
            if not track:
                return False
            
            track.play_count = (track.play_count or 0) + 1
            track.last_played = datetime.utcnow()
            
            self.db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to record play: {e}")
            return False
    
    def toggle_favorite(self, track_id: int, user_id: int) -> bool:
        """Toggle favorite status"""
        try:
            track = self.Song.query.filter_by(id=track_id, user_id=user_id).first()
            if not track:
                return False
            
            track.is_favorite = not (track.is_favorite or False)
            self.db.session.commit()
            
            logger.info(f"⭐ Toggled favorite for track {track_id}: {track.is_favorite}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to toggle favorite: {e}")
            return False
    
    def get_library_stats(self, user_id: int) -> Dict:
        """Get library statistics"""
        try:
            total_tracks = self.Song.query.filter_by(user_id=user_id).count()
            music_tracks = self.Song.query.filter_by(user_id=user_id, source_type='music').count()
            studio_tracks = self.Song.query.filter_by(user_id=user_id, source_type='mini_studio').count()
            favorites = self.Song.query.filter_by(user_id=user_id, is_favorite=True).count()
            
            # Calculate total file size
            tracks_with_size = self.Song.query.filter_by(user_id=user_id).all()
            total_size_bytes = sum(track.file_size_bytes or 0 for track in tracks_with_size)
            
            return {
                'total_tracks': total_tracks,
                'music_tracks': music_tracks,
                'studio_tracks': studio_tracks,
                'favorites': favorites,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'most_played': self._get_most_played_track(user_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get library stats: {e}")
            return {'error': str(e)}
    
    def _track_to_dict(self, track) -> Dict:
        """Convert track model to dictionary"""
        if not track:
            return {}
        
        try:
            metadata = json.loads(track.metadata_json or '{}')
        except:
            metadata = {}
        
        return {
            'id': track.id,
            'title': track.title,
            'tags': track.tags,
            'file_path': track.file_path,
            'source_type': getattr(track, 'source_type', 'music'),
            'track_type': getattr(track, 'track_type', 'generated'),
            'duration_seconds': getattr(track, 'duration_seconds', 0),
            'file_size_bytes': getattr(track, 'file_size_bytes', 0),
            'is_favorite': getattr(track, 'is_favorite', False),
            'likes': track.likes or 0,
            'play_count': track.play_count or 0,
            'created_at': track.created_at.isoformat() if track.created_at else None,
            'last_played': track.last_played.isoformat() if getattr(track, 'last_played', None) else None,
            'metadata': metadata
        }
    
    def _get_most_played_track(self, user_id: int) -> Optional[Dict]:
        """Get user's most played track"""
        try:
            track = self.Song.query.filter_by(user_id=user_id)\
                .order_by(self.Song.play_count.desc())\
                .first()
            return self._track_to_dict(track) if track else None
        except:
            return None