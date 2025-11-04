import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';
import { FocusTrap } from '../focus-trap';
import { SkipLinks } from '../skip-links';
import { AriaLiveRegion } from '../aria-live-region';
import { AriaEnhancedButton } from '../aria-enhanced-button';
import { AriaEnhancedForm } from '../aria-enhanced-form';
import { AriaEnhancedInput } from '../aria-enhanced-input';
import { ScreenReader } from '../screen-reader';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock screen reader API
const mockScreenReader = {
  announce: vi.fn(),
  setLiveRegion: vi.fn(),
};

vi.mock('../screen-reader-api', () => ({
  screenReaderAPI: mockScreenReader,
}));

describe('Accessibility System', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  describe('FocusTrap', () => {
    it('should trap focus within the container', async () => {
      const user = userEvent.setup();
      
      render(
        <div>
          <Button aria-label="Button">Outside Before</Button>
          <FocusTrap active data-testid="focus-trap">
            <Button data-testid="first-button" aria-label="Button">First</Button>
            <Button data-testid="second-button" aria-label="Button">Second</Button>
            <Button data-testid="third-button" aria-label="Button">Third</Button>
          </FocusTrap>
          <Button aria-label="Button">Outside After</Button>
        </div>
      );

      const firstButton = screen.getByTestId('first-button');
      const thirdButton = screen.getByTestId('third-button');

      // Focus should start on first focusable element
      expect(firstButton).toHaveFocus();

      // Tab should cycle within the trap
      await user.tab();
      expect(screen.getByTestId('second-button')).toHaveFocus();

      await user.tab();
      expect(thirdButton).toHaveFocus();

      // Tab from last element should go to first
      await user.tab();
      expect(firstButton).toHaveFocus();

      // Shift+Tab should go backwards
      await user.keyboard('{Shift>}{Tab}{/Shift}');
      expect(thirdButton).toHaveFocus();

    it('should restore focus when deactivated', async () => {
      const user = userEvent.setup();
      
      const TestComponent = () => {
        const [active, setActive] = React.useState(false);
        
        return (
          <div>
            <Button 
              onClick={() => setActive(true)}
              data-testid="trigger"
            >
            </Button>
            <FocusTrap 
              active={active} 
              onEscape={() => setActive(false)}
              restoreFocus
            >
              <Button data-testid="trapped-button" aria-label="Button">Trapped</Button>
            </FocusTrap>
          </div>
        );
      };

      render(<TestComponent />);

      const trigger = screen.getByTestId('trigger');
      trigger.focus();
      
      await user.click(trigger);
      
      // Focus should move to trapped element
      expect(screen.getByTestId('trapped-button')).toHaveFocus();
      
      // Escape should restore focus
      await user.keyboard('{Escape}');
      expect(trigger).toHaveFocus();

    it('should handle empty trap gracefully', () => {
      render(
        <FocusTrap active data-testid="empty-trap">
          <div>No focusable elements</div>
        </FocusTrap>
      );

      const trap = screen.getByTestId('empty-trap');
      expect(trap).toBeInTheDocument();

    it('should be accessible', async () => {
      const { container } = render(
        <FocusTrap active>
          <Button aria-label="Button">Accessible Button</Button>
        </FocusTrap>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('SkipLinks', () => {
    it('should render skip links for main content areas', () => {
      render(
        <SkipLinks
          links={[
            { href: '#main', label: 'Skip to main content' },
            { href: '#nav', label: 'Skip to navigation' },
            { href: '#footer', label: 'Skip to footer' },
          ]}
        />
      );

      expect(screen.getByText('Skip to main content')).toBeInTheDocument();
      expect(screen.getByText('Skip to navigation')).toBeInTheDocument();
      expect(screen.getByText('Skip to footer')).toBeInTheDocument();

    it('should be visually hidden until focused', async () => {
      const user = userEvent.setup();
      
      render(
        <SkipLinks
          links={[
            { href: '#main', label: 'Skip to main content' },
          ]}
        />
      );

      const skipLink = screen.getByText('Skip to main content');
      
      // Should be visually hidden initially
      expect(skipLink).toHaveClass('sr-only');
      
      // Should become visible on focus
      await user.tab();
      expect(skipLink).toHaveFocus();
      expect(skipLink).toHaveClass('not-sr-only');

    it('should navigate to target elements', async () => {
      const user = userEvent.setup();
      
      render(
        <div>
          <SkipLinks
            links={[
              { href: '#main', label: 'Skip to main content' },
            ]}
          />
          <main id="main" tabIndex={-1}>
            <h1>Main Content</h1>
          </main>
        </div>
      );

      const skipLink = screen.getByText('Skip to main content');
      const mainContent = screen.getByRole('main');
      
      await user.click(skipLink);
      
      // Focus should move to main content
      expect(mainContent).toHaveFocus();

    it('should be accessible', async () => {
      const { container } = render(
        <SkipLinks
          links={[
            { href: '#main', label: 'Skip to main content' },
          ]}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('AriaLiveRegion', () => {
    it('should announce messages to screen readers', async () => {
      render(
        <AriaLiveRegion 
          message="Form submitted successfully" 
          politeness="polite"
          data-testid="live-region"
        />
      );

      const liveRegion = screen.getByTestId('live-region');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      expect(liveRegion).toHaveTextContent('Form submitted successfully');

    it('should support different politeness levels', () => {
      const { rerender } = render(
        <AriaLiveRegion 
          message="Polite message" 
          politeness="polite"
          data-testid="live-region"
        />
      );

      let liveRegion = screen.getByTestId('live-region');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');

      rerender(
        <AriaLiveRegion 
          message="Assertive message" 
          politeness="assertive"
          data-testid="live-region"
        />
      );

      liveRegion = screen.getByTestId('live-region');
      expect(liveRegion).toHaveAttribute('aria-live', 'assertive');

    it('should clear messages after timeout', async () => {
      vi.useFakeTimers();
      
      render(
        <AriaLiveRegion 
          message="Temporary message" 
          clearAfter={3000}
          data-testid="live-region"
        />
      );

      const liveRegion = screen.getByTestId('live-region');
      expect(liveRegion).toHaveTextContent('Temporary message');

      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(liveRegion).toHaveTextContent('');

      vi.useRealTimers();

    it('should be accessible', async () => {
      const { container } = render(
        <AriaLiveRegion message="Accessible message" />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('AriaEnhancedButton', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <AriaEnhancedButton
          aria-label="Close dialog"
          aria-describedby="close-help"
          data-testid="aria-button"
        >
          ×
        </AriaEnhancedButton>
      );

      const button = screen.getByTestId('aria-button');
      expect(button).toHaveAttribute('aria-label', 'Close dialog');
      expect(button).toHaveAttribute('aria-describedby', 'close-help');

    it('should handle loading state with ARIA', () => {
      render(
        <AriaEnhancedButton loading data-testid="loading-button">
        </AriaEnhancedButton>
      );

      const button = screen.getByTestId('loading-button');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toBeDisabled();

    it('should support pressed state for toggle buttons', async () => {
      const user = userEvent.setup();
      
      const ToggleButton = () => {
        const [pressed, setPressed] = React.useState(false);
        
        return (
          <AriaEnhancedButton
            pressed={pressed}
            onClick={() => setPressed(!pressed)}
            data-testid="toggle-button"
          >
          </AriaEnhancedButton>
        );
      };

      render(<ToggleButton />);

      const button = screen.getByTestId('toggle-button');
      expect(button).toHaveAttribute('aria-pressed', 'false');

      await user.click(button);
      expect(button).toHaveAttribute('aria-pressed', 'true');

    it('should be accessible', async () => {
      const { container } = render(
        <AriaEnhancedButton>Accessible Button</AriaEnhancedButton>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('AriaEnhancedForm', () => {
    it('should provide form context with ARIA attributes', () => {
      render(
        <AriaEnhancedForm
          aria-label="Contact form"
          data-testid="enhanced-form"
        >
          <AriaEnhancedInput
            label="Name"
            required
            data-testid="name-input"
          />
          <AriaEnhancedButton type="submit">
          </AriaEnhancedButton>
        </AriaEnhancedForm>
      );

      const form = screen.getByTestId('enhanced-form');
      expect(form).toHaveAttribute('aria-label', 'Contact form');
      
      const input = screen.getByTestId('name-input');
      expect(input).toHaveAttribute('required');
      expect(input).toHaveAttribute('aria-required', 'true');

    it('should handle form validation errors', async () => {
      const user = userEvent.setup();
      
      render(
        <AriaEnhancedForm data-testid="validation-form">
          <AriaEnhancedInput
            label="Email"
            type="email"
            required
            error="Please enter a valid email"
            data-testid="email-input"
          />
          <AriaEnhancedButton type="submit">
          </AriaEnhancedButton>
        </AriaEnhancedForm>
      );

      const input = screen.getByTestId('email-input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-describedby');
      
      const errorMessage = screen.getByText('Please enter a valid email');
      expect(errorMessage).toBeInTheDocument();

    it('should be accessible', async () => {
      const { container } = render(
        <AriaEnhancedForm>
          <AriaEnhancedInput label="Name" />
          <AriaEnhancedButton type="submit">Submit</AriaEnhancedButton>
        </AriaEnhancedForm>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('AriaEnhancedInput', () => {
    it('should have proper label association', () => {
      render(
        <AriaEnhancedInput
          label="Full Name"
          data-testid="labeled-input"
        />
      );

      const input = screen.getByTestId('labeled-input');
      const label = screen.getByText('Full Name');
      
      expect(input).toHaveAttribute('aria-labelledby');
      expect(label).toHaveAttribute('id');
      expect(input.getAttribute('aria-labelledby')).toBe(label.getAttribute('id'));

    it('should show validation errors with ARIA', () => {
      render(
        <AriaEnhancedInput
          label="Password"
          error="Password must be at least 8 characters"
          data-testid="error-input"
        />
      );

      const input = screen.getByTestId('error-input');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-describedby');
      
      const errorMessage = screen.getByText('Password must be at least 8 characters');
      expect(errorMessage).toHaveAttribute('role', 'alert');

    it('should support help text', () => {
      render(
        <AriaEnhancedInput
          label="Username"
          helpText="Must be 3-20 characters long"
          data-testid="help-input"
        />
      );

      const input = screen.getByTestId('help-input');
      const helpText = screen.getByText('Must be 3-20 characters long');
      
      expect(input).toHaveAttribute('aria-describedby');
      expect(helpText).toHaveAttribute('id');

    it('should be accessible', async () => {
      const { container } = render(
        <AriaEnhancedInput label="Accessible Input" />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();


  describe('ScreenReader', () => {
    it('should announce messages to screen readers', () => {
      render(
        <ScreenReader
          message="Page loaded successfully"
          priority="polite"
        />
      );

      expect(mockScreenReader.announce).toHaveBeenCalledWith(
        'Page loaded successfully',
        'polite'
      );

    it('should handle different priority levels', () => {
      const { rerender } = render(
        <ScreenReader
          message="Low priority message"
          priority="polite"
        />
      );

      expect(mockScreenReader.announce).toHaveBeenCalledWith(
        'Low priority message',
        'polite'
      );

      rerender(
        <ScreenReader
          message="High priority message"
          priority="assertive"
        />
      );

      expect(mockScreenReader.announce).toHaveBeenCalledWith(
        'High priority message',
        'assertive'
      );

    it('should not announce empty messages', () => {
      render(<ScreenReader message="" />);
      
      expect(mockScreenReader.announce).not.toHaveBeenCalled();


  describe('Keyboard Navigation', () => {
    it('should support arrow key navigation in lists', async () => {
      const user = userEvent.setup();
      
      render(
        <div role="listbox" data-testid="listbox">
          <div role="option" tabIndex={0} data-testid="option-1">Option 1</div>
          <div role="option" tabIndex={-1} data-testid="option-2">Option 2</div>
          <div role="option" tabIndex={-1} data-testid="option-3">Option 3</div>
        </div>
      );

      const option1 = screen.getByTestId('option-1');
      const option2 = screen.getByTestId('option-2');
      const option3 = screen.getByTestId('option-3');

      option1.focus();
      expect(option1).toHaveFocus();

      await user.keyboard('{ArrowDown}');
      expect(option2).toHaveFocus();

      await user.keyboard('{ArrowDown}');
      expect(option3).toHaveFocus();

      await user.keyboard('{ArrowUp}');
      expect(option2).toHaveFocus();

    it('should handle escape key for modal dismissal', async () => {
      const onEscape = vi.fn();
      const user = userEvent.setup();
      
      render(
        <div
          role="dialog"
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              onEscape();
            }
          }}
          tabIndex={0}
          data-testid="modal"
        >
        </div>
      );

      const modal = screen.getByTestId('modal');
      modal.focus();

      await user.keyboard('{Escape}');
      expect(onEscape).toHaveBeenCalledTimes(1);


  describe('High Contrast Mode', () => {
    it('should work in high contrast mode', () => {
      // Mock high contrast media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),

      render(
        <AriaEnhancedButton data-testid="high-contrast-btn">
        </AriaEnhancedButton>
      );

      const button = screen.getByTestId('high-contrast-btn');
      expect(button).toHaveClass('contrast-more:border-2');


  describe('Reduced Motion', () => {
    it('should respect reduced motion preferences', () => {
      // Mock reduced motion media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),

      render(
        <AriaEnhancedButton data-testid="reduced-motion-btn">
        </AriaEnhancedButton>
      );

      const button = screen.getByTestId('reduced-motion-btn');
      expect(button).toHaveClass('motion-reduce:transform-none');


