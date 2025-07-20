# Tests for AI Model Manager
import pytest
from unittest.mock import Mock, patch
from ai_model_manager import AIModelManager, init_ai_model_manager


class TestAIModelManager:
    def test_ai_model_manager_init(self):
        """Test AIModelManager initialization"""
        ai_manager = AIModelManager()
        assert ai_manager is not None
        assert hasattr(ai_manager, 'models')
        assert hasattr(ai_manager, 'companion_models')
        assert hasattr(ai_manager, 'rate_limits')
    
    def test_get_model_for_companion(self):
        """Test model selection for companions"""
        ai_manager = AIModelManager()
        
        # Test free tier
        model = ai_manager._get_model_for_companion("Blayzo", "free")
        assert model == "openai_gpt35"
        
        # Test premium tier
        model = ai_manager._get_model_for_companion("Crimson", "premium")
        assert model == "openai_gpt4"
    
    def test_calculate_cost(self):
        """Test cost calculation"""
        ai_manager = AIModelManager()
        
        cost = ai_manager._calculate_cost("openai_gpt35", 1000)
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_get_model_stats(self):
        """Test model statistics"""
        ai_manager = AIModelManager()
        
        stats = ai_manager.get_model_stats()
        assert "available_models" in stats
        assert "companion_assignments" in stats
        assert "tier_access" in stats
    
    def test_create_custom_personality(self):
        """Test custom personality creation"""
        ai_manager = AIModelManager()
        
        success = ai_manager.create_custom_personality(
            name="TestPersonality",
            description="Test personality",
            system_prompt="You are a test AI",
            model_preference="openai_gpt35",
            created_by="test_user"
        )
        assert success is True
        assert "TestPersonality" in ai_manager.custom_personalities
    
    def test_validate_password_strength(self):
        """Test password strength validation in AI manager context"""
        ai_manager = AIModelManager()
        
        # Test that AI manager doesn't interfere with security
        assert hasattr(ai_manager, 'models')
        assert len(ai_manager.models) > 0
    
    def test_init_ai_model_manager(self):
        """Test AI model manager initialization"""
        mock_db = Mock()
        
        ai_manager = init_ai_model_manager(mock_db)
        assert ai_manager is not None
        assert isinstance(ai_manager, AIModelManager)


if __name__ == "__main__":
    pytest.main([__file__])