"""
Create password_reset_tokens table if it doesn't exist
"""
import logging
from auth import Database

logger = logging.getLogger(__name__)

def create_password_reset_tokens_table():
    """Create the password_reset_tokens table if it doesn't exist"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            # PostgreSQL version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    request_ip TEXT NULL,
                    request_ua TEXT NULL
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)")
        else:
            # SQLite version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    request_ip TEXT NULL,
                    request_ua TEXT NULL
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Password reset tokens table created/verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create password_reset_tokens table: {e}")
        return False

if __name__ == "__main__":
    # Can be run directly to create the table
    logging.basicConfig(level=logging.INFO)
    success = create_password_reset_tokens_table()
    if success:
        print("✅ Password reset tokens table created successfully")
    else:
        print("❌ Failed to create password reset tokens table")