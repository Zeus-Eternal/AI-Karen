# Accessibility System

This directory contains a comprehensive accessibility system that provides ARIA attributes, keyboard navigation, focus management, and screen reader support for the Karen AI UI.

## Overview

The accessibility system is built around four core pillars:

1. **ARIA Attributes System** - Comprehensive ARIA attribute management
2. **Keyboard Navigation** - Full keyboard navigation support
3. **Focus Management** - Advanced focus trapping and restoration
4. **Screen Reader Support** - Live announcements and semantic markup

## Components

### ARIA Utilities (`utils/aria.ts`)

Core utilities for creating and managing ARIA attributes:

```typescript
import { createAriaLabel, createInteractiveAria, ARIA_ROLES } from '@/utils/aria';

// Create ARIA label attributes
const labelProps = createAriaLabel('Button label', 'label-id', 'desc-id');

// Create interactive ARIA attributes
const interactiveProps = createInteractiveAria(true, false, undefined, 'page');

// Use ARIA role constants
<div role={ARIA_ROLES.BUTTON} />
```

### Enhanced Components

#### AriaEnhancedButton
Button component with comprehensive ARIA support:

```typescript
import { AriaEnhancedButton } from '@/components/ui/aria-enhanced-button';

<AriaEnhancedButton
  ariaLabel="Save document"
  loading={isLoading}
  loadingText="Saving..."
  successMessage="Document saved"
  pressed={isPressed}
  expanded={isExpanded}
>
  Save
</AriaEnhancedButton>
```

#### AriaEnhancedForm
Form components with built-in accessibility:

```typescript
import { 
  Form, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormControl, 
  FormMessage 
} from '@/components/ui/aria-enhanced-form';

<Form>
  <FormField
    name="email"
    required={true}
    render={({ field }) => (
      <FormItem>
        <FormLabel showRequired>Email</FormLabel>
        <FormControl>
          <AriaEnhancedInput {...field} type="email" />
        </FormControl>
        <FormMessage />
      </FormItem>
    )}
  />
</Form>
```

### Navigation Components

#### AriaNavigation
Accessible navigation with proper landmarks:

```typescript
import { 
  Navigation, 
  NavList, 
  NavItem, 
  NavLink 
} from '@/components/ui/aria-navigation';

<Navigation navType="primary" ariaLabel="Main navigation">
  <NavList orientation="horizontal">
    <NavItem current="page">
      <NavLink href="/" current="page">Home</NavLink>
    </NavItem>
    <NavItem>
      <NavLink href="/about">About</NavLink>
    </NavItem>
  </NavList>
</Navigation>
```

#### Breadcrumb Navigation
Accessible breadcrumb navigation:

```typescript
import { Breadcrumb, BreadcrumbItem } from '@/components/ui/aria-navigation';

<Breadcrumb>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/products">Products</BreadcrumbItem>
  <BreadcrumbItem current>Current Page</BreadcrumbItem>
</Breadcrumb>
```

### Focus Management

#### FocusTrap
Traps focus within modals and dialogs:

```typescript
import { FocusTrap, ModalFocusTrap } from '@/components/ui/focus-trap';

<ModalFocusTrap open={isOpen} autoFocus>
  <div>Modal content</div>
</ModalFocusTrap>
```

#### Focus Management Hook
Advanced focus management:

```typescript
import { useFocusManagement } from '@/hooks/use-focus-management';

const MyComponent = () => {
  const focusManager = useFocusManagement({
    trapFocus: true,
    restoreFocus: true,
    initialFocus: '.first-input',
  });

  return (
    <div {...focusManager.containerProps}>
      <input className="first-input" />
      <Button onClick={focusManager.focusFirst}>Focus First</Button>
    </div>
  );
};
```

### Keyboard Navigation

#### Keyboard Navigation Hook
Comprehensive keyboard navigation:

```typescript
import { useKeyboardNavigation } from '@/hooks/use-keyboard-navigation';

const ListComponent = ({ items }) => {
  const navigation = useKeyboardNavigation(items.length, {
    orientation: 'vertical',
    loop: true,
    onActivate: (index) => selectItem(index),
  });

  return (
    <ul {...navigation.containerProps}>
      {items.map((item, index) => (
        <li key={index} tabIndex={navigation.activeIndex === index ? 0 : -1}>
          {item}
        </li>
      ))}
    </ul>
  );
};
```

#### Enhanced Keyboard Shortcuts
Context-aware keyboard shortcuts:

```typescript
import { useEnhancedKeyboardShortcuts } from '@/hooks/use-enhanced-keyboard-shortcuts';

const MyComponent = () => {
  useEnhancedKeyboardShortcuts([
    {
      key: 's',
      ctrlKey: true,
      handler: handleSave,
      description: 'Save document',
      announce: true,
      announcementText: 'Document saved',
    }
  ], {
    context: 'editor',
    enabled: true,
    announce: (message) => console.log(message),
  });
};
```

### Screen Reader Support

#### Live Announcements
Screen reader announcements:

```typescript
import {
  AriaLiveRegion,
  ScreenReaderAnnouncer
} from '@/components/ui/aria-live-region';
import { useAriaAnnouncements } from '@/components/ui/aria-live-announcements';

const MyComponent = () => {
  const { announce } = useAriaAnnouncements();

  const handleAction = () => {
    announce('Action completed successfully', 'polite');
  };

  return (
    <div>
      <Button onClick={handleAction}>Perform Action</Button>
      <AriaLiveRegion politeness="polite" />
    </div>
  );
};
```

#### Screen Reader Components
Semantic markup for screen readers:

```typescript
import { 
  ScreenReaderOnly,
  HeadingStructure,
  LandmarkRegion,
  StatusMessage 
} from '@/components/ui/screen-reader';

<LandmarkRegion landmark="main" label="Main content">
  <HeadingStructure level={1} visualLevel={2}>
    Page Title
  </HeadingStructure>
  
  <ScreenReaderOnly>
    Additional context for screen readers
  </ScreenReaderOnly>
  
  <StatusMessage 
    message="Form submitted successfully" 
    type="success" 
  />
</LandmarkRegion>
```

### Skip Links

#### Skip Navigation
Keyboard navigation shortcuts:

```typescript
import { SkipLinks, SkipToContent, MainContent } from '@/components/ui/skip-links';

// At the top of your app
<SkipLinks links={[
  { id: 'skip-main', target: 'main-content', label: 'Skip to main content' },
  { id: 'skip-nav', target: 'navigation', label: 'Skip to navigation' },
]} />

// Or use the simple version
<SkipToContent targetId="main-content" />

// Main content area
<MainContent contentId="main-content">
  <h1>Page Content</h1>
</MainContent>
```

## Hooks

### Focus Management
- `useFocusManagement` - Advanced focus management
- `useFocusTrap` - Focus trapping for modals
- `useFocusRestore` - Focus restoration
- `useFocusVisible` - Focus visibility detection

### Keyboard Navigation
- `useKeyboardNavigation` - List/grid navigation
- `useGridNavigation` - 2D grid navigation
- `useRovingTabIndex` - Roving tabindex pattern
- `useTabOrder` - Tab order management

### Keyboard Shortcuts
- `useKeyboardShortcuts` - Basic keyboard shortcuts
- `useEnhancedKeyboardShortcuts` - Advanced shortcuts with context
- `useCommonShortcuts` - Common application shortcuts
- `useNavigationShortcuts` - Navigation-specific shortcuts

### Screen Reader Support
- `useAriaAnnouncements` - Live announcements
- `useScreenReaderAnnouncements` - Specialized announcements

## Testing

### Accessibility Testing
Built-in accessibility testing tools:

```typescript
import { AccessibilityTester, AccessibilityReport } from '@/components/ui/accessibility-testing';

const MyPage = () => {
  const [testResults, setTestResults] = useState(null);

  return (
    <div>
      <AccessibilityTester
        target={document.body}
        onTestComplete={setTestResults}
        autoRun={false}
      />
      
      {testResults && (
        <AccessibilityReport testSuite={testResults} />
      )}
    </div>
  );
};
```

## Best Practices

### 1. Always Use Semantic HTML
Start with semantic HTML elements before adding ARIA:

```typescript
// Good
<Button onClick={handleClick}>Click me</Button>

// Avoid
<div role="button" onClick={handleClick}>Click me</div>
```

### 2. Provide Multiple Ways to Access Content
- Keyboard navigation
- Screen reader support
- Skip links
- Proper heading hierarchy

### 3. Test with Real Assistive Technology
- Use screen readers (NVDA, JAWS, VoiceOver)
- Test keyboard-only navigation
- Verify color contrast ratios
- Test with browser zoom up to 200%

### 4. Progressive Enhancement
Build accessibility in from the start:

```typescript
// Base functionality works without JavaScript
<form action="/submit" method="post">
  <input name="email" required />
  <Button type="submit">Submit</Button>
</form>

// Enhanced with JavaScript
<EnhancedForm onSubmit={handleSubmit}>
  <AriaEnhancedInput 
    name="email" 
    required 
    ariaLabel="Email address"
    invalid={hasError}
    errorId="email-error"
  />
  <AriaEnhancedButton type="submit" loading={isSubmitting}>
    Submit
  </AriaEnhancedButton>
</EnhancedForm>
```

### 5. Consistent Focus Management
Always manage focus appropriately:

```typescript
// When opening a modal
const openModal = () => {
  setIsOpen(true);
  // Focus will be managed by ModalFocusTrap
};

// When closing a modal
const closeModal = () => {
  setIsOpen(false);
  // Focus will be restored automatically
};
```

## Browser Support

This accessibility system supports:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## WCAG Compliance

The system is designed to meet WCAG 2.1 AA standards:
- ✅ Perceivable - Proper contrast, text alternatives
- ✅ Operable - Keyboard accessible, no seizure triggers
- ✅ Understandable - Clear navigation, consistent interface
- ✅ Robust - Compatible with assistive technologies

## Contributing

When adding new components:

1. Include proper ARIA attributes
2. Support keyboard navigation
3. Provide screen reader announcements
4. Write accessibility tests
5. Update documentation

## Resources

- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Guidelines](https://webaim.org/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)