"""
SoulBridge AI - Content Service
Handles specific content types (chat, creative, fortune, etc.)
Extracted from monolith app.py with improvements
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from .library_manager import LibraryManager

logger = logging.getLogger(__name__)

class ContentService:
    """Service for managing specific content types in user library"""
    
    def __init__(self, database=None):
        self.database = database
        self.library_manager = LibraryManager(database)
    
    def save_chat_conversation(self, user_id: int, title: str, messages: List[Dict], 
                             companion_id: str = None) -> Optional[int]:
        """Save chat conversation to library"""
        try:
            # Prepare conversation data
            conversation_data = {
                'messages': messages,
                'companion_id': companion_id,
                'message_count': len(messages),
                'saved_at': datetime.now().isoformat()
            }
            
            # Create content for library
            conversation_text = self._format_conversation_for_storage(messages)
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='chat',
                title=title,
                content=conversation_text,
                metadata=conversation_data
            )
            
            if content_id:
                logger.info(f"💬 Saved chat conversation '{title}' for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save chat conversation: {e}")
            return None
    
    def save_fortune_reading(self, user_id: int, question: str, card: str, 
                           interpretation: str, spread: str = "single") -> Optional[int]:
        """Save fortune reading to library"""
        try:
            title = f"Fortune Reading - {question[:50]}{'...' if len(question) > 50 else ''}"
            
            # Prepare fortune data
            fortune_data = {
                'question': question,
                'card': card,
                'interpretation': interpretation,
                'spread': spread,
                'reading_date': datetime.now().isoformat()
            }
            
            # Create readable content
            content = f"Question: {question}\n\nCard Drawn: {card}\n\nInterpretation:\n{interpretation}"
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='fortune',
                title=title,
                content=content,
                metadata=fortune_data
            )
            
            if content_id:
                logger.info(f"🔮 Saved fortune reading for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save fortune reading: {e}")
            return None
    
    def save_horoscope_reading(self, user_id: int, sign: str, horoscope_text: str,
                             reading_type: str = "daily") -> Optional[int]:
        """Save horoscope reading to library"""
        try:
            title = f"{reading_type.title()} Horoscope - {sign}"
            
            # Prepare horoscope data
            horoscope_data = {
                'sign': sign,
                'reading_type': reading_type,
                'reading_date': datetime.now().isoformat()
            }
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='horoscope',
                title=title,
                content=horoscope_text,
                metadata=horoscope_data
            )
            
            if content_id:
                logger.info(f"⭐ Saved horoscope reading for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save horoscope reading: {e}")
            return None
    
    def save_decoder_session(self, user_id: int, input_text: str, decoded_text: str,
                           method: str = "ai") -> Optional[int]:
        """Save decoder session to library"""
        try:
            title = f"Decoder Session - {input_text[:30]}{'...' if len(input_text) > 30 else ''}"
            
            # Prepare decoder data
            decoder_data = {
                'input_text': input_text,
                'decoded_text': decoded_text,
                'method': method,
                'session_date': datetime.now().isoformat()
            }
            
            # Create readable content
            content = f"Original Text:\n{input_text}\n\nDecoded Message:\n{decoded_text}"
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='decoder',
                title=title,
                content=content,
                metadata=decoder_data
            )
            
            if content_id:
                logger.info(f"🔓 Saved decoder session for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save decoder session: {e}")
            return None
    
    def save_creative_writing(self, user_id: int, prompt: str, generated_text: str,
                            style: str = "general") -> Optional[int]:
        """Save creative writing to library"""
        try:
            title = f"Creative Writing - {prompt[:40]}{'...' if len(prompt) > 40 else ''}"
            
            # Prepare creative data
            creative_data = {
                'prompt': prompt,
                'style': style,
                'word_count': len(generated_text.split()),
                'created_date': datetime.now().isoformat()
            }
            
            # Create readable content
            content = f"Prompt: {prompt}\n\nStyle: {style}\n\nGenerated Text:\n{generated_text}"
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='creative',
                title=title,
                content=content,
                metadata=creative_data
            )
            
            if content_id:
                logger.info(f"✍️ Saved creative writing for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save creative writing: {e}")
            return None
    
    def save_ai_image(self, user_id: int, prompt: str, image_url: str, 
                     style: str = "photorealistic", size: str = "1024x1024") -> Optional[int]:
        """Save AI generated image to library"""
        try:
            title = f"AI Image - {prompt[:40]}{'...' if len(prompt) > 40 else ''}"
            
            # Prepare AI image data
            image_data = {
                'prompt': prompt,
                'image_url': image_url,
                'style': style,
                'size': size,
                'generated_date': datetime.now().isoformat()
            }
            
            # Create readable content
            content = f"Prompt: {prompt}\n\nStyle: {style}\nSize: {size}\nImage URL: {image_url}"
            
            content_id = self.library_manager.add_content(
                user_id=user_id,
                content_type='ai_image',
                title=title,
                content=content,
                metadata=image_data
            )
            
            if content_id:
                logger.info(f"🎨 Saved AI image to library for user {user_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to save AI image: {e}")
            return None
    
    def get_chat_conversations(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved chat conversations"""
        return self.library_manager.get_user_library(user_id, 'chat', limit)
    
    def get_fortune_readings(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved fortune readings"""
        return self.library_manager.get_user_library(user_id, 'fortune', limit)
    
    def get_horoscope_readings(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved horoscope readings"""
        return self.library_manager.get_user_library(user_id, 'horoscope', limit)
    
    def get_decoder_sessions(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved decoder sessions"""
        return self.library_manager.get_user_library(user_id, 'decoder', limit)
    
    def get_creative_writings(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved creative writings"""
        return self.library_manager.get_user_library(user_id, 'creative', limit)
    
    def get_recent_activity(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's recent library activity across all content types"""
        return self.library_manager.get_user_library(user_id, None, limit)
    
    def search_content(self, user_id: int, query: str, content_type: str = None) -> List[Dict[str, Any]]:
        """Search user's content library"""
        return self.library_manager.search_library(user_id, query, content_type)
    
    def get_content_with_plan_limits(self, user_id: int, content_type: str, 
                                   user_plan: str) -> Dict[str, Any]:
        """Get content respecting plan-based limits"""
        return self.library_manager.get_content_by_type_with_limits(
            user_id, content_type, user_plan
        )
    
    def _format_conversation_for_storage(self, messages: List[Dict]) -> str:
        """Format conversation messages for readable storage"""
        try:
            formatted_lines = []
            
            for message in messages:
                sender = message.get('sender', 'User')
                content = message.get('content', message.get('message', ''))
                timestamp = message.get('timestamp', '')
                
                if timestamp:
                    formatted_lines.append(f"[{timestamp}] {sender}: {content}")
                else:
                    formatted_lines.append(f"{sender}: {content}")
                formatted_lines.append("")  # Add blank line between messages
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            logger.error(f"Failed to format conversation: {e}")
            return str(messages)  # Fallback to raw data
    
    def export_user_library(self, user_id: int, content_type: str = None) -> Dict[str, Any]:
        """Export user's library content for backup/download"""
        try:
            library_items = self.library_manager.get_user_library(user_id, content_type)
            stats = self.library_manager.get_library_stats(user_id)
            
            export_data = {
                'user_id': user_id,
                'export_date': datetime.now().isoformat(),
                'content_type_filter': content_type,
                'total_items': len(library_items),
                'statistics': stats,
                'content': library_items
            }
            
            logger.info(f"📤 Exported {len(library_items)} library items for user {user_id}")
            
            return {
                'success': True,
                'data': export_data
            }
            
        except Exception as e:
            logger.error(f"Failed to export library: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def bulk_delete_content(self, user_id: int, content_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple content items in bulk"""
        try:
            deleted_count = 0
            failed_count = 0
            
            for content_id in content_ids:
                if self.library_manager.delete_content(user_id, content_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"🗑️ Bulk deleted {deleted_count} items for user {user_id}")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'total_requested': len(content_ids)
            }
            
        except Exception as e:
            logger.error(f"Failed bulk delete: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_count': 0,
                'failed_count': len(content_ids)
            }