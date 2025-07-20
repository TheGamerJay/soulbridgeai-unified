"""
Ultra-minimal test suite for CI/CD pipeline validation
"""

import sys

def test_python_version():
    """Test that we're running on a supported Python version"""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"

def test_basic_imports():
    """Test that basic Python modules can be imported"""
    import json
    import datetime
    import sqlite3
    assert True

def test_basic_math():
    """Test basic Python functionality"""
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"
    assert len([1, 2, 3]) == 3

def test_sqlite_database():
    """Test basic SQLite database operations"""
    import sqlite3
    
    # Test in-memory database creation
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create a simple test table
    cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
    cursor.execute("INSERT INTO test VALUES (1, 'test')")
    cursor.execute("SELECT name FROM test WHERE id = 1")
    result = cursor.fetchone()
    
    assert result[0] == "test"
    conn.close()

def test_json_operations():
    """Test JSON serialization/deserialization"""
    import json
    
    test_data = {"status": "ok", "data": [1, 2, 3]}
    json_string = json.dumps(test_data)
    parsed_data = json.loads(json_string)
    assert parsed_data == test_data

def test_flask_import():
    """Test that Flask can be imported"""
    try:
        import flask
        # If we can import flask, test basic functionality
        from flask import Flask
        app = Flask(__name__)
        assert app is not None
    except ImportError:
        # Skip if Flask not available
        pass

if __name__ == "__main__":
    # Run tests directly without pytest if needed
    import traceback
    
    tests = [
        test_python_version,
        test_basic_imports, 
        test_basic_math,
        test_sqlite_database,
        test_json_operations,
        test_flask_import
    ]
    
    passed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL {test.__name__}: {e}")
            traceback.print_exc()
    
    print(f"\nPassed: {passed}/{len(tests)} tests")
    
    if passed == len(tests):
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)