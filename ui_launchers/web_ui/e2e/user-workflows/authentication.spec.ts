import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Authentication Workflows', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
    await page.goto('/');
  });

  test.describe('Login Flow', () => {
    test('should successfully login with valid credentials', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      
      await authHelper.login(credentials.username, credentials.password);
      
      // Verify successful login
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
      await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
    });

    test('should show error for invalid credentials', async ({ page }) => {
      const credentials = testData.getInvalidCredentials();
      
      await authHelper.login(credentials.username, credentials.password);
      
      // Verify error message
      await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="login-error"]')).toContainText('Invalid credentials');
      await expect(page).toHaveURL(/\/login/);
    });

    test('should handle network errors gracefully', async ({ page }) => {
      // Simulate network failure
      await page.route('**/api/auth/login', route => route.abort());
      
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Verify network error handling
      await expect(page.locator('[data-testid="network-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    });

    test('should support password reset flow', async ({ page }) => {
      await page.click('[data-testid="forgot-password-link"]');
      
      await expect(page).toHaveURL(/\/reset-password/);
      
      const email = testData.getValidEmail();
      await page.fill('[data-testid="reset-email-input"]', email);
      await page.click('[data-testid="send-reset-button"]');
      
      await expect(page.locator('[data-testid="reset-success-message"]')).toBeVisible();
    });
  });

  test.describe('Session Management', () => {
    test('should maintain session across page refreshes', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.reload();
      
      // Verify session persistence
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    });

    test('should handle session expiration', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Simulate expired token
      await page.evaluate(() => {
        localStorage.setItem('auth_token', 'expired_token');
      });
      
      await page.reload();
      
      // Verify redirect to login
      await expect(page).toHaveURL(/\/login/);
      await expect(page.locator('[data-testid="session-expired-message"]')).toBeVisible();
    });

    test('should logout successfully', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await authHelper.logout();
      
      // Verify logout
      await expect(page).toHaveURL(/\/login/);
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    });
  });

  test.describe('Role-Based Access Control', () => {
    test('should enforce admin-only access', async ({ page }) => {
      const userCredentials = testData.getUserCredentials();
      await authHelper.login(userCredentials.username, userCredentials.password);
      
      await page.goto('/admin');
      
      // Verify access denied
      await expect(page.locator('[data-testid="access-denied"]')).toBeVisible();
      await expect(page.locator('[data-testid="insufficient-permissions"]')).toBeVisible();
    });

    test('should allow admin access to restricted areas', async ({ page }) => {
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
      
      await page.goto('/admin');
      
      // Verify admin access
      await expect(page.locator('[data-testid="admin-dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-management"]')).toBeVisible();
    });
  });
});