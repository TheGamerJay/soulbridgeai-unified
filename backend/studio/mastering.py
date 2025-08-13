# ============================================
# 📁 backend/studio/mastering.py
# Professional audio mastering tools
# ============================================
import os
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy.signal import butter, filtfilt
from pydub import AudioSegment
import logging

from config import PATHS
from .utils import new_id

logger = logging.getLogger(__name__)

def _read_audio(path):
    """Read audio file and ensure float32 format"""
    y, sr = sf.read(path, always_2d=False)
    if y.dtype != np.float32:
        y = y.astype(np.float32, copy=False)
    return y, sr

def _write_audio(path, y, sr):
    """Write audio file with proper directory creation"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, y, sr, subtype='PCM_16')

def _db_to_linear(db):
    """Convert decibels to linear scale"""
    return 10.0 ** (db / 20.0)

def _soft_limiter(y, ceiling_db=-1.0):
    """Soft limiter using tanh to avoid harsh clipping"""
    peak = np.max(np.abs(y)) + 1e-9
    y = np.tanh(y / max(peak, 1e-6))  # Gentle compression
    
    # Apply ceiling
    ceiling_linear = _db_to_linear(ceiling_db)
    current_peak = np.max(np.abs(y)) + 1e-9
    if current_peak > ceiling_linear:
        y *= (ceiling_linear / current_peak)
    
    return y

def _create_filter(filter_type, cutoff_hz, sr, order=4):
    """Create Butterworth filter coefficients"""
    nyquist = 0.5 * sr
    normalized_cutoff = np.clip(cutoff_hz / nyquist, 1e-6, 0.999999)
    
    if filter_type == "highpass":
        b, a = butter(order, normalized_cutoff, btype='high', analog=False)
    elif filter_type == "lowpass":
        b, a = butter(order, normalized_cutoff, btype='low', analog=False)
    else:
        raise ValueError("filter_type must be 'highpass' or 'lowpass'")
    
    return b, a

def _apply_filter(y, b, a):
    """Apply filter to audio (handles mono/stereo)"""
    if y.ndim == 1:
        return filtfilt(b, a, y)
    else:
        # Handle stereo/multi-channel
        filtered_channels = []
        for ch in range(y.shape[-1]):
            filtered_channels.append(filtfilt(b, a, y[:, ch]))
        return np.stack(filtered_channels, axis=-1)

def master_track(
    wav_path: str,
    target_lufs: float = -14.0,
    ceiling_db: float = -1.0,
    highpass_hz: float = 20.0,
    lowpass_hz: float = None,
):
    """
    Professional audio mastering:
    1) High-pass and low-pass filtering
    2) Loudness normalization to target LUFS
    3) Soft limiting with ceiling
    
    Returns: output WAV path
    """
    logger.info(f"Mastering track: {wav_path}")
    
    try:
        y, sr = _read_audio(wav_path)
        
        # Apply filters
        if highpass_hz and highpass_hz > 0:
            logger.info(f"Applying high-pass filter: {highpass_hz}Hz")
            b, a = _create_filter("highpass", highpass_hz, sr, order=4)
            y = _apply_filter(y, b, a)
        
        if lowpass_hz and lowpass_hz > 0:
            logger.info(f"Applying low-pass filter: {lowpass_hz}Hz")
            b, a = _create_filter("lowpass", lowpass_hz, sr, order=6)
            y = _apply_filter(y, b, a)
        
        # Loudness normalization using EBU R128 standard
        logger.info(f"Normalizing to {target_lufs} LUFS")
        meter = pyln.Meter(sr)
        
        # Measure current loudness (convert to mono for measurement)
        mono_signal = y if y.ndim == 1 else y.mean(axis=1)
        current_loudness = meter.integrated_loudness(mono_signal)
        
        # Calculate gain needed
        gain_db = target_lufs - current_loudness
        gain_linear = _db_to_linear(gain_db)
        y = y * gain_linear
        
        logger.info(f"Applied {gain_db:.2f}dB gain (was {current_loudness:.2f} LUFS)")
        
        # Apply soft limiter
        y = _soft_limiter(y, ceiling_db=ceiling_db)
        
        # Write output
        output_path = os.path.join(PATHS["audio"], f"{new_id()}_mastered.wav")
        _write_audio(output_path, y, sr)
        
        logger.info(f"Mastered track saved: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Mastering failed: {e}")
        raise

def make_seamless_loop(
    wav_path: str,
    loop_seconds: int = 8,
    crossfade_ms: int = 120,
):
    """
    Create a seamless loop by crossfading the end into the beginning
    
    Args:
        wav_path: Source audio file
        loop_seconds: Target loop length in seconds
        crossfade_ms: Crossfade duration in milliseconds
    
    Returns: output WAV path
    """
    logger.info(f"Creating {loop_seconds}s seamless loop with {crossfade_ms}ms crossfade")
    
    try:
        # Use pydub for robust timing across sample rates
        segment = AudioSegment.from_file(wav_path)
        
        # Ensure we have enough audio
        target_length_ms = loop_seconds * 1000
        min_length = target_length_ms + crossfade_ms + 100  # Add safety margin
        
        if len(segment) < min_length:
            # Tile the audio to reach desired length
            repetitions = int(np.ceil(min_length / len(segment))) + 1
            segment = sum([segment] * repetitions)
        
        # Extract the base loop
        base_loop = segment[:target_length_ms]
        
        # Create crossfade
        head = base_loop[:crossfade_ms]
        body = base_loop[:-crossfade_ms]
        
        # Crossfade the head onto the end of the body
        looped_segment = body.append(head, crossfade=crossfade_ms)
        
        # Export
        output_path = os.path.join(PATHS["audio"], f"{new_id()}_loop.wav")
        looped_segment.export(output_path, format="wav")
        
        logger.info(f"Seamless loop created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Loop creation failed: {e}")
        raise