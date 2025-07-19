# Use Node.js for frontend build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Use Python for backend
FROM python:3.9-alpine
WORKDIR /app

# Install minimal system dependencies for Python packages
RUN apk add --no-cache gcc musl-dev linux-headers

# Copy Python requirements and install with optimizations
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --only-binary=all --timeout=1000 -r requirements.txt || \
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