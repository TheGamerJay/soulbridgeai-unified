# =========================================
# 📁 FILE: backend/studio/inspiration_writer.py
# =========================================
import os
from .utils import new_id

WRITER_SYSTEM_PROMPT = (
    "You are InspirationWriter, a concise lyric ghostwriter. "
    "Write singable lines (8–12 syllables), natural rhyme, vivid images."
)

def write_lyrics(theme: str, mood: str="emotional", lang: str="en", syllables: int=10):
    try:
        from config import OPENAI_API_KEY
    except ImportError:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    if not OPENAI_API_KEY:
        # lightweight local fallback
        return f"[{lang}] ({mood}) Theme: {theme}\n" \
               "Verse 1:\nFading streetlights hum the truth I hide...\n" \
               "Pre:\nIf I break tonight, will the dawn still rise?\n" \
               "Hook:\nHold me like the last spark in the rain..."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"Theme: {theme}\nMood: {mood}\nLanguage: {lang}\nTarget syllables/line: {syllables}\nFormat a short Verse + Hook."
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":WRITER_SYSTEM_PROMPT},
                      {"role":"user","content":prompt}],
            temperature=0.8
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        # Fallback if OpenAI fails
        return f"[{lang}] ({mood}) Theme: {theme}\n" \
               "Verse 1:\nIn the silence of the night I find\n" \
               "Echoes of a love I left behind\n" \
               "Pre:\nWill tomorrow bring me peace at last?\n" \
               "Hook:\nDancing with the shadows of my past..."