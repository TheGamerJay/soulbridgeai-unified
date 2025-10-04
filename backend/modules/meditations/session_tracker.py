"""
SoulBridge AI - Session Tracker
Tracks meditation sessions, statistics, and user progress
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import json
from database_utils import format_query

logger = logging.getLogger(__name__)

class SessionTracker:
    """Tracks meditation sessions and user progress in database"""
    
    def __init__(self, database=None):
        self.database = database
        
    def save_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save completed meditation session to database"""
        try:
            if not self.database:
                # Fallback to session storage for demo
                logger.warning("Database unavailable - session not persistently saved")
                return {
                    'success': True,
                    'message': 'Session saved to temporary storage',
                    'session_id': session_data.get('id')
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Insert meditation session
            if self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO meditation_sessions 
                    (user_id, meditation_id, title, category, duration_seconds, 
                     duration_minutes, completed, started_at, completed_at, 
                     satisfaction_rating, notes, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    session_data['user_id'],
                    session_data['meditation_id'],
                    session_data['title'],
                    session_data['category'],
                    session_data['duration_seconds'],
                    session_data['duration_minutes'],
                    session_data['completed'],
                    session_data['started_at'],
                    session_data['completed_at'],
                    session_data.get('satisfaction_rating'),
                    session_data.get('notes', ''),
                    json.dumps(session_data.get('metadata', {}))
                ))
            else:
                cursor.execute(format_query("""
                    INSERT INTO meditation_sessions 
                    (user_id, meditation_id, title, category, duration_seconds, 
                     duration_minutes, completed, started_at, completed_at, 
                     satisfaction_rating, notes, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """), (
                    session_data['user_id'],
                    session_data['meditation_id'],
                    session_data['title'],
                    session_data['category'],
                    session_data['duration_seconds'],
                    session_data['duration_minutes'],
                    session_data['completed'],
                    session_data['started_at'],
                    session_data['completed_at'],
                    session_data.get('satisfaction_rating'),
                    session_data.get('notes', ''),
                    json.dumps(session_data.get('metadata', {}))
                ))
            
            if self.database.use_postgres:
                session_id = cursor.fetchone()[0]
            else:
                session_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Saved meditation session {session_id} for user {session_data['user_id']}")
            
            return {
                'success': True,
                'message': 'Session saved successfully',
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error saving meditation session: {e}")
            return {
                'success': False,
                'error': 'Failed to save session'
            }
    
    def get_user_sessions(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """Get user's recent meditation sessions"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'sessions': [],
                    'total_count': 0
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get user's meditation sessions
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT id, meditation_id, title, category, duration_minutes, 
                           completed, started_at, completed_at, satisfaction_rating, 
                           notes, metadata
                    FROM meditation_sessions 
                    WHERE user_id = %s 
                    ORDER BY completed_at DESC 
                    LIMIT %s
                """, (user_id, limit))
            else:
                cursor.execute(format_query("""
                    SELECT id, meditation_id, title, category, duration_minutes, 
                           completed, started_at, completed_at, satisfaction_rating, 
                           notes, metadata
                    FROM meditation_sessions 
                    WHERE user_id = ? 
                    ORDER BY completed_at DESC 
                    LIMIT ?
                """), (user_id, limit))
            
            sessions = []
            for row in cursor.fetchall():
                session_id, meditation_id, title, category, duration, completed, started, completed_at, rating, notes, metadata = row
                
                # Parse metadata
                try:
                    metadata_dict = json.loads(metadata) if metadata else {}
                except:
                    metadata_dict = {}
                
                sessions.append({
                    'id': session_id,
                    'meditation_id': meditation_id,
                    'title': title,
                    'category': category,
                    'duration_minutes': duration,
                    'completed': bool(completed),
                    'started_at': started,
                    'completed_at': completed_at,
                    'satisfaction_rating': rating,
                    'notes': notes,
                    'metadata': metadata_dict
                })
            
            # Get total count
            if self.database.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM meditation_sessions WHERE user_id = %s", (user_id,))
            else:
                cursor.execute(format_query(SELECT COUNT(*) FROM meditation_sessions WHERE user_id = ?"), (user_id,))
            
            total_count = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'success': True,
                'sessions': sessions,
                'total_count': total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return {
                'success': False,
                'error': 'Failed to load sessions'
            }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive meditation statistics for user"""
        try:
            if not self.database:
                # Return basic stats for demo
                return {
                    'success': True,
                    'stats': {
                        'total_sessions': 0,
                        'total_minutes': 0,
                        'streak_days': 0,
                        'favorite_type': 'Stress Relief',
                        'categories_tried': 0,
                        'longest_session_minutes': 0,
                        'average_session_minutes': 0,
                        'sessions_this_week': 0,
                        'sessions_this_month': 0
                    }
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Basic session statistics
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COALESCE(SUM(duration_minutes), 0) as total_minutes,
                        COALESCE(MAX(duration_minutes), 0) as longest_session,
                        COALESCE(AVG(duration_minutes), 0) as average_session,
                        COUNT(DISTINCT category) as categories_tried
                    FROM meditation_sessions 
                    WHERE user_id = %s AND completed = TRUE
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COALESCE(SUM(duration_minutes), 0) as total_minutes,
                        COALESCE(MAX(duration_minutes), 0) as longest_session,
                        COALESCE(AVG(duration_minutes), 0) as average_session,
                        COUNT(DISTINCT category) as categories_tried
                    FROM meditation_sessions 
                    WHERE user_id = ? AND completed = 1
                """), (user_id,))
            
            result = cursor.fetchone()
            if result:
                stats['total_sessions'] = result[0] or 0
                stats['total_minutes'] = int(result[1] or 0)
                stats['longest_session_minutes'] = int(result[2] or 0)
                stats['average_session_minutes'] = round(result[3] or 0, 1)
                stats['categories_tried'] = result[4] or 0
            
            # Find favorite meditation type
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT category, COUNT(*) as session_count
                    FROM meditation_sessions 
                    WHERE user_id = %s AND completed = TRUE
                    GROUP BY category 
                    ORDER BY session_count DESC 
                    LIMIT 1
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT category, COUNT(*) as session_count
                    FROM meditation_sessions 
                    WHERE user_id = ? AND completed = 1
                    GROUP BY category 
                    ORDER BY session_count DESC 
                    LIMIT 1
                """), (user_id,))
            
            favorite_result = cursor.fetchone()
            stats['favorite_type'] = favorite_result[0] if favorite_result else 'Stress Relief'
            
            # Calculate recent activity
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN completed_at >= NOW() - INTERVAL '7 days' THEN 1 END) as week_sessions,
                        COUNT(CASE WHEN completed_at >= NOW() - INTERVAL '30 days' THEN 1 END) as month_sessions
                    FROM meditation_sessions 
                    WHERE user_id = %s AND completed = TRUE
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        COUNT(CASE WHEN completed_at >= date('now', '-7 days') THEN 1 END) as week_sessions,
                        COUNT(CASE WHEN completed_at >= date('now', '-30 days') THEN 1 END) as month_sessions
                    FROM meditation_sessions 
                    WHERE user_id = ? AND completed = 1
                """), (user_id,))
            
            activity_result = cursor.fetchone()
            if activity_result:
                stats['sessions_this_week'] = activity_result[0] or 0
                stats['sessions_this_month'] = activity_result[1] or 0
            
            # Calculate streak
            stats['streak_days'] = self._calculate_meditation_streak(cursor, user_id)
            
            conn.close()
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user meditation stats: {e}")
            return {
                'success': False,
                'error': 'Failed to load statistics'
            }
    
    def get_category_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics broken down by meditation category"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'categories': {}
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get category breakdown
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        category,
                        COUNT(*) as session_count,
                        SUM(duration_minutes) as total_minutes,
                        AVG(duration_minutes) as avg_minutes,
                        AVG(satisfaction_rating) as avg_rating
                    FROM meditation_sessions 
                    WHERE user_id = %s AND completed = TRUE
                    GROUP BY category
                    ORDER BY session_count DESC
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        category,
                        COUNT(*) as session_count,
                        SUM(duration_minutes) as total_minutes,
                        AVG(duration_minutes) as avg_minutes,
                        AVG(satisfaction_rating) as avg_rating
                    FROM meditation_sessions 
                    WHERE user_id = ? AND completed = 1
                    GROUP BY category
                    ORDER BY session_count DESC
                """), (user_id,))
            
            categories = {}
            for row in cursor.fetchall():
                category, count, total_min, avg_min, avg_rating = row
                categories[category] = {
                    'session_count': count,
                    'total_minutes': int(total_min or 0),
                    'average_minutes': round(avg_min or 0, 1),
                    'average_rating': round(avg_rating or 0, 1) if avg_rating else None
                }
            
            conn.close()
            
            return {
                'success': True,
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return {
                'success': False,
                'error': 'Failed to load category statistics'
            }
    
    def get_meditation_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get meditation history over specified number of days"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'history': [],
                    'days_with_sessions': 0
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get daily meditation data
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        DATE(completed_at) as session_date,
                        COUNT(*) as session_count,
                        SUM(duration_minutes) as total_minutes
                    FROM meditation_sessions 
                    WHERE user_id = %s 
                        AND completed = TRUE 
                        AND completed_at >= NOW() - INTERVAL '%s days'
                    GROUP BY DATE(completed_at)
                    ORDER BY session_date DESC
                """, (user_id, days))
            else:
                cursor.execute(format_query("""
                    SELECT 
                        DATE(completed_at) as session_date,
                        COUNT(*) as session_count,
                        SUM(duration_minutes) as total_minutes
                    FROM meditation_sessions 
                    WHERE user_id = ? 
                        AND completed = 1 
                        AND completed_at >= date('now', '-%s days')
                    GROUP BY DATE(completed_at)
                    ORDER BY session_date DESC
                """), (user_id, days))
            
            history = []
            days_with_sessions = 0
            
            for row in cursor.fetchall():
                session_date, session_count, total_minutes = row
                history.append({
                    'date': str(session_date),
                    'session_count': session_count,
                    'total_minutes': int(total_minutes or 0)
                })
                days_with_sessions += 1
            
            conn.close()
            
            return {
                'success': True,
                'history': history,
                'days_with_sessions': days_with_sessions,
                'total_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting meditation history: {e}")
            return {
                'success': False,
                'error': 'Failed to load meditation history'
            }
    
    def _calculate_meditation_streak(self, cursor, user_id: int) -> int:
        """Calculate user's current meditation streak"""
        try:
            # Get distinct dates with completed sessions
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT DISTINCT DATE(completed_at) as session_date
                    FROM meditation_sessions 
                    WHERE user_id = %s AND completed = TRUE
                    ORDER BY session_date DESC
                    LIMIT 100
                """, (user_id,))
            else:
                cursor.execute(format_query("""
                    SELECT DISTINCT DATE(completed_at) as session_date
                    FROM meditation_sessions 
                    WHERE user_id = ? AND completed = 1
                    ORDER BY session_date DESC
                    LIMIT 100
                """), (user_id,))
            
            session_dates = [row[0] for row in cursor.fetchall()]
            
            if not session_dates:
                return 0
            
            # Convert to date objects for comparison
            if isinstance(session_dates[0], str):
                session_dates = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in session_dates]
            
            # Calculate streak
            today = datetime.now().date()
            streak_days = 0
            
            # Start with today or most recent session date
            current_date = session_dates[0] if session_dates[0] == today else today - timedelta(days=1)
            
            for session_date in session_dates:
                if session_date == current_date:
                    streak_days += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            return streak_days
            
        except Exception as e:
            logger.error(f"Error calculating meditation streak: {e}")
            return 0
    
    def update_session_rating(self, session_id: int, user_id: int, rating: int, 
                             notes: str = '') -> Dict[str, Any]:
        """Update session rating and notes"""
        try:
            if not self.database:
                return {
                    'success': True,
                    'message': 'Rating saved (demo mode)'
                }
            
            # Validate rating
            if not (1 <= rating <= 5):
                return {
                    'success': False,
                    'error': 'Rating must be between 1 and 5'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Update session rating
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE meditation_sessions 
                    SET satisfaction_rating = %s, notes = %s
                    WHERE id = %s AND user_id = %s
                """, (rating, notes, session_id, user_id))
            else:
                cursor.execute(format_query("""
                    UPDATE meditation_sessions 
                    SET satisfaction_rating = ?, notes = ?
                    WHERE id = ? AND user_id = ?
                """), (rating, notes, session_id, user_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return {
                    'success': False,
                    'error': 'Session not found or not owned by user'
                }
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Updated rating for meditation session {session_id}: {rating}/5")
            
            return {
                'success': True,
                'message': 'Rating updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating session rating: {e}")
            return {
                'success': False,
                'error': 'Failed to update rating'
            }
    
    def ensure_database_schema(self) -> Dict[str, Any]:
        """Ensure meditation-related database tables exist"""
        try:
            if not self.database:
                return {
                    'success': False,
                    'error': 'Database service unavailable'
                }
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Create meditation_sessions table
            if self.database.use_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meditation_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        meditation_id VARCHAR(100) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        duration_seconds INTEGER NOT NULL DEFAULT 0,
                        duration_minutes INTEGER NOT NULL DEFAULT 0,
                        completed BOOLEAN NOT NULL DEFAULT FALSE,
                        started_at TIMESTAMP WITH TIME ZONE,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
                        notes TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_user_id 
                    ON meditation_sessions(user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_completed_at 
                    ON meditation_sessions(completed_at)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_category 
                    ON meditation_sessions(category)
                """)
                
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meditation_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        meditation_id VARCHAR(100) NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        duration_seconds INTEGER NOT NULL DEFAULT 0,
                        duration_minutes INTEGER NOT NULL DEFAULT 0,
                        completed BOOLEAN NOT NULL DEFAULT 0,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
                        notes TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_user_id 
                    ON meditation_sessions(user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_completed_at 
                    ON meditation_sessions(completed_at)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_meditation_sessions_category 
                    ON meditation_sessions(category)
                """)
            
            conn.commit()
            conn.close()
            
            logger.info("🛠️ Meditation database schema updated successfully")
            
            return {
                'success': True,
                'message': 'Database schema updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error ensuring meditation database schema: {e}")
            return {
                'success': False,
                'error': str(e)
            }