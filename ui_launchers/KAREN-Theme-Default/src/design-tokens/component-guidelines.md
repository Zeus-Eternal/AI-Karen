# Component Styling Guidelines

This document provides specific guidelines for styling components using the modern design token system.

## Table of Contents

1. [Component Architecture](#component-architecture)
2. [Styling Patterns](#styling-patterns)
3. [Responsive Design](#responsive-design)
4. [Theme Support](#theme-support)
5. [Animation Guidelines](#animation-guidelines)
6. [Accessibility Requirements](#accessibility-requirements)
7. [Component Examples](#component-examples)

## Component Architecture

### File Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.module.css
│   │   │   ├── Button.stories.tsx
│   │   │   └── index.ts
│   │   └── Card/
│   │       ├── Card.tsx
│   │       ├── Card.module.css
│   │       ├── Card.stories.tsx
│   │       └── index.ts
│   └── layout/
│       ├── Grid/
│       └── Container/
├── design-tokens/
│   ├── index.ts
│   ├── css-tokens.ts
│   └── README.md
└── styles/
    ├── design-tokens.css
    ├── utilities.css
    └── globals.css
```

### Component Structure

Each component should follow this structure:

```typescript
// Button.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  // Base styles using design tokens
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'underline-offset-4 hover:underline text-primary',
      },
      size: {
        default: 'h-10 py-2 px-4',
        sm: 'h-9 px-3 rounded-md',
        lg: 'h-11 px-8 rounded-md',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    return (
      <Button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
```

## Styling Patterns

### 1. Use CSS Custom Properties

Always use design tokens through CSS custom properties:

```css
/* Button.module.css */
.button {
  /* Spacing */
  padding: var(--space-sm) var(--space-md);
  gap: var(--space-xs);
  
  /* Typography */
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-none);
  
  /* Colors */
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
  border: 1px solid transparent;
  
  /* Layout */
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  /* Animation */
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized);
}

.button:hover {
  background-color: var(--color-primary-600);
  transform: translateY(-1px);
}

.button:focus-visible {
  outline: var(--focus-ring-width) var(--focus-ring-style) var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}
```

### 2. Variant System

Use a consistent variant system for component variations:

```css
/* Base component */
.card {
  background-color: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-sm);
}

/* Variants */
.card--elevated {
  box-shadow: var(--shadow-lg);
}

.card--outlined {
  background-color: transparent;
  border: 2px solid var(--color-neutral-300);
  box-shadow: none;
}

.card--filled {
  background-color: var(--color-primary-50);
  border-color: var(--color-primary-200);
}

/* Sizes */
.card--sm {
  padding: var(--space-md);
  border-radius: var(--radius-md);
}

.card--lg {
  padding: var(--space-xl);
  border-radius: var(--radius-xl);
}
```

### 3. State Management

Handle component states consistently:

```css
.input {
  background-color: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-300);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-base);
  transition: border-color var(--duration-fast) var(--ease-standard);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.input:disabled {
  background-color: var(--color-neutral-100);
  color: var(--color-neutral-400);
  cursor: not-allowed;
}

.input--error {
  border-color: var(--color-error-500);
}

.input--error:focus {
  border-color: var(--color-error-500);
  box-shadow: 0 0 0 3px var(--color-error-100);
}
```

## Responsive Design

### Container Queries

Use container queries for component-based responsive design:

```css
.card-grid {
  display: grid;
  gap: var(--space-md);
  container-type: inline-size;
}

/* Component responds to its container, not viewport */
@container (min-width: 300px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-lg);
  }
}

@container (min-width: 600px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-xl);
  }
}
```

### Fallback Media Queries

Provide fallbacks for browsers without container query support:

```css
/* Fallback for older browsers */
@media (min-width: 640px) {
  @supports not (container-type: inline-size) {
    .card-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: var(--space-lg);
    }
  }
}
```

### Fluid Spacing

Use clamp() for fluid spacing that adapts to screen size:

```css
.section {
  padding: clamp(var(--space-lg), 4vw, var(--space-3xl));
  margin-bottom: clamp(var(--space-xl), 6vw, var(--space-4xl));
}
```

## Theme Support

### Semantic Color Mapping

Map design tokens to semantic CSS properties for easy theming:

```css
:root {
  /* Light theme mappings */
  --background: var(--color-neutral-50);
  --foreground: var(--color-neutral-900);
  --card-background: var(--color-neutral-50);
  --card-foreground: var(--color-neutral-900);
  --border: var(--color-neutral-200);
  --input-background: var(--color-neutral-50);
}

.dark {
  /* Dark theme mappings */
  --background: var(--color-neutral-950);
  --foreground: var(--color-neutral-50);
  --card-background: var(--color-neutral-900);
  --card-foreground: var(--color-neutral-50);
  --border: var(--color-neutral-800);
  --input-background: var(--color-neutral-900);
}

/* Components use semantic properties */
.card {
  background-color: var(--card-background);
  color: var(--card-foreground);
  border: 1px solid var(--border);
}
```

### Theme-Aware Components

Components should automatically adapt to theme changes:

```css
.button {
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
}

/* Dark theme automatically uses different primary colors */
.dark .button {
  /* No additional CSS needed - design tokens handle this */
}
```

## Animation Guidelines

### Consistent Timing

Use design token animation values for consistency:

```css
.modal {
  opacity: 0;
  transform: scale(0.95);
  transition:
    opacity var(--duration-normal) var(--ease-emphasized),
    transform var(--duration-normal) var(--ease-emphasized);
}

.modal--open {
  opacity: 1;
  transform: scale(1);
}
```

### Micro-interactions

Add subtle micro-interactions using design tokens:

```css
.button {
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

.button:active {
  transform: translateY(0);
  transition-duration: var(--duration-instant);
}
```

### Reduced Motion Support

Respect user preferences for reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  .animated-component {
    animation: none;
    transition: none;
  }
}
```

## Accessibility Requirements

### Focus Management

Ensure proper focus styles using design tokens:

```css
.interactive-element:focus-visible {
  outline: var(--focus-ring-width) var(--focus-ring-style) var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  border-radius: var(--radius-sm);
}
```

### Color Contrast

Use design tokens that maintain proper contrast ratios:

```css
.text-primary {
  color: var(--color-primary-600); /* Ensures contrast in light theme */
}

.dark .text-primary {
  color: var(--color-primary-400); /* Ensures contrast in dark theme */
}
```

### Touch Targets

Ensure minimum touch target sizes:

```css
.touch-target {
  min-height: 44px; /* iOS minimum */
  min-width: 44px;
  padding: var(--space-sm);
}
```

## Component Examples

### Modern Button Component

```css
.button {
  /* Base styles */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  
  /* Typography */
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-none);
  text-decoration: none;
  white-space: nowrap;
  
  /* Layout */
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  min-height: 40px;
  
  /* Interaction */
  cursor: pointer;
  user-select: none;
  
  /* Animation */
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized),
    box-shadow var(--duration-fast) var(--ease-standard);
}

/* Primary variant */
.button--primary {
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
}

.button--primary:hover {
  background-color: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.button--primary:active {
  background-color: var(--color-primary-700);
  transform: translateY(0);
}

/* Secondary variant */
.button--secondary {
  background-color: var(--color-secondary-100);
  color: var(--color-secondary-900);
  border-color: var(--color-secondary-200);
}

.button--secondary:hover {
  background-color: var(--color-secondary-200);
  border-color: var(--color-secondary-300);
}

/* Outline variant */
.button--outline {
  background-color: transparent;
  color: var(--color-primary-600);
  border-color: var(--color-primary-300);
}

.button--outline:hover {
  background-color: var(--color-primary-50);
  border-color: var(--color-primary-400);
}

/* Ghost variant */
.button--ghost {
  background-color: transparent;
  color: var(--color-neutral-700);
}

.button--ghost:hover {
  background-color: var(--color-neutral-100);
}

/* Size variants */
.button--sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-xs);
  min-height: 32px;
}

.button--lg {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--text-base);
  min-height: 48px;
}

/* State modifiers */
.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.button--loading {
  color: transparent;
  position: relative;
}

.button--loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

### Modern Card Component

```css
.card {
  /* Base styles */
  background-color: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  
  /* Container query support */
  container-type: inline-size;
  container-name: card;
  
  /* Animation */
  transition:
    box-shadow var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized),
    border-color var(--duration-fast) var(--ease-standard);
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--color-neutral-300);
}

/* Card sections */
.card__header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-neutral-200);
  background-color: var(--color-neutral-50);
}

.card__content {
  padding: var(--space-lg);
}

.card__footer {
  padding: var(--space-lg);
  border-top: 1px solid var(--color-neutral-200);
  background-color: var(--color-neutral-100);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

/* Container query responsive behavior */
@container card (min-width: 400px) {
  .card__content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }
}

@container card (min-width: 600px) {
  .card {
    border-radius: var(--radius-xl);
  }
  
  .card__header,
  .card__content,
  .card__footer {
    padding: var(--space-xl);
  }
}

/* Variants */
.card--elevated {
  box-shadow: var(--shadow-lg);
}

.card--elevated:hover {
  box-shadow: var(--shadow-xl);
  transform: translateY(-4px);
}

.card--outlined {
  background-color: transparent;
  border: 2px solid var(--color-neutral-300);
  box-shadow: none;
}

.card--filled {
  background-color: var(--color-primary-50);
  border-color: var(--color-primary-200);
}

.card--filled .card__header {
  background-color: var(--color-primary-100);
  border-color: var(--color-primary-200);
}

.card--filled .card__footer {
  background-color: var(--color-primary-100);
  border-color: var(--color-primary-200);
}

/* Dark theme support */
.dark .card {
  background-color: var(--color-neutral-900);
  border-color: var(--color-neutral-800);
}

.dark .card__header {
  background-color: var(--color-neutral-900);
  border-color: var(--color-neutral-800);
}

.dark .card__footer {
  background-color: var(--color-neutral-800);
  border-color: var(--color-neutral-700);
}
```

### Form Input Component

```css
.input {
  /* Base styles */
  width: 100%;
  background-color: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-300);
  border-radius: var(--radius-md);
  padding: var(--space-sm) var(--space-md);
  
  /* Typography */
  font-family: inherit;
  font-size: var(--text-base);
  line-height: var(--line-height-normal);
  color: var(--color-neutral-900);
  
  /* Interaction */
  transition:
    border-color var(--duration-fast) var(--ease-standard),
    box-shadow var(--duration-fast) var(--ease-standard),
    background-color var(--duration-fast) var(--ease-standard);
}

.input::placeholder {
  color: var(--color-neutral-500);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
  background-color: var(--color-neutral-50);
}

.input:disabled {
  background-color: var(--color-neutral-100);
  color: var(--color-neutral-400);
  cursor: not-allowed;
  opacity: 0.7;
}

/* States */
.input--error {
  border-color: var(--color-error-500);
}

.input--error:focus {
  border-color: var(--color-error-500);
  box-shadow: 0 0 0 3px var(--color-error-100);
}

.input--success {
  border-color: var(--color-success-500);
}

.input--success:focus {
  border-color: var(--color-success-500);
  box-shadow: 0 0 0 3px var(--color-success-100);
}

/* Sizes */
.input--sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-sm);
}

.input--lg {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--text-lg);
}

/* Dark theme */
.dark .input {
  background-color: var(--color-neutral-900);
  border-color: var(--color-neutral-700);
  color: var(--color-neutral-100);
}

.dark .input::placeholder {
  color: var(--color-neutral-400);
}

.dark .input:focus {
  background-color: var(--color-neutral-900);
  border-color: var(--color-primary-400);
  box-shadow: 0 0 0 3px var(--color-primary-900);
}
```

## Best Practices Summary

1. **Always use design tokens** instead of hardcoded values
2. **Follow the spacing scale** for consistent layouts
3. **Use semantic color mapping** for theme support
4. **Implement container queries** for modern responsive design
5. **Provide fallbacks** for older browsers
6. **Maintain accessibility** with proper focus styles and contrast
7. **Use consistent animation patterns** with design token timing
8. **Test across themes** to ensure proper contrast and visibility
9. **Document component variants** and usage patterns
10. **Keep components composable** and reusable

By following these guidelines, you'll create a consistent, maintainable, and accessible component system that leverages the full power of the modern design token architecture.
