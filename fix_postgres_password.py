#!/usr/bin/env python3
"""
Script to fix PostgreSQL password in Railway database
This needs to run from Railway environment to access postgres.railway.internal
"""
import os
import sys

# Check if we're in Railway environment
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    print("❌ This script must run in Railway environment")
    print("💡 Deploy this to Railway and run it there")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 not available")
    sys.exit(1)

def fix_postgres_password():
    # Get the DATABASE_URL from Railway environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ No DATABASE_URL found")
        return False
        
    print(f"🔗 Using DATABASE_URL: {database_url[:50]}...")
    
    try:
        # Try to connect with the current credentials
        print("🔐 Attempting to connect to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Change the postgres user password
        new_password = "Yar1el_2025_Secure!"
        print(f"🔑 Changing postgres user password to: {new_password}")
        
        cursor.execute(
            sql.SQL("ALTER USER postgres PASSWORD %s"),
            [new_password]
        )
        
        print("✅ Password changed successfully!")
        
        cursor.close()
        conn.close()
        
        # Test the new connection
        print("🧪 Testing new connection...")
        test_url = database_url.replace(
            database_url.split('@')[0].split(':')[-1], 
            new_password
        )
        
        test_conn = psycopg2.connect(test_url)
        test_conn.close()
        print("✅ New password verified!")
        
        return True
        
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            print("❌ Password authentication failed - the current password in DATABASE_URL is wrong")
            print("💡 The PostgreSQL database password is different from what Railway thinks it is")
            return False
        else:
            print(f"❌ Connection error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PostgreSQL Password Fix Tool")
    print("=" * 40)
    
    success = fix_postgres_password()
    
    if success:
        print("\n🎉 Password fix completed successfully!")
        print("🔄 Now redeploy your main service for the changes to take effect.")
    else:
        print("\n💥 Password fix failed.")
        print("🔄 You may need to recreate the PostgreSQL service.")