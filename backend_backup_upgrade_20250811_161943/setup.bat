@echo off
echo.
echo ===============================================
echo       SoulBridge AI Backend Setup
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python is installed
python --version

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo ✅ pip is available

:: Install dependencies
echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

:: Check .env file
if not exist ".env" (
    echo ❌ .env file not found
    echo Creating .env file...
    copy nul .env
    echo OPENAI_API_KEY=your_openai_api_key_here >> .env
    echo SESSION_SECRET=your_session_secret_here >> .env
    echo PORT=5000 >> .env
)

echo.
echo ===============================================
echo            Setup Complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Edit the .env file and add your OpenAI API key
echo 2. Run 'python app.py' or double-click 'start.bat'
echo.
pause
