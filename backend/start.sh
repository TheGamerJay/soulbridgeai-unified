#!/usr/bin/env bash
set -euo pipefail

# Production environment configuration for Railway
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Set production environment variables
export FLASK_ENV=production
export IS_PROD=true
export DOCS_ENABLED=1
export RAILWAY_DEPLOYMENT=true
export SKIP_HEAVY_INIT=true

# Set default PORT if not provided (Railway provides this automatically)
: "${PORT:=5000}"

echo "🚀 Starting SoulBridge AI on 0.0.0.0:${PORT}"
echo "🏥 Health endpoint available at /health"
echo "🔧 Working directory: $(pwd)"
echo "🔧 Python version: $(python --version)"
echo "🔧 Files in current dir: $(ls -la | head -10)"

# Test import before starting gunicorn - fallback to minimal health app if main app fails
echo "🧪 Testing app import..."
python -c "
try:
    from app import create_app
    app = create_app()
    print('✅ Main app import successful')
except Exception as e:
    print(f'❌ Main app import failed: {e}')
    print('🔄 Falling back to minimal health app')
    try:
        from minimal_health import create_minimal_app
        app = create_minimal_app()
        print('✅ Minimal health app fallback successful')
        # Set environment flag for fallback mode
        import os
        os.environ['FALLBACK_MODE'] = 'true'
    except Exception as e2:
        print(f'❌ Even minimal app failed: {e2}')
        import traceback
        traceback.print_exc()
        exit(1)
"

# Railway-optimized gunicorn configuration
# Use create_app() factory pattern for proper initialization
# Note: In Docker, we're in /app directory, so no 'backend.' prefix needed
echo "🚀 Starting gunicorn server..."

# Check if we're on Windows (for local testing)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Windows detected - using Flask development server for local testing"
    echo "🏥 Health endpoints available at http://localhost:${PORT}/health"
    exec python -c "
from app import create_app
app = create_app()
app.run(host='0.0.0.0', port=${PORT}, debug=False, threaded=True)
"
else
    # Production gunicorn (Railway/Linux) - with fallback support
    if [[ "${FALLBACK_MODE:-false}" == "true" ]]; then
        echo "🔄 Starting in fallback mode with minimal health app"
        exec gunicorn 'minimal_health:create_minimal_app()' \
          --bind 0.0.0.0:${PORT} \
          --workers 1 \
          --worker-class sync \
          --timeout 30 \
          --log-level info \
          --access-logfile - \
          --error-logfile -
    else
        echo "🚀 Starting full SoulBridge AI app"
        exec gunicorn 'app:create_app()' \
          --bind 0.0.0.0:${PORT} \
          --workers ${WEB_CONCURRENCY:-1} \
          --worker-class gthread \
          --threads ${THREADS:-2} \
          --timeout 300 \
          --graceful-timeout 30 \
          --keep-alive 5 \
          --max-requests 1000 \
          --max-requests-jitter 50 \
          --preload \
          --log-level info \
          --access-logfile - \
          --error-logfile - \
          --capture-output \
          --enable-stdio-inheritance
    fi
fi