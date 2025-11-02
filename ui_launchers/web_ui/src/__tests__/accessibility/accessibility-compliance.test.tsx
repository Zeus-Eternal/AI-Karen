/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { AccessibilityTestSuite } from '../../lib/accessibility/accessibility-testing';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock components for testing
function MockButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props}>{children}</button>;
}

function MockForm() {
  return (
    <form>
      <label htmlFor="name">Name</label>
      <input id="name" type="text" required />
      
      <label htmlFor="email">Email</label>
      <input id="email" type="email" required />
      
      <button type="submit">Submit</button>
    </form>
  );
}

function MockNavigation() {
  return (
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="#home">Home</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </nav>
  );
}

function MockModal({ isOpen }: { isOpen: boolean }) {
  if (!isOpen) return null;
  
  return (
    <div role="dialog" aria-labelledby="modal-title" aria-modal="true">
      <h2 id="modal-title">Modal Title</h2>
      <p>Modal content</p>
      <button>Close</button>
    </div>
  );
}

function MockLandmarks() {
  return (
    <div>
      <header>
        <h1>Page Title</h1>
      </header>
      <nav aria-label="Main navigation">
        <ul>
          <li><a href="#main">Main Content</a></li>
        </ul>
      </nav>
      <main id="main">
        <h2>Main Content</h2>
        <p>This is the main content area.</p>
      </main>
      <aside>
        <h3>Sidebar</h3>
        <p>Additional information</p>
      </aside>
      <footer>
        <p>Footer content</p>
      </footer>
    </div>
  );
}

describe('Accessibility Compliance Tests', () => {
  describe('Basic WCAG 2.1 AA Compliance', () => {
    it('should pass axe accessibility tests for buttons', async () => {
      const { container } = render(
        <div>
          <MockButton>Click me</MockButton>
          <MockButton disabled>Disabled button</MockButton>
          <MockButton aria-label="Close dialog">×</MockButton>
        </div>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should pass axe accessibility tests for forms', async () => {
      const { container } = render(<MockForm />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should pass axe accessibility tests for navigation', async () => {
      const { container } = render(<MockNavigation />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should pass axe accessibility tests for modals', async () => {
      const { container } = render(<MockModal isOpen={true} />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should pass axe accessibility tests for landmarks', async () => {
      const { container } = render(<MockLandmarks />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('Custom Accessibility Test Suite', () => {
    it('should pass basic accessibility tests', async () => {
      const { container } = render(<MockForm />);
      
      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.basic();

      expect(report.passed).toBe(true);
      expect(report.score).toBeGreaterThanOrEqual(80);
      expect(report.violations).toHaveLength(0);

    it('should pass keyboard accessibility tests', async () => {
      const { container } = render(
        <div>
          <button>Button 1</button>
          <a href="#test">Link</a>
          <input type="text" />
          <select>
            <option>Option 1</option>
          </select>
        </div>
      );

      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.keyboard();

      expect(report.passed).toBe(true);
      expect(report.focusableElements).toBeGreaterThan(0);
      expect(report.unreachableElements).toHaveLength(0);

    it('should pass screen reader tests', async () => {
      const { container } = render(
        <div>
          <img src="test.jpg" alt="Test image" />
          <label htmlFor="test-input">Test Input</label>
          <input id="test-input" type="text" />
          <main>
            <h1>Main Heading</h1>
            <p>Content</p>
          </main>
        </div>
      );

      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.screenReader();

      expect(report.passed).toBe(true);
      expect(report.missingLabels).toHaveLength(0);

    it('should pass ARIA tests', async () => {
      const { container } = render(
        <div>
          <button aria-expanded="false" aria-controls="menu">Menu</button>
          <ul id="menu" aria-hidden="true">
            <li role="menuitem">Item 1</li>
            <li role="menuitem">Item 2</li>
          </ul>
          <div aria-live="polite" aria-atomic="true"></div>
        </div>
      );

      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.aria();

      expect(report.passed).toBe(true);
      expect(report.invalidAttributes).toHaveLength(0);
      expect(report.brokenReferences).toHaveLength(0);


  describe('Error Scenarios', () => {
    it('should detect missing form labels', async () => {
      const { container } = render(
        <form>
          <input type="text" placeholder="Name" />
          <input type="email" placeholder="Email" />
          <button type="submit">Submit</button>
        </form>
      );

      const results = await axe(container);
      expect(results.violations.length).toBeGreaterThan(0);
      
      const labelViolations = results.violations.filter(
        violation => violation.id === 'label'
      );
      expect(labelViolations.length).toBeGreaterThan(0);

    it('should detect missing alt text', async () => {
      const { container } = render(
        <div>
          <img src="test.jpg" />
        </div>
      );

      const results = await axe(container);
      expect(results.violations.length).toBeGreaterThan(0);
      
      const imageAltViolations = results.violations.filter(
        violation => violation.id === 'image-alt'
      );
      expect(imageAltViolations.length).toBeGreaterThan(0);

    it('should detect invalid ARIA attributes', async () => {
      const { container } = render(
        <div>
          <button aria-expanded="invalid">Toggle</button>
          <div aria-labelledby="non-existent-id">Content</div>
        </div>
      );

      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.aria();

      expect(report.passed).toBe(false);
      expect(report.invalidAttributes.length + report.brokenReferences.length).toBeGreaterThan(0);

    it('should detect focus trap issues', async () => {
      const { container } = render(
        <div data-focus-trap="true">
          <p>No focusable elements here</p>
        </div>
      );

      const testSuite = new AccessibilityTestSuite(container);
      const report = await testSuite.keyboard();

      expect(report.trapIssues.length).toBeGreaterThan(0);


  describe('Complex Component Testing', () => {
    function ComplexComponent() {
      return (
        <div>
          <header>
            <h1>Application Title</h1>
            <nav aria-label="Main navigation">
              <ul>
                <li><a href="#main">Main</a></li>
                <li><a href="#settings">Settings</a></li>
              </ul>
            </nav>
          </header>
          
          <main id="main">
            <section>
              <h2>Form Section</h2>
              <form>
                <fieldset>
                  <legend>Personal Information</legend>
                  <label htmlFor="firstName">First Name</label>
                  <input id="firstName" type="text" required aria-describedby="firstName-help" />
                  <div id="firstName-help">Enter your first name</div>
                  
                  <label htmlFor="lastName">Last Name</label>
                  <input id="lastName" type="text" required />
                </fieldset>
                
                <button type="submit">Submit Form</button>
              </form>
            </section>
            
            <section>
              <h2>Interactive Elements</h2>
              <button aria-expanded="false" aria-controls="collapsible">
              </button>
              <div id="collapsible" aria-hidden="true">
                <p>Collapsible content</p>
              </div>
              
              <div role="tablist">
                <button role="tab" aria-selected="true" aria-controls="panel1">Tab 1</button>
                <button role="tab" aria-selected="false" aria-controls="panel2">Tab 2</button>
              </div>
              <div id="panel1" role="tabpanel">Panel 1 content</div>
              <div id="panel2" role="tabpanel" hidden>Panel 2 content</div>
            </section>
          </main>
          
          <aside>
            <h2>Sidebar</h2>
            <div aria-live="polite" aria-atomic="true" className="sr-only"></div>
          </aside>
          
          <footer>
            <p>Footer content</p>
          </footer>
        </div>
      );
    }

    it('should pass comprehensive accessibility tests', async () => {
      const { container } = render(<ComplexComponent />);

      const results = await axe(container, {
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21aa'],
        },

      expect(results).toHaveNoViolations();

    it('should pass custom test suite', async () => {
      const { container } = render(<ComplexComponent />);

      const testSuite = new AccessibilityTestSuite(container);
      const [basic, keyboard, screenReader, aria] = await Promise.all([
        testSuite.basic(),
        testSuite.keyboard(),
        testSuite.screenReader(),
        testSuite.aria(),
      ]);

      expect(basic.passed).toBe(true);
      expect(keyboard.passed).toBe(true);
      expect(screenReader.passed).toBe(true);
      expect(aria.passed).toBe(true);


