# docs.py
"""
Swagger UI documentation blueprint for SoulBridge AI Beat & Lyrics API
CSP-compliant implementation with session-based authentication
"""
import logging
from flask import Blueprint, Response, send_file, abort, session
from pathlib import Path
from swagger_ui_bundle import swagger_ui_path

logger = logging.getLogger(__name__)

docs_bp = Blueprint(
    "docs", __name__,
    static_folder=swagger_ui_path,      # serves swagger assets at /docs/static/*
    static_url_path="/docs/static", 
    url_prefix=""
)

SPEC_PATH = Path(__file__).parent / "openapi.yaml"

@docs_bp.before_request
def _docs_auth():
    """
    Protect docs with same session auth as /api/beat/* endpoints
    Only authenticated users can access API documentation
    """
    if not session.get("logged_in") or not session.get("user_id"):
        logger.warning(f"Unauthorized docs access attempt from {session}")
        abort(401)

@docs_bp.get("/openapi.yaml")
def openapi_yaml():
    """
    Serve OpenAPI specification file
    Served from same origin so CSP connect-src 'self' is satisfied
    """
    try:
        return send_file(SPEC_PATH, mimetype="application/yaml")
    except FileNotFoundError:
        logger.error(f"OpenAPI spec file not found at {SPEC_PATH}")
        abort(404)
    except Exception as e:
        logger.error(f"Error serving OpenAPI spec: {e}")
        abort(500)

@docs_bp.get("/docs")
def docs_index():
    """
    Swagger UI main page
    No inline scripts - stays compatible with CSP script-src 'self'
    Uses external JavaScript files to avoid CSP violations
    """
    html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>SoulBridge AI - Beat & Lyrics API Documentation</title>
    <meta name="description" content="Interactive API documentation for SoulBridge AI Beat & Lyrics endpoints"/>
    <link rel="stylesheet" href="/docs/static/swagger-ui.css"/>
    <style>
      html, body, #swagger-ui { 
        height: 100%; 
        margin: 0; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      .swagger-ui .topbar { 
        background-color: #1a1a2e; 
        border-bottom: 3px solid #16213e;
      }
      .swagger-ui .topbar .download-url-wrapper { display: none; }
      .swagger-ui .info { margin: 20px 0; }
      .swagger-ui .info .title { color: #16213e; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="/docs/static/swagger-ui-bundle.js"></script>
    <script src="/docs/init.js"></script>
  </body>
</html>"""
    return Response(html, mimetype="text/html")

@docs_bp.get("/docs/init.js")
def docs_init_js():
    """
    Swagger UI initialization script
    External JS file (not inline) so CSP script-src 'self' allows it
    Ensures session cookies are included in "Try it out" requests via requestInterceptor
    """
    js = """
// Initialize Swagger UI with SoulBridge AI configuration
window.ui = SwaggerUIBundle({
  url: "/openapi.yaml",
  dom_id: "#swagger-ui",
  layout: "BaseLayout",
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  presets: [
    SwaggerUIBundle.presets.apis,
    SwaggerUIBundle.SwaggerUIStandalonePreset
  ],
  plugins: [
    SwaggerUIBundle.plugins.DownloadUrl
  ],
  // Ensure session cookies are sent with all requests
  requestInterceptor: function(request) {
    request.credentials = 'include';
    
    // Add user-friendly headers
    if (!request.headers['User-Agent']) {
      request.headers['User-Agent'] = 'SoulBridge-API-Docs/1.0';
    }
    
    return request;
  },
  // Handle response errors gracefully
  responseInterceptor: function(response) {
    if (response.status === 401) {
      console.warn('Authentication required - please ensure you are logged in');
    } else if (response.status === 429) {
      console.warn('Rate limit exceeded - please wait before trying again');
    }
    return response;
  },
  // UI configuration
  docExpansion: 'list',
  defaultModelsExpandDepth: 2,
  defaultModelRendering: 'example',
  displayOperationId: false,
  displayRequestDuration: true,
  filter: false,
  showExtensions: false,
  showCommonExtensions: true,
  tryItOutEnabled: true,
  
  // Custom styling
  onComplete: function() {
    console.log('SoulBridge AI API Documentation loaded successfully');
    
    // Add custom header
    const header = document.createElement('div');
    header.innerHTML = '<h2 style="text-align: center; color: #16213e; margin: 20px;">🎵 SoulBridge AI - Beat & Lyrics API</h2>';
    const infoSection = document.querySelector('.swagger-ui .info');
    if (infoSection && infoSection.parentNode) {
      infoSection.parentNode.insertBefore(header, infoSection);
    }
  }
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
  // Ctrl/Cmd + K to focus search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    const searchBox = document.querySelector('.swagger-ui .filter-container input');
    if (searchBox) {
      searchBox.focus();
    }
  }
});

// Error handling for failed API spec loading
window.addEventListener('error', function(e) {
  if (e.message && e.message.includes('openapi')) {
    console.error('Failed to load API specification. Please check server status.');
  }
});
"""
    return Response(js, mimetype="application/javascript")

@docs_bp.get("/docs/health")
def docs_health():
    """
    Documentation service health check
    Returns status of docs service and API spec availability
    """
    try:
        spec_exists = SPEC_PATH.exists()
        swagger_ui_available = swagger_ui_path is not None
        
        return {
            "ok": True,
            "service": "SoulBridge API Documentation",
            "spec_available": spec_exists,
            "swagger_ui_available": swagger_ui_available,
            "spec_path": str(SPEC_PATH),
            "endpoints": [
                "/docs",
                "/openapi.yaml", 
                "/docs/health"
            ]
        }
    except Exception as e:
        logger.error(f"Docs health check failed: {e}")
        return {"ok": False, "error": str(e)}, 500

# Error handlers for docs blueprint
@docs_bp.errorhandler(401)
def docs_unauthorized(error):
    """Custom 401 handler for docs"""
    return Response("""
    <!DOCTYPE html>
    <html>
    <head><title>Authentication Required</title></head>
    <body>
        <h1>🔐 Authentication Required</h1>
        <p>Please <a href="/auth/login">log in</a> to access API documentation.</p>
        <p><a href="/">← Back to SoulBridge AI</a></p>
    </body>
    </html>
    """, status=401, mimetype="text/html")

@docs_bp.errorhandler(404)  
def docs_not_found(error):
    """Custom 404 handler for docs"""
    return Response("""
    <!DOCTYPE html>
    <html>
    <head><title>Documentation Not Found</title></head>
    <body>
        <h1>📚 Documentation Not Found</h1>
        <p>The requested documentation page could not be found.</p>
        <p><a href="/docs">← Back to API Documentation</a></p>
    </body>
    </html>
    """, status=404, mimetype="text/html")