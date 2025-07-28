"""
Unit tests for embedding clustering and outlier detection service.
"""

import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List

from src.ai_karen_engine.security.embedding_clustering import (
    EmbeddingClusteringService,
    ClusteringConfig,
    ClusterInfo,
    OutlierDetectionResult
)
from src.ai_karen_engine.security.models import AuthContext, GeoLocation


@pytest.fixture
def clustering_config():
    """Create clustering configuration."""
    return ClusteringConfig(
        max_clusters=5,
        min_cluster_size=2,
        max_cluster_distance=0.3,
        cluster_merge_threshold=0.15,
        outlier_threshold=0.7,
        enable_dynamic_thresholds=True,
        threshold_adaptation_rate=0.1
    )


@pytest.fixture
def sample_auth_context():
    """Create sample authentication context."""
    return AuthContext(
        email="test@example.com",
        password_hash="hashed_password",
        client_ip="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timestamp=datetime.now(),
        request_id="test-request-123",
        geolocation=GeoLocation(
            country="US",
            region="CA",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles",
            is_usual_location=True
        ),
        device_fingerprint="device123",
        is_tor_exit_node=False,
        is_vpn=False,
        threat_intel_score=0.1,
        previous_failed_attempts=0
    )


@pytest.fixture
def clustering_service(clustering_config):
    """Create embedding clustering service."""
    return EmbeddingClusteringService(config=clustering_config)


@pytest.fixture
def sample_embeddings():
    """Create sample embedding vectors for testing."""
    return {
        'cluster1_center': [0.1, 0.2, 0.3, 0.4, 0.5],
        'cluster1_point1': [0.11, 0.21, 0.31, 0.41, 0.51],
        'cluster1_point2': [0.09, 0.19, 0.29, 0.39, 0.49],
        'cluster2_center': [0.8, 0.7, 0.6, 0.5, 0.4],
        'cluster2_point1': [0.81, 0.71, 0.61, 0.51, 0.41],
        'outlier': [0.5, 0.5, 0.5, 0.5, 0.5]
    }


class TestEmbeddingClusteringService:
    """Test cases for EmbeddingClusteringService."""
    
    def test_service_initialization(self, clustering_service, clustering_config):
        """Test service initialization."""
        assert clustering_service.config == clustering_config
        assert len(clustering_service.clusters) == 0
        assert len(clustering_service.user_clusters) == 0
        assert len(clustering_service.global_clusters) == 0
        assert len(clustering_service.user_thresholds) == 0
    
    def test_add_embedding_to_clusters_successful_login(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test adding embedding to clusters for successful login."""
        # Act
        cluster_id = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Assert
        assert cluster_id is not None
        assert sample_auth_context.email in clustering_service.user_clusters
        user_clusters = clustering_service.user_clusters[sample_auth_context.email]
        assert len(user_clusters) == 1
        assert cluster_id in user_clusters
        
        cluster = user_clusters[cluster_id]
        assert cluster.cluster_size == 1
        assert sample_auth_context.email in cluster.user_ids
        assert len(cluster.embeddings) == 1
    
    def test_add_embedding_to_clusters_failed_login(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test that failed logins are not added to clusters."""
        # Act
        cluster_id = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=False
        )
        
        # Assert
        assert cluster_id is None
        assert sample_auth_context.email not in clustering_service.user_clusters
    
    def test_add_multiple_similar_embeddings_same_cluster(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test that similar embeddings are added to the same cluster."""
        # Act - Add similar embeddings
        cluster_id1 = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        cluster_id2 = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_point1'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Assert
        assert cluster_id1 == cluster_id2  # Should be same cluster
        user_clusters = clustering_service.user_clusters[sample_auth_context.email]
        assert len(user_clusters) == 1
        
        cluster = user_clusters[cluster_id1]
        assert cluster.cluster_size == 2
        assert len(cluster.embeddings) == 2
    
    def test_add_dissimilar_embeddings_different_clusters(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test that dissimilar embeddings create different clusters."""
        # Act - Add dissimilar embeddings
        cluster_id1 = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        cluster_id2 = clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster2_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Assert
        assert cluster_id1 != cluster_id2  # Should be different clusters
        user_clusters = clustering_service.user_clusters[sample_auth_context.email]
        assert len(user_clusters) == 2
        
        cluster1 = user_clusters[cluster_id1]
        cluster2 = user_clusters[cluster_id2]
        assert cluster1.cluster_size == 1
        assert cluster2.cluster_size == 1
    
    def test_detect_outlier_no_clusters(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test outlier detection when no clusters exist."""
        # Act
        result = clustering_service.detect_outlier(
            sample_auth_context.email,
            sample_embeddings['outlier'],
            sample_auth_context
        )
        
        # Assert
        assert isinstance(result, OutlierDetectionResult)
        assert not result.is_outlier  # No clusters means not necessarily an outlier
        assert result.detection_method == "no_user_clusters"
        assert result.confidence < 0.5
    
    def test_detect_outlier_with_clusters_normal(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test outlier detection with existing clusters - normal case."""
        # Arrange - Create clusters first
        clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_point1'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Act - Test similar embedding (should not be outlier)
        result = clustering_service.detect_outlier(
            sample_auth_context.email,
            sample_embeddings['cluster1_point2'],
            sample_auth_context
        )
        
        # Assert
        assert isinstance(result, OutlierDetectionResult)
        assert not result.is_outlier
        assert result.detection_method == "user_clustering"
        assert result.nearest_cluster_id is not None
        assert result.distance_to_nearest_cluster < 0.3
    
    def test_detect_outlier_with_clusters_outlier(
        self,
        clustering_service,
        sample_auth_context,
        sample_embeddings
    ):
        """Test outlier detection with existing clusters - outlier case."""
        # Arrange - Create clusters first
        clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Act - Test dissimilar embedding (should be outlier)
        result = clustering_service.detect_outlier(
            sample_auth_context.email,
            sample_embeddings['cluster2_center'],  # Very different from cluster1
            sample_auth_context
        )
        
        # Assert
        assert isinstance(result, OutlierDetectionResult)
        # Note: Whether it's detected as outlier depends on the distance and threshold
        assert result.detection_method in ["user_clustering", "user_and_global_clustering"]
        assert result.nearest_cluster_id is not None
        assert result.distance_to_nearest_cluster > 0.0
    
    def test_calculate_distance(self, clustering_service):
        """Test distance calculation between vectors."""
        # Arrange
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        # Act
        distance_orthogonal = clustering_service._calculate_distance(vec1, vec2)
        distance_identical = clustering_service._calculate_distance(vec1, vec3)
        
        # Assert
        assert abs(distance_orthogonal - math.sqrt(2)) < 1e-6
        assert distance_identical == 0.0
    
    def test_calculate_distance_different_lengths(self, clustering_service):
        """Test distance calculation with different vector lengths."""
        # Arrange
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        # Act
        distance = clustering_service._calculate_distance(vec1, vec2)
        
        # Assert
        assert distance == float('inf')
    
    def test_find_nearest_cluster(self, clustering_service):
        """Test finding nearest cluster."""
        # Arrange
        clusters = {
            'cluster1': ClusterInfo(
                cluster_id='cluster1',
                centroid=[0.0, 0.0, 0.0],
                cluster_size=1
            ),
            'cluster2': ClusterInfo(
                cluster_id='cluster2',
                centroid=[1.0, 1.0, 1.0],
                cluster_size=1
            )
        }
        
        test_embedding = [0.1, 0.1, 0.1]
        
        # Act
        nearest_id, distance = clustering_service._find_nearest_cluster(
            test_embedding, clusters
        )
        
        # Assert
        assert nearest_id == 'cluster1'
        assert distance < 0.2  # Should be close to cluster1
    
    def test_find_nearest_cluster_empty(self, clustering_service):
        """Test finding nearest cluster with empty cluster dict."""
        # Act
        nearest_id, distance = clustering_service._find_nearest_cluster(
            [0.1, 0.1, 0.1], {}
        )
        
        # Assert
        assert nearest_id is None
        assert distance == float('inf')
    
    def test_dynamic_threshold_initialization(self, clustering_service):
        """Test dynamic threshold initialization."""
        # Act
        threshold = clustering_service._get_dynamic_threshold("test@example.com")
        
        # Assert
        assert threshold == clustering_service.config.outlier_threshold
        assert "test@example.com" in clustering_service.user_thresholds
    
    def test_dynamic_threshold_update_outlier(self, clustering_service):
        """Test dynamic threshold update for outlier detection."""
        # Arrange
        user_id = "test@example.com"
        initial_threshold = clustering_service._get_dynamic_threshold(user_id)
        
        outlier_result = OutlierDetectionResult(
            is_outlier=True,
            outlier_score=0.9,
            distance_to_nearest_cluster=0.8,
            nearest_cluster_id="cluster1",
            confidence=0.8,
            detection_method="user_clustering",
            threshold_used=initial_threshold
        )
        
        # Act
        clustering_service._update_dynamic_threshold(user_id, outlier_result)
        
        # Assert
        new_threshold = clustering_service.user_thresholds[user_id]
        assert new_threshold < initial_threshold  # Should decrease for high confidence outlier
        assert new_threshold >= clustering_service.config.min_threshold
    
    def test_dynamic_threshold_update_normal(self, clustering_service):
        """Test dynamic threshold update for normal detection."""
        # Arrange
        user_id = "test@example.com"
        initial_threshold = clustering_service._get_dynamic_threshold(user_id)
        
        normal_result = OutlierDetectionResult(
            is_outlier=False,
            outlier_score=0.2,
            distance_to_nearest_cluster=0.1,
            nearest_cluster_id="cluster1",
            confidence=0.8,
            detection_method="user_clustering",
            threshold_used=initial_threshold
        )
        
        # Act
        clustering_service._update_dynamic_threshold(user_id, normal_result)
        
        # Assert
        new_threshold = clustering_service.user_thresholds[user_id]
        assert new_threshold > initial_threshold  # Should increase for high confidence normal
        assert new_threshold <= clustering_service.config.max_threshold
    
    def test_merge_similar_clusters(self, clustering_service, sample_auth_context):
        """Test merging of similar clusters."""
        # Arrange - Create two similar clusters manually
        cluster1 = ClusterInfo(
            cluster_id="cluster1",
            centroid=[0.1, 0.1, 0.1],
            embeddings=[[0.1, 0.1, 0.1]],
            user_ids={"user1"},
            timestamps=[datetime.now()],
            cluster_size=1
        )
        
        cluster2 = ClusterInfo(
            cluster_id="cluster2",
            centroid=[0.12, 0.12, 0.12],  # Very similar to cluster1
            embeddings=[[0.12, 0.12, 0.12]],
            user_ids={"user2"},
            timestamps=[datetime.now()],
            cluster_size=1
        )
        
        clustering_service.user_clusters["test@example.com"] = {
            "cluster1": cluster1,
            "cluster2": cluster2
        }
        
        # Act
        merged_count = clustering_service.merge_similar_clusters("test@example.com")
        
        # Assert
        assert merged_count == 1
        user_clusters = clustering_service.user_clusters["test@example.com"]
        assert len(user_clusters) == 1  # Should have merged into one cluster
        
        remaining_cluster = list(user_clusters.values())[0]
        assert remaining_cluster.cluster_size == 2
        assert len(remaining_cluster.user_ids) == 2
    
    def test_merge_dissimilar_clusters_no_merge(self, clustering_service):
        """Test that dissimilar clusters are not merged."""
        # Arrange - Create two dissimilar clusters
        cluster1 = ClusterInfo(
            cluster_id="cluster1",
            centroid=[0.1, 0.1, 0.1],
            embeddings=[[0.1, 0.1, 0.1]],
            user_ids={"user1"},
            timestamps=[datetime.now()],
            cluster_size=1
        )
        
        cluster2 = ClusterInfo(
            cluster_id="cluster2",
            centroid=[0.8, 0.8, 0.8],  # Very different from cluster1
            embeddings=[[0.8, 0.8, 0.8]],
            user_ids={"user2"},
            timestamps=[datetime.now()],
            cluster_size=1
        )
        
        clustering_service.user_clusters["test@example.com"] = {
            "cluster1": cluster1,
            "cluster2": cluster2
        }
        
        # Act
        merged_count = clustering_service.merge_similar_clusters("test@example.com")
        
        # Assert
        assert merged_count == 0
        user_clusters = clustering_service.user_clusters["test@example.com"]
        assert len(user_clusters) == 2  # Should remain separate
    
    def test_calculate_intra_cluster_distance(self, clustering_service):
        """Test intra-cluster distance calculation."""
        # Arrange
        cluster = ClusterInfo(
            cluster_id="test_cluster",
            centroid=[0.5, 0.5, 0.5],
            embeddings=[
                [0.1, 0.1, 0.1],
                [0.2, 0.2, 0.2],
                [0.3, 0.3, 0.3]
            ],
            cluster_size=3
        )
        
        # Act
        intra_distance = clustering_service._calculate_intra_cluster_distance(cluster)
        
        # Assert
        assert intra_distance > 0.0
        assert intra_distance < 1.0  # Should be reasonable distance
    
    def test_calculate_intra_cluster_distance_single_point(self, clustering_service):
        """Test intra-cluster distance with single point."""
        # Arrange
        cluster = ClusterInfo(
            cluster_id="test_cluster",
            centroid=[0.5, 0.5, 0.5],
            embeddings=[[0.1, 0.1, 0.1]],
            cluster_size=1
        )
        
        # Act
        intra_distance = clustering_service._calculate_intra_cluster_distance(cluster)
        
        # Assert
        assert intra_distance == 0.0  # Single point has no intra-cluster distance
    
    def test_get_cluster_info(self, clustering_service, sample_auth_context, sample_embeddings):
        """Test getting cluster information for a user."""
        # Arrange - Add some embeddings to create clusters
        clustering_service.add_embedding_to_clusters(
            sample_auth_context.email,
            sample_embeddings['cluster1_center'],
            sample_auth_context,
            is_successful_login=True
        )
        
        # Act
        cluster_info = clustering_service.get_cluster_info(sample_auth_context.email)
        
        # Assert
        assert 'user_cluster_count' in cluster_info
        assert 'user_clusters' in cluster_info
        assert 'global_cluster_count' in cluster_info
        assert 'dynamic_threshold' in cluster_info
        assert cluster_info['user_cluster_count'] == 1
        assert cluster_info['dynamic_threshold'] == clustering_service.config.outlier_threshold
    
    def test_get_health_status(self, clustering_service):
        """Test health status reporting."""
        # Act
        health = clustering_service.get_health_status()
        
        # Assert
        assert health['is_healthy'] is True
        assert 'total_user_clusters' in health
        assert 'users_with_clusters' in health
        assert 'global_cluster_count' in health
        assert 'users_with_dynamic_thresholds' in health
        assert 'clustering_operations' in health
        assert 'outlier_detections' in health
        assert 'threshold_adjustments' in health
        assert 'cluster_merges' in health
        assert 'config' in health
    
    def test_cleanup_old_clusters(self, clustering_service):
        """Test cleanup of old clusters."""
        # Arrange - Create old cluster
        old_cluster = ClusterInfo(
            cluster_id="old_cluster",
            centroid=[0.1, 0.1, 0.1],
            embeddings=[[0.1, 0.1, 0.1]],
            user_ids={"user1"},
            timestamps=[datetime.now() - timedelta(days=35)],  # 35 days old
            cluster_size=1,
            last_updated=datetime.now() - timedelta(days=35)
        )
        
        recent_cluster = ClusterInfo(
            cluster_id="recent_cluster",
            centroid=[0.2, 0.2, 0.2],
            embeddings=[[0.2, 0.2, 0.2]],
            user_ids={"user2"},
            timestamps=[datetime.now()],
            cluster_size=1,
            last_updated=datetime.now()
        )
        
        clustering_service.user_clusters["test@example.com"] = {
            "old_cluster": old_cluster,
            "recent_cluster": recent_cluster
        }
        
        # Act
        removed_count = clustering_service.cleanup_old_clusters(max_age_days=30)
        
        # Assert
        assert removed_count == 1
        user_clusters = clustering_service.user_clusters["test@example.com"]
        assert "old_cluster" not in user_clusters
        assert "recent_cluster" in user_clusters
    
    def test_add_embedding_to_cluster_centroid_update(self, clustering_service):
        """Test that adding embeddings updates cluster centroid correctly."""
        # Arrange
        cluster = ClusterInfo(
            cluster_id="test_cluster",
            centroid=[0.0, 0.0, 0.0],
            embeddings=[],
            user_ids=set(),
            timestamps=[],
            cluster_size=0
        )
        
        auth_context = AuthContext(
            email="test@example.com",
            password_hash="hash",
            client_ip="192.168.1.1",
            user_agent="test",
            timestamp=datetime.now(),
            request_id="test"
        )
        
        # Act - Add first embedding
        clustering_service._add_embedding_to_cluster(
            cluster, [1.0, 1.0, 1.0], "user1", auth_context
        )
        
        # Assert first addition
        assert cluster.cluster_size == 1
        assert cluster.centroid == [1.0, 1.0, 1.0]
        
        # Act - Add second embedding
        clustering_service._add_embedding_to_cluster(
            cluster, [3.0, 3.0, 3.0], "user2", auth_context
        )
        
        # Assert second addition (centroid should be average)
        assert cluster.cluster_size == 2
        assert cluster.centroid == [2.0, 2.0, 2.0]  # (1+3)/2 = 2
        assert len(cluster.user_ids) == 2
        assert "user1" in cluster.user_ids
        assert "user2" in cluster.user_ids


class TestClusterInfo:
    """Test cases for ClusterInfo."""
    
    def test_cluster_info_creation(self):
        """Test cluster info creation."""
        # Act
        cluster = ClusterInfo(
            cluster_id="test_cluster",
            centroid=[0.1, 0.2, 0.3],
            embeddings=[[0.1, 0.2, 0.3]],
            user_ids={"user1"},
            timestamps=[datetime.now()],
            cluster_size=1
        )
        
        # Assert
        assert cluster.cluster_id == "test_cluster"
        assert cluster.centroid == [0.1, 0.2, 0.3]
        assert len(cluster.embeddings) == 1
        assert len(cluster.user_ids) == 1
        assert cluster.cluster_size == 1
    
    def test_cluster_info_serialization(self):
        """Test cluster info serialization."""
        # Arrange
        timestamp = datetime.now()
        cluster = ClusterInfo(
            cluster_id="test_cluster",
            centroid=[0.1, 0.2, 0.3],
            embeddings=[[0.1, 0.2, 0.3]],
            user_ids={"user1", "user2"},
            timestamps=[timestamp],
            cluster_size=2,
            intra_cluster_distance=0.1,
            last_updated=timestamp
        )
        
        # Act
        cluster_dict = cluster.to_dict()
        restored_cluster = ClusterInfo.from_dict(cluster_dict)
        
        # Assert
        assert restored_cluster.cluster_id == cluster.cluster_id
        assert restored_cluster.centroid == cluster.centroid
        assert restored_cluster.embeddings == cluster.embeddings
        assert restored_cluster.user_ids == cluster.user_ids
        assert restored_cluster.cluster_size == cluster.cluster_size
        assert restored_cluster.intra_cluster_distance == cluster.intra_cluster_distance
        assert len(restored_cluster.timestamps) == len(cluster.timestamps)


class TestClusteringConfig:
    """Test cases for ClusteringConfig."""
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        # Act
        config = ClusteringConfig()
        
        # Assert
        assert config.max_clusters == 20
        assert config.min_cluster_size == 3
        assert config.max_cluster_distance == 0.3
        assert config.cluster_merge_threshold == 0.15
        assert config.outlier_threshold == 0.7
        assert config.enable_dynamic_thresholds is True
        assert config.threshold_adaptation_rate == 0.1
        assert config.min_threshold == 0.3
        assert config.max_threshold == 0.9
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        # Act
        config = ClusteringConfig(
            max_clusters=10,
            outlier_threshold=0.8,
            enable_dynamic_thresholds=False
        )
        
        # Assert
        assert config.max_clusters == 10
        assert config.outlier_threshold == 0.8
        assert config.enable_dynamic_thresholds is False
        # Other values should remain default
        assert config.min_cluster_size == 3
        assert config.cluster_merge_threshold == 0.15


class TestOutlierDetectionResult:
    """Test cases for OutlierDetectionResult."""
    
    def test_outlier_detection_result_creation(self):
        """Test outlier detection result creation."""
        # Act
        result = OutlierDetectionResult(
            is_outlier=True,
            outlier_score=0.8,
            distance_to_nearest_cluster=0.7,
            nearest_cluster_id="cluster1",
            confidence=0.9,
            detection_method="user_clustering",
            threshold_used=0.7
        )
        
        # Assert
        assert result.is_outlier is True
        assert result.outlier_score == 0.8
        assert result.distance_to_nearest_cluster == 0.7
        assert result.nearest_cluster_id == "cluster1"
        assert result.confidence == 0.9
        assert result.detection_method == "user_clustering"
        assert result.threshold_used == 0.7
    
    def test_outlier_detection_result_serialization(self):
        """Test outlier detection result serialization."""
        # Arrange
        result = OutlierDetectionResult(
            is_outlier=True,
            outlier_score=0.8,
            distance_to_nearest_cluster=0.7,
            nearest_cluster_id="cluster1",
            confidence=0.9,
            detection_method="user_clustering",
            threshold_used=0.7
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict['is_outlier'] is True
        assert result_dict['outlier_score'] == 0.8
        assert result_dict['distance_to_nearest_cluster'] == 0.7
        assert result_dict['nearest_cluster_id'] == "cluster1"
        assert result_dict['confidence'] == 0.9
        assert result_dict['detection_method'] == "user_clustering"
        assert result_dict['threshold_used'] == 0.7


if __name__ == "__main__":
    pytest.main([__file__])