"""
SoulBridge AI - Mini Studio Service
Handles integration with professional Docker-based music studio
"""
import logging
import requests
from typing import Dict, Any, Optional
from ..credits import get_artistic_time, deduct_artistic_time

logger = logging.getLogger(__name__)

class StudioService:
    """Service for integrating with professional Mini Studio Docker system"""
    
    def __init__(self):
        # Configure Docker service URLs (default to localhost for development)
        self.api_url = "http://localhost:8080"
        self.beats_url = "http://localhost:7001"  
        self.vocals_url = "http://localhost:7002"
        
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to studio services with error handling"""
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Studio service request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_credits(self, user_id: int) -> Dict[str, Any]:
        """Get user's artistic time credits for studio use"""
        try:
            credits = get_artistic_time(user_id)
            return {
                "success": True,
                "credits_remaining": credits,
                "credits_type": "artistic_time"
            }
        except Exception as e:
            logger.error(f"Error getting user credits: {e}")
            return {"success": False, "error": "Failed to get credits"}
    
    def ensure_project(self, user_id: int) -> Dict[str, Any]:
        """Ensure user has a studio project"""
        return self._make_request(
            "POST",
            f"{self.api_url}/api/projects/ensure",
            headers={"X-User-ID": str(user_id)}
        )
    
    def upload_asset(self, user_id: int, project_id: str, file_data: bytes, 
                    filename: str, asset_kind: str) -> Dict[str, Any]:
        """Upload asset to studio (lyrics, beat, midi)"""
        files = {"file": (filename, file_data)}
        data = {"project_id": project_id, "kind": asset_kind}
        
        try:
            response = requests.post(
                f"{self.api_url}/api/assets/upload",
                files=files,
                data=data,
                headers={"X-User-ID": str(user_id)},
                timeout=60
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            logger.error(f"Asset upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_lyrics(self, user_id: int, project_id: str, concept: str, 
                       bpm: int = 94, key_hint: str = "A minor", 
                       language: str = "spanglish") -> Dict[str, Any]:
        """Generate lyrics using OpenAI with structured outputs"""
        # Check and deduct credits (5 credits for lyrics generation)
        if not deduct_artistic_time(user_id, 5):
            return {"success": False, "error": "Insufficient artistic time credits"}
        
        payload = {
            "project_id": project_id,
            "concept": concept,
            "bpm": bpm,
            "key_hint": key_hint,
            "language": language
        }
        
        result = self._make_request(
            "POST",
            f"{self.api_url}/api/lyrics/generate",
            json=payload,
            headers={"X-User-ID": str(user_id)}
        )
        
        if not result["success"]:
            # Refund credits on failure
            deduct_artistic_time(user_id, -5)
        
        return result
    
    def compose_beat(self, user_id: int, project_id: str, prompt: str = "melodic trap beat",
                    bpm: int = 94, key: str = "A minor", seconds: int = 15,
                    demucs: bool = False) -> Dict[str, Any]:
        """Generate beat using MusicGen with MIDI stems"""
        # Check and deduct credits (10 credits for beat generation)
        if not deduct_artistic_time(user_id, 10):
            return {"success": False, "error": "Insufficient artistic time credits"}
        
        payload = {
            "project_id": project_id,
            "prompt": prompt,
            "bpm": bpm,
            "key": key,
            "seconds": seconds,
            "demucs": demucs
        }
        
        result = self._make_request(
            "POST",
            f"{self.api_url}/api/beats/compose",
            json=payload,
            headers={"X-User-ID": str(user_id)}
        )
        
        if not result["success"]:
            # Refund credits on failure
            deduct_artistic_time(user_id, -10)
        
        return result
    
    def generate_vocals(self, user_id: int, project_id: str, 
                       lyrics_asset_id: Optional[str] = None,
                       beat_asset_id: Optional[str] = None,
                       midi_asset_id: Optional[str] = None,
                       bpm: int = 94) -> Dict[str, Any]:
        """Generate vocals using DiffSinger"""
        # Calculate dynamic pricing based on what's provided
        has_lyrics = lyrics_asset_id is not None
        has_beat = beat_asset_id is not None
        
        # Pricing: 10 base + 5 for missing lyrics + 10 for missing beat
        cost = 10 + (0 if has_lyrics else 5) + (0 if has_beat else 10)
        
        if not deduct_artistic_time(user_id, cost):
            return {"success": False, "error": "Insufficient artistic time credits"}
        
        payload = {
            "project_id": project_id,
            "lyrics_asset_id": lyrics_asset_id,
            "beat_asset_id": beat_asset_id,
            "midi_asset_id": midi_asset_id,
            "bpm": bpm
        }
        
        result = self._make_request(
            "POST",
            f"{self.api_url}/api/vocals/sing",
            json=payload,
            headers={"X-User-ID": str(user_id)}
        )
        
        if not result["success"]:
            # Refund credits on failure
            deduct_artistic_time(user_id, -cost)
        
        return result
    
    def get_studio_library(self, user_id: int) -> Dict[str, Any]:
        """Get user's studio assets and projects"""
        return self._make_request(
            "GET",
            f"{self.api_url}/api/mini-studio/library",
            headers={"X-User-ID": str(user_id)}
        )
    
    def delete_asset(self, user_id: int, asset_id: str) -> Dict[str, Any]:
        """Delete asset from studio library"""
        return self._make_request(
            "DELETE",
            f"{self.api_url}/api/mini-studio/library/{asset_id}",
            headers={"X-User-ID": str(user_id)}
        )
    
    def export_asset(self, user_id: int, asset_id: str) -> Dict[str, Any]:
        """Export/download asset from studio"""
        try:
            response = requests.get(
                f"{self.api_url}/api/mini-studio/export/{asset_id}",
                headers={"X-User-ID": str(user_id)},
                timeout=60
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "content": response.content,
                "content_type": response.headers.get('Content-Type', 'application/octet-stream'),
                "filename": f"asset_{asset_id}.{self._get_extension_from_content_type(response.headers.get('Content-Type', ''))}"
            }
        except Exception as e:
            logger.error(f"Asset export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type"""
        type_map = {
            'audio/wav': 'wav',
            'audio/mp3': 'mp3',
            'application/zip': 'zip',
            'application/json': 'json',
            'text/plain': 'txt',
            'audio/midi': 'mid'
        }
        return type_map.get(content_type, 'bin')
    
    def check_studio_health(self) -> Dict[str, Any]:
        """Check if all studio services are running"""
        services = {
            "api": self.api_url,
            "beats": self.beats_url,
            "vocals": self.vocals_url
        }
        
        status = {}
        all_healthy = True
        
        for service_name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                status[service_name] = {
                    "healthy": response.status_code == 200,
                    "status_code": response.status_code
                }
            except Exception:
                status[service_name] = {
                    "healthy": False,
                    "error": "Service unreachable"
                }
                all_healthy = False
        
        return {
            "success": True,
            "all_healthy": all_healthy,
            "services": status
        }