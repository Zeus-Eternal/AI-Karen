# Hierarchical Extension Management System

This directory contains the components and utilities for the hierarchical extension management system in AI Karen's web UI.

## Project Structure

```
src/
├── components/extensions/
│   ├── core/                     # Core extension management components
│   │   ├── ExtensionProvider.tsx
│   │   ├── ExtensionSidebar.tsx
│   │   ├── ExtensionHeader.tsx
│   │   ├── ExtensionStats.tsx
│   │   ├── ExtensionBreadcrumb.tsx
│   │   └── ExtensionContent.tsx
│   ├── plugins/                  # Plugin-related components
│   │   ├── providers/            # Plugin provider components
│   │   │   ├── LLMProviderList.tsx
│   │   │   ├── VoiceProviderList.tsx
│   │   │   ├── VideoProviderList.tsx
│   │   │   ├── ServiceProviderList.tsx
│   │   │   ├── ProviderCard.tsx
│   │   │   └── ModelCard.tsx
│   │   └── models/               # Plugin model components
│   │       ├── LLMModelList.tsx
│   │       ├── VoiceModelList.tsx
│   │       ├── VideoModelList.tsx
│   │       ├── ModelConfigPanel.tsx
│   │       └── ModelMetrics.tsx
│   ├── system/                   # System extension components
│   │   ├── categories/           # System extension categories
│   │   │   ├── AnalyticsExtensions.tsx
│   │   │   ├── CommunicationExtensions.tsx
│   │   │   ├── DevelopmentExtensions.tsx
│   │   │   ├── IntegrationExtensions.tsx
│   │   │   ├── ProductivityExtensions.tsx
│   │   │   ├── SecurityExtensions.tsx
│   │   │   └── ExperimentalExtensions.tsx
│   │   └── SystemExtensionsList.tsx
│   ├── automation/               # Automation components
│   │   ├── AgentList.tsx
│   │   └── WorkflowList.tsx
│   ├── shared/                   # Shared components
│   │   ├── ExtensionCard.tsx
│   │   ├── ExtensionControls.tsx
│   │   ├── ExtensionSettings.tsx
│   │   ├── HealthIndicator.tsx
│   │   ├── ResourceUsage.tsx
│   │   ├── PermissionManager.tsx
│   │   └── ErrorBoundary.tsx
│   ├── marketplace/              # Marketplace components
│   │   ├── ExtensionStore.tsx
│   │   ├── ExtensionSearch.tsx
│   │   ├── ExtensionFilters.tsx
│   │   ├── ExtensionInstaller.tsx
│   │   ├── ExtensionRating.tsx
│   │   └── ExtensionReviews.tsx
│   └── index.ts                  # Main exports
├── extensions/                   # Extension context and types
│   ├── types.ts                  # Core type definitions
│   ├── ExtensionContext.tsx      # React context provider
│   └── index.ts                  # Extension exports
├── hooks/extensions/             # Extension-related hooks
│   ├── useExtensions.ts
│   ├── useExtensionNavigation.ts
│   ├── useExtensionHealth.ts
│   ├── useExtensionSettings.ts
│   ├── useExtensionControls.ts
│   ├── useExtensionMarketplace.ts
│   ├── useExtensionCache.ts
│   └── index.ts
├── services/extensions/          # Extension API services
│   ├── types.ts                  # API type definitions
│   ├── extensionAPI.ts
│   ├── pluginService.ts
│   ├── systemExtensionService.ts
│   ├── marketplaceService.ts
│   ├── cacheService.ts
│   └── index.ts
└── lib/extensions/               # Extension utilities
    ├── constants.ts              # Extension constants
    ├── extensionUtils.ts         # Extension utility functions
    ├── navigationUtils.ts        # Navigation utilities
    ├── validationUtils.ts        # Validation utilities
    ├── permissionUtils.ts        # Permission utilities
    ├── healthUtils.ts            # Health monitoring utilities
    └── index.ts                  # Utility exports
```

## Architecture Overview

The hierarchical extension management system follows a dual-category approach:

### Categories

1. **Plugins** - User-installable marketplace items from `/plugin_marketplace`
   - LLM Providers (OpenAI, Anthropic, LlamaCpp, etc.)
   - Voice Providers (TTS, STT services)
   - Video Providers (Image/video generation)
   - Service Providers (Third-party integrations)

2. **Extensions** - System modules from `/extensions` folder
   - **Agents** - Autonomous agents from `/extensions/automation/`
   - **Automations** - Workflows from `/extensions/automation/workflow-builder/`
   - **System Extensions** - Analytics, Communication, Development, etc.

### Navigation Hierarchy

```
Category (Plugins/Extensions)
└── Submenu (Providers/Agents/Automations/System)
    └── Items (Specific providers/extensions)
        └── Settings/Controls (Configuration)
```

## Key Features

### Type System
- Comprehensive TypeScript interfaces for all extension types
- Dual-category system (Plugins vs Extensions)
- Hierarchical navigation state management
- Resource usage and health monitoring types

### Navigation
- Breadcrumb-based navigation
- Context-aware state management
- Back navigation support
- Level-based hierarchy traversal

### Utilities
- Extension validation and sanitization
- Permission management and risk assessment
- Health monitoring and diagnostics
- Resource usage tracking
- Navigation state management

### Components
- Modular component architecture
- Shared components for common functionality
- Category-specific components
- Responsive design with Shadcn/ui integration
- Sidebar header with toggle button
- Stats overview for plugins and extensions
- Breadcrumb navigation component

## Usage

### Basic Setup

```tsx
import { ExtensionProvider } from '@/extensions';
import { ExtensionSidebar, ExtensionHeader, ExtensionContent } from '@/components/extensions';

function App() {
  return (
    <ExtensionProvider initialCategory="Plugins">
      <div className="flex">
        <ExtensionSidebar />
        <main className="flex-1">
          <ExtensionHeader title="Extension Manager" />
          <ExtensionContent>{/* extension views */}</ExtensionContent>
        </main>
      </div>
    </ExtensionProvider>
  );
}
```

### Navigation

```tsx
import { useExtensionContext } from '@/extensions';

function NavigationExample() {
  const { state, dispatch } = useExtensionContext();
  
  const navigateToLLMProviders = () => {
    dispatch({
      type: 'SET_NAVIGATION',
      navigation: {
        selectedPluginProvider: 'llm'
      }
    });
  };
  
  return (
    <button onClick={navigateToLLMProviders}>
      View LLM Providers
    </button>
  );
}
```

### Health Monitoring

```tsx
import { performHealthCheck } from '@/lib/extensions';

async function checkExtensionHealth(extension) {
  const result = await performHealthCheck(extension);
  console.log(`Health status: ${result.status}`);
  console.log(`Message: ${result.message}`);
}
```

## Development Guidelines

### Adding New Extension Types
1. Define types in `extensions/types.ts`
2. Add constants in `lib/extensions/constants.ts`
3. Create components in appropriate category folder
4. Add navigation logic in `navigationUtils.ts`
5. Update validation in `validationUtils.ts`

### Component Development
- Use existing Shadcn/ui components for consistency
- Follow the established naming conventions
- Include proper TypeScript types
- Add error boundaries for robustness
- Implement responsive design patterns

### Testing
- Unit tests for utility functions
- Component tests with React Testing Library
- Integration tests for navigation flows
- E2E tests for complete user workflows

## Integration Points

### Backend APIs
- Extension CRUD operations
- Health monitoring endpoints
- Permission management
- Marketplace integration

### File System Integration
- Plugin marketplace scanning (`/plugin_marketplace`)
- System extension discovery (`/extensions`)
- Configuration file management
- Asset loading and caching

### Security Considerations
- Permission validation and enforcement
- Input sanitization and XSS prevention
- Secure API key storage
- Extension signature verification

## Future Enhancements

- Real-time extension status updates via WebSocket
- Advanced filtering and search capabilities
- Extension dependency management
- Performance monitoring and analytics
- Automated extension updates
- Extension development toolkit integration