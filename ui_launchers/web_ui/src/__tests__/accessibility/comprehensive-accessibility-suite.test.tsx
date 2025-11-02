/**
 * Comprehensive Accessibility Test Suite
 * 
 * Tests all interaction patterns and component variations for accessibility compliance.
 * Covers WCAG 2.1 AA standards and common accessibility patterns.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import '@testing-library/jest-dom';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock components for testing
const MockButton = ({ children, disabled, onClick, ...props }: any) => (
  <button disabled={disabled} onClick={onClick} {...props}>
    {children}
  </button>
);

const MockInput = ({ label, error, required, ...props }: any) => (
  <div>
    <label htmlFor={props.id}>
      {label}
      {required && <span aria-label="required"> *</span>}
    </label>
    <input {...props} aria-invalid={error ? 'true' : 'false'} />
    {error && (
      <div role="alert" id={`${props.id}-error`} aria-describedby={props.id}>
        {error}
      </div>
    )}
  </div>
);

const MockModal = ({ isOpen, onClose, title, children }: any) => {
  React.useEffect(() => {
    if (isOpen) {
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement?.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement?.focus();
            }
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      firstElement?.focus();

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="modal-overlay"
    >
      <div className="modal-content">
        <h2 id="modal-title">{title}</h2>
        {children}
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
};

const MockNavigation = ({ items }: any) => (
  <nav aria-label="Main navigation">
    <ul>
      {items.map((item: any, index: number) => (
        <li key={index}>
          <a
            href={item.href}
            aria-current={item.current ? 'page' : undefined}
          >
            {item.label}
          </a>
        </li>
      ))}
    </ul>
  </nav>
);

const MockTable = ({ data, headers }: any) => (
  <table>
    <caption>Data table with {data.length} rows</caption>
    <thead>
      <tr>
        {headers.map((header: string, index: number) => (
          <th key={index} scope="col">
            {header}
          </th>
        ))}
      </tr>
    </thead>
    <tbody>
      {data.map((row: any, rowIndex: number) => (
        <tr key={rowIndex}>
          {headers.map((header: string, cellIndex: number) => (
            <td key={cellIndex}>{row[header]}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);

const MockAccordion = ({ items }: any) => {
  const [expandedItems, setExpandedItems] = React.useState<Set<number>>(new Set());

  const toggleItem = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  return (
    <div>
      {items.map((item: any, index: number) => {
        const isExpanded = expandedItems.has(index);
        return (
          <div key={index}>
            <button
              aria-expanded={isExpanded}
              aria-controls={`panel-${index}`}
              onClick={() => toggleItem(index)}
            >
              {item.title}
            </button>
            <div
              id={`panel-${index}`}
              role="region"
              aria-labelledby={`button-${index}`}
              hidden={!isExpanded}
            >
              {item.content}
            </div>
          </div>
        );
      })}
    </div>
  );
};

describe('Comprehensive Accessibility Test Suite', () => {
  describe('Button Interactions', () => {
    test('should have no accessibility violations', async () => {
      const { container } = render(
        <MockButton onClick={() => {}}>Click me</MockButton>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should be keyboard accessible', async () => {
      const handleClick = jest.fn();
      render(<MockButton onClick={handleClick}>Click me</MockButton>);
      
      const button = screen.getByRole('button');
      button.focus();
      
      // Test Enter key
      fireEvent.keyDown(button, { key: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);
      
      // Test Space key
      fireEvent.keyDown(button, { key: ' ' });
      expect(handleClick).toHaveBeenCalledTimes(2);

    test('should handle disabled state correctly', async () => {
      const handleClick = jest.fn();
      const { container } = render(
        <MockButton disabled onClick={handleClick}>
        </MockButton>
      );
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      
      // Should not be clickable when disabled
      fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should have proper ARIA attributes', () => {
      render(
        <MockButton
          aria-label="Custom button label"
          aria-describedby="button-description"
        >
        </MockButton>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Custom button label');
      expect(button).toHaveAttribute('aria-describedby', 'button-description');


  describe('Form Interactions', () => {
    test('should have no accessibility violations', async () => {
      const { container } = render(
        <MockInput
          id="test-input"
          label="Test Input"
          required
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should associate labels with inputs', () => {
      render(
        <MockInput
          id="email-input"
          label="Email Address"
          type="email"
          required
        />
      );
      
      const input = screen.getByLabelText(/email address/i);
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'email');
      expect(input).toBeRequired();

    test('should handle error states correctly', async () => {
      const { container } = render(
        <MockInput
          id="error-input"
          label="Input with Error"
          error="This field is required"
        />
      );
      
      const input = screen.getByLabelText(/input with error/i);
      expect(input).toHaveAttribute('aria-invalid', 'true');
      
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveTextContent('This field is required');
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should indicate required fields', () => {
      render(
        <MockInput
          id="required-input"
          label="Required Field"
          required
        />
      );
      
      const requiredIndicator = screen.getByLabelText('required');
      expect(requiredIndicator).toBeInTheDocument();
      
      const input = screen.getByLabelText(/required field/i);
      expect(input).toBeRequired();


  describe('Modal Dialog Interactions', () => {
    test('should have no accessibility violations', async () => {
      const { container } = render(
        <MockModal
          isOpen={true}
          onClose={() => {}}
          title="Test Modal"
        >
          <p>Modal content</p>
        </MockModal>
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should trap focus within modal', async () => {
      const handleClose = jest.fn();
      render(
        <div>
          <button>Outside button</button>
          <MockModal
            isOpen={true}
            onClose={handleClose}
            title="Focus Trap Modal"
          >
            <button>First button</button>
            <button>Second button</button>
          </MockModal>
        </div>
      );
      
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
      
      // Focus should be trapped within modal
      const firstButton = screen.getByText('First button');
      const secondButton = screen.getByText('Second button');
      const closeButton = screen.getByText('Close');
      
      // Tab through modal elements
      userEvent.tab();
      expect(secondButton).toHaveFocus();
      
      userEvent.tab();
      expect(closeButton).toHaveFocus();
      
      // Should cycle back to first element
      userEvent.tab();
      expect(firstButton).toHaveFocus();

    test('should close on Escape key', () => {
      const handleClose = jest.fn();
      render(
        <MockModal
          isOpen={true}
          onClose={handleClose}
          title="Escapable Modal"
        >
          <p>Press Escape to close</p>
        </MockModal>
      );
      
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(handleClose).toHaveBeenCalled();

    test('should have proper ARIA attributes', () => {
      render(
        <MockModal
          isOpen={true}
          onClose={() => {}}
          title="ARIA Modal"
        >
          <p>Modal with proper ARIA</p>
        </MockModal>
      );
      
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby', 'modal-title');
      
      const title = screen.getByText('ARIA Modal');
      expect(title).toHaveAttribute('id', 'modal-title');


  describe('Navigation Interactions', () => {
    const navItems = [
      { href: '/', label: 'Home', current: true },
      { href: '/about', label: 'About', current: false },
      { href: '/contact', label: 'Contact', current: false }
    ];

    test('should have no accessibility violations', async () => {
      const { container } = render(<MockNavigation items={navItems} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should have proper navigation structure', () => {
      render(<MockNavigation items={navItems} />);
      
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Main navigation');
      
      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
      
      const listItems = screen.getAllByRole('listitem');
      expect(listItems).toHaveLength(3);

    test('should indicate current page', () => {
      render(<MockNavigation items={navItems} />);
      
      const currentLink = screen.getByRole('link', { name: 'Home' });
      expect(currentLink).toHaveAttribute('aria-current', 'page');
      
      const otherLinks = screen.getAllByRole('link').filter(link => 
        link.getAttribute('aria-current') !== 'page'
      );
      expect(otherLinks).toHaveLength(2);

    test('should be keyboard navigable', () => {
      render(<MockNavigation items={navItems} />);
      
      const links = screen.getAllByRole('link');
      
      // Should be able to tab through all links
      links.forEach(link => {
        link.focus();
        expect(link).toHaveFocus();



  describe('Table Interactions', () => {
    const tableData = [
      { Name: 'John Doe', Age: '30', City: 'New York' },
      { Name: 'Jane Smith', Age: '25', City: 'Los Angeles' }
    ];
    const headers = ['Name', 'Age', 'City'];

    test('should have no accessibility violations', async () => {
      const { container } = render(
        <MockTable data={tableData} headers={headers} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should have proper table structure', () => {
      render(<MockTable data={tableData} headers={headers} />);
      
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
      
      const caption = screen.getByText(/data table with 2 rows/i);
      expect(caption).toBeInTheDocument();
      
      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders).toHaveLength(3);
      
      columnHeaders.forEach(header => {
        expect(header).toHaveAttribute('scope', 'col');


    test('should have accessible table content', () => {
      render(<MockTable data={tableData} headers={headers} />);
      
      // Check that all data is accessible
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();


  describe('Accordion Interactions', () => {
    const accordionItems = [
      { title: 'Section 1', content: 'Content for section 1' },
      { title: 'Section 2', content: 'Content for section 2' }
    ];

    test('should have no accessibility violations', async () => {
      const { container } = render(<MockAccordion items={accordionItems} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should have proper ARIA attributes', () => {
      render(<MockAccordion items={accordionItems} />);
      
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(2);
      
      buttons.forEach((button, index) => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
        expect(button).toHaveAttribute('aria-controls', `panel-${index}`);


    test('should expand and collapse sections', async () => {
      render(<MockAccordion items={accordionItems} />);
      
      const firstButton = screen.getByText('Section 1');
      const firstPanel = screen.getByText('Content for section 1');
      
      // Initially collapsed
      expect(firstButton).toHaveAttribute('aria-expanded', 'false');
      expect(firstPanel).not.toBeVisible();
      
      // Click to expand
      fireEvent.click(firstButton);
      
      await waitFor(() => {
        expect(firstButton).toHaveAttribute('aria-expanded', 'true');
        expect(firstPanel).toBeVisible();

      // Click to collapse
      fireEvent.click(firstButton);
      
      await waitFor(() => {
        expect(firstButton).toHaveAttribute('aria-expanded', 'false');
        expect(firstPanel).not.toBeVisible();


    test('should be keyboard accessible', () => {
      render(<MockAccordion items={accordionItems} />);
      
      const firstButton = screen.getByText('Section 1');
      
      // Should be focusable
      firstButton.focus();
      expect(firstButton).toHaveFocus();
      
      // Should activate with Enter
      fireEvent.keyDown(firstButton, { key: 'Enter' });
      expect(firstButton).toHaveAttribute('aria-expanded', 'true');
      
      // Should activate with Space
      fireEvent.keyDown(firstButton, { key: ' ' });
      expect(firstButton).toHaveAttribute('aria-expanded', 'false');


  describe('Live Regions and Dynamic Content', () => {
    const LiveRegionComponent = () => {
      const [message, setMessage] = React.useState('');
      const [status, setStatus] = React.useState('');
      
      return (
        <div>
          <button onClick={() => setMessage('Content updated!')}>
          </button>
          <button onClick={() => setStatus('Operation completed')}>
          </button>
          <div aria-live="polite" id="live-region">
            {message}
          </div>
          <div role="status" aria-live="polite">
            {status}
          </div>
        </div>
      );
    };

    test('should have no accessibility violations', async () => {
      const { container } = render(<LiveRegionComponent />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();

    test('should announce dynamic content changes', async () => {
      render(<LiveRegionComponent />);
      
      const updateButton = screen.getByText('Update Content');
      const liveRegion = screen.getByText('', { selector: '[aria-live="polite"]' });
      
      fireEvent.click(updateButton);
      
      await waitFor(() => {
        expect(liveRegion).toHaveTextContent('Content updated!');


    test('should have proper live region attributes', () => {
      render(<LiveRegionComponent />);
      
      const liveRegion = document.querySelector('#live-region');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      
      const statusRegion = screen.getByRole('status');
      expect(statusRegion).toHaveAttribute('aria-live', 'polite');


  describe('Color and Contrast', () => {
    test('should not rely on color alone for information', () => {
      const ColorComponent = () => (
        <div>
          <span style={{ color: 'red' }} aria-label="Error">
            ❌ Error message
          </span>
          <span style={{ color: 'green' }} aria-label="Success">
            ✅ Success message
          </span>
        </div>
      );
      
      render(<ColorComponent />);
      
      // Information should be conveyed through text and icons, not just color
      expect(screen.getByLabelText('Error')).toHaveTextContent('❌ Error message');
      expect(screen.getByLabelText('Success')).toHaveTextContent('✅ Success message');


  describe('Focus Management', () => {
    const FocusManagementComponent = () => {
      const [showContent, setShowContent] = React.useState(false);
      const buttonRef = React.useRef<HTMLButtonElement>(null);
      
      const handleToggle = () => {
        setShowContent(!showContent);
        if (showContent) {
          // Return focus to trigger when hiding content
          setTimeout(() => buttonRef.current?.focus(), 0);
        }
      };
      
      return (
        <div>
          <button ref={buttonRef} onClick={handleToggle}>
            {showContent ? 'Hide' : 'Show'} Content
          </button>
          {showContent && (
            <div>
              <h2>Dynamic Content</h2>
              <button>Focusable element</button>
              <button onClick={handleToggle}>Close</button>
            </div>
          )}
        </div>
      );
    };

    test('should manage focus appropriately', async () => {
      render(<FocusManagementComponent />);
      
      const toggleButton = screen.getByText('Show Content');
      
      // Show content
      fireEvent.click(toggleButton);
      
      await waitFor(() => {
        expect(screen.getByText('Dynamic Content')).toBeInTheDocument();

      // Hide content
      const closeButton = screen.getByText('Close');
      fireEvent.click(closeButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Dynamic Content')).not.toBeInTheDocument();

      // Focus should return to original trigger
      expect(toggleButton).toHaveFocus();


  describe('Skip Links', () => {
    const SkipLinksComponent = () => (
      <div>
        <a href="#main-content" className="skip-link">
        </a>
        <nav>
          <a href="/">Home</a>
          <a href="/about">About</a>
        </nav>
        <main id="main-content">
          <h1>Main Content</h1>
          <p>This is the main content area.</p>
        </main>
      </div>
    );

    test('should have functional skip links', () => {
      render(<SkipLinksComponent />);
      
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toHaveAttribute('href', '#main-content');
      
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('id', 'main-content');


  describe('Responsive and Zoom Support', () => {
    test('should handle zoom and responsive behavior', () => {
      const ResponsiveComponent = () => (
        <div style={{ fontSize: '16px', lineHeight: '1.5' }}>
          <p>This text should be readable at 200% zoom</p>
          <button style={{ minHeight: '44px', minWidth: '44px' }}>
          </button>
        </div>
      );
      
      const { container } = render(<ResponsiveComponent />);
      
      // Check minimum touch target size
      const button = screen.getByRole('button');
      const styles = window.getComputedStyle(button);
      
      // These would be actual pixel values in a real browser
      expect(button).toHaveStyle('min-height: 44px');
      expect(button).toHaveStyle('min-width: 44px');


  describe('Error Handling and Recovery', () => {
    const ErrorBoundaryComponent = ({ hasError }: { hasError: boolean }) => {
      if (hasError) {
        return (
          <div role="alert">
            <h2>Something went wrong</h2>
            <p>Please try refreshing the page or contact support.</p>
            <button>Retry</button>
          </div>
        );
      }
      
      return <div>Normal content</div>;
    };

    test('should handle errors accessibly', async () => {
      const { container, rerender } = render(
        <ErrorBoundaryComponent hasError={false} />
      );
      
      expect(screen.getByText('Normal content')).toBeInTheDocument();
      
      // Simulate error state
      rerender(<ErrorBoundaryComponent hasError={true} />);
      
      const errorAlert = screen.getByRole('alert');
      expect(errorAlert).toBeInTheDocument();
      expect(errorAlert).toHaveTextContent('Something went wrong');
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();



// Helper function to test component accessibility
export const testComponentAccessibility = async (component: React.ReactElement) => {
  const { container } = render(component);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  return { container, results };
};

// Helper function to test keyboard navigation
export const testKeyboardNavigation = (
  element: HTMLElement,
  expectedKeys: string[] = ['Enter', ' ']
) => {
  const handleKeyDown = jest.fn();
  element.addEventListener('keydown', handleKeyDown);
  
  expectedKeys.forEach(key => {
    fireEvent.keyDown(element, { key });

  expect(handleKeyDown).toHaveBeenCalledTimes(expectedKeys.length);
  
  element.removeEventListener('keydown', handleKeyDown);
};

// Helper function to test focus management
export const testFocusManagement = (
  triggerElement: HTMLElement,
  targetElement: HTMLElement
) => {
  triggerElement.focus();
  expect(triggerElement).toHaveFocus();
  
  fireEvent.click(triggerElement);
  
  // Allow for async focus changes
  setTimeout(() => {
    expect(targetElement).toHaveFocus();
  }, 0);
};