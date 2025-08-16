#!/usr/bin/env python3
"""
Audio Effects Processor
Fast local audio effects processing using librosa, scipy, and pydub
"""

import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Check for required libraries
try:
    import librosa
    import soundfile as sf
    from scipy.signal import fftconvolve, iirfilter, lfilter, butter, sosfilt
    from pydub import AudioSegment
    import parselmouth
    AUDIO_LIBS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Audio libraries not fully available: {e}")
    AUDIO_LIBS_AVAILABLE = False

class AudioEffectsProcessor:
    """Fast local audio effects processing"""
    
    def __init__(self, default_sr: int = 44100):
        """
        Initialize audio effects processor
        
        Args:
            default_sr: Default sample rate for processing
        """
        self.default_sr = default_sr
        if not AUDIO_LIBS_AVAILABLE:
            raise ImportError("Required audio libraries not available")
    
    def load_audio(self, file_path: str, sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        Load audio file
        
        Args:
            file_path: Path to audio file
            sr: Target sample rate (uses default if None)
        
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        sr = sr or self.default_sr
        try:
            y, actual_sr = librosa.load(file_path, sr=sr, mono=True)
            return y, actual_sr
        except Exception as e:
            logger.error(f"Failed to load audio {file_path}: {e}")
            raise
    
    def save_audio(self, file_path: str, audio_data: np.ndarray, sr: int) -> bool:
        """
        Save audio to file
        
        Args:
            file_path: Output file path
            audio_data: Audio data array
            sr: Sample rate
        
        Returns:
            True if successful
        """
        try:
            # Ensure output directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Normalize and save
            audio_normalized = np.clip(audio_data, -1.0, 1.0)
            sf.write(file_path, audio_normalized, sr)
            return True
        except Exception as e:
            logger.error(f"Failed to save audio {file_path}: {e}")
            return False
    
    def pitch_shift(self, audio_data: np.ndarray, sr: int, semitones: float) -> np.ndarray:
        """
        Shift pitch by semitones
        
        Args:
            audio_data: Input audio
            sr: Sample rate
            semitones: Pitch shift in semitones (+/- 12)
        
        Returns:
            Pitch-shifted audio
        """
        try:
            return librosa.effects.pitch_shift(audio_data, sr=sr, n_steps=semitones)
        except Exception as e:
            logger.error(f"Pitch shift failed: {e}")
            return audio_data
    
    def time_stretch(self, audio_data: np.ndarray, rate: float) -> np.ndarray:
        """
        Time stretch audio (change speed without pitch)
        
        Args:
            audio_data: Input audio
            rate: Stretch rate (0.5 = half speed, 2.0 = double speed)
        
        Returns:
            Time-stretched audio
        """
        try:
            return librosa.effects.time_stretch(audio_data, rate=rate)
        except Exception as e:
            logger.error(f"Time stretch failed: {e}")
            return audio_data
    
    def simple_eq(self, audio_data: np.ndarray, sr: int, 
                  low_gain_db: float = 0.0, 
                  mid_gain_db: float = 0.0, 
                  high_gain_db: float = 0.0) -> np.ndarray:
        """
        Simple 3-band EQ
        
        Args:
            audio_data: Input audio
            sr: Sample rate
            low_gain_db: Low frequency gain (-12 to +12 dB)
            mid_gain_db: Mid frequency gain (-12 to +12 dB)
            high_gain_db: High frequency gain (-12 to +12 dB)
        
        Returns:
            EQ'd audio
        """
        try:
            audio_out = audio_data.copy()
            
            # Low shelf around 120 Hz
            if abs(low_gain_db) > 0.1:
                sos_low = butter(2, 120, 'low', fs=sr, output='sos')
                low_filtered = sosfilt(sos_low, audio_data)
                gain_linear = 10 ** (low_gain_db / 20)
                audio_out += (gain_linear - 1) * low_filtered
            
            # High shelf around 6 kHz
            if abs(high_gain_db) > 0.1:
                sos_high = butter(2, 6000, 'high', fs=sr, output='sos')
                high_filtered = sosfilt(sos_high, audio_data)
                gain_linear = 10 ** (high_gain_db / 20)
                audio_out += (gain_linear - 1) * high_filtered
            
            # Mid boost/cut (simple gain)
            if abs(mid_gain_db) > 0.1:
                mid_gain_linear = 10 ** (mid_gain_db / 20)
                audio_out *= mid_gain_linear
            
            return np.clip(audio_out, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"EQ processing failed: {e}")
            return audio_data
    
    def simple_reverb(self, audio_data: np.ndarray, sr: int, 
                     decay: float = 0.3, 
                     delay_ms: float = 80.0) -> np.ndarray:
        """
        Simple reverb effect using multiple delays
        
        Args:
            audio_data: Input audio
            sr: Sample rate
            decay: Decay factor (0.0 to 1.0)
            delay_ms: Initial delay in milliseconds
        
        Returns:
            Reverb-processed audio
        """
        try:
            delay_samples = int(sr * delay_ms / 1000.0)
            
            # Create simple reverb impulse response
            ir_length = delay_samples * 4
            impulse_response = np.zeros(ir_length)
            
            # Multiple delays with decreasing amplitude
            impulse_response[0] = 1.0  # Direct signal
            impulse_response[delay_samples] = decay
            impulse_response[delay_samples * 2] = decay ** 2
            impulse_response[delay_samples * 3] = decay ** 3
            
            # Convolve with input
            wet_signal = fftconvolve(audio_data, impulse_response, mode='same')
            
            # Mix dry and wet (70% dry, 30% wet)
            mixed = 0.7 * audio_data + 0.3 * wet_signal
            
            return np.clip(mixed, -1.0, 1.0)
            
        except Exception as e:
            logger.error(f"Reverb processing failed: {e}")
            return audio_data
    
    def vocal_pitch_correction(self, audio_data: np.ndarray, sr: int, 
                              target_pitch: Optional[float] = None) -> np.ndarray:
        """
        Basic vocal pitch correction using Parselmouth
        
        Args:
            audio_data: Input vocal audio
            sr: Sample rate
            target_pitch: Target pitch in Hz (auto-detect if None)
        
        Returns:
            Pitch-corrected audio
        """
        try:
            # Convert to Parselmouth sound object
            sound = parselmouth.Sound(audio_data, sampling_frequency=sr)
            
            # Get pitch
            pitch = sound.to_pitch()
            
            if target_pitch is None:
                # Auto-correct to nearest semitone
                pitch_values = pitch.selected_array['frequency']
                valid_pitches = pitch_values[pitch_values > 0]
                
                if len(valid_pitches) > 0:
                    mean_pitch = np.mean(valid_pitches)
                    # Round to nearest semitone
                    semitone_ratio = 2 ** (1/12)
                    target_pitch = 440 * (semitone_ratio ** round(12 * np.log2(mean_pitch / 440)))
                else:
                    return audio_data  # No pitch detected
            
            # Apply pitch shift to match target
            if target_pitch and len(valid_pitches) > 0:
                current_pitch = np.mean(valid_pitches)
                shift_ratio = target_pitch / current_pitch
                shift_semitones = 12 * np.log2(shift_ratio)
                
                return self.pitch_shift(audio_data, sr, shift_semitones)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Vocal pitch correction failed: {e}")
            return audio_data
    
    def apply_effects_chain(self, input_path: str, output_path: str, 
                           effects_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a chain of effects to an audio file
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            effects_config: Configuration for effects to apply
        
        Returns:
            Result dictionary with success status
        """
        try:
            # Load audio
            audio, sr = self.load_audio(input_path)
            original_audio = audio.copy()
            
            effects_applied = []
            
            # Apply effects in order
            if 'pitch_shift' in effects_config:
                semitones = effects_config['pitch_shift']
                audio = self.pitch_shift(audio, sr, semitones)
                effects_applied.append(f"pitch_shift: {semitones} semitones")
            
            if 'time_stretch' in effects_config:
                rate = effects_config['time_stretch']
                audio = self.time_stretch(audio, rate)
                effects_applied.append(f"time_stretch: {rate}x")
            
            if 'eq' in effects_config:
                eq_config = effects_config['eq']
                audio = self.simple_eq(
                    audio, sr,
                    eq_config.get('low', 0),
                    eq_config.get('mid', 0),
                    eq_config.get('high', 0)
                )
                effects_applied.append(f"eq: L{eq_config.get('low', 0)}dB M{eq_config.get('mid', 0)}dB H{eq_config.get('high', 0)}dB")
            
            if 'reverb' in effects_config:
                reverb_config = effects_config['reverb']
                audio = self.simple_reverb(
                    audio, sr,
                    reverb_config.get('decay', 0.3),
                    reverb_config.get('delay_ms', 80)
                )
                effects_applied.append(f"reverb: decay {reverb_config.get('decay', 0.3)}")
            
            if 'vocal_correction' in effects_config and effects_config['vocal_correction']:
                audio = self.vocal_pitch_correction(audio, sr)
                effects_applied.append("vocal_pitch_correction")
            
            # Save processed audio
            if self.save_audio(output_path, audio, sr):
                return {
                    "success": True,
                    "input_path": input_path,
                    "output_path": output_path,
                    "effects_applied": effects_applied,
                    "sample_rate": sr,
                    "duration_seconds": len(audio) / sr
                }
            else:
                return {"success": False, "error": "Failed to save processed audio"}
            
        except Exception as e:
            logger.error(f"Effects chain processing failed: {e}")
            return {"success": False, "error": str(e)}

def mix_tracks(vocal_path: str, instrumental_path: str, output_path: str,
               vocal_gain_db: float = 0.0, instrumental_gain_db: float = -3.0) -> Dict[str, Any]:
    """
    Mix vocal and instrumental tracks using pydub
    
    Args:
        vocal_path: Path to vocal track
        instrumental_path: Path to instrumental track
        output_path: Output mixed track path
        vocal_gain_db: Vocal gain in dB
        instrumental_gain_db: Instrumental gain in dB
    
    Returns:
        Result dictionary
    """
    try:
        # Load tracks
        vocals = AudioSegment.from_file(vocal_path)
        instrumental = AudioSegment.from_file(instrumental_path)
        
        # Apply gains
        vocals = vocals.apply_gain(vocal_gain_db)
        instrumental = instrumental.apply_gain(instrumental_gain_db)
        
        # Mix tracks (overlay)
        mixed = vocals.overlay(instrumental)
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Export mixed track
        mixed.export(output_path, format="wav")
        
        return {
            "success": True,
            "output_path": output_path,
            "vocal_gain_db": vocal_gain_db,
            "instrumental_gain_db": instrumental_gain_db,
            "duration_ms": len(mixed)
        }
        
    except Exception as e:
        logger.error(f"Track mixing failed: {e}")
        return {"success": False, "error": str(e)}

def is_audio_processing_available() -> bool:
    """Check if audio processing is available"""
    return AUDIO_LIBS_AVAILABLE

if __name__ == "__main__":
    # Test audio effects
    logging.basicConfig(level=logging.INFO)
    
    if AUDIO_LIBS_AVAILABLE:
        processor = AudioEffectsProcessor()
        print("✅ Audio effects processor ready")
        
        # Test loading a sine wave
        import numpy as np
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 44100))
        pitched = processor.pitch_shift(test_audio, 44100, 5)
        print(f"✅ Pitch shift test: {len(pitched)} samples")
    else:
        print("❌ Audio libraries not available")