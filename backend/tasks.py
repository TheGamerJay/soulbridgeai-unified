# ============================
# 📁 backend/tasks.py
# Background tasks for RQ workers
# ============================
import logging
from studio.diffsinger_engine import DiffSingerEngine
from studio.effects import apply_effects
from studio.mixer import mix_tracks
from studio.cover_art import generate_art

logger = logging.getLogger("tasks")

def task_generate_vocals(lyrics: str, midi_path: str | None, voice: str, bpm: int):
    """Background task for vocal generation (can be slow)"""
    logger.info(f"Starting vocal generation task: voice={voice}, bpm={bpm}")
    try:
        engine = DiffSingerEngine(voice_name=voice)
        result = engine.generate_vocals(lyrics_text=lyrics, midi_path=midi_path, bpm=bpm)
        logger.info(f"Vocal generation completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Vocal generation failed: {e}")
        raise

def task_apply_fx(wav_path: str, pitch_semitones: int, reverb_amount: float):
    """Background task for audio effects processing"""
    logger.info(f"Starting effects task: {wav_path}")
    try:
        result = apply_effects(wav_path, pitch_semitones=pitch_semitones, reverb_amount=reverb_amount)
        logger.info(f"Effects processing completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Effects processing failed: {e}")
        raise

def task_mix_tracks(vocals_wav: str, bgm_wav: str, vocal_db: float, bgm_db: float):
    """Background task for track mixing"""
    logger.info(f"Starting mix task: vocals={vocals_wav}, bgm={bgm_wav}")
    try:
        result = mix_tracks(vocals_wav, bgm_wav, vocal_db=vocal_db, bgm_db=bgm_db)
        logger.info(f"Track mixing completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Track mixing failed: {e}")
        raise

def task_generate_art(prompt: str, size: str):
    """Background task for cover art generation"""
    logger.info(f"Starting cover art task: {prompt[:50]}...")
    try:
        result = generate_art(prompt, size=size)
        logger.info(f"Cover art generation completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cover art generation failed: {e}")
        raise