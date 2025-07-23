@echo off
echo 🚀 Starting SoulBridge AI in Production Mode (Windows)...

REM Set environment variables
set FLASK_ENV=production
set PYTHONPATH=%cd%\backend

REM Change to backend directory
cd backend

REM Start with Waitress (Windows-compatible production server)
echo 🔧 Starting Waitress server with optimized configuration...
waitress-serve --host=0.0.0.0 --port=8080 --threads=8 --connection-limit=1000 --cleanup-interval=30 --channel-timeout=120 app_fixed:app

echo ✅ SoulBridge AI production server started!