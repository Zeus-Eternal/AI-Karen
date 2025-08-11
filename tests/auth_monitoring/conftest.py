import pytest
from prometheus_client import CollectorRegistry

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.monitoring import (
    AlertManager,
    MetricsCollector,
    init_auth_metrics,
)
from ai_karen_engine.auth.monitoring_extensions import (
    PerformanceTrendAnalyzer,
    SecurityEventCorrelator,
    EnhancedAuthMonitor,
)


@pytest.fixture
def auth_config():
    """Base authentication config."""
    return AuthConfig()


@pytest.fixture
def metrics_config(auth_config):
    """Config with metrics enabled."""
    auth_config.monitoring.enable_monitoring = True
    auth_config.monitoring.enable_metrics = True
    return auth_config


@pytest.fixture
def alerting_config(auth_config):
    """Config with alerting enabled (and metrics for collectors)."""
    auth_config.monitoring.enable_monitoring = True
    auth_config.monitoring.enable_alerting = True
    auth_config.monitoring.enable_metrics = True
    return auth_config


@pytest.fixture
def metrics_collector(metrics_config):
    """Shared MetricsCollector instance."""
    return MetricsCollector(metrics_config)


@pytest.fixture
def alert_manager(alerting_config):
    """Shared AlertManager instance with metrics."""
    metrics = MetricsCollector(alerting_config)
    return AlertManager(alerting_config, metrics)


@pytest.fixture
def correlator(auth_config):
    """SecurityEventCorrelator using base config."""
    return SecurityEventCorrelator(auth_config)


@pytest.fixture
def performance_analyzer(auth_config):
    """PerformanceTrendAnalyzer using base config."""
    return PerformanceTrendAnalyzer(auth_config)


@pytest.fixture
def enhanced_monitor(auth_config):
    """EnhancedAuthMonitor using base config."""
    return EnhancedAuthMonitor(auth_config)


@pytest.fixture
def metrics_registry():
    """Fresh Prometheus registry for each test."""
    registry = CollectorRegistry()
    init_auth_metrics(registry, force=True)
    return registry
