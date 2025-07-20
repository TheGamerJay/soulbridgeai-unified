from flask import Flask, render_template, request, jsonify
import stripe
import os

app = Flask(__name__)

# Configure Stripe - use test keys for now
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "your_stripe_test_key_here")


@app.route("/")
def home():
    return "Test server is working!"


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/subscription")
def subscription():
    return render_template("subscription.html")


@app.route("/customization")
def customization():
    return render_template("color_studio.html")


@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    """Create a Stripe PaymentIntent"""
    try:
        data = request.get_json()
        amount = data.get("amount", 1000)  # Default to $10

        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount, currency="usd", automatic_payment_methods={"enabled": True}
        )

        return jsonify({"clientSecret": intent.client_secret})

    except Exception as e:
        return jsonify({"error": str(e), "test_url": "/test-payment-success"}), 500


@app.route("/test-payment-success")
def test_payment_success():
    """Test route to simulate successful payment"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Payment Success</title></head>
    <body style="background: #000; color: #22d3ee; font-family: Arial; padding: 2rem; text-align: center;">
        <h1>🎉 Payment Successful!</h1>
        <p>Your SoulBridge Plus subscription is now active.</p>
        <p><strong>Test Mode:</strong> This is a simulated payment.</p>
        <br>
        <script>
            // Set premium access flags
            localStorage.setItem('soulbridge_payment_confirmed', 'true');
            localStorage.setItem('soulbridge_subscription', 'plus');
            localStorage.setItem('isPremium', 'true');
            
            // Redirect to subscription page with success
            setTimeout(() => {
                window.location.href = '/subscription?success=true&session_id=test_session_123';
            }, 2000);
        </script>
    </body>
    </html>
    """


@app.route("/test")
def test():
    return "Test route works!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)
