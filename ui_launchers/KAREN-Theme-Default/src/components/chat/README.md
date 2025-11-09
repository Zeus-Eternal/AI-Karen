# Model Selector Components

This directory contains modern React components for selecting and managing AI models in the Karen AI interface.

## Components

### ModelSelector
A clean, modern model selector component with the following features:

- **Provider Grouping**: Models are organized by provider (transformers, llama-cpp, etc.)
- **Status Indicators**: Visual indicators for local, available, and downloading models
- **Size Display**: Human-readable file sizes for each model
- **Responsive Design**: Works well on different screen sizes
- **Loading States**: Proper loading indicators and error handling
- **Accessibility**: Full keyboard navigation and screen reader support

#### Usage
```tsx
import { ModelSelector } from '@/components/chat/ModelSelector';

function ChatInterface() {
  const [selectedModel, setSelectedModel] = useState<string>('');

  return (
    <ModelSelector
      value={selectedModel}
      onValueChange={setSelectedModel}
      placeholder="Select a model..."
      className="w-full"
    />
  );
}
```

#### Props
- `value?: string` - Currently selected model ID
- `onValueChange?: (value: string) => void` - Callback when selection changes
- `placeholder?: string` - Placeholder text when no model is selected
- `disabled?: boolean` - Whether the selector is disabled
- `className?: string` - Additional CSS classes
- `compact?: boolean` - Use compact layout with less detail

### EnhancedModelSelector
An advanced model selector with additional features:

- **Search/Filter**: Real-time search through available models
- **Model Actions**: Download, remove, and info buttons for each model
- **Provider Management**: Collapsible provider sections
- **Progress Tracking**: Download progress indicators
- **Detailed Metadata**: Extended model information display

#### Usage
```tsx
import { EnhancedModelSelector } from '@/components/chat/EnhancedModelSelector';

function ModelManagement() {
  const [selectedModel, setSelectedModel] = useState<string>('');

  return (
    <EnhancedModelSelector
      value={selectedModel}
      onValueChange={setSelectedModel}
      onDownload={(modelId) => console.log('Download:', modelId)}
      onRemove={(modelId) => console.log('Remove:', modelId)}
      showActions={true}
    />
  );
}
```

#### Props
- All props from `ModelSelector`
- `showActions?: boolean` - Show action buttons for each model
- `onDownload?: (modelId: string) => void` - Download action callback
- `onRemove?: (modelId: string) => void` - Remove action callback
- `onInfo?: (modelId: string) => void` - Info action callback
- `searchable?: boolean` - Enable search functionality

## Utilities

### model-utils.ts
Utility functions for model management:

- `formatFileSize(bytes: number)` - Format bytes to human-readable size
- `getProviderIcon(provider: string)` - Get emoji icon for provider
- `getStatusColor(status: string)` - Get Tailwind color class for status
- `groupModelsByProvider(models: Model[])` - Group models by provider
- `sortModelsByRelevance(models: Model[])` - Sort models by relevance
- `filterModels(models: Model[], query: string)` - Filter models by search query

## API Integration

The components use the Karen Backend Service to fetch model data from:
- `/api/models/library` - Public endpoint for model library data

### Model Data Structure
```typescript
interface Model {
  id: string;
  name: string;
  provider: string;
  size: number;
  description: string;
  capabilities: string[];
  status: 'local' | 'available' | 'downloading';
  download_progress?: number;
  metadata: Record<string, any>;
  local_path?: string;
  download_url?: string;
  // ... additional fields
}
```

## Styling

The components use:
- **shadcn/ui**: For base UI components (Select, Badge, Button, etc.)
- **Tailwind CSS**: For styling and responsive design
- **Lucide React**: For icons
- **CSS Variables**: For theme consistency

## Testing

The components are validated directly inside the production chat experience.  Use the
`/chat` route to exercise model selection behaviour within the fully authenticated
workflow.

## Authentication

The model selector components use public API endpoints that don't require authentication, ensuring they work even when users aren't logged in.

## Performance

- **Lazy Loading**: Models are fetched only when needed
- **Caching**: API responses are cached to reduce server load
- **Debounced Search**: Search queries are debounced to improve performance
- **Virtual Scrolling**: Large model lists use virtual scrolling (in enhanced version)

## Accessibility

- Full keyboard navigation support
- Screen reader compatible
- High contrast mode support
- Focus management
- ARIA labels and descriptions

## Browser Support

- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Progressive enhancement for older browsers