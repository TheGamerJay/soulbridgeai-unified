# -*- coding: utf-8 -*-
"""
Lyrics Workshop - Enhanced Implementation
Combines user's original concept with comprehensive analysis system
"""
import re
import base64
import json
from io import BytesIO
from flask import Blueprint, request, jsonify
from typing import Dict, List, Tuple, Any

# Import our existing analysis system
from .lyrics_analyzer import analyze_lyrics_comprehensive, _analyze_genre, _analyze_mood

lyrics_workshop_bp = Blueprint("lyrics_workshop", __name__, url_prefix="/api/beat")

# Beat patterns and MIDI generation
STYLE_BPM = {
    'trap': 140,
    'drill': 140, 
    'rnb': 85,
    'pop': 120,
    'reggaeton': 95,
    'bachata': 90,
    'house': 125,
    'afrobeats': 105
}

BEAT_PATTERNS = {
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
    'rnb': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        'openhat': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    },
    'reggaeton': {
        'kick': [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'clap': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0]
    },
    'bachata': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'bongo': [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
        'guira': [1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1]
    },
    'house': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'hihat': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        'openhat': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    },
    'afrobeats': {
        'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        'shaker': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'log': [0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0]
    }
}

# MIDI note mappings (General MIDI drum kit)
DRUM_NOTES = {
    'kick': 36,
    'snare': 38,
    'hihat': 42,
    'openhat': 46,
    'clap': 39,
    'bongo': 60,
    'guira': 37,
    'shaker': 70,
    'log': 77
}

def detect_emotion_and_bpm(lyrics: str) -> Tuple[str, int]:
    """Enhanced emotion detection using our existing mood analysis"""
    mood, confidence = _analyze_mood(lyrics)
    
    # Map our moods to simplified emotions for beat selection
    emotion_map = {
        'romantic': 'romantic',
        'dark': 'angry', 
        'energetic': 'confident',
        'sad': 'sad',
        'emotional': 'sad',
        'party': 'confident'
    }
    
    emotion = emotion_map.get(mood, 'neutral')
    
    # BPM suggestions based on emotion
    bpm_map = {
        'sad': 75,
        'romantic': 85,
        'angry': 145,
        'confident': 130,
        'neutral': 120
    }
    
    return emotion, bpm_map.get(emotion, 120)

def find_sections(lyrics: str) -> List[Dict[str, Any]]:
    """Find and identify sections in lyrics"""
    lines = lyrics.replace('\r', '').split('\n')
    sections = []
    current_section = None
    start_line = 0
    
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        
        # Check for section headers
        if any(keyword in line_clean for keyword in ['verse', 'chorus', 'hook', 'bridge', 'intro', 'outro']):
            # End previous section
            if current_section:
                sections.append({
                    'name': current_section,
                    'start': start_line,
                    'end': i - 1,
                    'text': '\n'.join(lines[start_line:i])
                })
            
            # Start new section
            if 'verse' in line_clean:
                current_section = 'Verse'
            elif any(word in line_clean for word in ['chorus', 'hook']):
                current_section = 'Chorus'
            elif 'bridge' in line_clean:
                current_section = 'Bridge'
            elif 'intro' in line_clean:
                current_section = 'Intro'
            elif 'outro' in line_clean:
                current_section = 'Outro'
            else:
                current_section = 'Section'
                
            start_line = i + 1
        elif line.strip() == '' and current_section and i - start_line > 3:
            # End section on empty line if we have content
            sections.append({
                'name': current_section,
                'start': start_line,
                'end': i - 1,
                'text': '\n'.join(lines[start_line:i])
            })
            current_section = None
            start_line = i + 1
    
    # Add final section
    if current_section and start_line < len(lines):
        sections.append({
            'name': current_section,
            'start': start_line,
            'end': len(lines) - 1,
            'text': '\n'.join(lines[start_line:])
        })
    
    # If no sections found, treat as one big section
    if not sections and lyrics.strip():
        sections.append({
            'name': 'Full Lyrics',
            'start': 0,
            'end': len(lines) - 1,
            'text': lyrics.strip()
        })
    
    return sections

def syllables_per_line(lines: List[str]) -> List[int]:
    """Count syllables per line using simple vowel counting"""
    def count_syllables(word: str) -> int:
        word = word.lower().strip()
        if not word:
            return 0
        
        vowels = 'aeiouy'
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        return max(count, 1)
    
    syllable_counts = []
    for line in lines:
        words = re.findall(r'\b\w+\b', line)
        total_syllables = sum(count_syllables(word) for word in words)
        syllable_counts.append(total_syllables)
    
    return syllable_counts

def improve_block(text: str, keep_emotion: bool = True, sharper_wordplay: bool = False, 
                 more_melodic: bool = False) -> Tuple[str, List[Dict[str, str]]]:
    """Improve a block of lyrics with rule-based suggestions"""
    lines = text.split('\n')
    improved_lines = []
    diffs = []
    
    for line in lines:
        original_line = line.strip()
        if not original_line:
            improved_lines.append(line)
            continue
            
        improved_line = original_line
        
        # Rule-based improvements
        improvements = []
        
        # Fix common issues
        if improved_line.count(' the ') > 2:
            improved_line = improved_line.replace(' the ', ' that ', 1)
            improvements.append("reduced repetitive 'the'")
        
        # Add alliteration for sharper wordplay
        if sharper_wordplay:
            words = improved_line.split()
            if len(words) > 2 and words[0][0].lower() == words[1][0].lower():
                improvements.append("enhanced alliteration")
        
        # Make more melodic (add vowel sounds)
        if more_melodic:
            # Simple vowel enhancement
            vowel_heavy_words = ['flowing', 'soaring', 'glowing', 'knowing']
            for word in improved_line.split():
                if len(word) > 4 and word.lower() not in vowel_heavy_words:
                    # This is a simplified example - in practice, you'd use more sophisticated replacement
                    pass
        
        # Only add to diffs if line actually changed
        if improved_line != original_line:
            diffs.append({
                'original': original_line,
                'suggestion': improved_line,
                'improvements': improvements
            })
        
        improved_lines.append(improved_line)
    
    return '\n'.join(improved_lines), diffs

def make_pattern(style: str) -> Dict[str, List[int]]:
    """Get beat pattern for style"""
    return BEAT_PATTERNS.get(style, BEAT_PATTERNS['trap'])

def write_midi(pattern: Dict[str, List[int]], bpm: int) -> bytes:
    """Generate MIDI file from pattern"""
    try:
        import mido
    except ImportError:
        # Return empty bytes if mido not available
        return b''
    
    # Create MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set tempo
    tempo = mido.bpm2tempo(bpm)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))
    
    # Calculate ticks per 16th note (assuming 480 ticks per quarter note)
    ticks_per_quarter = 480
    ticks_per_16th = ticks_per_quarter // 4
    
    # Add drum patterns
    for instrument, pattern_list in pattern.items():
        if instrument in DRUM_NOTES:
            note = DRUM_NOTES[instrument]
            time = 0
            
            for i, hit in enumerate(pattern_list):
                if hit:
                    # Note on
                    track.append(mido.Message('note_on', channel=9, note=note, velocity=100, time=time))
                    # Note off (short duration)
                    track.append(mido.Message('note_off', channel=9, note=note, velocity=0, time=60))
                    time = ticks_per_16th - 60  # Remaining time to next 16th note
                else:
                    time += ticks_per_16th
    
    # Save to bytes
    output = BytesIO()
    mid.save(file=output)
    return output.getvalue()

# ------------------ API Endpoints ------------------
@lyrics_workshop_bp.route("/workshop", methods=["GET"])
def workshop_page():
    """Serve the enhanced Lyrics Workshop page"""
    from flask import render_template
    return render_template('lyrics_workshop.html')

@lyrics_workshop_bp.route('/workshop/analyze', methods=['POST'])
def workshop_analyze():
    """Enhanced analysis combining both systems"""
    data = request.get_json(force=True) or {}
    lyrics = data.get('lyrics', '').strip()
    
    if not lyrics:
        return jsonify({'error': 'No lyrics provided'}), 400
    
    try:
        # Use our comprehensive analysis
        analysis = analyze_lyrics_comprehensive(lyrics)
        
        # Add workshop-specific data
        lines = lyrics.replace('\r', '').split('\n')
        sections = find_sections(lyrics)
        syllables = syllables_per_line([line for line in lines if line.strip()])
        avg_syllables = sum(syllables) / max(len(syllables), 1) if syllables else 0
        
        return jsonify({
            'sections': sections,
            'syllables_per_line': syllables,
            'avg_syllables': round(avg_syllables, 1),
            'detected_emotion': analysis['detected_mood'],
            'recommended_bpm': STYLE_BPM.get(analysis['final_genre'], 120),
            'comprehensive_analysis': analysis  # Include full analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lyrics_workshop_bp.route('/workshop/improve', methods=['POST'])
def workshop_improve():
    """Improve lyrics with options"""
    data = request.get_json(force=True) or {}
    lyrics = data.get('lyrics', '')
    mode = data.get('mode', 'full')
    target = data.get('targetSection')
    keep_emotion = data.get('keepEmotion', True)
    sharper_wordplay = data.get('sharperWordplay', False)
    more_melodic = data.get('moreMelodic', False)
    
    try:
        lines = lyrics.replace('\r', '').split('\n')
        sections = find_sections(lyrics)
        
        if mode == 'section' and target:
            # Find target section
            target_section = None
            for section in sections:
                if section['name'].lower() == target.lower():
                    target_section = section
                    break
            
            if not target_section:
                return jsonify({
                    'improved_lyrics': lyrics, 
                    'diffs': [],
                    'error': f'Section "{target}" not found'
                })
            
            # Extract section text
            start, end = target_section['start'], target_section['end']
            section_text = '\n'.join(lines[start:end+1])
            
            # Improve section
            improved_section, diffs = improve_block(
                section_text, keep_emotion, sharper_wordplay, more_melodic
            )
            
            # Replace in original
            new_lines = lines[:]
            new_lines[start:end+1] = improved_section.split('\n')
            improved_lyrics = '\n'.join(new_lines)
            
        else:
            # Improve full lyrics
            improved_lyrics, diffs = improve_block(
                lyrics, keep_emotion, sharper_wordplay, more_melodic
            )
        
        return jsonify({
            'improved_lyrics': improved_lyrics,
            'diffs': diffs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lyrics_workshop_bp.route('/workshop/beat', methods=['POST'])
def workshop_beat():
    """Generate beat pattern and MIDI from lyrics"""
    data = request.get_json(force=True) or {}
    lyrics = data.get('lyrics', '')
    prefer_bpm = data.get('prefer_bpm')
    
    try:
        # Detect emotion and genre
        emotion, rec_bpm = detect_emotion_and_bpm(lyrics)
        genre, _ = _analyze_genre(lyrics)
        
        # Map emotion to beat style
        style_map = {
            'sad': 'rnb',
            'romantic': 'bachata' if 'bachata' in lyrics.lower() else 'rnb',
            'angry': 'drill',
            'confident': 'trap',
            'neutral': genre if genre in BEAT_PATTERNS else 'trap'
        }
        
        style = style_map.get(emotion, 'trap')
        bpm = int(prefer_bpm) if prefer_bpm else STYLE_BPM.get(style, rec_bpm)
        pattern = make_pattern(style)
        
        # Generate MIDI
        midi_bytes = write_midi(pattern, bpm)
        midi_b64 = base64.b64encode(midi_bytes).decode('utf-8') if midi_bytes else None
        
        return jsonify({
            'bpm': bpm,
            'style': style,
            'pattern': pattern,
            'midi_base64': midi_b64,
            'emotion': emotion,
            'detected_genre': genre
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lyrics_workshop_bp.route('/workshop/export', methods=['POST'])
def workshop_export():
    """Export improved lyrics in various formats"""
    data = request.get_json(force=True) or {}
    lyrics = data.get('lyrics', '')
    format_type = data.get('format', 'txt')  # txt, json, pdf
    
    try:
        if format_type == 'json':
            # Export as structured JSON
            analysis = analyze_lyrics_comprehensive(lyrics)
            sections = find_sections(lyrics)
            
            export_data = {
                'lyrics': lyrics,
                'analysis': analysis,
                'sections': sections,
                'export_timestamp': '2024-01-01',  # You'd use datetime.now()
                'format_version': '1.0'
            }
            
            return jsonify({
                'success': True,
                'data': export_data,
                'filename': 'lyrics_analysis.json'
            })
            
        else:
            # Export as plain text
            return jsonify({
                'success': True,
                'data': lyrics,
                'filename': 'improved_lyrics.txt'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500