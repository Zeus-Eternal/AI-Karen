# Layout Components API Documentation

This document provides detailed API documentation for all layout components in the KAREN-Theme-Default application.

## Table of Contents

1. [AppShell](#appshell)
2. [ModernLayout Components](#modernlayout-components)
3. [Header](#Header)
4. [ModernSidebar](#modernsidebar)
5. [AuthenticatedHeader](#authenticatedheader)
6. [DeveloperNav](#developernav)
7. [ErrorBoundary](#errorboundary)
8. [Layout Types](#layout-types)

---

## AppShell

The main application shell component that provides the overall layout structure.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the AppShell |

### Example

```tsx
import { AppShell } from '@/components/layout';

function MyApp() {
  return (
    <AppShell className="custom-class">
      <YourContent />
    </AppShell>
  );
}
```

### Accessibility

- Includes a "Skip to main content" link for keyboard navigation
- Uses semantic HTML elements with proper ARIA roles
- Main content area has `id="main-content"` for skip link target

---

## ModernLayout Components

A collection of flexible layout components for building responsive layouts.

### Layout

Base layout component that provides a full-page container.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the Layout |

#### Example

```tsx
import { Layout } from '@/components/layout';

function MyPage() {
  return (
    <Layout className="bg-gray-100">
      <YourContent />
    </Layout>
  );
}
```

### LayoutGrid

Grid-based layout component using CSS Grid.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the LayoutGrid |

#### Example

```tsx
import { LayoutGrid } from '@/components/layout';

function MyGrid() {
  return (
    <LayoutGrid className="grid-cols-3">
      <div>Column 1</div>
      <div>Column 2</div>
      <div>Column 3</div>
    </LayoutGrid>
  );
}
```

### LayoutFlex

Flexbox-based layout component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the LayoutFlex |

#### Example

```tsx
import { LayoutFlex } from '@/components/layout';

function MyFlex() {
  return (
    <LayoutFlex className="flex-row">
      <div>Item 1</div>
      <div>Item 2</div>
    </LayoutFlex>
  );
}
```

### LayoutSection

Section component for content areas.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the LayoutSection |

#### Example

```tsx
import { LayoutSection } from '@/components/layout';

function MySection() {
  return (
    <LayoutSection className="py-8">
      <h2>Section Title</h2>
      <p>Section content</p>
    </LayoutSection>
  );
}
```

### LayoutHeader

Header component for page or section headers.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the LayoutHeader |

#### Example

```tsx
import { LayoutHeader } from '@/components/layout';

function MyHeader() {
  return (
    <LayoutHeader className="bg-blue-500 text-white">
      <h1>Page Title</h1>
    </LayoutHeader>
  );
}
```

### LayoutContainer

Container component with responsive width constraints.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the LayoutContainer |

#### Example

```tsx
import { LayoutContainer } from '@/components/layout';

function MyContainer() {
  return (
    <LayoutContainer className="max-w-4xl">
      <p>Centered content</p>
    </LayoutContainer>
  );
}
```

---

## Header

The main header component with navigation and user controls.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |
| `children` | `React.ReactNode` | `undefined` | Content to render within the Header |

### Example

```tsx
import { Header } from '@/components/layout';

function MyHeader() {
  return (
    <Header className="border-b">
      <h1>Application Title</h1>
      <nav>Navigation Items</nav>
    </Header>
  );
}
```

### Accessibility

- Uses `role="toolbar"` for toolbar functionality
- Includes proper ARIA labels for interactive elements
- Supports keyboard navigation
- Icons have `aria-hidden="true"` for decorative elements

---

## ModernSidebar

A collapsible sidebar with navigation sections.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |

### Example

```tsx
import { Sidebar } from '@/components/layout';

function MySidebar() {
  return (
    <SidebarclassName="w-64" />
  );
}
```

### Features

- Collapsible with toggle button
- Multiple navigation sections
- Active state indicators
- Responsive design for mobile devices
- Keyboard navigation support

### Accessibility

- Uses `role="navigation"` with proper labels
- Includes "Skip to main content" link
- Proper ARIA attributes for collapsible state
- Keyboard navigation support
- Icons have `aria-hidden="true"` for decorative elements

---

## AuthenticatedHeader

Header component for authenticated users with profile information.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |

### Example

```tsx
import { AuthenticatedHeader } from '@/components/layout';

function MyAuthenticatedHeader() {
  return (
    <AuthenticatedHeader className="shadow-md" />
  );
}
```

### Features

- User profile display
- Notification indicators
- User menu with actions
- Responsive design
- Keyboard navigation support

### Accessibility

- Uses `role="toolbar"` for toolbar functionality
- Includes proper ARIA labels for interactive elements
- Supports keyboard navigation
- Icons have `aria-hidden="true"` for decorative elements

---

## DeveloperNav

Developer navigation component with tools and links.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `className` | `string` | `''` | Additional CSS classes to apply to the component |

### Example

```tsx
import { DeveloperNav } from '@/components/layout';

function MyDeveloperNav() {
  return (
    <DeveloperNav className="bg-gray-900" />
  );
}
```

### Features

- Navigation links to developer tools
- Status badges (New, Beta, etc.)
- Dropdown menus for related tools
- Responsive design
- Keyboard navigation support

### Accessibility

- Uses `role="navigation"` with proper labels
- Includes proper ARIA attributes for menu items
- Keyboard navigation support
- Icons have `aria-hidden="true"` for decorative elements

---

## ErrorBoundary

Error handling components for graceful failure recovery.

### Components

1. **ErrorBoundary** - Class-based error boundary component
2. **useErrorBoundary** - Hook-based error boundary
3. **withErrorBoundary** - Higher-order component wrapper

### ErrorBoundary Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `React.ReactNode` | `undefined` | Content to render within the ErrorBoundary |
| `fallback` | `React.ReactNode` | `undefined` | Fallback UI to render when an error occurs |
| `onError` | `(error: Error, errorInfo: React.ErrorInfo) => void` | `undefined` | Callback function when an error occurs |

### Example

```tsx
import { ErrorBoundary } from '@/components/ui/error-boundary';

function MyComponent() {
  return (
    <ErrorBoundary 
      fallback={<div>Something went wrong</div>}
      onError={(error, errorInfo) => console.error(error, errorInfo)}
    >
      <YourComponent />
    </ErrorBoundary>
  );
}
```

### useErrorBoundary Hook

```tsx
import { useErrorBoundary } from '@/components/ui/error-boundary';

function MyComponent() {
  const { error, resetError } = useErrorBoundary();
  
  if (error) {
    return (
      <div>
        <h2>Something went wrong</h2>
        <button onClick={resetError}>Try again</button>
      </div>
    );
  }
  
  return <YourComponent />;
}
```

### withErrorBoundary HOC

```tsx
import { withErrorBoundary } from '@/components/ui/error-boundary';

const MyComponentWithBoundary = withErrorBoundary(MyComponent, {
  fallback: <div>Something went wrong</div>,
});
```

---

## Layout Types

Comprehensive TypeScript type definitions for all layout components.

### Key Types

#### LayoutProps

```tsx
interface LayoutProps {
  className?: string;
  children?: React.ReactNode;
}
```

#### HeaderProps

```tsx
interface HeaderProps {
  className?: string;
  children?: React.ReactNode;
}
```

#### ModernSidebarProps

```tsx
interface ModernSidebarProps {
  className?: string;
}
```

#### AuthenticatedHeaderProps

```tsx
interface AuthenticatedHeaderProps {
  className?: string;
}
```

#### DeveloperNavProps

```tsx
interface DeveloperNavProps {
  className?: string;
}
```

### Usage

```tsx
import type { 
  LayoutProps, 
  HeaderProps, 
  ModernSidebarProps 
} from '@/components/layout/layout-types';

// Use types for props validation
function MyComponent({ className, children }: LayoutProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}
```

---

## Styling Guidelines

All layout components follow consistent styling patterns:

### CSS Classes

- Use Tailwind CSS utility classes
- Follow BEM naming convention for custom classes
- Use responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`) for responsive design
- Use state prefixes (`hover:`, `focus:`, `active:`, `disabled:`) for interactive states

### Responsive Breakpoints

- `sm:` 640px and up
- `md:` 768px and up
- `lg:` 1024px and up
- `xl:` 1280px and up
- `2xl:` 1536px and up

### Color Palette

- Primary: `bg-primary`, `text-primary`, `border-primary`
- Secondary: `bg-secondary`, `text-secondary`, `border-secondary`
- Background: `bg-background`, `text-background`
- Foreground: `bg-foreground`, `text-foreground`

---

## Performance Considerations

All layout components are optimized for performance:

- **React.memo**: All components are wrapped in `React.memo` to prevent unnecessary re-renders
- **useMemo**: Expensive calculations are memoized using `useMemo`
- **useCallback**: Event handlers and functions passed as props are memoized using `useCallback`
- **Debouncing**: Resize event handlers are debounced to improve performance
- **Context Optimization**: Context values are memoized to prevent unnecessary updates

---

## Testing Guidelines

All layout components include comprehensive tests:

### Test Structure

- **Rendering Tests**: Verify components render correctly
- **Accessibility Tests**: Verify ARIA compliance and keyboard navigation
- **Interaction Tests**: Verify user interactions work as expected
- **Responsive Tests**: Verify components work across different screen sizes
- **Error Handling Tests**: Verify error boundaries work correctly
- **Performance Tests**: Verify components are optimized for performance

### Testing Tools

- **Vitest**: Test runner
- **Testing Library**: Testing utilities
- **Jest DOM**: DOM testing utilities
- **User Event**: User interaction simulation

### Running Tests

```bash
# Run all tests
npm test

# Run specific component tests
npm test AppShell

# Run tests with coverage
npm test -- --coverage