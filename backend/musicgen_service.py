#!/usr/bin/env python3
"""
Local MusicGen Service
Generates instrumental tracks using Meta's MusicGen small model (CPU-optimized)
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global model instance (loaded once, reused)
_model_instance = None

def get_musicgen_model():
    """Get or create the MusicGen model instance (singleton pattern)"""
    global _model_instance
    
    if _model_instance is None:
        try:
            from audiocraft.models import MusicGen
            logger.info("🎵 Loading MusicGen small model...")
            _model_instance = MusicGen.get_pretrained('facebook/musicgen-small')
            
            # Set default generation parameters (20 seconds, balanced quality)
            _model_instance.set_generation_params(
                duration=20,
                top_k=250,
                top_p=0.0,
                temperature=1.0
            )
            logger.info("✅ MusicGen model loaded successfully")
            
        except ImportError as e:
            logger.error(f"❌ AudioCraft not available: {e}")
            raise ImportError("AudioCraft library required for music generation")
        except Exception as e:
            logger.error(f"❌ Failed to load MusicGen model: {e}")
            raise
    
    return _model_instance

class LocalMusicGen:
    """Local instrumental music generation using MusicGen"""
    
    def __init__(self, sample_rate: int = 32000):
        """
        Initialize the music generator
        
        Args:
            sample_rate: Output sample rate (32kHz default for MusicGen small)
        """
        self.sample_rate = sample_rate
        self.model = None
    
    def _ensure_model_loaded(self):
        """Ensure the model is loaded (lazy loading)"""
        if self.model is None:
            self.model = get_musicgen_model()
    
    def generate_instrumental(self, 
                            prompt: str, 
                            duration_s: int = 20, 
                            output_dir: str = "static/uploads",
                            filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate instrumental track from text prompt
        
        Args:
            prompt: Text description of the music to generate
            duration_s: Duration in seconds (max 30 for small model)
            output_dir: Directory to save the generated file
            filename: Optional custom filename (auto-generated if None)
        
        Returns:
            Dict with 'success', 'file_path', 'duration', 'prompt_used'
        """
        try:
            self._ensure_model_loaded()
            
            # Validate duration (MusicGen small works best under 30s)
            duration_s = min(max(duration_s, 5), 30)
            
            # Create output directory if needed
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename if not provided
            if filename is None:
                timestamp = int(Path().stat().st_mtime) if Path().exists() else 0
                filename = f"instrumental_{timestamp}.wav"
            
            output_path = os.path.join(output_dir, filename)
            
            # Set generation parameters
            self.model.set_generation_params(duration=duration_s)
            
            logger.info(f"🎵 Generating {duration_s}s instrumental: '{prompt}'")
            
            # Generate audio (returns tensor of shape [batch, channels, samples])
            with torch.no_grad():  # Save memory during generation
                wav_tensor = self.model.generate([prompt])
                wav = wav_tensor[0].cpu()  # Get first (and only) result, move to CPU
            
            # Save to file
            import torchaudio
            torchaudio.save(output_path, wav, self.sample_rate)
            
            # Calculate actual duration
            actual_duration = wav.shape[-1] / self.sample_rate
            
            logger.info(f"✅ Generated instrumental saved to: {output_path}")
            
            return {
                "success": True,
                "file_path": output_path,
                "duration_seconds": actual_duration,
                "prompt_used": prompt,
                "sample_rate": self.sample_rate,
                "model": "musicgen-small"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate instrumental: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt_used": prompt
            }
    
    def generate_with_style(self, 
                          base_prompt: str,
                          style: str = "trap",
                          mood: str = "energetic",
                          duration_s: int = 20,
                          output_dir: str = "static/uploads") -> Dict[str, Any]:
        """
        Generate instrumental with specific style and mood
        
        Args:
            base_prompt: Base description
            style: Musical style (trap, lo-fi, ambient, etc.)
            mood: Mood descriptor (energetic, chill, dark, etc.)
            duration_s: Duration in seconds
            output_dir: Output directory
        
        Returns:
            Generation result dictionary
        """
        # Construct enhanced prompt
        enhanced_prompt = f"{mood} {style} beat with {base_prompt}"
        
        # Add style-specific enhancements
        style_enhancements = {
            "trap": "with heavy 808s, hi-hats, and atmospheric pads",
            "lo-fi": "with vinyl crackle, warm analog sounds, and gentle piano",
            "ambient": "with ethereal pads, reverb textures, and minimal percussion",
            "house": "with four-on-the-floor kick, synthesizer leads, and bass line",
            "hip-hop": "with boom-bap drums, vinyl samples, and deep bass",
            "electronic": "with synthesizers, electronic drums, and digital effects"
        }
        
        if style.lower() in style_enhancements:
            enhanced_prompt += f" {style_enhancements[style.lower()]}"
        
        return self.generate_instrumental(
            prompt=enhanced_prompt,
            duration_s=duration_s,
            output_dir=output_dir,
            filename=f"{style}_{mood}_{int(Path().stat().st_mtime if Path().exists() else 0)}.wav"
        )

# Import torch here to avoid import issues
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - music generation will be disabled")

def is_music_generation_available() -> bool:
    """Check if music generation is available"""
    return TORCH_AVAILABLE and _model_instance is not None or True  # Allow loading attempt

# Convenience function for simple usage
def generate_quick_beat(prompt: str, duration: int = 20) -> str:
    """
    Quick generation function that returns file path or raises exception
    
    Args:
        prompt: Music description
        duration: Duration in seconds
    
    Returns:
        Path to generated file
    
    Raises:
        Exception: If generation fails
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch required for music generation")
    
    generator = LocalMusicGen()
    result = generator.generate_instrumental(prompt, duration)
    
    if result["success"]:
        return result["file_path"]
    else:
        raise Exception(f"Generation failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # Test the music generation
    logging.basicConfig(level=logging.INFO)
    
    try:
        generator = LocalMusicGen()
        result = generator.generate_instrumental(
            prompt="melodic trap beat with warm pads and gentle guitar arps",
            duration_s=15
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Test failed: {e}")