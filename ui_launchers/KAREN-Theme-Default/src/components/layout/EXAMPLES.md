# Layout Components Examples

This document provides practical examples of how to use the layout components in the KAREN-Theme-Default application.

## Table of Contents

1. [Basic Layout Examples](#basic-layout-examples)
2. [Advanced Layout Examples](#advanced-layout-examples)
3. [Responsive Design Examples](#responsive-design-examples)
4. [Theming Examples](#theming-examples)
5. [Error Handling Examples](#error-handling-examples)
6. [Accessibility Examples](#accessibility-examples)
7. [Performance Optimization Examples](#performance-optimization-examples)

---

## Basic Layout Examples

### Simple App with AppShell

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import { Sidebar } from '@/components/layout';

function SimpleApp() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">My Application</h1>
      </Header>
      
      <div className="flex">
        <Sidebar/>
        
        <main id="main-content" className="flex-1 p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome to My App</h2>
          <p>This is the main content area.</p>
        </main>
      </div>
    </AppShell>
  );
}
```

### Using ModernLayout Components

```tsx
import { 
  Layout, 
  LayoutGrid, 
  LayoutFlex, 
  LayoutSection, 
  LayoutHeader, 
  LayoutContainer 
} from '@/components/layout';

function ModernLayoutExample() {
  return (
    <Layout>
      <LayoutHeader className="bg-blue-600 text-white">
        <LayoutContainer>
          <h1 className="text-3xl font-bold">Modern Layout</h1>
        </LayoutContainer>
      </LayoutHeader>
      
      <LayoutSection>
        <LayoutContainer>
          <LayoutGrid className="grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-3">Card 1</h2>
              <p>Content for card 1</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-3">Card 2</h2>
              <p>Content for card 2</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-3">Card 3</h2>
              <p>Content for card 3</p>
            </div>
          </LayoutGrid>
        </LayoutContainer>
      </LayoutSection>
    </Layout>
  );
}
```

### Dashboard Layout

```tsx
import { AppShell } from '@/components/layout';
import { AuthenticatedHeader } from '@/components/layout';
import { Sidebar } from '@/components/layout';
import { LayoutGrid, LayoutContainer } from '@/components/layout';

function Dashboard() {
  return (
    <AppShell>
      <AuthenticatedHeader />
      
      <div className="flex">
        <Sidebar/>
        
        <main id="main-content" className="flex-1">
          <LayoutContainer className="py-6">
            <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
            
            <LayoutGrid className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold mb-2">Total Users</h2>
                <p className="text-3xl font-bold">1,234</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold mb-2">Revenue</h2>
                <p className="text-3xl font-bold">$12,345</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold mb-2">Conversion</h2>
                <p className="text-3xl font-bold">5.6%</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold mb-2">Sessions</h2>
                <p className="text-3xl font-bold">8,901</p>
              </div>
            </LayoutGrid>
          </LayoutContainer>
        </main>
      </div>
    </AppShell>
  );
}
```

---

## Advanced Layout Examples

### Nested Layouts

```tsx
import { 
  Layout, 
  LayoutGrid, 
  LayoutFlex, 
  LayoutSection, 
  LayoutHeader, 
  LayoutContainer 
} from '@/components/layout';

function NestedLayoutExample() {
  return (
    <Layout>
      <LayoutHeader>
        <LayoutContainer>
          <h1>Nested Layout Example</h1>
        </LayoutContainer>
      </LayoutHeader>
      
      <LayoutSection>
        <LayoutContainer>
          <LayoutGrid className="grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <LayoutGrid className="grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Card 1</h2>
                  <p>Content for card 1</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Card 2</h2>
                  <p>Content for card 2</p>
                </div>
              </LayoutGrid>
            </div>
            
            <div>
              <LayoutFlex className="flex-col gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Sidebar Item 1</h2>
                  <p>Content for sidebar item 1</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Sidebar Item 2</h2>
                  <p>Content for sidebar item 2</p>
                </div>
              </LayoutFlex>
            </div>
          </LayoutGrid>
        </LayoutContainer>
      </LayoutSection>
    </Layout>
  );
}
```

### Complex Dashboard with Multiple Sections

```tsx
import { AppShell } from '@/components/layout';
import { AuthenticatedHeader } from '@/components/layout';
import { Sidebar } from '@/components/layout';
import { DeveloperNav } from '@/components/layout';
import { 
  LayoutGrid, 
  LayoutFlex, 
  LayoutSection, 
  LayoutContainer 
} from '@/components/layout';

function ComplexDashboard() {
  return (
    <AppShell>
      <AuthenticatedHeader />
      
      <div className="flex">
        <Sidebar/>
        <DeveloperNav className="hidden lg:block" />
        
        <main id="main-content" className="flex-1">
          <LayoutContainer className="py-6">
            <h1 className="text-2xl font-bold mb-6">Complex Dashboard</h1>
            
            <LayoutSection>
              <LayoutGrid className="grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Main Content</h2>
                  <p>This is the main content area with detailed information.</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-xl font-semibold mb-4">Sidebar</h2>
                  <p>This is the sidebar with related information.</p>
                </div>
              </LayoutGrid>
            </LayoutSection>
            
            <LayoutSection>
              <h2 className="text-xl font-semibold mb-4">Data Grid</h2>
              <LayoutGrid className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((item) => (
                  <div key={item} className="bg-white p-4 rounded-lg shadow">
                    <h3 className="font-semibold mb-2">Item {item}</h3>
                    <p>Description for item {item}</p>
                  </div>
                ))}
              </LayoutGrid>
            </LayoutSection>
          </LayoutContainer>
        </main>
      </div>
    </AppShell>
  );
}
```

---

## Responsive Design Examples

### Responsive Grid Layout

```tsx
import { Layout, LayoutGrid, LayoutSection, LayoutContainer } from '@/components/layout';

function ResponsiveGridLayout() {
  return (
    <Layout>
      <LayoutSection>
        <LayoutContainer>
          <h1 className="text-2xl font-bold mb-6">Responsive Grid Layout</h1>
          
          {/* 1 column on mobile, 2 on tablet, 4 on desktop */}
          <LayoutGrid className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((item) => (
              <div key={item} className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-semibold mb-2">Card {item}</h2>
                <p>This card adapts to different screen sizes.</p>
              </div>
            ))}
          </LayoutGrid>
        </LayoutContainer>
      </LayoutSection>
    </Layout>
  );
}
```

### Responsive Sidebar Layout

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import { Sidebar } from '@/components/layout';

function ResponsiveSidebarLayout() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Responsive Sidebar Layout</h1>
      </Header>
      
      <div className="flex">
        {/* Sidebar is hidden on mobile, visible on tablet and desktop */}
        <SidebarclassName="hidden md:block" />
        
        <main id="main-content" className="flex-1 p-6">
          <h2 className="text-xl font-semibold mb-4">Main Content</h2>
          <p>The sidebar is hidden on mobile devices and visible on larger screens.</p>
          
          {/* Mobile menu button (visible only on mobile) */}
          <button className="md:hidden bg-blue-500 text-white p-2 rounded">
            Toggle Menu
          </button>
        </main>
      </div>
    </AppShell>
  );
}
```

### Responsive Flex Layout

```tsx
import { Layout, LayoutFlex, LayoutSection, LayoutContainer } from '@/components/layout';

function ResponsiveFlexLayout() {
  return (
    <Layout>
      <LayoutSection>
        <LayoutContainer>
          <h1 className="text-2xl font-bold mb-6">Responsive Flex Layout</h1>
          
          {/* Column on mobile, row on tablet and desktop */}
          <LayoutFlex className="flex-col md:flex-row gap-6">
            <div className="flex-1 bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-2">Section 1</h2>
              <p>This section stacks vertically on mobile and horizontally on larger screens.</p>
            </div>
            <div className="flex-1 bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-2">Section 2</h2>
              <p>This section stacks vertically on mobile and horizontally on larger screens.</p>
            </div>
          </LayoutFlex>
        </LayoutContainer>
      </LayoutSection>
    </Layout>
  );
}
```

---

## Theming Examples

### Dark Theme Layout

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import { Sidebar } from '@/components/layout';

function DarkThemeLayout() {
  return (
    <AppShell className="bg-gray-900 text-white">
      <Header className="bg-gray-800 border-gray-700">
        <h1 className="text-2xl font-bold">Dark Theme Layout</h1>
      </Header>
      
      <div className="flex">
        <SidebarclassName="bg-gray-800 border-gray-700" />
        
        <main id="main-content" className="flex-1 p-6">
          <h2 className="text-xl font-semibold mb-4">Main Content</h2>
          <div className="bg-gray-800 p-6 rounded-lg">
            <p>This is a dark-themed layout with proper contrast and readability.</p>
          </div>
        </main>
      </div>
    </AppShell>
  );
}
```

### Custom Colored Theme

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import { Sidebar } from '@/components/layout';

function CustomColoredTheme() {
  return (
    <AppShell className="bg-indigo-50">
      <Header className="bg-indigo-600 text-white">
        <h1 className="text-2xl font-bold">Custom Colored Theme</h1>
      </Header>
      
      <div className="flex">
        <SidebarclassName="bg-indigo-100" />
        
        <main id="main-content" className="flex-1 p-6">
          <h2 className="text-xl font-semibold mb-4 text-indigo-900">Main Content</h2>
          <div className="bg-white p-6 rounded-lg shadow border border-indigo-200">
            <p className="text-indigo-800">This is a custom-colored layout with an indigo theme.</p>
          </div>
        </main>
      </div>
    </AppShell>
  );
}
```

---

## Error Handling Examples

### Error Boundary with Fallback UI

```tsx
import { AppShell } from '@/components/layout';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Header } from '@/components/layout';

function ErrorHandlingExample() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Error Handling Example</h1>
      </Header>
      
      <main id="main-content" className="p-6">
        <ErrorBoundary 
          fallback={
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-red-800 mb-2">Something went wrong</h2>
              <p className="text-red-600">We're sorry, but something went wrong. Please try again later.</p>
              <button 
                className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                onClick={() => window.location.reload()}
              >
                Reload Page
              </button>
            </div>
          }
        >
          <BuggyComponent />
        </ErrorBoundary>
      </main>
    </AppShell>
  );
}

// This component will throw an error
function BuggyComponent() {
  const [count, setCount] = React.useState(0);
  
  if (count > 2) {
    throw new Error('This is a test error');
  }
  
  return (
    <div>
      <p>Count: {count}</p>
      <button 
        className="bg-blue-500 text-white px-4 py-2 rounded"
        onClick={() => setCount(count + 1)}
      >
        Increment
      </button>
      <p className="mt-4 text-sm text-gray-600">
        Click the button 3 times to trigger an error and see the error boundary in action.
      </p>
    </div>
  );
}
```

### Error Boundary with Error Recovery

```tsx
import { AppShell } from '@/components/layout';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { Header } from '@/components/layout';

function ErrorRecoveryExample() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Error Recovery Example</h1>
      </Header>
      
      <main id="main-content" className="p-6">
        <ErrorBoundary 
          fallback={({ error, resetError }) => (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-red-800 mb-2">Something went wrong</h2>
              <p className="text-red-600 mb-4">{error.message}</p>
              <button 
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 mr-2"
                onClick={resetError}
              >
                Try Again
              </button>
              <button 
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                onClick={() => window.location.reload()}
              >
                Reload Page
              </button>
            </div>
          )}
        >
          <BuggyComponentWithRecovery />
        </ErrorBoundary>
      </main>
    </AppShell>
  );
}

function BuggyComponentWithRecovery() {
  const [shouldError, setShouldError] = React.useState(false);
  
  if (shouldError) {
    throw new Error('This is a recoverable error');
  }
  
  return (
    <div>
      <p>This component is working properly.</p>
      <button 
        className="bg-blue-500 text-white px-4 py-2 rounded"
        onClick={() => setShouldError(true)}
      >
        Trigger Error
      </button>
      <p className="mt-4 text-sm text-gray-600">
        Click the button to trigger an error. You can then recover using the "Try Again" button.
      </p>
    </div>
  );
}
```

---

## Accessibility Examples

### Accessible Navigation

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';

function AccessibleNavigationExample() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Accessible Navigation</h1>
        <nav aria-label="Main navigation">
          <ul className="flex space-x-4">
            <li><a href="#home" className="hover:underline">Home</a></li>
            <li><a href="#about" className="hover:underline">About</a></li>
            <li><a href="#contact" className="hover:underline">Contact</a></li>
          </ul>
        </nav>
      </Header>
      
      <main id="main-content" className="p-6">
        <h2 className="text-xl font-semibold mb-4">Main Content</h2>
        <p>This page includes accessible navigation with proper ARIA attributes.</p>
        
        <section id="home" className="mt-8">
          <h3 className="text-lg font-semibold mb-2">Home Section</h3>
          <p>Content for the home section.</p>
        </section>
        
        <section id="about" className="mt-8">
          <h3 className="text-lg font-semibold mb-2">About Section</h3>
          <p>Content for the about section.</p>
        </section>
        
        <section id="contact" className="mt-8">
          <h3 className="text-lg font-semibold mb-2">Contact Section</h3>
          <p>Content for the contact section.</p>
        </section>
      </main>
    </AppShell>
  );
}
```

### Accessible Form

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';

function AccessibleFormExample() {
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Accessible Form Example</h1>
      </Header>
      
      <main id="main-content" className="p-6">
        <h2 className="text-xl font-semibold mb-4">Contact Form</h2>
        
        <form className="max-w-md">
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium mb-1">
              Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              className="w-full px-3 py-2 border rounded-md"
              aria-required="true"
              aria-describedby="name-error"
            />
            <div id="name-error" className="text-red-600 text-sm mt-1 hidden">
              Please enter your name
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              className="w-full px-3 py-2 border rounded-md"
              aria-required="true"
              aria-describedby="email-error"
            />
            <div id="email-error" className="text-red-600 text-sm mt-1 hidden">
              Please enter a valid email address
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="message" className="block text-sm font-medium mb-1">
              Message
            </label>
            <textarea
              id="message"
              name="message"
              rows={4}
              className="w-full px-3 py-2 border rounded-md"
              aria-required="true"
              aria-describedby="message-error"
            ></textarea>
            <div id="message-error" className="text-red-600 text-sm mt-1 hidden">
              Please enter a message
            </div>
          </div>
          
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Submit
          </button>
        </form>
      </main>
    </AppShell>
  );
}
```

---

## Performance Optimization Examples

### Memoized Components

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import React, { useState, useEffect } from 'react';

// Memoized child component
const MemoizedChildComponent = React.memo(function MemoizedChildComponent({ data }: { data: string }) {
  console.log('MemoizedChildComponent rendered');
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <p>{data}</p>
    </div>
  );
});

function PerformanceOptimizationExample() {
  const [count, setCount] = useState(0);
  const [data, setData] = useState('Initial data');
  
  // This effect simulates data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setData('Updated data');
    }, 2000);
    
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Performance Optimization Example</h1>
      </Header>
      
      <main id="main-content" className="p-6">
        <h2 className="text-xl font-semibold mb-4">Memoized Components</h2>
        
        <div className="mb-6">
          <p>Count: {count}</p>
          <button 
            className="bg-blue-500 text-white px-4 py-2 rounded"
            onClick={() => setCount(count + 1)}
          >
            Increment
          </button>
          <p className="mt-2 text-sm text-gray-600">
            Clicking this button updates the count but doesn't re-render the memoized component below.
          </p>
        </div>
        
        <MemoizedChildComponent data={data} />
        
        <p className="mt-4 text-sm text-gray-600">
          Check the console to see when the MemoizedChildComponent renders.
          It only renders when the data prop changes, not when the count changes.
        </p>
      </main>
    </AppShell>
  );
}
```

### Optimized List Rendering

```tsx
import { AppShell } from '@/components/layout';
import { Header } from '@/components/layout';
import React, { useState, useMemo } from 'react';

// Memoized list item component
const ListItem = React.memo(function ListItem({ item }: { item: { id: number; name: string; description: string } }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow mb-4">
      <h3 className="text-lg font-semibold">{item.name}</h3>
      <p>{item.description}</p>
    </div>
  );
});

function OptimizedListExample() {
  const [filter, setFilter] = useState('');
  const [items, setItems] = useState([
    { id: 1, name: 'Item 1', description: 'Description for item 1' },
    { id: 2, name: 'Item 2', description: 'Description for item 2' },
    { id: 3, name: 'Item 3', description: 'Description for item 3' },
    { id: 4, name: 'Item 4', description: 'Description for item 4' },
    { id: 5, name: 'Item 5', description: 'Description for item 5' },
  ]);
  
  // Memoized filtered items
  const filteredItems = useMemo(() => {
    console.log('Filtering items');
    return items.filter(item => 
      item.name.toLowerCase().includes(filter.toLowerCase()) ||
      item.description.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);
  
  return (
    <AppShell>
      <Header>
        <h1 className="text-2xl font-bold">Optimized List Rendering</h1>
      </Header>
      
      <main id="main-content" className="p-6">
        <h2 className="text-xl font-semibold mb-4">Filterable List</h2>
        
        <div className="mb-6">
          <input
            type="text"
            placeholder="Filter items..."
            className="w-full px-3 py-2 border rounded-md"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <p className="mt-2 text-sm text-gray-600">
            Typing in the filter field will trigger the useMemo hook to filter the items.
          </p>
        </div>
        
        <div>
          {filteredItems.map(item => (
            <ListItem key={item.id} item={item} />
          ))}
        </div>
        
        <p className="mt-4 text-sm text-gray-600">
          Check the console to see when the filtering runs. It only runs when the filter or items change.
        </p>
      </main>
    </AppShell>
  );
}