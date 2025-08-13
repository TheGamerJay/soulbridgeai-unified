#!/usr/bin/env python3
"""
Test script for local AI integration with Flask app
"""
import requests
import json
import time

def test_local_ai_chat():
    """Test the local AI chat integration"""
    print("Testing Local AI Chat Integration...")
    
    # Base URL for local development
    base_url = "http://localhost:5000"
    
    # Create a session to maintain login
    session = requests.Session()
    
    try:
        # Step 1: Login with test credentials
        print("\n1. Testing login...")
        login_data = {
            "email": "test@soulbridge.ai",
            "password": "test123"
        }
        
        login_response = session.post(f"{base_url}/api/login", json=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print(f"Login success: {login_result.get('ok', False)}")
            print(f"User plan: {login_result.get('plan', 'unknown')}")
        else:
            print(f"Login failed: {login_response.text}")
            return
        
        # Step 2: Test chat with local AI (should use local AI for free users)
        print("\n2. Testing chat API with local AI...")
        chat_data = {
            "message": "Hello, I'm feeling stressed about work today. Can you help me?",
            "character": "Blayzo",
            "context": ""
        }
        
        print(f"Sending message: {chat_data['message']}")
        start_time = time.time()
        
        chat_response = session.post(f"{base_url}/api/chat", json=chat_data)
        response_time = time.time() - start_time
        
        print(f"Chat API status: {chat_response.status_code}")
        print(f"Response time: {response_time:.2f}s")
        
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            print(f"Chat success: {chat_result.get('success', False)}")
            print(f"AI Response: {chat_result.get('response', 'No response')}")
            print(f"User tier: {chat_result.get('tier', 'unknown')}")
            
            if 'local' in chat_result.get('response', '').lower():
                print("SUCCESS: Local AI is being used!")
            else:
                print("INFO: Response received (may be local AI or fallback)")
                
        else:
            print(f"Chat failed: {chat_response.text}")
        
        # Step 3: Test another message
        print("\n3. Testing second message...")
        chat_data2 = {
            "message": "What are some good ways to relax?",
            "character": "Blayzo",
            "context": ""
        }
        
        start_time = time.time()
        chat_response2 = session.post(f"{base_url}/api/chat", json=chat_data2)
        response_time2 = time.time() - start_time
        
        if chat_response2.status_code == 200:
            chat_result2 = chat_response2.json()
            print(f"Second response time: {response_time2:.2f}s")
            print(f"AI Response: {chat_result2.get('response', 'No response')}")
        
        print("\nTest completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Flask app. Make sure the server is running on localhost:5000")
        print("Start the server with: python app.py")
        
    except Exception as e:
        print(f"ERROR: {e}")

def test_local_ai_service_directly():
    """Test the local AI service directly"""
    print("\nTesting Local AI Service Directly...")
    
    try:
        from local_ai_service import get_local_ai_service
        
        ai_service = get_local_ai_service()
        
        # Test messages
        test_messages = [
            ("Hello, how are you?", "Blayzo"),
            ("I'm feeling stressed about work", "Blayzo"),
            ("Can you give me some advice?", "Blayzo")
        ]
        
        for i, (message, character) in enumerate(test_messages, 1):
            print(f"\nTest {i}: {message}")
            
            start_time = time.time()
            result = ai_service.generate_response(message, character)
            response_time = time.time() - start_time
            
            print(f"Success: {result['success']}")
            print(f"Response: {result['response']}")
            print(f"Time: {response_time:.2f}s")
            
            if not result['success']:
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Show stats
        stats = ai_service.get_stats()
        print(f"\nService Stats: {stats}")
        
    except Exception as e:
        print(f"Direct test error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("LOCAL AI INTEGRATION TEST")
    print("=" * 50)
    
    # Test local AI service directly first
    test_local_ai_service_directly()
    
    # Test via Flask API
    test_local_ai_chat()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)