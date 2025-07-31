#!/usr/bin/env python3
"""
Script to create user account in production PostgreSQL database
"""
import os
import bcrypt
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_production_user():
    """Create user account in production PostgreSQL database"""
    try:
        # Database connection details
        host = "shinkansen.proxy.rlwy.net"
        port = 15522
        user = "postgres"
        password = os.environ.get("PGPASSWORD")
        database = "railway"
        
        if not password or "your_postgres_password_here" in password:
            print("❌ PostgreSQL password not configured properly in .env")
            print("Please set PGPASSWORD in your .env file")
            return False
        
        # Connect to database
        print(f"Connecting to PostgreSQL at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Users table doesn't exist. Run database initialization first.")
            return False
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"Users table columns: {[col[0] for col in columns]}")
        
        # Check if user already exists
        email = "dagamerjay13@gmail.com"
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"✅ User {email} already exists with ID: {existing_user[0]}")
            return True
        
        # Create password hash
        password_hash = bcrypt.hashpw("Yariel13".encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        
        # Insert user (handle both with and without plan_type column)
        has_plan_type = 'plan_type' in [col[0] for col in columns]
        
        if has_plan_type:
            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, plan_type, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (email, password_hash, "GamerJay", "foundation", True))
        else:
            cursor.execute("""
                INSERT INTO users (email, password_hash, display_name, email_verified, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (email, password_hash, "GamerJay", True))
        
        conn.commit()
        
        # Get the created user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
        
        print(f"✅ User created successfully!")
        print(f"   Email: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Display Name: GamerJay")
        print(f"   Plan Type: {'foundation' if has_plan_type else 'not set (column missing)'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating production user account...")
    success = create_production_user()
    if success:
        print("✅ Production user account ready!")
    else:
        print("❌ Failed to create production user account")