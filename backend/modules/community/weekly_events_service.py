"""
SoulBridge AI - Weekly Events Service
Manages "This Week's Most Liked Post" and other community events
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WeeklyEventsService:
    """Service for managing weekly community events"""
    
    def __init__(self, database=None):
        self.database = database
        
    def get_current_weekly_event(self) -> Optional[Dict[str, Any]]:
        """Get the current active weekly event"""
        try:
            if not self.database:
                return None
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now()
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT id, event_type, title, description, start_date, end_date, 
                           status, total_participants, total_reactions, winner_post_id
                    FROM weekly_events 
                    WHERE status = 'active' AND start_date <= %s AND end_date >= %s
                    ORDER BY start_date DESC LIMIT 1
                """, (now, now))
            else:
                cursor.execute("""
                    SELECT id, event_type, title, description, start_date, end_date, 
                           status, total_participants, total_reactions, winner_post_id
                    FROM weekly_events 
                    WHERE status = 'active' AND start_date <= ? AND end_date >= ?
                    ORDER BY start_date DESC LIMIT 1
                """, (now, now))
                
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'event_type': result[1],
                    'title': result[2],
                    'description': result[3],
                    'start_date': result[4],
                    'end_date': result[5],
                    'status': result[6],
                    'total_participants': result[7],
                    'total_reactions': result[8],
                    'winner_post_id': result[9],
                    'time_remaining': self._calculate_time_remaining(result[5])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current weekly event: {e}")
            return None
    
    def get_weekly_leaderboard(self, event_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the current leaderboard for a weekly event"""
        try:
            if not self.database:
                return []
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT wpm.post_id, wpm.user_id, wpm.total_reactions, wpm.unique_reactors,
                           wpm.final_score, wpm.ranking_position, wpm.reaction_breakdown,
                           cp.text, cp.category, cp.created_at, cp.companion_id
                    FROM weekly_post_metrics wpm
                    JOIN community_posts cp ON wpm.post_id = cp.id
                    WHERE wpm.event_id = %s
                    ORDER BY wpm.final_score DESC, wpm.total_reactions DESC, wpm.unique_reactors DESC
                    LIMIT %s
                """, (event_id, limit))
            else:
                cursor.execute("""
                    SELECT wpm.post_id, wpm.user_id, wpm.total_reactions, wpm.unique_reactors,
                           wpm.final_score, wpm.ranking_position, wpm.reaction_breakdown,
                           cp.text, cp.category, cp.created_at, cp.companion_id
                    FROM weekly_post_metrics wpm
                    JOIN community_posts cp ON wpm.post_id = cp.id
                    WHERE wpm.event_id = ?
                    ORDER BY wpm.final_score DESC, wpm.total_reactions DESC, wpm.unique_reactors DESC
                    LIMIT ?
                """, (event_id, limit))
                
            results = cursor.fetchall()
            conn.close()
            
            leaderboard = []
            for i, result in enumerate(results, 1):
                try:
                    reaction_breakdown = json.loads(result[6]) if result[6] else {}
                except:
                    reaction_breakdown = {}
                    
                leaderboard.append({
                    'position': i,
                    'post_id': result[0],
                    'user_id': result[1],
                    'total_reactions': result[2],
                    'unique_reactors': result[3],
                    'final_score': float(result[4]),
                    'reaction_breakdown': reaction_breakdown,
                    'post_preview': result[7][:100] + "..." if len(result[7]) > 100 else result[7],
                    'category': result[8],
                    'created_at': result[9],
                    'companion_id': result[10]
                })
                
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting weekly leaderboard: {e}")
            return []
    
    def update_post_metrics(self, post_id: int, event_id: int) -> bool:
        """Update metrics for a post in the current event"""
        try:
            if not self.database:
                return False
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get current reaction stats for this post
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_reactions,
                        COUNT(DISTINCT viewer_uid) as unique_reactors,
                        JSON_OBJECT_AGG(emoji, reaction_count) as reaction_breakdown
                    FROM (
                        SELECT emoji, COUNT(*) as reaction_count
                        FROM community_reactions 
                        WHERE post_id = %s 
                        GROUP BY emoji
                    ) emoji_counts
                """, (post_id,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_reactions,
                        COUNT(DISTINCT viewer_uid) as unique_reactors
                    FROM community_reactions 
                    WHERE post_id = ?
                """, (post_id,))
            
            result = cursor.fetchone()
            total_reactions = result[0] if result else 0
            unique_reactors = result[1] if result else 0
            
            # Get reaction breakdown
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT emoji, COUNT(*) as count
                    FROM community_reactions 
                    WHERE post_id = %s 
                    GROUP BY emoji
                """, (post_id,))
            else:
                cursor.execute("""
                    SELECT emoji, COUNT(*) as count
                    FROM community_reactions 
                    WHERE post_id = ? 
                    GROUP BY emoji
                """, (post_id,))
                
            reactions = cursor.fetchall()
            reaction_breakdown = {emoji: count for emoji, count in reactions}
            
            # Calculate final score (weighted by unique reactors and diversity)
            diversity_bonus = len(reaction_breakdown) * 0.1  # Bonus for emoji diversity
            final_score = (unique_reactors * 2.0) + (total_reactions * 1.0) + diversity_bonus
            
            # Update or insert post metrics
            if self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO weekly_post_metrics 
                    (event_id, post_id, user_id, post_created_at, total_reactions, unique_reactors,
                     reaction_breakdown, final_score, last_updated)
                    SELECT %s, %s, author_uid, created_at, %s, %s, %s, %s, %s
                    FROM community_posts WHERE id = %s
                    ON CONFLICT (event_id, post_id) 
                    DO UPDATE SET 
                        total_reactions = %s, 
                        unique_reactors = %s,
                        reaction_breakdown = %s,
                        final_score = %s,
                        last_updated = %s
                """, (event_id, post_id, total_reactions, unique_reactors, 
                      json.dumps(reaction_breakdown), final_score, datetime.now(),
                      post_id, total_reactions, unique_reactors, 
                      json.dumps(reaction_breakdown), final_score, datetime.now()))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO weekly_post_metrics 
                    (event_id, post_id, user_id, post_created_at, total_reactions, unique_reactors,
                     reaction_breakdown, final_score, last_updated)
                    SELECT ?, ?, author_uid, created_at, ?, ?, ?, ?, ?
                    FROM community_posts WHERE id = ?
                """, (event_id, post_id, total_reactions, unique_reactors,
                      json.dumps(reaction_breakdown), final_score, datetime.now(), post_id))
            
            # Update the community_posts table as well
            if self.database.use_postgres:
                cursor.execute("""
                    UPDATE community_posts 
                    SET total_reactions = %s, unique_reactors = %s, reaction_score = %s
                    WHERE id = %s
                """, (total_reactions, unique_reactors, final_score, post_id))
            else:
                cursor.execute("""
                    UPDATE community_posts 
                    SET total_reactions = ?, unique_reactors = ?, reaction_score = ?
                    WHERE id = ?
                """, (total_reactions, unique_reactors, final_score, post_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Updated metrics for post {post_id}: {total_reactions} reactions, {unique_reactors} unique reactors, score: {final_score:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating post metrics: {e}")
            return False
    
    def register_participant(self, event_id: int, user_id: int, companion_id: str = None) -> bool:
        """Register a user as a participant in the weekly event"""
        try:
            if not self.database:
                return False
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO event_participants (event_id, user_id, companion_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_id, user_id) DO NOTHING
                """, (event_id, user_id, companion_id))
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO event_participants (event_id, user_id, companion_id)
                    VALUES (?, ?, ?)
                """, (event_id, user_id, companion_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error registering participant: {e}")
            return False
    
    def get_user_event_stats(self, user_id: int, event_id: int) -> Dict[str, Any]:
        """Get a user's statistics for a specific event"""
        try:
            if not self.database:
                return {}
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT 
                        posts_submitted, total_reactions_received, best_post_score,
                        (SELECT COUNT(*) FROM event_participants WHERE event_id = %s AND best_post_score > ep.best_post_score) + 1 as current_rank
                    FROM event_participants ep
                    WHERE event_id = %s AND user_id = %s
                """, (event_id, event_id, user_id))
            else:
                cursor.execute("""
                    SELECT 
                        posts_submitted, total_reactions_received, best_post_score,
                        (SELECT COUNT(*) FROM event_participants WHERE event_id = ? AND best_post_score > ep.best_post_score) + 1 as current_rank
                    FROM event_participants ep
                    WHERE event_id = ? AND user_id = ?
                """, (event_id, event_id, user_id))
                
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'posts_submitted': result[0],
                    'total_reactions_received': result[1],
                    'best_post_score': float(result[2]),
                    'current_rank': result[3],
                    'is_participating': True
                }
            else:
                return {'is_participating': False}
                
        except Exception as e:
            logger.error(f"Error getting user event stats: {e}")
            return {}
    
    def _calculate_time_remaining(self, end_date: datetime) -> Dict[str, int]:
        """Calculate time remaining until event ends"""
        try:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            now = datetime.now()
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=now.tzinfo)
            
            delta = end_date - now
            
            if delta.total_seconds() <= 0:
                return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0}
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                'days': days,
                'hours': hours, 
                'minutes': minutes,
                'seconds': seconds
            }
            
        except Exception as e:
            logger.error(f"Error calculating time remaining: {e}")
            return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0}
    
    def create_next_weekly_event(self) -> bool:
        """Create the next week's event when current one ends"""
        try:
            if not self.database:
                return False
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Calculate next week's dates
            now = datetime.now()
            next_week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_week_start += timedelta(days=7 - now.weekday())  # Start next Monday
            next_week_end = next_week_start + timedelta(days=7) - timedelta(microseconds=1)
            
            if self.database.use_postgres:
                cursor.execute("""
                    INSERT INTO weekly_events (event_type, title, description, start_date, end_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    'most_appreciated_post',
                    'Most Appreciated Post This Week 🏆',
                    'Share your most meaningful content with the community! The post that receives the most genuine appreciation wins special recognition and rewards.',
                    next_week_start,
                    next_week_end,
                    'upcoming'
                ))
            else:
                cursor.execute("""
                    INSERT INTO weekly_events (event_type, title, description, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    'most_appreciated_post',
                    'Most Appreciated Post This Week 🏆',
                    'Share your most meaningful content with the community! The post that receives the most genuine appreciation wins special recognition and rewards.',
                    next_week_start,
                    next_week_end,
                    'upcoming'
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🏆 Created next weekly event: {next_week_start} to {next_week_end}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating next weekly event: {e}")
            return False
    
    def end_current_week_and_crown_winner(self) -> Dict[str, Any]:
        """End the current week's event and crown the winner automatically"""
        try:
            if not self.database:
                return {"success": False, "error": "Database not available"}
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Get current active event
            current_event = self.get_current_weekly_event()
            if not current_event:
                return {"success": False, "error": "No active event to end"}
            
            # Get the winner (highest scoring post)
            leaderboard = self.get_weekly_leaderboard(current_event['id'], limit=1)
            
            if leaderboard:
                winner = leaderboard[0]
                
                # Update the event with winner information
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE weekly_events 
                        SET status = 'ended', 
                            winner_post_id = %s, 
                            winner_user_id = %s,
                            winner_prize_type = %s,
                            winner_prize_value = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        winner['post_id'], 
                        winner['user_id'],
                        'recognition_badge',
                        'Most Appreciated Post Winner 🏆',
                        current_event['id']
                    ))
                else:
                    cursor.execute("""
                        UPDATE weekly_events 
                        SET status = 'ended', 
                            winner_post_id = ?, 
                            winner_user_id = ?,
                            winner_prize_type = ?,
                            winner_prize_value = ?,
                            updated_at = datetime('now')
                        WHERE id = ?
                    """, (
                        winner['post_id'], 
                        winner['user_id'],
                        'recognition_badge',
                        'Most Appreciated Post Winner 🏆',
                        current_event['id']
                    ))
                
                # Mark the winning post in weekly_post_metrics
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE weekly_post_metrics 
                        SET is_winner = TRUE, ranking_position = 1
                        WHERE event_id = %s AND post_id = %s
                    """, (current_event['id'], winner['post_id']))
                else:
                    cursor.execute("""
                        UPDATE weekly_post_metrics 
                        SET is_winner = 1, ranking_position = 1
                        WHERE event_id = ? AND post_id = ?
                    """, (current_event['id'], winner['post_id']))
                
                # Update participant stats
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE event_participants 
                        SET best_post_id = %s, best_post_score = %s
                        WHERE event_id = %s AND user_id = %s
                    """, (winner['post_id'], winner['final_score'], current_event['id'], winner['user_id']))
                else:
                    cursor.execute("""
                        UPDATE event_participants 
                        SET best_post_id = ?, best_post_score = ?
                        WHERE event_id = ? AND user_id = ?
                    """, (winner['post_id'], winner['final_score'], current_event['id'], winner['user_id']))
                
                conn.commit()
                
                # Create next week's event
                self.create_next_weekly_event()
                
                result = {
                    "success": True,
                    "message": "Weekly event ended successfully",
                    "winner": {
                        "post_id": winner['post_id'],
                        "user_id": winner['user_id'],
                        "final_score": winner['final_score'],
                        "total_reactions": winner['total_reactions'],
                        "unique_reactors": winner['unique_reactors'],
                        "post_preview": winner['post_preview']
                    },
                    "event_ended": current_event,
                    "next_event_created": True
                }
                
                logger.info(f"🏆 Week {current_event['id']} ended! Winner: Post {winner['post_id']} by User {winner['user_id']} with score {winner['final_score']}")
                return result
                
            else:
                # No participants, just end the event
                if self.database.use_postgres:
                    cursor.execute("""
                        UPDATE weekly_events 
                        SET status = 'ended', updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (current_event['id'],))
                else:
                    cursor.execute("""
                        UPDATE weekly_events 
                        SET status = 'ended', updated_at = datetime('now')
                        WHERE id = ?
                    """, (current_event['id'],))
                
                conn.commit()
                self.create_next_weekly_event()
                
                logger.info(f"📝 Week {current_event['id']} ended with no participants")
                return {
                    "success": True,
                    "message": "Weekly event ended (no participants)",
                    "winner": None,
                    "event_ended": current_event,
                    "next_event_created": True
                }
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Error ending weekly event: {e}")
            return {"success": False, "error": str(e)}
    
    def check_and_transition_weekly_events(self) -> Dict[str, Any]:
        """Check if current event should end and automatically transition to next week"""
        try:
            current_event = self.get_current_weekly_event()
            if not current_event:
                # No active event, create one if needed
                self.create_next_weekly_event()
                return {"action": "created_new_event"}
            
            # Check if current event should end
            now = datetime.now()
            end_date = current_event['end_date']
            
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if now >= end_date:
                # Event should end, crown winner and create next event
                result = self.end_current_week_and_crown_winner()
                return {
                    "action": "transitioned_week",
                    "transition_result": result
                }
            else:
                # Event still active
                time_remaining = self._calculate_time_remaining(end_date)
                return {
                    "action": "event_still_active",
                    "time_remaining": time_remaining
                }
                
        except Exception as e:
            logger.error(f"Error checking weekly event transition: {e}")
            return {"action": "error", "error": str(e)}
    
    def get_event_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get history of past weekly events with their winners"""
        try:
            if not self.database:
                return []
                
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            if self.database.use_postgres:
                cursor.execute("""
                    SELECT we.id, we.title, we.start_date, we.end_date, we.status,
                           we.winner_post_id, we.winner_user_id, we.total_participants,
                           we.total_reactions, cp.text as winner_post_text
                    FROM weekly_events we
                    LEFT JOIN community_posts cp ON we.winner_post_id = cp.id
                    WHERE we.status = 'ended'
                    ORDER BY we.end_date DESC
                    LIMIT %s
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT we.id, we.title, we.start_date, we.end_date, we.status,
                           we.winner_post_id, we.winner_user_id, we.total_participants,
                           we.total_reactions, cp.text as winner_post_text
                    FROM weekly_events we
                    LEFT JOIN community_posts cp ON we.winner_post_id = cp.id
                    WHERE we.status = 'ended'
                    ORDER BY we.end_date DESC
                    LIMIT ?
                """, (limit,))
                
            results = cursor.fetchall()
            conn.close()
            
            history = []
            for result in results:
                history.append({
                    'event_id': result[0],
                    'title': result[1],
                    'start_date': result[2],
                    'end_date': result[3],
                    'status': result[4],
                    'winner_post_id': result[5],
                    'winner_user_id': result[6],
                    'total_participants': result[7],
                    'total_reactions': result[8],
                    'winner_post_preview': result[9][:100] + "..." if result[9] and len(result[9]) > 100 else result[9]
                })
                
            return history
            
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return []