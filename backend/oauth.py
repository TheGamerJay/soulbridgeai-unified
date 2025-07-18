# OAuth Integration for Google and Facebook
import os
import secrets
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
from flask import request, session, redirect, url_for, jsonify

class OAuthManager:
    def __init__(self, db):
        self.db = db
        
        # OAuth configurations
        self.oauth_configs = {
            'google': {
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            },
            'facebook': {
                'client_id': os.environ.get('FACEBOOK_CLIENT_ID'),
                'client_secret': os.environ.get('FACEBOOK_CLIENT_SECRET'),
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'user_info_url': 'https://graph.facebook.com/v18.0/me',
                'scope': 'email public_profile'
            }
        }
    
    def get_auth_url(self, provider, redirect_uri):
        """Generate OAuth authorization URL"""
        try:
            if provider not in self.oauth_configs:
                return {'success': False, 'error': 'Invalid OAuth provider'}
            
            config = self.oauth_configs[provider]
            
            if not config['client_id'] or not config['client_secret']:
                return {'success': False, 'error': f'{provider.title()} OAuth not configured'}
            
            # Generate state token for CSRF protection
            state_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(minutes=10)
            
            # Store state token
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO oauth_states (state_token, provider, redirect_url, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', (state_token, provider, redirect_uri, expires_at))
                conn.commit()
            
            # Build authorization URL
            params = {
                'client_id': config['client_id'],
                'redirect_uri': redirect_uri,
                'scope': config['scope'],
                'response_type': 'code',
                'state': state_token
            }
            
            if provider == 'google':
                params['access_type'] = 'offline'
                params['prompt'] = 'consent'
            
            auth_url = f"{config['auth_url']}?{urlencode(params)}"
            
            return {'success': True, 'auth_url': auth_url, 'state': state_token}
            
        except Exception as e:
            logging.error(f"Error generating OAuth URL for {provider}: {e}")
            return {'success': False, 'error': 'Failed to generate authorization URL'}
    
    def handle_callback(self, provider, code, state, redirect_uri):
        """Handle OAuth callback"""
        try:
            # Verify state token
            if not self._verify_state_token(state, provider):
                return {'success': False, 'error': 'Invalid state token'}
            
            # Exchange code for access token
            token_result = self._exchange_code_for_token(provider, code, redirect_uri)
            if not token_result['success']:
                return token_result
            
            access_token = token_result['access_token']
            
            # Get user info from OAuth provider
            user_info_result = self._get_user_info(provider, access_token)
            if not user_info_result['success']:
                return user_info_result
            
            user_info = user_info_result['user_info']
            
            # Create or get existing user
            user_result = self._create_or_get_oauth_user(provider, user_info)
            
            # Clean up state token
            self._cleanup_state_token(state)
            
            return user_result
            
        except Exception as e:
            logging.error(f"Error handling OAuth callback for {provider}: {e}")
            return {'success': False, 'error': 'OAuth authentication failed'}
    
    def _verify_state_token(self, state_token, provider):
        """Verify OAuth state token"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM oauth_states 
                    WHERE state_token = ? AND provider = ? AND expires_at > CURRENT_TIMESTAMP
                ''', (state_token, provider))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logging.error(f"Error verifying state token: {e}")
            return False
    
    def _exchange_code_for_token(self, provider, code, redirect_uri):
        """Exchange authorization code for access token"""
        try:
            config = self.oauth_configs[provider]
            
            data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            response = requests.post(config['token_url'], data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            if 'access_token' not in token_data:
                return {'success': False, 'error': 'No access token received'}
            
            return {'success': True, 'access_token': token_data['access_token']}
            
        except requests.RequestException as e:
            logging.error(f"Error exchanging code for token: {e}")
            return {'success': False, 'error': 'Failed to exchange authorization code'}
    
    def _get_user_info(self, provider, access_token):
        """Get user information from OAuth provider"""
        try:
            config = self.oauth_configs[provider]
            
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {}
            
            if provider == 'facebook':
                params['fields'] = 'id,name,email,picture'
            
            response = requests.get(config['user_info_url'], headers=headers, params=params)
            response.raise_for_status()
            
            user_data = response.json()
            
            # Normalize user data across providers
            if provider == 'google':
                user_info = {
                    'id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture'),
                    'verified_email': user_data.get('verified_email', False)
                }
            elif provider == 'facebook':
                user_info = {
                    'id': user_data.get('id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture', {}).get('data', {}).get('url'),
                    'verified_email': True  # Facebook emails are considered verified
                }
            
            return {'success': True, 'user_info': user_info}
            
        except requests.RequestException as e:
            logging.error(f"Error getting user info from {provider}: {e}")
            return {'success': False, 'error': 'Failed to get user information'}
    
    def _create_or_get_oauth_user(self, provider, user_info):
        """Create or get existing OAuth user"""
        try:
            from auth import User
            user_manager = User(self.db)
            
            # Check if user exists by OAuth ID
            existing_user = user_manager.get_user_by_oauth(provider, user_info['id'])
            
            if existing_user:
                # Update last login
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', 
                                 (existing_user['id'],))
                    conn.commit()
                
                return {'success': True, 'user': existing_user, 'is_new_user': False}
            
            # Check if user exists by email
            if user_info.get('email'):
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, email, display_name FROM users WHERE email = ?', 
                                 (user_info['email'],))
                    email_user = cursor.fetchone()
                    
                    if email_user:
                        # Link OAuth account to existing email user
                        cursor.execute('''
                            UPDATE users SET oauth_provider = ?, oauth_id = ?, profile_picture_url = ?, 
                                   email_verified = TRUE, last_login = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (provider, user_info['id'], user_info.get('picture'), email_user['id']))
                        conn.commit()
                        
                        return {
                            'success': True, 
                            'user': dict(email_user), 
                            'is_new_user': False,
                            'linked_account': True
                        }
            
            # Create new user
            result = user_manager.create_user(
                email=user_info.get('email'),
                display_name=user_info.get('name'),
                oauth_provider=provider,
                oauth_id=user_info['id'],
                profile_picture_url=user_info.get('picture')
            )
            
            if result['success']:
                # Mark email as verified for OAuth users
                if user_info.get('verified_email'):
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('UPDATE users SET email_verified = TRUE WHERE id = ?', 
                                     (result['user_id'],))
                        conn.commit()
                
                # Get user data
                user_data = user_manager.get_user_by_id(result['user_id'])
                return {'success': True, 'user': user_data, 'is_new_user': True}
            
            return result
            
        except Exception as e:
            logging.error(f"Error creating/getting OAuth user: {e}")
            return {'success': False, 'error': 'Failed to process user account'}
    
    def _cleanup_state_token(self, state_token):
        """Clean up used state token"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM oauth_states WHERE state_token = ?', (state_token,))
                conn.commit()
        except Exception as e:
            logging.error(f"Error cleaning up state token: {e}")
    
    def is_provider_configured(self, provider):
        """Check if OAuth provider is configured"""
        if provider not in self.oauth_configs:
            return False
        
        config = self.oauth_configs[provider]
        return bool(config['client_id'] and config['client_secret'])
    
    def get_configured_providers(self):
        """Get list of configured OAuth providers"""
        configured = []
        for provider in self.oauth_configs:
            if self.is_provider_configured(provider):
                configured.append(provider)
        return configured
