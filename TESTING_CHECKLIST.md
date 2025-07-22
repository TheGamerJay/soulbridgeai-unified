# SoulBridge AI Testing Checklist

## Critical User Flows - Test Before Each Deployment

### 🔐 Authentication Flow
- [ ] **Registration**: /auth/register accepts new user signup
- [ ] **Login**: /auth/login authenticates existing users  
- [ ] **Home Access**: After login, users go to chat app (not plans loop)
- [ ] **Logout**: /auth/logout clears session and redirects to login
- [ ] **Direct URL Access**: Auth URLs work when accessed directly

### 📊 Plan Selection
- [ ] **Plan Display**: Foundation, Premium, Enterprise plans show correct prices
- [ ] **Plan Selection**: Clicking plans successfully calls /api/select-plan
- [ ] **Backend Validation**: Plans use correct names (foundation/premium/enterprise)
- [ ] **Session Storage**: Selected plans persist in user session
- [ ] **No Undefined**: Plans don't show "undefined" in UI

### 💬 Chat Functionality  
- [ ] **Chat Access**: Authenticated users can access chat interface
- [ ] **Character Selection**: Blayzo, Sapphire, other characters work
- [ ] **Sapphire Image**: Correct blue Sapphire character displays (not Violet)
- [ ] **Message Sending**: Chat API accepts and responds to messages
- [ ] **Error Handling**: Failed requests show user-friendly errors

### 🛠️ Add-ons (if implemented)
- [ ] **Add-on Display**: Add-ons show correct information
- [ ] **Purchase Flow**: Add-on purchase process works
- [ ] **Activation**: Purchased add-ons activate properly

### 🌐 Core Routes
- [ ] **Health Check**: /health returns healthy status
- [ ] **Static Assets**: CSS, JS, images load correctly
- [ ] **Template Rendering**: All pages render without errors
- [ ] **Mobile Responsiveness**: App works on mobile devices

## Regression Prevention Rules

### 🚫 Before Making Changes
1. **Read this checklist** - Know what functionality must be preserved
2. **Test locally first** - Verify changes work in development
3. **Check dependencies** - Understand what your change might affect
4. **Review related code** - Look for similar patterns that might break

### ✅ After Making Changes  
1. **Test the specific feature** you changed
2. **Test related features** that might be affected
3. **Test basic user flows** from the checklist above
4. **Check browser console** for JavaScript errors
5. **Verify no "Method Not Allowed" errors** on any routes

### 🔍 Common Issues to Watch For
- **Route method mismatches** (GET vs POST)
- **Frontend/backend naming inconsistencies** 
- **Session data assumptions** that may not exist
- **Authentication bypass** in route logic
- **JavaScript undefined variables** from missing data
- **CSS/JS file loading failures**

## Quick Test Commands

```bash
# Check if routes respond correctly
curl -I https://www.soulbridgeai.com/health
curl -I https://www.soulbridgeai.com/login  
curl -I https://www.soulbridgeai.com/auth/register

# Check for JavaScript errors in browser console
# Navigate to each page and verify no red errors appear
```

## Recovery Protocol

If something breaks after deployment:
1. **Identify the specific issue** - What's broken?
2. **Check git log** - What was the last working commit?
3. **Revert if necessary** - `git revert <commit-hash>`
4. **Fix systematically** - Address root cause, not symptoms
5. **Test thoroughly** - Use this checklist before redeploying

---

**Remember**: It's better to deploy smaller, well-tested changes than large changes that break multiple systems.