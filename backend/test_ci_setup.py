#!/usr/bin/env python3
"""
CI/CD Setup Test Script
Tests that all critical components can be imported and basic functionality works
"""

import sys
import os
import sqlite3
from datetime import datetime

def test_basic_imports():
    """Test basic Python imports"""
    print("Testing basic imports...")
    
    try:
        import flask
        import sqlite3
        import json
        import uuid
        import datetime
        print("+ Basic imports successful")
        return True
    except ImportError as e:
        print(f"- Basic import failed: {e}")
        return False

def test_app_imports():
    """Test application imports"""
    print("Testing application imports...")
    
    try:
        # Set environment for testing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret'
        
        from app import app
        print("+ Flask app imports successfully")
        
        # Test app creation
        with app.app_context():
            print("+ Flask app context works")
        
        return True
    except Exception as e:
        print(f"- App import failed: {e}")
        return False

def test_notification_system():
    """Test notification system imports"""
    print("Testing notification system...")
    
    try:
        from notification_system import NotificationManager, NotificationTemplate, NotificationType
        from notification_api import notifications_api
        from notification_scheduler import NotificationScheduler
        
        # Test basic functionality
        manager = NotificationManager()
        notification = NotificationTemplate.mood_check_in('test_user')
        
        print("+ Notification system imports and basic functionality work")
        return True
    except Exception as e:
        print(f"- Notification system failed: {e}")
        return False

def test_business_intelligence():
    """Test business intelligence imports"""
    print("Testing business intelligence...")
    
    try:
        from business_intelligence import BusinessIntelligenceManager
        from data_visualization import DataVisualizationManager
        from admin_dashboard import admin_dashboard
        
        # Test basic functionality
        bi_manager = BusinessIntelligenceManager()
        viz_manager = DataVisualizationManager()
        
        print("+ Business intelligence imports and basic functionality work")
        return True
    except Exception as e:
        print(f"- Business intelligence failed: {e}")
        return False

def test_security_components():
    """Test security components"""
    print("Testing security components...")
    
    try:
        from security_manager import SecurityManager
        from security_monitor import SecurityMonitor
        from security_alerts import SecurityAlertManager
        
        print("+ Security components import successfully")
        return True
    except Exception as e:
        print(f"- Security components failed: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("Testing database operations...")
    
    try:
        # Test SQLite operations
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Test notification database schema
        from notification_api import init_notification_database
        init_notification_database(conn)
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if len(tables) >= 3:  # Should have at least 3 notification tables
            print(f"+ Database operations successful - {len(tables)} tables created")
            conn.close()
            return True
        else:
            print(f"- Database operations failed - only {len(tables)} tables created")
            conn.close()
            return False
            
    except Exception as e:
        print(f"- Database operations failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    print("Testing health endpoint...")
    
    try:
        os.environ['FLASK_ENV'] = 'testing'
        from app import app
        
        with app.test_client() as client:
            response = client.get('/health')
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('status') == 'healthy':
                    print("+ Health endpoint works correctly")
                    return True
                else:
                    print("- Health endpoint returned incorrect data")
                    return False
            else:
                print(f"- Health endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"- Health endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("CI/CD Setup Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_app_imports,
        test_notification_system,
        test_business_intelligence,
        test_security_components,
        test_database_operations,
        test_health_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"- Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 50)
    
    if passed == total:
        print("SUCCESS: All tests passed! CI/CD setup is ready.")
        sys.exit(0)
    else:
        print(f"FAILED: {total - passed} tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()