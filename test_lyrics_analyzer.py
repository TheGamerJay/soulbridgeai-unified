#!/usr/bin/env python3
"""
Test script for Lyrics Analyzer API
Comprehensive testing of lyrics analysis, improvement suggestions, and beat generation
"""
import requests
import json

# Test endpoint URLs
BASE_URL = "http://localhost:5000/api/beat"
ANALYZE_URL = f"{BASE_URL}/analyze_lyrics"
IMPROVE_URL = f"{BASE_URL}/improve_section"
BEAT_URL = f"{BASE_URL}/generate_beat_from_lyrics"

# Test cases with different genres and styles
test_lyrics = {
    "trap": """
    Verse 1:
    Started from the bottom now we climbing up the ladder
    Money in my pocket, dreams are getting fatter
    808s are thumping while I spit these bars
    Trap life forever, we the rising stars
    
    Chorus:
    We rise up, never gonna fall down
    Grinding every day in this small town
    Trap beats hitting hard like a freight train
    Success running thick up in my veins
    """,
    
    "bachata": """
    Verso 1:
    Tu eres mi amor, mi corazón late por ti
    Bailemos juntos bajo la luz de la luna
    Guitarra suena dulce, como tu voz
    En esta noche de bachata y fortuna
    
    Coro:
    Baila conmigo, hasta el amanecer
    Tu cuerpo cerca, me hace estremecer
    Bachata en el alma, amor en el corazón
    Contigo mi vida encuentra su canción
    """,
    
    "pop": """
    Verse 1:
    Dancing under neon lights tonight
    Everything is gonna be alright
    Music pumping, hearts are beating loud
    We're young and free above the crowd
    
    Pre-Chorus:
    Turn it up, turn it loud
    Make me proud, sing it out
    
    Chorus:
    We shine bright like diamonds in the sky
    Never gonna let this feeling die
    Pop dreams and electric energy
    This is our night of victory
    """,
    
    "reggaeton": """
    Verso 1:
    Dale que vamo' a perrear toda la noche
    Dembow sonando fuerte en la discoteca
    Tu cuerpo se mueve con ese derroche
    Reggaetón que nunca se seca
    
    Coro:
    Perreo hasta abajo, hasta que salga el sol
    Tu y yo bailando al ritmo del tambor
    Reggaetón que nos pone a gozar
    Esta noche no vamos a parar
    """
}

test_sections = {
    "weak_verse": """
    I wake up every morning feeling good
    Life is great, everything is as it should
    Walking down the street in my neighborhood
    Everything is fine and understood
    """,
    
    "flow_issues": """
    Today is the day
    That I'm gonna make my way to the top of the mountain high
    Nothing can stop me now
    Success
    """,
    
    "repetitive": """
    Money money money, that's all I need
    Money money money, fulfills my greed
    Money money money, helps me succeed  
    Money money money, it's my creed
    """
}

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_section(title):
    print(f"\n{'-'*30}")
    print(f"  {title}")
    print(f"{'-'*30}")

def test_lyrics_analysis():
    print_header("🔍 LYRICS ANALYSIS TESTS")
    
    for genre, lyrics in test_lyrics.items():
        print_section(f"Testing {genre.upper()} lyrics")
        
        try:
            response = requests.post(ANALYZE_URL, 
                                   headers={"Content-Type": "application/json"},
                                   json={"lyrics": lyrics},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    analysis = result['analysis']
                    
                    print(f"✅ Analysis successful")
                    print(f"📊 Detected Genre: {analysis['detected_genre']} ({analysis['genre_confidence']*100:.1f}% confidence)")
                    print(f"🎭 Detected Mood: {analysis['detected_mood']} ({analysis['mood_confidence']*100:.1f}% confidence)")
                    print(f"📈 Scores - Overall: {analysis['scores']['overall']}/100, Flow: {analysis['scores']['flow']}/100")
                    print(f"📑 Sections: {len(analysis['sections'])} sections, {analysis['total_lines']} total lines")
                    print(f"⚠️ Issues Found: {len(analysis['issues'])} issues")
                    
                    # Show first few suggestions
                    if analysis['sections']:
                        first_section = analysis['sections'][0]
                        print(f"💡 First section suggestions:")
                        for i, suggestion in enumerate(first_section['suggestions'][:2], 1):
                            print(f"   {i}. {suggestion}")
                else:
                    print(f"❌ Analysis failed: {result['error']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

def test_section_improvement():
    print_header("✨ SECTION IMPROVEMENT TESTS")
    
    for issue_type, section_text in test_sections.items():
        print_section(f"Testing {issue_type} improvement")
        
        try:
            response = requests.post(IMPROVE_URL,
                                   headers={"Content-Type": "application/json"},
                                   json={
                                       "section_text": section_text,
                                       "section_type": "verse",
                                       "issue_type": issue_type.replace("_", " ") if "_" in issue_type else None
                                   },
                                   timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ Improvement analysis successful")
                    print(f"🎵 Current Rhyme Scheme: {result['current_rhyme_scheme']}")
                    print(f"📊 Recommended Syllables: {result['recommended_syllables']}")
                    print(f"💡 Suggestions:")
                    
                    for i, suggestion in enumerate(result['suggestions'], 1):
                        print(f"   {i}. {suggestion}")
                        
                    flow = result['flow_analysis']
                    print(f"📈 Flow: {flow['average']} avg syllables, {flow['consistency']*100:.1f}% consistency")
                else:
                    print(f"❌ Improvement failed: {result['error']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

def test_beat_generation():
    print_header("🎵 BEAT GENERATION TESTS")
    
    # Test beat generation for each genre
    for genre, lyrics in test_lyrics.items():
        print_section(f"Generating beat for {genre.upper()}")
        
        try:
            response = requests.post(BEAT_URL,
                                   headers={
                                       "Content-Type": "application/json",
                                       "Accept": "text/plain"
                                   },
                                   json={"lyrics": lyrics},
                                   timeout=20)
            
            if response.status_code == 200:
                beat_brief = response.text
                print(f"✅ Beat generation successful")
                print(f"📝 Brief length: {len(beat_brief)} characters")
                print(f"🎵 Generated Beat Brief:")
                print(f"   {beat_brief[:200]}{'...' if len(beat_brief) > 200 else ''}")
                
                # Check that no lyrics are repeated
                lyrics_words = set(lyrics.lower().split())
                brief_words = set(beat_brief.lower().split())
                
                # Check for potential echoes (3+ word sequences)
                lyrics_lower = lyrics.lower()
                brief_lower = beat_brief.lower()
                
                # Simple check for word sequences
                echo_found = False
                words = lyrics_lower.split()
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10 and phrase in brief_lower:
                        echo_found = True
                        print(f"⚠️  POTENTIAL ECHO: '{phrase}'")
                
                if not echo_found:
                    print(f"✅ No lyric echo detected")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

def test_edge_cases():
    print_header("🧪 EDGE CASES & ERROR HANDLING")
    
    edge_cases = [
        ("Empty lyrics", ""),
        ("Too short", "Hi"),
        ("Only spaces", "   \n  \n  "),
        ("Special characters", "!@#$%^&*()"),
        ("Very long lyrics", "Test " * 1000),
    ]
    
    for test_name, lyrics in edge_cases:
        print_section(f"Testing: {test_name}")
        
        try:
            response = requests.post(ANALYZE_URL,
                                   headers={"Content-Type": "application/json"},
                                   json={"lyrics": lyrics},
                                   timeout=10)
            
            result = response.json()
            
            if response.status_code == 200:
                if result['success']:
                    print(f"✅ Handled gracefully - analysis completed")
                else:
                    print(f"✅ Proper error handling: {result['error']}")
            elif response.status_code == 400:
                print(f"✅ Proper validation: {result.get('error', 'Bad request')}")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

def show_frontend_usage():
    print_header("🌐 FRONTEND USAGE EXAMPLES")
    
    js_examples = '''
// 1. Analyze lyrics
const lyricsAnalysis = await fetch('/api/beat/analyze_lyrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        lyrics: userLyrics,
        target_genre: "trap" // optional
    })
});

// 2. Improve specific section
const improvements = await fetch('/api/beat/improve_section', {
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        section_text: selectedSection,
        section_type: "verse", 
        issue_type: "weak_rhymes" // optional
    })
});

// 3. Generate beat from lyrics
const beatBrief = await fetch('/api/beat/generate_beat_from_lyrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'text/plain' },
    body: JSON.stringify({ lyrics: userLyrics })
});

// Access the full UI at: /api/beat/lyrics
'''
    
    print("JavaScript Integration Examples:")
    print(js_examples)
    
    print("\n📍 Available Endpoints:")
    print("• GET  /api/beat/lyrics                    - Full lyrics analyzer UI")
    print("• POST /api/beat/analyze_lyrics           - Comprehensive lyrics analysis")  
    print("• POST /api/beat/improve_section          - Section-specific improvements")
    print("• POST /api/beat/generate_beat_from_lyrics - Beat brief generation")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Lyrics Analyzer Tests")
    print("Make sure your Flask app is running on localhost:5000")
    
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
    except:
        print("⚠️  Warning: Could not connect to server. Make sure Flask app is running.")
        print("   Run: python backend/app.py")
    
    # Run all tests
    test_lyrics_analysis()
    test_section_improvement()
    test_beat_generation()
    test_edge_cases()
    show_frontend_usage()
    
    print(f"\n{'='*50}")
    print("🎉 ALL TESTS COMPLETED!")
    print("📝 Check the results above for any issues")
    print("🌐 Visit http://localhost:5000/api/beat/lyrics for the full UI")
    print(f"{'='*50}")