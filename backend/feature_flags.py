"""
Feature Flags & A/B Testing System for SoulBridge AI
Enables safe feature rollouts and experimentation
"""

import os
import json
import logging
import time
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from flask import g, request

logger = logging.getLogger(__name__)


class FeatureState(Enum):
    """Feature flag states"""

    DISABLED = "disabled"
    ENABLED = "enabled"
    TESTING = "testing"
    ROLLOUT = "rollout"
    DEPRECATED = "deprecated"


class RolloutStrategy(Enum):
    """Rollout strategies for feature flags"""

    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    USER_TIER = "user_tier"
    GEOGRAPHIC = "geographic"
    TIME_WINDOW = "time_window"


@dataclass
class FeatureFlag:
    """Feature flag configuration"""

    name: str
    description: str
    state: FeatureState
    rollout_strategy: RolloutStrategy
    rollout_percentage: float = 0.0
    target_users: List[str] = None
    target_tiers: List[str] = None
    target_regions: List[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = "system"

    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.target_tiers is None:
            self.target_tiers = []
        if self.target_regions is None:
            self.target_regions = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class ABTest:
    """A/B Test configuration"""

    name: str
    description: str
    variants: Dict[str, float]  # variant_name -> percentage
    target_users: List[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class FeatureFlagManager:
    """Manages feature flags and A/B tests"""

    def __init__(self, storage_backend=None):
        self.storage = storage_backend or InMemoryStorage()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = 0

        # Initialize default feature flags
        self._init_default_flags()

    def _init_default_flags(self):
        """Initialize default feature flags"""
        default_flags = [
            FeatureFlag(
                name="new_chat_ui",
                description="New chat interface with enhanced UX",
                state=FeatureState.TESTING,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=10.0,
            ),
            FeatureFlag(
                name="premium_companions",
                description="Access to premium AI companions",
                state=FeatureState.ENABLED,
                rollout_strategy=RolloutStrategy.USER_TIER,
                target_tiers=["premium", "premium_annual"],
            ),
            FeatureFlag(
                name="voice_chat",
                description="Voice chat functionality",
                state=FeatureState.ROLLOUT,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=25.0,
            ),
            FeatureFlag(
                name="advanced_analytics",
                description="Enhanced user analytics dashboard",
                state=FeatureState.DISABLED,
                rollout_strategy=RolloutStrategy.USER_LIST,
                target_users=["admin"],
            ),
            FeatureFlag(
                name="real_time_notifications",
                description="WebSocket-based real-time notifications",
                state=FeatureState.TESTING,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=5.0,
            ),
        ]

        for flag in default_flags:
            if not self.storage.get_feature_flag(flag.name):
                self.storage.save_feature_flag(flag)

    def _refresh_cache(self):
        """Refresh feature flags cache if needed"""
        current_time = time.time()
        if current_time - self.last_cache_update > self.cache_ttl:
            self.cache = {}
            self.last_cache_update = current_time

    def _get_user_context(self) -> Dict[str, Any]:
        """Get current user context for feature flag evaluation"""
        context = {"user_id": None, "tier": "bronze", "region": None, "ip": None}

        # Get user info from Flask context
        if hasattr(g, "current_user") and g.current_user:
            context["user_id"] = g.current_user.get("userID")
            context["tier"] = g.current_user.get("subscription_status", "bronze")

        # Get IP and region from request
        if request:
            context["ip"] = request.remote_addr
            # You could add GeoIP lookup here for region

        return context

    def _hash_user_for_percentage(self, user_id: str, feature_name: str) -> float:
        """Generate consistent hash for percentage-based rollouts"""
        hash_input = f"{user_id}:{feature_name}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        # Convert first 8 chars of hash to percentage (0-100)
        return int(hash_value[:8], 16) % 100

    def is_feature_enabled(self, feature_name: str, user_context: Dict = None) -> bool:
        """Check if a feature is enabled for the current user"""
        self._refresh_cache()

        # Check cache first
        cache_key = f"{feature_name}:{user_context.get('user_id') if user_context else 'anonymous'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Get user context
        if user_context is None:
            user_context = self._get_user_context()

        # Get feature flag
        flag = self.storage.get_feature_flag(feature_name)
        if not flag:
            logger.warning(f"Feature flag '{feature_name}' not found")
            result = False
        else:
            result = self._evaluate_feature_flag(flag, user_context)

        # Cache result
        self.cache[cache_key] = result
        return result

    def _evaluate_feature_flag(self, flag: FeatureFlag, user_context: Dict) -> bool:
        """Evaluate if feature flag should be enabled for user"""
        # Check if feature is globally disabled
        if flag.state == FeatureState.DISABLED:
            return False

        # Check if feature is globally enabled
        if flag.state == FeatureState.ENABLED:
            return True

        # Check time windows
        now = datetime.utcnow()
        if flag.start_time and now < flag.start_time:
            return False
        if flag.end_time and now > flag.end_time:
            return False

        # Apply rollout strategy
        if flag.rollout_strategy == RolloutStrategy.ALL_USERS:
            return True

        elif flag.rollout_strategy == RolloutStrategy.USER_LIST:
            return user_context.get("user_id") in flag.target_users

        elif flag.rollout_strategy == RolloutStrategy.USER_TIER:
            return user_context.get("tier") in flag.target_tiers

        elif flag.rollout_strategy == RolloutStrategy.PERCENTAGE:
            user_id = user_context.get("user_id", user_context.get("ip", "anonymous"))
            user_hash = self._hash_user_for_percentage(user_id, flag.name)
            return user_hash < flag.rollout_percentage

        elif flag.rollout_strategy == RolloutStrategy.GEOGRAPHIC:
            return user_context.get("region") in flag.target_regions

        return False

    def get_ab_test_variant(self, test_name: str, user_context: Dict = None) -> str:
        """Get A/B test variant for user"""
        if user_context is None:
            user_context = self._get_user_context()

        test = self.storage.get_ab_test(test_name)
        if not test or not test.is_active:
            return "control"

        # Check time windows
        now = datetime.utcnow()
        if test.start_time and now < test.start_time:
            return "control"
        if test.end_time and now > test.end_time:
            return "control"

        # Check target users
        if test.target_users and user_context.get("user_id") not in test.target_users:
            return "control"

        # Determine variant based on hash
        user_id = user_context.get("user_id", user_context.get("ip", "anonymous"))
        user_hash = self._hash_user_for_percentage(user_id, test_name)

        cumulative_percentage = 0
        for variant, percentage in test.variants.items():
            cumulative_percentage += percentage
            if user_hash < cumulative_percentage:
                return variant

        return "control"

    def create_feature_flag(self, flag: FeatureFlag) -> bool:
        """Create a new feature flag"""
        try:
            flag.created_at = datetime.utcnow()
            flag.updated_at = datetime.utcnow()
            self.storage.save_feature_flag(flag)
            self.cache = {}  # Clear cache
            logger.info(f"Created feature flag: {flag.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create feature flag {flag.name}: {e}")
            return False

    def update_feature_flag(self, name: str, updates: Dict) -> bool:
        """Update an existing feature flag"""
        try:
            flag = self.storage.get_feature_flag(name)
            if not flag:
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)

            flag.updated_at = datetime.utcnow()
            self.storage.save_feature_flag(flag)
            self.cache = {}  # Clear cache
            logger.info(f"Updated feature flag: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update feature flag {name}: {e}")
            return False

    def delete_feature_flag(self, name: str) -> bool:
        """Delete a feature flag"""
        try:
            self.storage.delete_feature_flag(name)
            self.cache = {}  # Clear cache
            logger.info(f"Deleted feature flag: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete feature flag {name}: {e}")
            return False

    def list_feature_flags(self) -> List[FeatureFlag]:
        """List all feature flags"""
        return self.storage.list_feature_flags()

    def create_ab_test(self, test: ABTest) -> bool:
        """Create a new A/B test"""
        try:
            test.created_at = datetime.utcnow()
            self.storage.save_ab_test(test)
            logger.info(f"Created A/B test: {test.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create A/B test {test.name}: {e}")
            return False

    def list_ab_tests(self) -> List[ABTest]:
        """List all A/B tests"""
        return self.storage.list_ab_tests()


class InMemoryStorage:
    """In-memory storage for feature flags (development use)"""

    def __init__(self):
        self.feature_flags = {}
        self.ab_tests = {}

    def get_feature_flag(self, name: str) -> Optional[FeatureFlag]:
        return self.feature_flags.get(name)

    def save_feature_flag(self, flag: FeatureFlag):
        self.feature_flags[flag.name] = flag

    def delete_feature_flag(self, name: str):
        self.feature_flags.pop(name, None)

    def list_feature_flags(self) -> List[FeatureFlag]:
        return list(self.feature_flags.values())

    def get_ab_test(self, name: str) -> Optional[ABTest]:
        return self.ab_tests.get(name)

    def save_ab_test(self, test: ABTest):
        self.ab_tests[test.name] = test

    def list_ab_tests(self) -> List[ABTest]:
        return list(self.ab_tests.values())


class DatabaseStorage:
    """Database storage for feature flags (production use)"""

    def __init__(self, db_manager):
        self.db = db_manager
        # Tables are already created in postgres_db.py

    def get_feature_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get feature flag from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT flag_name, description, is_enabled, rollout_percentage, 
                       target_groups, conditions, metadata, created_by, created_date, updated_date
                FROM feature_flags WHERE flag_name = %s
                """,
                (name,)
            )
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Convert database result to FeatureFlag object
            flag_name, description, is_enabled, rollout_percentage, target_groups, conditions, metadata, created_by, created_date, updated_date = result
            
            # Map database state to enum
            state = FeatureState.ENABLED if is_enabled else FeatureState.DISABLED
            
            # Determine rollout strategy from data
            if rollout_percentage > 0:
                rollout_strategy = RolloutStrategy.PERCENTAGE
            elif target_groups:
                rollout_strategy = RolloutStrategy.USER_LIST
            else:
                rollout_strategy = RolloutStrategy.ALL_USERS if is_enabled else RolloutStrategy.ALL_USERS
            
            return FeatureFlag(
                name=flag_name,
                description=description,
                state=state,
                rollout_strategy=rollout_strategy,
                rollout_percentage=float(rollout_percentage),
                target_users=json.loads(target_groups) if target_groups else [],
                created_at=created_date,
                updated_at=updated_date,
                created_by=created_by
            )
            
        except Exception as e:
            logger.error(f"Error getting feature flag {name}: {e}")
            return None

    def save_feature_flag(self, flag: FeatureFlag):
        """Save feature flag to database"""
        try:
            cursor = self.db.connection.cursor()
            
            # Check if flag exists
            cursor.execute("SELECT flag_id FROM feature_flags WHERE flag_name = %s", (flag.name,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing flag
                cursor.execute(
                    """
                    UPDATE feature_flags SET
                        description = %s,
                        is_enabled = %s,
                        rollout_percentage = %s,
                        target_groups = %s,
                        conditions = %s,
                        metadata = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE flag_name = %s
                    """,
                    (
                        flag.description,
                        flag.state == FeatureState.ENABLED,
                        flag.rollout_percentage,
                        json.dumps(flag.target_users),
                        json.dumps({}),  # conditions
                        json.dumps({}),  # metadata
                        flag.name
                    )
                )
            else:
                # Create new flag
                flag_id = f"flag_{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    """
                    INSERT INTO feature_flags (
                        flag_id, flag_name, description, is_enabled, rollout_percentage,
                        target_groups, conditions, metadata, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        flag_id,
                        flag.name,
                        flag.description,
                        flag.state == FeatureState.ENABLED,
                        flag.rollout_percentage,
                        json.dumps(flag.target_users),
                        json.dumps({}),  # conditions
                        json.dumps({}),  # metadata
                        flag.created_by
                    )
                )
                
        except Exception as e:
            logger.error(f"Error saving feature flag {flag.name}: {e}")
            raise

    def delete_feature_flag(self, name: str):
        """Delete feature flag from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM feature_flags WHERE flag_name = %s", (name,))
        except Exception as e:
            logger.error(f"Error deleting feature flag {name}: {e}")
            raise

    def list_feature_flags(self) -> List[FeatureFlag]:
        """List all feature flags from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT flag_name, description, is_enabled, rollout_percentage, 
                       target_groups, conditions, metadata, created_by, created_date, updated_date
                FROM feature_flags ORDER BY created_date DESC
                """
            )
            
            flags = []
            for result in cursor.fetchall():
                flag_name, description, is_enabled, rollout_percentage, target_groups, conditions, metadata, created_by, created_date, updated_date = result
                
                state = FeatureState.ENABLED if is_enabled else FeatureState.DISABLED
                rollout_strategy = RolloutStrategy.PERCENTAGE if rollout_percentage > 0 else RolloutStrategy.ALL_USERS
                
                flags.append(FeatureFlag(
                    name=flag_name,
                    description=description,
                    state=state,
                    rollout_strategy=rollout_strategy,
                    rollout_percentage=float(rollout_percentage),
                    target_users=json.loads(target_groups) if target_groups else [],
                    created_at=created_date,
                    updated_at=updated_date,
                    created_by=created_by
                ))
            
            return flags
            
        except Exception as e:
            logger.error(f"Error listing feature flags: {e}")
            return []

    def get_ab_test(self, name: str) -> Optional[ABTest]:
        """Get A/B test from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT experiment_name, description, is_active, variants, 
                       traffic_allocation, target_criteria, success_metrics, 
                       start_date, end_date, created_date
                FROM ab_experiments WHERE experiment_name = %s
                """,
                (name,)
            )
            
            result = cursor.fetchone()
            if not result:
                return None
            
            experiment_name, description, is_active, variants, traffic_allocation, target_criteria, success_metrics, start_date, end_date, created_date = result
            
            return ABTest(
                name=experiment_name,
                description=description,
                is_active=is_active,
                variants=json.loads(variants),
                target_users=json.loads(target_criteria).get('target_users', []) if target_criteria else [],
                start_time=start_date,
                end_time=end_date,
                created_at=created_date
            )
            
        except Exception as e:
            logger.error(f"Error getting A/B test {name}: {e}")
            return None

    def save_ab_test(self, test: ABTest):
        """Save A/B test to database"""
        try:
            cursor = self.db.connection.cursor()
            
            # Check if experiment exists
            cursor.execute("SELECT experiment_id FROM ab_experiments WHERE experiment_name = %s", (test.name,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing experiment
                cursor.execute(
                    """
                    UPDATE ab_experiments SET
                        description = %s,
                        is_active = %s,
                        variants = %s,
                        traffic_allocation = %s,
                        target_criteria = %s,
                        start_date = %s,
                        end_date = %s,
                        updated_date = CURRENT_TIMESTAMP
                    WHERE experiment_name = %s
                    """,
                    (
                        test.description,
                        test.is_active,
                        json.dumps(test.variants),
                        json.dumps(test.variants),  # traffic_allocation same as variants for simplicity
                        json.dumps({'target_users': test.target_users}),
                        test.start_time,
                        test.end_time,
                        test.name
                    )
                )
            else:
                # Create new experiment
                experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    """
                    INSERT INTO ab_experiments (
                        experiment_id, experiment_name, description, is_active, variants,
                        traffic_allocation, target_criteria, success_metrics,
                        start_date, end_date, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        experiment_id,
                        test.name,
                        test.description,
                        test.is_active,
                        json.dumps(test.variants),
                        json.dumps(test.variants),
                        json.dumps({'target_users': test.target_users}),
                        json.dumps([]),  # success_metrics
                        test.start_time,
                        test.end_time,
                        'system'  # created_by
                    )
                )
                
        except Exception as e:
            logger.error(f"Error saving A/B test {test.name}: {e}")
            raise

    def list_ab_tests(self) -> List[ABTest]:
        """List all A/B tests from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT experiment_name, description, is_active, variants, 
                       traffic_allocation, target_criteria, success_metrics, 
                       start_date, end_date, created_date
                FROM ab_experiments ORDER BY created_date DESC
                """
            )
            
            tests = []
            for result in cursor.fetchall():
                experiment_name, description, is_active, variants, traffic_allocation, target_criteria, success_metrics, start_date, end_date, created_date = result
                
                tests.append(ABTest(
                    name=experiment_name,
                    description=description,
                    is_active=is_active,
                    variants=json.loads(variants),
                    target_users=json.loads(target_criteria).get('target_users', []) if target_criteria else [],
                    start_time=start_date,
                    end_time=end_date,
                    created_at=created_date
                ))
            
            return tests
            
        except Exception as e:
            logger.error(f"Error listing A/B tests: {e}")
            return []


# Global feature flag manager - will be initialized in app.py
feature_manager = None


# Convenience functions
def is_feature_enabled(feature_name: str, user_context: Dict = None) -> bool:
    """Check if a feature is enabled"""
    global feature_manager
    if not feature_manager:
        logger.warning("Feature flag manager not initialized")
        return False
    return feature_manager.is_feature_enabled(feature_name, user_context)


def get_ab_test_variant(test_name: str, user_context: Dict = None) -> str:
    """Get A/B test variant"""
    global feature_manager
    if not feature_manager:
        logger.warning("Feature flag manager not initialized")
        return "control"
    return feature_manager.get_ab_test_variant(test_name, user_context)


def feature_flag(feature_name: str):
    """Decorator to gate functions behind feature flags"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_feature_enabled(feature_name):
                return func(*args, **kwargs)
            else:
                return None

        return wrapper

    return decorator


def init_feature_flags(app, db_manager=None):
    """Initialize feature flags for Flask app"""
    global feature_manager
    
    # Initialize feature manager with database storage if available
    if db_manager:
        storage = DatabaseStorage(db_manager)
        feature_manager = FeatureFlagManager(storage)
    else:
        feature_manager = FeatureFlagManager()
    
    logger.info("Feature flag manager initialized")

    @app.route("/api/admin/feature-flags", methods=["GET"])
    def list_feature_flags():
        """List all feature flags (admin only)"""
        # Add admin authentication check here
        if not feature_manager:
            return {"feature_flags": []}
        flags = feature_manager.list_feature_flags()
        return {"feature_flags": [asdict(flag) for flag in flags]}

    @app.route("/api/admin/feature-flags", methods=["POST"])
    def create_feature_flag():
        """Create a new feature flag (admin only)"""
        # Add admin authentication check here
        data = request.get_json()

        flag = FeatureFlag(
            name=data["name"],
            description=data["description"],
            state=FeatureState(data["state"]),
            rollout_strategy=RolloutStrategy(data["rollout_strategy"]),
            rollout_percentage=data.get("rollout_percentage", 0.0),
            target_users=data.get("target_users", []),
            target_tiers=data.get("target_tiers", []),
        )

        success = feature_manager.create_feature_flag(flag)
        return {"success": success}

    @app.route("/api/admin/feature-flags/<name>", methods=["PUT"])
    def update_feature_flag(name):
        """Update a feature flag (admin only)"""
        # Add admin authentication check here
        data = request.get_json()
        success = feature_manager.update_feature_flag(name, data)
        return {"success": success}

    @app.route("/api/admin/feature-flags/<name>", methods=["DELETE"])
    def delete_feature_flag(name):
        """Delete a feature flag (admin only)"""
        # Add admin authentication check here
        success = feature_manager.delete_feature_flag(name)
        return {"success": success}

    @app.route("/api/feature-flags/check/<feature_name>")
    def check_feature_flag(feature_name):
        """Check if a feature is enabled for current user"""
        enabled = is_feature_enabled(feature_name)
        return {"enabled": enabled, "feature": feature_name}

    @app.route("/api/ab-tests/<test_name>/variant")
    def get_test_variant(test_name):
        """Get A/B test variant for current user"""
        variant = get_ab_test_variant(test_name)
        return {"variant": variant, "test": test_name}

    logger.info("Feature flags initialized")
