# ==========================================
# 📁 FILE: backend/studio/diffsinger_engine.py
# ==========================================
"""
Wrapper that tries:
1) Python import: from diffsinger import Synth  (example API)
2) CLI fallback: python tools/svs_infer.py --model ... --midi ... --lyrics ...
Adjust commands to your local DiffSinger fork.
"""
import os, subprocess, shutil
from .utils import new_id
from .auto_midi import generate_midi

class DiffSingerEngine:
    def __init__(self, voice_name="default"):
        self.voice_name = voice_name
        
        # Try to get PATHS from config
        try:
            from config import PATHS
            self.model_dir = os.path.join(PATHS["diffsinger_models"], voice_name)
        except ImportError:
            # Fallback if config not available
            self.model_dir = os.path.join("models", "diffsinger", voice_name)
        
        if not os.path.isdir(self.model_dir):
            # Create placeholder directory
            os.makedirs(self.model_dir, exist_ok=True)
            print(f"Warning: DiffSinger model directory created at {self.model_dir}")
        
        self.python_api_ok = False
        try:
            # Replace with your actual Python API if available
            import diffsinger  # noqa: F401
            self.python_api_ok = True
        except Exception:
            self.python_api_ok = False

    def _cli_infer(self, lyrics_path, midi_path, out_wav):
        """
        Example CLI — replace with your actual entrypoint.
        """
        infer_script = os.path.join(self.model_dir, "svs_infer.py")  # put your script here
        if not os.path.isfile(infer_script):
            # Create a mock output for development
            print(f"Warning: DiffSinger infer script not found at {infer_script}")
            print("Creating mock vocal output for development...")
            
            # Create a simple mock WAV file (silence)
            try:
                import soundfile as sf
                import numpy as np
                duration = 10.0  # 10 seconds
                sample_rate = 22050
                silence = np.zeros(int(duration * sample_rate))
                sf.write(out_wav, silence, sample_rate)
                return out_wav
            except ImportError:
                # Even simpler fallback - just create an empty file
                os.makedirs(os.path.dirname(out_wav), exist_ok=True)
                with open(out_wav, 'wb') as f:
                    f.write(b'')  # Empty file as placeholder
                return out_wav

        cmd = [
            "python", infer_script,
            "--model_dir", self.model_dir,
            "--lyrics", lyrics_path,
            "--midi", midi_path,
            "--out", out_wav
        ]
        subprocess.check_call(cmd)
        return out_wav

    def generate_vocals(self, lyrics_text: str, midi_path: str | None = None, bpm=88):
        # Prepare inputs
        try:
            from config import PATHS
            tmp_dir = PATHS["tmp"]
            audio_dir = PATHS["audio"]
        except ImportError:
            tmp_dir = "tmp"
            audio_dir = "audio"
            os.makedirs(tmp_dir, exist_ok=True)
            os.makedirs(audio_dir, exist_ok=True)
        
        lyrics_file = os.path.join(tmp_dir, f"{new_id()}_lyrics.txt")
        with open(lyrics_file, "w", encoding="utf-8") as f:
            f.write(lyrics_text.strip())

        if not midi_path:
            midi_path = generate_midi("Cmaj7|Am|F|G", bpm=bpm, bars=8, style="arp")

        out_wav = os.path.join(audio_dir, f"{new_id()}_vocals.wav")

        if self.python_api_ok:
            # Pseudocode: replace with your actual Python API call
            # from diffsinger import Synth
            # synth = Synth(model_dir=self.model_dir)
            # synth.render(lyrics=lyrics_file, midi=midi_path, out=out_wav)
            return self._cli_infer(lyrics_file, midi_path, out_wav)  # fallback to CLI in this stub
        else:
            return self._cli_infer(lyrics_file, midi_path, out_wav)