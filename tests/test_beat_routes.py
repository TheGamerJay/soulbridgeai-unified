# tests/test_beat_routes.py
"""
Basic tests for beat routes - lyrics analyzer and workshop endpoints
"""
import pytest
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app import create_app

@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_lyrics_analyzer_ping(client):
    """Test lyrics analyzer ping endpoint"""
    response = client.get("/api/beat/lyrics/ping")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert data['blueprint'] == 'beat_lyrics'
    assert '/api/beat/lyrics' in data['route']

def test_workshop_ping(client):
    """Test workshop ping endpoint"""  
    response = client.get("/api/beat/ping")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert data['blueprint'] == 'beat_workshop'
    assert '/api/beat/workshop' in data['route']

def test_workshop_page_requires_auth(client):
    """Test workshop page requires authentication"""
    response = client.get("/api/beat/workshop")
    # Should redirect to login
    assert response.status_code == 302
    assert 'auth/login' in response.location

def test_midi_generation_requires_auth(client):
    """Test MIDI generation requires authentication"""
    response = client.post("/api/beat/midi", 
                          json={"bpm": 92, "genre": "trap"})
    # Should return 401 unauthorized
    assert response.status_code == 401
    data = response.get_json()
    assert 'Authentication required' in data['error']

def test_lyrics_analysis_requires_auth(client):
    """Test lyrics analysis requires authentication"""
    test_lyrics = """[Verse 1]
Started from the bottom now we here
Never gave up fighting through the fear
Built this empire brick by brick
Now they all watch our every trick

[Chorus] 
We rise up, never fall down
Kings and queens wear the crown
Nothing gonna stop us now
We make it happen somehow"""
    
    response = client.post("/api/beat/analyze_lyrics",
                          json={"lyrics": test_lyrics})
    # Should return 401 unauthorized
    assert response.status_code == 401
    
    data = response.get_json()
    assert data['success'] is False
    assert 'Authentication required' in data['error']

def test_workshop_analyze_requires_auth(client):
    """Test workshop analyze requires authentication"""  
    test_lyrics = """Working hard every single day
Building dreams in every way
Never stop until we make it
Success is ours for the taking"""
    
    response = client.post("/api/beat/workshop/analyze",
                          json={"lyrics": test_lyrics})
    # Should return 401 unauthorized
    assert response.status_code == 401
    
    data = response.get_json()
    assert 'Authentication required' in data['error']

def test_health_checks(client):
    """Test health check endpoints"""
    # Test healthz
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    
    # Test readyz  
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.get_json()
    assert data['ready'] is True
    
    # Test livez
    response = client.get("/livez")
    assert response.status_code == 200
    data = response.get_json()
    assert data['alive'] is True

def test_security_headers(client):
    """Test security headers are properly set"""
    response = client.get("/healthz")
    assert response.status_code == 200
    
    # Check security headers
    assert 'X-Content-Type-Options' in response.headers
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert 'Content-Security-Policy' in response.headers
    assert 'Referrer-Policy' in response.headers

def test_error_handling(client):
    """Test error handling for invalid requests"""
    # Empty lyrics (should require auth first)
    response = client.post("/api/beat/analyze_lyrics", json={})
    assert response.status_code == 401  # Auth required before validation
    
    # Invalid JSON (should require auth first) 
    response = client.post("/api/beat/workshop/analyze", 
                          data="invalid json",
                          content_type="application/json")
    assert response.status_code == 401  # Auth required before validation