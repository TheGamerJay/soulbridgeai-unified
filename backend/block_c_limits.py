# =========================================
# BLOCK C – Song, Lyrics & Beat Limits
# =========================================

# Configurable limits
MAX_SONG_LENGTH_SECONDS = 270      # 4 min 30 sec
MAX_LYRICS_CHARS = 3500
MAX_BEAT_DESC_CHARS = 3500

# This block just defines constants. You already enforce:
# - Length cap in audio_tools.song_cap()
# - Prompt length checks in audio routes
# If you later add a "generate new song" endpoint with lyrics input,
# apply MAX_LYRICS_CHARS before deducting credits.