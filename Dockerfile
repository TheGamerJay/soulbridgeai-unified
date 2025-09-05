# Use Python 3.13 slim image for SoulBridge AI
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    pkg-config \
    libffi-dev \
    libssl-dev \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for predictable builds and network reliability
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=5

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .

# Install dependencies with robust retry and fallback logic
RUN python -m pip install --upgrade pip --timeout 300 --retries 5
RUN pip install -r requirements.txt --timeout 300 --retries 5 --default-timeout=100 || \
    (echo "First attempt failed, trying with different PyPI mirror..." && \
     pip install -r requirements.txt --timeout 300 --retries 5 --index-url https://pypi.org/simple/) || \
    (echo "Second attempt failed, trying individual packages..." && \
     pip install --timeout 300 --retries 5 flask flask-socketio python-socketio eventlet openai gunicorn)

# Copy backend application
COPY backend/ .

# Create necessary directories
RUN mkdir -p static/uploads static/logos

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port (Railway will provide actual port via $PORT env var)
EXPOSE 5000

# Make start script executable
RUN chmod +x start.sh

# Use Gunicorn via start.sh for production
CMD ["./start.sh"]