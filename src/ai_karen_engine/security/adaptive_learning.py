"""
Adaptive learning engine for intelligent authentication system.

This module provides continuous model improvement through feedback processing,
user-specific threshold adjustments, and model versioning with rollback capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from cachetools import TTLCache
import statistics
import pickle

from ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    RiskThresholds,
    IntelligentAuthConfig,
    RiskLevel
)
from ai_karen_engine.security.intelligent_auth_base import (
    BaseIntelligentAuthService,
    ServiceHealthStatus,
    ServiceStatus
)

logger = logging.getLogger(__name__)


@dataclass
class AuthFeedback:
    """Feedback data for authentication decisions."""
    
    user_id: str
    request_id: str
    timestamp: datetime
    original_risk_score: float
    original_decision: str  # 'allow', 'block', 'require_2fa'
    
    # Feedback type
    is_false_positive: bool = False
    is_false_negative: bool = False
    is_correct: bool = True
    
    # Additional context
    actual_outcome: Optional[str] = None  # What actually happened
    user_reported: bool = False  # User-reported feedback
    admin_verified: bool = False  # Admin-verified feedback
    confidence: float = 1.0  # Confidence in feedback (0.0-1.0)
    
    # Metadata
    feedback_source: str = "system"  # 'system', 'user', 'admin'
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthFeedback:
        """Create instance from dictionary."""
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ModelVersion:
    """Model version information for tracking and rollback."""
    
    version_id: str
    created_at: datetime
    model_type: str  # 'thresholds', 'weights', 'behavioral_model'
    model_data: Dict[str, Any]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_active: bool = False
    rollback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModelVersion:
        """Create instance from dictionary."""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class UserAdaptiveProfile:
    """User-specific adaptive learning profile."""
    
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Threshold adjustments
    adaptive_thresholds: Optional[RiskThresholds] = None
    threshold_adjustment_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Feedback history
    feedback_history: List[AuthFeedback] = field(default_factory=list)
    false_positive_count: int = 0
    false_negative_count: int = 0
    correct_predictions: int = 0
    
    # Behavioral patterns
    typical_login_hours: List[int] = field(default_factory=list)
    typical_locations: List[str] = field(default_factory=list)
    typical_devices: List[str] = field(default_factory=list)
    
    # Risk score history
    risk_score_history: List[float] = field(default_factory=list)
    baseline_risk: float = 0.5
    
    # Performance metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    def update_feedback(self, feedback: AuthFeedback) -> None:
        """Update profile with new feedback."""
        self.feedback_history.append(feedback)
        
        if feedback.is_false_positive:
            self.false_positive_count += 1
        elif feedback.is_false_negative:
            self.false_negative_count += 1
        elif feedback.is_correct:
            self.correct_predictions += 1
        
        self.last_updated = datetime.now()
        
        # Keep only recent feedback (last 1000 entries)
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-1000:]
    
    def update_risk_history(self, risk_score: float, max_history: int = 500) -> None:
        """Update risk score history."""
        self.risk_score_history.append(risk_score)
        
        if len(self.risk_score_history) > max_history:
            self.risk_score_history = self.risk_score_history[-max_history:]
        
        # Update baseline risk
        if len(self.risk_score_history) >= 10:
            self.baseline_risk = statistics.mean(self.risk_score_history[-50:])
        
        self.last_updated = datetime.now()
    
    def calculate_performance_metrics(self) -> None:
        """Calculate performance metrics from feedback history."""
        if not self.feedback_history:
            return
        
        total_predictions = len(self.feedback_history)
        true_positives = sum(1 for f in self.feedback_history 
                           if not f.is_false_positive and f.original_decision != 'allow')
        false_positives = self.false_positive_count
        false_negatives = self.false_negative_count
        true_negatives = total_predictions - true_positives - false_positives - false_negatives
        
        # Accuracy
        self.accuracy = (true_positives + true_negatives) / total_predictions if total_predictions > 0 else 0.0
        
        # Precision
        self.precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        
        # Recall
        self.recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        
        # F1 Score
        self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall) if (self.precision + self.recall) > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        data['feedback_history'] = [f.to_dict() for f in self.feedback_history]
        if self.adaptive_thresholds:
            data['adaptive_thresholds'] = self.adaptive_thresholds.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserAdaptiveProfile:
        """Create instance from dictionary."""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_updated'), str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        feedback_history = []
        for f_data in data.get('feedback_history', []):
            feedback_history.append(AuthFeedback.from_dict(f_data))
        data['feedback_history'] = feedback_history
        
        if data.get('adaptive_thresholds'):
            data['adaptive_thresholds'] = RiskThresholds.from_dict(data['adaptive_thresholds'])
        
        return cls(**data)


@dataclass
class LearningConfig:
    """Configuration for adaptive learning engine."""
    
    # Learning parameters
    learning_rate: float = 0.01
    adaptation_window: int = 100  # Number of recent samples to consider
    min_samples_for_adaptation: int = 10
    
    # Threshold adjustment parameters
    threshold_adjustment_step: float = 0.05
    max_threshold_adjustment: float = 0.3
    min_threshold_value: float = 0.1
    max_threshold_value: float = 0.95
    
    # Model versioning
    max_model_versions: int = 10
    auto_rollback_threshold: float = 0.1  # Performance degradation threshold
    
    # Feedback processing
    feedback_confidence_threshold: float = 0.7
    admin_feedback_weight: float = 2.0
    user_feedback_weight: float = 1.0
    system_feedback_weight: float = 0.5
    
    # Time-based adjustments
    enable_time_based_adjustments: bool = True
    time_adjustment_window: timedelta = timedelta(hours=24)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['time_adjustment_window'] = self.time_adjustment_window.total_seconds()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LearningConfig:
        """Create instance from dictionary."""
        if 'time_adjustment_window' in data:
            data['time_adjustment_window'] = timedelta(seconds=data['time_adjustment_window'])
        return cls(**data)


class AdaptiveLearningEngine(BaseIntelligentAuthService):
    """
    Adaptive learning engine for continuous model improvement through
    feedback processing, threshold adjustments, and model versioning.
    """
    
    def __init__(self, config: IntelligentAuthConfig, learning_config: Optional[LearningConfig] = None):
        super().__init__(config)
        
        self.learning_config = learning_config or LearningConfig()
        
        # User profiles for adaptive learning
        self.user_profiles: Dict[str, UserAdaptiveProfile] = {}
        self.profiles_lock = threading.RLock()
        
        # Model versioning
        self.model_versions: Dict[str, List[ModelVersion]] = defaultdict(list)
        self.active_models: Dict[str, ModelVersion] = {}
        self.versions_lock = threading.RLock()
        
        # Feedback processing
        self.feedback_queue: deque = deque(maxlen=10000)
        self.feedback_lock = threading.RLock()
        
        # Global learning metrics
        self.global_metrics = {
            'total_feedback_processed': 0,
            'false_positives_reduced': 0,
            'false_negatives_reduced': 0,
            'threshold_adjustments_made': 0,
            'model_rollbacks': 0,
            'performance_improvements': 0
        }
        
        # Caching for performance
        self.adaptation_cache = TTLCache(maxsize=1000, ttl=3600)
        self.cache_lock = threading.RLock()
        
        # Storage paths
        self.storage_path = Path("data/intelligent_auth/adaptive_learning")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("AdaptiveLearningEngine initialized")
    
    async def initialize(self) -> bool:
        """Initialize the adaptive learning engine."""
        try:
            # Load persisted user profiles
            await self._load_user_profiles()
            
            # Load model versions
            await self._load_model_versions()
            
            # Start background processing
            asyncio.create_task(self._background_feedback_processor())
            asyncio.create_task(self._background_model_optimizer())
            
            self.logger.info("AdaptiveLearningEngine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AdaptiveLearningEngine: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        try:
            # Save user profiles
            await self._save_user_profiles()
            
            # Save model versions
            await self._save_model_versions()
            
            # Clear caches
            with self.cache_lock:
                self.adaptation_cache.clear()
            
            self.logger.info("AdaptiveLearningEngine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during AdaptiveLearningEngine shutdown: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check for the adaptive learning engine."""
        try:
            # Test basic functionality
            test_feedback = AuthFeedback(
                user_id="test_user",
                request_id="test_request",
                timestamp=datetime.now(),
                original_risk_score=0.5,
                original_decision="allow",
                is_correct=True
            )
            
            # Test feedback processing
            await self.process_feedback(test_feedback)
            
            # Test threshold calculation
            thresholds = await self.get_adaptive_thresholds("test_user")
            
            return thresholds is not None
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def process_feedback(self, feedback: AuthFeedback) -> None:
        """
        Process authentication feedback for model improvement.
        
        Args:
            feedback: Authentication feedback data
        """
        try:
            # Validate feedback
            if not self._validate_feedback(feedback):
                self.logger.warning(f"Invalid feedback received: {feedback}")
                return
            
            # Add to processing queue
            with self.feedback_lock:
                self.feedback_queue.append(feedback)
            
            # Update user profile immediately for high-confidence feedback
            if feedback.confidence >= self.learning_config.feedback_confidence_threshold:
                await self._update_user_profile_with_feedback(feedback)
            
            # Update global metrics
            self.global_metrics['total_feedback_processed'] += 1
            
            self.logger.debug(f"Processed feedback for user {feedback.user_id}: {feedback.original_decision}")
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback: {e}")
    
    async def get_adaptive_thresholds(self, user_id: str) -> RiskThresholds:
        """
        Get user-specific adaptive thresholds.
        
        Args:
            user_id: User identifier
            
        Returns:
            User-specific risk thresholds or default thresholds
        """
        try:
            with self.profiles_lock:
                if user_id in self.user_profiles:
                    profile = self.user_profiles[user_id]
                    if profile.adaptive_thresholds:
                        return profile.adaptive_thresholds
            
            # Return default thresholds if no user-specific ones exist
            return self.config.risk_thresholds
            
        except Exception as e:
            self.logger.error(f"Failed to get adaptive thresholds for {user_id}: {e}")
            return self.config.risk_thresholds
    
    async def update_user_behavioral_model(self, user_id: str, auth_context: AuthContext, success: bool) -> None:
        """
        Update user-specific behavioral model based on authentication outcome.
        
        Args:
            user_id: User identifier
            auth_context: Authentication context
            success: Whether authentication was successful
        """
        try:
            with self.profiles_lock:
                if user_id not in self.user_profiles:
                    self.user_profiles[user_id] = UserAdaptiveProfile(user_id=user_id)
                
                profile = self.user_profiles[user_id]
                
                # Update behavioral patterns
                if success:
                    # Update typical patterns for successful logins
                    login_hour = auth_context.timestamp.hour
                    if login_hour not in profile.typical_login_hours:
                        profile.typical_login_hours.append(login_hour)
                    
                    # Keep only recent patterns (last 50)
                    if len(profile.typical_login_hours) > 50:
                        profile.typical_login_hours = profile.typical_login_hours[-50:]
                    
                    # Update location patterns
                    if auth_context.geolocation and auth_context.geolocation.country:
                        location_key = f"{auth_context.geolocation.country}:{auth_context.geolocation.city}"
                        if location_key not in profile.typical_locations:
                            profile.typical_locations.append(location_key)
                        
                        if len(profile.typical_locations) > 20:
                            profile.typical_locations = profile.typical_locations[-20:]
                    
                    # Update device patterns
                    if auth_context.device_fingerprint:
                        if auth_context.device_fingerprint not in profile.typical_devices:
                            profile.typical_devices.append(auth_context.device_fingerprint)
                        
                        if len(profile.typical_devices) > 10:
                            profile.typical_devices = profile.typical_devices[-10:]
                
                profile.last_updated = datetime.now()
            
            self.logger.debug(f"Updated behavioral model for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update behavioral model for {user_id}: {e}")
    
    async def create_model_version(self, model_type: str, model_data: Dict[str, Any], performance_metrics: Optional[Dict[str, float]] = None) -> str:
        """
        Create a new model version for tracking and rollback.
        
        Args:
            model_type: Type of model ('thresholds', 'weights', 'behavioral_model')
            model_data: Model data to version
            performance_metrics: Optional performance metrics
            
        Returns:
            Version ID of the created model
        """
        try:
            version_id = f"{model_type}_{int(time.time())}"
            
            model_version = ModelVersion(
                version_id=version_id,
                created_at=datetime.now(),
                model_type=model_type,
                model_data=model_data.copy(),
                performance_metrics=performance_metrics or {},
                is_active=True
            )
            
            with self.versions_lock:
                # Deactivate previous version
                if model_type in self.active_models:
                    self.active_models[model_type].is_active = False
                
                # Add new version
                self.model_versions[model_type].append(model_version)
                self.active_models[model_type] = model_version
                
                # Limit number of stored versions
                if len(self.model_versions[model_type]) > self.learning_config.max_model_versions:
                    self.model_versions[model_type] = self.model_versions[model_type][-self.learning_config.max_model_versions:]
            
            self.logger.info(f"Created model version {version_id} for {model_type}")
            return version_id
            
        except Exception as e:
            self.logger.error(f"Failed to create model version: {e}")
            return ""
    
    async def rollback_model(self, model_type: str, target_version_id: Optional[str] = None, reason: str = "manual_rollback") -> bool:
        """
        Rollback model to a previous version.
        
        Args:
            model_type: Type of model to rollback
            target_version_id: Specific version to rollback to (None for previous version)
            reason: Reason for rollback
            
        Returns:
            True if rollback was successful
        """
        try:
            with self.versions_lock:
                if model_type not in self.model_versions or not self.model_versions[model_type]:
                    self.logger.warning(f"No versions available for model type {model_type}")
                    return False
                
                versions = self.model_versions[model_type]
                target_version = None
                
                if target_version_id:
                    # Find specific version
                    target_version = next((v for v in versions if v.version_id == target_version_id), None)
                else:
                    # Get previous version (second to last)
                    if len(versions) >= 2:
                        target_version = versions[-2]
                
                if not target_version:
                    self.logger.warning(f"Target version not found for rollback: {target_version_id}")
                    return False
                
                # Deactivate current version
                if model_type in self.active_models:
                    self.active_models[model_type].is_active = False
                    self.active_models[model_type].rollback_reason = reason
                
                # Activate target version
                target_version.is_active = True
                self.active_models[model_type] = target_version
                
                # Update metrics
                self.global_metrics['model_rollbacks'] += 1
            
            self.logger.info(f"Rolled back {model_type} to version {target_version.version_id}: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback model {model_type}: {e}")
            return False
    
    async def get_model_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive model performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        try:
            metrics = {
                'global_metrics': self.global_metrics.copy(),
                'user_metrics': {},
                'model_versions': {},
                'learning_config': self.learning_config.to_dict()
            }
            
            # User-specific metrics
            with self.profiles_lock:
                for user_id, profile in self.user_profiles.items():
                    profile.calculate_performance_metrics()
                    metrics['user_metrics'][user_id] = {
                        'accuracy': profile.accuracy,
                        'precision': profile.precision,
                        'recall': profile.recall,
                        'f1_score': profile.f1_score,
                        'false_positives': profile.false_positive_count,
                        'false_negatives': profile.false_negative_count,
                        'correct_predictions': profile.correct_predictions,
                        'baseline_risk': profile.baseline_risk,
                        'last_updated': profile.last_updated.isoformat()
                    }
            
            # Model version metrics
            with self.versions_lock:
                for model_type, versions in self.model_versions.items():
                    metrics['model_versions'][model_type] = {
                        'total_versions': len(versions),
                        'active_version': self.active_models.get(model_type, {}).version_id if model_type in self.active_models else None,
                        'latest_performance': versions[-1].performance_metrics if versions else {}
                    }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    async def _update_user_profile_with_feedback(self, feedback: AuthFeedback) -> None:
        """Update user profile with feedback data."""
        try:
            with self.profiles_lock:
                if feedback.user_id not in self.user_profiles:
                    self.user_profiles[feedback.user_id] = UserAdaptiveProfile(user_id=feedback.user_id)
                
                profile = self.user_profiles[feedback.user_id]
                profile.update_feedback(feedback)
                
                # Adjust thresholds based on feedback
                if feedback.is_false_positive:
                    await self._adjust_user_thresholds(feedback.user_id, increase_threshold=True)
                    self.global_metrics['false_positives_reduced'] += 1
                elif feedback.is_false_negative:
                    await self._adjust_user_thresholds(feedback.user_id, increase_threshold=False)
                    self.global_metrics['false_negatives_reduced'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to update user profile with feedback: {e}")
    
    async def _adjust_user_thresholds(self, user_id: str, increase_threshold: bool) -> None:
        """Adjust user-specific thresholds based on feedback."""
        try:
            with self.profiles_lock:
                if user_id not in self.user_profiles:
                    return
                
                profile = self.user_profiles[user_id]
                
                if not profile.adaptive_thresholds:
                    profile.adaptive_thresholds = RiskThresholds(
                        low_risk_threshold=self.config.risk_thresholds.low_risk_threshold,
                        medium_risk_threshold=self.config.risk_thresholds.medium_risk_threshold,
                        high_risk_threshold=self.config.risk_thresholds.high_risk_threshold,
                        critical_risk_threshold=self.config.risk_thresholds.critical_risk_threshold
                    )
                
                adjustment = self.learning_config.threshold_adjustment_step
                if not increase_threshold:
                    adjustment = -adjustment
                
                # Apply adjustment with bounds checking
                thresholds = profile.adaptive_thresholds
                
                thresholds.low_risk_threshold = max(
                    self.learning_config.min_threshold_value,
                    min(self.learning_config.max_threshold_value, thresholds.low_risk_threshold + adjustment)
                )
                
                thresholds.medium_risk_threshold = max(
                    thresholds.low_risk_threshold + 0.1,
                    min(self.learning_config.max_threshold_value, thresholds.medium_risk_threshold + adjustment)
                )
                
                thresholds.high_risk_threshold = max(
                    thresholds.medium_risk_threshold + 0.1,
                    min(self.learning_config.max_threshold_value, thresholds.high_risk_threshold + adjustment)
                )
                
                thresholds.critical_risk_threshold = max(
                    thresholds.high_risk_threshold + 0.05,
                    min(1.0, thresholds.critical_risk_threshold + adjustment)
                )
                
                # Record adjustment
                adjustment_record = {
                    'timestamp': datetime.now().isoformat(),
                    'adjustment': adjustment,
                    'reason': 'false_positive' if increase_threshold else 'false_negative',
                    'new_thresholds': thresholds.to_dict()
                }
                profile.threshold_adjustment_history.append(adjustment_record)
                
                # Keep only recent adjustments
                if len(profile.threshold_adjustment_history) > 100:
                    profile.threshold_adjustment_history = profile.threshold_adjustment_history[-100:]
                
                self.global_metrics['threshold_adjustments_made'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to adjust thresholds for {user_id}: {e}")
    
    def _validate_feedback(self, feedback: AuthFeedback) -> bool:
        """Validate feedback data."""
        try:
            return (
                bool(feedback.user_id) and
                bool(feedback.request_id) and
                isinstance(feedback.timestamp, datetime) and
                0.0 <= feedback.original_risk_score <= 1.0 and
                feedback.original_decision in ['allow', 'block', 'require_2fa'] and
                0.0 <= feedback.confidence <= 1.0
            )
        except Exception:
            return False
    
    async def _background_feedback_processor(self) -> None:
        """Background task to process feedback queue."""
        while True:
            try:
                await asyncio.sleep(10)  # Process every 10 seconds
                
                feedback_batch = []
                with self.feedback_lock:
                    # Process up to 100 feedback items at a time
                    for _ in range(min(100, len(self.feedback_queue))):
                        if self.feedback_queue:
                            feedback_batch.append(self.feedback_queue.popleft())
                
                for feedback in feedback_batch:
                    if feedback.confidence < self.learning_config.feedback_confidence_threshold:
                        await self._update_user_profile_with_feedback(feedback)
                
            except Exception as e:
                self.logger.error(f"Background feedback processing error: {e}")
    
    async def _background_model_optimizer(self) -> None:
        """Background task to optimize models based on performance."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Check for performance degradation and auto-rollback if needed
                await self._check_and_rollback_underperforming_models()
                
                # Optimize user profiles
                await self._optimize_user_profiles()
                
            except Exception as e:
                self.logger.error(f"Background model optimization error: {e}")
    
    async def _check_and_rollback_underperforming_models(self) -> None:
        """Check for underperforming models and rollback if necessary."""
        try:
            with self.versions_lock:
                for model_type, versions in self.model_versions.items():
                    if len(versions) < 2:
                        continue
                    
                    current_version = versions[-1]
                    previous_version = versions[-2]
                    
                    # Compare performance metrics
                    current_performance = current_version.performance_metrics.get('f1_score', 0.0)
                    previous_performance = previous_version.performance_metrics.get('f1_score', 0.0)
                    
                    # Check for significant degradation
                    if (previous_performance - current_performance) > self.learning_config.auto_rollback_threshold:
                        await self.rollback_model(
                            model_type,
                            previous_version.version_id,
                            f"auto_rollback_performance_degradation_{current_performance:.3f}_to_{previous_performance:.3f}"
                        )
            
        except Exception as e:
            self.logger.error(f"Failed to check underperforming models: {e}")
    
    async def _optimize_user_profiles(self) -> None:
        """Optimize user profiles by removing stale data and updating metrics."""
        try:
            cutoff_time = datetime.now() - timedelta(days=90)
            
            with self.profiles_lock:
                for user_id, profile in list(self.user_profiles.items()):
                    # Remove old feedback
                    profile.feedback_history = [
                        f for f in profile.feedback_history
                        if f.timestamp > cutoff_time
                    ]
                    
                    # Remove profiles with no recent activity
                    if profile.last_updated < cutoff_time and not profile.feedback_history:
                        del self.user_profiles[user_id]
                        continue
                    
                    # Recalculate performance metrics
                    profile.calculate_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to optimize user profiles: {e}")
    
    async def _load_user_profiles(self) -> None:
        """Load user profiles from persistent storage."""
        try:
            profiles_file = self.storage_path / "user_profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                
                with self.profiles_lock:
                    for user_id, profile_data in data.items():
                        self.user_profiles[user_id] = UserAdaptiveProfile.from_dict(profile_data)
                
                self.logger.info(f"Loaded {len(self.user_profiles)} user profiles")
            
        except Exception as e:
            self.logger.error(f"Failed to load user profiles: {e}")
    
    async def _save_user_profiles(self) -> None:
        """Save user profiles to persistent storage."""
        try:
            # Ensure storage directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)
            profiles_file = self.storage_path / "user_profiles.json"
            
            with self.profiles_lock:
                data = {
                    user_id: profile.to_dict()
                    for user_id, profile in self.user_profiles.items()
                }
            
            with open(profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.user_profiles)} user profiles")
            
        except Exception as e:
            self.logger.error(f"Failed to save user profiles: {e}")
    
    async def _load_model_versions(self) -> None:
        """Load model versions from persistent storage."""
        try:
            versions_file = self.storage_path / "model_versions.json"
            if versions_file.exists():
                with open(versions_file, 'r') as f:
                    data = json.load(f)
                
                with self.versions_lock:
                    for model_type, versions_data in data.items():
                        versions = [ModelVersion.from_dict(v) for v in versions_data]
                        self.model_versions[model_type] = versions
                        
                        # Find active version
                        active_version = next((v for v in versions if v.is_active), None)
                        if active_version:
                            self.active_models[model_type] = active_version
                
                total_versions = sum(len(versions) for versions in self.model_versions.values())
                self.logger.info(f"Loaded {total_versions} model versions")
            
        except Exception as e:
            self.logger.error(f"Failed to load model versions: {e}")
    
    async def _save_model_versions(self) -> None:
        """Save model versions to persistent storage."""
        try:
            # Ensure storage directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)
            versions_file = self.storage_path / "model_versions.json"
            
            with self.versions_lock:
                data = {
                    model_type: [version.to_dict() for version in versions]
                    for model_type, versions in self.model_versions.items()
                }
            
            with open(versions_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            total_versions = sum(len(versions) for versions in self.model_versions.values())
            self.logger.info(f"Saved {total_versions} model versions")
            
        except Exception as e:
            self.logger.error(f"Failed to save model versions: {e}")