"""
Security module for AI Karen Engine.
Provides comprehensive security testing, threat protection, and compliance features.
"""

# Always import basic penetration testing components
from .penetration_testing import PenetrationTestSuite, SecurityScanner

# Initialize basic exports
__all__ = [
    'PenetrationTestSuite',
    'SecurityScanner'
]

# Try to import optional components that require additional dependencies
try:
    from .threat_protection import ThreatProtectionSystem, IntrusionDetectionSystem
    __all__.extend(['ThreatProtectionSystem', 'IntrusionDetectionSystem'])
except ImportError:
    pass

try:
    from .incident_response import SecurityIncidentManager, IncidentResponsePlan
    __all__.extend(['SecurityIncidentManager', 'IncidentResponsePlan'])
except ImportError:
    pass

try:
    from .compliance import ComplianceReporter, SOC2Reporter, GDPRReporter
    __all__.extend(['ComplianceReporter', 'SOC2Reporter', 'GDPRReporter'])
except ImportError:
    pass