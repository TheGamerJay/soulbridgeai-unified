import pytest
import os
from unittest.mock import patch, MagicMock

# Set test environment
os.environ["TEST_MODE"] = "true"

from feature_flags import FeatureFlagManager, FeatureFlag, FeatureState, RolloutStrategy, InMemoryStorage


class TestFeatureFlags:
    """Test feature flag functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.storage = InMemoryStorage()
        self.manager = FeatureFlagManager(self.storage)
    
    def test_create_feature_flag(self):
        """Test creating a feature flag"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.ENABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        result = self.manager.create_feature_flag(flag)
        assert result is True
        
        # Verify flag was stored
        retrieved_flag = self.storage.get_feature_flag("test_feature")
        assert retrieved_flag is not None
        assert retrieved_flag.name == "test_feature"
        assert retrieved_flag.state == FeatureState.ENABLED
    
    def test_feature_enabled_all_users(self):
        """Test feature enabled for all users"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.ENABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        self.manager.create_feature_flag(flag)
        
        # Should be enabled for any user
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user1"})
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user2"})
        assert self.manager.is_feature_enabled("test_feature", {})
    
    def test_feature_disabled(self):
        """Test disabled feature"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.DISABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        self.manager.create_feature_flag(flag)
        
        # Should be disabled for all users
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user1"})
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user2"})
        assert not self.manager.is_feature_enabled("test_feature", {})
    
    def test_percentage_rollout(self):
        """Test percentage-based rollout"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.ROLLOUT,
            rollout_strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=50.0
        )
        
        self.manager.create_feature_flag(flag)
        
        # Test with different user IDs to see percentage distribution
        enabled_count = 0
        total_tests = 100
        
        for i in range(total_tests):
            user_context = {"user_id": f"user{i}"}
            if self.manager.is_feature_enabled("test_feature", user_context):
                enabled_count += 1
        
        # Should be roughly 50% (allow some variance)
        assert 30 <= enabled_count <= 70
    
    def test_user_list_targeting(self):
        """Test user list targeting"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.TESTING,
            rollout_strategy=RolloutStrategy.USER_LIST,
            target_users=["user1", "user3"]
        )
        
        self.manager.create_feature_flag(flag)
        
        # Should be enabled only for target users
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user1"})
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user2"})
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user3"})
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user4"})
    
    def test_user_tier_targeting(self):
        """Test user tier targeting"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.ENABLED,
            rollout_strategy=RolloutStrategy.USER_TIER,
            target_tiers=["premium", "premium_annual"]
        )
        
        self.manager.create_feature_flag(flag)
        
        # Should be enabled only for premium tiers
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user1", "tier": "premium"})
        assert self.manager.is_feature_enabled("test_feature", {"user_id": "user2", "tier": "premium_annual"})
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user3", "tier": "free"})
        assert not self.manager.is_feature_enabled("test_feature", {"user_id": "user4", "tier": "basic"})
    
    def test_nonexistent_feature(self):
        """Test checking nonexistent feature"""
        # Should return False for nonexistent features
        assert not self.manager.is_feature_enabled("nonexistent_feature", {"user_id": "user1"})
    
    def test_update_feature_flag(self):
        """Test updating a feature flag"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.DISABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        self.manager.create_feature_flag(flag)
        
        # Update the flag
        updates = {"state": FeatureState.ENABLED}
        result = self.manager.update_feature_flag("test_feature", updates)
        assert result is True
        
        # Verify update
        updated_flag = self.storage.get_feature_flag("test_feature")
        assert updated_flag.state == FeatureState.ENABLED
    
    def test_delete_feature_flag(self):
        """Test deleting a feature flag"""
        flag = FeatureFlag(
            name="test_feature",
            description="Test feature",
            state=FeatureState.ENABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        self.manager.create_feature_flag(flag)
        
        # Verify flag exists
        assert self.storage.get_feature_flag("test_feature") is not None
        
        # Delete flag
        result = self.manager.delete_feature_flag("test_feature")
        assert result is True
        
        # Verify flag is gone
        assert self.storage.get_feature_flag("test_feature") is None
    
    def test_list_feature_flags(self):
        """Test listing feature flags"""
        # Create multiple flags
        flag1 = FeatureFlag(
            name="feature1",
            description="Feature 1",
            state=FeatureState.ENABLED,
            rollout_strategy=RolloutStrategy.ALL_USERS
        )
        
        flag2 = FeatureFlag(
            name="feature2",
            description="Feature 2",
            state=FeatureState.DISABLED,
            rollout_strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=25.0
        )
        
        self.manager.create_feature_flag(flag1)
        self.manager.create_feature_flag(flag2)
        
        # List flags
        flags = self.manager.list_feature_flags()
        assert len(flags) >= 2
        
        flag_names = [flag.name for flag in flags]
        assert "feature1" in flag_names
        assert "feature2" in flag_names


class TestFeatureFlagConvenienceFunctions:
    """Test convenience functions"""
    
    def test_is_feature_enabled_no_manager(self):
        """Test is_feature_enabled when manager is not initialized"""
        from feature_flags import is_feature_enabled
        
        # Should return False when manager is None
        result = is_feature_enabled("test_feature")
        assert result is False
    
    def test_get_ab_test_variant_no_manager(self):
        """Test get_ab_test_variant when manager is not initialized"""
        from feature_flags import get_ab_test_variant
        
        # Should return control when manager is None
        result = get_ab_test_variant("test_experiment")
        assert result == "control"