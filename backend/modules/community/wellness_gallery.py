"""
SoulBridge AI - Wellness Gallery
Manages anonymous community content sharing and wellness gallery
Extracted from backend/app.py with improvements
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from database_utils import format_query

logger = logging.getLogger(__name__)

class WellnessGallery:
    """Service for managing the wellness gallery and anonymous content sharing"""
    
    def __init__(self, database=None, content_moderator=None):
        self.database = database
        self.content_moderator = content_moderator
        self.max_content_length = 2000
        self.max_items_per_query = 50
        self.supported_themes = [
            'wellness', 'gratitude', 'growth', 'creativity', 'support',
            'inspiration', 'meditation', 'healing', 'relationships', 'mindfulness',
            'stress', 'peace', 'dreams', 'freeform'
        ]
        self.supported_content_types = [
            'creative_writing', 'poetry', 'artwork', 'reflection',
            'affirmation', 'story', 'journal_entry', 'meditation'
        ]
    
    def share_content(self, user_id: int, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Share content to the wellness gallery (anonymous)"""
        try:
            # Validate content data
            validation_result = self._validate_content(content_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            content = content_data['content']
            content_type = content_data.get('content_type', 'creative_writing')
            theme = content_data.get('theme', 'wellness')
            mood = content_data.get('mood', '')
            
            # Content moderation - CRITICAL SAFETY CHECK
            if self.content_moderator:
                moderation_result = self.content_moderator.moderate_content(content, content_type)
                
                if not moderation_result['is_safe']:
                    logger.warning(f"Content rejected in moderation: {moderation_result['reason']}")
                    return {
                        'success': False,
                        'error': "Content doesn't meet our wellness community guidelines. Please ensure your content is positive, supportive, and appropriate for a wellness-focused community."
                    }
                
                # Auto-approve if high confidence, otherwise mark for review
                is_approved = moderation_result['confidence'] >= 0.8
                moderation_status = "approved" if is_approved else "pending"
                moderation_confidence = moderation_result['confidence']
                moderation_reason = moderation_result['reason']
            else:
                # Basic fallback if no moderator available
                is_approved = True
                moderation_status = "approved"
                moderation_confidence = 0.6
                moderation_reason = "Basic validation passed"
            
            # Prepare content for storage
            gallery_item = {
                'content_type': content_type,
                'content': content,
                'theme': theme,
                'mood': mood,
                'is_approved': is_approved,
                'moderation_status': moderation_status,
                'hearts_count': 0,
                'created_at': datetime.now(),
                'metadata': {
                    'moderation_confidence': moderation_confidence,
                    'moderation_reason': moderation_reason,
                    'original_content_type': content_type,
                    'sharing_timestamp': datetime.now().isoformat(),
                    'word_count': len(content.split()) if content_type in ['creative_writing', 'poetry', 'story'] else None
                }
            }
            
            # Save to database
            if self.database:
                content_id = self._save_to_database(gallery_item)
                if content_id:
                    logger.info(f"📝 Content shared to wellness gallery: {theme} - {content_type}")
                    
                    response_message = (
                        "Shared to Wellness Gallery!" if is_approved 
                        else "Shared to Wellness Gallery! Your content is being reviewed and will appear soon."
                    )
                    
                    return {
                        'success': True,
                        'message': response_message,
                        'approved': is_approved,
                        'content_id': content_id
                    }
                else:
                    return {'success': False, 'error': 'Failed to save content'}
            else:
                return {'success': False, 'error': 'Database not available'}
            
        except Exception as e:
            logger.error(f"Failed to share content to wellness gallery: {e}")
            return {'success': False, 'error': f'Failed to share content: {str(e)}'}
    
    def get_gallery_content(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get approved content from wellness gallery"""
        try:
            filters = filters or {}
            
            if not self.database:
                return {
                    'success': True,
                    'items': [],
                    'total': 0,
                    'filters_applied': filters
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Extract filters
            theme_filter = filters.get('theme', 'all')
            content_type_filter = filters.get('type', 'all')
            limit = min(int(filters.get('limit', 20)), self.max_items_per_query)
            offset = max(0, int(filters.get('offset', 0)))
            
            # Build query with filters
            base_query = """
                SELECT id, content_type, content, theme, mood, hearts_count, created_at, metadata
                FROM wellness_gallery 
                WHERE is_approved = {} AND moderation_status = 'approved'
            """.format('TRUE' if hasattr(self.database, 'use_postgres') and self.database.use_postgres else '1')
            
            params = []
            
            # Add theme filter
            if theme_filter != 'all' and theme_filter in self.supported_themes:
                placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
                base_query += f" AND theme = {placeholder}"
                params.append(theme_filter)
            
            # Add content type filter
            if content_type_filter != 'all' and content_type_filter in self.supported_content_types:
                placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
                base_query += f" AND content_type = {placeholder}"
                params.append(content_type_filter)
            
            # Add ordering and pagination
            base_query += " ORDER BY created_at DESC"
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            base_query += f" LIMIT {placeholder}"
            params.append(limit)
            
            if offset > 0:
                base_query += f" OFFSET {placeholder}"
                params.append(offset)
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            # Format results
            gallery_items = []
            for row in rows:
                try:
                    metadata = json.loads(row[7]) if row[7] else {}
                except:
                    metadata = {}
                
                item = {
                    'id': row[0],
                    'content_type': row[1],
                    'content': row[2],
                    'theme': row[3],
                    'mood': row[4],
                    'hearts_count': row[5] or 0,
                    'created_at': row[6].isoformat() if row[6] else None,
                    'metadata': metadata,
                    'display': self._format_display_data(row[1], row[3], row[5] or 0, row[6])
                }
                gallery_items.append(item)
            
            conn.close()
            
            logger.info(f"📖 Retrieved {len(gallery_items)} items from wellness gallery")
            
            return {
                'success': True,
                'items': gallery_items,
                'total': len(gallery_items),
                'filters_applied': {
                    'theme': theme_filter,
                    'content_type': content_type_filter,
                    'limit': limit,
                    'offset': offset
                },
                'has_more': len(gallery_items) == limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get wellness gallery content: {e}")
            return {
                'success': False,
                'error': str(e),
                'items': [],
                'total': 0
            }
    
    def add_heart(self, user_id: int, content_id: int) -> Dict[str, Any]:
        """Add a heart to wellness gallery content"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Increment heart count
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    UPDATE wellness_gallery 
                    SET hearts_count = COALESCE(hearts_count, 0) + 1 
                    WHERE id = %s AND is_approved = TRUE
                    RETURNING hearts_count
                """, (content_id,))
                result = cursor.fetchone()
            else:
                cursor.execute(format_query("""
                    UPDATE wellness_gallery 
                    SET hearts_count = COALESCE(hearts_count, 0) + 1 
                    WHERE id = ? AND is_approved = 1
                """), (content_id,))
                
                # Get updated count for SQLite
                cursor.execute(format_query(SELECT hearts_count FROM wellness_gallery WHERE id = ?"), (content_id,))
                result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {'success': False, 'error': 'Content not found or not approved'}
            
            new_count = result[0]
            conn.commit()
            conn.close()
            
            logger.info(f"❤️ Added heart to wellness content {content_id} (new count: {new_count})")
            
            return {
                'success': True,
                'hearts_count': new_count,
                'message': 'Heart added successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to add heart to content: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_gallery_stats(self) -> Dict[str, Any]:
        """Get wellness gallery statistics"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'stats': {
                        'total_content': 0,
                        'approved_content': 0,
                        'pending_content': 0,
                        'total_hearts': 0,
                        'content_by_theme': {},
                        'content_by_type': {},
                        'recent_activity': 0
                    }
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get total counts
            cursor.execute("SELECT COUNT(*) FROM wellness_gallery")
            total_content = cursor.fetchone()[0] or 0
            
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = TRUE")
                approved_content = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = FALSE")
                pending_content = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(hearts_count) FROM wellness_gallery WHERE is_approved = TRUE")
            else:
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = 1")
                approved_content = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM wellness_gallery WHERE is_approved = 0")
                pending_content = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(hearts_count) FROM wellness_gallery WHERE is_approved = 1")
            
            total_hearts = cursor.fetchone()[0] or 0
            
            # Get content by theme
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT theme, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    GROUP BY theme
                """)
            else:
                cursor.execute("""
                    SELECT theme, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    GROUP BY theme
                """)
            
            content_by_theme = dict(cursor.fetchall())
            
            # Get content by type
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT content_type, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    GROUP BY content_type
                """)
            else:
                cursor.execute("""
                    SELECT content_type, COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    GROUP BY content_type
                """)
            
            content_by_type = dict(cursor.fetchall())
            
            # Get recent activity (last 7 days)
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = TRUE 
                    AND created_at >= NOW() - INTERVAL '7 days'
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM wellness_gallery 
                    WHERE is_approved = 1 
                    AND created_at >= date('now', '-7 days')
                """)
            
            recent_activity = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats = {
                'total_content': total_content,
                'approved_content': approved_content,
                'pending_content': pending_content,
                'total_hearts': total_hearts,
                'content_by_theme': content_by_theme,
                'content_by_type': content_by_type,
                'recent_activity': recent_activity,
                'engagement_rate': (total_hearts / approved_content * 100) if approved_content > 0 else 0
            }
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get gallery stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_content(self, content_data: Dict[str, Any]) -> Dict[str, bool]:
        """Validate content before sharing"""
        try:
            # Check required fields
            if 'content' not in content_data:
                return {'valid': False, 'error': 'Content is required'}
            
            content = content_data['content'].strip()
            if not content:
                return {'valid': False, 'error': 'Content cannot be empty'}
            
            # Check content length
            if len(content) > self.max_content_length:
                return {
                    'valid': False,
                    'error': f'Content too long. Maximum {self.max_content_length} characters allowed.'
                }
            
            if len(content) < 10:
                return {'valid': False, 'error': 'Content too short. Minimum 10 characters required.'}
            
            # Validate content type
            content_type = content_data.get('content_type', 'creative_writing')
            if content_type not in self.supported_content_types:
                return {
                    'valid': False,
                    'error': f'Invalid content type. Supported types: {", ".join(self.supported_content_types)}'
                }
            
            # Validate theme
            theme = content_data.get('theme', 'wellness')
            if theme not in self.supported_themes:
                return {
                    'valid': False,
                    'error': f'Invalid theme. Supported themes: {", ".join(self.supported_themes)}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return {'valid': False, 'error': 'Failed to validate content'}
    
    def _save_to_database(self, gallery_item: Dict[str, Any]) -> Optional[int]:
        """Save gallery item to database"""
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            metadata_json = json.dumps(gallery_item['metadata'])
            
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO wellness_gallery 
                    (content_type, content, theme, mood, is_approved, moderation_status, 
                     hearts_count, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    gallery_item['content_type'],
                    gallery_item['content'],
                    gallery_item['theme'],
                    gallery_item['mood'],
                    gallery_item['is_approved'],
                    gallery_item['moderation_status'],
                    gallery_item['hearts_count'],
                    gallery_item['created_at'],
                    metadata_json
                ))
                content_id = cursor.fetchone()[0]
            else:
                cursor.execute(format_query("""
                    INSERT INTO wellness_gallery 
                    (content_type, content, theme, mood, is_approved, moderation_status, 
                     hearts_count, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """), (
                    gallery_item['content_type'],
                    gallery_item['content'],
                    gallery_item['theme'],
                    gallery_item['mood'],
                    1 if gallery_item['is_approved'] else 0,
                    gallery_item['moderation_status'],
                    gallery_item['hearts_count'],
                    gallery_item['created_at'],
                    metadata_json
                ))
                content_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return None
    
    def _format_display_data(self, content_type: str, theme: str, hearts_count: int, created_at) -> Dict[str, str]:
        """Format display data for content items"""
        return {
            'content_type_label': content_type.replace('_', ' ').title(),
            'theme_label': theme.replace('_', ' ').title(),
            'hearts_display': f"{hearts_count} ❤️" if hearts_count > 0 else "0 ❤️",
            'time_ago': self._format_time_ago(created_at)
        }
    
    def _format_time_ago(self, timestamp) -> str:
        """Format timestamp as time ago"""
        try:
            if not timestamp:
                return "Recently"
            
            if isinstance(timestamp, str):
                created_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                created_time = timestamp
            
            now = datetime.now()
            if created_time.tzinfo:
                created_time = created_time.replace(tzinfo=None)
            
            diff = now - created_time
            
            if diff.days > 30:
                return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
            elif diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
                
        except Exception:
            return "Recently"
    
    def get_supported_themes(self) -> List[str]:
        """Get list of supported themes"""
        return self.supported_themes
    
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types"""
        return self.supported_content_types