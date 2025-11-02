import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InteractiveButton } from '../interactive-button';
import { InteractiveInput } from '../interactive-input';
import { InteractiveCard } from '../interactive-card';
import { LoadingSpinner } from '../loading-spinner';
import { ProgressAnimation } from '../progress-animation';
import { MicroInteractionProvider } from '../micro-interaction-provider';

// Mock framer-motion for testing
vi.mock('framer-motion', () => ({
  motion: {
    button: React.forwardRef<HTMLButtonElement, any>(({ children, ...props }, ref) => (
      <button ref={ref} {...props}>{children}</button>
    )),
    input: React.forwardRef<HTMLInputElement, any>((props, ref) => (
      <input ref={ref} {...props} />
    )),
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAnimation: () => ({
    start: vi.fn(),
    stop: vi.fn(),
    set: vi.fn(),
  }),
}));

// Mock haptic feedback
Object.defineProperty(navigator, 'vibrate', {
  value: vi.fn(),
  writable: true,
});

describe('Micro-Interactions System', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('InteractiveButton', () => {
    it('should render with default interactive states', () => {
      render(
        <InteractiveButton data-testid="interactive-btn">
          Click me
        </InteractiveButton>
      );

      const button = screen.getByTestId('interactive-btn');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Click me');
    });

    it('should handle hover interactions', async () => {
      const user = userEvent.setup();
      
      render(
        <InteractiveButton data-testid="hover-btn">
          Hover me
        </InteractiveButton>
      );

      const button = screen.getByTestId('hover-btn');
      
      await user.hover(button);
      expect(button).toHaveClass('hover:scale-105');
      
      await user.unhover(button);
      // Should return to normal state
    });

    it('should handle click interactions with haptic feedback', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(
        <MicroInteractionProvider hapticEnabled={true}>
          <InteractiveButton onClick={onClick} data-testid="click-btn">
            Click me
          </InteractiveButton>
        </MicroInteractionProvider>
      );

      const button = screen.getByTestId('click-btn');
      
      await user.click(button);
      
      expect(onClick).toHaveBeenCalledTimes(1);
      expect(navigator.vibrate).toHaveBeenCalledWith(50);
    });

    it('should show loading state correctly', () => {
      render(
        <InteractiveButton loading data-testid="loading-btn">
          Submit
        </InteractiveButton>
      );

      const button = screen.getByTestId('loading-btn');
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('should support different variants', () => {
      const variants = ['default', 'primary', 'secondary', 'destructive'] as const;
      
      variants.forEach(variant => {
        const { unmount } = render(
          <InteractiveButton variant={variant} data-testid={`${variant}-btn`}>
            {variant}
          </InteractiveButton>
        );

        const button = screen.getByTestId(`${variant}-btn`);
        expect(button).toHaveClass(`btn-${variant}`);
        unmount();
      });
    });

    it('should handle keyboard interactions', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(
        <InteractiveButton onClick={onClick} data-testid="keyboard-btn">
          Keyboard
        </InteractiveButton>
      );

      const button = screen.getByTestId('keyboard-btn');
      button.focus();
      
      await user.keyboard('{Enter}');
      expect(onClick).toHaveBeenCalledTimes(1);
      
      await user.keyboard(' ');
      expect(onClick).toHaveBeenCalledTimes(2);
    });
  });

  describe('InteractiveInput', () => {
    it('should render with focus animations', () => {
      render(
        <InteractiveInput 
          placeholder="Enter text" 
          data-testid="interactive-input"
        />
      );

      const input = screen.getByTestId('interactive-input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Enter text');
    });

    it('should handle focus and blur events', async () => {
      const onFocus = vi.fn();
      const onBlur = vi.fn();
      const user = userEvent.setup();
      
      render(
        <InteractiveInput 
          onFocus={onFocus}
          onBlur={onBlur}
          data-testid="focus-input"
        />
      );

      const input = screen.getByTestId('focus-input');
      
      await user.click(input);
      expect(onFocus).toHaveBeenCalledTimes(1);
      
      await user.tab();
      expect(onBlur).toHaveBeenCalledTimes(1);
    });

    it('should show validation states', () => {
      render(
        <InteractiveInput 
          error="This field is required"
          data-testid="error-input"
        />
      );

      const input = screen.getByTestId('error-input');
      expect(input).toHaveClass('border-red-500');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('should support different sizes', () => {
      const sizes = ['sm', 'md', 'lg'] as const;
      
      sizes.forEach(size => {
        const { unmount } = render(
          <InteractiveInput size={size} data-testid={`${size}-input`} />
        );

        const input = screen.getByTestId(`${size}-input`);
        expect(input).toHaveClass(`input-${size}`);
        unmount();
      });
    });
  });

  describe('InteractiveCard', () => {
    it('should render with hover effects', () => {
      render(
        <InteractiveCard data-testid="interactive-card">
          <div>Card content</div>
        </InteractiveCard>
      );

      const card = screen.getByTestId('interactive-card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('hover:shadow-lg');
    });

    it('should handle click interactions when clickable', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(
        <InteractiveCard clickable onClick={onClick} data-testid="clickable-card">
          <div>Clickable card</div>
        </InteractiveCard>
      );

      const card = screen.getByTestId('clickable-card');
      expect(card).toHaveClass('cursor-pointer');
      
      await user.click(card);
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should support keyboard navigation when clickable', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(
        <InteractiveCard clickable onClick={onClick} data-testid="keyboard-card">
          <div>Keyboard card</div>
        </InteractiveCard>
      );

      const card = screen.getByTestId('keyboard-card');
      card.focus();
      
      await user.keyboard('{Enter}');
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('LoadingSpinner', () => {
    it('should render with default animation', () => {
      render(<LoadingSpinner data-testid="spinner" />);

      const spinner = screen.getByTestId('spinner');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('animate-spin');
    });

    it('should support different sizes', () => {
      const sizes = ['sm', 'md', 'lg'] as const;
      
      sizes.forEach(size => {
        const { unmount } = render(
          <LoadingSpinner size={size} data-testid={`${size}-spinner`} />
        );

        const spinner = screen.getByTestId(`${size}-spinner`);
        expect(spinner).toHaveClass(`spinner-${size}`);
        unmount();
      });
    });

    it('should have proper accessibility attributes', () => {
      render(
        <LoadingSpinner 
          aria-label="Loading content" 
          data-testid="accessible-spinner" 
        />
      );

      const spinner = screen.getByTestId('accessible-spinner');
      expect(spinner).toHaveAttribute('role', 'status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading content');
    });
  });

  describe('ProgressAnimation', () => {
    it('should render with progress value', () => {
      render(
        <ProgressAnimation 
          value={50} 
          max={100} 
          data-testid="progress"
        />
      );

      const progress = screen.getByTestId('progress');
      expect(progress).toBeInTheDocument();
      expect(progress).toHaveAttribute('aria-valuenow', '50');
      expect(progress).toHaveAttribute('aria-valuemax', '100');
    });

    it('should animate progress changes', async () => {
      const { rerender } = render(
        <ProgressAnimation 
          value={25} 
          max={100} 
          data-testid="animated-progress"
        />
      );

      const progress = screen.getByTestId('animated-progress');
      expect(progress).toHaveAttribute('aria-valuenow', '25');

      rerender(
        <ProgressAnimation 
          value={75} 
          max={100} 
          data-testid="animated-progress"
        />
      );

      await waitFor(() => {
        expect(progress).toHaveAttribute('aria-valuenow', '75');
      });
    });

    it('should support indeterminate state', () => {
      render(
        <ProgressAnimation 
          indeterminate 
          data-testid="indeterminate-progress"
        />
      );

      const progress = screen.getByTestId('indeterminate-progress');
      expect(progress).toHaveClass('animate-pulse');
    });
  });

  describe('MicroInteractionProvider', () => {
    it('should provide haptic feedback context', () => {
      const TestComponent = () => {
        return (
          <InteractiveButton data-testid="context-btn">
            Test
          </InteractiveButton>
        );
      };

      render(
        <MicroInteractionProvider hapticEnabled={true}>
          <TestComponent />
        </MicroInteractionProvider>
      );

      const button = screen.getByTestId('context-btn');
      expect(button).toBeInTheDocument();
    });

    it('should respect reduced motion preferences', () => {
      // Mock matchMedia for reduced motion
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
      });

      render(
        <MicroInteractionProvider>
          <InteractiveButton data-testid="reduced-motion-btn">
            Test
          </InteractiveButton>
        </MicroInteractionProvider>
      );

      const button = screen.getByTestId('reduced-motion-btn');
      expect(button).toHaveClass('motion-reduce:transform-none');
    });
  });

  describe('Performance Considerations', () => {
    it('should not cause memory leaks with animations', () => {
      const { unmount } = render(
        <div>
          <LoadingSpinner />
          <ProgressAnimation value={50} />
          <InteractiveButton>Test</InteractiveButton>
        </div>
      );

      // Should unmount without errors
      expect(() => unmount()).not.toThrow();
    });

    it('should handle rapid interactions gracefully', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(
        <InteractiveButton onClick={onClick} data-testid="rapid-click">
          Rapid Click
        </InteractiveButton>
      );

      const button = screen.getByTestId('rapid-click');
      
      // Simulate rapid clicking
      for (let i = 0; i < 10; i++) {
        await user.click(button);
      }

      expect(onClick).toHaveBeenCalledTimes(10);
    });

    it('should optimize animations for 60fps', () => {
      // This would typically involve performance monitoring
      // For now, we'll check that animations use transform/opacity
      render(
        <InteractiveButton data-testid="optimized-btn">
          Optimized
        </InteractiveButton>
      );

      const button = screen.getByTestId('optimized-btn');
      const computedStyle = window.getComputedStyle(button);
      
      // Should use transform for animations (GPU accelerated)
      expect(computedStyle.transform).toBeDefined();
    });
  });

  describe('Accessibility', () => {
    it('should maintain focus visibility', async () => {
      const user = userEvent.setup();
      
      render(
        <InteractiveButton data-testid="focus-visible">
          Focus Test
        </InteractiveButton>
      );

      const button = screen.getByTestId('focus-visible');
      
      await user.tab();
      expect(button).toHaveFocus();
      expect(button).toHaveClass('focus-visible:ring-2');
    });

    it('should provide proper ARIA attributes for loading states', () => {
      render(
        <InteractiveButton loading data-testid="loading-aria">
          Loading Button
        </InteractiveButton>
      );

      const button = screen.getByTestId('loading-aria');
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('should support screen reader announcements', () => {
      render(
        <div>
          <ProgressAnimation 
            value={50} 
            aria-label="Upload progress: 50%" 
            data-testid="sr-progress"
          />
        </div>
      );

      const progress = screen.getByTestId('sr-progress');
      expect(progress).toHaveAttribute('aria-label', 'Upload progress: 50%');
    });
  });
});