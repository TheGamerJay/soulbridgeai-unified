#!/usr/bin/env python3
"""
Simple authentication system test
"""
import os
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

# Use the same configuration as in db.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///soulbridge.db")
print(f"Using database: {DATABASE_URL}")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create Base and User model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False, default="User")  # Required field
    user_plan = Column(String, nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def setup_test_user():
    """Create test user in the database"""
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        print("Database tables created/verified")
        
        with SessionLocal() as db:
            # Create test user
            test_email = "test@soulbridge.ai"
            test_password = "test123"
            
            # Check if user exists
            existing_user = db.query(User).filter(User.email == test_email).first()
            if existing_user:
                print(f"Test user {test_email} already exists")
                return test_email, test_password
            
            # Create new user
            password_hash = generate_password_hash(test_password)
            new_user = User(
                email=test_email,
                password_hash=password_hash,
                display_name="Test User",
                user_plan="max"
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"Created test user: {test_email} with password: {test_password}")
            print(f"   User ID: {new_user.id}")
            return test_email, test_password
            
    except Exception as e:
        print(f"Database error: {e}")
        return None, None

def verify_user_login(email, password):
    """Verify user can login with credentials"""
    try:
        from werkzeug.security import check_password_hash
        
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"User {email} not found")
                return False
                
            if not check_password_hash(user.password_hash, password):
                print(f"Invalid password for {email}")
                return False
                
            print(f"Login credentials verified for {email}")
            return True
            
    except Exception as e:
        print(f"Login verification error: {e}")
        return False

if __name__ == "__main__":
    print("Setting up authentication test...")
    
    email, password = setup_test_user()
    if email and password:
        print("\nTesting login verification...")
        if verify_user_login(email, password):
            print(f"\nAuthentication system is ready!")
            print(f"   Test user: {email}")
            print(f"   Test password: {password}")
            print(f"   You can now test the /api/login endpoint")
        else:
            print("Authentication verification failed")
    else:
        print("Failed to set up test user")