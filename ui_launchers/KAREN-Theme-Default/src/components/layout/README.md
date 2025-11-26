# Layout Components

This directory contains a comprehensive set of layout components for the KAREN-Theme-Default application. These components provide a modern, accessible, and responsive foundation for building user interfaces.

## Components Overview

### Core Layout Components

1. **AppShell** - The main application shell that provides the overall layout structure
2. **ModernLayout** - A collection of flexible layout components (Layout, LayoutGrid, LayoutFlex, etc.)
3. **Header** - The main header component with navigation and user controls
4. **ModernSidebar** - A collapsible sidebar with navigation sections
5. **AuthenticatedHeader** - Header component for authenticated users with profile information
6. **DeveloperNav** - Developer navigation with tools and links

### Supporting Components

1. **ErrorBoundary** - Error handling components for graceful failure recovery
2. **Layout Types** - Comprehensive TypeScript type definitions for all layout components

## Features

### Performance Optimizations
- All components are wrapped in `React.memo` to prevent unnecessary re-renders
- Extensive use of `useMemo` hooks for expensive calculations
- `useCallback` hooks for stable function references
- Debounced event handlers for resize events

### Accessibility Features
- Proper ARIA attributes and roles throughout
- Skip to main content links for keyboard navigation
- Semantic HTML structure with proper landmark roles
- Full keyboard navigation support
- Screen reader compatibility

### Modern React Patterns
- Component composition patterns
- Custom hooks for shared logic
- Context API for state management
- ForwardRef for DOM access
- TypeScript for type safety

### Responsive Design
- Mobile-first approach
- Responsive breakpoints
- Collapsible navigation for mobile devices
- Touch-friendly interaction areas

## Usage

### AppShell

```tsx
import { AppShell } from '@/components/layout';

function MyComponent() {
  return (
    <AppShell>
      <YourContent />
    </AppShell>
  );
}
```

### ModernLayout Components

```tsx
import { 
  Layout, 
  LayoutGrid, 
  LayoutFlex, 
  LayoutSection, 
  LayoutHeader, 
  LayoutContainer 
} from '@/components/layout';

function MyComponent() {
  return (
    <Layout>
      <LayoutHeader>
        <h1>Header Content</h1>
      </LayoutHeader>
      <LayoutSection>
        <LayoutContainer>
          <LayoutGrid>
            <div>Grid Content</div>
          </LayoutGrid>
        </LayoutContainer>
      </LayoutSection>
    </Layout>
  );
}
```

### Header

```tsx
import { Header } from '@/components/layout';

function MyComponent() {
  return (
    <Header>
      <h1>Application Title</h1>
    </Header>
  );
}
```

### ModernSidebar

```tsx
import { Sidebar } from '@/components/layout';

function MyComponent() {
  return (
    <Sidebar/>
  );
}
```

### AuthenticatedHeader

```tsx
import { AuthenticatedHeader } from '@/components/layout';

function MyComponent() {
  return (
    <AuthenticatedHeader />
  );
}
```

### DeveloperNav

```tsx
import { DeveloperNav } from '@/components/layout';

function MyComponent() {
  return (
    <DeveloperNav />
  );
}
```

## Error Handling

All components include error boundaries to gracefully handle errors:

```tsx
import { ErrorBoundary } from '@/components/ui/error-boundary';

function MyComponent() {
  return (
    <ErrorBoundary>
      <YourComponent />
    </ErrorBoundary>
  );
}
```

## Styling

Components use Tailwind CSS for styling with a consistent design system:

- **Colors**: Primary, secondary, background, foreground
- **Spacing**: Consistent padding and margins
- **Typography**: Font sizes, weights, and line heights
- **Breakpoints**: Responsive design for mobile, tablet, and desktop

## Testing

All components have comprehensive test coverage using Vitest and Testing Library:

- Unit tests for individual components
- Integration tests for component interactions
- Accessibility tests for ARIA compliance
- Performance tests for rendering optimization

Run tests with:

```bash
npm test
```

## TypeScript Support

Comprehensive TypeScript type definitions are provided in `layout-types.ts`:

```tsx
import type { 
  LayoutProps, 
  LayoutGridProps, 
  LayoutFlexProps,
  // ... other types
} from '@/components/layout/layout-types';
```

## Contributing

When contributing to layout components:

1. Follow the established patterns and conventions
2. Ensure accessibility compliance
3. Add tests for new functionality
4. Update type definitions as needed
5. Document new props and features

## Dependencies

- React 18+
- Next.js 13+
- Tailwind CSS
- Lucide React Icons
- Radix UI primitives
- Vitest for testing
- TypeScript for type safety

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License