"""
SoulBridge AI - Music Library Service
Handles music and mini studio tracks in the unified library
Extracted from backend/unified_library.py with improvements
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class MusicService:
    """Service for managing music library content"""
    
    def __init__(self, database=None):
        self.database = database
        self.supported_formats = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        self.safe_directories = {'static/uploads', 'static/library', 'temp', 'output', 'mini_studio_output'}
    
    def add_track(self, user_id: int, title: str, file_path: str = None,
                  source_type: str = 'music', track_type: str = 'generated',
                  tags: str = '', metadata: Dict = None) -> Optional[int]:
        """Add a music track to the library"""
        try:
            if not self.database:
                logger.error("Database not available")
                return None
            
            # Calculate file info if file exists
            duration_seconds = 0
            file_size_bytes = 0
            
            if file_path and os.path.exists(file_path):
                try:
                    file_size_bytes = os.path.getsize(file_path)
                    # TODO: Add audio duration calculation when audio libraries are available
                    duration_seconds = self._estimate_duration(file_size_bytes)
                except Exception as e:
                    logger.warning(f"Could not get file info for {file_path}: {e}")
            
            # Prepare track data
            track_data = {
                'title': title,
                'file_path': file_path,
                'source_type': source_type,
                'track_type': track_type,
                'tags': tags,
                'duration_seconds': duration_seconds,
                'file_size_bytes': file_size_bytes,
                'is_favorite': False,
                'play_count': 0,
                'created_at': datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add to library using the existing user_library table structure
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            content_type = 'mini_studio' if source_type == 'mini_studio' else 'music'
            
            track_id = library_manager.add_content(
                user_id=user_id,
                content_type=content_type,
                title=title,
                content=f"Music Track: {title}\nFile: {file_path or 'No file'}\nTags: {tags}",
                metadata=track_data
            )
            
            if track_id:
                logger.info(f"🎵 Added {source_type} track '{title}' for user {user_id}")
            
            return track_id
            
        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            return None
    
    def get_user_tracks(self, user_id: int, source_type: str = None, 
                       track_type: str = None, favorites_only: bool = False) -> List[Dict]:
        """Get user's music tracks with filtering"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            # Get all music content
            music_content = library_manager.get_user_library(user_id, 'music')
            studio_content = library_manager.get_user_library(user_id, 'mini_studio')
            
            # Combine and filter
            all_tracks = []
            
            if not source_type or source_type == 'music':
                all_tracks.extend([self._format_track_data(item) for item in music_content])
            
            if not source_type or source_type == 'mini_studio':
                all_tracks.extend([self._format_track_data(item) for item in studio_content])
            
            # Apply filters
            if track_type:
                all_tracks = [track for track in all_tracks if track.get('track_type') == track_type]
            
            if favorites_only:
                all_tracks = [track for track in all_tracks if track.get('is_favorite', False)]
            
            # Sort by creation date (newest first)
            all_tracks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"🎶 Retrieved {len(all_tracks)} tracks for user {user_id}")
            return all_tracks
            
        except Exception as e:
            logger.error(f"Failed to get user tracks: {e}")
            return []
    
    def get_track(self, track_id: int, user_id: int) -> Optional[Dict]:
        """Get specific track by ID"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            track_data = library_manager.get_content_by_id(user_id, track_id)
            if not track_data:
                return None
            
            # Check if it's a music-related content type
            if track_data.get('content_type') not in ['music', 'mini_studio']:
                return None
            
            return self._format_track_data(track_data)
            
        except Exception as e:
            logger.error(f"Failed to get track: {e}")
            return None
    
    def update_track(self, track_id: int, user_id: int, updates: Dict) -> bool:
        """Update track details"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            # Get current track data
            current_track = library_manager.get_content_by_id(user_id, track_id)
            if not current_track:
                return False
            
            # Update metadata
            current_metadata = current_track.get('metadata', {})
            
            # Update allowed fields
            allowed_fields = ['title', 'tags', 'is_favorite']
            update_data = {}
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'title':
                        update_data['title'] = value
                    else:
                        current_metadata[field] = value
            
            if current_metadata != current_track.get('metadata', {}):
                update_data['metadata'] = current_metadata
            
            if update_data:
                success = library_manager.update_content(user_id, track_id, update_data)
                if success:
                    logger.info(f"🎵 Updated track {track_id} for user {user_id}")
                return success
            
            return True  # No updates needed
            
        except Exception as e:
            logger.error(f"Failed to update track: {e}")
            return False
    
    def delete_track(self, track_id: int, user_id: int, delete_file: bool = True) -> bool:
        """Delete track and optionally remove file"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            # Get track info before deletion
            track_data = library_manager.get_content_by_id(user_id, track_id)
            if not track_data:
                return False
            
            file_path = track_data.get('metadata', {}).get('file_path')
            
            # Delete from library
            success = library_manager.delete_content(user_id, track_id)
            
            if success and delete_file and file_path:
                self._delete_track_file(file_path)
            
            if success:
                logger.info(f"🗑️ Deleted track {track_id} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete track: {e}")
            return False
    
    def toggle_favorite(self, track_id: int, user_id: int) -> Dict[str, Any]:
        """Toggle favorite status for a track"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            # Get current track
            track_data = library_manager.get_content_by_id(user_id, track_id)
            if not track_data:
                return {'success': False, 'error': 'Track not found'}
            
            # Toggle favorite in metadata
            metadata = track_data.get('metadata', {})
            current_favorite = metadata.get('is_favorite', False)
            new_favorite = not current_favorite
            
            success = self.update_track(track_id, user_id, {'is_favorite': new_favorite})
            
            if success:
                logger.info(f"⭐ Toggled favorite for track {track_id}: {new_favorite}")
                return {'success': True, 'is_favorite': new_favorite}
            else:
                return {'success': False, 'error': 'Failed to update favorite status'}
            
        except Exception as e:
            logger.error(f"Failed to toggle favorite: {e}")
            return {'success': False, 'error': str(e)}
    
    def record_play(self, track_id: int, user_id: int) -> bool:
        """Record a play/listen event"""
        try:
            from .library_manager import LibraryManager
            library_manager = LibraryManager(self.database)
            
            # Get current track
            track_data = library_manager.get_content_by_id(user_id, track_id)
            if not track_data:
                return False
            
            # Update play count in metadata
            metadata = track_data.get('metadata', {})
            play_count = metadata.get('play_count', 0) + 1
            metadata['play_count'] = play_count
            metadata['last_played'] = datetime.now().isoformat()
            
            success = library_manager.update_content(user_id, track_id, {'metadata': metadata})
            
            if success:
                logger.info(f"▶️ Recorded play for track {track_id} (count: {play_count})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to record play: {e}")
            return False
    
    def get_library_stats(self, user_id: int) -> Dict[str, Any]:
        """Get music library statistics"""
        try:
            tracks = self.get_user_tracks(user_id)
            
            if not tracks:
                return {
                    'total_tracks': 0,
                    'music_tracks': 0,
                    'studio_tracks': 0,
                    'favorites': 0,
                    'total_size_mb': 0,
                    'most_played': None,
                    'total_plays': 0
                }
            
            # Calculate stats
            music_tracks = len([t for t in tracks if t.get('source_type') == 'music'])
            studio_tracks = len([t for t in tracks if t.get('source_type') == 'mini_studio'])
            favorites = len([t for t in tracks if t.get('is_favorite', False)])
            
            total_size_bytes = sum(t.get('file_size_bytes', 0) for t in tracks)
            total_plays = sum(t.get('play_count', 0) for t in tracks)
            
            # Find most played track
            most_played = max(tracks, key=lambda t: t.get('play_count', 0), default=None)
            if most_played and most_played.get('play_count', 0) == 0:
                most_played = None
            
            return {
                'total_tracks': len(tracks),
                'music_tracks': music_tracks,
                'studio_tracks': studio_tracks,
                'favorites': favorites,
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
                'most_played': most_played,
                'total_plays': total_plays
            }
            
        except Exception as e:
            logger.error(f"Failed to get library stats: {e}")
            return {'error': str(e)}
    
    def _format_track_data(self, library_item: Dict) -> Dict:
        """Format library item as track data"""
        metadata = library_item.get('metadata', {})
        
        return {
            'id': library_item.get('id'),
            'title': library_item.get('title'),
            'content_type': library_item.get('content_type'),
            'created_at': library_item.get('created_at'),
            
            # Extract from metadata
            'file_path': metadata.get('file_path'),
            'source_type': metadata.get('source_type', 'music'),
            'track_type': metadata.get('track_type', 'generated'),
            'tags': metadata.get('tags', ''),
            'duration_seconds': metadata.get('duration_seconds', 0),
            'file_size_bytes': metadata.get('file_size_bytes', 0),
            'is_favorite': metadata.get('is_favorite', False),
            'play_count': metadata.get('play_count', 0),
            'last_played': metadata.get('last_played'),
            
            # Full metadata for advanced use
            'metadata': metadata
        }
    
    def _estimate_duration(self, file_size_bytes: int) -> int:
        """Rough estimation of audio duration from file size"""
        try:
            # Very rough estimate: ~1MB per minute for typical MP3
            # This is just a placeholder until proper audio analysis is available
            estimated_minutes = file_size_bytes / (1024 * 1024)
            return int(estimated_minutes * 60)
        except:
            return 0
    
    def _delete_track_file(self, file_path: str) -> bool:
        """Safely delete track file"""
        try:
            if not file_path or not os.path.exists(file_path):
                return False
            
            # Security check: only delete files in safe directories
            if not any(safe_dir in file_path for safe_dir in self.safe_directories):
                logger.warning(f"Refusing to delete file outside safe directories: {file_path}")
                return False
            
            os.remove(file_path)
            logger.info(f"🗑️ Deleted track file: {file_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not delete track file {file_path}: {e}")
            return False
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file for library addition"""
        try:
            if not file_path or not os.path.exists(file_path):
                return {'valid': False, 'error': 'File does not exist'}
            
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext not in self.supported_formats:
                return {
                    'valid': False, 
                    'error': f'Unsupported format. Supported: {", ".join(self.supported_formats)}'
                }
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size = 50 * 1024 * 1024  # 50MB limit
            
            if file_size > max_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum: {max_size // (1024*1024)}MB'
                }
            
            if file_size < 1024:  # Less than 1KB
                return {'valid': False, 'error': 'File appears to be empty'}
            
            return {
                'valid': True,
                'file_size_bytes': file_size,
                'format': ext,
                'estimated_duration': self._estimate_duration(file_size)
            }
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return {'valid': False, 'error': str(e)}