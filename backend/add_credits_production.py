"""
Add artistic credits to production Railway database
Run with: railway run python add_credits_production.py <user_id> <amount>
"""
import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_credits_to_production(user_id, amount):
    """Add artistic credits to user in production PostgreSQL database"""
    try:
        # Get DATABASE_URL from environment (Railway sets this)
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL not found. Make sure to run with: railway run python add_credits_production.py")
            return False

        logger.info(f"Connecting to production database...")

        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if user exists
        cursor.execute("SELECT id, email, artistic_credits FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            logger.error(f"User {user_id} not found in production database")
            conn.close()
            return False

        current_credits = user['artistic_credits'] or 0
        new_balance = current_credits + amount

        logger.info(f"User found: {user['email']}")
        logger.info(f"Current credits: {current_credits}")
        logger.info(f"Adding: {amount}")
        logger.info(f"New balance: {new_balance}")

        # Update credits
        cursor.execute("""
            UPDATE users SET artistic_credits = %s WHERE id = %s
        """, (new_balance, user_id))

        conn.commit()
        conn.close()

        logger.info(f"✅ Successfully added {amount} credits to user {user_id} in production!")
        logger.info(f"   {user['email']}: {current_credits} -> {new_balance}")
        return True

    except Exception as e:
        logger.error(f"❌ Error adding credits to production: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: railway run python add_credits_production.py <user_id> [amount]")
        print("Example: railway run python add_credits_production.py 104 500\n")
        sys.exit(1)

    user_id = int(sys.argv[1])
    amount = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print(f"\n🚀 Adding {amount} artistic credits to user {user_id} in PRODUCTION...\n")
    success = add_credits_to_production(user_id, amount)

    if success:
        print(f"\n✅ Success! User {user_id} now has {amount} additional credits in production!\n")
        print("🌐 Refresh your website to see the updated credits.\n")
    else:
        print("\n❌ Failed to add credits to production.\n")
