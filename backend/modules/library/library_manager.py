"""
SoulBridge AI - Library Manager
Unified library system for managing all user content types
Extracted from backend/unified_library.py with improvements
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from database_utils import format_query

logger = logging.getLogger(__name__)

class LibraryManager:
    """Central manager for all user library content"""
    
    def __init__(self, database=None):
        self.database = database
        self.content_types = {
            'chat': 'chat_conversations',
            'music': 'music_tracks', 
            'creative': 'creative_content',
            'fortune': 'fortune_readings',
            'horoscope': 'horoscope_readings',
            'decoder': 'decoder_sessions',
            'ai_image': 'ai_images',
            'mini_studio': 'studio_tracks'
        }
    
    def add_content(self, user_id: int, content_type: str, title: str, 
                   content: str, metadata: Dict = None) -> Optional[int]:
        """Add content to user's library"""
        try:
            if not self.database:
                logger.error("Database not available")
                return None
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Use correct placeholder for database type
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            # Insert into user_library table
            cursor.execute(f"""
                INSERT INTO user_library (user_email, title, content, content_type, created_at, metadata)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                self._get_user_email(user_id),
                title,
                content,
                content_type,
                datetime.now(),
                json.dumps(metadata or {})
            ))
            
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("SELECT LASTVAL()")
            else:
                cursor.execute("SELECT last_insert_rowid()")
            
            content_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            
            logger.info(f"📚 Added {content_type} content '{title}' for user {user_id}")
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to add content to library: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return None
    
    def get_user_library(self, user_id: int, content_type: str = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get user's library content with optional filtering"""
        try:
            if not self.database:
                return []
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return []
            
            # Build query with optional filtering
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            if content_type:
                query = f"""
                    SELECT id, title, content, content_type, created_at, metadata
                    FROM user_library 
                    WHERE user_email = {placeholder} AND content_type = {placeholder}
                    ORDER BY created_at DESC
                    LIMIT {placeholder}
                """
                cursor.execute(query, (user_email, content_type, limit))
            else:
                query = f"""
                    SELECT id, title, content, content_type, created_at, metadata
                    FROM user_library 
                    WHERE user_email = {placeholder}
                    ORDER BY created_at DESC
                    LIMIT {placeholder}
                """
                cursor.execute(query, (user_email, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            library_items = []
            for row in rows:
                try:
                    metadata = json.loads(row[5] or '{}')
                except:
                    metadata = {}
                
                library_items.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'content_type': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'metadata': metadata
                })
            
            logger.info(f"📖 Retrieved {len(library_items)} library items for user {user_id}")
            return library_items
            
        except Exception as e:
            logger.error(f"Failed to get user library: {e}")
            return []
    
    def get_content_by_id(self, user_id: int, content_id: int) -> Optional[Dict[str, Any]]:
        """Get specific content item by ID"""
        try:
            if not self.database:
                return None
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return None
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            cursor.execute(f"""
                SELECT id, title, content, content_type, created_at, metadata
                FROM user_library 
                WHERE id = {placeholder} AND user_email = {placeholder}
            """, (content_id, user_email))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            try:
                metadata = json.loads(row[5] or '{}')
            except:
                metadata = {}
            
            return {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'content_type': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get content by ID: {e}")
            return None
    
    def update_content(self, user_id: int, content_id: int, updates: Dict[str, Any]) -> bool:
        """Update content item"""
        try:
            if not self.database:
                return False
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return False
            
            # Build update query
            update_fields = []
            values = []
            
            allowed_fields = ['title', 'content', 'metadata']
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'metadata' and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                conn.close()
                return False
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                # Replace ? with %s for PostgreSQL
                update_query = ", ".join(update_fields).replace("?", "%s")
            else:
                update_query = ", ".join(update_fields)
            
            values.extend([content_id, user_email])
            
            cursor.execute(f"""
                UPDATE user_library 
                SET {update_query}
                WHERE id = {placeholder} AND user_email = {placeholder}
            """, values)
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                logger.info(f"📝 Updated library content {content_id} for user {user_id}")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update content: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def delete_content(self, user_id: int, content_id: int) -> bool:
        """Delete content from library"""
        try:
            if not self.database:
                return False
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return False
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            cursor.execute(f"""
                DELETE FROM user_library 
                WHERE id = {placeholder} AND user_email = {placeholder}
            """, (content_id, user_email))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"🗑️ Deleted library content {content_id} for user {user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete content: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def get_library_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's library statistics"""
        try:
            if not self.database:
                return {}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return {}
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*) FROM user_library WHERE user_email = {placeholder}
            """, (user_email,))
            total_items = cursor.fetchone()[0]
            
            # Get count by content type
            cursor.execute(f"""
                SELECT content_type, COUNT(*) 
                FROM user_library 
                WHERE user_email = {placeholder}
                GROUP BY content_type
            """, (user_email,))
            
            type_counts = dict(cursor.fetchall())
            
            # Get recent activity
            cursor.execute(f"""
                SELECT content_type, MAX(created_at) as last_saved
                FROM user_library 
                WHERE user_email = {placeholder}
                GROUP BY content_type
                ORDER BY last_saved DESC
                LIMIT 5
            """, (user_email,))
            
            recent_activity = []
            for row in cursor.fetchall():
                recent_activity.append({
                    'content_type': row[0],
                    'last_saved': row[1].isoformat() if row[1] else None
                })
            
            conn.close()
            
            return {
                'total_items': total_items,
                'by_type': type_counts,
                'recent_activity': recent_activity,
                'content_types_available': list(self.content_types.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get library stats: {e}")
            return {'error': str(e)}
    
    def search_library(self, user_id: int, query: str, content_type: str = None) -> List[Dict[str, Any]]:
        """Search user's library content"""
        try:
            if not self.database or not query.strip():
                return []
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            user_email = self._get_user_email(user_id)
            if not user_email:
                conn.close()
                return []
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            search_pattern = f"%{query.strip()}%"
            
            if content_type:
                cursor.execute(f"""
                    SELECT id, title, content, content_type, created_at, metadata
                    FROM user_library 
                    WHERE user_email = {placeholder} 
                    AND content_type = {placeholder}
                    AND (title LIKE {placeholder} OR content LIKE {placeholder})
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_email, content_type, search_pattern, search_pattern))
            else:
                cursor.execute(f"""
                    SELECT id, title, content, content_type, created_at, metadata
                    FROM user_library 
                    WHERE user_email = {placeholder}
                    AND (title LIKE {placeholder} OR content LIKE {placeholder})
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_email, search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            results = []
            for row in rows:
                try:
                    metadata = json.loads(row[5] or '{}')
                except:
                    metadata = {}
                
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'content_type': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'metadata': metadata
                })
            
            logger.info(f"🔍 Found {len(results)} search results for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search library: {e}")
            return []
    
    def get_content_by_type_with_limits(self, user_id: int, content_type: str, 
                                      user_plan: str) -> Dict[str, Any]:
        """Get content with plan-based limits applied"""
        try:
            # Import here to avoid circular imports
            from ..tiers.artistic_time import get_feature_limit
            
            # Get plan-based limits
            if content_type == 'chat':
                limit = get_feature_limit(user_plan, 'library_chats')
            else:
                limit = 100  # Default limit for other content types
            
            content_items = self.get_user_library(user_id, content_type, limit)
            
            return {
                'items': content_items,
                'limit': limit,
                'count': len(content_items),
                'has_more': len(content_items) == limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get content with limits: {e}")
            return {
                'items': [],
                'limit': 0,
                'count': 0,
                'has_more': False,
                'error': str(e)
            }
    
    def save_content(self, user_id: int, content_type: str, content_data: Dict[str, Any], 
                    metadata: Dict = None) -> Optional[int]:
        """Alias for add_content to maintain compatibility"""
        title = content_data.get('title', f"{content_type.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        content = json.dumps(content_data) if isinstance(content_data, dict) else str(content_data)
        
        return self.add_content(user_id, content_type, title, content, metadata)
    
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email from user ID"""
        try:
            if not self.database:
                return None
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"SELECT email FROM users WHERE id = {placeholder}", (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get user email: {e}")
            return None