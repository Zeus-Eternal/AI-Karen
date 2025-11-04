/**
 * Automated Accessibility Test Suite
 * 
 * Comprehensive automated accessibility testing using axe-core and custom validators.
 * This suite tests all components for WCAG compliance and accessibility best practices.
 */

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';

  runAccessibilityTest, 
  testKeyboardAccessibility, 
  testScreenReaderAccessibility,
  validateColorContrast,
  validateAriaAttributes,
  accessibilityTestConfigs
import { } from '@/utils/accessibility-testing';

// Import all components to test
import { Card } from '@/components/ui/compound/card';
import { Modal } from '@/components/ui/compound/modal';
import { Form } from '@/components/ui/compound/form';
import { GridContainer } from '@/components/ui/layout/grid-container';
import { FlexContainer } from '@/components/ui/layout/flex-container';
import { ResponsiveContainer } from '@/components/ui/layout/responsive-container';
import { InteractiveButton } from '@/components/ui/micro-interactions/interactive-button';
import { InteractiveInput } from '@/components/ui/micro-interactions/interactive-input';
import { AriaEnhancedButton } from '@/components/ui/aria-enhanced-button';
import { AriaEnhancedForm } from '@/components/ui/aria-enhanced-form';
import { AriaEnhancedInput } from '@/components/ui/aria-enhanced-input';
import { FocusTrap } from '@/components/ui/focus-trap';
import { SkipLinks } from '@/components/ui/skip-links';
import { PolymorphicText } from '@/components/ui/polymorphic/text';
import { PolymorphicButton } from '@/components/ui/polymorphic/button';
import { PolymorphicContainer } from '@/components/ui/polymorphic/container';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Test wrapper for consistent testing environment
const AccessibilityTestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div role="main" id="main-content" lang="en">
    <h1>Test Page</h1>
    {children}
  </div>
);

describe('Automated Accessibility Test Suite', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();

  afterEach(() => {
    // Clean up any DOM modifications
    document.body.innerHTML = '';

  describe('Core Accessibility Testing', () => {
    it('should run comprehensive accessibility tests on all components', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          {/* Layout Components */}
          <GridContainer columns={2} gap="1rem" role="grid">
            <div role="gridcell">Grid Item 1</div>
            <div role="gridcell">Grid Item 2</div>
          </GridContainer>

          <FlexContainer direction="row" gap="1rem">
            <Button>Flex Item 1</Button>
            <Button>Flex Item 2</Button>
          </FlexContainer>

          <ResponsiveContainer>
            <h2>Responsive Content</h2>
            <p>This content adapts to different screen sizes.</p>
          </ResponsiveContainer>

          {/* Compound Components */}
          <Card.Root>
            <Card.Header>
              <Card.Title>Accessible Card</Card.Title>
              <Card.Description>Card with proper semantic structure</Card.Description>
            </Card.Header>
            <Card.Content>
              <p>Card content with proper markup.</p>
            </Card.Content>
            <Card.Footer>
              <Card.Actions>
                <Button>Primary</Button>
                <Button>Secondary</Button>
              </Card.Actions>
            </Card.Footer>
          </Card.Root>

          {/* Form Components */}
          <Form.Root>
            <Form.Field>
              <Form.Label htmlFor="test-input">Test Input</Form.Label>
              <input id="test-input" type="text" aria-describedby="test-help" />
              <Form.Help id="test-help">Help text for the input</Form.Help>
            </Form.Field>
            <Form.Actions>
              <Button type="submit">Submit</Button>
            </Form.Actions>
          </Form.Root>

          {/* Interactive Components */}
          <InteractiveButton aria-label="Interactive button">
          </InteractiveButton>

          <label htmlFor="interactive-input">Interactive Input</label>
          <InteractiveInput
            id="interactive-input"
            type="text"
            placeholder="Type here"
          />

          {/* ARIA Enhanced Components */}
          <AriaEnhancedButton
            aria-describedby="button-help"
            onClick={() => {}}
          >
          </AriaEnhancedButton>
          <div id="button-help">Additional button information</div>

          <AriaEnhancedForm aria-label="Enhanced form">
            <AriaEnhancedInput
              label="Enhanced Input"
              helpText="This input has enhanced ARIA support"
            />
          </AriaEnhancedForm>

          {/* Polymorphic Components */}
          <PolymorphicText as="h3">Polymorphic Heading</PolymorphicText>
          <PolymorphicButton as="button" onClick={() => {}}>
          </PolymorphicButton>
          <PolymorphicContainer as="section">
            <p>Polymorphic container content</p>
          </PolymorphicContainer>

          {/* Focus Management */}
          <SkipLinks
            links={[
              { href: '#main-content', label: 'Skip to main content' },
              { href: '#navigation', label: 'Skip to navigation' },
            ]}
          />
        </AccessibilityTestWrapper>
      );

      // Run comprehensive accessibility test
      const report = await runAccessibilityTest(container, accessibilityTestConfigs.comprehensive);
      
      // Expect no violations
      expect(report.violations).toHaveLength(0);
      expect(report.summary.violations).toBe(0);

      // Also run axe directly for additional validation
      const axeResults = await axe(container);
      expect(axeResults).toHaveNoViolations();

    it('should validate keyboard accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <Button>Button 1</Button>
          <a href="#test">Link 1</a>
          <input type="text" placeholder="Input 1" />
          <select>
            <option>Option 1</option>
          </select>
          <textarea placeholder="Textarea 1"></textarea>
          <div tabIndex={0} role="button">Custom Button</div>
        </AccessibilityTestWrapper>
      );

      const keyboardTest = testKeyboardAccessibility(container);
      
      expect(keyboardTest.allReachable).toBe(true);
      expect(keyboardTest.unreachableElements).toHaveLength(0);
      expect(keyboardTest.focusOrderIssues).toHaveLength(0);

    it('should validate screen reader accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <form>
            <label htmlFor="name">Name</label>
            <input id="name" type="text" />
            
            <label htmlFor="email">Email</label>
            <input id="email" type="email" aria-describedby="email-help" />
            <div id="email-help">Enter a valid email address</div>
          </form>
          
          <img src="/test.jpg" alt="Test image description" />
          
          <main>
            <h1>Main Content</h1>
            <p>Content with proper landmark structure</p>
          </main>
        </AccessibilityTestWrapper>
      );

      const screenReaderTest = testScreenReaderAccessibility(container);
      
      expect(screenReaderTest.hasLabels).toBe(true);
      expect(screenReaderTest.missingLabels).toHaveLength(0);
      expect(screenReaderTest.landmarkIssues).toHaveLength(0);


  describe('Color Contrast Validation', () => {
    it('should validate color contrast ratios', () => {
      // Test high contrast combinations
      const highContrast = validateColorContrast('#000000', '#ffffff');
      expect(highContrast.passes.aa).toBe(true);
      expect(highContrast.passes.aaa).toBe(true);
      expect(highContrast.ratio).toBeGreaterThan(7);

      // Test medium contrast combinations
      const mediumContrast = validateColorContrast('#666666', '#ffffff');
      expect(mediumContrast.passes.aa).toBe(true);
      expect(mediumContrast.ratio).toBeGreaterThan(4.5);

      // Test brand colors
      const brandContrast = validateColorContrast('#0066cc', '#ffffff');
      expect(brandContrast.passes.aa).toBe(true);

    it('should test color contrast in rendered components', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <div 
            style={{ 
              backgroundColor: '#ffffff', 
              color: '#000000', 
              padding: '1rem' 
            }}
          >
            <h2>High Contrast Text</h2>
            <p>This text should have excellent contrast.</p>
          </div>
          
          <div 
            style={{ 
              backgroundColor: '#0066cc', 
              color: '#ffffff', 
              padding: '1rem' 
            }}
          >
            <h3>Brand Color Text</h3>
            <p>This text uses brand colors with good contrast.</p>
          </div>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }

      expect(results).toHaveNoViolations();


  describe('ARIA Validation', () => {
    it('should validate ARIA attributes', () => {
      const validElement = document.createElement('button');
      validElement.setAttribute('aria-expanded', 'false');
      validElement.setAttribute('aria-controls', 'menu');
      validElement.setAttribute('aria-label', 'Toggle menu');

      const issues = validateAriaAttributes(validElement);
      expect(issues).toHaveLength(0);

    it('should detect ARIA attribute issues', () => {
      const invalidElement = document.createElement('div');
      invalidElement.setAttribute('aria-expanded', 'invalid');
      invalidElement.setAttribute('aria-level', '0');
      invalidElement.setAttribute('aria-describedby', '');

      const issues = validateAriaAttributes(invalidElement);
      expect(issues.length).toBeGreaterThan(0);
      expect(issues).toContain('aria-expanded must be "true" or "false"');
      expect(issues).toContain('aria-level must be a positive integer');
      expect(issues).toContain('aria-describedby has empty value');


  describe('Form Accessibility', () => {
    it('should test complex form accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <form aria-label="Registration form">
            <fieldset>
              <legend>Personal Information</legend>
              
              <div>
                <label htmlFor="firstName">First Name *</label>
                <input 
                  id="firstName"
                  type="text" 
                  required
                  aria-describedby="firstName-help"
                />
                <div id="firstName-help">Enter your legal first name</div>
              </div>
              
              <div>
                <label htmlFor="email">Email Address *</label>
                <input 
                  id="email"
                  type="email" 
                  required
                  aria-describedby="email-error"
                  aria-invalid="true"
                />
                <div id="email-error" role="alert">
                </div>
              </div>
            </fieldset>
            
            <fieldset>
              <legend>Preferences</legend>
              
              <div role="group" aria-labelledby="notification-legend">
                <div id="notification-legend">Notification Preferences</div>
                <label>
                  <input type="checkbox" name="notifications" value="email" />
                </label>
                <label>
                  <input type="checkbox" name="notifications" value="sms" />
                </label>
              </div>
            </fieldset>
            
            <Button type="submit">Create Account</Button>
          </form>
        </AccessibilityTestWrapper>
      );

      const results = await runAccessibilityTest(container, accessibilityTestConfigs.forms);
      expect(results.violations).toHaveLength(0);

      const axeResults = await axe(container);
      expect(axeResults).toHaveNoViolations();


  describe('Navigation Accessibility', () => {
    it('should test navigation accessibility', async () => {
      const { container } = render(
        <div>
          <SkipLinks
            links={[
              { href: '#main', label: 'Skip to main content' },
              { href: '#nav', label: 'Skip to navigation' },
            ]}
          />
          
          <header>
            <nav id="nav" aria-label="Main navigation">
              <ul>
                <li><a href="/" aria-current="page">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
              </ul>
            </nav>
          </header>
          
          <main id="main">
            <h1>Page Title</h1>
            
            <nav aria-label="Breadcrumb">
              <ol>
                <li><a href="/">Home</a></li>
                <li><a href="/section">Section</a></li>
                <li aria-current="page">Current Page</li>
              </ol>
            </nav>
            
            <article>
              <h2>Article Title</h2>
              <p>Article content goes here.</p>
            </article>
          </main>
          
          <footer>
            <nav aria-label="Footer navigation">
              <ul>
                <li><a href="/privacy">Privacy</a></li>
                <li><a href="/terms">Terms</a></li>
              </ul>
            </nav>
          </footer>
        </div>
      );

      const results = await runAccessibilityTest(container, accessibilityTestConfigs.navigation);
      expect(results.violations).toHaveLength(0);

      const axeResults = await axe(container);
      expect(axeResults).toHaveNoViolations();


  describe('Modal and Dialog Accessibility', () => {
    it('should test modal accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <Modal.Root open={true}>
            <Modal.Content>
              <Modal.Header>
                <Modal.Title>Accessible Modal</Modal.Title>
                <Modal.Description>
                  This modal demonstrates proper accessibility implementation.
                </Modal.Description>
              </Modal.Header>
              <Modal.Body>
                <p>Modal content with proper focus management.</p>
                <Button>Action Button</Button>
              </Modal.Body>
              <Modal.Actions>
                <Button>Cancel</Button>
                <Button>Confirm</Button>
              </Modal.Actions>
            </Modal.Content>
          </Modal.Root>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should test focus trap accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <FocusTrap active>
            <div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
              <h2 id="dialog-title">Dialog Title</h2>
              <p>Content inside focus trap.</p>
              <Button>First Button</Button>
              <Button>Second Button</Button>
              <Button>Close</Button>
            </div>
          </FocusTrap>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('Data Table Accessibility', () => {
    it('should test data table accessibility', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <table>
            <caption>User Account Information</caption>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Email</th>
                <th scope="col">Role</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">John Doe</th>
                <td>john@example.com</td>
                <td>Admin</td>
                <td>
                  <Button aria-label="Edit John Doe">Edit</Button>
                  <Button aria-label="Delete John Doe">Delete</Button>
                </td>
              </tr>
              <tr>
                <th scope="row">Jane Smith</th>
                <td>jane@example.com</td>
                <td>User</td>
                <td>
                  <Button aria-label="Edit Jane Smith">Edit</Button>
                  <Button aria-label="Delete Jane Smith">Delete</Button>
                </td>
              </tr>
            </tbody>
          </table>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('Live Region Accessibility', () => {
    it('should test live regions and announcements', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <div aria-live="polite" id="status-messages">
            <p>Status updates appear here</p>
          </div>
          
          <div aria-live="assertive" id="error-messages">
            <p>Critical errors appear here</p>
          </div>
          
          <div aria-live="off" id="background-updates">
            <p>Background updates that don't need announcement</p>
          </div>
          
          <Button 
            aria-expanded="false"
            aria-controls="collapsible-content"
            aria-describedby="expand-help"
          >
          </Button>
          <div id="expand-help">Click to reveal additional information</div>
          
          <div id="collapsible-content" hidden>
            <p>This content can be expanded</p>
          </div>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('Keyboard Navigation Testing', () => {
    it('should test keyboard navigation patterns', async () => {
      const { container } = render(
        <AccessibilityTestWrapper>
          <div role="tablist" aria-label="Settings tabs">
            <Button 
              role="tab" 
              aria-selected="true" 
              aria-controls="general-panel"
              id="general-tab"
            >
            </Button>
            <Button 
              role="tab" 
              aria-selected="false" 
              aria-controls="privacy-panel"
              id="privacy-tab"
            >
            </Button>
          </div>
          
          <div 
            role="tabpanel" 
            id="general-panel" 
            aria-labelledby="general-tab"
          >
            <h3>General Settings</h3>
            <Button>Save General Settings</Button>
          </div>
          
          <div 
            role="tabpanel" 
            id="privacy-panel" 
            aria-labelledby="privacy-tab"
            hidden
          >
            <h3>Privacy Settings</h3>
            <Button>Save Privacy Settings</Button>
          </div>
        </AccessibilityTestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Test keyboard navigation
      const firstTab = screen.getByRole('tab', { name: 'General' });
      const secondTab = screen.getByRole('tab', { name: 'Privacy' });

      // Test tab key navigation
      firstTab.focus();
      expect(document.activeElement).toBe(firstTab);

      await user.keyboard('{Tab}');
      expect(document.activeElement).toBe(secondTab);


  describe('Performance and Accessibility', () => {
    it('should complete accessibility tests within reasonable time', async () => {
      const startTime = performance.now();
      
      const { container } = render(
        <AccessibilityTestWrapper>
          {/* Large component tree for performance testing */}
          {Array.from({ length: 50 }, (_, i) => (
            <div key={i}>
              <h3>Section {i + 1}</h3>
              <Button>Button {i + 1}</Button>
              <input type="text" aria-label={`Input ${i + 1}`} />
            </div>
          ))}
        </AccessibilityTestWrapper>
      );

      const report = await runAccessibilityTest(container);
      const endTime = performance.now();
      
      // Test should complete within 5 seconds
      expect(endTime - startTime).toBeLessThan(5000);
      expect(report.violations).toHaveLength(0);


