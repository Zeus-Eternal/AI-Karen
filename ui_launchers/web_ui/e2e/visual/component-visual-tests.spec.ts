import { test, expect } from '@playwright/test';

test.describe('Component Visual Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Setup Storybook environment
    await page.goto('http://localhost:6006');
    
    // Wait for Storybook to load
    await expect(page.locator('[data-testid="storybook-explorer"]')).toBeVisible({ timeout: 10000 });
    
    // Disable animations for consistent screenshots
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
      document.head.appendChild(style);
    });
  });

  test.describe('Button Components', () => {
    test('should match primary button variants', async ({ page }) => {
      await page.click('[data-testid="button-primary-story"]');
      await page.waitForLoadState('networkidle');
      
      // Wait for component to render
      await expect(page.locator('[data-testid="story-canvas"]')).toBeVisible();
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('button-primary-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match secondary button variants', async ({ page }) => {
      await page.click('[data-testid="button-secondary-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('button-secondary-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match button states', async ({ page }) => {
      await page.click('[data-testid="button-states-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('button-states.png', {
        animations: 'disabled'
      });
    });

    test('should match button sizes', async ({ page }) => {
      await page.click('[data-testid="button-sizes-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('button-sizes.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Form Components', () => {
    test('should match input field variants', async ({ page }) => {
      await page.click('[data-testid="input-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('input-field-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match input field states', async ({ page }) => {
      await page.click('[data-testid="input-states-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('input-field-states.png', {
        animations: 'disabled'
      });
    });

    test('should match select dropdown variants', async ({ page }) => {
      await page.click('[data-testid="select-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('select-dropdown-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match checkbox and radio variants', async ({ page }) => {
      await page.click('[data-testid="checkbox-radio-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('checkbox-radio-variants.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Navigation Components', () => {
    test('should match sidebar navigation', async ({ page }) => {
      await page.click('[data-testid="sidebar-navigation-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('sidebar-navigation.png', {
        animations: 'disabled'
      });
    });

    test('should match breadcrumb navigation', async ({ page }) => {
      await page.click('[data-testid="breadcrumb-navigation-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('breadcrumb-navigation.png', {
        animations: 'disabled'
      });
    });

    test('should match tab navigation', async ({ page }) => {
      await page.click('[data-testid="tab-navigation-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('tab-navigation.png', {
        animations: 'disabled'
      });
    });

    test('should match pagination component', async ({ page }) => {
      await page.click('[data-testid="pagination-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('pagination-component.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Data Display Components', () => {
    test('should match table variants', async ({ page }) => {
      await page.click('[data-testid="table-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('table-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match card components', async ({ page }) => {
      await page.click('[data-testid="card-components-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('card-components.png', {
        animations: 'disabled'
      });
    });

    test('should match metric widgets', async ({ page }) => {
      await page.click('[data-testid="metric-widgets-story"]');
      await page.waitForLoadState('networkidle');
      
      // Normalize dynamic values
      await page.addStyleTag({
        content: `
          [data-testid*="metric-value"] {
            color: transparent !important;
          }
          [data-testid*="metric-value"]:after {
            content: "42.5%" !important;
            color: var(--text-color) !important;
          }
        `
      });
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('metric-widgets.png', {
        animations: 'disabled'
      });
    });

    test('should match chart components', async ({ page }) => {
      await page.click('[data-testid="chart-components-story"]');
      await page.waitForLoadState('networkidle');
      
      // Wait for charts to render
      await page.waitForTimeout(2000);
      
      // Blur charts for consistent screenshots
      await page.addStyleTag({
        content: `
          canvas, svg {
            filter: blur(1px) !important;
          }
        `
      });
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('chart-components.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Feedback Components', () => {
    test('should match alert variants', async ({ page }) => {
      await page.click('[data-testid="alert-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('alert-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match toast notifications', async ({ page }) => {
      await page.click('[data-testid="toast-notifications-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('toast-notifications.png', {
        animations: 'disabled'
      });
    });

    test('should match loading states', async ({ page }) => {
      await page.click('[data-testid="loading-states-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('loading-states.png', {
        animations: 'disabled'
      });
    });

    test('should match progress indicators', async ({ page }) => {
      await page.click('[data-testid="progress-indicators-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('progress-indicators.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Modal and Overlay Components', () => {
    test('should match modal variants', async ({ page }) => {
      await page.click('[data-testid="modal-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('modal-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match dropdown menus', async ({ page }) => {
      await page.click('[data-testid="dropdown-menus-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('dropdown-menus.png', {
        animations: 'disabled'
      });
    });

    test('should match tooltip variants', async ({ page }) => {
      await page.click('[data-testid="tooltip-variants-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('tooltip-variants.png', {
        animations: 'disabled'
      });
    });

    test('should match popover components', async ({ page }) => {
      await page.click('[data-testid="popover-components-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('popover-components.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Layout Components', () => {
    test('should match grid layouts', async ({ page }) => {
      await page.click('[data-testid="grid-layouts-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('grid-layouts.png', {
        animations: 'disabled'
      });
    });

    test('should match flex layouts', async ({ page }) => {
      await page.click('[data-testid="flex-layouts-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('flex-layouts.png', {
        animations: 'disabled'
      });
    });

    test('should match container components', async ({ page }) => {
      await page.click('[data-testid="container-components-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('container-components.png', {
        animations: 'disabled'
      });
    });

    test('should match spacing utilities', async ({ page }) => {
      await page.click('[data-testid="spacing-utilities-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('spacing-utilities.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Theme Variations', () => {
    test('should match components in light theme', async ({ page }) => {
      // Set light theme
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'light');
      });
      
      await page.click('[data-testid="theme-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-light-theme.png', {
        animations: 'disabled'
      });
    });

    test('should match components in dark theme', async ({ page }) => {
      // Set dark theme
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark');
      });
      
      await page.click('[data-testid="theme-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-dark-theme.png', {
        animations: 'disabled'
      });
    });

    test('should match components in high contrast theme', async ({ page }) => {
      // Set high contrast theme
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'high-contrast');
      });
      
      await page.click('[data-testid="theme-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-high-contrast-theme.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Responsive Component Variations', () => {
    test('should match components on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.click('[data-testid="responsive-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-mobile.png', {
        animations: 'disabled'
      });
    });

    test('should match components on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await page.click('[data-testid="responsive-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-tablet.png', {
        animations: 'disabled'
      });
    });

    test('should match components on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      await page.click('[data-testid="responsive-showcase-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('components-desktop.png', {
        animations: 'disabled'
      });
    });
  });

  test.describe('Interactive States', () => {
    test('should match hover states', async ({ page }) => {
      await page.click('[data-testid="hover-states-story"]');
      await page.waitForLoadState('networkidle');
      
      // Simulate hover state
      await page.hover('[data-testid="interactive-button"]');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('hover-states.png', {
        animations: 'disabled'
      });
    });

    test('should match focus states', async ({ page }) => {
      await page.click('[data-testid="focus-states-story"]');
      await page.waitForLoadState('networkidle');
      
      // Focus on interactive element
      await page.focus('[data-testid="interactive-input"]');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('focus-states.png', {
        animations: 'disabled'
      });
    });

    test('should match active states', async ({ page }) => {
      await page.click('[data-testid="active-states-story"]');
      await page.waitForLoadState('networkidle');
      
      // Simulate active state
      await page.locator('[data-testid="interactive-button"]').dispatchEvent('mousedown');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('active-states.png', {
        animations: 'disabled'
      });
    });

    test('should match disabled states', async ({ page }) => {
      await page.click('[data-testid="disabled-states-story"]');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('[data-testid="story-canvas"]')).toHaveScreenshot('disabled-states.png', {
        animations: 'disabled'
      });
    });
  });
});