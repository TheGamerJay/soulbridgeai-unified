# Tests for Security Manager
import pytest
from unittest.mock import Mock, patch
from security_manager import SecurityManager, init_security_features


class TestSecurityManager:
    def test_security_manager_init(self):
        """Test SecurityManager initialization"""
        sm = SecurityManager()
        assert sm is not None
        assert hasattr(sm, 'max_login_attempts')
        assert hasattr(sm, 'lockout_duration')
    
    def test_hash_password(self):
        """Test password hashing"""
        sm = SecurityManager()
        password = "test_password_123"
        hashed = sm.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith('pbkdf2:sha256:')
    
    def test_verify_password(self):
        """Test password verification"""
        sm = SecurityManager()
        password = "test_password_123"
        hashed = sm.hash_password(password)
        
        # Test correct password
        assert sm.verify_password(password, hashed) is True
        
        # Test incorrect password
        assert sm.verify_password("wrong_password", hashed) is False
    
    def test_validate_password_strength(self):
        """Test password strength validation"""
        sm = SecurityManager()
        
        # Test weak password
        weak_result = sm.validate_password_strength("123")
        assert weak_result["valid"] is False
        assert weak_result["strength"] == "weak"
        
        # Test strong password
        strong_result = sm.validate_password_strength("StrongPassword123!")
        assert strong_result["valid"] is True
        assert strong_result["strength"] == "strong"
    
    def test_init_security_features(self):
        """Test security features initialization"""
        mock_app = Mock()
        mock_app.config = {"APP_NAME": "Test App"}
        
        sm = init_security_features(mock_app)
        assert sm is not None
        assert isinstance(sm, SecurityManager)


if __name__ == "__main__":
    pytest.main([__file__])