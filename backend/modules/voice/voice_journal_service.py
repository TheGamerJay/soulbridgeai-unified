"""
SoulBridge AI - Voice Journal Service
Voice journaling with AI analysis and emotion detection
Extracted from monolith app.py with improvements
"""
import os
import json
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import session

logger = logging.getLogger(__name__)

class VoiceJournalService:
    """Complete voice journaling service with AI analysis"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI client if available"""
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for voice journaling")
            else:
                logger.warning("OpenAI API key not set - voice journaling will use mock data")
        except ImportError:
            logger.warning("OpenAI package not installed - voice journaling will use mock data")
    
    def validate_access(self, user_plan: str, user_addons: List[str], trial_active: bool) -> bool:
        """Validate if user can access voice journaling"""
        return (
            user_plan in ['silver', 'gold'] or 
            trial_active or 
            'voice-journaling' in user_addons
        )
    
    def validate_audio_file(self, audio_file) -> Dict[str, Any]:
        """Validate uploaded audio file"""
        if not audio_file or not audio_file.filename:
            return {"valid": False, "error": "No audio file provided"}
        
        # Check file extension
        allowed_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm'}
        file_ext = os.path.splitext(audio_file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return {
                "valid": False, 
                "error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            }
        
        # Check file size (max 25MB for voice journaling)
        audio_file.seek(0, 2)  # Seek to end
        size = audio_file.tell()
        audio_file.seek(0)  # Seek back to beginning
        
        max_size = 25 * 1024 * 1024  # 25MB
        if size > max_size:
            return {
                "valid": False,
                "error": f"Audio file too large (max {max_size // (1024*1024)}MB)"
            }
        
        return {"valid": True}
    
    def transcribe_audio(self, audio_file) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            if not self.openai_client:
                # Return mock transcription for development
                return {
                    "success": True,
                    "transcription": "This is a mock transcription for development. The actual Whisper API would process the audio file and return the spoken text here.",
                    "provider": "mock"
                }
            
            logger.info(f"🎙️ Transcribing audio file: {audio_file.filename}")
            
            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                audio_file.save(tmp_file.name)
                
                # Transcribe using Whisper
                with open(tmp_file.name, 'rb') as audio_data:
                    transcription_response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data
                    )
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                transcription_text = transcription_response.text.strip()
                
                if not transcription_text:
                    return {
                        "success": False,
                        "error": "No speech detected in audio"
                    }
                
                logger.info(f"✅ Transcription successful: {len(transcription_text)} characters")
                
                return {
                    "success": True,
                    "transcription": transcription_text,
                    "provider": "whisper"
                }
                
        except Exception as e:
            logger.error(f"❌ Voice transcription failed: {e}")
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
            }
    
    def analyze_emotions(self, transcription_text: str) -> Dict[str, Any]:
        """Analyze emotions and provide insights"""
        try:
            if not self.openai_client:
                # Return mock analysis for development
                return {
                    "success": True,
                    "analysis": {
                        "summary": "Your voice journal entry shows thoughtful reflection and self-awareness.",
                        "emotions": ["Reflection", "Self-awareness", "Contemplation"],
                        "mood_score": 7.0,
                        "recommendations": [
                            "Continue journaling regularly to track emotional patterns",
                            "Practice self-compassion during difficult moments", 
                            "Reflect on positive moments throughout your day"
                        ]
                    },
                    "provider": "mock"
                }
            
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze this voice journal entry for emotional insights:
            
            "{transcription_text}"
            
            Provide a JSON response with:
            1. summary: Brief emotional summary of the entry (1-2 sentences)
            2. emotions: Array of 3-5 main emotions detected
            3. mood_score: Rating from 1-10 (1=very negative, 10=very positive)
            4. recommendations: Array of 3 helpful suggestions for emotional wellness
            
            Be empathetic and supportive in your analysis. Focus on growth and self-compassion.
            """
            
            # Get AI analysis
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an empathetic emotional wellness coach analyzing voice journal entries. Always respond with valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse JSON response
            try:
                analysis_data = json.loads(response.choices[0].message.content)
                
                # Validate required fields
                required_fields = ['summary', 'emotions', 'mood_score', 'recommendations']
                for field in required_fields:
                    if field not in analysis_data:
                        raise ValueError(f"Missing required field: {field}")
                
                logger.info("✅ Emotional analysis completed")
                
                return {
                    "success": True,
                    "analysis": analysis_data,
                    "provider": "gpt-4"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI analysis JSON: {e}")
                # Fallback to mock analysis
                return {
                    "success": True,
                    "analysis": {
                        "summary": "Your voice journal entry has been analyzed for emotional patterns.",
                        "emotions": ["Reflection", "Self-awareness"],
                        "mood_score": 7.0,
                        "recommendations": [
                            "Continue journaling regularly",
                            "Practice self-compassion", 
                            "Reflect on positive moments"
                        ]
                    },
                    "provider": "fallback"
                }
                
        except Exception as e:
            logger.error(f"❌ Emotional analysis failed: {e}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
    
    def save_entry(self, user_id: int, transcription: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Save voice journal entry to database/session"""
        try:
            # Create entry data
            entry = {
                "id": self._generate_entry_id(),
                "user_id": user_id,
                "transcription": transcription,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Save to session (in production, save to database)
            if 'voice_journal_entries' not in session:
                session['voice_journal_entries'] = []
            
            session['voice_journal_entries'].append(entry)
            
            # Keep only last 50 entries in session
            if len(session['voice_journal_entries']) > 50:
                session['voice_journal_entries'] = session['voice_journal_entries'][-50:]
            
            logger.info(f"📝 Voice journal entry saved for user {user_id}")
            
            return {
                "success": True,
                "entry_id": entry["id"],
                "message": "Journal entry saved successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to save voice journal entry: {e}")
            return {
                "success": False,
                "error": f"Failed to save entry: {str(e)}"
            }
    
    def get_entries(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """Get user's voice journal entries"""
        try:
            # Get entries from session (in production, get from database)
            entries = session.get('voice_journal_entries', [])
            
            # Filter by user ID and sort by timestamp
            user_entries = [
                entry for entry in entries 
                if entry.get('user_id') == user_id
            ]
            
            # Sort by timestamp, most recent first
            user_entries.sort(
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            
            # Limit results
            limited_entries = user_entries[:limit]
            
            logger.info(f"📚 Retrieved {len(limited_entries)} journal entries for user {user_id}")
            
            return {
                "success": True,
                "entries": limited_entries,
                "total": len(user_entries)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get voice journal entries: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve entries: {str(e)}",
                "entries": []
            }
    
    def delete_entry(self, user_id: int, entry_id: str) -> Dict[str, Any]:
        """Delete a voice journal entry"""
        try:
            entries = session.get('voice_journal_entries', [])
            
            # Find and remove the entry
            original_count = len(entries)
            entries[:] = [
                entry for entry in entries
                if not (entry.get('user_id') == user_id and entry.get('id') == entry_id)
            ]
            
            if len(entries) < original_count:
                session['voice_journal_entries'] = entries
                logger.info(f"🗑️ Deleted voice journal entry {entry_id} for user {user_id}")
                return {
                    "success": True,
                    "message": "Entry deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Entry not found or access denied"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to delete voice journal entry: {e}")
            return {
                "success": False,
                "error": f"Failed to delete entry: {str(e)}"
            }
    
    def get_emotion_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get emotional trends from journal entries"""
        try:
            entries_result = self.get_entries(user_id, limit=100)
            if not entries_result.get('success'):
                return entries_result
            
            entries = entries_result.get('entries', [])
            
            # Filter entries from last N days
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_entries = []
            for entry in entries:
                try:
                    entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                    if entry_date >= cutoff_date:
                        recent_entries.append(entry)
                except:
                    continue
            
            if not recent_entries:
                return {
                    "success": True,
                    "trends": {
                        "total_entries": 0,
                        "average_mood": 0,
                        "common_emotions": [],
                        "mood_trend": "neutral"
                    }
                }
            
            # Calculate trends
            mood_scores = []
            all_emotions = []
            
            for entry in recent_entries:
                analysis = entry.get('analysis', {})
                mood_score = analysis.get('mood_score', 0)
                emotions = analysis.get('emotions', [])
                
                if mood_score > 0:
                    mood_scores.append(mood_score)
                all_emotions.extend(emotions)
            
            # Calculate statistics
            avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
            
            # Count emotion frequency
            emotion_counts = {}
            for emotion in all_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Get top 5 emotions
            common_emotions = sorted(
                emotion_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # Determine mood trend
            if len(mood_scores) >= 3:
                recent_avg = sum(mood_scores[-3:]) / 3
                older_avg = sum(mood_scores[:-3]) / len(mood_scores[:-3]) if len(mood_scores) > 3 else recent_avg
                
                if recent_avg > older_avg + 0.5:
                    mood_trend = "improving"
                elif recent_avg < older_avg - 0.5:
                    mood_trend = "declining"
                else:
                    mood_trend = "stable"
            else:
                mood_trend = "insufficient_data"
            
            return {
                "success": True,
                "trends": {
                    "total_entries": len(recent_entries),
                    "average_mood": round(avg_mood, 1),
                    "common_emotions": [{"emotion": emotion, "count": count} for emotion, count in common_emotions],
                    "mood_trend": mood_trend,
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get emotion trends: {e}")
            return {
                "success": False,
                "error": f"Failed to analyze trends: {str(e)}"
            }
    
    def _generate_entry_id(self) -> str:
        """Generate unique entry ID"""
        import uuid
        return str(uuid.uuid4())[:8]