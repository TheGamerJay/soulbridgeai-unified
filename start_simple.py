#!/usr/bin/env python3
"""
Simplified app starter
"""
import os
import sys
import subprocess

# Set environment for Unicode handling
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# Change to project directory
os.chdir('C:/Users/jaaye/OneDrive/Desktop/soulbridgeai-unified')

print("Starting SoulBridge AI server...")

# Start the app in a subprocess to avoid Unicode import issues
try:
    result = subprocess.run([
        sys.executable, 
        'backend/app.py'
    ], 
    cwd='C:/Users/jaaye/OneDrive/Desktop/soulbridgeai-unified',
    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
    capture_output=False,
    text=True,
    encoding='utf-8',
    errors='replace'
    )
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error: {e}")