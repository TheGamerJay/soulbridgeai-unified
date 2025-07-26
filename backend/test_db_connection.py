#!/usr/bin/env python3
"""
Quick database connection test to diagnose PostgreSQL issues
"""
import os
import sys

# Test 1: Check environment variables
print("=== DATABASE ENVIRONMENT CHECK ===")
database_url = os.environ.get('DATABASE_URL')
postgres_url = os.environ.get('POSTGRES_URL')

print(f"DATABASE_URL present: {bool(database_url)}")
if database_url:
    # Mask the password for security
    masked_url = database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://')[-1]
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
                masked_url = masked_url.replace(f':{password}@', ':***@')
    print(f"DATABASE_URL: {masked_url}")

print(f"POSTGRES_URL present: {bool(postgres_url)}")

# Test individual PG variables
pg_vars = ['PGHOST', 'PGUSER', 'PGPASSWORD', 'PGDATABASE', 'PGPORT']
print("\nIndividual PostgreSQL variables:")
for var in pg_vars:
    value = os.environ.get(var)
    if var == 'PGPASSWORD' and value:
        print(f"{var}: ***")
    else:
        print(f"{var}: {value}")

# Test 2: Try importing PostgreSQL driver
print("\n=== POSTGRESQL DRIVER CHECK ===")
try:
    import psycopg2
    print("✅ psycopg2 imported successfully")
    print(f"psycopg2 version: {psycopg2.__version__}")
except ImportError as e:
    print(f"❌ psycopg2 import failed: {e}")
    sys.exit(1)

# Test 3: Try connecting to database
print("\n=== DATABASE CONNECTION TEST ===")
if database_url:
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        print(f"Public tables count: {table_count}")
        
        cursor.close()
        conn.close()
        print("✅ Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'pgcode'):
            print(f"PostgreSQL error code: {e.pgcode}")
        sys.exit(1)
else:
    print("❌ No DATABASE_URL found")
    sys.exit(1)

print("\n✅ All database tests passed!")