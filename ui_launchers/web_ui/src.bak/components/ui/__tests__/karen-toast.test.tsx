/**
 * Test suite for KarenToast component
 */

import * as React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KarenToast, KarenToastProvider, KarenToastViewport } from '../karen-toast';
import type { KarenAlert } from '@/types/karen-alerts';

// Mock the utils
vi.mock('@/lib/utils', () => ({
  cn: (...classes: any[]) => classes.filter(Boolean).join(' '),
}));

describe('KarenToast', () => {
  const mockAlert: KarenAlert = {
    id: 'test-alert-1',
    type: 'info',
    variant: 'karen-info',
    title: 'Test Alert',
    message: 'This is a test message',
    emoji: '💡',
    priority: 'normal',
    timestamp: Date.now(),
    source: 'test',
  };

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <KarenToastProvider>
        <KarenToastViewport />
        {component}
      </KarenToastProvider>
    );
  };

  describe('Basic Rendering', () => {
    test('should render with basic alert data', () => {
      renderWithProvider(<KarenToast alert={mockAlert} />);
      
      expect(screen.getByText('Test Alert')).toBeInTheDocument();
      expect(screen.getByText('This is a test message')).toBeInTheDocument();
      expect(screen.getByText('💡')).toBeInTheDocument();
    });

    test('should render without alert data', () => {
      renderWithProvider(<KarenToast>Fallback content</KarenToast>);
      
      expect(screen.getByText('Fallback content')).toBeInTheDocument();
    });

    test('should apply correct variant classes', () => {
      const { container } = renderWithProvider(
        <KarenToast alert={mockAlert} variant="karen-success" />
      );
      
      const toastElement = container.querySelector('[role="status"]');
      expect(toastElement).toHaveClass('border-green-200');
      expect(toastElement?.className).toContain('bg-green-50');
      expect(toastElement).toHaveClass('text-green-900');
    });
  });

  describe('Alert Variants', () => {
    test.each([
      ['karen-success', 'border-green-200', 'bg-green-50', 'text-green-900'],
      ['karen-info', 'border-blue-200', 'bg-blue-50', 'text-blue-900'],
      ['karen-warning', 'border-amber-200', 'bg-amber-50', 'text-amber-900'],
      ['karen-error', 'border-red-200', 'bg-red-50', 'text-red-900'],
      ['karen-system', 'border-purple-200', 'bg-purple-50', 'text-purple-900'],
    ])('should apply correct styles for %s variant', (variant, borderClass, bgClass, textClass) => {
      const { container } = renderWithProvider(
        <KarenToast alert={mockAlert} variant={variant as any} />
      );
      
      const toastElement = container.querySelector('[role="status"]');
      expect(toastElement).toHaveClass(borderClass);
      expect(toastElement?.className).toContain(bgClass);
      expect(toastElement).toHaveClass(textClass);
    });
  });

  describe('Expandable Content', () => {
    test('should show expandable content when provided', () => {
      const alertWithExpandable: KarenAlert = {
        ...mockAlert,
        expandableContent: <div>Detailed information here</div>,
      };

      renderWithProvider(<KarenToast alert={alertWithExpandable} />);
      
      expect(screen.getByText('Show more')).toBeInTheDocument();
      expect(screen.queryByText('Detailed information here')).not.toBeInTheDocument();
    });

    test('should expand and collapse content when clicked', async () => {
      const alertWithExpandable: KarenAlert = {
        ...mockAlert,
        expandableContent: <div>Detailed information here</div>,
      };

      renderWithProvider(<KarenToast alert={alertWithExpandable} />);
      
      const expandButton = screen.getByText('Show more');
      
      // Expand
      fireEvent.click(expandButton);
      await waitFor(() => {
        expect(screen.getByText('Show less')).toBeInTheDocument();
        expect(screen.getByText('Detailed information here')).toBeInTheDocument();
      });
      
      // Collapse
      fireEvent.click(screen.getByText('Show less'));
      await waitFor(() => {
        expect(screen.getByText('Show more')).toBeInTheDocument();
        expect(screen.queryByText('Detailed information here')).not.toBeInTheDocument();
      });
    });
  });

  describe('Action Buttons', () => {
    test('should render action buttons when provided', () => {
      const alertWithActions: KarenAlert = {
        ...mockAlert,
        actions: [
          {
            label: 'Retry',
            action: vi.fn(),
            variant: 'default',
          },
          {
            label: 'Cancel',
            action: vi.fn(),
            variant: 'outline',
          },
        ],
      };

      renderWithProvider(<KarenToast alert={alertWithActions} />);
      
      expect(screen.getByText('Retry')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    test('should call action function when button is clicked', () => {
      const mockAction = vi.fn();
      const mockOnActionClick = vi.fn();
      
      const alertWithActions: KarenAlert = {
        ...mockAlert,
        actions: [
          {
            label: 'Test Action',
            action: mockAction,
            variant: 'default',
          },
        ],
      };

      renderWithProvider(
        <KarenToast alert={alertWithActions} onActionClick={mockOnActionClick} />
      );
      
      const actionButton = screen.getByText('Test Action');
      fireEvent.click(actionButton);
      
      expect(mockAction).toHaveBeenCalledTimes(1);
      expect(mockOnActionClick).toHaveBeenCalledWith(alertWithActions.actions![0]);
    });

    test('should render action with icon', () => {
      const alertWithIconAction: KarenAlert = {
        ...mockAlert,
        actions: [
          {
            label: 'Refresh',
            action: vi.fn(),
            icon: <span data-testid="refresh-icon">🔄</span>,
          },
        ],
      };

      renderWithProvider(<KarenToast alert={alertWithIconAction} />);
      
      expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  describe('Progress Indicator', () => {
    test('should show progress indicator when showProgress is true and duration is set', () => {
      const alertWithDuration: KarenAlert = {
        ...mockAlert,
        duration: 5000,
      };

      const { container } = renderWithProvider(
        <KarenToast alert={alertWithDuration} showProgress={true} />
      );
      
      // Look for progress indicator element
      const progressElement = container.querySelector('.absolute.bottom-0.left-0.h-1');
      expect(progressElement).toBeInTheDocument();
    });

    test('should not show progress indicator when showProgress is false', () => {
      const alertWithDuration: KarenAlert = {
        ...mockAlert,
        duration: 5000,
      };

      const { container } = renderWithProvider(
        <KarenToast alert={alertWithDuration} showProgress={false} />
      );
      
      const progressElement = container.querySelector('.absolute.bottom-0.left-0.h-1');
      expect(progressElement).not.toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    test('should render close button', () => {
      renderWithProvider(<KarenToast alert={mockAlert} />);
      
      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();
    });

    test('should have proper accessibility attributes', () => {
      renderWithProvider(<KarenToast alert={mockAlert} />);
      
      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toHaveAttribute('toast-close', '');
    });
  });

  describe('Accessibility', () => {
    test('should have proper ARIA attributes', () => {
      renderWithProvider(<KarenToast alert={mockAlert} />);
      
      // Check for emoji accessibility
      const emojiElement = screen.getByRole('img', { name: /alert indicator/i });
      expect(emojiElement).toBeInTheDocument();
    });

    test('should have proper expandable content accessibility', () => {
      const alertWithExpandable: KarenAlert = {
        ...mockAlert,
        expandableContent: <div>Detailed information</div>,
      };

      renderWithProvider(<KarenToast alert={alertWithExpandable} />);
      
      const expandButton = screen.getByRole('button', { name: /show more/i });
      expect(expandButton).toHaveAttribute('aria-expanded', 'false');
      expect(expandButton).toHaveAttribute('aria-controls', 'expandable-content');
    });

    test('should update aria-expanded when content is expanded', async () => {
      const alertWithExpandable: KarenAlert = {
        ...mockAlert,
        expandableContent: <div>Detailed information</div>,
      };

      renderWithProvider(<KarenToast alert={alertWithExpandable} />);
      
      const expandButton = screen.getByRole('button', { name: /show more/i });
      
      fireEvent.click(expandButton);
      
      await waitFor(() => {
        expect(expandButton).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  describe('Viewport Positioning', () => {
    test('should apply correct positioning classes', () => {
      const { container } = render(
        <KarenToastProvider>
          <KarenToastViewport position="bottom-left" />
        </KarenToastProvider>
      );
      
      // Look for the viewport element with a more general selector
      const viewport = container.querySelector('[data-radix-toast-viewport]') || 
                      container.querySelector('.fixed.z-\\[100\\]') ||
                      container.firstElementChild;
      
      expect(viewport).toBeTruthy();
      if (viewport) {
        expect(viewport).toHaveClass('bottom-0', 'left-0', 'flex-col-reverse');
      }
    });

    test.each([
      ['top-left', ['top-0', 'left-0', 'flex-col']],
      ['top-right', ['top-0', 'right-0', 'flex-col']],
      ['bottom-left', ['bottom-0', 'left-0', 'flex-col-reverse']],
      ['bottom-right', ['bottom-0', 'right-0', 'flex-col-reverse']],
    ])('should apply correct classes for %s position', (position, expectedClasses) => {
      const { container } = render(
        <KarenToastProvider>
          <KarenToastViewport position={position as any} />
        </KarenToastProvider>
      );
      
      // Look for the viewport element with a more general selector
      const viewport = container.querySelector('[data-radix-toast-viewport]') || 
                      container.querySelector('.fixed.z-\\[100\\]') ||
                      container.firstElementChild;
      
      expect(viewport).toBeTruthy();
      if (viewport) {
        expectedClasses.forEach(className => {
          expect(viewport).toHaveClass(className);
        });
      }
    });
  });
});