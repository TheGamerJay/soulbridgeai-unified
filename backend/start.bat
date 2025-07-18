@echo off
echo Starting SoulBridge AI Backend...
echo.
echo Please make sure you have:
echo 1. Python 3.8+ installed
echo 2. Set your OPENAI_API_KEY in the .env file
echo.
pip install -r requirements.txt
echo.
echo Starting Flask server...
python app.py
pause
