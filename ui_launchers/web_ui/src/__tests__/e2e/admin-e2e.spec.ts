/**
 * Admin Management System End-to-End Tests
 * 
 * These tests verify complete admin workflows in a real browser environment,
 * testing the full stack integration from UI to database.
 */

import { test, expect, Page } from '@playwright/test';

// Test data
const testUsers = {
  superAdmin: {
    email: 'superadmin@test.com',
    username: 'superadmin',
    password: 'SuperSecure123!@#',
  },
  admin: {
    email: 'admin@test.com',
    username: 'admin',
    password: 'AdminSecure123!@#',
  },
  user: {
    email: 'user@test.com',
    username: 'testuser',
    password: 'UserSecure123!@#',
  },
};

// Helper functions
async function setupDatabase(page: Page) {
  // Reset database to clean state
  await page.goto('/api/test/reset-database');
  await expect(page.locator('body')).toContainText('Database reset complete');
}

async function createSuperAdmin(page: Page) {
  await page.goto('/setup');
  
  // Complete setup wizard
  await page.click('button:has-text("Next")');
  
  await page.fill('input[name="email"]', testUsers.superAdmin.email);
  await page.fill('input[name="username"]', testUsers.superAdmin.username);
  await page.fill('input[name="password"]', testUsers.superAdmin.password);
  await page.fill('input[name="confirmPassword"]', testUsers.superAdmin.password);
  
  await page.click('button:has-text("Create Super Admin")');
  
  // Wait for setup completion
  await expect(page.locator('text=Setup Complete')).toBeVisible();
  await page.click('button:has-text("Continue to Dashboard")');
}

async function loginAs(page: Page, userType: 'superAdmin' | 'admin' | 'user') {
  const user = testUsers[userType];
  
  await page.goto('/login');
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for successful login
  await expect(page.locator('text=Dashboard')).toBeVisible();
}

test.describe('Admin Management System E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupDatabase(page);
  });

  test.describe('First-Run Setup Process', () => {
    test('should complete first-run setup successfully', async ({ page }) => {
      await page.goto('/');
      
      // Should redirect to setup page when no super admin exists
      await expect(page).toHaveURL('/setup');
      
      // Welcome step
      await expect(page.locator('h1')).toContainText('Welcome to Admin Setup');
      await page.click('button:has-text("Next")');
      
      // Admin details step
      await expect(page.locator('h2')).toContainText('Create Super Admin');
      
      await page.fill('input[name="email"]', testUsers.superAdmin.email);
      await page.fill('input[name="username"]', testUsers.superAdmin.username);
      await page.fill('input[name="password"]', testUsers.superAdmin.password);
      await page.fill('input[name="confirmPassword"]', testUsers.superAdmin.password);
      
      // Verify password strength indicator
      await expect(page.locator('.password-strength')).toContainText('Strong');
      
      await page.click('button:has-text("Create Super Admin")');
      
      // Setup completion
      await expect(page.locator('h2')).toContainText('Setup Complete');
      await expect(page.locator('text=Super admin account created successfully')).toBeVisible();
      
      await page.click('button:has-text("Continue to Dashboard")');
      
      // Should redirect to super admin dashboard
      await expect(page).toHaveURL('/admin/super');
      await expect(page.locator('h1')).toContainText('Super Admin Dashboard');
    });

    test('should prevent setup access when super admin exists', async ({ page }) => {
      // Create super admin first
      await createSuperAdmin(page);
      
      // Try to access setup page
      await page.goto('/setup');
      
      // Should redirect to login
      await expect(page).toHaveURL('/login');
    });

    test('should validate password requirements', async ({ page }) => {
      await page.goto('/setup');
      await page.click('button:has-text("Next")');
      
      // Test weak password
      await page.fill('input[name="password"]', 'weak');
      await expect(page.locator('.password-error')).toContainText('Password must be at least 12 characters');
      
      // Test password without special characters
      await page.fill('input[name="password"]', 'WeakPassword123');
      await expect(page.locator('.password-error')).toContainText('Password must contain special characters');
      
      // Test strong password
      await page.fill('input[name="password"]', testUsers.superAdmin.password);
      await expect(page.locator('.password-error')).not.toBeVisible();
      await expect(page.locator('.password-strength')).toContainText('Strong');
    });
  });

  test.describe('User Management Workflows', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
    });

    test('should create and manage users as admin', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Navigate to user management
      await page.click('nav a:has-text("User Management")');
      await expect(page).toHaveURL('/admin/users');
      
      // Create new user
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.check('input[name="sendWelcomeEmail"]');
      
      await page.click('button:has-text("Create User")');
      
      // Verify user appears in table
      await expect(page.locator('table')).toContainText(testUsers.user.email);
      await expect(page.locator('table')).toContainText('user');
      
      // Edit user
      await page.click(`tr:has-text("${testUsers.user.email}") button:has-text("Edit")`);
      
      await page.fill('input[name="username"]', 'updateduser');
      await page.click('button:has-text("Save Changes")');
      
      // Verify update
      await expect(page.locator('table')).toContainText('updateduser');
      
      // Deactivate user
      await page.click(`tr:has-text("${testUsers.user.email}") button:has-text("Deactivate")`);
      await page.click('button:has-text("Confirm")');
      
      // Verify user is deactivated
      await expect(page.locator(`tr:has-text("${testUsers.user.email}")`)).toContainText('Inactive');
    });

    test('should promote and demote users', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Create a regular user first
      await page.click('nav a:has-text("User Management")');
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.click('button:has-text("Create User")');
      
      // Navigate to admin management
      await page.click('nav a:has-text("Admin Management")');
      
      // Promote user to admin
      await page.click(`tr:has-text("${testUsers.user.email}") button:has-text("Promote")`);
      await page.click('button:has-text("Confirm Promotion")');
      
      // Verify promotion
      await expect(page.locator('table')).toContainText('admin');
      
      // Demote admin back to user
      await page.click(`tr:has-text("${testUsers.user.email}") button:has-text("Demote")`);
      await page.click('button:has-text("Confirm Demotion")');
      
      // Verify demotion
      await expect(page.locator('table')).toContainText('user');
    });

    test('should handle bulk user operations', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Create multiple users for bulk operations
      const bulkUsers = [
        { email: 'bulk1@test.com', username: 'bulk1' },
        { email: 'bulk2@test.com', username: 'bulk2' },
        { email: 'bulk3@test.com', username: 'bulk3' },
      ];
      
      await page.click('nav a:has-text("User Management")');
      
      for (const user of bulkUsers) {
        await page.click('button:has-text("Create User")');
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="username"]', user.username);
        await page.click('button:has-text("Create User")');
        await page.waitForTimeout(500); // Brief pause between creations
      }
      
      // Select all users
      await page.check('thead input[type="checkbox"]');
      
      // Perform bulk deactivation
      await page.click('button:has-text("Bulk Actions")');
      await page.click('text=Deactivate Selected');
      await page.click('button:has-text("Confirm")');
      
      // Verify progress indicator
      await expect(page.locator('.progress-bar')).toBeVisible();
      
      // Wait for completion
      await expect(page.locator('text=Bulk operation completed')).toBeVisible();
      
      // Verify all users are deactivated
      for (const user of bulkUsers) {
        await expect(page.locator(`tr:has-text("${user.email}")`)).toContainText('Inactive');
      }
    });
  });

  test.describe('Role-Based Access Control', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
      
      // Create admin user
      await page.click('nav a:has-text("Admin Management")');
      await page.click('button:has-text("Invite Admin")');
      
      await page.fill('input[name="email"]', testUsers.admin.email);
      await page.fill('input[name="username"]', testUsers.admin.username);
      await page.fill('input[name="password"]', testUsers.admin.password);
      await page.click('button:has-text("Create Admin")');
      
      await page.click('button:has-text("Logout")');
    });

    test('should enforce super admin access restrictions', async ({ page }) => {
      await loginAs(page, 'admin');
      
      // Try to access super admin routes
      await page.goto('/admin/super');
      
      // Should redirect to unauthorized page
      await expect(page).toHaveURL('/unauthorized');
      await expect(page.locator('h1')).toContainText('Unauthorized Access');
    });

    test('should enforce admin access restrictions', async ({ page }) => {
      // Create regular user
      await loginAs(page, 'superAdmin');
      await page.click('nav a:has-text("User Management")');
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.fill('input[name="password"]', testUsers.user.password);
      await page.click('button:has-text("Create User")');
      
      await page.click('button:has-text("Logout")');
      
      // Login as regular user
      await loginAs(page, 'user');
      
      // Try to access admin routes
      await page.goto('/admin');
      
      // Should redirect to unauthorized page
      await expect(page).toHaveURL('/unauthorized');
    });

    test('should show appropriate navigation based on role', async ({ page }) => {
      // Test super admin navigation
      await loginAs(page, 'superAdmin');
      
      await expect(page.locator('nav')).toContainText('Super Admin');
      await expect(page.locator('nav')).toContainText('Admin Management');
      await expect(page.locator('nav')).toContainText('System Configuration');
      await expect(page.locator('nav')).toContainText('Audit Logs');
      
      await page.click('button:has-text("Logout")');
      
      // Test admin navigation
      await loginAs(page, 'admin');
      
      await expect(page.locator('nav')).toContainText('User Management');
      await expect(page.locator('nav')).not.toContainText('Admin Management');
      await expect(page.locator('nav')).not.toContainText('System Configuration');
    });
  });

  test.describe('Audit Logging', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
    });

    test('should log administrative actions', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Perform some administrative actions
      await page.click('nav a:has-text("User Management")');
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.click('button:has-text("Create User")');
      
      // Check audit logs
      await page.click('nav a:has-text("Audit Logs")');
      
      // Verify user creation is logged
      await expect(page.locator('table')).toContainText('user_created');
      await expect(page.locator('table')).toContainText(testUsers.user.email);
      await expect(page.locator('table')).toContainText(testUsers.superAdmin.username);
      
      // Click on log entry for details
      await page.click('tr:has-text("user_created")');
      
      // Verify detailed information
      await expect(page.locator('.audit-details')).toContainText('IP Address');
      await expect(page.locator('.audit-details')).toContainText('User Agent');
      await expect(page.locator('.audit-details')).toContainText('Resource ID');
    });

    test('should filter audit logs correctly', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Perform multiple actions to generate logs
      await page.click('nav a:has-text("User Management")');
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.click('button:has-text("Create User")');
      
      // Edit the user
      await page.click(`tr:has-text("${testUsers.user.email}") button:has-text("Edit")`);
      await page.fill('input[name="username"]', 'editeduser');
      await page.click('button:has-text("Save Changes")');
      
      // Check audit logs
      await page.click('nav a:has-text("Audit Logs")');
      
      // Filter by action type
      await page.selectOption('select[name="actionType"]', 'user_updated');
      await page.click('button:has-text("Apply Filters")');
      
      // Verify only update actions are shown
      await expect(page.locator('table')).toContainText('user_updated');
      await expect(page.locator('table')).not.toContainText('user_created');
      
      // Filter by date range
      await page.selectOption('select[name="actionType"]', ''); // Clear action filter
      await page.fill('input[name="startDate"]', '2024-01-01');
      await page.fill('input[name="endDate"]', '2024-12-31');
      await page.click('button:has-text("Apply Filters")');
      
      // Verify both actions are shown
      await expect(page.locator('table')).toContainText('user_created');
      await expect(page.locator('table')).toContainText('user_updated');
    });

    test('should export audit logs', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Generate some audit data
      await page.click('nav a:has-text("User Management")');
      await page.click('button:has-text("Create User")');
      
      await page.fill('input[name="email"]', testUsers.user.email);
      await page.fill('input[name="username"]', testUsers.user.username);
      await page.click('button:has-text("Create User")');
      
      // Go to audit logs
      await page.click('nav a:has-text("Audit Logs")');
      
      // Start download
      const downloadPromise = page.waitForEvent('download');
      await page.click('button:has-text("Export")');
      
      const download = await downloadPromise;
      
      // Verify download
      expect(download.suggestedFilename()).toMatch(/audit-logs-.*\.csv/);
    });
  });

  test.describe('System Configuration', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
    });

    test('should update system configuration', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      await page.click('nav a:has-text("System Configuration")');
      
      // Update password policy
      await page.fill('input[name="passwordMinLength"]', '14');
      await page.check('input[name="requireSpecialChars"]');
      await page.check('input[name="requireNumbers"]');
      
      // Update session settings
      await page.fill('input[name="sessionTimeout"]', '20');
      await page.check('input[name="mfaRequired"]');
      
      await page.click('button:has-text("Save Configuration")');
      
      // Verify success message
      await expect(page.locator('text=Configuration saved successfully')).toBeVisible();
      
      // Verify settings are persisted
      await page.reload();
      
      await expect(page.locator('input[name="passwordMinLength"]')).toHaveValue('14');
      await expect(page.locator('input[name="requireSpecialChars"]')).toBeChecked();
      await expect(page.locator('input[name="sessionTimeout"]')).toHaveValue('20');
      await expect(page.locator('input[name="mfaRequired"]')).toBeChecked();
    });

    test('should validate configuration changes', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      await page.click('nav a:has-text("System Configuration")');
      
      // Try invalid password length
      await page.fill('input[name="passwordMinLength"]', '3');
      await page.click('button:has-text("Save Configuration")');
      
      // Verify validation error
      await expect(page.locator('.error-message')).toContainText('Password length must be at least 8 characters');
      
      // Try invalid session timeout
      await page.fill('input[name="passwordMinLength"]', '12');
      await page.fill('input[name="sessionTimeout"]', '0');
      await page.click('button:has-text("Save Configuration")');
      
      // Verify validation error
      await expect(page.locator('.error-message')).toContainText('Session timeout must be at least 5 minutes');
    });
  });

  test.describe('Error Handling and Recovery', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
    });

    test('should handle network errors gracefully', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Simulate network failure
      await page.route('/api/admin/users', route => route.abort());
      
      await page.click('nav a:has-text("User Management")');
      
      // Verify error message is shown
      await expect(page.locator('.error-message')).toContainText('Failed to load users');
      
      // Verify retry button is available
      await expect(page.locator('button:has-text("Retry")')).toBeVisible();
      
      // Remove network simulation and retry
      await page.unroute('/api/admin/users');
      await page.click('button:has-text("Retry")');
      
      // Verify successful retry
      await expect(page.locator('table')).toBeVisible();
      await expect(page.locator('.error-message')).not.toBeVisible();
    });

    test('should handle session expiration', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Simulate session expiration
      await page.route('/api/admin/**', route => {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Session expired' }),
        });
      });
      
      await page.click('nav a:has-text("User Management")');
      
      // Should redirect to login
      await expect(page).toHaveURL('/login');
      await expect(page.locator('.error-message')).toContainText('Session expired');
    });

    test('should handle server errors with appropriate messaging', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Simulate server error
      await page.route('/api/admin/users', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      });
      
      await page.click('nav a:has-text("User Management")');
      
      // Verify appropriate error message
      await expect(page.locator('.error-message')).toContainText('Server error occurred');
      await expect(page.locator('text=Please try again later')).toBeVisible();
    });
  });

  test.describe('Performance and Scalability', () => {
    test.beforeEach(async ({ page }) => {
      await createSuperAdmin(page);
    });

    test('should handle large user lists with pagination', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Create many users (simulate via API)
      await page.goto('/api/test/create-bulk-users?count=150');
      
      await page.click('nav a:has-text("User Management")');
      
      // Verify pagination is present
      await expect(page.locator('.pagination')).toBeVisible();
      await expect(page.locator('text=Page 1 of')).toBeVisible();
      
      // Verify only 50 users per page are shown
      const userRows = page.locator('tbody tr');
      await expect(userRows).toHaveCount(50);
      
      // Navigate to next page
      await page.click('button:has-text("Next")');
      
      // Verify page 2 content
      await expect(page.locator('text=Page 2 of')).toBeVisible();
      await expect(userRows).toHaveCount(50);
    });

    test('should load admin interfaces quickly', async ({ page }) => {
      await loginAs(page, 'superAdmin');
      
      // Measure navigation time to admin dashboard
      const startTime = Date.now();
      await page.click('nav a:has-text("User Management")');
      await expect(page.locator('table')).toBeVisible();
      const loadTime = Date.now() - startTime;
      
      // Verify reasonable load time (less than 2 seconds)
      expect(loadTime).toBeLessThan(2000);
    });
  });
});