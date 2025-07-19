# Use Node.js for frontend build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Use Python for backend
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies with timeout settings
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python requirements and install with optimizations
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout=1000 -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set Python path to include backend directory
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Copy Google verification file to build directory
COPY frontend/public/googlea4d68d68f81c1843.html ./frontend/build/

# Expose port
EXPOSE 8080

# Copy and set up start script
COPY start.sh .
RUN chmod +x start.sh

# Start command
CMD ["./start.sh"]