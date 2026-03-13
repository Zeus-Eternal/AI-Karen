import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogOverlay,
  AlertDialogPortal,
} from '../alert-dialog';
import { Button } from '../button';
import { render as customRender } from '@/lib/__tests__/test-utils';

describe('AlertDialog', () => {
  const mockOnAction = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Basic AlertDialog', () => {
    it('renders alert dialog with trigger and content', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      const trigger = screen.getByRole('button', { name: /open dialog/i });
      expect(trigger).toBeInTheDocument();
      
      // Dialog should not be visible initially
      expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
      
      // Click to open dialog
      await user.click(trigger);
      
      // Dialog should be visible now
      await waitFor(() => {
        expect(screen.getByText('Confirm Action')).toBeInTheDocument();
        expect(screen.getByText('Are you sure you want to perform this action?')).toBeInTheDocument();
        expect(screen.getByText('Cancel')).toBeInTheDocument();
        expect(screen.getByText('Continue')).toBeInTheDocument();
      });
    });

    it('handles action button click', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={mockOnAction}>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const actionButton = screen.getByRole('button', { name: /continue/i });
      await user.click(actionButton);
      
      expect(mockOnAction).toHaveBeenCalledTimes(1);
    });

    it('handles cancel button click', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={mockOnCancel}>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);
      
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('closes dialog after action button click', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const actionButton = screen.getByRole('button', { name: /continue/i });
      await user.click(actionButton);
      
      // Dialog should close after action
      await waitFor(() => {
        expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
      });
    });

    it('closes dialog after cancel button click', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);
      
      // Dialog should close after cancel
      await waitFor(() => {
        expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
      });
    });
  });

  describe('AlertDialog Components', () => {
    it('renders AlertDialogHeader with correct styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Title</AlertDialogTitle>
              <AlertDialogDescription>Description</AlertDialogDescription>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const header = screen.getByText('Title').parentElement;
      expect(header).toHaveClass('flex flex-col space-y-2');
    });

    it('renders AlertDialogFooter with correct styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const footer = screen.getByText('Cancel').parentElement;
      expect(footer).toHaveClass('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2');
    });

    it('renders AlertDialogTitle with correct styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Dialog Title</AlertDialogTitle>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const title = screen.getByText('Dialog Title');
      expect(title).toHaveClass('text-lg font-semibold');
    });

    it('renders AlertDialogDescription with correct styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogDescription>Dialog Description</AlertDialogDescription>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const description = screen.getByText('Dialog Description');
      expect(description).toHaveClass('text-sm text-muted-foreground');
    });
  });

  describe('AlertDialogAction and AlertDialogCancel', () => {
    it('renders AlertDialogAction with default button styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogFooter>
              <AlertDialogAction>Action</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const actionButton = screen.getByRole('button', { name: /action/i });
      expect(actionButton).toHaveClass('bg-primary text-primary-foreground hover:bg-primary/90');
    });

    it('renders AlertDialogCancel with outline button styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toHaveClass('border border-input bg-background hover:bg-accent hover:text-accent-foreground');
      expect(cancelButton).toHaveClass('mt-2 sm:mt-0');
    });
  });

  describe('AlertDialogOverlay', () => {
    it('renders overlay with correct styling', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Title</AlertDialogTitle>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      // Check for overlay element
      const overlay = document.querySelector('[data-state="open"]');
      expect(overlay).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      const trigger = screen.getByRole('button', { name: /open dialog/i });
      expect(trigger).toHaveAttribute('data-state', 'closed');
      
      await user.click(trigger);
      
      // After opening, trigger should have open state
      expect(trigger).toHaveAttribute('data-state', 'open');
      
      // Check for proper dialog role - AlertDialog uses role="alertdialog"
      await waitFor(() => {
        const dialog = document.querySelector('[role="alertdialog"]');
        expect(dialog).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to perform this action?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={mockOnCancel}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={mockOnAction}>Continue</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      const trigger = screen.getByRole('button', { name: /open dialog/i });
      trigger.focus();
      
      // Open dialog with Enter key
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      });
      
      // Click the action button directly
      const actionButton = screen.getByRole('button', { name: /continue/i });
      await user.click(actionButton);
      
      expect(mockOnAction).toHaveBeenCalledTimes(1);
    });

    it('closes dialog with Escape key', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Open Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Confirm Action</AlertDialogTitle>
            </AlertDialogHeader>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /open dialog/i }));
      
      // Close with Escape key
      await user.keyboard('{Escape}');
      
      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty dialog content', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Empty Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            {/* No content */}
          </AlertDialogContent>
        </AlertDialog>
      );

      const trigger = screen.getByRole('button', { name: /empty dialog/i });
      await user.click(trigger);
      
      // Should not throw error
      expect(trigger).toHaveAttribute('data-state', 'open');
    });

    it('handles custom className', async () => {
      const user = userEvent.setup();
      
      customRender(
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button>Custom Dialog</Button>
          </AlertDialogTrigger>
          <AlertDialogContent className="custom-dialog">
            <AlertDialogHeader className="custom-header">
              <AlertDialogTitle className="custom-title">Custom Title</AlertDialogTitle>
            </AlertDialogHeader>
            <AlertDialogFooter className="custom-footer">
              <AlertDialogCancel className="custom-cancel">Cancel</AlertDialogCancel>
              <AlertDialogAction className="custom-action">Action</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      );

      await user.click(screen.getByRole('button', { name: /custom dialog/i }));
      
      const dialog = document.querySelector('.custom-dialog');
      const header = document.querySelector('.custom-header');
      const title = document.querySelector('.custom-title');
      const footer = document.querySelector('.custom-footer');
      const cancel = document.querySelector('.custom-cancel');
      const action = document.querySelector('.custom-action');
      
      expect(dialog).toBeInTheDocument();
      expect(header).toBeInTheDocument();
      expect(title).toBeInTheDocument();
      expect(footer).toBeInTheDocument();
      expect(cancel).toBeInTheDocument();
      expect(action).toBeInTheDocument();
    });

    it('handles multiple dialogs independently', async () => {
      const user = userEvent.setup();
      
      customRender(
        <div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button>Dialog 1</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Dialog 1</AlertDialogTitle>
              </AlertDialogHeader>
            </AlertDialogContent>
          </AlertDialog>
          
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button>Dialog 2</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Dialog 2</AlertDialogTitle>
              </AlertDialogHeader>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      );

      const trigger1 = screen.getAllByRole('button', { name: /dialog 1/i })[0];
      const trigger2 = screen.getAllByRole('button', { name: /dialog 2/i })[0];
      
      // Open first dialog
      await user.click(trigger1!);
      expect(screen.getByRole('heading', { name: 'Dialog 1' })).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: 'Dialog 2' })).not.toBeInTheDocument();
      
      // Close first dialog
      await user.keyboard('{Escape}');
      
      // Open second dialog
      await user.click(trigger2!);
      expect(screen.getByRole('heading', { name: 'Dialog 2' })).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: 'Dialog 1' })).not.toBeInTheDocument();
    });
  });
});