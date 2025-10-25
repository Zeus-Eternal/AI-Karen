# Modern Design Token System Documentation

This documentation covers the comprehensive design token system and CSS architecture for the Karen AI UI modernization project.

## Table of Contents

1. [Overview](#overview)
2. [Design Token Structure](#design-token-structure)
3. [Usage Patterns](#usage-patterns)
4. [CSS Architecture](#css-architecture)
5. [Component Styling Guidelines](#component-styling-guidelines)
6. [Naming Conventions](#naming-conventions)
7. [Examples](#examples)
8. [Migration Guide](#migration-guide)

## Overview

The design token system provides a centralized, scalable approach to managing design decisions across the application. It includes:

- **Semantic color scales** with 11-step progression
- **Mathematical spacing system** using T-shirt sizing
- **Fluid typography** with clamp() functions
- **Modern shadow system** with proper layering
- **Animation tokens** with consistent easing curves
- **CSS logical properties** for internationalization
- **Container query support** for modern responsive design

## Design Token Structure

### Color System

The color system uses an 11-step scale (50-950) for maximum flexibility:

```typescript
interface ColorScale {
  50: string;   // Lightest
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;  // Base color
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;  // Darkest
}
```

#### Color Categories

- **Primary**: Electric purple theme (`--color-primary-*`)
- **Secondary**: Soft lavender (`--color-secondary-*`)
- **Neutral**: Modern grays (`--color-neutral-*`)
- **Semantic**: Success, warning, error, info (`--color-success-*`, etc.)

### Spacing System

Mathematical progression using T-shirt sizing:

```css
--space-3xs: 0.125rem;  /* 2px */
--space-2xs: 0.25rem;   /* 4px */
--space-xs: 0.5rem;     /* 8px */
--space-sm: 0.75rem;    /* 12px */
--space-md: 1rem;       /* 16px - base */
--space-lg: 1.5rem;     /* 24px */
--space-xl: 2rem;       /* 32px */
--space-2xl: 3rem;      /* 48px */
--space-3xl: 4rem;      /* 64px */
```

### Typography System

Fluid typography using clamp() functions:

```css
--text-xs: clamp(0.75rem, 0.7rem + 0.2vw, 0.8rem);
--text-sm: clamp(0.875rem, 0.8rem + 0.3vw, 0.95rem);
--text-base: clamp(1rem, 0.9rem + 0.4vw, 1.125rem);
--text-lg: clamp(1.125rem, 1rem + 0.5vw, 1.25rem);
/* ... and so on */
```

### Shadow System

Modern shadow system with proper layering:

```css
--shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

### Animation System

Consistent timing and easing:

```css
/* Durations */
--duration-instant: 0ms;
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 350ms;
--duration-slower: 500ms;

/* Easing curves */
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
--ease-emphasized: cubic-bezier(0.2, 0, 0, 1);
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
```

## Usage Patterns

### In CSS

```css
.my-component {
  /* Use spacing tokens */
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
  gap: var(--space-sm);
  
  /* Use color tokens */
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
  border: 1px solid var(--color-neutral-200);
  
  /* Use typography tokens */
  font-size: var(--text-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  
  /* Use shadow tokens */
  box-shadow: var(--shadow-md);
  
  /* Use animation tokens */
  transition: 
    background-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized);
}

.my-component:hover {
  background-color: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}
```

### In TypeScript/React

```typescript
import { designTokens, getSpacing, getColorValue } from '@/design-tokens';

// Access tokens directly
const spacing = designTokens.spacing.md; // "1rem"
const primaryColor = designTokens.colors.primary[500]; // "#a855f7"

// Use utility functions
const padding = getSpacing('lg'); // "1.5rem"
const textColor = getColorValue(designTokens.colors.neutral, 700); // "#404040"
```

### Utility Classes

```html
<!-- Spacing utilities -->
<div class="p-md m-lg gap-sm">
  
<!-- Typography utilities -->
<h1 class="text-2xl font-bold leading-tight tracking-tight">

<!-- Color utilities -->
<div class="bg-primary-500 text-primary-50 border border-neutral-200">

<!-- Shadow utilities -->
<div class="shadow-md hover:shadow-lg">

<!-- Animation utilities -->
<button class="transition-fast hover-lift">
```

## CSS Architecture

### Layer Structure

The CSS is organized in layers for optimal cascade management:

```css
/* 1. Design Tokens */
@import "./design-tokens.css";

/* 2. Utility Classes */
@import "./utilities.css";

/* 3. Base Styles */
@layer base { /* ... */ }

/* 4. Component Styles */
@layer components { /* ... */ }

/* 5. Utility Overrides */
@layer utilities { /* ... */ }
```

### Modern CSS Features

#### CSS Logical Properties

For better internationalization support:

```css
/* Instead of margin-left/margin-right */
margin-inline-start: var(--space-md);
margin-inline-end: var(--space-md);

/* Instead of margin-top/margin-bottom */
margin-block-start: var(--space-sm);
margin-block-end: var(--space-sm);
```

#### Container Queries

For component-based responsive design:

```css
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 300px) {
  .card-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }
}
```

#### Modern Focus Styles

```css
.focus-ring:focus-visible {
  outline: var(--focus-ring-width) var(--focus-ring-style) var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  border-radius: var(--radius-sm);
}
```

## Component Styling Guidelines

### 1. Use Design Tokens First

Always use design tokens instead of hardcoded values:

```css
/* ✅ Good */
.button {
  padding: var(--space-sm) var(--space-md);
  background-color: var(--color-primary-500);
  border-radius: var(--radius-md);
}

/* ❌ Bad */
.button {
  padding: 12px 16px;
  background-color: #a855f7;
  border-radius: 6px;
}
```

### 2. Follow the Spacing Scale

Use the mathematical progression for consistent spacing:

```css
/* ✅ Good - follows the scale */
.card {
  padding: var(--space-lg);        /* 24px */
  margin-bottom: var(--space-xl);  /* 32px */
  gap: var(--space-md);            /* 16px */
}

/* ❌ Bad - arbitrary values */
.card {
  padding: 20px;
  margin-bottom: 30px;
  gap: 14px;
}
```

### 3. Use Semantic Color Mapping

Map design tokens to semantic CSS custom properties:

```css
:root {
  --background: var(--color-neutral-50);
  --foreground: var(--color-neutral-900);
  --primary: var(--color-primary-500);
  --border: var(--color-neutral-200);
}

.dark {
  --background: var(--color-neutral-950);
  --foreground: var(--color-neutral-50);
  --primary: var(--color-primary-400);
  --border: var(--color-neutral-800);
}
```

### 4. Consistent Animation Patterns

Use the animation tokens for consistent motion:

```css
.interactive-element {
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized),
    box-shadow var(--duration-fast) var(--ease-standard);
}

.interactive-element:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}
```

## Naming Conventions

### CSS Custom Properties

- **Colors**: `--color-{category}-{step}` (e.g., `--color-primary-500`)
- **Spacing**: `--space-{size}` (e.g., `--space-md`)
- **Typography**: `--text-{size}` (e.g., `--text-lg`)
- **Shadows**: `--shadow-{size}` (e.g., `--shadow-md`)
- **Animation**: `--duration-{speed}`, `--ease-{curve}`

### CSS Classes

- **Utility classes**: Follow the token naming (e.g., `.p-md`, `.text-lg`, `.bg-primary-500`)
- **Component classes**: Use BEM methodology (e.g., `.card`, `.card__header`, `.card--elevated`)
- **State classes**: Use descriptive names (e.g., `.is-active`, `.is-loading`, `.has-error`)

### TypeScript Interfaces

- **PascalCase** for interfaces (e.g., `ColorScale`, `DesignTokens`)
- **camelCase** for properties (e.g., `primaryColors`, `spacingScale`)
- **kebab-case** for CSS-related strings (e.g., `'primary-500'`, `'space-md'`)

## Examples

### Button Component

```css
.button {
  /* Base styles using design tokens */
  padding: var(--space-sm) var(--space-md);
  font-size: var(--text-base);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-none);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  
  /* Animation */
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    border-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized);
}

/* Variants */
.button--primary {
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
}

.button--primary:hover {
  background-color: var(--color-primary-600);
  transform: translateY(-1px);
}

.button--secondary {
  background-color: var(--color-secondary-100);
  color: var(--color-secondary-900);
  border-color: var(--color-secondary-200);
}

.button--outline {
  background-color: transparent;
  color: var(--color-primary-500);
  border-color: var(--color-primary-500);
}

/* Sizes */
.button--sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--text-sm);
}

.button--lg {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--text-lg);
}
```

### Card Component

```css
.card {
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
    transform var(--duration-fast) var(--ease-emphasized);
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.card__header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-neutral-200);
}

.card__content {
  padding: var(--space-lg);
}

.card__footer {
  padding: var(--space-lg);
  border-top: 1px solid var(--color-neutral-200);
  background-color: var(--color-neutral-100);
}

/* Container query responsive behavior */
@container card (min-width: 400px) {
  .card__content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
  }
}

/* Dark theme */
.dark .card {
  background-color: var(--color-neutral-900);
  border-color: var(--color-neutral-800);
}

.dark .card__header,
.dark .card__footer {
  border-color: var(--color-neutral-800);
}

.dark .card__footer {
  background-color: var(--color-neutral-800);
}
```

### Layout Grid

```css
.layout-grid {
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-lg);
  
  /* Default: single column */
  grid-template-columns: 1fr;
  
  /* Container query support */
  container-type: inline-size;
}

/* Responsive grid using container queries */
@container (min-width: 640px) {
  .layout-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-xl);
    padding: var(--space-xl);
  }
}

@container (min-width: 1024px) {
  .layout-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-2xl);
    padding: var(--space-2xl);
  }
}

/* Fallback for browsers without container query support */
@media (min-width: 640px) {
  @supports not (container-type: inline-size) {
    .layout-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: var(--space-xl);
      padding: var(--space-xl);
    }
  }
}
```

## Migration Guide

### From Old System to New Design Tokens

#### 1. Replace Hardcoded Values

```css
/* Before */
.component {
  padding: 16px;
  margin: 24px;
  color: #333;
  background: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* After */
.component {
  padding: var(--space-md);
  margin: var(--space-lg);
  color: var(--color-neutral-700);
  background: var(--color-neutral-100);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
```

#### 2. Update Color References

```css
/* Before */
.primary-button {
  background: #6366f1;
  color: white;
}

/* After */
.primary-button {
  background: var(--color-primary-500);
  color: var(--color-primary-50);
}
```

#### 3. Modernize Typography

```css
/* Before */
h1 {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
}

/* After */
h1 {
  font-size: var(--text-3xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}
```

#### 4. Update Animations

```css
/* Before */
.animated {
  transition: all 0.2s ease-in-out;
}

/* After */
.animated {
  transition:
    background-color var(--duration-fast) var(--ease-standard),
    transform var(--duration-fast) var(--ease-emphasized);
}
```

### Best Practices for Migration

1. **Gradual Migration**: Update components one at a time
2. **Test Thoroughly**: Ensure visual consistency during migration
3. **Use Utility Classes**: Leverage the new utility class system
4. **Update Documentation**: Keep component documentation current
5. **Team Training**: Ensure all team members understand the new system

### Common Pitfalls to Avoid

1. **Mixing Systems**: Don't mix old hardcoded values with new tokens
2. **Skipping Semantic Mapping**: Always use semantic color mappings for themes
3. **Ignoring Container Queries**: Take advantage of modern responsive techniques
4. **Forgetting Accessibility**: Maintain focus styles and contrast ratios
5. **Over-Engineering**: Keep it simple and follow the established patterns

## Conclusion

This design token system provides a solid foundation for scalable, maintainable, and modern CSS architecture. By following these guidelines and patterns, you'll create consistent, accessible, and performant user interfaces that adapt beautifully across devices and themes.

For questions or contributions to this system, please refer to the project's contribution guidelines or reach out to the design system team.