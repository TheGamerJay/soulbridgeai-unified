"""
Environment validation for SoulBridge AI
Ensures all required environment variables are set and valid
"""

import os
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validates environment variables and configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_required_env_var(self, name: str, description: str = "") -> bool:
        """Validate that a required environment variable is set"""
        value = os.environ.get(name)
        if not value:
            self.errors.append(f"Missing required environment variable: {name} - {description}")
            return False
        self.info.append(f"✓ {name} is set")
        return True
    
    def validate_optional_env_var(self, name: str, description: str = "") -> bool:
        """Validate optional environment variable and warn if missing"""
        value = os.environ.get(name)
        if not value:
            self.warnings.append(f"Optional environment variable not set: {name} - {description}")
            return False
        self.info.append(f"✓ {name} is set")
        return True
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None
    
    def validate_api_key(self, key: str, min_length: int = 20) -> bool:
        """Validate API key format"""
        return len(key) >= min_length and key.replace('-', '').replace('_', '').isalnum()
    
    def validate_database_url(self, url: str) -> bool:
        """Validate database URL format"""
        postgres_pattern = r'^postgres(ql)?://[^:]+:[^@]+@[^/]+/[^?]+(\?.+)?$'
        return re.match(postgres_pattern, url) is not None
    
    def validate_port(self, port_str: str) -> bool:
        """Validate port number"""
        try:
            port = int(port_str)
            return 1 <= port <= 65535
        except ValueError:
            return False
    
    def run_validation(self) -> Tuple[bool, Dict]:
        """Run comprehensive environment validation"""
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Critical environment variables
        self.validate_required_env_var("SECRET_KEY", "Flask session secret key")
        
        # Database
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            if not self.validate_database_url(db_url):
                self.errors.append("DATABASE_URL format is invalid (should be postgresql://user:pass@host/db)")
            else:
                self.info.append("✓ DATABASE_URL format is valid")
        else:
            self.validate_optional_env_var("DATABASE_URL", "PostgreSQL connection string")
        
        # OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            if not openai_key.startswith("sk-"):
                self.errors.append("OPENAI_API_KEY format is invalid (should start with 'sk-')")
            elif len(openai_key) < 40:
                self.errors.append("OPENAI_API_KEY appears too short")
            else:
                self.info.append("✓ OPENAI_API_KEY format is valid")
        else:
            self.validate_required_env_var("OPENAI_API_KEY", "Required for AI chat functionality")
        
        # Stripe
        stripe_secret = os.environ.get("STRIPE_SECRET_KEY")
        stripe_public = os.environ.get("STRIPE_PUBLIC_KEY")
        
        if stripe_secret:
            if not stripe_secret.startswith("sk_"):
                self.errors.append("STRIPE_SECRET_KEY format is invalid (should start with 'sk_')")
            else:
                self.info.append("✓ STRIPE_SECRET_KEY format is valid")
        else:
            self.validate_optional_env_var("STRIPE_SECRET_KEY", "Required for payment processing")
        
        if stripe_public:
            if not stripe_public.startswith("pk_"):
                self.errors.append("STRIPE_PUBLIC_KEY format is invalid (should start with 'pk_')")
            else:
                self.info.append("✓ STRIPE_PUBLIC_KEY format is valid")
        else:
            self.validate_optional_env_var("STRIPE_PUBLIC_KEY", "Required for payment processing")
        
        # Email configuration
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = os.environ.get("SMTP_PORT")
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if smtp_server and smtp_port and smtp_user and smtp_pass:
            if not self.validate_port(smtp_port):
                self.errors.append("SMTP_PORT is not a valid port number")
            if not self.validate_email(smtp_user):
                self.errors.append("SMTP_USER is not a valid email address")
            if len(smtp_pass) < 8:
                self.warnings.append("SMTP_PASS appears very short")
            self.info.append("✓ SMTP configuration appears complete")
        else:
            self.validate_optional_env_var("SMTP_SERVER", "Email server hostname")
            self.validate_optional_env_var("SMTP_PORT", "Email server port (usually 587)")
            self.validate_optional_env_var("SMTP_USER", "Email username")
            self.validate_optional_env_var("SMTP_PASS", "Email password")
        
        # SendGrid
        sendgrid_key = os.environ.get("SENDGRID_API_KEY")
        if sendgrid_key:
            if not sendgrid_key.startswith("SG."):
                self.warnings.append("SENDGRID_API_KEY format unusual (should start with 'SG.')")
            else:
                self.info.append("✓ SENDGRID_API_KEY format is valid")
        else:
            self.validate_optional_env_var("SENDGRID_API_KEY", "Alternative email service")
        
        # Redis (for rate limiting)
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            if not self.validate_url(redis_url):
                self.warnings.append("REDIS_URL format appears invalid")
            else:
                self.info.append("✓ REDIS_URL format is valid")
        else:
            self.validate_optional_env_var("REDIS_URL", "Required for production rate limiting")
        
        # Railway specific
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            self.info.append("✓ Running on Railway")
            if not os.environ.get("PORT"):
                self.warnings.append("PORT not set, Railway may have issues")
        
        # Development vs Production
        if os.environ.get("PRODUCTION") or os.environ.get("RAILWAY_ENVIRONMENT"):
            self.info.append("✓ Production environment detected")
            if os.environ.get("SECRET_KEY") == "dev-secret-key":
                self.errors.append("Using development SECRET_KEY in production!")
        else:
            self.info.append("✓ Development environment detected")
        
        # Security headers
        if not os.environ.get("SESSION_SECRET"):
            self.warnings.append("SESSION_SECRET not set, using SECRET_KEY fallback")
        
        # JWT for admin
        if not os.environ.get("JWT_SECRET"):
            self.warnings.append("JWT_SECRET not set, using SECRET_KEY fallback")
        
        # Check for common security issues
        secret_key = os.environ.get("SECRET_KEY", "")
        if secret_key and len(secret_key) < 32:
            self.warnings.append("SECRET_KEY is shorter than recommended (32+ characters)")
        
        if secret_key == "your-secret-key-here" or secret_key == "change-me":
            self.errors.append("SECRET_KEY is using default/placeholder value!")
        
        # Summary
        is_valid = len(self.errors) == 0
        
        result = {
            "valid": is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "critical_services": {
                    "database": bool(os.environ.get("DATABASE_URL")),
                    "openai": bool(os.environ.get("OPENAI_API_KEY")),
                    "stripe": bool(os.environ.get("STRIPE_SECRET_KEY")),
                    "email": bool(os.environ.get("SMTP_SERVER") or os.environ.get("SENDGRID_API_KEY")),
                    "redis": bool(os.environ.get("REDIS_URL"))
                }
            }
        }
        
        # Log results
        if is_valid:
            logger.info("Environment validation passed")
        else:
            logger.error(f"Environment validation failed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        for warning in self.warnings:
            logger.warning(f"  - {warning}")
        
        return is_valid, result

# Global validator instance
env_validator = EnvironmentValidator()

def validate_environment() -> Tuple[bool, Dict]:
    """Validate the current environment"""
    return env_validator.run_validation()

def init_environment_validation(app):
    """Initialize environment validation for Flask app"""
    
    @app.route("/debug/env-check")
    def env_check():
        """Debug endpoint to check environment configuration"""
        # Only allow in development or for admins
        if not (app.debug or os.environ.get("TEST_MODE")):
            return jsonify({"error": "Not available in production"}), 403
        
        is_valid, result = validate_environment()
        return jsonify(result)
    
    # Run validation on startup
    is_valid, result = validate_environment()
    
    if not is_valid:
        logger.warning("Starting with environment validation errors - check /debug/env-check")
    
    logger.info("Environment validation initialized")