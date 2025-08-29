# =================================
# 📁 FILE: backend/studio/effects.py
# =================================
from .utils import new_id
import os

try:
    from pydub import AudioSegment
    from config import PATHS
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

def apply_effects(wav_path, pitch_semitones=0, reverb_amount=0.0, eq=None):
    """
    Simple placeholder FX:
    - pitch via speed change (approx)
    - mild 'reverb' via very short echo
    - no-op EQ stub you can expand
    """
    if not PYDUB_AVAILABLE:
        raise ImportError("pydub is required for audio effects")
    
    seg = AudioSegment.from_file(wav_path)

    # pseudo pitch (speed) — replace with DSP lib if needed
    if pitch_semitones != 0:
        factor = 2 ** (pitch_semitones / 12.0)
        seg = seg._spawn(seg.raw_data, overrides={
            "frame_rate": int(seg.frame_rate * factor)
        }).set_frame_rate(seg.frame_rate)

    if reverb_amount > 0:
        echo = seg - (18 + int(12 * reverb_amount))
        seg = seg.overlay(echo, delay=80)

    from config import PATHS
    out = os.path.join(PATHS["audio"], f"{new_id()}.wav")
    seg.export(out, format="wav")
    return out