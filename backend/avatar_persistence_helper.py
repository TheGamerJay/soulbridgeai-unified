"""
Avatar Persistence Helper
Utility functions for handling avatar persistence across refreshes and deploys
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from database_utils import format_query

logger = logging.getLogger(__name__)

class AvatarPersistenceManager:
    """Manages avatar persistence with multiple storage strategies"""
    
    def __init__(self, database=None, cloud_storage=None):
        self.database = database
        self.cloud_storage = cloud_storage
        
    def save_avatar_persistent(self, user_id: int, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save avatar with multiple persistence strategies
        Priority: Database > Cloud Storage > Local File (for development)
        """
        try:
            timestamp = datetime.now().isoformat()
            avatar_data['saved_at'] = timestamp
            avatar_data['cache_buster'] = int(datetime.now().timestamp())
            
            # Strategy 1: Database (PostgreSQL/SQLite)
            db_result = self._save_to_database(user_id, avatar_data)
            if db_result['success']:
                logger.info(f"✅ Avatar saved to database for user {user_id}")
                return db_result
            
            # Strategy 2: Cloud Storage (if configured)
            if self.cloud_storage:
                cloud_result = self._save_to_cloud(user_id, avatar_data)
                if cloud_result['success']:
                    logger.info(f"✅ Avatar saved to cloud storage for user {user_id}")
                    return cloud_result
            
            # Strategy 3: Fallback to local storage (development only)
            local_result = self._save_to_local_storage(user_id, avatar_data)
            logger.warning(f"⚠️ Using local storage fallback for user {user_id}")
            return local_result
            
        except Exception as e:
            logger.error(f"❌ Failed to save avatar persistently: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_avatar_persistent(self, user_id: int) -> Dict[str, Any]:
        """
        Load avatar with cache busting and fallback strategies
        """
        try:
            # Try database first
            db_result = self._load_from_database(user_id)
            if db_result['success']:
                avatar_data = db_result['data']
                # Add cache busting to URLs
                avatar_data = self._add_cache_busting(avatar_data)
                logger.info(f"✅ Avatar loaded from database for user {user_id}")
                return {'success': True, 'data': avatar_data}
            
            # Try cloud storage
            if self.cloud_storage:
                cloud_result = self._load_from_cloud(user_id)
                if cloud_result['success']:
                    avatar_data = self._add_cache_busting(cloud_result['data'])
                    logger.info(f"✅ Avatar loaded from cloud for user {user_id}")
                    return {'success': True, 'data': avatar_data}
            
            # Try local storage
            local_result = self._load_from_local_storage(user_id)
            if local_result['success']:
                avatar_data = self._add_cache_busting(local_result['data'])
                logger.info(f"✅ Avatar loaded from local storage for user {user_id}")
                return {'success': True, 'data': avatar_data}
            
            return {'success': False, 'error': 'No avatar data found'}
            
        except Exception as e:
            logger.error(f"❌ Failed to load avatar: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_to_database(self, user_id: int, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save avatar data to database"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            avatar_json = json.dumps(avatar_data)
            
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE users 
                    SET companion_data = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (avatar_json, user_id))
            else:
                cursor.execute(format_query("""
                    UPDATE users 
                    SET companion_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """), (avatar_json, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {'success': True, 'storage': 'database'}
            else:
                conn.close()
                return {'success': False, 'error': 'User not found'}
                
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_from_database(self, user_id: int) -> Dict[str, Any]:
        """Load avatar data from database"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("SELECT companion_data FROM users WHERE id = %s"), (user_id,))
            else:
                cursor.execute(format_query("SELECT companion_data FROM users WHERE id = ?"), (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                avatar_data = json.loads(result[0])
                return {'success': True, 'data': avatar_data}
            else:
                return {'success': False, 'error': 'No avatar data found'}
                
        except Exception as e:
            logger.error(f"Database load failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_to_cloud(self, user_id: int, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save avatar to cloud storage (placeholder for S3, Supabase, etc.)"""
        try:
            # TODO: Implement cloud storage (AWS S3, Supabase Storage, Cloudinary)
            # Example for S3:
            # key = f"avatars/user_{user_id}_avatar.json"
            # self.cloud_storage.put_object(Key=key, Body=json.dumps(avatar_data))
            return {'success': False, 'error': 'Cloud storage not implemented'}
        except Exception as e:
            logger.error(f"Cloud save failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_from_cloud(self, user_id: int) -> Dict[str, Any]:
        """Load avatar from cloud storage"""
        try:
            # TODO: Implement cloud storage loading
            return {'success': False, 'error': 'Cloud storage not implemented'}
        except Exception as e:
            logger.error(f"Cloud load failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_to_local_storage(self, user_id: int, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save avatar to local file (development fallback)"""
        try:
            import os
            
            # Create avatars directory if it doesn't exist
            avatar_dir = os.path.join(os.path.dirname(__file__), 'persistent_avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # Save to file
            avatar_file = os.path.join(avatar_dir, f'user_{user_id}_avatar.json')
            with open(avatar_file, 'w') as f:
                json.dump(avatar_data, f, indent=2)
            
            return {'success': True, 'storage': 'local_file'}
            
        except Exception as e:
            logger.error(f"Local storage save failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _load_from_local_storage(self, user_id: int) -> Dict[str, Any]:
        """Load avatar from local file"""
        try:
            import os
            
            avatar_dir = os.path.join(os.path.dirname(__file__), 'persistent_avatars')
            avatar_file = os.path.join(avatar_dir, f'user_{user_id}_avatar.json')
            
            if os.path.exists(avatar_file):
                with open(avatar_file, 'r') as f:
                    avatar_data = json.load(f)
                return {'success': True, 'data': avatar_data}
            else:
                return {'success': False, 'error': 'Local avatar file not found'}
                
        except Exception as e:
            logger.error(f"Local storage load failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _add_cache_busting(self, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add cache busting parameters to image URLs"""
        try:
            import time
            
            # Use saved timestamp or current time for cache busting
            if 'saved_at' in avatar_data:
                try:
                    saved_time = datetime.fromisoformat(avatar_data['saved_at'].replace('Z', '+00:00'))
                    cache_buster = int(saved_time.timestamp())
                except:
                    cache_buster = int(time.time())
            else:
                cache_buster = int(time.time())
            
            # Add cache buster to image URLs
            for url_field in ['avatar_url', 'image_url']:
                if url_field in avatar_data and avatar_data[url_field]:
                    url = avatar_data[url_field]
                    # Add or update cache buster parameter
                    if '?' in url:
                        # Remove existing cache buster if present
                        url_parts = url.split('?')[0]
                        url = f"{url_parts}?t={cache_buster}"
                    else:
                        url = f"{url}?t={cache_buster}"
                    avatar_data[url_field] = url
            
            avatar_data['cache_buster'] = cache_buster
            return avatar_data
            
        except Exception as e:
            logger.error(f"Cache busting failed: {e}")
            return avatar_data
    
    def cleanup_old_avatars(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old avatar data to prevent storage bloat"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleanup_count = 0
            
            # TODO: Implement cleanup for each storage method
            # Database: DELETE old records
            # Cloud: Delete old files
            # Local: Remove old files
            
            return {
                'success': True,
                'cleaned_up': cleanup_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Avatar cleanup failed: {e}")
            return {'success': False, 'error': str(e)}


# Convenience functions for direct use
def save_user_avatar_persistent(user_id: int, avatar_data: Dict[str, Any], database=None) -> Dict[str, Any]:
    """Convenience function to save avatar with persistence"""
    manager = AvatarPersistenceManager(database=database)
    return manager.save_avatar_persistent(user_id, avatar_data)

def load_user_avatar_persistent(user_id: int, database=None) -> Dict[str, Any]:
    """Convenience function to load avatar with cache busting"""
    manager = AvatarPersistenceManager(database=database)
    return manager.load_avatar_persistent(user_id)