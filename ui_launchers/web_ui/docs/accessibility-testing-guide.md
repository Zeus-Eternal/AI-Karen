# Accessibility Testing Guide

This guide provides comprehensive instructions for testing accessibility in the Karen AI web UI using both automated tools and manual testing with assistive technologies.

## Table of Contents

1. [Overview](#overview)
2. [Automated Testing](#automated-testing)
3. [Manual Testing with Assistive Technologies](#manual-testing-with-assistive-technologies)
4. [Testing Checklist](#testing-checklist)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Continuous Integration](#continuous-integration)

## Overview

Accessibility testing ensures that our application is usable by people with disabilities. We use a multi-layered approach:

- **Automated Testing**: Using axe-core and custom validators
- **Manual Testing**: Testing with actual assistive technologies
- **Code Analysis**: ESLint rules for accessibility
- **User Testing**: Testing with real users who use assistive technologies

## Automated Testing

### Running Accessibility Tests

```bash
# Run all accessibility tests
npm run test:accessibility

# Run specific accessibility test suites
npm test -- --run src/__tests__/accessibility/

# Run automated accessibility suite
npm test -- --run src/__tests__/accessibility/automated-accessibility-suite.test.tsx

# Run accessibility tests with coverage
npm test -- --coverage src/__tests__/accessibility/
```

### Test Configuration

Our accessibility tests use different configurations for different scenarios:

- **Basic**: Essential WCAG 2.1 A rules
- **Standard**: WCAG 2.1 AA compliance (default)
- **Comprehensive**: All rules and best practices
- **Forms**: Form-specific accessibility rules
- **Navigation**: Navigation-specific rules
- **Visual**: Color contrast and visual accessibility

### Writing Accessibility Tests

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { runAccessibilityTest, accessibilityConfigs } from '@/utils/accessibility-testing';

expect.extend(toHaveNoViolations);

it('should be accessible', async () => {
  const { container } = render(<YourComponent />);
  
  // Using axe directly
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  
  // Using our custom test runner
  const report = await runAccessibilityTest(container, accessibilityConfigs.comprehensive);
  expect(report.violations).toHaveLength(0);
});
```

## Manual Testing with Assistive Technologies

### Screen Reader Testing

#### Tools
- **Windows**: NVDA (free), JAWS (commercial), Narrator (built-in)
- **macOS**: VoiceOver (built-in)
- **Linux**: Orca (free)

#### Testing Process

1. **Start the screen reader**
2. **Navigate to the application** (http://localhost:8000)
3. **Test navigation patterns**:
   - Use heading navigation (H key in NVDA/JAWS)
   - Navigate by landmarks (D key for landmarks)
   - Navigate by forms (F key for form controls)
   - Navigate by links (K key for links)
   - Navigate by buttons (B key for buttons)

4. **Test specific scenarios**:
   - Form completion and validation
   - Modal dialog interaction
   - Table navigation
   - Live region announcements
   - Error handling and feedback

#### Screen Reader Commands

**NVDA/JAWS Common Commands**:
- `H/Shift+H`: Next/Previous heading
- `K/Shift+K`: Next/Previous link
- `B/Shift+B`: Next/Previous button
- `F/Shift+F`: Next/Previous form field
- `T/Shift+T`: Next/Previous table
- `D/Shift+D`: Next/Previous landmark
- `Insert+F7`: Elements list
- `Insert+Space`: Toggle focus/browse mode

**VoiceOver Commands**:
- `VO+Right/Left`: Navigate elements
- `VO+U`: Rotor (elements list)
- `VO+Command+H`: Navigate headings
- `VO+Command+L`: Navigate links
- `VO+Command+J`: Navigate form controls

### Keyboard Navigation Testing

#### Testing Process

1. **Disconnect your mouse** (or don't use it)
2. **Navigate using only keyboard**:
   - `Tab`: Move to next focusable element
   - `Shift+Tab`: Move to previous focusable element
   - `Enter`: Activate buttons and links
   - `Space`: Activate buttons and checkboxes
   - `Arrow keys`: Navigate within complex widgets
   - `Escape`: Close modals and menus

3. **Verify**:
   - All interactive elements are reachable
   - Focus order is logical
   - Focus indicators are visible
   - No keyboard traps exist
   - Skip links work properly

#### Keyboard Testing Script

```bash
# Run keyboard testing instructions
node scripts/assistive-technology-test.js keyboard
```

### Voice Control Testing

#### Tools
- **Windows**: Dragon NaturallySpeaking, Windows Speech Recognition
- **macOS**: Voice Control (built-in)
- **Linux**: Simon, Julius

#### Testing Process

1. **Enable voice control software**
2. **Test voice commands**:
   - "Click [button name]"
   - "Click [link text]"
   - "Show numbers" (for numbered navigation)
   - "Type [text]" (for form input)

3. **Verify**:
   - All interactive elements can be activated by voice
   - Button and link text is descriptive
   - Form labels are clear and unique

### Screen Magnification Testing

#### Tools
- **Windows**: Windows Magnifier, ZoomText
- **macOS**: Zoom (built-in)
- **Linux**: Kmag, Virtual Magnifying Glass

#### Testing Process

1. **Enable screen magnification** (200% and 400%)
2. **Test navigation and interaction**:
   - Content reflows properly
   - Text doesn't get cut off
   - Interactive elements remain accessible
   - Focus tracking works with magnification

## Testing Checklist

### Automated Checks ✅

- [ ] All components pass axe-core tests
- [ ] Color contrast meets WCAG AA standards
- [ ] Form controls have proper labels
- [ ] Images have alt text or are marked decorative
- [ ] Headings create logical hierarchy
- [ ] ARIA attributes are used correctly
- [ ] Interactive elements have accessible names
- [ ] Focus indicators are visible

### Manual Testing ✅

#### Keyboard Navigation
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical
- [ ] Focus indicators are clearly visible
- [ ] No keyboard traps exist
- [ ] Skip links work properly
- [ ] Keyboard shortcuts function correctly

#### Screen Reader
- [ ] All content is announced correctly
- [ ] Navigation by headings works
- [ ] Form controls are properly labeled
- [ ] Error messages are announced
- [ ] Live regions announce updates
- [ ] Tables have proper structure
- [ ] Landmarks aid navigation

#### Voice Control
- [ ] Interactive elements can be activated by voice
- [ ] Button and link text is descriptive
- [ ] Form labels are clear and unique
- [ ] No duplicate accessible names

#### Visual/Magnification
- [ ] Content is readable at 200% zoom
- [ ] Content reflows properly when magnified
- [ ] Focus indicators scale appropriately
- [ ] Information isn't conveyed by color alone

## Common Issues and Solutions

### Issue: Missing Form Labels
**Problem**: Form controls without proper labels
**Solution**: 
```jsx
// Bad
<input type="text" placeholder="Name" />

// Good
<label htmlFor="name">Name</label>
<input id="name" type="text" />

// Or with aria-label
<input type="text" aria-label="Name" />
```

### Issue: Poor Color Contrast
**Problem**: Text doesn't meet WCAG contrast requirements
**Solution**: Use our design tokens with tested contrast ratios
```css
/* Use design tokens with proper contrast */
color: var(--color-text-primary);
background-color: var(--color-background-primary);
```

### Issue: Missing Focus Indicators
**Problem**: No visible focus indicators
**Solution**: 
```css
.interactive-element:focus {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
```

### Issue: Inaccessible Custom Components
**Problem**: Custom components without proper ARIA
**Solution**: Use our ARIA-enhanced components
```jsx
import { AriaEnhancedButton } from '@/components/ui/aria-enhanced-button';

<AriaEnhancedButton
  aria-label="Delete item"
  aria-describedby="delete-warning"
>
  Delete
</AriaEnhancedButton>
```

### Issue: Missing Live Region Announcements
**Problem**: Dynamic content changes not announced
**Solution**: Use ARIA live regions
```jsx
<div aria-live="polite" id="status-messages">
  {statusMessage}
</div>

<div aria-live="assertive" id="error-messages">
  {errorMessage}
</div>
```

## Continuous Integration

### Pre-commit Hooks

Accessibility tests run automatically before commits:

```bash
# Install pre-commit hooks
npm run prepare

# Run accessibility linting
npm run lint:accessibility

# Run accessibility tests
npm run test:accessibility
```

### CI/CD Pipeline

Our CI/CD pipeline includes:

1. **ESLint accessibility rules** - Catch issues during development
2. **Automated accessibility tests** - Run on every PR
3. **Visual regression tests** - Ensure focus indicators remain visible
4. **Performance tests** - Ensure accessibility features don't impact performance

### Accessibility Reports

Generate comprehensive accessibility reports:

```bash
# Generate accessibility checklist
node scripts/assistive-technology-test.js checklist

# Run all assistive technology test instructions
node scripts/assistive-technology-test.js all

# Generate test report
node scripts/assistive-technology-test.js automated
```

## Resources

### WCAG Guidelines
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WCAG 2.1 Understanding](https://www.w3.org/WAI/WCAG21/Understanding/)

### Testing Tools
- [axe-core](https://github.com/dequelabs/axe-core)
- [NVDA Screen Reader](https://www.nvaccess.org/download/)
- [Accessibility Insights](https://accessibilityinsights.io/)

### Best Practices
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Inclusive Design Principles](https://inclusivedesignprinciples.org/)
- [WebAIM Resources](https://webaim.org/resources/)

## Getting Help

If you encounter accessibility issues or need help with testing:

1. Check this guide and our component documentation
2. Run automated tests to identify specific issues
3. Use the assistive technology testing script for guidance
4. Consult the WCAG guidelines for detailed requirements
5. Test with actual assistive technology users when possible

Remember: Accessibility is not a one-time task but an ongoing commitment to inclusive design.