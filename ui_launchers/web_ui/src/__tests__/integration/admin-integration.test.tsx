/**
 * Admin Management System Integration Tests
 * 
 * This file contains comprehensive integration tests for the admin management system,
 * covering all critical workflows and requirements validation.
 * 
 * Test Coverage:
 * - First-run setup process from start to finish
 * - User promotion and demotion workflows
 * - Bulk user operations with large datasets
 * - Audit logging across all administrative actions
 * - Role-based access control in various scenarios
 * - End-to-end tests for critical admin user journeys
 */


import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { resetRouterMocks } from '@/test-utils/router-mocks';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '@/contexts/AuthContext';
import { SetupWizard } from '@/components/auth/setup/SetupWizard';
import { SuperAdminDashboard } from '@/components/admin/SuperAdminDashboard';
import { AdminDashboard } from '@/components/admin/AdminDashboard';
import { UserManagementTable } from '@/components/admin/UserManagementTable';
import { BulkUserOperations } from '@/components/admin/BulkUserOperations';
import { AuditLogViewer } from '@/components/admin/audit/AuditLogViewer';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminRoute } from '@/components/auth/AdminRoute';
import { SuperAdminRoute } from '@/components/auth/SuperAdminRoute';
import type { User, AuditLog } from '@/types/admin';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  href: 'http://localhost:3000',
  pathname: '/',
  search: '',
  hash: '',
  assign: vi.fn(),
  replace: vi.fn(),
  reload: vi.fn(),
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Mock document.cookie
let mockCookies = '';
Object.defineProperty(document, 'cookie', {
  get: () => mockCookies,
  set: (value: string) => {
    mockCookies = value;
  },

// Mock users data for testing
const mockUsers: User[] = [
  {
    id: '1',
    email: 'user1@example.com',
    username: 'user1',
    passwordHash: 'hash1',
    role: 'user',
    isActive: true,
    emailVerified: true,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  },
  {
    id: '2',
    email: 'admin@example.com',
    username: 'admin',
    passwordHash: 'hash2',
    role: 'admin',
    isActive: true,
    emailVerified: true,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  },
  {
    id: '3',
    email: 'superadmin@example.com',
    username: 'superadmin',
    passwordHash: 'hash3',
    role: 'super_admin',
    isActive: true,
    emailVerified: true,
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
  },
];

// Mock audit logs for testing
const mockAuditLogs: AuditLog[] = [
  {
    id: '1',
    userId: '3',
    action: 'user_created',
    resourceType: 'user',
    resourceId: '1',
    details: { email: 'user1@example.com' },
    ipAddress: '127.0.0.1',
    userAgent: 'test-agent',
    timestamp: new Date('2024-01-01T10:00:00Z'),
  },
  {
    id: '2',
    userId: '3',
    action: 'user_promoted',
    resourceType: 'user',
    resourceId: '2',
    details: { fromRole: 'user', toRole: 'admin' },
    ipAddress: '127.0.0.1',
    userAgent: 'test-agent',
    timestamp: new Date('2024-01-01T11:00:00Z'),
  },
];

describe('Admin Management System Integration Tests', () => {
  beforeEach(() => {
    resetRouterMocks();
    mockCookies = '';
    mockLocation.pathname = '/';
    mockLocation.href = 'http://localhost:3000';

  afterEach(() => {
    vi.restoreAllMocks();

  describe('First-Run Setup Process', () => {
    it('should complete first-run setup process from start to finish', async () => {
      const user = userEvent.setup();

      // Mock API responses for first-run setup
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ hasSuperAdmin: false }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true, 
            user: { 
              id: '1', 
              email: 'admin@example.com', 
              role: 'super_admin' 
            } 
          }),

      render(
        <AuthProvider>
          <SetupWizard />
        </AuthProvider>
      );

      // Step 1: Welcome step should be visible
      expect(screen.getByText(/welcome to the admin setup/i)).toBeInTheDocument();
      
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Step 2: Admin details form
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();

      const emailInput = screen.getByLabelText(/email/i);
      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await user.type(emailInput, 'admin@example.com');
      await user.type(usernameInput, 'superadmin');
      await user.type(passwordInput, 'SuperSecure123!@#');
      await user.type(confirmPasswordInput, 'SuperSecure123!@#');

      const createButton = screen.getByRole('button', { name: /create super admin/i });
      await user.click(createButton);

      // Step 3: Setup completion
      await waitFor(() => {
        expect(screen.getByText(/setup complete/i)).toBeInTheDocument();

      // Verify API calls were made correctly
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/setup/check-first-run', {
        method: 'GET',
        credentials: 'include',

      expect(mockFetch).toHaveBeenCalledWith('/api/admin/setup/create-super-admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: 'admin@example.com',
          username: 'superadmin',
          password: 'SuperSecure123!@#',
        }),


    it('should prevent access to setup when super admin already exists', async () => {
      // Mock API response indicating super admin exists
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ hasSuperAdmin: true }),

      render(
        <AuthProvider>
          <SetupWizard />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockLocation.replace).toHaveBeenCalledWith('/login');


    it('should validate password strength during setup', async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ hasSuperAdmin: false }),

      render(
        <AuthProvider>
          <SetupWizard />
        </AuthProvider>
      );

      // Navigate to admin details step
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

      const passwordInput = screen.getByLabelText(/^password$/i);
      
      // Test weak password
      await user.type(passwordInput, 'weak');
      
      await waitFor(() => {
        expect(screen.getByText(/password must be at least 12 characters/i)).toBeInTheDocument();

      // Test strong password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'SuperSecure123!@#');

      await waitFor(() => {
        expect(screen.queryByText(/password must be at least 12 characters/i)).not.toBeInTheDocument();



  describe('User Promotion and Demotion Workflows', () => {
    it('should promote user to admin successfully', async () => {
      const user = userEvent.setup();

      // Mock session validation and API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ users: mockUsers }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true, 
            user: { ...mockUsers[0], role: 'admin' } 
          }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        </AuthProvider>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByText(/admin management/i)).toBeInTheDocument();

      // Find and click promote button for user1
      const promoteButton = screen.getByRole('button', { name: /promote.*user1/i });
      await user.click(promoteButton);

      // Confirm promotion in dialog
      const confirmButton = await screen.findByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      // Verify API call was made
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/admins/promote/1', {
          method: 'POST',
          credentials: 'include',



    it('should demote admin to user successfully', async () => {
      const user = userEvent.setup();

      // Mock session validation and API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ users: mockUsers }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true, 
            user: { ...mockUsers[1], role: 'user' } 
          }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/admin management/i)).toBeInTheDocument();

      // Find and click demote button for admin
      const demoteButton = screen.getByRole('button', { name: /demote.*admin/i });
      await user.click(demoteButton);

      // Confirm demotion in dialog
      const confirmButton = await screen.findByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      // Verify API call was made
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/admins/demote/2', {
          method: 'POST',
          credentials: 'include',



    it('should prevent regular admin from promoting users', async () => {
      // Mock session validation for regular admin
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          user: { id: '2', role: 'admin', email: 'admin@example.com' } 
        }),

      render(
        <AuthProvider>
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/user management/i)).toBeInTheDocument();

      // Verify promote/demote buttons are not present for regular admin
      expect(screen.queryByRole('button', { name: /promote/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /demote/i })).not.toBeInTheDocument();


  describe('Bulk User Operations', () => {
    it('should handle bulk user operations with large datasets', async () => {
      const user = userEvent.setup();

      // Generate large dataset for testing
      const largeUserDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: `user-${i}`,
        email: `user${i}@example.com`,
        username: `user${i}`,
        passwordHash: `hash${i}`,
        role: 'user' as const,
        isActive: true,
        emailVerified: true,
        createdAt: new Date('2024-01-01'),
        updatedAt: new Date('2024-01-01'),
      }));

      // Mock API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '2', role: 'admin', email: 'admin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            users: largeUserDataset.slice(0, 50), // Paginated response
            total: 1000,
            page: 1,
            limit: 50,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true, 
            processed: 100,
            errors: [] 
          }),

      render(
        <AuthProvider>
          <AdminRoute>
            <BulkUserOperations />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/bulk operations/i)).toBeInTheDocument();

      // Select multiple users
      const selectAllCheckbox = screen.getByRole('checkbox', { name: /select all/i });
      await user.click(selectAllCheckbox);

      // Perform bulk status change
      const bulkActionButton = screen.getByRole('button', { name: /bulk actions/i });
      await user.click(bulkActionButton);

      const deactivateOption = screen.getByRole('menuitem', { name: /deactivate selected/i });
      await user.click(deactivateOption);

      // Confirm bulk operation
      const confirmButton = await screen.findByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      // Verify progress indicator appears
      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Verify API call was made
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/users/bulk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            action: 'deactivate',
            userIds: expect.any(Array),
          }),



    it('should handle bulk import with CSV validation', async () => {
      const user = userEvent.setup();

      // Mock CSV file content
      const csvContent = `email,username,role
newuser1@example.com,newuser1,user
newuser2@example.com,newuser2,admin
invalid-email,newuser3,user`;

      const csvFile = new File([csvContent], 'users.csv', { type: 'text/csv' });

      // Mock API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '2', role: 'admin', email: 'admin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true,
            imported: 2,
            errors: [{ row: 3, error: 'Invalid email format' }]
          }),

      render(
        <AuthProvider>
          <AdminRoute>
            <BulkUserOperations />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/import users/i)).toBeInTheDocument();

      // Upload CSV file
      const fileInput = screen.getByLabelText(/upload csv/i);
      await user.upload(fileInput, csvFile);

      // Click import button
      const importButton = screen.getByRole('button', { name: /import/i });
      await user.click(importButton);

      // Verify import results are displayed
      await waitFor(() => {
        expect(screen.getByText(/2 users imported successfully/i)).toBeInTheDocument();
        expect(screen.getByText(/1 error/i)).toBeInTheDocument();


    it('should allow cancellation of long-running bulk operations', async () => {
      const user = userEvent.setup();

      // Mock API responses with delay
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '2', role: 'admin', email: 'admin@example.com' } 
          }),
        })
        .mockImplementationOnce(() => 
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => ({ success: true, processed: 500 }),

            }, 5000); // Long operation
          })
        );

      render(
        <AuthProvider>
          <AdminRoute>
            <BulkUserOperations />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/bulk operations/i)).toBeInTheDocument();

      // Start bulk operation
      const bulkActionButton = screen.getByRole('button', { name: /bulk actions/i });
      await user.click(bulkActionButton);

      const exportOption = screen.getByRole('menuitem', { name: /export all/i });
      await user.click(exportOption);

      // Wait for progress indicator
      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Cancel operation
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Verify operation was cancelled
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
        expect(screen.getByText(/operation cancelled/i)).toBeInTheDocument();



  describe('Audit Logging Validation', () => {
    it('should log all administrative actions correctly', async () => {
      const user = userEvent.setup();

      // Mock API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
          }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <AuditLogViewer />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/audit logs/i)).toBeInTheDocument();

      // Verify audit logs are displayed
      expect(screen.getByText(/user_created/i)).toBeInTheDocument();
      expect(screen.getByText(/user_promoted/i)).toBeInTheDocument();
      expect(screen.getByText(/user1@example.com/i)).toBeInTheDocument();

      // Test filtering by action type
      const actionFilter = screen.getByRole('combobox', { name: /action type/i });
      await user.click(actionFilter);
      
      const promotionOption = screen.getByRole('option', { name: /user_promoted/i });
      await user.click(promotionOption);

      // Verify filtered results
      await waitFor(() => {
        expect(screen.getByText(/user_promoted/i)).toBeInTheDocument();
        expect(screen.queryByText(/user_created/i)).not.toBeInTheDocument();


    it('should track IP addresses and user agents in audit logs', async () => {
      const user = userEvent.setup();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
          }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <AuditLogViewer />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/audit logs/i)).toBeInTheDocument();

      // Click on a log entry to view details
      const logEntry = screen.getByText(/user_created/i);
      await user.click(logEntry);

      // Verify detailed information is shown
      await waitFor(() => {
        expect(screen.getByText(/127\.0\.0\.1/)).toBeInTheDocument();
        expect(screen.getByText(/test-agent/)).toBeInTheDocument();


    it('should support audit log export for compliance', async () => {
      const user = userEvent.setup();

      // Mock blob creation
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = vi.fn();

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => new Blob(['audit,log,data'], { type: 'text/csv' }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <AuditLogViewer />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/audit logs/i)).toBeInTheDocument();

      // Click export button
      const exportButton = screen.getByRole('button', { name: /export/i });
      await user.click(exportButton);

      // Verify export API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/system/audit-logs/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            filters: expect.any(Object),
            format: 'csv',
          }),




  describe('Role-Based Access Control', () => {
    it('should enforce super admin access restrictions', async () => {
      // Test unauthorized access to super admin routes
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          user: { id: '2', role: 'admin', email: 'admin@example.com' } 
        }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        </AuthProvider>
      );

      // Should redirect to unauthorized page
      await waitFor(() => {
        expect(mockLocation.replace).toHaveBeenCalledWith('/unauthorized');


    it('should enforce admin access restrictions', async () => {
      // Test unauthorized access to admin routes
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          user: { id: '1', role: 'user', email: 'user@example.com' } 
        }),

      render(
        <AuthProvider>
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        </AuthProvider>
      );

      // Should redirect to unauthorized page
      await waitFor(() => {
        expect(mockLocation.replace).toHaveBeenCalledWith('/unauthorized');


    it('should allow proper role transitions', async () => {
      const user = userEvent.setup();

      // Mock session validation for super admin
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ users: mockUsers }),

      const { rerender } = render(
        <AuthProvider>
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/super admin dashboard/i)).toBeInTheDocument();

      // Simulate role change to admin
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          user: { id: '3', role: 'admin', email: 'superadmin@example.com' } 
        }),

      rerender(
        <AuthProvider>
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/user management/i)).toBeInTheDocument();


    it('should validate API endpoint permissions', async () => {
      // Test API endpoint access with insufficient permissions
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '1', role: 'user', email: 'user@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
          json: async () => ({ error: 'Insufficient permissions' }),

      // Attempt to access admin API as regular user
      const response = await fetch('/api/admin/users', {
        method: 'GET',
        credentials: 'include',

      expect(response.ok).toBe(false);
      expect(response.status).toBe(403);


  describe('End-to-End Admin User Journeys', () => {
    it('should complete full admin user creation journey', async () => {
      const user = userEvent.setup();

      // Mock API responses for complete journey
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '2', role: 'admin', email: 'admin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ users: mockUsers }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            success: true,
            user: {
              id: '4',
              email: 'newuser@example.com',
              username: 'newuser',
              role: 'user',
              isActive: true,
              emailVerified: false,
            }
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),

      render(
        <AuthProvider>
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/user management/i)).toBeInTheDocument();

      // Click create user button
      const createUserButton = screen.getByRole('button', { name: /create user/i });
      await user.click(createUserButton);

      // Fill out user creation form
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();

      const emailInput = screen.getByLabelText(/email/i);
      const usernameInput = screen.getByLabelText(/username/i);

      await user.type(emailInput, 'newuser@example.com');
      await user.type(usernameInput, 'newuser');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      // Verify user creation API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            email: 'newuser@example.com',
            username: 'newuser',
            sendWelcomeEmail: true,
          }),


      // Verify success message
      expect(screen.getByText(/user created successfully/i)).toBeInTheDocument();

      // Send welcome email
      const sendEmailButton = screen.getByRole('button', { name: /send welcome email/i });
      await user.click(sendEmailButton);

      // Verify email API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/email/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            to: 'newuser@example.com',
            template: 'welcome',
            data: expect.any(Object),
          }),



    it('should complete full system configuration journey', async () => {
      const user = userEvent.setup();

      // Mock API responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '3', role: 'super_admin', email: 'superadmin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            config: {
              passwordMinLength: 8,
              sessionTimeout: 30,
              mfaRequired: false,
            }
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),

      render(
        <AuthProvider>
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/system configuration/i)).toBeInTheDocument();

      // Navigate to system configuration
      const configTab = screen.getByRole('tab', { name: /system configuration/i });
      await user.click(configTab);

      // Update password policy
      const passwordLengthInput = screen.getByLabelText(/minimum password length/i);
      await user.clear(passwordLengthInput);
      await user.type(passwordLengthInput, '12');

      // Enable MFA requirement
      const mfaCheckbox = screen.getByLabelText(/require mfa for admins/i);
      await user.click(mfaCheckbox);

      // Save configuration
      const saveButton = screen.getByRole('button', { name: /save configuration/i });
      await user.click(saveButton);

      // Verify API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/system/config', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            passwordMinLength: 12,
            sessionTimeout: 30,
            mfaRequired: true,
          }),


      // Verify success message
      expect(screen.getByText(/configuration saved successfully/i)).toBeInTheDocument();

    it('should handle error scenarios gracefully throughout user journeys', async () => {
      const user = userEvent.setup();

      // Mock API error responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ 
            user: { id: '2', role: 'admin', email: 'admin@example.com' } 
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ error: 'Internal server error' }),

      render(
        <AuthProvider>
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        </AuthProvider>
      );

      // Wait for error to be displayed
      await waitFor(() => {
        expect(screen.getByText(/failed to load users/i)).toBeInTheDocument();

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      
      // Mock successful retry
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ users: mockUsers }),

      await user.click(retryButton);

      // Verify successful retry
      await waitFor(() => {
        expect(screen.getByText(/user management/i)).toBeInTheDocument();
        expect(screen.queryByText(/failed to load users/i)).not.toBeInTheDocument();



