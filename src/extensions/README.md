# AI Karen Extensions System

The AI Karen Extensions System provides a robust framework for building complex, feature-rich modules that extend the core platform capabilities.

## Directory Structure

```
src/extensions/
├── README.md                    # This file - system overview
├── __init__.py                  # Main exports and backward compatibility
├── core/                        # Extension framework code
│   ├── __init__.py             # Core framework exports
│   ├── base.py                 # BaseExtension class (to be moved from root)
│   ├── manager.py              # ExtensionManager (to be moved from root)
│   ├── registry.py             # ExtensionRegistry (to be moved from root)
│   ├── models.py               # Extension data models (to be moved from root)
│   ├── security.py             # Security framework (to be moved from root)
│   ├── api_integration.py      # FastAPI integration (to be moved from root)
│   ├── background_tasks.py     # Background task support (to be moved from root)
│   └── tests/                  # Framework tests
├── docs/                       # Extension system documentation
│   ├── README.md               # Documentation overview
│   ├── development-guide.md    # Extension development guide
│   ├── api-reference.md        # API reference documentation
│   ├── security-guide.md       # Security guidelines
│   └── troubleshooting-guide.md # Common issues and solutions
└── [framework files]           # Current framework files (to be moved to core/)
```

## Extension vs Plugin

**Extensions** are complex, feature-rich modules suitable for:
- Multi-component features
- Complex business logic
- UI components and interfaces
- Background services
- Database integrations
- Multiple API endpoints

**Plugins** are simple, focused functions suitable for:
- Single-purpose utilities
- Quick integrations
- Simple transformations
- Lightweight tools

## Extension Implementations

Extension implementations are stored separately in the `/extensions/` directory at the project root. This separation keeps the framework code organized while allowing extensions to be easily discovered and managed.

## Framework Components

### Core Classes
- **BaseExtension**: Base class for all extensions
- **ExtensionManager**: Manages extension lifecycle and operations
- **ExtensionRegistry**: Registry for tracking loaded extensions

### Data Models
- **ExtensionManifest**: Extension metadata and configuration
- **ExtensionRecord**: Runtime extension information
- **ExtensionStatus**: Extension state tracking

### Integration
- **ExtensionAPIIntegration**: FastAPI integration utilities
- **Security**: Security framework and decorators
- **Background Tasks**: Background task support

## Development Workflow

1. **Design**: Plan your extension architecture and features
2. **Create**: Use the framework to build your extension
3. **Test**: Implement comprehensive tests
4. **Document**: Provide clear documentation
5. **Deploy**: Package and distribute your extension

## Getting Started

1. Read the documentation in `docs/development-guide.md`
2. Review existing extensions in `/extensions/` for examples
3. Use the framework components to build your extension
4. Follow security guidelines for safe development
5. Test thoroughly before deployment

## Migration Status

This directory structure is part of the extensions consolidation effort:
- ✅ **Task 1**: New directory structure created
- ⏳ **Task 2**: Framework code will be moved to `core/`
- ⏳ **Task 3**: Plugin systems will be consolidated
- ⏳ **Task 4**: Plugin implementations will be organized
- ⏳ **Task 5**: Extension discovery will be updated

## Support

- Check `docs/troubleshooting-guide.md` for common issues
- Review the API reference for technical details
- Examine existing extensions for implementation patterns
- Follow security guidelines for safe development