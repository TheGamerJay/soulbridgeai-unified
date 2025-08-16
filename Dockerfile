# Use Python 3.11 slim image for SoulBridge AI
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
CMD ["python", "app_fixed.py"]