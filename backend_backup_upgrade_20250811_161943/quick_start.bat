@echo off
echo ==========================================
echo  SoulBridge AI - Quick Start
echo ==========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python not found!
    echo Please install Python from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo.
echo ✅ Python found! Installing dependencies...
pip install flask openai python-dotenv flask-sqlalchemy gunicorn email-validator psycopg2-binary requests flask-mail reportlab flask-cors itsdangerous

echo.
if not exist .env (
    echo ⚠️  .env file not found! Copy .env.example to .env and edit your secrets.
    pause
)

echo 🚀 Starting SoulBridge AI Backend...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
pause
