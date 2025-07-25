# Railway PostgreSQL Setup Instructions

## ✅ Configuration Updated

Your `.env` files have been updated with the new Railway PostgreSQL configuration.

## 🔧 What You Need to Do

**IMPORTANT**: Update the password in your `.env` files:

### 1. Main .env file
Edit: `C:\Users\jaaye\OneDrive\Desktop\soulbridgeai-unified\.env`

Replace:
```env
PGPASSWORD=your_password_here
```

With your actual Railway PostgreSQL password.

### 2. Backend .env file  
Edit: `C:\Users\jaaye\OneDrive\Desktop\soulbridgeai-unified\backend\.env`

Replace:
```env
PGPASSWORD=your_password_here
```

With your actual Railway PostgreSQL password.

## 🗄️ Current Configuration

```env
PGHOST=shinkansen.proxy.rlwy.net
PGPORT=15522
PGUSER=postgres
PGPASSWORD=your_actual_password_here  # ← UPDATE THIS
PGDATABASE=railway
```

## 🧪 Test Database Connection

After updating the password, test the connection:

```bash
cd backend
python -c "
from dotenv import load_dotenv
from auth import Database
import os

load_dotenv()
print('Testing PostgreSQL connection...')
try:
    db = Database()
    print('✅ Database connection successful!')
    print(f'Using PostgreSQL: {db.use_postgres}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## 🚀 Railway Environment Variables

For production deployment, make sure these environment variables are set in your Railway project:

```env
PGHOST=shinkansen.proxy.rlwy.net
PGPORT=15522
PGUSER=postgres
PGPASSWORD=your_actual_password
PGDATABASE=railway
```

## ✅ What's Already Done

- ✅ Added environment variable loading to Flask app
- ✅ Updated .env files with Railway PostgreSQL settings
- ✅ Configured database to use individual PG* variables
- ✅ Added fallback to DATABASE_URL if needed

## 🔄 Next Steps

1. Update the password in both .env files
2. Test the database connection
3. Deploy to Railway with the new environment variables
4. Verify PostgreSQL connection in production