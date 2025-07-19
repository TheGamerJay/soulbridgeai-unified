#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

import sys
import os
import traceback

def test_import(module_name):
    try:
        if module_name == "models":
            from models import SoulBridgeDB
            print(f"✅ {module_name}: OK")
        elif module_name == "referral_system":
            from referral_system import referral_manager
            print(f"✅ {module_name}: OK")
        elif module_name == "openai":
            from openai import OpenAI
            print(f"✅ {module_name}: OK")
        elif module_name == "flask":
            from flask import Flask
            print(f"✅ {module_name}: OK")
        elif module_name == "stripe":
            import stripe
            print(f"✅ {module_name}: OK")
        else:
            __import__(module_name)
            print(f"✅ {module_name}: OK")
    except Exception as e:
        print(f"❌ {module_name}: FAILED - {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Python imports...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print("-" * 50)
    
    modules = [
        "flask", "openai", "stripe", "jwt", 
        "models", "referral_system"
    ]
    
    for module in modules:
        test_import(module)
    
    print("-" * 50)
    print("Import test complete")