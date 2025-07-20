# Directory Structure Reorganization Requirements

## Introduction

The Kari AI platform currently has an inconsistent and confusing directory structure for extensions and plugins. This creates confusion for developers and makes the codebase harder to navigate and maintain. We need to reorganize the directory structure to create a clear separation between:

- **System Code**: Core extension and plugin system implementations
- **Extension Development**: Actual extensions that can be developed and distributed
- **Plugin Development**: Individual plugin implementations

The current structure has overlapping concerns and unclear boundaries, which needs to be resolved before further extension system development.

## Requirements

### Requirement 1: Clear System Code Organization

**User Story:** As a platform developer, I want the core extension and plugin system code to be clearly organized in the source tree, so that I can easily find and maintain system components.

#### Acceptance Criteria

1. WHEN I look for extension system code THEN it SHALL be located in `src/ai_karen_engine/extensions/`
2. WHEN I look for plugin system code THEN it SHALL be located in `src/ai_karen_engine/plugins/`
3. WHEN system code is organized THEN each subsystem SHALL have its own clear directory structure
4. WHEN importing system components THEN import paths SHALL be consistent and logical
5. WHEN maintaining system code THEN related components SHALL be co-located

### Requirement 2: Clear Extension Development Structure

**User Story:** As an extension developer, I want a dedicated directory structure for developing and organizing extensions, so that I can easily create, test, and distribute extensions.

#### Acceptance Criteria

1. WHEN I develop extensions THEN they SHALL be located in the root `extensions/` directory
2. WHEN extensions are categorized THEN they SHALL be organized in category subdirectories
3. WHEN I create a new extension THEN the directory structure SHALL be clear and consistent
4. WHEN I look for examples THEN they SHALL be in `extensions/examples/`
5. WHEN extensions are distributed THEN the directory structure SHALL support marketplace organization

### Requirement 3: Plugin System Reorganization

**User Story:** As a plugin developer, I want the plugin system to have a clear and consistent directory structure, so that I can easily develop and maintain plugins.

#### Acceptance Criteria

1. WHEN I develop plugins THEN the plugin system code SHALL be separate from individual plugins
2. WHEN I look for plugin implementations THEN they SHALL be clearly organized by category or type
3. WHEN I create new plugins THEN the directory structure SHALL guide proper organization
4. WHEN plugins interact with extensions THEN the boundaries SHALL be clear
5. WHEN maintaining plugins THEN related components SHALL be co-located

### Requirement 4: Import Path Consistency

**User Story:** As a developer working on the platform, I want consistent and logical import paths, so that I can easily import components without confusion.

#### Acceptance Criteria

1. WHEN importing extension system components THEN paths SHALL start with `ai_karen_engine.extensions`
2. WHEN importing plugin system components THEN paths SHALL start with `ai_karen_engine.plugins`
3. WHEN importing individual plugins THEN paths SHALL be consistent and predictable
4. WHEN importing extensions THEN paths SHALL be separate from system code imports
5. WHEN refactoring imports THEN the structure SHALL minimize breaking changes

### Requirement 5: Backward Compatibility During Migration

**User Story:** As a platform maintainer, I want the reorganization to maintain backward compatibility where possible, so that existing code continues to work during the transition.

#### Acceptance Criteria

1. WHEN reorganizing directories THEN existing imports SHALL continue to work temporarily
2. WHEN moving files THEN deprecation warnings SHALL be provided for old import paths
3. WHEN updating references THEN all internal code SHALL use new paths
4. WHEN testing THEN all existing functionality SHALL continue to work
5. WHEN migration is complete THEN old import paths SHALL be cleanly removed

### Requirement 6: Documentation and Developer Experience

**User Story:** As a developer new to the platform, I want clear documentation about the directory structure, so that I can quickly understand how to navigate and contribute to the codebase.

#### Acceptance Criteria

1. WHEN I read the documentation THEN the directory structure SHALL be clearly explained
2. WHEN I look at the codebase THEN README files SHALL guide me to the right locations
3. WHEN I develop extensions THEN examples SHALL show the proper directory structure
4. WHEN I develop plugins THEN the structure SHALL be self-documenting
5. WHEN I contribute code THEN the organization SHALL make it clear where new code belongs

### Requirement 7: Build and Deployment Consistency

**User Story:** As a DevOps engineer, I want the directory reorganization to maintain consistent build and deployment processes, so that CI/CD pipelines continue to work correctly.

#### Acceptance Criteria

1. WHEN building the platform THEN all source code SHALL be properly included
2. WHEN running tests THEN test discovery SHALL work with the new structure
3. WHEN packaging extensions THEN the directory structure SHALL support distribution
4. WHEN deploying THEN the new structure SHALL not break existing deployment scripts
5. WHEN monitoring THEN logging and metrics SHALL reflect the new organization

### Requirement 8: Tool and IDE Support

**User Story:** As a developer using IDEs and development tools, I want the directory structure to work well with common development tools, so that I have a good development experience.

#### Acceptance Criteria

1. WHEN using IDEs THEN code navigation SHALL work correctly with the new structure
2. WHEN using linters THEN they SHALL properly discover and check all code
3. WHEN using formatters THEN they SHALL work with the reorganized structure
4. WHEN using debugging tools THEN source mapping SHALL work correctly
5. WHEN using version control THEN the reorganization SHALL have clean history

## Current State Analysis

### Current Directory Structure Issues

```
Current Structure (Problematic):
├── extensions/                    # Extension development (good)
│   ├── examples/
│   ├── automation/
│   └── ...
├── src/ai_karen_engine/
│   ├── extensions/               # Extension system code (good)
│   │   ├── manager.py
│   │   ├── base.py
│   │   └── ...
│   ├── plugins/                  # Plugin system + individual plugins (mixed)
│   │   ├── hello_world/         # Individual plugin
│   │   ├── time_query/          # Individual plugin
│   │   └── sandbox.py           # System code
│   └── ...
└── ...
```

### Problems Identified

1. **Mixed Concerns**: `src/ai_karen_engine/plugins/` contains both system code and individual plugins
2. **Unclear Boundaries**: Hard to distinguish between system components and implementations
3. **Import Confusion**: Import paths don't clearly indicate what type of component is being imported
4. **Maintenance Issues**: System code mixed with plugin implementations makes maintenance harder
5. **Developer Confusion**: New developers struggle to understand where different types of code belong

## Proposed Target Structure

```
Target Structure (Clean):
├── extensions/                    # Extension development/marketplace
│   ├── examples/                 # Example extensions
│   ├── automation/               # Automation extensions
│   ├── analytics/                # Analytics extensions
│   └── ...
├── plugins/                      # Plugin development/marketplace  
│   ├── examples/                 # Example plugins
│   ├── core/                     # Core plugins
│   ├── integrations/             # Integration plugins
│   └── ...
├── src/ai_karen_engine/
│   ├── extensions/               # Extension system code
│   │   ├── manager.py           # Extension manager
│   │   ├── base.py              # Base extension class
│   │   ├── registry.py          # Extension registry
│   │   └── ...
│   ├── plugins/                  # Plugin system code
│   │   ├── manager.py           # Plugin manager  
│   │   ├── router.py            # Plugin router
│   │   ├── registry.py          # Plugin registry
│   │   └── ...
│   └── ...
└── ...
```

This reorganization will create clear boundaries, improve developer experience, and make the codebase more maintainable and scalable.