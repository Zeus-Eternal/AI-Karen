/**
 * API Mocks
 * Mock implementations for API services
 */

// Note: Mock functions should be imported from the test framework being used
// This file provides mock implementations that can work with any test framework
import {
  Task,
  TaskFilters,
  TaskSortOptions,
  TaskListResponse,
  TaskStatistics,
  TaskActionPayload,
  TaskUpdateEvent,
} from '@/components/task-management/types';

import {
  Memory,
  MemoryFilters,
  MemorySortOptions,
  MemoryListResponse,
  MemoryStatistics,
  MemoryActionPayload,
  MemoryUpdateEvent,
  MemorySearchResponse,
} from '@/components/memory/types';

// Mock Task API responses
export const mockTaskListResponse: TaskListResponse = {
  tasks: [
    {
      id: 'task-1',
      title: 'Test Task 1',
      description: 'Description for test task 1',
      status: 'pending',
      priority: 'medium',
      executionMode: 'native',
      createdAt: new Date('2023-01-01'),
      updatedAt: new Date('2023-01-01'),
      progress: 0,
      metadata: {
        agentUsed: 'test-agent',
        tags: ['test'],
      },
    },
    {
      id: 'task-2',
      title: 'Test Task 2',
      description: 'Description for test task 2',
      status: 'running',
      priority: 'high',
      executionMode: 'langgraph',
      createdAt: new Date('2023-01-02'),
      updatedAt: new Date('2023-01-02'),
      startedAt: new Date('2023-01-02'),
      progress: 45,
      metadata: {
        agentUsed: 'test-agent-2',
        tags: ['test', 'important'],
      },
    },
  ],
  total: 2,
  page: 1,
  pageSize: 20,
  hasMore: false,
};

export const mockTask: Task = {
  id: 'task-1',
  title: 'Test Task',
  description: 'Description for test task',
  status: 'pending',
  priority: 'medium',
  executionMode: 'native',
  createdAt: new Date('2023-01-01'),
  updatedAt: new Date('2023-01-01'),
  progress: 0,
  metadata: {
    agentUsed: 'test-agent',
    tags: ['test'],
  },
};

export const mockTaskStatistics: TaskStatistics = {
  total: 10,
  pending: 3,
  running: 2,
  completed: 4,
  failed: 1,
  cancelled: 0,
  paused: 0,
  averageExecutionTime: 300000, // 5 minutes in ms
  successRate: 80,
  tasksByPriority: {
    low: 2,
    medium: 5,
    high: 2,
    critical: 1,
  },
  tasksByExecutionMode: {
    native: 5,
    langgraph: 3,
    deepagents: 2,
  },
  tasksByAgent: {
    'test-agent': 6,
    'test-agent-2': 4,
  },
};

// Mock Memory API responses
export const mockMemoryListResponse: MemoryListResponse = {
  memories: [
    {
      id: 'memory-1',
      title: 'Test Memory 1',
      content: 'Content for test memory 1',
      type: 'conversation',
      status: 'active',
      priority: 'medium',
      createdAt: new Date('2023-01-01'),
      updatedAt: new Date('2023-01-01'),
      metadata: {
        source: 'conversation',
        confidence: 0.9,
        importance: 0.8,
        tags: ['test'],
      },
      size: 100,
      hash: 'test-hash-1',
      version: 1,
      userId: 'user-1',
    },
    {
      id: 'memory-2',
      title: 'Test Memory 2',
      content: 'Content for test memory 2',
      type: 'case',
      status: 'active',
      priority: 'high',
      createdAt: new Date('2023-01-02'),
      updatedAt: new Date('2023-01-02'),
      metadata: {
        source: 'document',
        confidence: 0.95,
        importance: 0.9,
        tags: ['test', 'important'],
      },
      size: 200,
      hash: 'test-hash-2',
      version: 1,
      userId: 'user-1',
    },
  ],
  total: 2,
  page: 1,
  pageSize: 20,
  hasMore: false,
  facets: {
    types: {
      conversation: 1,
      case: 1,
      unified: 0,
      fact: 0,
      preference: 0,
      context: 0,
    },
    statuses: {
      active: 2,
      archived: 0,
      deleted: 0,
      processing: 0,
    },
    priorities: {
      low: 0,
      medium: 1,
      high: 1,
      critical: 0,
    },
    sources: {
      'user-input': 0,
      conversation: 1,
      document: 1,
      api: 0,
      system: 0,
      import: 0,
    },
    categories: {},
    tags: {
      test: 2,
      important: 1,
    },
    folders: {},
    collections: {},
  },
};

export const mockMemory: Memory = {
  id: 'memory-1',
  title: 'Test Memory',
  content: 'Content for test memory',
  type: 'conversation',
  status: 'active',
  priority: 'medium',
  createdAt: new Date('2023-01-01'),
  updatedAt: new Date('2023-01-01'),
  metadata: {
    source: 'conversation',
    confidence: 0.9,
    importance: 0.8,
    tags: ['test'],
  },
  size: 100,
  hash: 'test-hash',
  version: 1,
  userId: 'user-1',
};

export const mockMemoryStatistics: MemoryStatistics = {
  total: 15,
  byType: {
    conversation: 8,
    case: 4,
    unified: 2,
    fact: 1,
    preference: 0,
    context: 0,
  },
  byStatus: {
    active: 12,
    archived: 2,
    deleted: 1,
    processing: 0,
  },
  byPriority: {
    low: 3,
    medium: 7,
    high: 4,
    critical: 1,
  },
  bySource: {
    'user-input': 2,
    conversation: 8,
    document: 3,
    api: 1,
    system: 1,
    import: 0,
  },
  totalSize: 5000,
  averageSize: 333,
  oldestMemory: new Date('2023-01-01'),
  newestMemory: new Date('2023-01-15'),
  averageConfidence: 0.85,
  averageImportance: 0.75,
  totalAccessCount: 45,
  averageAccessCount: 3,
  expiredCount: 0,
  nearExpiryCount: 1,
  encryptedCount: 2,
  processingCount: 0,
  indexedCount: 15,
  retentionStats: {
    expiredLastMonth: 0,
    expiringNextMonth: 1,
    averageRetentionDays: 365,
  },
  usageStats: {
    memoriesCreatedToday: 1,
    memoriesCreatedThisWeek: 3,
    memoriesCreatedThisMonth: 8,
    memoriesAccessedToday: 2,
    memoriesAccessedThisWeek: 10,
    memoriesAccessedThisMonth: 25,
  },
  storageStats: {
    totalStorageUsed: 5000,
    storageByType: {
      conversation: 2500,
      case: 1500,
      unified: 500,
      fact: 250,
      preference: 0,
      context: 250,
    },
    storageGrowthRate: 5.2,
    projectedStorageUsage: 6500,
  },
};

// Mock API client - framework agnostic
// Note: Mock functions should be created by the test framework being used
export const createMockTaskApiClient = (mockFramework: any = null) => {
  const fn = mockFramework?.fn || (() => {});
  return {
    get: fn(),
    post: fn(),
    patch: fn(),
    put: fn(),
    delete: fn(),
  };
};

export const createMockMemoryApiClient = (mockFramework: any = null) => {
  const fn = mockFramework?.fn || (() => {});
  return {
    get: fn(),
    post: fn(),
    patch: fn(),
    put: fn(),
    delete: fn(),
  };
};

// Mock BaseApiClient
export const mockBaseApiClient = (mockFramework: any = null) => {
  const fn = mockFramework?.fn || (() => {});
  return {
    get: fn(),
    post: fn(),
    patch: fn(),
    put: fn(),
    delete: fn(),
  };
};

// Mock WebSocket events
export const mockTaskUpdateEvent: TaskUpdateEvent = {
  type: 'task_updated',
  taskId: 'task-1',
  task: mockTask,
  timestamp: new Date(),
};

export const mockMemoryUpdateEvent: MemoryUpdateEvent = {
  type: 'memory_updated',
  memoryId: 'memory-1',
  memory: mockMemory,
  timestamp: new Date(),
};

// Mock search response
export const mockMemorySearchResponse: MemorySearchResponse = {
  results: [
    {
      memory: mockMemory,
      score: 0.95,
      highlights: [
        {
          field: 'content',
          fragments: ['Content for <mark>test</mark> memory'],
        },
      ],
    },
  ],
  total: 1,
  page: 1,
  pageSize: 20,
  hasMore: false,
  suggestions: ['test query', 'test memory'],
  facets: {
    type: {
      conversation: 1,
    },
    status: {
      active: 1,
    },
  },
};

// Helper functions to create mock responses
export const createMockTaskApiResponse = (data: any, status = 200) => ({
  data,
  status,
  headers: new Headers(),
  ok: status >= 200 && status < 300,
});

export const createMockMemoryApiResponse = (data: any, status = 200) => ({
  data,
  status,
  headers: new Headers(),
  ok: status >= 200 && status < 300,
});

// Mock error responses
export const mockTaskApiError = {
  response: {
    status: 500,
    data: {
      message: 'Internal Server Error',
      code: 'INTERNAL_ERROR',
    },
  },
};

export const mockMemoryApiError = {
  response: {
    status: 500,
    data: {
      message: 'Internal Server Error',
      code: 'INTERNAL_ERROR',
    },
  },
};

// Mock WebSocket connection
export const mockWebSocketConnection = {
  onopen: null,
  onmessage: null,
  onerror: null,
  onclose: null,
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1, // OPEN
};

// Mock subscription functions
export const mockTaskSubscription = vi.fn();
export const mockMemorySubscription = vi.fn();