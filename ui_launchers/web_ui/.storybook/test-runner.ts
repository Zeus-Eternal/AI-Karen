import type { TestRunnerConfig } from '@storybook/test-runner';
import { checkA11y, injectAxe } from 'axe-playwright';

const config: TestRunnerConfig = {
  setup() {
    // Add global setup here if needed
  },
  async preVisit(page, context) {
    // Inject axe-core for accessibility testing
    await injectAxe(page);
  },
  async postVisit(page, context) {
    // Run accessibility tests on each story
    await checkA11y(page, '#storybook-root', {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });

    // Take screenshot for visual regression testing
    const elementHandler = await page.$('#storybook-root');
    const innerHTML = await elementHandler?.innerHTML();
    
    if (innerHTML) {
      await page.screenshot({
        path: `screenshots/${context.id}.png`,
        fullPage: false,
        clip: await elementHandler?.boundingBox() || undefined,
      });
    }
  },
  tags: {
    include: ['test'],
    exclude: ['skip-test'],
    skip: ['skip-test'],
  },
};

export default config;