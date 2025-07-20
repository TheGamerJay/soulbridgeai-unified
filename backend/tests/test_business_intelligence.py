# Tests for Business Intelligence
import pytest
from unittest.mock import Mock
from business_intelligence import BusinessIntelligenceManager, init_business_intelligence


class TestBusinessIntelligenceManager:
    def test_business_intelligence_init(self):
        """Test BusinessIntelligenceManager initialization"""
        bi = BusinessIntelligenceManager()
        assert bi is not None
        assert hasattr(bi, 'aggregation_windows')
        assert hasattr(bi, 'kpi_thresholds')
    
    def test_get_comprehensive_user_analytics(self):
        """Test comprehensive user analytics"""
        bi = BusinessIntelligenceManager()
        
        analytics = bi.get_comprehensive_user_analytics(30)
        assert "period" in analytics
        assert "user_metrics" in analytics
        assert "generated_at" in analytics
    
    def test_get_comprehensive_revenue_analytics(self):
        """Test comprehensive revenue analytics"""
        bi = BusinessIntelligenceManager()
        
        analytics = bi.get_comprehensive_revenue_analytics(30)
        assert "period" in analytics
        assert "revenue_metrics" in analytics
        assert "generated_at" in analytics
    
    def test_get_predictive_insights(self):
        """Test predictive insights generation"""
        bi = BusinessIntelligenceManager()
        
        insights = bi.get_predictive_insights()
        assert "generated_at" in insights
        assert "insights" in insights
        assert "total_insights" in insights
    
    def test_calculate_churn_risk_score(self):
        """Test churn risk calculation"""
        bi = BusinessIntelligenceManager()
        
        test_user = {
            "userID": "test_user",
            "subscription_status": "active",
            "last_login": "2024-01-01"
        }
        
        risk_score = bi._calculate_churn_risk_score(test_user)
        assert isinstance(risk_score, float)
        assert 0 <= risk_score <= 1
    
    def test_calculate_distribution(self):
        """Test distribution calculation"""
        bi = BusinessIntelligenceManager()
        
        values = [0.1, 0.3, 0.5, 0.7, 0.9]
        distribution = bi._calculate_distribution(values)
        
        assert isinstance(distribution, dict)
        assert "0-20%" in distribution
        assert "80-100%" in distribution
    
    def test_get_users_data(self):
        """Test user data retrieval"""
        bi = BusinessIntelligenceManager()
        
        users = bi._get_users_data()
        assert isinstance(users, list)
        # Should return sample data when no DB is connected
        assert len(users) > 0
    
    def test_init_business_intelligence(self):
        """Test business intelligence initialization"""
        mock_db = Mock()
        mock_ai = Mock()
        mock_security = Mock()
        
        bi = init_business_intelligence(mock_db, mock_ai, mock_security)
        assert bi is not None
        assert isinstance(bi, BusinessIntelligenceManager)


if __name__ == "__main__":
    pytest.main([__file__])