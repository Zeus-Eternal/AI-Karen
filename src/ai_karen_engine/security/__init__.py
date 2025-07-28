"""
Security module for AI Karen Engine.
Provides comprehensive security testing, threat protection, compliance features,
and intelligent authentication capabilities.
"""

# Always import basic penetration testing components
from ai_karen_engine.security.penetration_testing import PenetrationTestSuite, SecurityScanner

# Import intelligent authentication models and base classes
try:
    from ai_karen_engine.security.models import (
        AuthContext,
        AuthAnalysisResult,
        IntelligentAuthConfig,
        RiskLevel,
        SecurityActionType,
        GeoLocation,
        NLPFeatures,
        EmbeddingAnalysis,
        BehavioralAnalysis,
        ThreatAnalysis,
        SecurityAction,
        RiskThresholds,
        FeatureFlags,
        FallbackConfig
    )
    from ai_karen_engine.security.intelligent_auth_base import (
        ServiceStatus,
        ServiceHealthStatus,
        IntelligentAuthHealthStatus,
        BaseIntelligentAuthService,
        ServiceRegistry,
        HealthMonitor,
        CredentialAnalyzerInterface,
        BehavioralEmbeddingInterface,
        AnomalyDetectorInterface,
        ThreatIntelligenceInterface,
        IntelligentAuthServiceInterface,
        get_service_registry,
        register_service,
        get_service
    )
    
    __all__ = [
        'PenetrationTestSuite',
        'SecurityScanner',
        # Intelligent authentication models
        'AuthContext',
        'AuthAnalysisResult', 
        'IntelligentAuthConfig',
        'RiskLevel',
        'SecurityActionType',
        'GeoLocation',
        'NLPFeatures',
        'EmbeddingAnalysis',
        'BehavioralAnalysis',
        'ThreatAnalysis',
        'SecurityAction',
        'RiskThresholds',
        'FeatureFlags',
        'FallbackConfig',
        # Intelligent authentication base classes
        'ServiceStatus',
        'ServiceHealthStatus',
        'IntelligentAuthHealthStatus',
        'BaseIntelligentAuthService',
        'ServiceRegistry',
        'HealthMonitor',
        'CredentialAnalyzerInterface',
        'BehavioralEmbeddingInterface',
        'AnomalyDetectorInterface',
        'ThreatIntelligenceInterface',
        'IntelligentAuthServiceInterface',
        'get_service_registry',
        'register_service',
        'get_service'
    ]
    
except ImportError as e:
    # Fallback if intelligent auth components are not available
    __all__ = [
        'PenetrationTestSuite',
        'SecurityScanner'
    ]

# Try to import optional components that require additional dependencies
try:
    from ai_karen_engine.security.threat_protection import (
        ThreatProtectionSystem,  # noqa: F401
        IntrusionDetectionSystem,  # noqa: F401
    )
    __all__.extend(['ThreatProtectionSystem', 'IntrusionDetectionSystem'])
except Exception:
    pass

try:
    from ai_karen_engine.security.auth_manager import (
        authenticate,  # noqa: F401
        update_credentials,  # noqa: F401
    )
    __all__.extend(['authenticate', 'update_credentials'])
except ImportError:
    pass

try:
    from ai_karen_engine.security.incident_response import (
        SecurityIncidentManager,  # noqa: F401
        IncidentResponsePlan,  # noqa: F401
    )
    __all__.extend(['SecurityIncidentManager', 'IncidentResponsePlan'])
except ImportError:
    pass

try:
    from ai_karen_engine.security.compliance import (
        ComplianceReporter,  # noqa: F401
        SOC2Reporter,  # noqa: F401
        GDPRReporter,  # noqa: F401
    )
    __all__.extend(["ComplianceReporter", "SOC2Reporter", "GDPRReporter"])
except Exception:
    pass
