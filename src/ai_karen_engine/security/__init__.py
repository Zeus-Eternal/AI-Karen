"""
Security module for AI Karen Engine.
Provides comprehensive security testing, threat protection, and compliance features.
"""

# Always import basic penetration testing components
from ai_karen_engine.security.penetration_testing import PenetrationTestSuite, SecurityScanner

# Initialize basic exports
__all__ = [
    'PenetrationTestSuite',
    'SecurityScanner'
]

# Try to import optional components that require additional dependencies
try:
    from ai_karen_engine.security.threat_protection import ThreatProtectionSystem, IntrusionDetectionSystem
    __all__.extend(['ThreatProtectionSystem', 'IntrusionDetectionSystem'])
except ImportError:
    pass

try:
    from ai_karen_engine.security.incident_response import SecurityIncidentManager, IncidentResponsePlan
    __all__.extend(['SecurityIncidentManager', 'IncidentResponsePlan'])
except ImportError:
    pass

try:
    from ai_karen_engine.security.compliance import ComplianceReporter, SOC2Reporter, GDPRReporter
    __all__.extend(['ComplianceReporter', 'SOC2Reporter', 'GDPRReporter'])
except ImportError:
    pass
