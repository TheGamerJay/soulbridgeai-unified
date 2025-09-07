# 🚂 Railway Session Survival Setup

## Problem
Avatar persistence works but sessions get invalidated on every deploy, causing users to see 401 → fallback to default avatar.

## Solution: Set Stable FLASK_SECRET_KEY

### 1. Generate a Strong Secret Key

```bash
# Generate a 32-byte random key (256-bit)
python -c "import secrets; print(secrets.token_hex(32))"
# Example output: a1b2c3d4e5f6789...64-char hex string
```

### 2. Set in Railway Dashboard

1. Go to Railway dashboard → Your project
2. Click **Variables** tab  
3. Add new variable:
   - **Name**: `FLASK_SECRET_KEY`
   - **Value**: `your-64-character-hex-string-from-step-1`
4. Click **Add**
5. **Redeploy** your service

### 3. Verify Session Stability

After setting the key and deploying:

1. **Login** to your app
2. **Select an avatar** 
3. **Deploy again** (or wait for auto-deploy)
4. **Refresh page** - avatar should persist! 🎉

### 4. How It Works

**Before (broken):**
- No stable SECRET_KEY → Flask generates random key on each boot
- Deploy → new SECRET_KEY → all sessions invalidated  
- User loads page → 401 response → fallback to default avatar

**After (fixed):**
- Stable FLASK_SECRET_KEY from environment
- Deploy → same SECRET_KEY → sessions survive
- User loads page → 200 with saved avatar → persistence works!

### 5. Optional: Redis Sessions (for heavy traffic)

For high-traffic apps, use Redis for server-side sessions:

#### 5.1 Add Redis to Railway

1. Go to Railway dashboard → Your project
2. Click **+ New** → **Add Service** → **Database** 
3. Select **Redis**
4. Wait for deployment (creates `REDIS_URL` automatically)

#### 5.2 Verify Redis Configuration

The app already supports Redis sessions automatically:

```python
# Already implemented in app.py
redis_url = os.environ.get("REDIS_URL")
if redis_url:
    app.config.update(
        SESSION_TYPE="redis",
        SESSION_REDIS=redis.from_url(redis_url),
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX="soulbridge:",
    )
    Session(app)
```

#### 5.3 Benefits of Redis Sessions

- ✅ **Survives all deploys** - sessions stored externally
- ✅ **Scales across instances** - shared session storage  
- ✅ **Better performance** - faster than filesystem
- ✅ **Automatic fallback** - uses filesystem if Redis fails

## Security Notes

- ⚠️ **Never commit SECRET_KEY to Git**
- ✅ **Use environment variables only**  
- ✅ **Generate a new key per environment** (dev/staging/prod)
- ✅ **Use at least 32-byte (256-bit) entropy**

## Troubleshooting

**Still getting 401s after setting key?**
1. Check Railway logs: `railway logs`
2. Look for: `✅ FLASK_SECRET_KEY loaded successfully`  
3. Verify variable is set: Railway dashboard → Variables
4. Try hard refresh: Ctrl+Shift+R (clear cookies)

**Sessions work but avatar still resets?**
1. Check browser Network tab for `/community/avatar` response
2. Should return 200 with your saved JSON (not 401)
3. Check console for: `✅ Avatar loaded from database`