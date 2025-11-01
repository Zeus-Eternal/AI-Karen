import { Page, expect } from '@playwright/test';

export class AuthenticationHelper {
  constructor(private page: Page) {}

  async login(username: string, password: string): Promise<void> {
    await this.page.goto('/login');
    
    // Wait for login form to be visible
    await expect(this.page.locator('[data-testid="login-form"]')).toBeVisible();
    
    // Fill credentials
    await this.page.fill('[data-testid="username-input"]', username);
    await this.page.fill('[data-testid="password-input"]', password);
    
    // Submit form
    await this.page.click('[data-testid="login-button"]');
    
    // Wait for navigation or error
    await this.page.waitForURL(/\/(dashboard|login)/, { timeout: 10000 });
  }

  async logout(): Promise<void> {
    // Check if user menu is visible (user is logged in)
    const userMenu = this.page.locator('[data-testid="user-menu"]');
    if (await userMenu.isVisible()) {
      await userMenu.click();
      await this.page.click('[data-testid="logout-button"]');
      await this.page.waitForURL(/\/login/, { timeout: 5000 });
    }
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      await expect(this.page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  async getCurrentUser(): Promise<string | null> {
    if (await this.isLoggedIn()) {
      const userMenu = this.page.locator('[data-testid="user-menu"]');
      await userMenu.click();
      const username = await this.page.locator('[data-testid="current-username"]').textContent();
      await userMenu.click(); // Close menu
      return username;
    }
    return null;
  }

  async resetPassword(email: string): Promise<void> {
    await this.page.goto('/reset-password');
    await this.page.fill('[data-testid="reset-email-input"]', email);
    await this.page.click('[data-testid="send-reset-button"]');
    await expect(this.page.locator('[data-testid="reset-success-message"]')).toBeVisible();
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.page.goto('/settings/security');
    await this.page.fill('[data-testid="current-password-input"]', currentPassword);
    await this.page.fill('[data-testid="new-password-input"]', newPassword);
    await this.page.fill('[data-testid="confirm-password-input"]', newPassword);
    await this.page.click('[data-testid="change-password-button"]');
    await expect(this.page.locator('[data-testid="password-changed-success"]')).toBeVisible();
  }

  async enableTwoFactor(): Promise<string> {
    await this.page.goto('/settings/security');
    await this.page.click('[data-testid="enable-2fa-button"]');
    
    // Get the backup codes
    await expect(this.page.locator('[data-testid="2fa-backup-codes"]')).toBeVisible();
    const backupCodes = await this.page.locator('[data-testid="backup-code"]').allTextContents();
    
    await this.page.click('[data-testid="confirm-2fa-setup"]');
    await expect(this.page.locator('[data-testid="2fa-enabled-success"]')).toBeVisible();
    
    return backupCodes.join(',');
  }

  async loginWithTwoFactor(username: string, password: string, totpCode: string): Promise<void> {
    await this.login(username, password);
    
    // Handle 2FA prompt
    await expect(this.page.locator('[data-testid="2fa-code-input"]')).toBeVisible();
    await this.page.fill('[data-testid="2fa-code-input"]', totpCode);
    await this.page.click('[data-testid="verify-2fa-button"]');
    
    await this.page.waitForURL(/\/dashboard/, { timeout: 10000 });
  }
}