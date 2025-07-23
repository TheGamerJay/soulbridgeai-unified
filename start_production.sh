#!/bin/bash
# SoulBridge AI Production Startup Script

echo "🚀 Starting SoulBridge AI in Production Mode..."

# Set environment variables
export FLASK_ENV=production
export PYTHONPATH="$(pwd)/backend"

# Change to backend directory
cd backend

# Start with Gunicorn
echo "🔧 Starting Gunicorn server with optimized configuration..."
gunicorn --config ../gunicorn_config.py app_fixed:app

echo "✅ SoulBridge AI production server started!"