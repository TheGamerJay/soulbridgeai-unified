"""
SoulBridge AI - Profile Media Manager
Handles user profile image and video upload, storage, and serving
Extracted from backend/app.py with improvements - now supports MP4 videos
"""
import logging
import base64
import io
from PIL import Image
from typing import Dict, Any, Optional, Tuple
import mimetypes

logger = logging.getLogger(__name__)

class ProfileImageManager:
    """Manager for user profile images and videos"""
    
    def __init__(self, database=None):
        self.database = database
        self.allowed_image_formats = {'JPEG', 'JPG', 'PNG', 'WEBP'}
        self.allowed_video_formats = {'MP4'}
        self.max_image_size = 5 * 1024 * 1024  # 5MB for images
        self.max_video_size = 50 * 1024 * 1024  # 50MB for videos
        self.max_dimension = 1024  # Max width/height for images
        self.quality = 85  # JPEG quality
    
    def upload_profile_image(self, user_id: int, media_file) -> Dict[str, Any]:
        """Upload and process user profile image or video"""
        try:
            if not media_file or not media_file.filename:
                return {'success': False, 'error': 'No file provided'}
            
            # Validate file (images or videos)
            validation_result = self._validate_media_file(media_file)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Read media data
            media_file.seek(0)
            media_data = media_file.read()
            
            # Process based on file type
            if validation_result['media_type'] == 'image':
                # Process image (resize, optimize)
                processed_result = self._process_image(media_data)
                if not processed_result['success']:
                    return processed_result
                final_data = processed_result['image_data']
            else:  # video
                # For videos, store as-is (no processing needed)
                final_data = base64.b64encode(media_data).decode('utf-8')
            
            # Save to database
            save_result = self._save_image_to_database(user_id, final_data)
            if not save_result['success']:
                return save_result
            
            # Generate profile URL
            profile_url = f"/api/profile-image/{user_id}"
            
            logger.info(f"📷 Uploaded profile image for user {user_id}")
            
            return {
                'success': True,
                'profileImage': profile_url,
                'message': 'Profile image updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to upload profile image: {e}")
            return {'success': False, 'error': f'Failed to upload image: {str(e)}'}
    
    def get_profile_image(self, user_id: int) -> Dict[str, Any]:
        """Get user's profile image data"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Ensure columns exist
            self._ensure_image_columns(cursor)
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"SELECT profile_image, profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or not (result[0] or result[1]):
                return {'success': False, 'error': 'No profile image found'}
            
            # Return image data info
            return {
                'success': True,
                'has_image': bool(result[1]),
                'image_url': result[0] or f"/api/profile-image/{user_id}",
                'stored_as_data': bool(result[1])
            }
            
        except Exception as e:
            logger.error(f"Failed to get profile image info: {e}")
            return {'success': False, 'error': str(e)}
    
    def serve_profile_image(self, user_id: int) -> Tuple[Optional[bytes], Optional[str]]:
        """Serve profile image or video data for HTTP response"""
        try:
            if not self.database:
                return None, None
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"SELECT profile_image_data FROM users WHERE id = {placeholder}", (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                return None, None
            
            # Decode base64 media data (image or video)
            try:
                # Remove data URL prefix if present
                media_data = result[0]
                if media_data.startswith('data:'):
                    # Extract just the base64 data
                    header, data = media_data.split(',', 1)
                    mime_type = header.split(':')[1].split(';')[0]
                else:
                    data = media_data
                    # Try to detect file type from first few bytes after decoding
                    try:
                        decoded_sample = base64.b64decode(data[:100])  # Just check first chunk
                        if decoded_sample.startswith(b'\xFF\xD8\xFF'):
                            mime_type = 'image/jpeg'
                        elif decoded_sample.startswith(b'\x89PNG'):
                            mime_type = 'image/png'
                        elif b'WEBP' in decoded_sample:
                            mime_type = 'image/webp'
                        elif b'ftyp' in decoded_sample:
                            mime_type = 'video/mp4'
                        else:
                            mime_type = 'image/jpeg'  # Default fallback
                    except:
                        mime_type = 'image/jpeg'  # Default fallback
                
                media_bytes = base64.b64decode(data)
                return media_bytes, mime_type
                
            except Exception as decode_error:
                logger.error(f"Failed to decode profile media: {decode_error}")
                return None, None
            
        except Exception as e:
            logger.error(f"Failed to serve profile media: {e}")
            return None, None
    
    def delete_profile_image(self, user_id: int) -> Dict[str, Any]:
        """Delete user's profile image"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            cursor.execute(f"""
                UPDATE users 
                SET profile_image = NULL, profile_image_data = NULL 
                WHERE id = {placeholder}
            """, (user_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"🗑️ Deleted profile image for user {user_id}")
                return {'success': True, 'message': 'Profile image deleted successfully'}
            else:
                return {'success': False, 'error': 'User not found'}
            
        except Exception as e:
            logger.error(f"Failed to delete profile image: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_profile_image_url(self, user_id: int, 
                            profile_image_path: str = None, 
                            has_profile_data: bool = False) -> str:
        """Get the appropriate profile image URL for a user"""
        try:
            # Check if already in correct API format
            if profile_image_path and profile_image_path.startswith('/api/profile-image/'):
                return profile_image_path
            
            # If user has profile image data, use API endpoint
            if has_profile_data:
                return f"/api/profile-image/{user_id}"
            
            # If has old filesystem path, convert to API endpoint
            if (profile_image_path and 
                not profile_image_path.endswith(('Sapphire.png', 'New IntroLogo.png'))):
                return f"/api/profile-image/{user_id}"
            
            # Default image
            return '/static/logos/New IntroLogo.png'
            
        except Exception as e:
            logger.error(f"Failed to get profile image URL: {e}")
            return '/static/logos/New IntroLogo.png'
    
    def _validate_media_file(self, media_file) -> Dict[str, Any]:
        """Validate uploaded image or video file"""
        try:
            # Check file size
            media_file.seek(0, 2)  # Seek to end
            file_size = media_file.tell()
            media_file.seek(0)  # Reset
            
            # Check file format by reading header
            media_file.seek(0)
            header = media_file.read(12)
            media_file.seek(0)
            
            # Detect format from header
            if header.startswith(b'\xFF\xD8\xFF'):
                format_type = 'JPEG'
                media_type = 'image'
                max_size = self.max_image_size
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                format_type = 'PNG'
                media_type = 'image'
                max_size = self.max_image_size
            elif header.startswith(b'RIFF') and b'WEBP' in header:
                format_type = 'WEBP'
                media_type = 'image'
                max_size = self.max_image_size
            elif header.startswith(b'\x00\x00\x00') and b'ftyp' in header:
                # MP4 file signature
                format_type = 'MP4'
                media_type = 'video'
                max_size = self.max_video_size
            else:
                return {'valid': False, 'error': 'Unsupported file format. Please use JPEG, PNG, WEBP, or MP4.'}
            
            # Check size limit based on file type
            if file_size > max_size:
                return {
                    'valid': False, 
                    'error': f'File too large. Maximum size for {media_type}s: {max_size // (1024*1024)}MB'
                }
            
            if file_size < 100:  # Less than 100 bytes
                return {'valid': False, 'error': 'File appears to be empty'}
            
            # Validate format is allowed
            allowed_formats = self.allowed_image_formats if media_type == 'image' else self.allowed_video_formats
            if format_type not in allowed_formats:
                return {'valid': False, 'error': f'Unsupported format: {format_type}'}
            
            return {
                'valid': True,
                'format': format_type,
                'media_type': media_type,
                'size': file_size
            }
            
        except Exception as e:
            logger.error(f"Media validation error: {e}")
            return {'valid': False, 'error': 'Failed to validate media file'}
    
    def _process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process image (resize, optimize, convert to base64)"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for JPEG output)
            if image.mode in ['RGBA', 'LA', 'P']:
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ['RGBA', 'LA'] else None)
                image = background
            
            # Resize if too large
            if max(image.size) > self.max_dimension:
                image.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
                logger.info(f"📏 Resized image to {image.size}")
            
            # Convert to JPEG and encode as base64
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.quality, optimize=True)
            output.seek(0)
            
            # Create base64 data URL
            jpeg_data = output.getvalue()
            base64_data = base64.b64encode(jpeg_data).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{base64_data}"
            
            return {
                'success': True,
                'image_data': data_url,
                'size': len(jpeg_data),
                'dimensions': image.size
            }
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {'success': False, 'error': f'Failed to process image: {str(e)}'}
    
    def _save_image_to_database(self, user_id: int, image_data: str) -> Dict[str, Any]:
        """Save processed image data to database"""
        try:
            if not self.database:
                return {'success': False, 'error': 'Database not available'}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            # Ensure columns exist
            self._ensure_image_columns(cursor)
            
            # Save image data and set profile_image path
            profile_url = f"/api/profile-image/{user_id}"
            placeholder = "%s" if hasattr(self.database, 'use_postgres') and self.database.use_postgres else "?"
            
            cursor.execute(f"""
                UPDATE users 
                SET profile_image = {placeholder}, profile_image_data = {placeholder}
                WHERE id = {placeholder}
            """, (profile_url, image_data, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                return {'success': True}
            else:
                return {'success': False, 'error': 'User not found'}
            
        except Exception as e:
            logger.error(f"Failed to save image to database: {e}")
            return {'success': False, 'error': str(e)}
    
    def _ensure_image_columns(self, cursor) -> None:
        """Ensure profile image columns exist in database"""
        try:
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
            else:
                # SQLite - check if columns exist
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = [col[1] for col in cursor.fetchall()]
                
                if 'profile_image' not in existing_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
                if 'profile_image_data' not in existing_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN profile_image_data TEXT")
                    
        except Exception as e:
            logger.warning(f"Failed to ensure image columns: {e}")
    
    def get_image_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's profile image"""
        try:
            image_info = self.get_profile_image(user_id)
            
            if not image_info['success']:
                return {
                    'success': True,
                    'stats': {
                        'has_image': False,
                        'image_size': 0,
                        'storage_type': 'none'
                    }
                }
            
            # Get image data to calculate size
            image_bytes, mime_type = self.serve_profile_image(user_id)
            
            stats = {
                'has_image': image_info.get('has_image', False),
                'image_size': len(image_bytes) if image_bytes else 0,
                'mime_type': mime_type,
                'storage_type': 'database' if image_info.get('stored_as_data') else 'filesystem',
                'image_url': image_info.get('image_url')
            }
            
            return {'success': True, 'stats': stats}
            
        except Exception as e:
            logger.error(f"Failed to get image stats: {e}")
            return {'success': False, 'error': str(e)}