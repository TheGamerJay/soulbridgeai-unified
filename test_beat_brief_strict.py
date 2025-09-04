#!/usr/bin/env python3
"""
Test script for Beat Brief Strict API
Demonstrates the strict beat description generator that never echoes user lyrics
"""
import requests
import json

# Test endpoint
API_URL = "http://localhost:5000/api/beat/brief_strict"

# Test cases
test_cases = [
    {
        "name": "🎵 Basic Trap Beat",
        "data": {
            "lyrics": "I'm on the block with my crew, making money moves, trap life forever",
            "mood": "dark", 
            "style": "trap",
            "bpm": 90
        }
    },
    {
        "name": "💃 Romantic Bachata",
        "data": {
            "lyrics": "Tu eres mi amor, mi corazón late por ti, bailamos juntos bajo la luna",
            "mood": "romantic",
            "style": "bachata",
            "key": "C major",
            "duration_sec": 180
        }
    },
    {
        "name": "🔥 Energetic Reggaeton",
        "data": {
            "lyrics": "Dale que vamo' a perrear toda la noche, dembow hasta el amanecer",
            "mood": "energetic", 
            "style": "reggaeton",
            "bpm": 98
        }
    },
    {
        "name": "🌙 Lo-Fi Hip Hop",
        "data": {
            "lyrics": "Chilling with the beats, late night vibes, vinyl crackle in the background",
            "mood": "sad",
            "style": "lo-fi hip-hop"
        }
    },
    {
        "name": "⚡ Future Bass Drop",
        "data": {
            "lyrics": "Drop the bass, feel the energy, synths are soaring high above",
            "style": "future bass",
            "mood": "energetic",
            "bpm": 150
        }
    },
    {
        "name": "🎼 Auto-Detection Test",
        "data": {
            "lyrics": "The beat goes hard with 808s sliding, trap snares hitting different"
            # No style specified - should auto-detect as trap
        }
    }
]

def test_endpoint():
    print("🎵 Testing Beat Brief Strict API")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 30)
        
        try:
            # Make API call
            response = requests.post(API_URL, 
                                   headers={
                                       "Content-Type": "application/json",
                                       "Accept": "text/plain"
                                   },
                                   json=test['data'],
                                   timeout=10)
            
            if response.status_code == 200:
                brief = response.text
                print(f"✅ Status: {response.status_code}")
                print(f"📝 Brief ({len(brief)} chars):")
                print(f"   {brief}")
                
                # Check that user lyrics aren't echoed
                user_text = test['data'].get('lyrics', '').lower()
                brief_lower = brief.lower()
                
                # Simple check for 3+ word sequences
                words = user_text.split()
                echoed = False
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10 and phrase in brief_lower:
                        echoed = True
                        print(f"⚠️  POSSIBLE ECHO DETECTED: '{phrase}'")
                
                if not echoed:
                    print("✅ NO LYRIC ECHO DETECTED")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

def show_frontend_example():
    print("\n" + "=" * 50)
    print("🌐 Frontend Integration Example")
    print("=" * 50)
    
    js_code = '''
// Frontend JavaScript Example
async function generateBeatBrief(userLyrics, mood = "energetic", style = "", bpm = null) {
    try {
        const response = await fetch("/api/beat/brief_strict", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "Accept": "text/plain" 
            },
            body: JSON.stringify({
                lyrics: userLyrics,          // Used for inference only - never echoed
                mood: mood,                  // "romantic", "dark", "energetic", etc.
                style: style,                // "bachata", "trap", "reggaeton", etc.
                bpm: bpm,                    // Optional BPM override
                key: "C major",              // Optional key
                time_sig: "4/4",             // Optional time signature
                duration_sec: 150            // Optional duration
            })
        });
        
        if (response.ok) {
            const beatBrief = await response.text();
            
            // Show the clean, copy-ready description
            document.getElementById('beat-description').textContent = beatBrief;
            
            // ✅ GUARANTEED: No user lyrics will appear in beatBrief
            console.log('Generated brief:', beatBrief);
            
        } else {
            console.error('API Error:', response.status);
        }
        
    } catch (error) {
        console.error('Network Error:', error);
    }
}

// Example usage:
generateBeatBrief(
    "I'm feeling the reggaeton vibes tonight, dale que vamos a bailar", 
    "energetic", 
    "reggaeton", 
    98
);
'''
    
    print(js_code)

if __name__ == "__main__":
    print("🚀 Starting Beat Brief Strict API Tests")
    print("Make sure your Flask app is running on localhost:5000")
    print()
    
    # Run tests
    test_endpoint()
    
    # Show frontend example
    show_frontend_example()
    
    print("\n✨ Tests completed! Check the output above for any issues.")