"""
AI Karen Extensions - Complex Feature Implementations

This package contains all extension implementations for AI Karen.
Extensions are complex, feature-rich modules suitable for:
- Multi-component features
- Complex business logic
- UI components and interfaces
- Background services
- Database integrations
- Multiple API endpoints

Directory Structure:
-------------------
extensions/
├── security/              # Security, authentication, authorization
├── debugging/             # Debugging, profiling, error tracking
├── performance/           # Performance monitoring and optimization
├── sdk/                   # Extension development SDK
├── marketplace-extension/ # Marketplace integration
├── community/             # Community features
├── onboarding/            # User onboarding flows
├── launch/                # Launch management
├── lifecycle/             # Lifecycle management
├── cli/                   # Extension CLI tools
├── docs/                  # Documentation
└── tests/                 # Tests

Framework Location:
------------------
The core extension framework is located in:
    src/ai_karen_engine/extensions/

Import the framework classes from there:
    from ai_karen_engine.extensions import ExtensionManager, ExtensionOrchestrator

Development:
-----------
To create a new extension:
1. Create directory: src/extensions/[name]/
2. Add implementation files
3. Register with extension manager
4. Add tests
5. Update documentation

See STRUCTURE.md for more details.
"""

# Framework is in ai_karen_engine.extensions
# This __init__ is for extension implementations only

__all__ = [
    # Extension implementations are imported dynamically by the framework
    # Add explicit exports here if needed for convenience
]

# Version info
__version__ = "1.0.0"
__author__ = "AI Karen Team"
