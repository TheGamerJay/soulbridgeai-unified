# Google OAuth Setup Instructions

## Overview
This guide will help you set up Google OAuth authentication for SoulBridge AI, allowing users to sign in/sign up with their Google accounts.

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Select a project" → "New Project"
   - Project name: `SoulBridge AI OAuth`
   - Click "Create"

## Step 2: Enable Google+ API

1. **Navigate to APIs & Services**
   - In the left sidebar, click "APIs & Services" → "Library"
   
2. **Enable Required APIs**
   - Search for "Google+ API" and enable it
   - Search for "Google Identity" and enable it

## Step 3: Create OAuth Credentials

1. **Go to Credentials**
   - Click "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"

2. **Configure OAuth Consent Screen** (if prompted)
   - Choose "External" user type
   - Fill in required fields:
     - App name: `SoulBridge AI`
     - User support email: Your email
     - Developer contact: Your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users (your email) for development

3. **Create OAuth Client ID**
   - Application type: "Web application"
   - Name: `SoulBridge AI Web Client`
   - Authorized redirect URIs:
     - Development: `http://localhost:8080/auth/oauth/google/callback`
     - Production: `https://www.soulbridgeai.com/auth/oauth/google/callback`

4. **Save Credentials**
   - Copy the `Client ID` and `Client Secret`
   - Download the JSON file for backup

## Step 4: Set Environment Variables

### For Local Development:
```bash
export GOOGLE_CLIENT_ID="your-client-id-here"
export GOOGLE_CLIENT_SECRET="your-client-secret-here"
```

### For Railway Production:
1. Go to your Railway project dashboard
2. Click on your service → "Variables"
3. Add these environment variables:
   - `GOOGLE_CLIENT_ID`: Your Google Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google Client Secret

## Step 5: Test the Integration

1. **Local Testing**
   - Start your local server: `python backend/app_fixed.py`
   - Go to: `http://localhost:8080/login`
   - Click "Continue with Google" button
   - Complete Google authentication
   - Verify you're logged into the app

2. **Production Testing**
   - Deploy to Railway with environment variables set
   - Go to: `https://www.soulbridgeai.com/login`
   - Test Google OAuth flow

## Step 6: OAuth Consent Screen Setup (For Production)

1. **Configure OAuth Consent Screen for Production**
   - Go back to "OAuth consent screen"
   - Fill in all required information:
     - App logo (optional)
     - App privacy policy URL
     - App terms of service URL
   - Submit for verification (may take a few days)

## Security Features Implemented

✅ **CSRF Protection**: Uses state parameter to prevent CSRF attacks
✅ **Secure Redirects**: Validates redirect URIs
✅ **User Data Protection**: Only requests email and profile information
✅ **Error Handling**: Graceful fallback for OAuth failures
✅ **Auto Account Creation**: Seamlessly creates accounts for new users

## Troubleshooting

### Common Issues:

1. **"OAuth Error: Invalid Client"**
   - Check that `GOOGLE_CLIENT_ID` is set correctly
   - Verify the client ID matches your Google Cloud project

2. **"Redirect URI Mismatch"**
   - Ensure the callback URL in Google Cloud Console matches exactly:
     - `https://www.soulbridgeai.com/auth/oauth/google/callback`
   - No trailing slashes or extra parameters

3. **"OAuth Failed"**
   - Check that `GOOGLE_CLIENT_SECRET` is set correctly
   - Verify APIs are enabled in Google Cloud Console

4. **"Access Blocked"**
   - During development, add your test email to the OAuth consent screen
   - For production, complete the app verification process

### Debug Tips:

- Check Railway logs for OAuth error messages
- Verify environment variables are set in Railway dashboard
- Test OAuth flow in incognito/private browser window
- Ensure Google account has email verified

## Support

If you encounter issues:
1. Check the Railway deployment logs
2. Verify all environment variables are set correctly  
3. Test with different Google accounts
4. Check Google Cloud Console for any quota or API issues

---

**Note**: The OAuth implementation automatically handles both new user registration and existing user login with the same "Continue with Google" button, just like modern apps such as Discord, Slack, and GitHub.