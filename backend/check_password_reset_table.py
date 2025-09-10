"""
Check the actual structure of the password_reset_tokens table
"""
import logging
from auth import Database

logger = logging.getLogger(__name__)

def check_password_reset_table_structure():
    """Check what columns actually exist in the password_reset_tokens table"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            # PostgreSQL: Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'password_reset_tokens'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("PostgreSQL password_reset_tokens columns:")
            for col_name, col_type in columns:
                print(f"  {col_name}: {col_type}")
                
            # Also check if table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'password_reset_tokens'
            """)
            table_exists = cursor.fetchone()
            print(f"Table exists: {bool(table_exists)}")
            
        else:
            # SQLite: Check table structure  
            cursor.execute("PRAGMA table_info(password_reset_tokens)")
            columns = cursor.fetchall()
            print("SQLite password_reset_tokens columns:")
            for col_info in columns:
                print(f"  {col_info[1]}: {col_info[2]}")  # name: type
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking table structure: {e}")

if __name__ == "__main__":
    check_password_reset_table_structure()