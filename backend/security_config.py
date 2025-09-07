# security_config.py
"""
Security configuration and middleware for SoulBridge AI
Implements rate limiting, CSRF protection, and enhanced security headers
"""
import logging
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

logger = logging.getLogger(__name__)


def init_security(app):
    """Initialize all security measures for the Flask app"""

    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["120 per minute", "2000 per hour"],
        storage_uri="memory://"  # Use Redis in production: redis://localhost:6379
    )

    # CSRF Protection - disable for API endpoints
    # APIs should use session/JWT auth instead of CSRF tokens
    csrf = None  # Disable CSRF for now since we're using session auth for APIs

    # TODO: Enable CSRF for form-based routes only in production:
    # csrf = CSRFProtect(app)
    # csrf.exempt("api")  # Exempt all routes under /api/

    logger.info("✅ Security middleware initialized")
    return limiter, csrf


def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session

        # Check if user is authenticated
        if not session.get('logged_in') or not session.get('user_id'):
            logger.warning(f"Unauthorized access attempt to {request.endpoint}")
            return jsonify({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401

        return f(*args, **kwargs)
    return decorated_function


def enhance_security_headers(app):
    """Add comprehensive security headers"""

    @app.after_request
    def set_security_headers(response):
        """Enhanced security headers"""
        try:
            # Existing headers (keep these)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            # Remove deprecated X-XSS-Protection header

            # Enhanced Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://pagead2.googlesyndication.com https://www.googletagservices.com https://ep2.adtrafficquality.google https://www.gstatic.com https://js.stripe.com; "
                "worker-src 'self' blob:; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: blob: https:; "
                "media-src 'self' blob: data:; "
                "connect-src 'self' wss: https:; "
                "frame-src 'self' https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://ep2.adtrafficquality.google https://www.google.com https://js.stripe.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            response.headers['Content-Security-Policy'] = csp

            # Additional security headers
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = (
                'camera=(), microphone=(), geolocation=(), '
                'payment=*, usb=(), magnetometer=(), gyroscope=()'
            )

            # HSTS for HTTPS (only in production)
            if request.is_secure:
                response.headers['Strict-Transport-Security'] = (
                    'max-age=31536000; includeSubDomains'
                )

            # Content-Type charset for HTML responses
            if response.mimetype == 'text/html' and 'charset=' not in response.content_type:
                response.content_type = 'text/html; charset=utf-8'

            # Cache control for different content types
            if request.path.startswith('/api/'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
            elif request.path.startswith('/static/'):
                # Static assets should be cached for a year with immutable tag
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            elif response.mimetype in ('text/html', 'application/json'):
                # HTML and JSON responses should not be cached
                response.headers['Cache-Control'] = 'no-store'

            return response

        except Exception as e:
            logger.error(f"Error setting security headers: {e}")
            return response

    logger.info("✅ Enhanced security headers configured")


def secure_error_handlers(app):
    """Set up secure error handling that doesn't leak information"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Access forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):

        logger.error(f"Unexpected error: {str(error)}")

        # Security: Don't leak stack traces to users
        return jsonify({
            'error': 'An unexpected error occurred',
            'message': 'Please try again later'
        }), 500

    logger.info("✅ Secure error handlers configured")
