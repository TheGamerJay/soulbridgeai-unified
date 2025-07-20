import pytest
import json

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    
    assert response.status_code == 200
    
    # Check if response is JSON
    data = json.loads(response.data)
    assert 'status' in data
    assert data['status'] == 'healthy'
    assert 'service' in data
    assert data['service'] == 'SoulBridge AI'

def test_health_endpoint_has_version(client):
    """Test that health endpoint includes version information."""
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert 'version' in data
    assert 'build_date' in data
    assert 'git_commit' in data