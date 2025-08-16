#!/usr/bin/env python3
"""
Cover Art Generation Service
Creates album/track cover art using OpenAI DALL-E API
"""

import os
import logging
import base64
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available - cover art generation disabled")

class CoverArtGenerator:
    """Generate cover art using OpenAI DALL-E"""
    
    def __init__(self):
        """Initialize the cover art generator"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library required for cover art generation")
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        self.client = OpenAI(api_key=api_key)
        
        # Style presets for different music genres
        self.style_presets = {
            "trap": "dark urban cityscape with neon lights, cyberpunk aesthetic, purple and cyan color scheme",
            "lo-fi": "cozy vintage aesthetic, warm analog colors, retro tape cassette vibes, pastel tones", 
            "ambient": "ethereal abstract landscape, flowing organic shapes, soft gradients, misty atmosphere",
            "house": "vibrant geometric patterns, disco ball reflections, energetic party atmosphere, bright colors",
            "hip-hop": "street art graffiti style, bold urban typography, concrete textures, gold accents",
            "electronic": "futuristic digital interface, circuit board patterns, electric blue glows, tech aesthetic",
            "rock": "grungy textures, distressed metal surfaces, bold typography, black and red color scheme",
            "jazz": "sophisticated vintage club atmosphere, art deco patterns, warm golden lighting",
            "classical": "elegant minimalist design, sheet music elements, orchestral instruments, refined typography",
            "pop": "colorful trendy design, playful geometric shapes, bright gradients, modern aesthetic"
        }
    
    def generate_cover_art(self, 
                          prompt: str,
                          style: str = "modern",
                          size: str = "1024x1024",
                          output_dir: str = "static/uploads",
                          filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate cover art from text prompt
        
        Args:
            prompt: Description of the desired artwork
            style: Art style or music genre for style preset
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            output_dir: Directory to save the generated image
            filename: Optional custom filename
        
        Returns:
            Dict with success status and file path
        """
        try:
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Enhance prompt with style preset if available
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = int(datetime.now().timestamp())
                safe_style = "".join(c for c in style if c.isalnum())
                filename = f"cover_art_{safe_style}_{timestamp}.png"
            
            output_path = os.path.join(output_dir, filename)
            
            logger.info(f"🎨 Generating cover art: '{enhanced_prompt}'")
            
            # Generate image using DALL-E
            response = self.client.images.generate(
                model="dall-e-3",  # Use DALL-E 3 for higher quality
                prompt=enhanced_prompt,
                size=size,
                quality="standard",  # or "hd" for higher quality (more expensive)
                n=1
            )
            
            # Get the image URL or base64 data
            image_url = response.data[0].url
            
            if image_url:
                # Download and save the image
                import requests
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(image_response.content)
                
                logger.info(f"✅ Cover art saved to: {output_path}")
                
                return {
                    "success": True,
                    "file_path": output_path,
                    "image_url": image_url,
                    "prompt_used": enhanced_prompt,
                    "original_prompt": prompt,
                    "style": style,
                    "size": size,
                    "model": "dall-e-3"
                }
            else:
                return {
                    "success": False,
                    "error": "No image URL returned from OpenAI",
                    "prompt_used": enhanced_prompt
                }
            
        except Exception as e:
            logger.error(f"❌ Cover art generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt_used": enhanced_prompt if 'enhanced_prompt' in locals() else prompt
            }
    
    def _enhance_prompt(self, base_prompt: str, style: str) -> str:
        """
        Enhance the prompt with style-specific elements
        
        Args:
            base_prompt: User's base prompt
            style: Style identifier
        
        Returns:
            Enhanced prompt
        """
        # Start with base prompt
        enhanced = base_prompt
        
        # Add style preset if available
        if style.lower() in self.style_presets:
            style_elements = self.style_presets[style.lower()]
            enhanced = f"{base_prompt}, {style_elements}"
        
        # Add general cover art improvements
        enhanced += ", album cover design, professional artwork, high quality digital art"
        
        # Ensure it's appropriate for cover art
        if "explicit" not in enhanced.lower():
            enhanced += ", clean and artistic"
        
        return enhanced
    
    def generate_track_cover(self, 
                           track_title: str,
                           artist_name: str = "SoulBridge AI",
                           genre: str = "electronic",
                           mood: str = "energetic",
                           output_dir: str = "static/uploads") -> Dict[str, Any]:
        """
        Generate cover art specifically for a track
        
        Args:
            track_title: Name of the track
            artist_name: Artist name to include
            genre: Music genre for styling
            mood: Mood of the track
            output_dir: Output directory
        
        Returns:
            Generation result
        """
        # Create prompt based on track info
        prompt = f"Album cover for '{track_title}' by {artist_name}, {mood} {genre} music"
        
        return self.generate_cover_art(
            prompt=prompt,
            style=genre,
            output_dir=output_dir,
            filename=f"cover_{track_title.replace(' ', '_').lower()}.png"
        )
    
    def generate_compilation_cover(self, 
                                 tracks: list,
                                 compilation_name: str = "Mini Studio Collection",
                                 output_dir: str = "static/uploads") -> Dict[str, Any]:
        """
        Generate cover art for a compilation/album
        
        Args:
            tracks: List of track information
            compilation_name: Name of the compilation
            output_dir: Output directory
        
        Returns:
            Generation result
        """
        # Analyze tracks to determine style
        genres = []
        moods = []
        
        for track in tracks:
            if isinstance(track, dict):
                genres.append(track.get('genre', 'electronic'))
                moods.append(track.get('mood', 'energetic'))
        
        # Find most common genre and mood
        most_common_genre = max(set(genres), key=genres.count) if genres else 'electronic'
        most_common_mood = max(set(moods), key=moods.count) if moods else 'energetic'
        
        prompt = f"Album cover for '{compilation_name}', collection of {most_common_mood} {most_common_genre} tracks"
        
        return self.generate_cover_art(
            prompt=prompt,
            style=most_common_genre,
            output_dir=output_dir,
            filename=f"compilation_{compilation_name.replace(' ', '_').lower()}.png"
        )

def quick_cover_art(prompt: str, style: str = "modern", output_dir: str = "static/uploads") -> str:
    """
    Quick cover art generation function
    
    Args:
        prompt: Art description
        style: Art style
        output_dir: Output directory
    
    Returns:
        Path to generated cover art
    
    Raises:
        Exception: If generation fails
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI library required for cover art generation")
    
    generator = CoverArtGenerator()
    result = generator.generate_cover_art(prompt, style, output_dir=output_dir)
    
    if result["success"]:
        return result["file_path"]
    else:
        raise Exception(f"Cover art generation failed: {result.get('error', 'Unknown error')}")

def is_cover_art_available() -> bool:
    """Check if cover art generation is available"""
    return OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY') is not None

if __name__ == "__main__":
    # Test cover art generation
    logging.basicConfig(level=logging.INFO)
    
    if is_cover_art_available():
        try:
            generator = CoverArtGenerator()
            result = generator.generate_cover_art(
                prompt="Futuristic music studio with holographic interfaces",
                style="electronic",
                size="1024x1024"
            )
            print(f"Test result: {result}")
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("Cover art generation not available - check OpenAI API key")