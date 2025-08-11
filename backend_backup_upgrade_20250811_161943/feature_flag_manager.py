"""
Feature Flag and A/B Testing Management System for SoulBridge AI
Provides comprehensive feature flag management with A/B testing capabilities
"""

import json
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TargetingCriteria(Enum):
    """Targeting criteria for feature flags"""
    USER_ID = "user_id"
    EMAIL = "email"
    SUBSCRIPTION_STATUS = "subscription_status"
    COMPANION = "companion"
    SIGNUP_DATE = "signup_date"
    COUNTRY = "country"
    DEVICE_TYPE = "device_type"
    USER_AGENT = "user_agent"


@dataclass
class FeatureFlag:
    """Feature flag data structure"""
    flag_id: str
    flag_name: str
    description: str
    is_enabled: bool
    rollout_percentage: float
    target_groups: List[Dict]
    conditions: Dict
    metadata: Dict
    created_by: str
    created_date: datetime
    updated_date: datetime


@dataclass
class ABExperiment:
    """A/B test experiment data structure"""
    experiment_id: str
    experiment_name: str
    description: str
    is_active: bool
    variants: Dict
    traffic_allocation: Dict
    target_criteria: Dict
    success_metrics: List
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_by: str
    created_date: datetime
    updated_date: datetime


class FeatureFlagManager:
    """Manages feature flags and A/B testing"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.cache = {}  # Simple in-memory cache for flags
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = None
        
    def create_feature_flag(
        self,
        flag_name: str,
        description: str,
        created_by: str,
        is_enabled: bool = False,
        rollout_percentage: float = 0.0,
        target_groups: List[Dict] = None,
        conditions: Dict = None,
        metadata: Dict = None
    ) -> Dict:
        """Create a new feature flag"""
        try:
            flag_id = f"flag_{uuid.uuid4().hex[:8]}"
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO feature_flags (
                    flag_id, flag_name, description, is_enabled, rollout_percentage,
                    target_groups, conditions, metadata, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING flag_id, flag_name, created_date
                """,
                (
                    flag_id,
                    flag_name,
                    description,
                    is_enabled,
                    rollout_percentage,
                    json.dumps(target_groups or []),
                    json.dumps(conditions or {}),
                    json.dumps(metadata or {}),
                    created_by
                )
            )
            
            result = cursor.fetchone()
            self._clear_cache()
            
            logger.info(f"Created feature flag: {flag_name} (ID: {flag_id})")
            
            return {
                "flag_id": result[0],
                "flag_name": result[1],
                "created_date": result[2].isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error creating feature flag {flag_name}: {e}")
            raise
    
    def update_feature_flag(
        self,
        flag_name: str,
        updates: Dict,
        updated_by: str
    ) -> Dict:
        """Update an existing feature flag"""
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = [
                'description', 'is_enabled', 'rollout_percentage',
                'target_groups', 'conditions', 'metadata'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field in ['target_groups', 'conditions', 'metadata']:
                        value = json.dumps(value)
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if not set_clauses:
                raise ValueError("No valid fields to update")
            
            set_clauses.append("updated_date = CURRENT_TIMESTAMP")
            values.append(flag_name)
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                f"""
                UPDATE feature_flags 
                SET {', '.join(set_clauses)}
                WHERE flag_name = %s
                RETURNING flag_id, flag_name, updated_date
                """,
                values
            )
            
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Feature flag {flag_name} not found")
            
            self._clear_cache()
            
            # Log the change
            self._log_flag_change(flag_name, updates, updated_by)
            
            return {
                "flag_id": result[0],
                "flag_name": result[1],
                "updated_date": result[2].isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error updating feature flag {flag_name}: {e}")
            raise
    
    def get_feature_flag(self, flag_name: str) -> Optional[Dict]:
        """Get a specific feature flag"""
        try:
            cursor = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM feature_flags WHERE flag_name = %s
                """,
                (flag_name,)
            )
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting feature flag {flag_name}: {e}")
            return None
    
    def list_feature_flags(self) -> List[Dict]:
        """List all feature flags"""
        try:
            cursor = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM feature_flags 
                ORDER BY created_date DESC
                """
            )
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error listing feature flags: {e}")
            return []
    
    def is_feature_enabled(
        self,
        flag_name: str,
        user_id: str = None,
        user_context: Dict = None
    ) -> bool:
        """Check if a feature is enabled for a user"""
        try:
            # Check cache first
            flag = self._get_cached_flag(flag_name)
            if not flag:
                flag = self.get_feature_flag(flag_name)
                if not flag:
                    logger.warning(f"Feature flag {flag_name} not found")
                    return False
                self._cache_flag(flag)
            
            # If flag is globally disabled, return False
            if not flag.get('is_enabled', False):
                return False
            
            # If no user context and rollout is 100%, return True
            if flag.get('rollout_percentage', 0) >= 100.0 and not flag.get('target_groups'):
                return True
            
            # Check user-specific assignment first
            if user_id:
                assignment = self._get_user_assignment(user_id, flag_name)
                if assignment:
                    return assignment.get('is_enabled', False)
            
            # Check targeting criteria
            if user_context and flag.get('target_groups'):
                if self._matches_targeting_criteria(user_context, flag['target_groups']):
                    return True
            
            # Check rollout percentage
            if user_id and flag.get('rollout_percentage', 0) > 0:
                return self._is_user_in_rollout(user_id, flag_name, flag['rollout_percentage'])
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feature flag {flag_name}: {e}")
            return False
    
    def assign_user_to_feature(
        self,
        user_id: str,
        flag_name: str,
        is_enabled: bool,
        experiment_id: str = None,
        variant_name: str = None
    ) -> Dict:
        """Manually assign a user to a feature flag"""
        try:
            assignment_id = f"assign_{uuid.uuid4().hex[:8]}"
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO user_feature_assignments (
                    assignment_id, user_id, flag_name, experiment_id, 
                    variant_name, is_enabled
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, flag_name) 
                DO UPDATE SET 
                    is_enabled = EXCLUDED.is_enabled,
                    experiment_id = EXCLUDED.experiment_id,
                    variant_name = EXCLUDED.variant_name,
                    assigned_date = CURRENT_TIMESTAMP
                RETURNING assignment_id
                """,
                (assignment_id, user_id, flag_name, experiment_id, variant_name, is_enabled)
            )
            
            result = cursor.fetchone()
            
            return {
                "assignment_id": result[0],
                "user_id": user_id,
                "flag_name": flag_name,
                "is_enabled": is_enabled,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error assigning user {user_id} to feature {flag_name}: {e}")
            raise
    
    def track_feature_usage(
        self,
        user_id: str,
        flag_name: str,
        event_type: str,
        event_data: Dict = None,
        session_id: str = None,
        experiment_id: str = None,
        variant_name: str = None
    ):
        """Track feature usage for analytics"""
        try:
            usage_id = f"usage_{uuid.uuid4().hex[:8]}"
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO feature_usage_analytics (
                    usage_id, user_id, flag_name, experiment_id, variant_name,
                    event_type, event_data, session_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    usage_id, user_id, flag_name, experiment_id, variant_name,
                    event_type, json.dumps(event_data or {}), session_id
                )
            )
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
    
    def create_ab_experiment(
        self,
        experiment_name: str,
        description: str,
        variants: Dict,
        traffic_allocation: Dict,
        created_by: str,
        target_criteria: Dict = None,
        success_metrics: List = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """Create a new A/B test experiment"""
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
            
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO ab_experiments (
                    experiment_id, experiment_name, description, variants,
                    traffic_allocation, target_criteria, success_metrics,
                    start_date, end_date, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING experiment_id, experiment_name, created_date
                """,
                (
                    experiment_id, experiment_name, description,
                    json.dumps(variants), json.dumps(traffic_allocation),
                    json.dumps(target_criteria or {}),
                    json.dumps(success_metrics or []),
                    start_date, end_date, created_by
                )
            )
            
            result = cursor.fetchone()
            
            logger.info(f"Created A/B experiment: {experiment_name} (ID: {experiment_id})")
            
            return {
                "experiment_id": result[0],
                "experiment_name": result[1],
                "created_date": result[2].isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error creating A/B experiment {experiment_name}: {e}")
            raise
    
    def get_user_variant(
        self,
        user_id: str,
        experiment_name: str,
        user_context: Dict = None
    ) -> Optional[str]:
        """Get the variant assigned to a user for an experiment"""
        try:
            # Check existing assignment
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT variant_name FROM user_feature_assignments 
                WHERE user_id = %s AND experiment_id IN (
                    SELECT experiment_id FROM ab_experiments 
                    WHERE experiment_name = %s AND is_active = TRUE
                )
                """,
                (user_id, experiment_name)
            )
            
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Get experiment details
            cursor.execute(
                """
                SELECT experiment_id, variants, traffic_allocation, target_criteria
                FROM ab_experiments 
                WHERE experiment_name = %s AND is_active = TRUE
                AND (start_date IS NULL OR start_date <= CURRENT_TIMESTAMP)
                AND (end_date IS NULL OR end_date > CURRENT_TIMESTAMP)
                """,
                (experiment_name,)
            )
            
            experiment = cursor.fetchone()
            if not experiment:
                return None
            
            experiment_id, variants, traffic_allocation, target_criteria = experiment
            
            # Check if user matches targeting criteria
            if target_criteria and user_context:
                if not self._matches_targeting_criteria(user_context, [target_criteria]):
                    return None
            
            # Assign variant based on consistent hashing
            variant = self._assign_variant(user_id, experiment_name, traffic_allocation)
            
            if variant:
                # Save assignment
                self.assign_user_to_feature(
                    user_id=user_id,
                    flag_name=experiment_name,
                    is_enabled=True,
                    experiment_id=experiment_id,
                    variant_name=variant
                )
            
            return variant
            
        except Exception as e:
            logger.error(f"Error getting user variant for {experiment_name}: {e}")
            return None
    
    def get_feature_analytics(self, flag_name: str, days: int = 30) -> Dict:
        """Get analytics for a feature flag"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get usage stats
            cursor.execute(
                """
                SELECT 
                    event_type,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM feature_usage_analytics 
                WHERE flag_name = %s 
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY event_type
                """,
                (flag_name, days)
            )
            
            usage_stats = cursor.fetchall()
            
            # Get daily usage
            cursor.execute(
                """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as events,
                    COUNT(DISTINCT user_id) as unique_users
                FROM feature_usage_analytics 
                WHERE flag_name = %s 
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY DATE(timestamp)
                ORDER BY date
                """,
                (flag_name, days)
            )
            
            daily_usage = cursor.fetchall()
            
            return {
                "flag_name": flag_name,
                "period_days": days,
                "usage_by_event": [
                    {"event_type": row[0], "count": row[1], "unique_users": row[2]}
                    for row in usage_stats
                ],
                "daily_usage": [
                    {"date": row[0].isoformat(), "events": row[1], "unique_users": row[2]}
                    for row in daily_usage
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics for {flag_name}: {e}")
            return {}
    
    # Private helper methods
    
    def _get_cached_flag(self, flag_name: str) -> Optional[Dict]:
        """Get flag from cache if available and fresh"""
        if not self.last_cache_update:
            return None
        
        if (datetime.now() - self.last_cache_update).seconds > self.cache_ttl:
            self._clear_cache()
            return None
        
        return self.cache.get(flag_name)
    
    def _cache_flag(self, flag: Dict):
        """Cache a flag"""
        self.cache[flag['flag_name']] = flag
        self.last_cache_update = datetime.now()
    
    def _clear_cache(self):
        """Clear the flag cache"""
        self.cache.clear()
        self.last_cache_update = None
    
    def _get_user_assignment(self, user_id: str, flag_name: str) -> Optional[Dict]:
        """Get user's specific assignment for a flag"""
        try:
            cursor = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM user_feature_assignments 
                WHERE user_id = %s AND flag_name = %s
                """,
                (user_id, flag_name)
            )
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting user assignment: {e}")
            return None
    
    def _matches_targeting_criteria(self, user_context: Dict, target_groups: List[Dict]) -> bool:
        """Check if user matches any targeting criteria"""
        for group in target_groups:
            matches = True
            for criterion, expected_value in group.items():
                user_value = user_context.get(criterion)
                
                if isinstance(expected_value, list):
                    if user_value not in expected_value:
                        matches = False
                        break
                elif user_value != expected_value:
                    matches = False
                    break
            
            if matches:
                return True
        
        return False
    
    def _is_user_in_rollout(self, user_id: str, flag_name: str, percentage: float) -> bool:
        """Determine if user is in rollout based on consistent hashing"""
        # Create a consistent hash of user_id + flag_name
        hash_input = f"{user_id}:{flag_name}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Convert to percentage (0-100)
        user_percentage = (hash_value % 10000) / 100.0
        
        return user_percentage < percentage
    
    def _assign_variant(self, user_id: str, experiment_name: str, traffic_allocation: Dict) -> Optional[str]:
        """Assign variant based on traffic allocation and consistent hashing"""
        # Create consistent hash
        hash_input = f"{user_id}:{experiment_name}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_percentage = (hash_value % 10000) / 100.0
        
        # Determine variant based on allocation
        current_percentage = 0.0
        for variant, allocation in traffic_allocation.items():
            current_percentage += allocation
            if user_percentage <= current_percentage:
                return variant
        
        return None
    
    def _log_flag_change(self, flag_name: str, changes: Dict, changed_by: str):
        """Log feature flag changes for audit"""
        logger.info(f"Feature flag {flag_name} updated by {changed_by}: {changes}")


# Import psycopg2 for cursor factory
try:
    import psycopg2.extras
except ImportError:
    # Handle gracefully if psycopg2 is not available
    psycopg2 = None
    logger.warning("psycopg2 not available - feature flags will not work")