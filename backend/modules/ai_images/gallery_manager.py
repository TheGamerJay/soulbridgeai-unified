"""
SoulBridge AI - AI Image Gallery Manager
Handles user gallery storage and management for generated images
Extracted from backend/app.py with improvements
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class GalleryManager:
    """Manager for user AI image galleries"""
    
    def __init__(self, database=None):
        self.database = database
        self.max_gallery_size = 100  # Maximum images per user
        
    def save_image_to_gallery(self, user_id: int, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save generated image to user's gallery"""
        try:
            # Validate required fields
            required_fields = ['imageUrl', 'prompt', 'style']
            for field in required_fields:
                if field not in image_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Create image record
            image_record = {
                'id': self._generate_image_id(user_id),
                'user_id': user_id,
                'image_url': image_data.get('imageUrl'),
                'original_prompt': image_data.get('prompt'),
                'enhanced_prompt': image_data.get('enhancedPrompt', ''),
                'revised_prompt': image_data.get('revisedPrompt', ''),
                'style': image_data.get('style'),
                'size': image_data.get('size', '1024x1024'),
                'quality': image_data.get('quality', 'standard'),
                'generation_time': image_data.get('generationTime', datetime.now().isoformat()),
                'saved_at': datetime.now().isoformat(),
                'is_favorite': False,
                'tags': image_data.get('tags', []),
                'metadata': image_data.get('metadata', {})
            }
            
            # Save to database or session (depending on implementation)
            if self.database:
                success = self._save_to_database(user_id, image_record)
            else:
                success = self._save_to_session(user_id, image_record)
            
            if success:
                logger.info(f"🖼️ Saved AI image to gallery for user {user_id}")
                return {
                    'success': True,
                    'image_id': image_record['id'],
                    'message': 'Image saved to gallery successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save image to gallery'
                }
            
        except Exception as e:
            logger.error(f"Failed to save image to gallery: {e}")
            return {
                'success': False,
                'error': f'Failed to save image: {str(e)}'
            }
    
    def get_user_gallery(self, user_id: int, limit: int = 50, 
                        favorites_only: bool = False) -> Dict[str, Any]:
        """Get user's AI image gallery"""
        try:
            if self.database:
                images = self._get_from_database(user_id, limit, favorites_only)
            else:
                images = self._get_from_session(user_id, limit, favorites_only)
            
            # Sort by saved time, most recent first
            images.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
            
            # Get gallery stats
            stats = self._calculate_gallery_stats(images)
            
            logger.info(f"📖 Retrieved {len(images)} AI images for user {user_id}")
            
            return {
                'success': True,
                'images': images,
                'count': len(images),
                'stats': stats,
                'has_more': len(images) == limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get user gallery: {e}")
            return {
                'success': False,
                'error': 'Failed to retrieve gallery',
                'images': []
            }
    
    def get_image_by_id(self, user_id: int, image_id: str) -> Optional[Dict[str, Any]]:
        """Get specific image by ID"""
        try:
            if self.database:
                return self._get_image_from_database(user_id, image_id)
            else:
                return self._get_image_from_session(user_id, image_id)
        
        except Exception as e:
            logger.error(f"Failed to get image by ID: {e}")
            return None
    
    def update_image(self, user_id: int, image_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update image metadata"""
        try:
            # Get current image
            current_image = self.get_image_by_id(user_id, image_id)
            if not current_image:
                return {
                    'success': False,
                    'error': 'Image not found'
                }
            
            # Update allowed fields
            allowed_fields = ['tags', 'is_favorite', 'metadata']
            updated_fields = {}
            
            for field, value in updates.items():
                if field in allowed_fields:
                    updated_fields[field] = value
            
            if not updated_fields:
                return {
                    'success': False,
                    'error': 'No valid fields to update'
                }
            
            # Apply updates
            for field, value in updated_fields.items():
                current_image[field] = value
            
            current_image['updated_at'] = datetime.now().isoformat()
            
            # Save updated image
            if self.database:
                success = self._update_in_database(user_id, image_id, current_image)
            else:
                success = self._update_in_session(user_id, image_id, current_image)
            
            if success:
                logger.info(f"📝 Updated AI image {image_id} for user {user_id}")
                return {
                    'success': True,
                    'updated_image': current_image
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update image'
                }
            
        except Exception as e:
            logger.error(f"Failed to update image: {e}")
            return {
                'success': False,
                'error': f'Failed to update image: {str(e)}'
            }
    
    def delete_image(self, user_id: int, image_id: str) -> Dict[str, Any]:
        """Delete image from gallery"""
        try:
            # Check if image exists
            image = self.get_image_by_id(user_id, image_id)
            if not image:
                return {
                    'success': False,
                    'error': 'Image not found'
                }
            
            # Delete from storage
            if self.database:
                success = self._delete_from_database(user_id, image_id)
            else:
                success = self._delete_from_session(user_id, image_id)
            
            if success:
                logger.info(f"🗑️ Deleted AI image {image_id} for user {user_id}")
                return {
                    'success': True,
                    'message': 'Image deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to delete image'
                }
            
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            return {
                'success': False,
                'error': f'Failed to delete image: {str(e)}'
            }
    
    def toggle_favorite(self, user_id: int, image_id: str) -> Dict[str, Any]:
        """Toggle favorite status for an image"""
        try:
            image = self.get_image_by_id(user_id, image_id)
            if not image:
                return {
                    'success': False,
                    'error': 'Image not found'
                }
            
            new_favorite_status = not image.get('is_favorite', False)
            
            update_result = self.update_image(user_id, image_id, {
                'is_favorite': new_favorite_status
            })
            
            if update_result['success']:
                logger.info(f"⭐ Toggled favorite for image {image_id}: {new_favorite_status}")
                return {
                    'success': True,
                    'is_favorite': new_favorite_status
                }
            else:
                return update_result
            
        except Exception as e:
            logger.error(f"Failed to toggle favorite: {e}")
            return {
                'success': False,
                'error': f'Failed to toggle favorite: {str(e)}'
            }
    
    def search_gallery(self, user_id: int, query: str) -> Dict[str, Any]:
        """Search user's image gallery"""
        try:
            # Get all user images
            gallery_result = self.get_user_gallery(user_id, limit=1000)
            if not gallery_result['success']:
                return gallery_result
            
            images = gallery_result['images']
            
            if not query.strip():
                return gallery_result
            
            # Search in prompts, tags, and metadata
            query_lower = query.lower().strip()
            matching_images = []
            
            for image in images:
                # Search in prompts
                original_prompt = image.get('original_prompt', '').lower()
                enhanced_prompt = image.get('enhanced_prompt', '').lower()
                
                # Search in tags
                tags = [tag.lower() for tag in image.get('tags', [])]
                
                # Search in style
                style = image.get('style', '').lower()
                
                if (query_lower in original_prompt or 
                    query_lower in enhanced_prompt or 
                    query_lower in style or 
                    any(query_lower in tag for tag in tags)):
                    matching_images.append(image)
            
            logger.info(f"🔍 Found {len(matching_images)} matching images for user {user_id}")
            
            return {
                'success': True,
                'images': matching_images,
                'count': len(matching_images),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Failed to search gallery: {e}")
            return {
                'success': False,
                'error': 'Failed to search gallery',
                'images': []
            }
    
    def _generate_image_id(self, user_id: int) -> str:
        """Generate unique image ID"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"img_{user_id}_{timestamp}"
        except Exception:
            import uuid
            return str(uuid.uuid4())
    
    def _calculate_gallery_stats(self, images: List[Dict]) -> Dict[str, Any]:
        """Calculate gallery statistics"""
        try:
            if not images:
                return {
                    'total_images': 0,
                    'favorites': 0,
                    'styles': {},
                    'sizes': {},
                    'most_recent': None
                }
            
            # Count by style
            styles = {}
            sizes = {}
            favorites = 0
            
            for image in images:
                # Count styles
                style = image.get('style', 'unknown')
                styles[style] = styles.get(style, 0) + 1
                
                # Count sizes
                size = image.get('size', 'unknown')
                sizes[size] = sizes.get(size, 0) + 1
                
                # Count favorites
                if image.get('is_favorite', False):
                    favorites += 1
            
            most_recent = images[0] if images else None
            
            return {
                'total_images': len(images),
                'favorites': favorites,
                'styles': styles,
                'sizes': sizes,
                'most_recent': most_recent
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate stats: {e}")
            return {'error': str(e)}
    
    # Database implementation placeholders
    def _save_to_database(self, user_id: int, image_record: Dict) -> bool:
        """Save image to database (placeholder for future implementation)"""
        # TODO: Implement database storage using user_library table
        # Could use content_type='ai_image' with image data in metadata
        return False
    
    def _get_from_database(self, user_id: int, limit: int, favorites_only: bool) -> List[Dict]:
        """Get images from database (placeholder)"""
        # TODO: Implement database retrieval
        return []
    
    def _get_image_from_database(self, user_id: int, image_id: str) -> Optional[Dict]:
        """Get specific image from database (placeholder)"""
        # TODO: Implement database lookup
        return None
    
    def _update_in_database(self, user_id: int, image_id: str, image_data: Dict) -> bool:
        """Update image in database (placeholder)"""
        # TODO: Implement database update
        return False
    
    def _delete_from_database(self, user_id: int, image_id: str) -> bool:
        """Delete image from database (placeholder)"""
        # TODO: Implement database deletion
        return False
    
    # Session implementation (current fallback)
    def _save_to_session(self, user_id: int, image_record: Dict) -> bool:
        """Save image to session storage (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        # Placeholder for session-based storage
        return True
    
    def _get_from_session(self, user_id: int, limit: int, favorites_only: bool) -> List[Dict]:
        """Get images from session storage (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        # Placeholder for session-based retrieval
        return []
    
    def _get_image_from_session(self, user_id: int, image_id: str) -> Optional[Dict]:
        """Get specific image from session (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        return None
    
    def _update_in_session(self, user_id: int, image_id: str, image_data: Dict) -> bool:
        """Update image in session (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        return True
    
    def _delete_from_session(self, user_id: int, image_id: str) -> bool:
        """Delete image from session (temporary implementation)"""
        # This would be implemented in the route handler using Flask session
        return True