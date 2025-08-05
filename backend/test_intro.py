#!/usr/bin/env python3
import traceback
try:
    from app import app
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
            sess['user_plan'] = 'free'
            sess['user_authenticated'] = True
            sess['session_version'] = '2025-07-28-banking-security'  # Required for auth
            sess['effective_plan'] = 'free'
            sess['trial_active'] = False
        
        response = client.get('/intro')
        print(f'Status: {response.status_code}')
        if response.status_code != 200:
            print(f'Response data: {response.get_data(as_text=True)[:500]}')
        else:
            print('Intro page loads successfully!')
            
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()