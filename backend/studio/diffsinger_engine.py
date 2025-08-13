# 📁 backend/studio/diffsinger_engine.py
import os, subprocess
from config import PATHS
from .utils import new_id
from .auto_midi import generate_midi

class DiffSingerEngine:
    """
    Runs DiffSinger via CLI. It will try two flag styles automatically:

    1) REAL (your described structure):
       python models/diffsinger/{voice}/svs_infer.py \
         --model_dir <model_dir> --lyrics <lyrics.txt> --midi <music.mid> --out <output.wav>

    2) PLACEHOLDER (your current stub):
       python models/diffsinger/{voice}/svs_infer.py \
         --text <lyrics.txt> --score <music.mid> --out <output.wav> --voice <voice> --bpm <bpm>

    If the first command fails (non-zero exit), it falls back to the second.
    """
    def __init__(self, voice_name: str = "default"):
        self.voice_name = voice_name
        self.model_dir = os.path.join(PATHS["diffsinger_models"], voice_name)
        if not os.path.isdir(self.model_dir):
            raise FileNotFoundError(f"DiffSinger model folder not found: {self.model_dir}")
        self.infer_script = os.path.join(self.model_dir, "svs_infer.py")
        if not os.path.isfile(self.infer_script):
            raise FileNotFoundError(f"Infer script not found: {self.infer_script}")

    def _run(self, cmd: list[str]) -> None:
        # Raises CalledProcessError if command fails (we use that to trigger fallback)
        subprocess.check_call(cmd)

    def _cli_infer(self, lyrics_path: str, midi_path: str, out_wav: str, bpm: int) -> str:
        # --- 1) REAL flags (your "To Use Your Real DiffSinger" structure)
        real_cmd = [
            "python", self.infer_script,
            "--model_dir", self.model_dir,
            "--lyrics", lyrics_path,
            "--midi", midi_path,
            "--out", out_wav,
        ]

        # --- 2) PLACEHOLDER flags (your current stub)
        placeholder_cmd = [
            "python", self.infer_script,
            "--text", lyrics_path,
            "--score", midi_path,
            "--out", out_wav,
            "--voice", self.voice_name,
            "--bpm", str(bpm),
        ]

        try:
            self._run(real_cmd)
        except subprocess.CalledProcessError:
            # Try the placeholder signature
            self._run(placeholder_cmd)

        return out_wav

    def generate_vocals(self, lyrics_text: str, midi_path: str | None = None, bpm: int = 120) -> str:
        # Ensure tmp/audio dirs exist
        os.makedirs(PATHS["tmp"], exist_ok=True)
        os.makedirs(PATHS["audio"], exist_ok=True)

        # Write lyrics file
        lyrics_file = os.path.join(PATHS["tmp"], f"{new_id()}_lyrics.txt")
        with open(lyrics_file, "w", encoding="utf-8") as f:
            f.write(lyrics_text.strip())

        # Ensure we have a MIDI (auto-generate if missing)
        if not midi_path:
            midi_path = generate_midi("Cmaj7|Am|F|G", bpm=bpm, bars=8, style="arp")

        # Output wav
        out_wav = os.path.join(PATHS["audio"], f"{new_id()}_vocals.wav")

        # Run CLI (auto-tries both flag styles)
        return self._cli_infer(lyrics_file, midi_path, out_wav, bpm=bpm)