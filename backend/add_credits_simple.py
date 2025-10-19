"""
Simple script to add artistic credits to all users (for testing)
"""
import logging
from database_utils import get_database, format_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_credits_to_all_users(amount=500):
    """Add artistic credits to all users in database"""
    try:
        db = get_database()
        if not db:
            logger.error("Database connection failed")
            return False

        conn = db.get_connection()
        cursor = conn.cursor()

        # Get all users
        cursor.execute(format_query("SELECT id, email, artistic_credits FROM users"))
        users = cursor.fetchall()

        if not users:
            logger.error("No users found in database")
            conn.close()
            return False

        logger.info(f"\nFound {len(users)} users:")
        for user in users:
            user_id, email, current_credits = user
            current_credits = current_credits or 0
            logger.info(f"  - User {user_id}: {email} (current credits: {current_credits})")

        # Add credits to all users
        for user in users:
            user_id, email, current_credits = user
            current_credits = current_credits or 0
            new_balance = current_credits + amount

            cursor.execute(format_query("""
                UPDATE users SET artistic_credits = ? WHERE id = ?
            """), (new_balance, user_id))

            logger.info(f"Updated user {user_id} ({email}): {current_credits} -> {new_balance}")

        conn.commit()
        conn.close()

        logger.info(f"\nSuccessfully added {amount} credits to {len(users)} users!")
        return True

    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\nAdding 500 artistic credits to all users...\n")
    success = add_credits_to_all_users(500)

    if success:
        print("\nSuccess! All users now have 500 additional artistic credits.\n")
    else:
        print("\nFailed to add credits.\n")
