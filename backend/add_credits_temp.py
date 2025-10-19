"""
Temporary script to add artistic credits for testing
"""
import logging
import sys
from database_utils import get_database, format_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_artistic_credits(user_id, amount):
    """Add artistic credits to user account"""
    try:
        db = get_database()
        if not db:
            logger.error("Database connection failed")
            return False

        conn = db.get_connection()
        cursor = conn.cursor()

        # First check if user exists in new credit system
        cursor.execute(format_query("""
            SELECT credits_remaining FROM user_credits WHERE user_id = ?
        """), (user_id,))

        result = cursor.fetchone()

        if result:
            # Update new system
            current_credits = result[0] or 0
            new_balance = current_credits + amount

            cursor.execute(format_query("""
                UPDATE user_credits SET credits_remaining = ? WHERE user_id = ?
            """), (new_balance, user_id))

            # Add to ledger
            cursor.execute(format_query("""
                INSERT INTO credit_ledger (user_id, delta, reason, metadata)
                VALUES (?, ?, ?, ?)
            """), (user_id, amount, 'admin_test_credits', '{}'))

            conn.commit()
            logger.info(f"✅ Added {amount} credits to user {user_id} (new system): {current_credits} -> {new_balance}")
        else:
            # Update old system (artistic_credits column)
            cursor.execute(format_query("""
                SELECT artistic_credits FROM users WHERE id = ?
            """), (user_id,))

            result = cursor.fetchone()
            if not result:
                logger.error(f"User {user_id} not found")
                conn.close()
                return False

            current_credits = result[0] or 0
            new_balance = current_credits + amount

            cursor.execute(format_query("""
                UPDATE users SET artistic_credits = ? WHERE id = ?
            """), (new_balance, user_id))

            conn.commit()
            logger.info(f"Added {amount} credits to user {user_id} (old system): {current_credits} -> {new_balance}")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error adding credits: {e}")
        return False

if __name__ == "__main__":
    # Get user ID from command line or use default
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    amount = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print(f"\nAdding {amount} artistic credits to user {user_id}...\n")
    success = add_artistic_credits(user_id, amount)

    if success:
        print(f"\nSuccessfully added {amount} credits!\n")
    else:
        print(f"\nFailed to add credits\n")
