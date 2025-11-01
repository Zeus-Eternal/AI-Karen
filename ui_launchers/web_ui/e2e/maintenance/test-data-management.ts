import { Page } from '@playwright/test';

export class TestDataManagement {
  private static instance: TestDataManagement;
  private testData: Map<string, any> = new Map();
  private cleanupTasks: Array<() => Promise<void>> = [];

  static getInstance(): TestDataManagement {
    if (!TestDataManagement.instance) {
      TestDataManagement.instance = new TestDataManagement();
    }
    return TestDataManagement.instance;
  }

  async setupTestEnvironment(page: Page): Promise<void> {
    // Setup test database state
    await this.setupTestDatabase(page);
    
    // Setup test users
    await this.setupTestUsers(page);
    
    // Setup test plugins
    await this.setupTestPlugins(page);
    
    // Setup test memory data
    await this.setupTestMemoryData(page);
  }

  private async setupTestDatabase(page: Page): Promise<void> {
    // Reset database to known state
    await page.request.post('/api/test/reset-database', {
      data: { confirm: true }
    });
    
    this.addCleanupTask(async () => {
      await page.request.post('/api/test/reset-database', {
        data: { confirm: true }
      });
    });
  }

  private async setupTestUsers(page: Page): Promise<void> {
    const testUsers = [
      {
        username: 'admin@test.com',
        password: 'AdminPass123!',
        role: 'admin',
        permissions: ['all']
      },
      {
        username: 'user@test.com',
        password: 'UserPass123!',
        role: 'user',
        permissions: ['read', 'write']
      },
      {
        username: 'moderator@test.com',
        password: 'ModPass123!',
        role: 'moderator',
        permissions: ['read', 'write', 'moderate']
      }
    ];

    for (const user of testUsers) {
      await page.request.post('/api/test/create-user', {
        data: user
      });
      
      this.addCleanupTask(async () => {
        await page.request.delete(`/api/test/users/${user.username}`);
      });
    }
  }

  private async setupTestPlugins(page: Page): Promise<void> {
    const testPlugins = [
      {
        id: 'test-analytics',
        name: 'Test Analytics Plugin',
        version: '1.0.0',
        status: 'active',
        config: {
          'api-key': 'test-key',
          'endpoint': 'http://localhost:8080'
        }
      },
      {
        id: 'test-utility',
        name: 'Test Utility Plugin',
        version: '1.5.0',
        status: 'inactive',
        config: {}
      }
    ];

    for (const plugin of testPlugins) {
      await page.request.post('/api/test/install-plugin', {
        data: plugin
      });
      
      this.addCleanupTask(async () => {
        await page.request.delete(`/api/test/plugins/${plugin.id}`);
      });
    }
  }

  private async setupTestMemoryData(page: Page): Promise<void> {
    const testMemories = [
      {
        content: 'Machine learning is a subset of artificial intelligence.',
        type: 'knowledge',
        tags: ['ai', 'ml'],
        embedding: Array(384).fill(0).map(() => Math.random())
      },
      {
        content: 'Neural networks are inspired by biological neural networks.',
        type: 'knowledge',
        tags: ['ai', 'neural-networks'],
        embedding: Array(384).fill(0).map(() => Math.random())
      },
      {
        content: 'Deep learning uses multiple layers for feature extraction.',
        type: 'knowledge',
        tags: ['ai', 'deep-learning'],
        embedding: Array(384).fill(0).map(() => Math.random())
      }
    ];

    for (const memory of testMemories) {
      await page.request.post('/api/test/create-memory', {
        data: memory
      });
    }
    
    this.addCleanupTask(async () => {
      await page.request.post('/api/test/clear-memories');
    });
  }

  async seedTestData(dataType: string, data: any): Promise<void> {
    this.testData.set(dataType, data);
  }

  getTestData(dataType: string): any {
    return this.testData.get(dataType);
  }

  addCleanupTask(task: () => Promise<void>): void {
    this.cleanupTasks.push(task);
  }

  async cleanup(): Promise<void> {
    // Execute all cleanup tasks in reverse order
    for (const task of this.cleanupTasks.reverse()) {
      try {
        await task();
      } catch (error) {
        console.error('Cleanup task failed:', error);
      }
    }
    
    this.cleanupTasks = [];
    this.testData.clear();
  }

  async createTestSnapshot(page: Page, snapshotName: string): Promise<void> {
    await page.request.post('/api/test/create-snapshot', {
      data: { name: snapshotName }
    });
  }

  async restoreTestSnapshot(page: Page, snapshotName: string): Promise<void> {
    await page.request.post('/api/test/restore-snapshot', {
      data: { name: snapshotName }
    });
  }

  async generateTestReport(): Promise<{
    totalTests: number;
    passedTests: number;
    failedTests: number;
    testDuration: number;
    coverage: number;
  }> {
    // This would integrate with actual test reporting
    return {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testDuration: 0,
      coverage: 0
    };
  }
}