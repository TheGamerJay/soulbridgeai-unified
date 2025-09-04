# ================================
# BACKEND (Flask) — LYRICS ANALYZER & BEAT GENERATOR
# ================================
# File: backend/modules/beat/lyrics_analyzer.py

import re
import json
from flask import Blueprint, request, jsonify, Response
from typing import Dict, List, Tuple, Any

lyrics_analyzer_bp = Blueprint(
    "beat_lyrics", __name__,
    url_prefix="/api/beat"   # matches your menu links
)

# ------------------ Core Analysis Maps ------------------
GENRE_KEYWORDS = {
    "trap": ["trap", "808", "flex", "drip", "bag", "sauce", "slide", "finesse", "gang", "crew"],
    "drill": ["drill", "opp", "smoke", "slide", "pull up", "caught", "block", "hood", "street"],
    "hip-hop": ["hip hop", "flow", "bars", "spit", "mic", "beats", "rhyme", "cypher", "freestyle"],
    "reggaeton": ["perreo", "dembow", "discoteca", "baila", "party", "noche", "reggaeton", "dale"],
    "bachata": ["amor", "corazón", "guitarra", "romantic", "bailar", "luna", "estrella", "bachata"],
    "r&b": ["love", "baby", "girl", "heart", "soul", "smooth", "tonight", "forever"],
    "pop": ["tonight", "party", "dance", "love", "young", "free", "dream", "shine"],
    "latin": ["mi amor", "corazón", "vida", "noche", "baila", "fiesta", "latino", "ritmo"],
    "afrobeats": ["dance", "move", "body", "rhythm", "african", "vibe", "celebration", "energy"]
}

MOOD_KEYWORDS = {
    "romantic": ["love", "heart", "baby", "kiss", "forever", "together", "beautiful", "sweet"],
    "energetic": ["party", "dance", "loud", "crazy", "wild", "energy", "power", "strong"],
    "dark": ["pain", "dark", "alone", "struggle", "hurt", "cold", "empty", "lost"],
    "confident": ["boss", "king", "queen", "winner", "success", "money", "rich", "power"],
    "emotional": ["feel", "cry", "tears", "heart", "soul", "deep", "emotion", "heavy"],
    "party": ["party", "club", "drink", "dance", "night", "fun", "celebrate", "turn up"]
}

RHYME_PATTERNS = {
    "AABB": "Simple couplets (rhyme every 2 lines)",
    "ABAB": "Alternating rhyme (classic verse pattern)",
    "ABCB": "Second and fourth lines rhyme",
    "AAAA": "Every line rhymes (challenge mode)",
    "ABCC": "Third and fourth lines rhyme",
    "FREE": "Free verse (no consistent pattern)"
}

COMMON_ISSUES = {
    "repetitive_words": "Uses the same words too frequently",
    "weak_rhymes": "Rhyme scheme could be stronger",
    "unclear_flow": "Syllable count varies too much between lines",
    "generic_content": "Content feels generic, needs more personality",
    "poor_structure": "Verses/choruses not clearly defined",
    "forced_rhymes": "Some rhymes feel forced or unnatural",
    "inconsistent_theme": "Theme or story isn't consistent throughout"
}

# ------------------ Utilities ------------------
def _clean_lyrics(lyrics: str) -> str:
    """Clean and normalize lyrics text"""
    lyrics = lyrics.strip()
    # Remove extra whitespace but preserve line breaks
    lyrics = re.sub(r' +', ' ', lyrics)
    lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics)
    return lyrics

def _split_into_sections(lyrics: str) -> List[Dict[str, Any]]:
    """Split lyrics into identifiable sections"""
    lines = lyrics.split('\n')
    sections = []
    current_section = []
    section_type = "verse"
    section_number = 1
    
    for line in lines:
        line = line.strip()
        if not line:  # Empty line - potential section break
            if current_section:
                sections.append({
                    'type': section_type,
                    'number': section_number,
                    'lines': current_section.copy(),
                    'text': '\n'.join(current_section)
                })
                current_section = []
                section_number += 1
        else:
            # Detect section types based on content
            line_lower = line.lower()
            if any(word in line_lower for word in ['chorus', 'hook', 'coro', 'estribillo']):
                if current_section:
                    sections.append({
                        'type': section_type,
                        'number': len([s for s in sections if s['type'] == section_type]) + 1,
                        'lines': current_section.copy(),
                        'text': '\n'.join(current_section)
                    })
                    current_section = []
                section_type = "chorus"
            elif any(word in line_lower for word in ['verse', 'verso', 'estrofa']):
                if current_section:
                    sections.append({
                        'type': section_type,
                        'number': len([s for s in sections if s['type'] == section_type]) + 1,
                        'lines': current_section.copy(),
                        'text': '\n'.join(current_section)
                    })
                    current_section = []
                section_type = "verse"
            else:
                current_section.append(line)
    
    # Add final section
    if current_section:
        sections.append({
            'type': section_type,
            'number': len([s for s in sections if s['type'] == section_type]) + 1,
            'lines': current_section.copy(),
            'text': '\n'.join(current_section)
        })
    
    return sections

def _analyze_genre(lyrics: str) -> Tuple[str, float]:
    """Analyze lyrics to detect genre with confidence"""
    lyrics_lower = lyrics.lower()
    genre_scores = {}
    
    for genre, keywords in GENRE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in lyrics_lower:
                score += lyrics_lower.count(keyword)
        genre_scores[genre] = score
    
    if not genre_scores or max(genre_scores.values()) == 0:
        return "hip-hop", 0.3  # Default with low confidence
    
    best_genre = max(genre_scores, key=genre_scores.get)
    total_keywords = sum(genre_scores.values())
    confidence = min(genre_scores[best_genre] / max(total_keywords, 1), 1.0)
    
    return best_genre, confidence

def _analyze_mood(lyrics: str) -> Tuple[str, float]:
    """Analyze lyrics to detect mood with confidence"""
    lyrics_lower = lyrics.lower()
    mood_scores = {}
    
    for mood, keywords in MOOD_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in lyrics_lower:
                score += lyrics_lower.count(keyword)
        mood_scores[mood] = score
    
    if not mood_scores or max(mood_scores.values()) == 0:
        return "emotional", 0.4  # Default with medium confidence
    
    best_mood = max(mood_scores, key=mood_scores.get)
    total_keywords = sum(mood_scores.values())
    confidence = min(mood_scores[best_mood] / max(total_keywords, 1), 1.0)
    
    return best_mood, confidence

def _analyze_rhyme_scheme(lines: List[str]) -> str:
    """Analyze rhyme scheme of a section"""
    if len(lines) < 2:
        return "FREE"
    
    # Simple rhyme detection based on ending sounds
    endings = []
    for line in lines:
        words = line.strip().split()
        if words:
            last_word = re.sub(r'[^\w]', '', words[-1].lower())
            # Simple phonetic similarity (last 2-3 chars)
            ending = last_word[-3:] if len(last_word) >= 3 else last_word
            endings.append(ending)
    
    if len(endings) < 2:
        return "FREE"
    
    # Check common patterns
    if len(endings) >= 4:
        if endings[0] == endings[1] and endings[2] == endings[3]:
            return "AABB"
        elif endings[0] == endings[2] and endings[1] == endings[3]:
            return "ABAB"
        elif endings[1] == endings[3]:
            return "ABCB"
        elif all(e == endings[0] for e in endings):
            return "AAAA"
    
    return "FREE"

def _count_syllables(word: str) -> int:
    """Simple syllable counter"""
    word = word.lower().strip()
    if not word:
        return 0
    
    # Simple vowel-based counting
    vowels = 'aeiouy'
    count = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Ensure at least 1 syllable
    return max(count, 1)

def _analyze_flow(lines: List[str]) -> Dict[str, Any]:
    """Analyze syllable count and flow consistency"""
    syllable_counts = []
    
    for line in lines:
        words = re.findall(r'\b\w+\b', line)
        syllables = sum(_count_syllables(word) for word in words)
        syllable_counts.append(syllables)
    
    if not syllable_counts:
        return {"average": 0, "consistency": 0, "range": [0, 0]}
    
    avg_syllables = sum(syllable_counts) / len(syllable_counts)
    variance = sum((x - avg_syllables) ** 2 for x in syllable_counts) / len(syllable_counts)
    consistency = max(0, 1 - (variance / max(avg_syllables, 1)))
    
    return {
        "average": round(avg_syllables, 1),
        "consistency": round(consistency, 2),
        "range": [min(syllable_counts), max(syllable_counts)],
        "counts": syllable_counts
    }

def _identify_issues(lyrics: str, sections: List[Dict]) -> List[Dict[str, Any]]:
    """Identify common issues in lyrics"""
    issues = []
    
    # Check for repetitive words
    words = re.findall(r'\b\w+\b', lyrics.lower())
    word_counts = {}
    for word in words:
        if len(word) > 3:  # Only check longer words
            word_counts[word] = word_counts.get(word, 0) + 1
    
    repetitive_words = [word for word, count in word_counts.items() 
                       if count > len(words) * 0.05 and count > 3]
    
    if repetitive_words:
        issues.append({
            "type": "repetitive_words",
            "description": f"Words used frequently: {', '.join(repetitive_words[:5])}",
            "severity": "medium",
            "suggestion": "Try using synonyms or varying your vocabulary"
        })
    
    # Check for weak flow consistency
    for section in sections:
        flow = _analyze_flow(section['lines'])
        if flow['consistency'] < 0.6:
            issues.append({
                "type": "unclear_flow",
                "description": f"{section['type'].title()} {section['number']} has inconsistent syllable count",
                "severity": "high",
                "suggestion": f"Try to keep syllables between {flow['range'][0]}-{flow['range'][1]} per line"
            })
    
    # Check for generic content
    if len(set(words)) / max(len(words), 1) < 0.4:  # Low unique word ratio
        issues.append({
            "type": "generic_content",
            "description": "Content could be more unique and personal",
            "severity": "medium",
            "suggestion": "Add specific details, personal experiences, or unique metaphors"
        })
    
    return issues

def _generate_suggestions(section: Dict[str, Any], issue_type: str = None) -> List[str]:
    """Generate specific improvement suggestions"""
    suggestions = []
    
    if not issue_type:
        # General suggestions based on section analysis
        rhyme_scheme = _analyze_rhyme_scheme(section['lines'])
        flow = _analyze_flow(section['lines'])
        
        if rhyme_scheme == "FREE":
            suggestions.append("Consider adding a consistent rhyme scheme (ABAB or AABB work well)")
        
        if flow['consistency'] < 0.7:
            suggestions.append(f"Try to maintain {int(flow['average'])} syllables per line for better flow")
        
        if len(section['lines']) < 4:
            suggestions.append("Consider expanding this section with more lines")
        
        suggestions.append("Add more specific imagery and personal details")
        suggestions.append("Strengthen the emotional connection with the listener")
        
    else:
        # Specific suggestions based on issue type
        if issue_type == "repetitive_words":
            suggestions.extend([
                "Use a thesaurus to find synonyms for overused words",
                "Vary your vocabulary with different word choices",
                "Replace repetitive words with metaphors or imagery"
            ])
        elif issue_type == "weak_rhymes":
            suggestions.extend([
                "Use perfect rhymes instead of near-rhymes where possible",
                "Try internal rhymes within lines for complexity",
                "Consider multisyllabic rhymes for advanced flow"
            ])
        elif issue_type == "unclear_flow":
            suggestions.extend([
                "Count syllables in each line and aim for consistency",
                "Practice reading aloud to test the natural flow",
                "Use shorter words to reduce syllable count if needed"
            ])
        elif issue_type == "generic_content":
            suggestions.extend([
                "Add personal experiences and specific details",
                "Use unique metaphors instead of common phrases",
                "Tell a story that only you can tell"
            ])
    
    return suggestions[:5]  # Limit to 5 suggestions

# ------------------ Main Analysis Function ------------------
def analyze_lyrics_comprehensive(lyrics: str, target_genre: str = None) -> Dict[str, Any]:
    """Comprehensive lyrics analysis with beat generation"""
    
    clean_lyrics = _clean_lyrics(lyrics)
    sections = _split_into_sections(clean_lyrics)
    
    # Genre and mood analysis
    detected_genre, genre_confidence = _analyze_genre(clean_lyrics)
    detected_mood, mood_confidence = _analyze_mood(clean_lyrics)
    
    # Use target genre if provided and confident
    final_genre = target_genre if target_genre else detected_genre
    
    # Analyze each section
    section_analysis = []
    for section in sections:
        rhyme_scheme = _analyze_rhyme_scheme(section['lines'])
        flow_analysis = _analyze_flow(section['lines'])
        
        section_analysis.append({
            "type": section['type'],
            "number": section['number'],
            "text": section['text'],
            "line_count": len(section['lines']),
            "rhyme_scheme": rhyme_scheme,
            "flow": flow_analysis,
            "suggestions": _generate_suggestions(section)
        })
    
    # Identify issues
    issues = _identify_issues(clean_lyrics, sections)
    
    # Calculate overall scores
    total_lines = sum(len(s['lines']) for s in sections)
    avg_flow_consistency = sum(s['flow']['consistency'] for s in section_analysis) / max(len(section_analysis), 1)
    
    overall_score = {
        "structure": min(len(sections) * 20, 100),  # More sections = better structure
        "flow": int(avg_flow_consistency * 100),
        "creativity": max(20, 100 - len(issues) * 15),  # Fewer issues = more creative
        "overall": 0
    }
    overall_score["overall"] = int((overall_score["structure"] + overall_score["flow"] + overall_score["creativity"]) / 3)
    
    return {
        "lyrics": clean_lyrics,
        "detected_genre": detected_genre,
        "genre_confidence": round(genre_confidence, 2),
        "detected_mood": detected_mood,
        "mood_confidence": round(mood_confidence, 2),
        "final_genre": final_genre,
        "sections": section_analysis,
        "issues": issues,
        "scores": overall_score,
        "total_lines": total_lines,
        "word_count": len(clean_lyrics.split()),
        "estimated_duration": max(60, total_lines * 3)  # Rough estimate: 3 seconds per line
    }

# ------------------ Frontend Route ------------------
@lyrics_analyzer_bp.route("/lyrics", methods=["GET"]) 
def lyrics_analyzer_page():
    """Serve the Lyrics Analyzer frontend page"""
    # Authentication check
    from flask import render_template, session, redirect
    if not session.get('logged_in'):
        return redirect('/auth/login?return_to=api/beat/lyrics')
    return render_template('lyrics_analyzer.html')

@lyrics_analyzer_bp.route("/lyrics/ping", methods=["GET"])
def analyzer_ping():
    """Health check endpoint for the lyrics analyzer"""
    q = request.args.get("q", "")
    return jsonify({
        'ok': True, 
        'route': "/api/beat/lyrics", 
        'q': q,
        'blueprint': 'beat_lyrics'
    })

# ------------------ API Endpoints ------------------
@lyrics_analyzer_bp.route("/analyze_lyrics", methods=["POST"])
def analyze_lyrics_endpoint():
    """
    Analyze user lyrics and provide comprehensive feedback
    
    JSON in: {
        "lyrics": "user lyrics text",
        "target_genre": "optional genre override"
    }
    
    Returns: Complete analysis with suggestions and beat recommendations
    """
    # Authentication check
    from flask import session
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
    data = request.get_json(silent=True) or {}
    lyrics = data.get("lyrics", "").strip()
    target_genre = data.get("target_genre", "").strip()
    
    if not lyrics:
        return jsonify({
            "success": False,
            "error": "No lyrics provided"
        }), 400
    
    if len(lyrics) < 10:
        return jsonify({
            "success": False,
            "error": "Lyrics too short for analysis"
        }), 400
    
    try:
        analysis = analyze_lyrics_comprehensive(lyrics, target_genre)
        
        return jsonify({
            "success": True,
            "analysis": analysis
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500

@lyrics_analyzer_bp.route("/generate_beat_from_lyrics", methods=["POST"])
def generate_beat_from_lyrics():
    """
    Generate beat brief based on analyzed lyrics
    
    JSON in: {
        "lyrics": "user lyrics text",
        "analysis": "optional pre-analyzed data"
    }
    
    Returns: text/plain beat description optimized for the lyrics
    """
    data = request.get_json(silent=True) or {}
    lyrics = data.get("lyrics", "").strip()
    analysis_data = data.get("analysis")
    
    if not lyrics:
        return Response("Error: No lyrics provided", mimetype="text/plain"), 400
    
    try:
        # Use provided analysis or generate new one
        if analysis_data:
            analysis = analysis_data
        else:
            analysis = analyze_lyrics_comprehensive(lyrics)
        
        # Generate beat brief using the strict brief system
        from .beat_brief_strict import make_strict_brief
        
        beat_brief = make_strict_brief(
            lyrics=lyrics,
            mood=analysis['detected_mood'],
            style=analysis['final_genre'],
            bpm=None,  # Let system decide based on genre
            key_hint="",
            time_sig="",
            duration_sec=analysis['estimated_duration']
        )
        
        return Response(beat_brief, mimetype="text/plain")
        
    except Exception as e:
        return Response(f"Error generating beat: {str(e)}", mimetype="text/plain"), 500

@lyrics_analyzer_bp.route("/improve_section", methods=["POST"])
def improve_section():
    """
    Get specific improvement suggestions for a lyrics section
    
    JSON in: {
        "section_text": "lyrics section text",
        "section_type": "verse/chorus/bridge",
        "issue_type": "optional specific issue to address"
    }
    
    Returns: Targeted suggestions for improving the section
    """
    data = request.get_json(silent=True) or {}
    section_text = data.get("section_text", "").strip()
    section_type = data.get("section_type", "verse")
    issue_type = data.get("issue_type")
    
    if not section_text:
        return jsonify({
            "success": False,
            "error": "No section text provided"
        }), 400
    
    try:
        # Create section object for analysis
        lines = section_text.split('\n')
        section = {
            'type': section_type,
            'number': 1,
            'lines': [line.strip() for line in lines if line.strip()],
            'text': section_text
        }
        
        # Generate targeted suggestions
        suggestions = _generate_suggestions(section, issue_type)
        
        # Additional analysis
        rhyme_scheme = _analyze_rhyme_scheme(section['lines'])
        flow_analysis = _analyze_flow(section['lines'])
        
        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "current_rhyme_scheme": rhyme_scheme,
            "rhyme_explanation": RHYME_PATTERNS.get(rhyme_scheme, "Unknown pattern"),
            "flow_analysis": flow_analysis,
            "recommended_syllables": int(flow_analysis['average'])
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500