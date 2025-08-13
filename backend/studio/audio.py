# ===============================
# 📁 FILE: backend/studio/audio.py
# ===============================
import os, uuid, numpy as np
from .utils import new_id

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from pydub import AudioSegment
    from config import PATHS, FFMPEG_PATH
    # pydub needs ffmpeg
    AudioSegment.converter = FFMPEG_PATH
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

def load_wav(path):
    if SOUNDFILE_AVAILABLE:
        y, sr = sf.read(path, always_2d=False)
        return y, sr
    else:
        # Fallback using basic audio loading
        raise ImportError("soundfile is required for audio loading")

def save_wav(path, y, sr):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if SOUNDFILE_AVAILABLE:
        sf.write(path, y, sr)
    else:
        raise ImportError("soundfile is required for audio saving")

def normalize_peak(y, peak=0.98):
    if np.max(np.abs(y)) < 1e-9:
        return y
    return y * (peak / np.max(np.abs(y)))

def wav_to_mp3(wav_path, out_dir=None):
    if not PYDUB_AVAILABLE:
        raise ImportError("pydub is required for MP3 conversion")
    
    if out_dir is None:
        from config import PATHS
        out_dir = PATHS["audio"]
    
    seg = AudioSegment.from_file(wav_path)
    out = os.path.join(out_dir, f"{new_id()}.mp3")
    seg.export(out, format="mp3")
    return out

def mix_two_files(vocals_path, bgm_path, vocal_db=-3.0, bgm_db=-8.0, out_dir=None):
    if not PYDUB_AVAILABLE:
        raise ImportError("pydub is required for audio mixing")
    
    if out_dir is None:
        from config import PATHS
        out_dir = PATHS["audio"]
    
    v = AudioSegment.from_file(vocals_path) + vocal_db
    b = AudioSegment.from_file(bgm_path) + bgm_db
    mixed = b.overlay(v)
    out = os.path.join(out_dir, f"{new_id()}.wav")
    mixed.export(out, format="wav")
    return out