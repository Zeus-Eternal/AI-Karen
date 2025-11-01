export class TestDataManager {
  private testUsers = {
    admin: {
      username: 'admin@test.com',
      password: 'AdminPass123!',
      role: 'admin'
    },
    user: {
      username: 'user@test.com',
      password: 'UserPass123!',
      role: 'user'
    },
    moderator: {
      username: 'moderator@test.com',
      password: 'ModPass123!',
      role: 'moderator'
    }
  };

  private testPlugins = [
    {
      id: 'test-analytics',
      name: 'Test Analytics Plugin',
      version: '1.0.0',
      category: 'analytics',
      dependencies: ['core-api'],
      permissions: ['read-analytics', 'write-reports']
    },
    {
      id: 'advanced-analytics',
      name: 'Advanced Analytics Plugin',
      version: '2.1.0',
      category: 'analytics',
      dependencies: ['core-api', 'database-connector', 'missing-dependency'],
      permissions: ['read-analytics', 'write-reports', 'admin-access']
    },
    {
      id: 'configurable',
      name: 'Configurable Plugin',
      version: '1.5.0',
      category: 'utility',
      dependencies: ['core-api'],
      permissions: ['read-config', 'write-config'],
      configurable: true
    }
  ];

  private testMemories = [
    {
      id: 'memory-1',
      content: 'Machine learning is a subset of artificial intelligence that focuses on algorithms.',
      type: 'knowledge',
      tags: ['ai', 'machine-learning', 'algorithms'],
      timestamp: '2024-01-15T10:30:00Z',
      similarity: 0.95
    },
    {
      id: 'memory-2',
      content: 'Neural networks are computing systems inspired by biological neural networks.',
      type: 'knowledge',
      tags: ['ai', 'neural-networks', 'biology'],
      timestamp: '2024-01-14T15:45:00Z',
      similarity: 0.87
    },
    {
      id: 'memory-3',
      content: 'Deep learning uses multiple layers to progressively extract features from raw input.',
      type: 'knowledge',
      tags: ['ai', 'deep-learning', 'features'],
      timestamp: '2024-01-13T09:20:00Z',
      similarity: 0.92
    }
  ];

  getValidCredentials() {
    return this.testUsers.user;
  }

  getAdminCredentials() {
    return this.testUsers.admin;
  }

  getUserCredentials() {
    return this.testUsers.user;
  }

  getModeratorCredentials() {
    return this.testUsers.moderator;
  }

  getInvalidCredentials() {
    return {
      username: 'invalid@test.com',
      password: 'WrongPassword123!'
    };
  }

  getValidEmail() {
    return 'test@example.com';
  }

  getTestPlugins() {
    return this.testPlugins;
  }

  getTestPlugin(id: string) {
    return this.testPlugins.find(plugin => plugin.id === id);
  }

  getTestMemories() {
    return this.testMemories;
  }

  getTestMemory(id: string) {
    return this.testMemories.find(memory => memory.id === id);
  }

  generateTestMemory(content: string, type: string = 'knowledge', tags: string[] = []) {
    return {
      id: `memory-${Date.now()}`,
      content,
      type,
      tags,
      timestamp: new Date().toISOString(),
      similarity: Math.random() * 0.3 + 0.7 // Random similarity between 0.7-1.0
    };
  }

  generateTestPlugin(name: string, category: string = 'utility') {
    return {
      id: `plugin-${Date.now()}`,
      name,
      version: '1.0.0',
      category,
      dependencies: ['core-api'],
      permissions: ['read-data']
    };
  }

  getSystemMetrics() {
    return {
      cpu: {
        usage: Math.random() * 30 + 20, // 20-50%
        threshold: 80
      },
      memory: {
        usage: Math.random() * 40 + 30, // 30-70%
        threshold: 80
      },
      gpu: {
        usage: Math.random() * 60 + 20, // 20-80%
        threshold: 90
      },
      network: {
        latency: Math.random() * 50 + 10, // 10-60ms
        threshold: 100
      }
    };
  }

  getHighUsageMetrics() {
    return {
      cpu: {
        usage: 95,
        threshold: 80
      },
      memory: {
        usage: 88,
        threshold: 80
      },
      gpu: {
        usage: 92,
        threshold: 90
      },
      network: {
        latency: 150,
        threshold: 100
      }
    };
  }

  getHealthySystemStatus() {
    return {
      overall: 'healthy',
      components: [
        { name: 'database', status: 'healthy', latency: 15 },
        { name: 'api', status: 'healthy', latency: 8 },
        { name: 'models', status: 'healthy', latency: 120 },
        { name: 'plugins', status: 'healthy', latency: 25 }
      ],
      alerts: []
    };
  }

  getCriticalSystemStatus() {
    return {
      overall: 'critical',
      components: [
        { name: 'database', status: 'critical', latency: 5000, error: 'Connection timeout' },
        { name: 'api', status: 'healthy', latency: 8 },
        { name: 'models', status: 'warning', latency: 800 },
        { name: 'plugins', status: 'healthy', latency: 25 }
      ],
      alerts: [
        {
          id: 'alert-1',
          severity: 'high',
          message: 'Database connection failed',
          timestamp: new Date().toISOString()
        }
      ]
    };
  }

  getTestConfiguration() {
    return {
      'api-key': 'test-api-key-12345',
      'endpoint-url': 'https://api.test.example.com',
      'timeout': '30',
      'retry-count': '3',
      'enable-logging': true
    };
  }

  getInvalidConfiguration() {
    return {
      'api-key': '',
      'endpoint-url': 'invalid-url',
      'timeout': '-1',
      'retry-count': 'not-a-number'
    };
  }

  getSearchQueries() {
    return [
      'machine learning algorithms',
      'neural networks',
      'deep learning',
      'artificial intelligence',
      'natural language processing',
      'computer vision',
      'reinforcement learning'
    ];
  }

  getSearchFilters() {
    return {
      contentTypes: ['knowledge', 'conversation', 'document', 'code'],
      dateRanges: [
        { start: '2024-01-01', end: '2024-01-31' },
        { start: '2024-02-01', end: '2024-02-29' }
      ],
      confidenceRanges: [
        { min: 0.8, max: 1.0 },
        { min: 0.6, max: 0.8 },
        { min: 0.4, max: 0.6 }
      ],
      tags: [
        ['ai', 'machine-learning'],
        ['neural-networks', 'deep-learning'],
        ['nlp', 'language-models']
      ]
    };
  }

  getNetworkGraphData() {
    return {
      nodes: [
        { id: 'node-1', label: 'Machine Learning', cluster: 'ai-concepts', connections: 5 },
        { id: 'node-2', label: 'Neural Networks', cluster: 'ai-concepts', connections: 8 },
        { id: 'node-3', label: 'Deep Learning', cluster: 'ai-concepts', connections: 6 },
        { id: 'node-4', label: 'Python Programming', cluster: 'programming', connections: 12 },
        { id: 'node-5', label: 'Data Science', cluster: 'data', connections: 7 }
      ],
      edges: [
        { source: 'node-1', target: 'node-2', weight: 0.8 },
        { source: 'node-2', target: 'node-3', weight: 0.9 },
        { source: 'node-1', target: 'node-4', weight: 0.6 },
        { source: 'node-4', target: 'node-5', weight: 0.7 }
      ],
      clusters: [
        { id: 'ai-concepts', name: 'AI Concepts', color: '#ff6b6b' },
        { id: 'programming', name: 'Programming', color: '#4ecdc4' },
        { id: 'data', name: 'Data Science', color: '#45b7d1' }
      ]
    };
  }

  getAuditLogEntries() {
    return [
      {
        id: 'audit-1',
        timestamp: '2024-01-15T10:30:00Z',
        user: 'admin@test.com',
        action: 'plugin_install',
        resource: 'test-analytics',
        details: 'Installed Test Analytics Plugin v1.0.0'
      },
      {
        id: 'audit-2',
        timestamp: '2024-01-15T10:25:00Z',
        user: 'user@test.com',
        action: 'memory_create',
        resource: 'memory-123',
        details: 'Created new memory entry about machine learning'
      },
      {
        id: 'audit-3',
        timestamp: '2024-01-15T10:20:00Z',
        user: 'moderator@test.com',
        action: 'config_update',
        resource: 'system-settings',
        details: 'Updated system configuration'
      }
    ];
  }

  cleanup() {
    // Reset any test data that might have been modified during tests
    // This method can be called in test teardown
  }
}