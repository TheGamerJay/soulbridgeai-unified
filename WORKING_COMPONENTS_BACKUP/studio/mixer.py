# ===================================
# 📁 FILE: backend/studio/mixer.py
# ===================================
from .audio import mix_two_files

def mix_tracks(vocals_wav, bgm_wav, vocal_db=-3.0, bgm_db=-8.0):
    return mix_two_files(vocals_wav, bgm_wav, vocal_db=vocal_db, bgm_db=bgm_db)