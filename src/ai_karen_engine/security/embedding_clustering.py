"""
Embedding clustering and outlier detection service for intelligent authentication system.

This module provides clustering algorithms for grouping similar login patterns,
outlier detection for identifying anomalous embedding vectors, and dynamic
threshold adjustment based on user behavior history.
"""

from __future__ import annotations

import logging
import time
import math
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import numpy as np

try:
    from ai_karen_engine.security.behavioral_embedding import (
        BehavioralEmbeddingResult, UserBehavioralProfile
    )
    from ai_karen_engine.security.models import AuthContext
except ImportError:
    # Fallback imports for testing
    from behavioral_embedding import BehavioralEmbeddingResult, UserBehavioralProfile
    from models import AuthContext

logger = logging.getLogger(__name__)


@dataclass
class ClusterInfo:
    """Information about a cluster of embeddings."""
    
    cluster_id: str
    centroid: List[float]
    embeddings: List[List[float]] = field(default_factory=list)
    user_ids: Set[str] = field(default_factory=set)
    timestamps: List[datetime] = field(default_factory=list)
    cluster_size: int = 0
    intra_cluster_distance: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'cluster_id': self.cluster_id,
            'centroid': self.centroid,
            'embeddings': self.embeddings,
            'user_ids': list(self.user_ids),
            'timestamps': [ts.isoformat() for ts in self.timestamps],
            'cluster_size': self.cluster_size,
            'intra_cluster_distance': self.intra_cluster_distance,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClusterInfo:
        """Create instance from dictionary."""
        return cls(
            cluster_id=data['cluster_id'],
            centroid=data['centroid'],
            embeddings=data.get('embeddings', []),
            user_ids=set(data.get('user_ids', [])),
            timestamps=[datetime.fromisoformat(ts) for ts in data.get('timestamps', [])],
            cluster_size=data.get('cluster_size', 0),
            intra_cluster_distance=data.get('intra_cluster_distance', 0.0),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        )


@dataclass
class OutlierDetectionResult:
    """Result of outlier detection analysis."""
    
    is_outlier: bool
    outlier_score: float
    distance_to_nearest_cluster: float
    nearest_cluster_id: Optional[str]
    confidence: float
    detection_method: str
    threshold_used: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'is_outlier': self.is_outlier,
            'outlier_score': self.outlier_score,
            'distance_to_nearest_cluster': self.distance_to_nearest_cluster,
            'nearest_cluster_id': self.nearest_cluster_id,
            'confidence': self.confidence,
            'detection_method': self.detection_method,
            'threshold_used': self.threshold_used
        }


@dataclass
class ClusteringConfig:
    """Configuration for embedding clustering service."""
    
    # Clustering parameters
    max_clusters: int = 20
    min_cluster_size: int = 3
    max_cluster_distance: float = 0.3
    cluster_merge_threshold: float = 0.15
    
    # Outlier detection parameters
    outlier_threshold: float = 0.7
    min_samples_for_outlier: int = 10
    outlier_percentile: float = 95.0
    
    # Dynamic threshold adjustment
    enable_dynamic_thresholds: bool = True
    threshold_adaptation_rate: float = 0.1
    min_threshold: float = 0.3
    max_threshold: float = 0.9
    
    # Performance settings
    max_embeddings_per_cluster: int = 100
    cluster_update_interval: int = 3600  # seconds
    enable_incremental_clustering: bool = True


class EmbeddingClusteringService:
    """
    Service for clustering embeddings and detecting outliers in authentication patterns.
    """
    
    def __init__(self, config: Optional[ClusteringConfig] = None):
        self.config = config or ClusteringConfig()
        self.logger = logger
        
        # Cluster storage
        self.clusters: Dict[str, ClusterInfo] = {}
        self.clusters_lock = threading.RLock()
        
        # User-specific clustering
        self.user_clusters: Dict[str, Dict[str, ClusterInfo]] = defaultdict(dict)
        self.user_clusters_lock = threading.RLock()
        
        # Global clustering for attack pattern detection
        self.global_clusters: Dict[str, ClusterInfo] = {}
        self.global_clusters_lock = threading.RLock()
        
        # Dynamic thresholds
        self.user_thresholds: Dict[str, float] = {}
        self.threshold_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.thresholds_lock = threading.RLock()
        
        # Metrics
        self._clustering_operations = 0
        self._outlier_detections = 0
        self._threshold_adjustments = 0
        self._cluster_merges = 0
        
        self.logger.info("EmbeddingClusteringService initialized")
    
    def add_embedding_to_clusters(
        self,
        user_id: str,
        embedding: List[float],
        auth_context: AuthContext,
        is_successful_login: bool = True
    ) -> Optional[str]:
        """
        Add embedding to appropriate clusters and return cluster assignment.
        
        Args:
            user_id: User identifier
            embedding: Embedding vector
            auth_context: Authentication context
            is_successful_login: Whether the login was successful
            
        Returns:
            Cluster ID if assigned, None otherwise
        """
        if not is_successful_login:
            return None  # Only cluster successful logins
        
        try:
            # Add to user-specific clusters
            user_cluster_id = self._add_to_user_clusters(user_id, embedding, auth_context)
            
            # Add to global clusters for attack pattern detection
            global_cluster_id = self._add_to_global_clusters(embedding, auth_context)
            
            self._clustering_operations += 1
            
            return user_cluster_id or global_cluster_id
            
        except Exception as e:
            self.logger.error(f"Failed to add embedding to clusters: {e}")
            return None
    
    def detect_outlier(
        self,
        user_id: str,
        embedding: List[float],
        auth_context: AuthContext
    ) -> OutlierDetectionResult:
        """
        Detect if an embedding is an outlier based on clustering analysis.
        
        Args:
            user_id: User identifier
            embedding: Embedding vector to analyze
            auth_context: Authentication context
            
        Returns:
            OutlierDetectionResult with detection details
        """
        try:
            # Get user-specific threshold
            threshold = self._get_dynamic_threshold(user_id)
            
            # Check against user-specific clusters first
            user_result = self._detect_outlier_in_user_clusters(
                user_id, embedding, threshold
            )
            
            if user_result.is_outlier:
                # Also check against global clusters for attack patterns
                global_result = self._detect_outlier_in_global_clusters(
                    embedding, threshold
                )
                
                # Combine results (user-specific takes precedence)
                final_result = OutlierDetectionResult(
                    is_outlier=True,
                    outlier_score=max(user_result.outlier_score, global_result.outlier_score),
                    distance_to_nearest_cluster=min(
                        user_result.distance_to_nearest_cluster,
                        global_result.distance_to_nearest_cluster
                    ),
                    nearest_cluster_id=user_result.nearest_cluster_id,
                    confidence=user_result.confidence,
                    detection_method="user_and_global_clustering",
                    threshold_used=threshold
                )
            else:
                final_result = user_result
            
            self._outlier_detections += 1
            
            # Update dynamic threshold based on result
            if self.config.enable_dynamic_thresholds:
                self._update_dynamic_threshold(user_id, final_result)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Failed to detect outlier: {e}")
            return OutlierDetectionResult(
                is_outlier=False,
                outlier_score=0.0,
                distance_to_nearest_cluster=1.0,
                nearest_cluster_id=None,
                confidence=0.0,
                detection_method="error_fallback",
                threshold_used=self.config.outlier_threshold
            )
    
    def _add_to_user_clusters(
        self,
        user_id: str,
        embedding: List[float],
        auth_context: AuthContext
    ) -> Optional[str]:
        """Add embedding to user-specific clusters."""
        with self.user_clusters_lock:
            user_clusters = self.user_clusters[user_id]
            
            # Find nearest cluster
            nearest_cluster_id, min_distance = self._find_nearest_cluster(
                embedding, user_clusters
            )
            
            if (nearest_cluster_id and 
                min_distance <= self.config.max_cluster_distance):
                # Add to existing cluster
                cluster = user_clusters[nearest_cluster_id]
                self._add_embedding_to_cluster(cluster, embedding, user_id, auth_context)
                return nearest_cluster_id
            else:
                # Create new cluster
                if len(user_clusters) < self.config.max_clusters:
                    cluster_id = f"user_{user_id}_{len(user_clusters)}"
                    new_cluster = ClusterInfo(
                        cluster_id=cluster_id,
                        centroid=embedding.copy(),
                        embeddings=[embedding],
                        user_ids={user_id},
                        timestamps=[auth_context.timestamp],
                        cluster_size=1
                    )
                    user_clusters[cluster_id] = new_cluster
                    return cluster_id
                else:
                    # Merge with nearest cluster if max clusters reached
                    if nearest_cluster_id:
                        cluster = user_clusters[nearest_cluster_id]
                        self._add_embedding_to_cluster(cluster, embedding, user_id, auth_context)
                        return nearest_cluster_id
        
        return None
    
    def _add_to_global_clusters(
        self,
        embedding: List[float],
        auth_context: AuthContext
    ) -> Optional[str]:
        """Add embedding to global clusters for attack pattern detection."""
        with self.global_clusters_lock:
            # Find nearest global cluster
            nearest_cluster_id, min_distance = self._find_nearest_cluster(
                embedding, self.global_clusters
            )
            
            if (nearest_cluster_id and 
                min_distance <= self.config.max_cluster_distance):
                # Add to existing global cluster
                cluster = self.global_clusters[nearest_cluster_id]
                self._add_embedding_to_cluster(
                    cluster, embedding, auth_context.email, auth_context
                )
                return nearest_cluster_id
            else:
                # Create new global cluster
                if len(self.global_clusters) < self.config.max_clusters * 2:  # More global clusters
                    cluster_id = f"global_{len(self.global_clusters)}"
                    new_cluster = ClusterInfo(
                        cluster_id=cluster_id,
                        centroid=embedding.copy(),
                        embeddings=[embedding],
                        user_ids={auth_context.email},
                        timestamps=[auth_context.timestamp],
                        cluster_size=1
                    )
                    self.global_clusters[cluster_id] = new_cluster
                    return cluster_id
        
        return None
    
    def _find_nearest_cluster(
        self,
        embedding: List[float],
        clusters: Dict[str, ClusterInfo]
    ) -> Tuple[Optional[str], float]:
        """Find the nearest cluster to an embedding."""
        if not clusters:
            return None, float('inf')
        
        min_distance = float('inf')
        nearest_cluster_id = None
        
        for cluster_id, cluster in clusters.items():
            distance = self._calculate_distance(embedding, cluster.centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_cluster_id = cluster_id
        
        return nearest_cluster_id, min_distance
    
    def _add_embedding_to_cluster(
        self,
        cluster: ClusterInfo,
        embedding: List[float],
        user_id: str,
        auth_context: AuthContext
    ) -> None:
        """Add embedding to an existing cluster and update centroid."""
        cluster.embeddings.append(embedding)
        cluster.user_ids.add(user_id)
        cluster.timestamps.append(auth_context.timestamp)
        cluster.cluster_size += 1
        cluster.last_updated = datetime.now()
        
        # Update centroid using incremental mean
        if len(cluster.centroid) == len(embedding):
            for i in range(len(cluster.centroid)):
                cluster.centroid[i] = (
                    (cluster.centroid[i] * (cluster.cluster_size - 1) + embedding[i]) /
                    cluster.cluster_size
                )
        
        # Limit cluster size for performance
        if len(cluster.embeddings) > self.config.max_embeddings_per_cluster:
            # Remove oldest embeddings
            cluster.embeddings = cluster.embeddings[-self.config.max_embeddings_per_cluster:]
            cluster.timestamps = cluster.timestamps[-self.config.max_embeddings_per_cluster:]
        
        # Update intra-cluster distance
        cluster.intra_cluster_distance = self._calculate_intra_cluster_distance(cluster)
    
    def _calculate_intra_cluster_distance(self, cluster: ClusterInfo) -> float:
        """Calculate average intra-cluster distance."""
        if cluster.cluster_size < 2:
            return 0.0
        
        total_distance = 0.0
        count = 0
        
        # Sample a subset for performance if cluster is large
        embeddings = cluster.embeddings
        if len(embeddings) > 20:
            # Sample 20 embeddings for distance calculation
            step = len(embeddings) // 20
            embeddings = embeddings[::step]
        
        for i, emb1 in enumerate(embeddings):
            for emb2 in embeddings[i+1:]:
                total_distance += self._calculate_distance(emb1, emb2)
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def _detect_outlier_in_user_clusters(
        self,
        user_id: str,
        embedding: List[float],
        threshold: float
    ) -> OutlierDetectionResult:
        """Detect outlier in user-specific clusters."""
        with self.user_clusters_lock:
            user_clusters = self.user_clusters.get(user_id, {})
            
            if not user_clusters:
                # No user clusters yet - not necessarily an outlier
                return OutlierDetectionResult(
                    is_outlier=False,
                    outlier_score=0.5,
                    distance_to_nearest_cluster=1.0,
                    nearest_cluster_id=None,
                    confidence=0.3,
                    detection_method="no_user_clusters",
                    threshold_used=threshold
                )
            
            # Find distance to nearest user cluster
            nearest_cluster_id, min_distance = self._find_nearest_cluster(
                embedding, user_clusters
            )
            
            # Calculate outlier score based on distance
            outlier_score = min(1.0, min_distance / threshold)
            is_outlier = outlier_score > threshold
            
            # Calculate confidence based on cluster maturity
            nearest_cluster = user_clusters.get(nearest_cluster_id)
            confidence = 0.5
            if nearest_cluster:
                confidence = min(1.0, nearest_cluster.cluster_size / 10.0)
            
            return OutlierDetectionResult(
                is_outlier=is_outlier,
                outlier_score=outlier_score,
                distance_to_nearest_cluster=min_distance,
                nearest_cluster_id=nearest_cluster_id,
                confidence=confidence,
                detection_method="user_clustering",
                threshold_used=threshold
            )
    
    def _detect_outlier_in_global_clusters(
        self,
        embedding: List[float],
        threshold: float
    ) -> OutlierDetectionResult:
        """Detect outlier in global clusters."""
        with self.global_clusters_lock:
            if not self.global_clusters:
                return OutlierDetectionResult(
                    is_outlier=False,
                    outlier_score=0.5,
                    distance_to_nearest_cluster=1.0,
                    nearest_cluster_id=None,
                    confidence=0.3,
                    detection_method="no_global_clusters",
                    threshold_used=threshold
                )
            
            # Find distance to nearest global cluster
            nearest_cluster_id, min_distance = self._find_nearest_cluster(
                embedding, self.global_clusters
            )
            
            # Calculate outlier score
            outlier_score = min(1.0, min_distance / threshold)
            is_outlier = outlier_score > threshold
            
            # Global clusters have lower confidence for individual users
            confidence = 0.4
            
            return OutlierDetectionResult(
                is_outlier=is_outlier,
                outlier_score=outlier_score,
                distance_to_nearest_cluster=min_distance,
                nearest_cluster_id=nearest_cluster_id,
                confidence=confidence,
                detection_method="global_clustering",
                threshold_used=threshold
            )
    
    def _get_dynamic_threshold(self, user_id: str) -> float:
        """Get dynamic threshold for user-specific outlier detection."""
        with self.thresholds_lock:
            if user_id in self.user_thresholds:
                return self.user_thresholds[user_id]
            else:
                # Initialize with default threshold
                self.user_thresholds[user_id] = self.config.outlier_threshold
                return self.config.outlier_threshold
    
    def _update_dynamic_threshold(
        self,
        user_id: str,
        detection_result: OutlierDetectionResult
    ) -> None:
        """Update dynamic threshold based on detection results."""
        if not self.config.enable_dynamic_thresholds:
            return
        
        with self.thresholds_lock:
            current_threshold = self.user_thresholds.get(
                user_id, self.config.outlier_threshold
            )
            
            # Adjust threshold based on detection result
            if detection_result.is_outlier and detection_result.confidence > 0.7:
                # High confidence outlier - slightly lower threshold for sensitivity
                adjustment = -self.config.threshold_adaptation_rate * 0.5
            elif not detection_result.is_outlier and detection_result.confidence > 0.7:
                # High confidence normal - slightly raise threshold to reduce false positives
                adjustment = self.config.threshold_adaptation_rate * 0.3
            else:
                # Low confidence - minimal adjustment
                adjustment = 0.0
            
            new_threshold = current_threshold + adjustment
            new_threshold = max(self.config.min_threshold, 
                              min(self.config.max_threshold, new_threshold))
            
            self.user_thresholds[user_id] = new_threshold
            
            # Record threshold history
            self.threshold_history[user_id].append((datetime.now(), new_threshold))
            if len(self.threshold_history[user_id]) > 100:
                self.threshold_history[user_id] = self.threshold_history[user_id][-100:]
            
            self._threshold_adjustments += 1
    
    def _calculate_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors."""
        if len(vec1) != len(vec2):
            return float('inf')
        
        try:
            # Use numpy if available for better performance
            import numpy as np
            # Convert to numpy arrays and handle potential stub issues
            arr1 = np.asarray(vec1, dtype=np.float64)
            arr2 = np.asarray(vec2, dtype=np.float64)
            diff = arr1 - arr2
            return float(np.sqrt(np.sum(diff * diff)))
        except (ImportError, TypeError, AttributeError):
            # Fallback to manual calculation
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
    
    def merge_similar_clusters(self, user_id: Optional[str] = None) -> int:
        """
        Merge similar clusters to optimize cluster structure.
        
        Args:
            user_id: If provided, merge only user-specific clusters
            
        Returns:
            Number of clusters merged
        """
        merged_count = 0
        
        if user_id:
            # Merge user-specific clusters
            with self.user_clusters_lock:
                user_clusters = self.user_clusters.get(user_id, {})
                merged_count += self._merge_clusters_in_dict(user_clusters)
        else:
            # Merge global clusters
            with self.global_clusters_lock:
                merged_count += self._merge_clusters_in_dict(self.global_clusters)
            
            # Merge all user clusters
            with self.user_clusters_lock:
                for uid in self.user_clusters:
                    merged_count += self._merge_clusters_in_dict(self.user_clusters[uid])
        
        self._cluster_merges += merged_count
        return merged_count
    
    def _merge_clusters_in_dict(self, clusters: Dict[str, ClusterInfo]) -> int:
        """Merge similar clusters within a cluster dictionary."""
        merged_count = 0
        cluster_ids = list(clusters.keys())
        
        i = 0
        while i < len(cluster_ids):
            cluster1_id = cluster_ids[i]
            if cluster1_id not in clusters:
                i += 1
                continue
            
            cluster1 = clusters[cluster1_id]
            
            j = i + 1
            while j < len(cluster_ids):
                cluster2_id = cluster_ids[j]
                if cluster2_id not in clusters:
                    j += 1
                    continue
                
                cluster2 = clusters[cluster2_id]
                
                # Check if clusters should be merged
                distance = self._calculate_distance(cluster1.centroid, cluster2.centroid)
                if distance <= self.config.cluster_merge_threshold:
                    # Merge cluster2 into cluster1
                    self._merge_two_clusters(cluster1, cluster2)
                    del clusters[cluster2_id]
                    cluster_ids.remove(cluster2_id)
                    merged_count += 1
                else:
                    j += 1
            
            i += 1
        
        return merged_count
    
    def _merge_two_clusters(self, cluster1: ClusterInfo, cluster2: ClusterInfo) -> None:
        """Merge cluster2 into cluster1."""
        total_size = cluster1.cluster_size + cluster2.cluster_size
        
        # Update centroid as weighted average
        for i in range(len(cluster1.centroid)):
            cluster1.centroid[i] = (
                (cluster1.centroid[i] * cluster1.cluster_size +
                 cluster2.centroid[i] * cluster2.cluster_size) / total_size
            )
        
        # Merge embeddings (keep most recent if over limit)
        all_embeddings = cluster1.embeddings + cluster2.embeddings
        all_timestamps = cluster1.timestamps + cluster2.timestamps
        
        if len(all_embeddings) > self.config.max_embeddings_per_cluster:
            # Sort by timestamp and keep most recent
            combined = list(zip(all_timestamps, all_embeddings))
            combined.sort(key=lambda x: x[0], reverse=True)
            
            cluster1.timestamps = [ts for ts, _ in combined[:self.config.max_embeddings_per_cluster]]
            cluster1.embeddings = [emb for _, emb in combined[:self.config.max_embeddings_per_cluster]]
        else:
            cluster1.embeddings = all_embeddings
            cluster1.timestamps = all_timestamps
        
        # Merge other attributes
        cluster1.user_ids.update(cluster2.user_ids)
        cluster1.cluster_size = total_size
        cluster1.last_updated = max(cluster1.last_updated, cluster2.last_updated)
        
        # Recalculate intra-cluster distance
        cluster1.intra_cluster_distance = self._calculate_intra_cluster_distance(cluster1)
    
    def get_cluster_info(self, user_id: str) -> Dict[str, Any]:
        """Get clustering information for a user."""
        with self.user_clusters_lock:
            user_clusters = self.user_clusters.get(user_id, {})
            
            cluster_info = {
                'user_cluster_count': len(user_clusters),
                'user_clusters': {
                    cid: {
                        'size': cluster.cluster_size,
                        'intra_distance': cluster.intra_cluster_distance,
                        'last_updated': cluster.last_updated.isoformat(),
                        'user_count': len(cluster.user_ids)
                    }
                    for cid, cluster in user_clusters.items()
                }
            }
        
        with self.global_clusters_lock:
            cluster_info['global_cluster_count'] = len(self.global_clusters)
        
        with self.thresholds_lock:
            cluster_info['dynamic_threshold'] = self.user_thresholds.get(
                user_id, self.config.outlier_threshold
            )
        
        return cluster_info
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the clustering service."""
        with self.user_clusters_lock:
            total_user_clusters = sum(len(clusters) for clusters in self.user_clusters.values())
            users_with_clusters = len(self.user_clusters)
        
        with self.global_clusters_lock:
            global_cluster_count = len(self.global_clusters)
        
        with self.thresholds_lock:
            users_with_dynamic_thresholds = len(self.user_thresholds)
        
        return {
            'is_healthy': True,
            'total_user_clusters': total_user_clusters,
            'users_with_clusters': users_with_clusters,
            'global_cluster_count': global_cluster_count,
            'users_with_dynamic_thresholds': users_with_dynamic_thresholds,
            'clustering_operations': self._clustering_operations,
            'outlier_detections': self._outlier_detections,
            'threshold_adjustments': self._threshold_adjustments,
            'cluster_merges': self._cluster_merges,
            'config': {
                'max_clusters': self.config.max_clusters,
                'outlier_threshold': self.config.outlier_threshold,
                'enable_dynamic_thresholds': self.config.enable_dynamic_thresholds
            }
        }
    
    def cleanup_old_clusters(self, max_age_days: int = 30) -> int:
        """Clean up old clusters that haven't been updated recently."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        # Clean user clusters
        with self.user_clusters_lock:
            for user_id in list(self.user_clusters.keys()):
                user_clusters = self.user_clusters[user_id]
                for cluster_id in list(user_clusters.keys()):
                    if user_clusters[cluster_id].last_updated < cutoff_date:
                        del user_clusters[cluster_id]
                        removed_count += 1
                
                # Remove empty user cluster dictionaries
                if not user_clusters:
                    del self.user_clusters[user_id]
        
        # Clean global clusters
        with self.global_clusters_lock:
            for cluster_id in list(self.global_clusters.keys()):
                if self.global_clusters[cluster_id].last_updated < cutoff_date:
                    del self.global_clusters[cluster_id]
                    removed_count += 1
        
        self.logger.info(f"Cleaned up {removed_count} old clusters")
        return removed_count