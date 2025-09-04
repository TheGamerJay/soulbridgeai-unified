# tests/test_docs.py
"""
Tests for the API documentation system (Swagger UI)
Verifies authentication, CSP compliance, and functionality
"""
import pytest
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app import create_app

@pytest.fixture
def app():
    """Create test app with docs enabled"""
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test_secret_key")
    # Ensure docs are enabled for testing
    os.environ["DOCS_ENABLED"] = "1"
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def authenticated_client(app):
    """Create authenticated test client"""
    client = app.test_client()
    with client.session_transaction() as session:
        session['logged_in'] = True
        session['user_id'] = 1
        session['email'] = 'test@example.com'
    return client

class TestDocsAuthentication:
    """Test authentication requirements for docs endpoints"""
    
    def test_docs_index_requires_auth(self, client):
        """Test that /docs requires authentication"""
        response = client.get("/docs")
        assert response.status_code == 401
        assert b"Authentication Required" in response.data

    def test_openapi_spec_requires_auth(self, client):
        """Test that /openapi.yaml requires authentication"""  
        response = client.get("/openapi.yaml")
        assert response.status_code == 401

    def test_docs_health_requires_auth(self, client):
        """Test that /docs/health requires authentication"""
        response = client.get("/docs/health")
        assert response.status_code == 401

    def test_docs_init_js_requires_auth(self, client):
        """Test that /docs/init.js requires authentication"""
        response = client.get("/docs/init.js")
        assert response.status_code == 401

class TestDocsAuthenticated:
    """Test docs functionality with authentication"""

    def test_docs_index_authenticated(self, authenticated_client):
        """Test docs main page renders with authentication"""
        response = authenticated_client.get("/docs")
        assert response.status_code == 200
        assert response.content_type.startswith("text/html")
        
        # Check for Swagger UI elements
        content = response.get_data(as_text=True)
        assert "swagger-ui.css" in content
        assert "swagger-ui-bundle.js" in content
        assert "/docs/init.js" in content
        assert "SoulBridge AI - Beat & Lyrics API Documentation" in content
        assert "swagger-ui" in content  # Main div ID

    def test_openapi_spec_authenticated(self, authenticated_client):
        """Test OpenAPI spec is served with authentication"""
        response = authenticated_client.get("/openapi.yaml")
        assert response.status_code == 200
        assert response.content_type.startswith("application/yaml")
        
        # Check OpenAPI spec content
        content = response.get_data(as_text=True)
        assert "openapi: 3.1.0" in content
        assert "SoulBridge AI" in content
        assert "/api/beat/lyrics" in content
        assert "/api/beat/workshop" in content
        assert "/api/beat/midi" in content

    def test_docs_init_js_authenticated(self, authenticated_client):
        """Test Swagger UI initialization JavaScript"""
        response = authenticated_client.get("/docs/init.js")
        assert response.status_code == 200
        assert response.content_type.startswith("application/javascript")
        
        # Check JavaScript content
        content = response.get_data(as_text=True)
        assert "SwaggerUIBundle" in content
        assert "credentials: 'include'" in content  # Ensures cookies sent
        assert "/openapi.yaml" in content
        assert "requestInterceptor" in content
        assert "responseInterceptor" in content

    def test_docs_health_authenticated(self, authenticated_client):
        """Test docs health check endpoint"""
        response = authenticated_client.get("/docs/health")
        assert response.status_code == 200
        assert response.content_type == "application/json"
        
        data = response.get_json()
        assert data["ok"] is True
        assert data["service"] == "SoulBridge API Documentation"
        assert "spec_available" in data
        assert "swagger_ui_available" in data
        assert "endpoints" in data
        
        # Check expected endpoints are listed
        endpoints = data["endpoints"]
        assert "/docs" in endpoints
        assert "/openapi.yaml" in endpoints
        assert "/docs/health" in endpoints

class TestDocsContent:
    """Test the content and structure of documentation"""

    def test_openapi_spec_structure(self, authenticated_client):
        """Test OpenAPI specification has correct structure"""
        response = authenticated_client.get("/openapi.yaml")
        content = response.get_data(as_text=True)
        
        # Check major sections exist
        assert "info:" in content
        assert "servers:" in content
        assert "security:" in content
        assert "tags:" in content
        assert "paths:" in content
        assert "components:" in content
        
        # Check authentication scheme
        assert "cookieAuth:" in content
        assert "securitySchemes:" in content
        
        # Check major endpoints documented
        assert "/api/beat/lyrics:" in content
        assert "/api/beat/workshop:" in content
        assert "/api/beat/midi:" in content
        assert "/api/beat/analyze_lyrics:" in content

    def test_openapi_spec_schemas(self, authenticated_client):
        """Test OpenAPI spec includes proper schemas"""
        response = authenticated_client.get("/openapi.yaml")
        content = response.get_data(as_text=True)
        
        # Check important schemas are defined
        assert "LyricsAnalysisRequest:" in content
        assert "LyricsAnalysisResponse:" in content
        assert "MidiGenerationRequest:" in content
        assert "PingResponse:" in content
        assert "Error:" in content
        
        # Check response definitions
        assert "Unauthorized:" in content
        assert "TooManyRequests:" in content
        assert "ServerError:" in content

class TestDocsCSPCompliance:
    """Test Content Security Policy compliance"""

    def test_no_inline_scripts(self, authenticated_client):
        """Test that docs page has no inline scripts (CSP compliance)"""
        response = authenticated_client.get("/docs")
        content = response.get_data(as_text=True)
        
        # Should not contain inline script tags
        assert "<script>" not in content.lower()
        assert "javascript:" not in content.lower()
        assert "onclick=" not in content.lower()
        assert "onload=" not in content.lower()
        
        # Should reference external script files
        assert 'src="/docs/static/swagger-ui-bundle.js"' in content
        assert 'src="/docs/init.js"' in content

    def test_external_css_only(self, authenticated_client):
        """Test that only external CSS is used (CSP compliance)"""
        response = authenticated_client.get("/docs")
        content = response.get_data(as_text=True)
        
        # Should reference external CSS
        assert 'href="/docs/static/swagger-ui.css"' in content
        
        # Inline styles in <style> tags are allowed and minimal
        # (they don't violate CSP like inline event handlers)
        style_count = content.count("<style>")
        assert style_count <= 1  # Only one style block expected

class TestDocsErrorHandling:
    """Test error handling in docs blueprint"""

    def test_docs_404_handler(self, authenticated_client):
        """Test custom 404 handler for docs"""
        response = authenticated_client.get("/docs/nonexistent")
        assert response.status_code == 404
        assert b"Documentation Not Found" in response.data
        assert b"Back to API Documentation" in response.data

    def test_docs_401_custom_response(self, client):
        """Test custom 401 response for docs"""
        response = client.get("/docs")
        assert response.status_code == 401
        assert b"Authentication Required" in response.data
        assert b"log in" in response.data
        assert b"Back to SoulBridge AI" in response.data

class TestDocsEnvironmentToggle:
    """Test environment-based enabling/disabling of docs"""

    def test_docs_can_be_disabled(self):
        """Test that docs can be disabled via environment variable"""
        # Set docs disabled
        os.environ["DOCS_ENABLED"] = "0"
        
        try:
            app = create_app()
            app.config.update(TESTING=True)
            
            with app.test_client() as client:
                with client.session_transaction() as session:
                    session['logged_in'] = True
                    session['user_id'] = 1
                
                # Docs should not be available
                response = client.get("/docs")
                assert response.status_code == 404
                
                response = client.get("/openapi.yaml")
                assert response.status_code == 404
                
        finally:
            # Reset for other tests
            os.environ["DOCS_ENABLED"] = "1"

    def test_docs_enabled_by_default_in_dev(self):
        """Test that docs are enabled by default in development"""
        # Don't set DOCS_ENABLED, should default to enabled in non-prod
        if "DOCS_ENABLED" in os.environ:
            del os.environ["DOCS_ENABLED"]
            
        try:
            app = create_app()
            app.config.update(TESTING=True)
            
            # Check if docs blueprint was registered by trying to access it
            with app.test_client() as client:
                with client.session_transaction() as session:
                    session['logged_in'] = True
                    session['user_id'] = 1
                
                response = client.get("/docs")
                # Should be accessible (200) not missing (404)
                assert response.status_code == 200
                
        finally:
            # Reset for other tests
            os.environ["DOCS_ENABLED"] = "1"

class TestDocsIntegration:
    """Integration tests for docs with the actual API"""

    def test_swagger_ui_cookie_integration(self, authenticated_client):
        """Test that Swagger UI will send cookies with requests"""
        response = authenticated_client.get("/docs/init.js")
        content = response.get_data(as_text=True)
        
        # Check that request interceptor sets credentials to include
        assert "credentials: 'include'" in content
        
        # Check that interceptor is configured
        assert "requestInterceptor:" in content
        assert "responseInterceptor:" in content

    def test_docs_references_correct_endpoints(self, authenticated_client):
        """Test that documented endpoints actually exist"""
        # Get the OpenAPI spec
        spec_response = authenticated_client.get("/openapi.yaml")
        spec_content = spec_response.get_data(as_text=True)
        
        # Extract some documented paths and verify they exist
        documented_paths = [
            "/api/beat/ping",
            "/api/beat/lyrics/ping", 
            "/api/beat/workshop",
            "/api/beat/midi"
        ]
        
        for path in documented_paths:
            assert path in spec_content
            
            # Try to access the endpoint (most will return 401 due to missing auth,
            # but they should exist and not return 404)
            response = authenticated_client.get(path)
            assert response.status_code != 404, f"Documented endpoint {path} returned 404"