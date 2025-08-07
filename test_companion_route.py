#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'backend')
from app import app

with app.test_client() as client:
    # Simulate a logged-in user session
    with client.session_transaction() as sess:
        sess['user_authenticated'] = True
        sess['user_id'] = 1
        sess['user_email'] = 'test@example.com'
        sess['session_version'] = '2025-07-28-banking-security'
        sess['user_plan'] = 'free'
        sess['trial_active'] = False
        sess['terms_accepted'] = True  # Accept terms to avoid redirect
    
    response = client.get('/companion-selection')
    print(f'Status: {response.status_code}')
    if response.status_code != 200:
        print('Error response:')
        print(response.get_data(as_text=True))
    else:
        print('SUCCESS: Route works')
        # Check if template has proper data
        content = response.get_data(as_text=True)
        if 'netflix-card' in content:
            print('Netflix cards found in template')
        else:
            print('Netflix cards NOT found in template')
        
        if 'referral_count' in content.lower():
            print('Referral count variable found')
        else:
            print('Referral count variable NOT found')
            
        # Check what's actually in the content
        print('Content length:', len(content))
        print('First 500 chars:')
        print(content[:500])