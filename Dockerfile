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

# Environment variables for predictable builds
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .

# Install torch first with CPU index (avoids resolver conflicts)
RUN pip install --upgrade pip \
 && pip install --extra-index-url https://download.pytorch.org/whl/cpu \
      torch==2.1.0+cpu torchaudio==2.1.0+cpu \
 && pip install -r requirements.txt

# Copy backend application
COPY backend/ .

# Create necessary directories
RUN mkdir -p static/uploads static/logos

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose Flask port
EXPOSE 8080

# Make start script executable
RUN chmod +x start.sh

# Use Python directly for simplicity
CMD ["python", "app.py"]