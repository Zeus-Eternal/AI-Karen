# Visual Regression Testing Guide

This document outlines the comprehensive visual regression testing setup for the modern UI system, including Storybook stories, Chromatic integration, and accessibility testing.

## Overview

Our visual regression testing strategy includes:

- **Storybook Stories**: Component documentation and visual testing
- **Chromatic**: Automated visual regression testing
- **Accessibility Testing**: Automated a11y testing with axe-core
- **Cross-browser Testing**: Testing across different browsers and viewports
- **Interaction Testing**: Testing component interactions and states

## Setup

### Prerequisites

1. **Node.js** (v18 or higher)
2. **Storybook** (configured)
3. **Chromatic Account** (for visual regression testing)

### Installation

The required dependencies are already included in the project:

```json
{
  "@storybook/addon-a11y": "^7.0.0",
  "@storybook/addon-interactions": "^7.0.0",
  "@storybook/addon-viewport": "^7.0.0",
  "@storybook/test-runner": "^0.13.0",
  "axe-playwright": "^1.2.3",
  "chromatic": "^7.0.0"
}
```

### Environment Variables

Create a `.env.local` file with your Chromatic project token:

```bash
CHROMATIC_PROJECT_TOKEN=your_chromatic_token_here
```

## Running Tests

### Local Development

Start Storybook for development:

```bash
npm run storybook
```

### Visual Regression Tests

Run the complete visual regression test suite:

```bash
npm run visual-test
```

Run specific test types:

```bash
# Skip Chromatic tests
npm run visual-test -- --skip-chromatic

# Skip accessibility tests
npm run visual-test -- --skip-a11y

# Verbose logging
npm run visual-test -- --verbose
```

### Individual Test Commands

```bash
# Build Storybook
npm run build-storybook

# Run Storybook test runner
npm run test-storybook

# Run Chromatic
npx chromatic --project-token=YOUR_TOKEN

# Run accessibility tests
npm run test-storybook -- --coverage
```

## Story Structure

### Design Tokens Stories

Located in `src/ArtifactSystem/ArtifactSystem.stories.tsx`:

- **Colors**: Complete color palette showcase
- **Spacing**: Spacing scale visualization
- **Typography**: Font sizes and weights
- **Shadows**: Shadow system examples
- **BorderRadius**: Border radius scale
- **Animations**: Animation tokens and easing curves
- **Overview**: Complete design system overview

### Layout Components Stories

Located in `src/components/ui/layout/layout.stories.tsx`:

- **GridLayouts**: CSS Grid examples and patterns
- **FlexLayouts**: Flexbox layouts and alignment
- **ResponsiveContainers**: Container query examples
- **ComplexLayouts**: Real-world layout combinations
- **Overview**: Layout system overview

### Compound Components Stories

Located in `src/components/ui/compound/compound.stories.tsx`:

- **Cards**: Card component variations
- **Modals**: Modal dialog examples
- **Forms**: Form component patterns
- **Overview**: Compound components overview

## Visual Testing Strategy

### Viewport Testing

Tests are run across multiple viewports:

- **Mobile**: 375px width
- **Tablet**: 768px width
- **Desktop**: 1024px width
- **Large Desktop**: 1440px width

### Theme Testing

Components are tested in both light and dark themes:

```javascript
export const MyComponent = {
  parameters: {
    themes: {
      themeOverride: 'dark'
    }
  }
};
```

### Interaction Testing

Interactive components include interaction tests:

```javascript
export const InteractiveExample = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const button = canvas.getByRole('button');
    
    await userEvent.click(button);
    await expect(canvas.getByText('Clicked')).toBeInTheDocument();
  }
};
```

## Accessibility Testing

### Automated Testing

All stories are automatically tested for accessibility violations using axe-core:

- Color contrast ratios
- Keyboard navigation
- ARIA attributes
- Focus management
- Screen reader compatibility

### Manual Testing

For comprehensive accessibility testing:

1. **Keyboard Navigation**: Tab through all interactive elements
2. **Screen Reader**: Test with NVDA, JAWS, or VoiceOver
3. **High Contrast**: Test in high contrast mode
4. **Zoom**: Test at 200% zoom level

### Accessibility Configuration

Accessibility rules are configured in `.storybook/preview.ts`:

```javascript
a11y: {
  config: {
    rules: [
      {
        id: 'color-contrast',
        enabled: true,
      },
      {
        id: 'focus-order-semantics',
        enabled: true,
      },
      {
        id: 'keyboard-navigation',
        enabled: true,
      },
    ],
  },
}
```

## Chromatic Integration

### Setup

1. Create a Chromatic account at [chromatic.com](https://chromatic.com)
2. Connect your repository
3. Get your project token
4. Add the token to your environment variables

### Configuration

Chromatic is configured in `chromatic.config.json`:

```json
{
  "projectToken": "PROJECT_TOKEN_PLACEHOLDER",
  "viewports": [375, 768, 1024, 1440],
  "modes": {
    "light": { "theme": "light" },
    "dark": { "theme": "dark" }
  },
  "diffThreshold": 0.2,
  "delay": 300
}
```

### CI/CD Integration

Add Chromatic to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run Chromatic
  uses: chromaui/action@v1
  with:
    projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
    buildScriptName: build-storybook
```

## Best Practices

### Story Writing

1. **Comprehensive Coverage**: Include all component variants and states
2. **Realistic Data**: Use realistic content and data
3. **Edge Cases**: Test with long text, empty states, error states
4. **Interactions**: Include hover, focus, and click states

### Visual Testing

1. **Consistent Naming**: Use descriptive story names
2. **Stable Screenshots**: Avoid animations in screenshots
3. **Cross-browser**: Test in multiple browsers
4. **Responsive**: Test all breakpoints

### Accessibility

1. **Semantic HTML**: Use proper HTML elements
2. **ARIA Labels**: Provide descriptive labels
3. **Keyboard Support**: Ensure keyboard accessibility
4. **Color Contrast**: Meet WCAG guidelines

## Troubleshooting

### Common Issues

#### Storybook Build Fails

```bash
# Clear cache and reinstall
rm -rf node_modules .next storybook-static
npm install
npm run build-storybook
```

#### Chromatic Differences

1. Check for animations or dynamic content
2. Verify consistent data across environments
3. Review viewport and theme settings
4. Check for timing issues with `delay` setting

#### Accessibility Violations

1. Review axe-core reports in Storybook
2. Test with actual screen readers
3. Verify keyboard navigation
4. Check color contrast ratios

### Debug Mode

Enable debug mode for detailed logging:

```bash
VERBOSE=true npm run visual-test
```

## Reporting

### Test Reports

Visual regression test reports are generated in `visual-regression-reports/`:

- `visual-regression-report.json`: Detailed test results
- `screenshots/`: Component screenshots
- `coverage/`: Accessibility coverage reports

### Metrics Tracked

- Total number of stories
- Screenshot count
- Accessibility violations
- Test execution time
- Browser compatibility

## Integration with Development Workflow

### Pre-commit Hooks

Add visual regression tests to pre-commit hooks:

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run visual-test -- --skip-chromatic"
    }
  }
}
```

### Pull Request Checks

Integrate with PR workflows:

1. **Storybook Build**: Ensure stories build successfully
2. **Accessibility**: Check for a11y violations
3. **Visual Changes**: Review Chromatic changes
4. **Cross-browser**: Verify browser compatibility

## Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep Storybook and testing tools updated
2. **Review Stories**: Ensure stories remain relevant and comprehensive
3. **Accessibility Audit**: Regular manual accessibility testing
4. **Performance**: Monitor test execution time and optimize

### Story Maintenance

1. **Add New Components**: Create stories for new components
2. **Update Existing**: Keep stories in sync with component changes
3. **Remove Deprecated**: Clean up stories for removed components
4. **Documentation**: Keep story documentation updated

## Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Chromatic Documentation](https://www.chromatic.com/docs)
- [axe-core Rules](https://dequeuniversity.com/rules/axe)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Testing Library](https://testing-library.com/docs/)

## Support

For questions or issues with visual regression testing:

1. Check this documentation
2. Review Storybook and Chromatic docs
3. Check existing GitHub issues
4. Create a new issue with detailed reproduction steps