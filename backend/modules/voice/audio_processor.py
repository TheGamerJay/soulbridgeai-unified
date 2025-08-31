"""
SoulBridge AI - Audio Processor
Audio processing utilities for voice features
Handles file validation, format conversion, and audio analysis
"""
import os
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio processing utilities for voice features"""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.webm', '.aac'}
    MAX_SIZE_VOICE_CHAT = 10 * 1024 * 1024  # 10MB
    MAX_SIZE_VOICE_JOURNAL = 25 * 1024 * 1024  # 25MB
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available for audio conversion"""
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            logger.info("✅ FFmpeg available for audio processing")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ FFmpeg not available - audio conversion disabled")
            return False
    
    def validate_audio_file(
        self, 
        audio_file, 
        max_size: Optional[int] = None,
        feature_type: str = "voice_chat"
    ) -> Dict[str, Any]:
        """Validate audio file for processing"""
        try:
            if not audio_file or not audio_file.filename:
                return {
                    "valid": False, 
                    "error": "No audio file provided"
                }
            
            filename = audio_file.filename
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Check file extension
            if file_ext not in self.SUPPORTED_FORMATS:
                return {
                    "valid": False,
                    "error": f"Unsupported format '{file_ext}'. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                }
            
            # Check file size
            if max_size is None:
                max_size = (
                    self.MAX_SIZE_VOICE_JOURNAL 
                    if feature_type == "voice_journal" 
                    else self.MAX_SIZE_VOICE_CHAT
                )
            
            audio_file.seek(0, 2)  # Seek to end
            size = audio_file.tell()
            audio_file.seek(0)  # Seek back to beginning
            
            if size > max_size:
                max_mb = max_size // (1024 * 1024)
                return {
                    "valid": False,
                    "error": f"File too large ({size // (1024*1024)}MB). Max: {max_mb}MB"
                }
            
            # Basic file content validation
            if size < 1024:  # Less than 1KB
                return {
                    "valid": False,
                    "error": "File appears to be empty or corrupted"
                }
            
            logger.info(f"✅ Audio file validated: {filename} ({size // 1024}KB)")
            
            return {
                "valid": True,
                "filename": filename,
                "size": size,
                "format": file_ext,
                "size_mb": round(size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Audio validation error: {e}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    def get_audio_duration(self, audio_file) -> Optional[float]:
        """Get audio duration in seconds (requires FFmpeg)"""
        if not self.ffmpeg_available:
            return None
        
        try:
            import subprocess
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                audio_file.save(tmp_file.name)
                
                try:
                    # Use FFprobe to get duration
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-show_entries', 
                        'format=duration', '-of', 'csv=p=0', tmp_file.name
                    ], capture_output=True, text=True, check=True)
                    
                    duration = float(result.stdout.strip())
                    logger.info(f"📏 Audio duration: {duration:.2f}s")
                    
                    return duration
                    
                finally:
                    # Clean up
                    os.unlink(tmp_file.name)
                    audio_file.seek(0)  # Reset file pointer
                    
        except Exception as e:
            logger.error(f"❌ Failed to get audio duration: {e}")
            return None
    
    def convert_to_wav(self, audio_file, output_sample_rate: int = 16000) -> Optional[str]:
        """Convert audio file to WAV format (requires FFmpeg)"""
        if not self.ffmpeg_available:
            logger.warning("Cannot convert audio - FFmpeg not available")
            return None
        
        try:
            import subprocess
            
            # Create input and output temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as input_tmp:
                audio_file.save(input_tmp.name)
                
                output_tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix='.wav'
                )
                output_tmp.close()
                
                try:
                    # Convert using FFmpeg
                    subprocess.run([
                        'ffmpeg', '-i', input_tmp.name,
                        '-ar', str(output_sample_rate),
                        '-ac', '1',  # Mono
                        '-y',  # Overwrite output
                        output_tmp.name
                    ], capture_output=True, check=True)
                    
                    logger.info(f"✅ Audio converted to WAV: {output_sample_rate}Hz")
                    
                    # Reset original file pointer
                    audio_file.seek(0)
                    
                    return output_tmp.name
                    
                finally:
                    # Clean up input file
                    os.unlink(input_tmp.name)
                    
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return None
    
    def analyze_audio_quality(self, audio_file) -> Dict[str, Any]:
        """Analyze audio quality and provide recommendations"""
        try:
            validation = self.validate_audio_file(audio_file)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # Get basic info
            size = validation["size"]
            format_ext = validation["format"]
            
            # Get duration if possible
            duration = self.get_audio_duration(audio_file)
            
            # Calculate approximate bitrate
            bitrate = None
            if duration and duration > 0:
                bitrate = (size * 8) / duration / 1000  # kbps
            
            # Quality assessment
            quality_score = 0
            recommendations = []
            
            # Format assessment
            if format_ext in ['.wav', '.flac']:
                quality_score += 30
            elif format_ext in ['.mp3', '.m4a']:
                quality_score += 20
            else:
                quality_score += 10
                recommendations.append("Consider using WAV or MP3 format for better compatibility")
            
            # Size/bitrate assessment
            if bitrate:
                if bitrate >= 128:
                    quality_score += 30
                elif bitrate >= 96:
                    quality_score += 20
                    recommendations.append("Audio bitrate is acceptable but could be higher for better quality")
                else:
                    quality_score += 10
                    recommendations.append("Low bitrate detected - consider higher quality recording")
            
            # Duration assessment
            if duration:
                if 5 <= duration <= 300:  # 5 seconds to 5 minutes
                    quality_score += 20
                elif duration < 5:
                    quality_score += 10
                    recommendations.append("Very short audio - ensure complete message is captured")
                else:
                    quality_score += 15
                    recommendations.append("Long audio file - consider breaking into shorter segments")
            
            # File size assessment
            size_mb = size / (1024 * 1024)
            if size_mb <= 5:
                quality_score += 20
            elif size_mb <= 15:
                quality_score += 15
            else:
                recommendations.append("Large file size - processing may take longer")
            
            # Overall quality rating
            if quality_score >= 80:
                quality_rating = "excellent"
            elif quality_score >= 60:
                quality_rating = "good"
            elif quality_score >= 40:
                quality_rating = "fair"
            else:
                quality_rating = "poor"
            
            # General recommendations
            if not recommendations:
                recommendations.append("Audio quality looks good for processing")
            
            logger.info(f"📊 Audio quality analysis: {quality_rating} ({quality_score}/100)")
            
            return {
                "success": True,
                "analysis": {
                    "quality_score": quality_score,
                    "quality_rating": quality_rating,
                    "format": format_ext,
                    "size_mb": round(size_mb, 2),
                    "duration_seconds": duration,
                    "estimated_bitrate_kbps": round(bitrate) if bitrate else None,
                    "recommendations": recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Audio quality analysis failed: {e}")
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
    
    def prepare_for_processing(
        self, 
        audio_file, 
        target_format: str = "wav",
        target_sample_rate: int = 16000
    ) -> Optional[str]:
        """Prepare audio file for AI processing"""
        try:
            # Validate file first
            validation = self.validate_audio_file(audio_file)
            if not validation["valid"]:
                logger.error(f"Cannot prepare invalid audio file: {validation['error']}")
                return None
            
            current_format = validation["format"]
            
            # If already in target format, just save to temp file
            if current_format == f'.{target_format.lower()}' and not self.ffmpeg_available:
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=f'.{target_format}'
                ) as tmp_file:
                    audio_file.save(tmp_file.name)
                    audio_file.seek(0)  # Reset pointer
                    
                    logger.info(f"✅ Audio prepared (no conversion): {tmp_file.name}")
                    return tmp_file.name
            
            # Convert if needed and possible
            if target_format.lower() == "wav" and self.ffmpeg_available:
                converted_path = self.convert_to_wav(audio_file, target_sample_rate)
                if converted_path:
                    logger.info(f"✅ Audio prepared (converted): {converted_path}")
                    return converted_path
            
            # Fallback: just save as-is
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=current_format
            ) as tmp_file:
                audio_file.save(tmp_file.name)
                audio_file.seek(0)  # Reset pointer
                
                logger.info(f"✅ Audio prepared (fallback): {tmp_file.name}")
                return tmp_file.name
                
        except Exception as e:
            logger.error(f"❌ Audio preparation failed: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_file(filepath: str) -> bool:
        """Clean up temporary audio file"""
        try:
            if filepath and os.path.exists(filepath):
                os.unlink(filepath)
                logger.debug(f"🧹 Cleaned up temp file: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to cleanup temp file {filepath}: {e}")
            return False