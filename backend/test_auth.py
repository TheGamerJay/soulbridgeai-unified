#!/usr/bin/env python3
"""
Test script for the new PostgreSQL authentication system
"""
import os
import sys
import requests
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

# Create Base and User model directly in test script to avoid import issues
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="max")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def setup_test_database():
    """Create test user in the database"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/ministudio")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    
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
            plan="max"
        )
        
        db.add(new_user)
        db.commit()
        print(f"Created test user: {test_email} with password: {test_password}")
        return test_email, test_password

def test_login(email, password, base_url="http://localhost:5000"):
    """Test the login endpoint"""
    print(f"\n🔍 Testing login with {email}")
    
    session = requests.Session()
    
    # Test login
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = session.post(f"{base_url}/api/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("ok"):
            print("✅ Login successful!")
            
            # Test accessing protected endpoint
            protected_response = session.get(f"{base_url}/mini-studio")
            print(f"Protected endpoint status: {protected_response.status_code}")
            
            if protected_response.status_code == 200:
                print("✅ Can access protected endpoint!")
            else:
                print("❌ Cannot access protected endpoint")
            
            # Test logout
            logout_response = session.post(f"{base_url}/api/logout")
            print(f"Logout response: {logout_response.json()}")
            
            if logout_response.json().get("ok"):
                print("✅ Logout successful!")
            else:
                print("❌ Logout failed")
                
        else:
            print("❌ Login failed!")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    print("🧪 Setting up test database and user...")
    email, password = setup_test_database()
    
    print("\n🚀 Testing authentication system...")
    test_login(email, password)