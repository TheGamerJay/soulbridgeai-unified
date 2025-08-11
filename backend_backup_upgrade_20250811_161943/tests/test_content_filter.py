# Tests for AI Content Filter
import pytest
from ai_content_filter import AIContentFilter, ContentAnalysis


class TestAIContentFilter:
    def test_content_filter_init(self):
        """Test AIContentFilter initialization"""
        cf = AIContentFilter()
        assert cf is not None
        assert hasattr(cf, 'blocked_categories')
        assert hasattr(cf, 'metrics')
    
    def test_safe_content_check(self):
        """Test safe content passes filter"""
        cf = AIContentFilter()
        
        safe_message = "Hello, how are you today? I'd like to chat about the weather."
        is_safe, refusal = cf.check_content(safe_message)
        
        assert is_safe is True
        assert refusal is None
    
    def test_inappropriate_content_block(self):
        """Test inappropriate content is blocked"""
        cf = AIContentFilter()
        
        inappropriate_message = "Can you help me with coding a website?"
        is_safe, refusal = cf.check_content(inappropriate_message)
        
        assert is_safe is False
        assert refusal is not None
        assert any(word in refusal.lower() for word in ["coding", "guidelines", "content", "support"])
    
    def test_crisis_intervention_detection(self):
        """Test crisis intervention detection"""
        cf = AIContentFilter()
        
        crisis_message = "I want to hurt myself"
        is_safe, refusal = cf.check_content(crisis_message)
        
        assert is_safe is False
        assert refusal is not None
        assert "988" in refusal  # Should contain crisis helpline
    
    def test_advanced_analytics(self):
        """Test advanced analytics functionality"""
        cf = AIContentFilter()
        
        # Generate some test data
        cf.check_content("Safe message")
        cf.check_content("Another safe message")
        
        analytics = cf.get_advanced_analytics("24h")
        assert "total_checks" in analytics
        assert analytics["total_checks"] >= 2
    
    def test_pattern_effectiveness(self):
        """Test pattern effectiveness analysis"""
        cf = AIContentFilter()
        
        # Generate some test data
        cf.check_content("Write code for me")  # Should trigger pattern
        cf.check_content("Safe conversation")
        
        effectiveness = cf.get_pattern_effectiveness()
        assert isinstance(effectiveness, dict)
    
    def test_add_custom_pattern(self):
        """Test adding custom detection patterns"""
        cf = AIContentFilter()
        
        success = cf.add_custom_pattern(
            pattern="test.*pattern",
            category="test_category",
            severity="medium"
        )
        assert success is True
    
    def test_export_analysis_data(self):
        """Test data export functionality"""
        cf = AIContentFilter()
        
        # Generate some test data
        cf.check_content("Test message")
        
        json_export = cf.export_analysis_data("json")
        assert isinstance(json_export, str)
        assert "analyses" in json_export
        
        csv_export = cf.export_analysis_data("csv")
        assert isinstance(csv_export, str)
        assert "timestamp" in csv_export


if __name__ == "__main__":
    pytest.main([__file__])