# ===================================
# 📁 FILE: backend/studio/auto_midi.py
# ===================================
import os
from .utils import new_id

try:
    import pretty_midi
    PRETTY_MIDI_AVAILABLE = True
except ImportError:
    PRETTY_MIDI_AVAILABLE = False

NOTE_MAP = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}

def chord_to_pitches(name, octave=4):
    root = ''.join([c for c in name if c.isalpha() or c in ['#','b']])
    kind = name.replace(root, "").lower()
    base = NOTE_MAP.get(root, 0)
    o = 12*octave
    triad = [base, base+4, base+7]  # maj triad
    if "m" in kind and "maj" not in kind:
        triad = [base, base+3, base+7]
    if "dim" in kind:
        triad = [base, base+3, base+6]
    if "aug" in kind:
        triad = [base, base+4, base+8]
    if "7" in kind and "maj7" not in kind:
        triad.append(base+10)
    if "maj7" in kind:
        triad.append(base+11)
    return [p+o for p in triad]

def generate_midi(chords: str, bpm=88, bars=8, style="arp", out_dir=None):
    """
    chords: "Cmaj7 | Am | F | G"
    """
    if not PRETTY_MIDI_AVAILABLE:
        raise ImportError("pretty_midi is required for MIDI generation")
    
    if out_dir is None:
        from config import PATHS
        out_dir = PATHS["midi"]
    
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0)  # piano
    bar_dur = 60.0 / bpm * 4
    t = 0.0
    seq = [c.strip() for c in chords.split("|")]
    while len(seq) < bars:
        seq += seq
    seq = seq[:bars]
    for c in seq:
        pitches = chord_to_pitches(c)
        if style == "block":
            for p in pitches:
                inst.notes.append(pretty_midi.Note(velocity=90, pitch=60 + (p - 60), start=t, end=t+bar_dur))
        else:  # arp
            step = bar_dur / max(1, len(pitches))
            for i, p in enumerate(pitches):
                inst.notes.append(pretty_midi.Note(velocity=90, pitch=60 + (p - 60), start=t + i*step, end=t + (i+1)*step))
        t += bar_dur

    pm.instruments.append(inst)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{new_id()}.mid")
    pm.write(path)
    return path