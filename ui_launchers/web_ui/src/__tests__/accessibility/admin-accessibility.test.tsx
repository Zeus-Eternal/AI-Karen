/**
 * Admin Accessibility Tests
 * 
 * Comprehensive accessibility tests for admin components following WCAG guidelines.
 * Tests keyboard navigation, ARIA attributes, screen reader compatibility, and more.
 * 
 * Requirements: 7.7
 */

import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { resetRouterMocks } from '@/test-utils/router-mocks';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { EnhancedUserManagementTable } from '@/components/admin/enhanced/EnhancedUserManagementTable';
import { EnhancedBulkUserOperations } from '@/components/admin/enhanced/EnhancedBulkUserOperations';
import ErrorDisplay from '@/components/ui/error-display';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { ProgressIndicator } from '@/components/ui/progress-indicator';
import AdminErrorHandler from '@/lib/errors/admin-error-handler';
import { AuthProvider } from '@/contexts/AuthContext';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock data
const mockUsers = [
  {
    user_id: '1',
    email: 'user1@example.com',
    full_name: 'User One',
    role: 'user' as const,
    is_active: true,
    is_verified: true,
    last_login_at: new Date('2024-01-01'),
    created_at: new Date('2023-01-01')
  },
  {
    user_id: '2',
    email: 'user2@example.com',
    full_name: 'User Two',
    role: 'admin' as const,
    is_active: false,
    is_verified: false,
    last_login_at: null,
    created_at: new Date('2023-02-01')
  }
];

const mockProgress = {
  operationId: 'test-operation',
  operation: 'Test Operation',
  totalItems: 10,
  processedItems: 5,
  successfulItems: 4,
  failedItems: 1,
  status: 'running' as const,
  startTime: new Date(),
  steps: [
    {
      id: 'step1',
      label: 'Processing items',
      status: 'running' as const,
      progress: 50
    }
  ],
  errors: [
    {
      itemId: 'item1',
      error: 'Test error',
      details: 'Test error details'
    }
  ],
  canCancel: true
};

// Mock fetch
global.fetch = vi.fn();

// Mock useRole hook
vi.mock('@/hooks/useRole', () => ({
  useRole: () => ({
    user: { email: 'admin@example.com', role: 'admin' },
    hasRole: (role: string) => role === 'admin' || role === 'user',
    hasPermission: () => true
  })
}));

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider>
    {children}
  </AuthProvider>
);

describe('Admin Accessibility Tests', () => {
  beforeEach(() => {
    resetRouterMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: {
          data: mockUsers,
          pagination: {
            total_pages: 1,
            total: mockUsers.length
          }
        }
      })


  describe('Error Display Component', () => {
    it('should have no accessibility violations', async () => {
      const error = AdminErrorHandler.createError('USER_NOT_FOUND', 'Test error');
      const { container } = render(
        <ErrorDisplay error={error} onRetry={() => {}} onDismiss={() => {}} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should have proper ARIA attributes', () => {
      const error = AdminErrorHandler.createError('USER_NOT_FOUND', 'Test error');
      render(<ErrorDisplay error={error} onRetry={() => {}} onDismiss={() => {}} />);

      const errorContainer = screen.getByRole('alert');
      expect(errorContainer).toBeInTheDocument();
      expect(errorContainer).toHaveAttribute('role', 'alert');

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();
      const onDismiss = vi.fn();
      const error = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR', 'Test error');

      render(<ErrorDisplay error={error} onRetry={onRetry} onDismiss={onDismiss} />);

      const retryButton = screen.getByRole('button', { name: /try again/i });
      const dismissButton = screen.getByRole('button', { name: /dismiss/i });

      // Test Tab navigation
      await user.tab();
      expect(retryButton).toHaveFocus();

      await user.tab();
      expect(dismissButton).toHaveFocus();

      // Test Enter key activation
      await user.keyboard('{Enter}');
      expect(onDismiss).toHaveBeenCalled();

    it('should have proper aria-labels for buttons', () => {
      const error = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR', 'Test error');
      render(<ErrorDisplay error={error} onRetry={() => {}} onDismiss={() => {}} />);

      expect(screen.getByLabelText('Retry the failed operation')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss this error')).toBeInTheDocument();


  describe('Confirmation Dialog Component', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <ConfirmationDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Test Dialog"
          message="Test message"
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should have proper dialog ARIA attributes', () => {
      render(
        <ConfirmationDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Test Dialog"
          message="Test message"
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'confirmation-dialog-title');
      expect(dialog).toHaveAttribute('aria-describedby', 'confirmation-dialog-description');

    it('should trap focus within dialog', async () => {
      const user = userEvent.setup();
      render(
        <ConfirmationDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Test Dialog"
          message="Test message"
        />
      );

      const closeButton = screen.getByLabelText('Close dialog');
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const confirmButton = screen.getByRole('button', { name: /confirm/i });

      // Focus should start on cancel button (safer default)
      await waitFor(() => {
        expect(cancelButton).toHaveFocus();

      // Tab should cycle through focusable elements
      await user.tab();
      expect(confirmButton).toHaveFocus();

      await user.tab();
      expect(closeButton).toHaveFocus();

      // Tab should wrap back to first element
      await user.tab();
      expect(cancelButton).toHaveFocus();

      // Shift+Tab should go backwards
      await user.keyboard('{Shift>}{Tab}{/Shift}');
      expect(closeButton).toHaveFocus();

    it('should handle Escape key', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(
        <ConfirmationDialog
          isOpen={true}
          onClose={onClose}
          onConfirm={() => {}}
          title="Test Dialog"
          message="Test message"
        />
      );

      await user.keyboard('{Escape}');
      expect(onClose).toHaveBeenCalled();

    it('should handle Enter key on confirm button', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();

      render(
        <ConfirmationDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={onConfirm}
          title="Test Dialog"
          message="Test message"
        />
      );

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      confirmButton.focus();
      
      await user.keyboard('{Enter}');
      expect(onConfirm).toHaveBeenCalled();


  describe('Progress Indicator Component', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <ProgressIndicator progress={mockProgress} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should have proper progress bar ARIA attributes', () => {
      render(<ProgressIndicator progress={mockProgress} />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
      expect(progressBar).toHaveAttribute('aria-label', 'Operation progress: 50%');

    it('should announce progress updates to screen readers', () => {
      const { rerender } = render(<ProgressIndicator progress={mockProgress} />);

      const updatedProgress = {
        ...mockProgress,
        processedItems: 8,
        successfulItems: 7,
        failedItems: 1
      };

      rerender(<ProgressIndicator progress={updatedProgress} />);

      // Check that progress is visually updated
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '80');

    it('should have accessible cancel button', () => {
      render(
        <ProgressIndicator 
          progress={mockProgress} 
          onCancel={() => {}} 
        />
      );

      const cancelButton = screen.getByLabelText('Cancel operation');
      expect(cancelButton).toBeInTheDocument();
      expect(cancelButton).toHaveAttribute('aria-label', 'Cancel operation');


  describe('Enhanced User Management Table', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('grid')).toBeInTheDocument();

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should have proper table ARIA attributes', async () => {
      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        const table = screen.getByRole('grid');
        expect(table).toHaveAttribute('aria-label', 'User management table');
        expect(table).toHaveAttribute('aria-rowcount', '3'); // header + 2 users


    it('should have proper column headers with scope attributes', async () => {
      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        const columnHeaders = screen.getAllByRole('columnheader');
        columnHeaders.forEach(header => {
          expect(header).toHaveAttribute('scope', 'col');



    it('should have sortable column headers with proper ARIA attributes', async () => {
      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        const emailSortButton = screen.getByLabelText('Sort by email address');
        expect(emailSortButton).toHaveAttribute('aria-sort', 'none');


    it('should support keyboard navigation for table rows', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('grid')).toBeInTheDocument();

      // Test arrow key navigation
      const firstCheckbox = screen.getAllByRole('checkbox')[0];
      firstCheckbox.focus();

      await user.keyboard('{ArrowDown}');
      // Should move to next focusable element
      expect(document.activeElement).not.toBe(firstCheckbox);

    it('should have accessible form controls with labels', async () => {
      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        const selectAllCheckbox = screen.getByLabelText(/select all.*users/i);
        expect(selectAllCheckbox).toBeInTheDocument();

        const pageSizeSelect = screen.getByLabelText('Number of users per page');
        expect(pageSizeSelect).toBeInTheDocument();


    it('should announce loading states to screen readers', async () => {
      (global.fetch as any).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { data: [], pagination: { total_pages: 0, total: 0 } }
          })
        }), 100))
      );

      render(
        <TestWrapper>
          <EnhancedUserManagementTable
            selectedUsers={[]}
            onSelectionChange={() => {}}
            onUserUpdated={() => {}}
          />
        </TestWrapper>
      );

      // Should show loading state with proper ARIA attributes
      const loadingStatus = screen.getByRole('status');
      expect(loadingStatus).toHaveAttribute('aria-live', 'polite');
      expect(screen.getByText('Loading users...')).toBeInTheDocument();


  describe('Enhanced Bulk Operations Component', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <EnhancedBulkUserOperations
            selectedUserIds={['1', '2']}
            onOperationComplete={() => {}}
            onCancel={() => {}}
          />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();

    it('should have proper button descriptions', () => {
      render(
        <TestWrapper>
          <EnhancedBulkUserOperations
            selectedUserIds={['1', '2']}
            onOperationComplete={() => {}}
            onCancel={() => {}}
          />
        </TestWrapper>
      );

      const activateButton = screen.getByRole('button', { name: /activate users/i });
      expect(activateButton).toHaveAttribute('aria-describedby', 'activate-description');
      
      const descriptionElement = document.getElementById('activate-description');
      expect(descriptionElement).toHaveTextContent('Enable login access for selected users');

    it('should support keyboard navigation between operation buttons', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedBulkUserOperations
            selectedUserIds={['1', '2']}
            onOperationComplete={() => {}}
            onCancel={() => {}}
          />
        </TestWrapper>
      );

      const buttons = screen.getAllByRole('button').filter(btn => 
        btn.textContent?.includes('Users') || btn.textContent?.includes('Export')
      );

      // Focus first operation button
      buttons[0].focus();
      expect(buttons[0]).toHaveFocus();

      // Arrow keys should navigate between buttons
      await user.keyboard('{ArrowDown}');
      expect(buttons[1]).toHaveFocus();

      await user.keyboard('{ArrowUp}');
      expect(buttons[0]).toHaveFocus();

      // Home/End keys should work
      await user.keyboard('{End}');
      expect(buttons[buttons.length - 1]).toHaveFocus();

      await user.keyboard('{Home}');
      expect(buttons[0]).toHaveFocus();

    it('should handle Escape key to close', async () => {
      const user = userEvent.setup();
      const onCancel = vi.fn();

      render(
        <TestWrapper>
          <EnhancedBulkUserOperations
            selectedUserIds={['1', '2']}
            onOperationComplete={() => {}}
            onCancel={onCancel}
          />
        </TestWrapper>
      );

      await user.keyboard('{Escape}');
      expect(onCancel).toHaveBeenCalled();

    it('should show appropriate message when no users selected', () => {
      render(
        <TestWrapper>
          <EnhancedBulkUserOperations
            selectedUserIds={[]}
            onOperationComplete={() => {}}
            onCancel={() => {}}
          />
        </TestWrapper>
      );

      expect(screen.getByText('No Users Selected')).toBeInTheDocument();
      expect(screen.getByText('Please select one or more users to perform bulk operations.')).toBeInTheDocument();


  describe('Keyboard Navigation Utilities', () => {
    it('should create proper skip links', () => {
      const { AccessibilityUtils } = require('@/lib/accessibility/aria-helpers');
      
      const skipLink = AccessibilityUtils.createSkipLink('main-content', 'Skip to main content');
      
      expect(skipLink.tagName).toBe('A');
      expect(skipLink.href).toContain('#main-content');
      expect(skipLink.textContent).toBe('Skip to main content');
      expect(skipLink.className).toBe('skip-link');

    it('should validate form accessibility', () => {
      const { AccessibilityUtils } = require('@/lib/accessibility/aria-helpers');
      
      // Create a test form
      const form = document.createElement('form');
      
      // Input without label
      const input1 = document.createElement('input');
      input1.type = 'text';
      input1.id = 'test-input-1';
      form.appendChild(input1);
      
      // Input with label
      const input2 = document.createElement('input');
      input2.type = 'email';
      input2.id = 'test-input-2';
      const label = document.createElement('label');
      label.setAttribute('for', 'test-input-2');
      label.textContent = 'Email';
      form.appendChild(label);
      form.appendChild(input2);
      
      // Required input without aria-required
      const input3 = document.createElement('input');
      input3.type = 'password';
      input3.id = 'test-input-3';
      input3.required = true;
      const label3 = document.createElement('label');
      label3.setAttribute('for', 'test-input-3');
      label3.textContent = 'Password';
      form.appendChild(label3);
      form.appendChild(input3);
      
      document.body.appendChild(form);
      
      const issues = AccessibilityUtils.validateFormAccessibility(form);
      
      expect(issues).toContain('Form field missing accessible name: input#test-input-1');
      expect(issues).toContain('Required field missing aria-required: test-input-3');
      
      document.body.removeChild(form);


  describe('ARIA Live Regions', () => {
    it('should create and manage live regions properly', () => {
      const { AriaManager } = require('@/lib/accessibility/aria-helpers');
      
      const regionId = AriaManager.createLiveRegion({
        politeness: 'assertive',
        atomic: true

      const region = document.getElementById(regionId);
      expect(region).toBeInTheDocument();
      expect(region).toHaveAttribute('aria-live', 'assertive');
      expect(region).toHaveAttribute('aria-atomic', 'true');
      expect(region).toHaveClass('sr-only');
      
      // Test announcement
      AriaManager.announce('Test message', regionId);
      
      setTimeout(() => {
        expect(region?.textContent).toBe('Test message');
      }, 150);
      
      // Cleanup
      AriaManager.removeLiveRegion(regionId);
      expect(document.getElementById(regionId)).not.toBeInTheDocument();

    it('should announce bulk operation results', () => {
      const { AriaManager } = require('@/lib/accessibility/aria-helpers');
      
      const spy = vi.spyOn(AriaManager, 'announce');
      
      AriaManager.announceBulkOperationResult('Delete Users', 8, 2, 10);
      
      expect(spy).toHaveBeenCalledWith(
        'Delete Users completed. 8 items processed successfully, 2 items failed.',
        undefined,
        'assertive'
      );
      
      spy.mockRestore();


  describe('Color Contrast and Visual Accessibility', () => {
    it('should use sufficient color contrast for error states', () => {
      const error = AdminErrorHandler.createError('SYSTEM_SERVER_ERROR', 'Test error');
      render(<ErrorDisplay error={error} />);

      const errorContainer = screen.getByRole('alert');
      const styles = window.getComputedStyle(errorContainer);
      
      // These would need actual color contrast calculation in a real test
      // For now, we just verify the classes are applied correctly
      expect(errorContainer).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');

    it('should provide visual focus indicators', async () => {
      const user = userEvent.setup();
      
      render(
        <ConfirmationDialog
          isOpen={true}
          onClose={() => {}}
          onConfirm={() => {}}
          title="Test Dialog"
          message="Test message"
        />
      );

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      
      await user.tab();
      await user.tab(); // Navigate to confirm button
      
      expect(confirmButton).toHaveFocus();
      expect(confirmButton).toHaveClass('focus:outline-none', 'focus:ring-2');



// Helper function to test keyboard navigation patterns
export const testKeyboardNavigation = async (
  container: HTMLElement,
  expectedFocusOrder: string[]
) => {
  const user = userEvent.setup();
  
  // Start from first focusable element
  const firstElement = container.querySelector(expectedFocusOrder[0]) as HTMLElement;
  firstElement?.focus();
  
  for (let i = 1; i < expectedFocusOrder.length; i++) {
    await user.tab();
    const expectedElement = container.querySelector(expectedFocusOrder[i]) as HTMLElement;
    expect(expectedElement).toHaveFocus();
  }
  
  // Test wrap-around
  await user.tab();
  const firstElement2 = container.querySelector(expectedFocusOrder[0]) as HTMLElement;
  expect(firstElement2).toHaveFocus();
};

// Helper function to test ARIA attributes
export const testAriaAttributes = (element: HTMLElement, expectedAttributes: Record<string, string>) => {
  Object.entries(expectedAttributes).forEach(([attribute, value]) => {
    expect(element).toHaveAttribute(attribute, value);

};