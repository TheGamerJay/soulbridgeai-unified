# SoulBridge AI - Stripe Payment Setup

## 🚀 Your payment system is now 95% complete!

### What's been implemented:
✅ **Stripe Checkout Session** - Professional payment flow  
✅ **Subscription Plans** - Monthly ($10) and Yearly ($100)  
✅ **Payment Success/Cancel** - Proper redirect handling  
✅ **Color Customization Unlock** - Premium features activation  
✅ **Environment Variable Support** - Secure key management  

### To make it 100% ready:

## Step 1: Get Your Stripe Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Create account if you don't have one
3. Get your test keys from **Developers > API Keys**:
   - `pk_test_...` (Publishable Key)
   - `sk_test_...` (Secret Key)

## Step 2: Create .env file

```bash
# Copy the template
cp .env.template .env
```

Then edit `.env` with your actual keys:

```bash
# Test Keys (for development)
STRIPE_SECRET_KEY=sk_test_your_actual_test_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_test_publishable_key_here

# Session Secret (generate a random string)
SESSION_SECRET=your-super-secret-random-string-here

# OpenAI (if you have one)
OPENAI_API_KEY=your-openai-key-here
```

## Step 3: Install Python Dependencies

```bash
pip install python-dotenv
```

## Step 4: Update app.py to load .env

Add this at the top of your app.py:

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file
```

## Step 5: Test the Flow

1. Start server: `python app.py`
2. Visit: `http://localhost:8080/subscription`
3. Click "🎨 Preview Color Studio" 
4. Click "🚀 Subscribe & Unlock Colors"
5. Use Stripe test card: `4242 4242 4242 4242`
6. Any expiry date in the future, any CVC

## Step 6: Go Live (when ready)

Replace test keys with live keys:
```bash
STRIPE_SECRET_KEY=sk_live_your_live_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key_here
```

## Test Cards for Development:
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **Require Authentication**: 4000 0025 0000 3155

## 🎉 You're ready for happy paying customers!

Your complete flow:
1. User sees color preview on subscription page
2. Clicks subscribe → Goes to Stripe checkout
3. Enters payment → Stripe processes securely
4. Redirects back → Premium features unlocked
5. User can customize colors → Happy customer!