#!/usr/bin/env python3
"""
Simple Tier Testing Server - SoulBridge AI
"""

from flask import Flask, session, jsonify, redirect

app = Flask(__name__)
app.secret_key = 'tier_test_secret_key_123'

# Simple tier constants  
FREE_LIMITS = {"decoder": 3, "fortune": 2, "horoscope": 3}
PREMIUM_LIMITS = {"decoder": 15, "fortune": 8, "horoscope": 10}
MAX_LIMITS = {"decoder": None, "fortune": None, "horoscope": None}
TIER_LIMITS = {"foundation": FREE_LIMITS, "premium": PREMIUM_LIMITS, "enterprise": MAX_LIMITS}

@app.route("/")
@app.route("/tier-test")
def tier_test_page():
    """Main tier testing page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tier System Tester - SoulBridge AI</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 30px; background: #000; color: #fff; }
            .container { max-width: 900px; margin: auto; }
            .tier-card { background: #1a1a1a; padding: 25px; margin: 20px 0; border-radius: 15px; border: 2px solid #22d3ee; }
            .tier-card.gold { border-color: #fbbf24; }
            .tier-card.silver { border-color: #22c55e; }
            .tier-card.bronze { border-color: #ef4444; }
            .test-btn { background: #22d3ee; color: #000; padding: 12px 25px; margin: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; }
            .test-btn.gold { background: #fbbf24; }
            .test-btn.silver { background: #22c55e; }
            .test-btn.bronze { background: #ef4444; color: #fff; }
            .test-btn:hover { opacity: 0.8; transform: translateY(-2px); }
            .result { background: #2a2a2a; padding: 15px; margin: 15px 0; border-radius: 8px; font-family: monospace; font-size: 13px; }
            h1 { color: #22d3ee; text-align: center; margin-bottom: 10px; }
            h2 { color: #fbbf24; margin-bottom: 15px; }
            .status { background: #065f46; color: #ecfdf5; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .feature-links { margin-top: 20px; padding: 15px; background: #2563eb; border-radius: 10px; }
            .feature-links a { color: #fff; text-decoration: none; margin: 0 15px; font-weight: bold; }
            .feature-links a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Tier System Tester</h1>
            <p style="text-align: center; color: #94a3b8; margin-bottom: 30px;">
                Test the SoulBridge AI tier system - manually upgrade to test Growth and Max tiers!
            </p>
            
            <div id="current-status" class="status">
                Current Tier: <span id="current-tier">Loading...</span>
            </div>
            
            <!-- Max Tier -->
            <div class="tier-card gold">
                <h2>Max Tier (Enterprise)</h2>
                <p><strong>Unlimited access</strong> to all features - decoder, fortune teller, horoscope</p>
                <button class="test-btn gold" onclick="upgradeTo('enterprise')">Upgrade to Gold Tier</button>
                <button class="test-btn" onclick="testLimits('enterprise')">Test Max Limits</button>
                <div id="enterprise-result" class="result" style="display: none;"></div>
            </div>
            
            <!-- Growth Tier -->  
            <div class="tier-card silver">
                <h2>Growth Tier (Premium)</h2>
                <p><strong>Enhanced limits:</strong> 15 decodes, 8 fortunes, 10 horoscopes per day</p>
                <button class="test-btn silver" onclick="upgradeTo('premium')">Upgrade to Silver Tier</button>
                <button class="test-btn" onclick="testLimits('premium')">Test Growth Limits</button>
                <div id="premium-result" class="result" style="display: none;"></div>
            </div>
            
            <!-- Free Tier -->
            <div class="tier-card bronze">
                <h2>Free Tier (Foundation)</h2>
                <p><strong>Basic limits:</strong> 3 decodes, 2 fortunes, 3 horoscopes per day</p>
                <button class="test-btn bronze" onclick="upgradeTo('foundation')">Reset to Bronze Tier</button>
                <button class="test-btn" onclick="testLimits('foundation')">Test Free Limits</button>
                <div id="foundation-result" class="result" style="display: none;"></div>
            </div>
            
            <!-- Feature Links -->
            <div class="feature-links">
                <strong>After upgrading, test these features:</strong>
                <a href="http://127.0.0.1:8080/decoder" target="_blank">Decoder</a>
                <a href="http://127.0.0.1:8080/fortune" target="_blank">Fortune Teller</a>
                <a href="http://127.0.0.1:8080/horoscope" target="_blank">Horoscope</a>
            </div>
        </div>

        <script>
            // Get current tier status on page load
            getCurrentTier();
            
            async function getCurrentTier() {
                try {
                    const response = await fetch('/current-tier');
                    const result = await response.json();
                    document.getElementById('current-tier').textContent = 
                        result.current_plan || 'Not Set';
                } catch (error) {
                    document.getElementById('current-tier').textContent = 'Error loading';
                }
            }
            
            async function upgradeTo(tier) {
                try {
                    const response = await fetch(`/upgrade-to/${tier}`, { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('current-tier').textContent = tier;
                        alert(`Successfully upgraded to ${tier} tier! Now test the features.`);
                        
                        // Auto-test the limits
                        setTimeout(() => testLimits(tier), 500);
                    } else {
                        alert(`Upgrade failed: ${result.error}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                }
            }
            
            async function testLimits(tier) {
                try {
                    const response = await fetch(`/test-limits/${tier}`);
                    const result = await response.json();
                    
                    const resultDiv = document.getElementById(`${tier}-result`);
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                } catch (error) {
                    const resultDiv = document.getElementById(`${tier}-result`);
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<div style="color: #ef4444;">Error: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.route("/current-tier")
def get_current_tier():
    """Get current tier from session"""
    return jsonify({
        "success": True,
        "current_plan": session.get('user_plan', 'Not Set'),
        "session_data": dict(session)
    })

@app.route("/upgrade-to/<tier>", methods=["POST"])
def upgrade_to_tier(tier):
    """Upgrade user to specified tier"""
    try:
        # Set up session like a logged-in user
        session['user_authenticated'] = True
        session['user_email'] = 'tester@soulbridgeai.com'
        session['user_id'] = 'tier_test_user'
        session['user_plan'] = tier
        session['display_name'] = f'Tier Tester ({tier.title()})'
        session.permanent = True
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": f"Successfully upgraded to {tier} tier",
            "tier": tier,
            "session_created": True
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/test-limits/<tier>")
def test_tier_limits(tier):
    """Test limits for a specific tier"""
    try:
        # Ensure session is set for this tier
        session['user_plan'] = tier
        session['user_authenticated'] = True
        session['user_id'] = 'tier_test_user'
        
        # Calculate limits using the same logic as main app
        limits = {}
        for feature in ['decoder', 'fortune', 'horoscope']:
            limit = TIER_LIMITS.get(tier, TIER_LIMITS["foundation"]).get(feature)
            limits[feature] = limit
        
        # Determine display plan
        if tier == 'enterprise':
            display_plan = 'enterprise'
        elif tier == 'premium':
            display_plan = 'premium'
        else:
            display_plan = 'bronze'
        
        return jsonify({
            "success": True,
            "tier": tier,
            "display_plan": display_plan,
            "limits": limits,
            "unlimited": tier == 'enterprise',
            "note": f"This shows what {tier} users should see"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    print("Starting Tier Testing Server...")
    print("Visit: http://127.0.0.1:5001/tier-test")
    print("This lets you test Growth and Max tiers!")
    print("-" * 50)
    app.run(host='127.0.0.1', port=5001, debug=False)