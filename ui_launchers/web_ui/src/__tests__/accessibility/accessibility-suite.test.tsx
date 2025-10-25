import * as React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';

// Import components to test
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

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Test wrapper for consistent testing environment
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div role="main" id="main-content">
    {children}
  </div>
);

describe('Accessibility Test Suite', () => {
  describe('Layout Components', () => {
    it('GridContainer should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <GridContainer columns={3} gap="1rem" role="grid">
            <div role="gridcell">Item 1</div>
            <div role="gridcell">Item 2</div>
            <div role="gridcell">Item 3</div>
          </GridContainer>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('FlexContainer should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <FlexContainer direction="column" gap="1rem">
            <button>Button 1</button>
            <button>Button 2</button>
            <button>Button 3</button>
          </FlexContainer>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('ResponsiveContainer should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <ResponsiveContainer>
            <h1>Accessible Heading</h1>
            <p>This is accessible content within a responsive container.</p>
          </ResponsiveContainer>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Compound Components', () => {
    it('Card component should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <Card.Root>
            <Card.Header>
              <Card.Title>Accessible Card Title</Card.Title>
              <Card.Description>
                This card has proper heading hierarchy and semantic structure.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <p>Card content with proper semantic markup.</p>
            </Card.Content>
            <Card.Footer>
              <Card.Actions>
                <button>Primary Action</button>
                <button>Secondary Action</button>
              </Card.Actions>
            </Card.Footer>
          </Card.Root>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('Modal component should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <Modal.Root open={true}>
            <Modal.Content>
              <Modal.Header>
                <Modal.Title>Accessible Modal</Modal.Title>
                <Modal.Description>
                  This modal has proper ARIA attributes and focus management.
                </Modal.Description>
              </Modal.Header>
              <Modal.Body>
                <p>Modal content with proper semantic structure.</p>
              </Modal.Body>
              <Modal.Actions>
                <button>Cancel</button>
                <button>Confirm</button>
              </Modal.Actions>
            </Modal.Content>
          </Modal.Root>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('Form component should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <Form.Root>
            <Form.Field>
              <Form.Label htmlFor="name">Full Name</Form.Label>
              <input 
                id="name"
                type="text" 
                required
                aria-describedby="name-help"
              />
              <Form.Help id="name-help">
                Enter your full legal name
              </Form.Help>
            </Form.Field>
            
            <Form.Field>
              <Form.Label htmlFor="email">Email Address</Form.Label>
              <input 
                id="email"
                type="email" 
                required
                aria-describedby="email-error"
              />
              <Form.Error id="email-error">
                Please enter a valid email address
              </Form.Error>
            </Form.Field>
            
            <Form.Actions>
              <button type="submit">Submit Form</button>
            </Form.Actions>
          </Form.Root>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Interactive Components', () => {
    it('InteractiveButton should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <InteractiveButton
            aria-label="Save document"
            aria-describedby="save-help"
          >
            Save
          </InteractiveButton>
          <div id="save-help">
            Save the current document to your account
          </div>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('InteractiveInput should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <label htmlFor="search-input">Search</label>
          <InteractiveInput
            id="search-input"
            type="search"
            placeholder="Enter search terms"
            aria-describedby="search-help"
          />
          <div id="search-help">
            Search through all available content
          </div>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ARIA Enhanced Components', () => {
    it('AriaEnhancedButton should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <AriaEnhancedButton
            aria-label="Delete item"
            aria-describedby="delete-warning"
          >
            Delete
          </AriaEnhancedButton>
          <div id="delete-warning" role="alert">
            This action cannot be undone
          </div>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('AriaEnhancedForm should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <AriaEnhancedForm aria-label="Contact form">
            <AriaEnhancedInput
              label="Your Name"
              required
              helpText="Enter your full name as it appears on official documents"
            />
            <AriaEnhancedInput
              label="Email Address"
              type="email"
              required
              error="Please enter a valid email address"
            />
            <button type="submit">Submit Contact Form</button>
          </AriaEnhancedForm>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('AriaEnhancedInput should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <AriaEnhancedInput
            label="Password"
            type="password"
            required
            helpText="Password must be at least 8 characters long"
            error="Password is too short"
          />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Focus Management Components', () => {
    it('FocusTrap should be accessible', async () => {
      const { container } = render(
        <TestWrapper>
          <FocusTrap active>
            <div role="dialog" aria-labelledby="dialog-title">
              <h2 id="dialog-title">Dialog Title</h2>
              <p>Dialog content with focus trapped inside.</p>
              <button>First Button</button>
              <button>Second Button</button>
              <button>Close Dialog</button>
            </div>
          </FocusTrap>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('SkipLinks should be accessible', async () => {
      const { container } = render(
        <div>
          <SkipLinks
            links={[
              { href: '#main-content', label: 'Skip to main content' },
              { href: '#navigation', label: 'Skip to navigation' },
              { href: '#footer', label: 'Skip to footer' },
            ]}
          />
          <TestWrapper>
            <nav id="navigation">
              <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
              </ul>
            </nav>
            <main id="main-content">
              <h1>Main Content</h1>
              <p>This is the main content area.</p>
            </main>
            <footer id="footer">
              <p>Footer content</p>
            </footer>
          </TestWrapper>
        </div>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Complex Accessibility Scenarios', () => {
    it('should handle complex form with validation', async () => {
      const { container } = render(
        <TestWrapper>
          <form aria-label="User registration form">
            <fieldset>
              <legend>Personal Information</legend>
              
              <div>
                <label htmlFor="first-name">First Name *</label>
                <input 
                  id="first-name"
                  type="text" 
                  required
                  aria-describedby="first-name-error"
                  aria-invalid="true"
                />
                <div id="first-name-error" role="alert">
                  First name is required
                </div>
              </div>
              
              <div>
                <label htmlFor="last-name">Last Name *</label>
                <input 
                  id="last-name"
                  type="text" 
                  required
                  aria-describedby="last-name-help"
                />
                <div id="last-name-help">
                  Enter your family name or surname
                </div>
              </div>
            </fieldset>
            
            <fieldset>
              <legend>Account Settings</legend>
              
              <div>
                <label htmlFor="username">Username *</label>
                <input 
                  id="username"
                  type="text" 
                  required
                  aria-describedby="username-help username-error"
                />
                <div id="username-help">
                  Username must be 3-20 characters long
                </div>
                <div id="username-error" role="alert">
                  Username is already taken
                </div>
              </div>
              
              <div>
                <label htmlFor="password">Password *</label>
                <input 
                  id="password"
                  type="password" 
                  required
                  aria-describedby="password-requirements"
                />
                <div id="password-requirements">
                  <p>Password must contain:</p>
                  <ul>
                    <li>At least 8 characters</li>
                    <li>One uppercase letter</li>
                    <li>One lowercase letter</li>
                    <li>One number</li>
                  </ul>
                </div>
              </div>
            </fieldset>
            
            <div>
              <input 
                type="checkbox" 
                id="terms"
                required
                aria-describedby="terms-error"
              />
              <label htmlFor="terms">
                I agree to the terms and conditions *
              </label>
              <div id="terms-error" role="alert">
                You must agree to the terms to continue
              </div>
            </div>
            
            <button type="submit">Create Account</button>
          </form>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should handle data table with proper headers', async () => {
      const { container } = render(
        <TestWrapper>
          <table>
            <caption>User Account Information</caption>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Email</th>
                <th scope="col">Role</th>
                <th scope="col">Status</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">John Doe</th>
                <td>john@example.com</td>
                <td>Administrator</td>
                <td>
                  <span aria-label="Active user">✓ Active</span>
                </td>
                <td>
                  <button aria-label="Edit John Doe">Edit</button>
                  <button aria-label="Delete John Doe">Delete</button>
                </td>
              </tr>
              <tr>
                <th scope="row">Jane Smith</th>
                <td>jane@example.com</td>
                <td>User</td>
                <td>
                  <span aria-label="Inactive user">✗ Inactive</span>
                </td>
                <td>
                  <button aria-label="Edit Jane Smith">Edit</button>
                  <button aria-label="Delete Jane Smith">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should handle navigation with proper landmarks', async () => {
      const { container } = render(
        <div>
          <header>
            <nav aria-label="Main navigation">
              <ul>
                <li><a href="/" aria-current="page">Home</a></li>
                <li><a href="/products">Products</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
              </ul>
            </nav>
          </header>
          
          <main>
            <h1>Welcome to Our Website</h1>
            
            <nav aria-label="Breadcrumb">
              <ol>
                <li><a href="/">Home</a></li>
                <li><a href="/products">Products</a></li>
                <li aria-current="page">Product Details</li>
              </ol>
            </nav>
            
            <article>
              <h2>Product Information</h2>
              <p>Detailed product description goes here.</p>
            </article>
            
            <aside aria-label="Related products">
              <h3>You might also like</h3>
              <ul>
                <li><a href="/product1">Related Product 1</a></li>
                <li><a href="/product2">Related Product 2</a></li>
              </ul>
            </aside>
          </main>
          
          <footer>
            <nav aria-label="Footer navigation">
              <ul>
                <li><a href="/privacy">Privacy Policy</a></li>
                <li><a href="/terms">Terms of Service</a></li>
                <li><a href="/support">Support</a></li>
              </ul>
            </nav>
          </footer>
        </div>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Color Contrast and Visual Accessibility', () => {
    it('should have sufficient color contrast for text', async () => {
      const { container } = render(
        <TestWrapper>
          <div style={{ backgroundColor: '#ffffff', color: '#000000', padding: '1rem' }}>
            <h1>High Contrast Heading</h1>
            <p>This text has sufficient contrast ratio for accessibility.</p>
          </div>
          
          <div style={{ backgroundColor: '#000000', color: '#ffffff', padding: '1rem' }}>
            <h2>Inverted High Contrast</h2>
            <p>This inverted text also has sufficient contrast.</p>
          </div>
          
          <div style={{ backgroundColor: '#0066cc', color: '#ffffff', padding: '1rem' }}>
            <h3>Blue Background</h3>
            <p>White text on blue background with good contrast.</p>
          </div>
        </TestWrapper>
      );

      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });
      expect(results).toHaveNoViolations();
    });

    it('should handle focus indicators properly', async () => {
      const { container } = render(
        <TestWrapper>
          <style>
            {`
              .focus-test:focus {
                outline: 2px solid #0066cc;
                outline-offset: 2px;
              }
            `}
          </style>
          
          <div>
            <button className="focus-test">Focusable Button</button>
            <a href="#" className="focus-test">Focusable Link</a>
            <input type="text" className="focus-test" placeholder="Focusable Input" />
            <select className="focus-test">
              <option>Focusable Select</option>
            </select>
          </div>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Screen Reader Compatibility', () => {
    it('should provide proper screen reader content', async () => {
      const { container } = render(
        <TestWrapper>
          <div>
            <h1>Page Title</h1>
            
            <div aria-live="polite" id="status-updates">
              <p>Status updates will appear here</p>
            </div>
            
            <div aria-live="assertive" id="error-messages">
              <p>Critical error messages will appear here</p>
            </div>
            
            <button 
              aria-expanded="false"
              aria-controls="collapsible-content"
              aria-describedby="expand-help"
            >
              Expand Section
            </button>
            <div id="expand-help" className="sr-only">
              Click to show additional content
            </div>
            
            <div id="collapsible-content" hidden>
              <p>This content is initially hidden</p>
            </div>
            
            <img 
              src="/placeholder.jpg" 
              alt="Descriptive alt text for the image content"
            />
            
            <div role="img" aria-label="Chart showing sales data for Q4 2023">
              {/* Chart content would go here */}
              <div>Chart visualization</div>
            </div>
          </div>
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});