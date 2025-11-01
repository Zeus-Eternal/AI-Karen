import { Page, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

export class VisualTestManagement {
  private static instance: VisualTestManagement;
  private baselineDir: string;
  private actualDir: string;
  private diffDir: string;
  private approvedBaselines: Set<string> = new Set();

  constructor() {
    this.baselineDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-baselines');
    this.actualDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-actual');
    this.diffDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-diffs');
    
    this.ensureDirectories();
  }

  static getInstance(): VisualTestManagement {
    if (!VisualTestManagement.instance) {
      VisualTestManagement.instance = new VisualTestManagement();
    }
    return VisualTestManagement.instance;
  }

  private ensureDirectories(): void {
    [this.baselineDir, this.actualDir, this.diffDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async captureBaseline(page: Page, testName: string, options: {
    fullPage?: boolean;
    clip?: { x: number; y: number; width: number; height: number };
    mask?: string[];
    threshold?: number;
  } = {}): Promise<void> {
    const screenshotPath = path.join(this.baselineDir, `${testName}.png`);
    
    // Prepare page for consistent screenshots
    await this.preparePageForScreenshot(page, options.mask);
    
    await page.screenshot({
      path: screenshotPath,
      fullPage: options.fullPage ?? true,
      clip: options.clip,
      animations: 'disabled'
    });
    
    console.log(`Baseline captured: ${screenshotPath}`);
  }

  async compareWithBaseline(page: Page, testName: string, options: {
    fullPage?: boolean;
    clip?: { x: number; y: number; width: number; height: number };
    mask?: string[];
    threshold?: number;
  } = {}): Promise<{
    passed: boolean;
    diffPixels?: number;
    diffPercentage?: number;
    diffPath?: string;
  }> {
    const baselinePath = path.join(this.baselineDir, `${testName}.png`);
    const actualPath = path.join(this.actualDir, `${testName}.png`);
    const diffPath = path.join(this.diffDir, `${testName}-diff.png`);
    
    // Check if baseline exists
    if (!fs.existsSync(baselinePath)) {
      console.warn(`No baseline found for ${testName}, creating new baseline`);
      await this.captureBaseline(page, testName, options);
      return { passed: true };
    }
    
    // Prepare page for consistent screenshots
    await this.preparePageForScreenshot(page, options.mask);
    
    // Capture actual screenshot
    await page.screenshot({
      path: actualPath,
      fullPage: options.fullPage ?? true,
      clip: options.clip,
      animations: 'disabled'
    });
    
    // Compare screenshots using Playwright's built-in comparison
    try {
      await expect(page).toHaveScreenshot(`${testName}.png`, {
        threshold: options.threshold ?? 0.2,
        animations: 'disabled'
      });
      
      return { passed: true };
    } catch (error) {
      // Generate diff image
      const diffResult = await this.generateDiffImage(baselinePath, actualPath, diffPath);
      
      return {
        passed: false,
        diffPixels: diffResult.diffPixels,
        diffPercentage: diffResult.diffPercentage,
        diffPath
      };
    }
  }

  private async preparePageForScreenshot(page: Page, maskSelectors?: string[]): Promise<void> {
    // Disable animations
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `
    });
    
    // Wait for fonts to load
    await page.waitForFunction(() => document.fonts.ready);
    
    // Wait for images to load
    await page.waitForFunction(() => {
      const images = Array.from(document.images);
      return images.every(img => img.complete);
    });
    
    // Mask dynamic content
    if (maskSelectors) {
      await page.addStyleTag({
        content: maskSelectors.map(selector => 
          `${selector} { background: #cccccc !important; color: transparent !important; }`
        ).join('\n')
      });
    }
    
    // Hide scrollbars
    await page.addStyleTag({
      content: `
        ::-webkit-scrollbar { display: none !important; }
        * { scrollbar-width: none !important; }
      `
    });
    
    // Ensure page is stable
    await page.waitForTimeout(500);
  }

  private async generateDiffImage(baselinePath: string, actualPath: string, diffPath: string): Promise<{
    diffPixels: number;
    diffPercentage: number;
  }> {
    // This would use a proper image comparison library like pixelmatch
    // For now, return mock values
    return {
      diffPixels: 100,
      diffPercentage: 0.5
    };
  }

  async approveBaseline(testName: string): Promise<void> {
    const actualPath = path.join(this.actualDir, `${testName}.png`);
    const baselinePath = path.join(this.baselineDir, `${testName}.png`);
    
    if (fs.existsSync(actualPath)) {
      fs.copyFileSync(actualPath, baselinePath);
      this.approvedBaselines.add(testName);
      console.log(`Baseline approved for ${testName}`);
    } else {
      throw new Error(`No actual screenshot found for ${testName}`);
    }
  }

  async rejectBaseline(testName: string): Promise<void> {
    const actualPath = path.join(this.actualDir, `${testName}.png`);
    const diffPath = path.join(this.diffDir, `${testName}-diff.png`);
    
    // Keep the diff for analysis but don't update baseline
    console.log(`Baseline rejected for ${testName}. Diff available at: ${diffPath}`);
  }

  async batchApproveBaselines(testNames: string[]): Promise<void> {
    for (const testName of testNames) {
      await this.approveBaseline(testName);
    }
  }

  async generateVisualTestReport(): Promise<{
    totalTests: number;
    passedTests: number;
    failedTests: number;
    newBaselines: number;
    approvedBaselines: number;
    testResults: Array<{
      testName: string;
      status: 'passed' | 'failed' | 'new' | 'approved';
      diffPercentage?: number;
      diffPath?: string;
    }>;
  }> {
    const actualFiles = fs.readdirSync(this.actualDir).filter(f => f.endsWith('.png'));
    const baselineFiles = fs.readdirSync(this.baselineDir).filter(f => f.endsWith('.png'));
    const diffFiles = fs.readdirSync(this.diffDir).filter(f => f.endsWith('-diff.png'));
    
    const testResults = [];
    let passedTests = 0;
    let failedTests = 0;
    let newBaselines = 0;
    
    for (const actualFile of actualFiles) {
      const testName = actualFile.replace('.png', '');
      const baselineExists = baselineFiles.includes(actualFile);
      const diffExists = diffFiles.includes(`${testName}-diff.png`);
      
      if (!baselineExists) {
        testResults.push({ testName, status: 'new' });
        newBaselines++;
      } else if (diffExists) {
        testResults.push({ 
          testName, 
          status: 'failed',
          diffPath: path.join(this.diffDir, `${testName}-diff.png`)
        });
        failedTests++;
      } else {
        testResults.push({ testName, status: 'passed' });
        passedTests++;
      }
    }
    
    return {
      totalTests: actualFiles.length,
      passedTests,
      failedTests,
      newBaselines,
      approvedBaselines: this.approvedBaselines.size,
      testResults
    };
  }

  async cleanupOldScreenshots(daysOld: number = 7): Promise<void> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    [this.actualDir, this.diffDir].forEach(dir => {
      const files = fs.readdirSync(dir);
      
      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stats = fs.statSync(filePath);
        
        if (stats.mtime < cutoffDate) {
          fs.unlinkSync(filePath);
          console.log(`Cleaned up old screenshot: ${filePath}`);
        }
      });
    });
  }

  async createVisualTestSuite(suiteName: string, tests: Array<{
    name: string;
    url: string;
    selector?: string;
    viewport?: { width: number; height: number };
    actions?: Array<{ type: 'click' | 'hover' | 'fill'; selector: string; value?: string }>;
  }>): Promise<string> {
    const suiteContent = `
import { test, expect } from '@playwright/test';
import { VisualTestManagement } from './visual-test-management';

test.describe('${suiteName}', () => {
  let visualTesting: VisualTestManagement;

  test.beforeEach(async ({ page }) => {
    visualTesting = VisualTestManagement.getInstance();
    
    // Setup consistent visual testing environment
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.textContent = \`
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      \`;
      document.head.appendChild(style);
    });
  });

${tests.map(testCase => `
  test('should match ${testCase.name}', async ({ page }) => {
    ${testCase.viewport ? `await page.setViewportSize(${JSON.stringify(testCase.viewport)});` : ''}
    await page.goto('${testCase.url}');
    await page.waitForLoadState('networkidle');
    
    ${testCase.actions ? testCase.actions.map(action => {
      switch (action.type) {
        case 'click':
          return `await page.click('${action.selector}');`;
        case 'hover':
          return `await page.hover('${action.selector}');`;
        case 'fill':
          return `await page.fill('${action.selector}', '${action.value}');`;
        default:
          return '';
      }
    }).join('\n    ') : ''}
    
    ${testCase.selector ? `
    await expect(page.locator('${testCase.selector}')).toBeVisible();
    await expect(page.locator('${testCase.selector}')).toHaveScreenshot('${testCase.name}.png', {
      animations: 'disabled'
    });
    ` : `
    await expect(page).toHaveScreenshot('${testCase.name}.png', {
      fullPage: true,
      animations: 'disabled'
    });
    `}
  });
`).join('')}
});
`;

    const suitePath = path.join(process.cwd(), 'e2e', 'visual', `${suiteName}.spec.ts`);
    fs.writeFileSync(suitePath, suiteContent);
    
    return suitePath;
  }

  getBaselineDirectory(): string {
    return this.baselineDir;
  }

  getActualDirectory(): string {
    return this.actualDir;
  }

  getDiffDirectory(): string {
    return this.diffDir;
  }
}