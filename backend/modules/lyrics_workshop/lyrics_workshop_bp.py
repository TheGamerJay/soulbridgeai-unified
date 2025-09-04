# -*- coding: utf-8 -*-
"""
Lyrics Workshop - Complete CPU Beat Studio Backend
Full multi-track MIDI generator with comprehensive analysis
"""

import re
import io
import base64
import random
from flask import Blueprint, render_template, request, jsonify
from mido import MidiFile, MidiTrack, Message

lyrics_workshop_bp = Blueprint("lyrics_workshop", __name__, url_prefix="/api/beat")

# ============================================================================
# MIDI Generation Constants
# ============================================================================

# Musical constants
KEYS = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
}

SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10]
}

# Drum MIDI note mappings (General MIDI)
DRUM_NOTES = {
    'kick': 36,
    'snare': 38,
    'hihat': 42,
    'openhat': 46,
    'crash': 49,
    'ride': 51
}

# Genre patterns (16th notes per bar)
GENRE_PATTERNS = {
    'trap': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0],
        'openhat': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    },
    'drill': {
        'kick': [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1],
        'openhat': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    'reggaeton': {
        'kick': [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'openhat': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    },
    'bachata-trap': {
        'kick': [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        'snare': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        'hihat': [1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
        'openhat': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
    },
    'boom-bap': {
        'kick': [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'openhat': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    },
    'rnb': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'openhat': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    }
}

# Chord progressions by scale
PROGRESSIONS = {
    'minor': [0, 5, 3, 4],  # i-vi-IV-v
    'major': [0, 3, 5, 4],  # I-IV-vi-V  
    'dorian': [0, 2, 5, 0], # i-iii-VI-i
    'mixolydian': [0, 6, 3, 0] # I-VII-IV-I
}

# ============================================================================
# Helper Functions
# ============================================================================

def count_syllables(word):
    """Count syllables in a word"""
    word = word.lower()
    if len(word) <= 3:
        return 1
    vowels = 'aeiouy'
    syllables = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllables += 1
        prev_was_vowel = is_vowel
    
    if word.endswith('e') and syllables > 1:
        syllables -= 1
    
    return max(syllables, 1)

def detect_emotion_and_bpm(lyrics):
    """Detect emotion and suggest BPM from lyrics"""
    lyrics_lower = lyrics.lower()
    
    # Emotion keywords
    emotions = {
        'energetic': ['party', 'dance', 'crazy', 'wild', 'hype', 'turn up', 'lit'],
        'sad': ['lonely', 'cry', 'pain', 'hurt', 'broken', 'tears', 'miss'],
        'romantic': ['love', 'baby', 'heart', 'kiss', 'forever', 'together'],
        'aggressive': ['fight', 'rage', 'angry', 'mad', 'hate', 'war'],
        'chill': ['relax', 'smooth', 'calm', 'peaceful', 'easy', 'vibe']
    }
    
    emotion_scores = {}
    for emotion, keywords in emotions.items():
        score = sum(lyrics_lower.count(keyword) for keyword in keywords)
        emotion_scores[emotion] = score
    
    dominant_emotion = max(emotion_scores, key=emotion_scores.get) if max(emotion_scores.values()) > 0 else 'neutral'
    
    # BPM suggestions based on emotion
    bpm_map = {
        'energetic': 140,
        'sad': 80,
        'romantic': 90,
        'aggressive': 150,
        'chill': 100,
        'neutral': 120
    }
    
    return dominant_emotion, bpm_map.get(dominant_emotion, 120)

def find_sections(lyrics):
    """Find verse/chorus sections in lyrics"""
    lines = lyrics.replace('\r', '').split('\n')
    sections = []
    current_section = {'type': 'verse', 'lines': [], 'start_line': 0}
    
    verse_count = 1
    chorus_count = 1
    
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        
        # Section markers
        if any(marker in line_clean for marker in ['[verse', '[chorus', '[bridge', '[hook']):
            if current_section['lines']:
                sections.append(current_section)
            
            if 'verse' in line_clean:
                current_section = {'type': f'verse_{verse_count}', 'lines': [], 'start_line': i}
                verse_count += 1
            elif 'chorus' in line_clean or 'hook' in line_clean:
                current_section = {'type': f'chorus_{chorus_count}', 'lines': [], 'start_line': i}
                chorus_count += 1
            else:
                current_section = {'type': 'bridge', 'lines': [], 'start_line': i}
        else:
            current_section['lines'].append(line)
    
    if current_section['lines']:
        sections.append(current_section)
    
    return sections

def progression_degrees(scale_mode):
    """Get chord progression for scale"""
    return PROGRESSIONS.get(scale_mode, PROGRESSIONS['minor'])

def chord_from_degree(root_midi, scale_mode, degree):
    """Generate chord from scale degree"""
    scale_intervals = SCALES[scale_mode]
    root = scale_intervals[degree % len(scale_intervals)]
    third = scale_intervals[(degree + 2) % len(scale_intervals)]
    fifth = scale_intervals[(degree + 4) % len(scale_intervals)]
    
    return [root_midi + root, root_midi + third, root_midi + fifth]

def write_full_midi(bpm, genre, key, scale, bars, include):
    """Generate complete multi-track MIDI file"""
    mid = MidiFile(ticks_per_beat=480)
    
    # Tempo track
    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_value = int(60000000 / bpm)  # Microseconds per beat
    tempo_track.append(Message('set_tempo', tempo=tempo_value, time=0))
    
    pattern = GENRE_PATTERNS.get(genre, GENRE_PATTERNS['trap'])
    sixteenth_ticks = mid.ticks_per_beat // 4
    
    # Drums track
    if include.get('drums', True):
        drums = MidiTrack()
        mid.tracks.append(drums)
        drums.append(Message('program_change', program=0, channel=9, time=0))  # Drum kit
        
        for bar in range(bars):
            for step in range(16):  # 16th notes
                time_offset = 0 if step == 0 and bar == 0 else sixteenth_ticks
                
                # Kick
                if pattern['kick'][step]:
                    velocity = random.randint(90, 110)
                    drums.append(Message('note_on', note=DRUM_NOTES['kick'], velocity=velocity, time=time_offset, channel=9))
                    drums.append(Message('note_off', note=DRUM_NOTES['kick'], velocity=64, time=sixteenth_ticks//2, channel=9))
                    time_offset = 0
                
                # Snare
                if pattern['snare'][step]:
                    velocity = random.randint(80, 100)
                    drums.append(Message('note_on', note=DRUM_NOTES['snare'], velocity=velocity, time=time_offset, channel=9))
                    drums.append(Message('note_off', note=DRUM_NOTES['snare'], velocity=64, time=sixteenth_ticks//2, channel=9))
                    time_offset = 0
                
                # Hi-hat
                if pattern['hihat'][step]:
                    velocity = random.randint(60, 80)
                    drums.append(Message('note_on', note=DRUM_NOTES['hihat'], velocity=velocity, time=time_offset, channel=9))
                    drums.append(Message('note_off', note=DRUM_NOTES['hihat'], velocity=64, time=sixteenth_ticks//4, channel=9))
                    time_offset = 0
                
                # Open hat
                if pattern['openhat'][step]:
                    velocity = random.randint(70, 90)
                    drums.append(Message('note_on', note=DRUM_NOTES['openhat'], velocity=velocity, time=time_offset, channel=9))
                    drums.append(Message('note_off', note=DRUM_NOTES['openhat'], velocity=64, time=sixteenth_ticks//2, channel=9))
                    time_offset = 0
    
    # Chord track
    if include.get('chords', True):
        chords = MidiTrack()
        mid.tracks.append(chords)
        chords.append(Message('program_change', program=0, channel=0, time=0))  # Piano
        
        root = 48 + KEYS[key]  # Middle C octave for chords
        degrees = progression_degrees(scale)
        
        for bar in range(bars):
            chord_degree = degrees[bar % len(degrees)]
            triad = chord_from_degree(root, scale, chord_degree)
            
            # Chord on
            for i, note in enumerate(triad):
                time_offset = 0 if i == 0 else 0
                chords.append(Message('note_on', note=note, velocity=72, time=time_offset, channel=0))
            
            # Chord off (full bar duration)
            for i, note in enumerate(triad):
                time_offset = mid.ticks_per_beat * 4 if i == 0 else 0
                chords.append(Message('note_off', note=note, velocity=64, time=time_offset, channel=0))
    
    # Bass track
    if include.get('bass', True):
        bass = MidiTrack()
        mid.tracks.append(bass)
        bass.append(Message('program_change', program=33, channel=1, time=0))  # Electric bass
        
        root = 36 + KEYS[key]  # Bass octave
        degrees = progression_degrees(scale)
        
        for bar in range(bars):
            chord_degree = degrees[bar % len(degrees)]
            bass_note = chord_from_degree(root, scale, chord_degree)[0]  # Root note only
            
            bass.append(Message('note_on', note=bass_note, velocity=100, time=0, channel=1))
            bass.append(Message('note_off', note=bass_note, velocity=64, time=mid.ticks_per_beat*4, channel=1))
    
    # Arpeggiator track
    if include.get('arp', False):
        arp = MidiTrack()
        mid.tracks.append(arp)
        arp.append(Message('program_change', program=80, channel=2, time=0))  # Lead synth
        
        root = 60 + KEYS[key]  # Higher octave for arp
        degrees = progression_degrees(scale)
        
        for bar in range(bars):
            chord_degree = degrees[bar % len(degrees)]
            triad = [n + 12 for n in chord_from_degree(root, scale, chord_degree)]  # Octave up
            arp_sequence = [triad[0], triad[1], triad[2], triad[1]]  # Up-down pattern
            
            for i, note in enumerate(arp_sequence):
                arp.append(Message('note_on', note=note, velocity=80, time=0, channel=2))
                arp.append(Message('note_off', note=note, velocity=64, time=mid.ticks_per_beat, channel=2))
    
    # Convert to bytes
    bio = io.BytesIO()
    mid.save(file=bio)
    return bio.getvalue()

# ============================================================================
# Routes
# ============================================================================

@lyrics_workshop_bp.route("/workshop", methods=["GET"])
def workshop_page():
    """Serve the Enhanced Lyrics Workshop & Beat Studio page"""
    return render_template('lyrics_workshop_enhanced.html')

@lyrics_workshop_bp.route('/workshop/analyze', methods=['POST'])
def analyze():
    """Analyze lyrics for structure and metrics"""
    data = request.get_json(force=True)
    lyrics = data.get('lyrics', '')
    
    if not lyrics.strip():
        return jsonify({'error': 'No lyrics provided'}), 400
    
    lines = lyrics.replace('\r','').split('\n')
    syllables_per_line = []
    
    for line in lines:
        words = re.findall(r"[a-zA-Z']+", line)
        syllable_count = sum(count_syllables(word) for word in words)
        syllables_per_line.append(syllable_count)
    
    avg_syllables = sum(syllables_per_line) / max(1, len(syllables_per_line))
    emotion, recommended_bpm = detect_emotion_and_bpm(lyrics)
    sections = find_sections(lyrics)
    
    return jsonify({
        'sections': sections,
        'syllables_per_line': syllables_per_line, 
        'avg_syllables': round(avg_syllables, 1),
        'detected_emotion': emotion,
        'recommended_bpm': recommended_bpm
    })

@lyrics_workshop_bp.route('/workshop/improve', methods=['POST'])
def improve():
    """Improve lyrics (placeholder for LLM integration)"""
    data = request.get_json(force=True)
    lyrics = data.get('lyrics','')
    focus_area = data.get('focus_area', 'general')
    
    # Placeholder - integrate with your LLM service
    improved_lyrics = f"# Improved ({focus_area})\\n{lyrics}"
    
    return jsonify({
        'improved_lyrics': improved_lyrics,
        'diffs': [{'type': 'addition', 'line': 0, 'text': f'# Improved ({focus_area})'}]
    })

@lyrics_workshop_bp.route('/midi/full', methods=['POST'])
def midi_full():
    """Generate full multi-track MIDI"""
    data = request.get_json(force=True)
    
    bpm = int(data.get('bpm', 100))
    genre = data.get('genre', 'trap')
    key = data.get('key', 'C')
    scale = data.get('scale', 'minor')
    bars = int(data.get('lengthBars', 4))
    include = data.get('include', {
        'drums': True,
        'bass': True, 
        'chords': True,
        'arp': False
    })
    
    try:
        midi_bytes = write_full_midi(bpm, genre, key, scale, bars, include)
        b64 = base64.b64encode(midi_bytes).decode('utf-8')
        
        return jsonify({'midi_base64': b64})
        
    except Exception as e:
        return jsonify({'error': f'MIDI generation failed: {str(e)}'}), 500

# Export blueprint
__all__ = ['lyrics_workshop_bp']