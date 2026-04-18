# Plugin Store UI

This module provides a comprehensive plugin store interface for Karen AI, allowing users to discover, install, and manage plugins from the plugin marketplace.

## Components

### Core Components

- **PluginStorePage** - Main page component with tabs for browsing, trending, and installed plugins
- **PluginCard** - Individual plugin display card with installation options
- **PluginGrid** - Responsive grid layout for plugin cards with pagination
- **PluginDetailsModal** - Modal dialog for viewing detailed plugin information
- **SearchBar** - Search input with history and sorting options
- **CategoryFilter** - Category selection with plugin counts
- **PluginStatusBadge** - Status indicator badges (installed, available, compatible, incompatible)

### Existing Components

- **PluginHost** - Renders plugin UI components (existing)
- **PluginOverviewPage** - Plugin health monitoring page (existing)

## State Management

The plugin store uses Zustand for state management via the `usePluginStore` hook:

```typescript
import { usePluginStore } from '@/stores/PluginStore';

const {
  plugins,
  loading,
  error,
  searchParams,
  categories,
  trendingPlugins,
  installingPlugins,
  setSearchParams,
  searchPlugins,
  installPlugin,
  getPluginDetails,
  loadCategories,
  loadTrending,
} = usePluginStore();
```

## API Integration

The `PluginStoreService` provides methods for interacting with the plugin store API:

```typescript
import pluginStoreService from '@/lib/PluginStoreService';

// Search plugins
const results = await pluginStoreService.searchPlugins({
  query: 'weather',
  category: 'utilities',
  sort_by: 'popularity',
  page: 1,
  per_page: 20,
});

// Get plugin details
const details = await pluginStoreService.getPluginDetails('weather-plugin');

// Install plugin
const result = await pluginStoreService.installPlugin({
  plugin_id: 'weather-plugin',
  version: '1.0.0',
});

// Get categories
const categories = await pluginStoreService.getCategories();

// Get trending plugins
const trending = await pluginStoreService.getTrendingPlugins(10);
```

## Types

All plugin-related types are defined in `src/types/plugin.ts`:

```typescript
import type {
  Plugin,
  PluginCategory,
  PluginSortOrder,
  PluginSearchParams,
  PluginSearchResponse,
  PluginDetails,
  PluginInstallRequest,
  PluginInstallResponse,
  PluginRatingRequest,
  PluginRatingResponse,
  PluginStoreStats,
  CategoryInfo,
  PluginUpdate,
} from '@/types/plugin';
```

## Usage Example

```typescript
import { PluginStorePage } from '@/components/plugins';

// In your app/routing
export default function App() {
  return (
    <PluginStorePage />
  );
}
```

## Features

- **Plugin Discovery**: Browse and search available plugins
- **Installation**: Install plugins with version selection
- **Categories**: Filter plugins by category
- **Trending**: View popular plugins
- **Management**: View and manage installed plugins
- **Search**: Real-time search with history
- **Sorting**: Sort by popularity, newest, name, rating
- **Pagination**: Navigate through plugin results
- **Compatibility**: Check plugin compatibility with current system
- **Details View**: View comprehensive plugin information
- **Responsive Design**: Works on desktop, tablet, and mobile

## Backend API

The plugin store UI integrates with the following backend endpoints:

- `GET /api/store/search` - Search for plugins
- `GET /api/store/plugins/{plugin_id}` - Get plugin details
- `POST /api/store/install` - Install plugin
- `POST /api/store/rate` - Rate a plugin
- `GET /api/store/statistics` - Get store statistics
- `GET /api/store/categories` - Get plugin categories
- `GET /api/store/trending` - Get trending plugins
- `GET /api/store/updates` - Get available updates

## Development

### Running the UI

```bash
cd ui_launchers/Karen-AI-Theme
npm run dev
```

### Building

```bash
npm run build
```

### Type Checking

```bash
npm run typecheck
```

### Linting

```bash
npm run lint
```

## Architecture

The plugin store follows a clean architecture pattern:

1. **Types**: Zod-validated type definitions in `src/types/plugin.ts`
2. **API Service**: Centralized API client in `src/lib/PluginStoreService.ts`
3. **State Management**: Zustand store in `src/stores/PluginStore.ts`
4. **Components**: Reusable UI components in `src/components/plugins/`
5. **Pages**: Page-level components that compose the UI

## Notes

- The plugin store uses the existing API client infrastructure
- All components are fully typed with TypeScript
- State management is centralized for consistency
- Components follow the existing design system using Radix UI
- Loading states and error handling are implemented throughout
