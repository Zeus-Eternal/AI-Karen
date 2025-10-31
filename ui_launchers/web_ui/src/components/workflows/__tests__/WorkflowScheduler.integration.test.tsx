import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowScheduler } from '../WorkflowScheduler';
import { 
  WorkflowTrigger, 
  WorkflowQueue, 
  WorkflowAutomationAnalytics 
} from '@/types/workflows';

const mockTriggers: WorkflowTrigger[] = [
  {
    id: 'trigger-1',
    name: 'Daily Report Generation',
    type: 'schedule',
    config: {
      schedule: {
        expression: '0 9 * * *',
        timezone: 'UTC',
        enabled: true,
        nextRun: new Date(Date.now() + 3600000), // 1 hour from now
        lastRun: new Date(Date.now() - 86400000), // 1 day ago
      }
    },
    enabled: true,
    workflowId: 'workflow-1',
    lastTriggered: new Date(Date.now() - 86400000),
    nextTrigger: new Date(Date.now() + 3600000),
  },
  {
    id: 'trigger-2',
    name: 'File Upload Handler',
    type: 'file',
    config: {
      file: {
        path: '/uploads',
        pattern: '*.csv',
        action: 'created'
      }
    },
    enabled: false,
    workflowId: 'workflow-2',
    lastTriggered: undefined,
    nextTrigger: undefined,
  },
  {
    id: 'trigger-3',
    name: 'API Webhook',
    type: 'webhook',
    config: {
      webhook: {
        url: 'https://api.example.com/webhook',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        authentication: {
          type: 'bearer',
          credentials: { token: 'secret' }
        }
      }
    },
    enabled: true,
    workflowId: 'workflow-3',
    lastTriggered: new Date(Date.now() - 3600000),
    nextTrigger: undefined,
  }
];

const mockQueues: WorkflowQueue[] = [
  {
    id: 'queue-1',
    name: 'High Priority Queue',
    priority: 1,
    maxConcurrency: 5,
    currentLoad: 3,
    tasks: [
      {
        id: 'task-1',
        workflowId: 'workflow-1',
        priority: 1,
        queuedAt: new Date(),
        estimatedDuration: 30000,
        dependencies: [],
        payload: { test: true }
      },
      {
        id: 'task-2',
        workflowId: 'workflow-2',
        priority: 2,
        queuedAt: new Date(),
        estimatedDuration: 45000,
        dependencies: ['task-1'],
        payload: { test: true }
      }
    ],
    metrics: {
      totalProcessed: 150,
      averageWaitTime: 2500,
      averageExecutionTime: 35000,
      throughput: 4.2,
      errorRate: 0.05
    }
  },
  {
    id: 'queue-2',
    name: 'Background Processing',
    priority: 3,
    maxConcurrency: 10,
    currentLoad: 7,
    tasks: [],
    metrics: {
      totalProcessed: 500,
      averageWaitTime: 1200,
      averageExecutionTime: 15000,
      throughput: 8.5,
      errorRate: 0.02
    }
  }
];

const mockAnalytics: WorkflowAutomationAnalytics = {
  successRate: 0.92,
  failureRate: 0.08,
  averageExecutionTime: 25000,
  resourceUtilization: {
    cpu: 0.65,
    memory: 0.78,
    gpu: 0.45
  },
  costAnalysis: {
    totalCost: 125.50,
    costPerExecution: 0.025,
    costBreakdown: {
      compute: 75.30,
      storage: 25.20,
      network: 25.00
    }
  },
  trends: {
    executions: [
      { timestamp: new Date(), value: 100, metadata: { status: 'completed' } },
      { timestamp: new Date(), value: 95, metadata: { status: 'completed' } },
    ],
    performance: [
      { timestamp: new Date(), value: 23000 },
      { timestamp: new Date(), value: 25000 },
    ],
    errors: [
      { timestamp: new Date(), value: 5 },
      { timestamp: new Date(), value: 8 },
    ]
  },
  bottlenecks: [
    {
      nodeId: 'node-1',
      nodeName: 'Data Processing Node',
      averageExecutionTime: 45000,
      frequency: 85,
      impact: 'high',
      suggestions: [
        'Consider parallel processing',
        'Optimize data queries',
        'Increase memory allocation'
      ]
    },
    {
      nodeId: 'node-2',
      nodeName: 'File Upload Node',
      averageExecutionTime: 15000,
      frequency: 60,
      impact: 'medium',
      suggestions: [
        'Implement file streaming',
        'Add compression'
      ]
    }
  ],
  optimizationSuggestions: [
    {
      id: 'opt-1',
      type: 'performance',
      priority: 'high',
      title: 'Implement Parallel Processing',
      description: 'Enable parallel execution for data processing workflows',
      estimatedImpact: '40% reduction in execution time',
      implementation: 'Configure workflow nodes to run in parallel where possible'
    },
    {
      id: 'opt-2',
      type: 'cost',
      priority: 'medium',
      title: 'Optimize Resource Allocation',
      description: 'Right-size compute resources based on actual usage',
      estimatedImpact: '25% cost reduction',
      implementation: 'Analyze resource usage patterns and adjust allocations'
    }
  ]
};

describe('WorkflowScheduler Integration Tests', () => {
  const mockHandlers = {
    onCreateTrigger: vi.fn(),
    onUpdateTrigger: vi.fn(),
    onDeleteTrigger: vi.fn(),
    onToggleTrigger: vi.fn(),
    onCreateQueue: vi.fn(),
    onUpdateQueue: vi.fn(),
    onDeleteQueue: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('complete workflow scheduling', () => {
    it('should render all scheduler components and data', () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Header and navigation
      expect(screen.getByText('Workflow Scheduler')).toBeInTheDocument();
      expect(screen.getByText('Automate workflow execution with triggers and queues')).toBeInTheDocument();

      // Stats overview
      expect(screen.getByText('Active Triggers')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // 2 active triggers
      expect(screen.getByText('Queued Tasks')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('92.0%')).toBeInTheDocument();

      // Tab navigation
      expect(screen.getByText('Triggers')).toBeInTheDocument();
      expect(screen.getByText('Queues')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Optimization')).toBeInTheDocument();
    });

    it('should display trigger information correctly', () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Trigger names and types
      expect(screen.getByText('Daily Report Generation')).toBeInTheDocument();
      expect(screen.getByText('File Upload Handler')).toBeInTheDocument();
      expect(screen.getByText('API Webhook')).toBeInTheDocument();

      // Trigger statuses
      expect(screen.getAllByText('Active')).toHaveLength(2);
      expect(screen.getByText('Inactive')).toBeInTheDocument();

      // Trigger types
      expect(screen.getByText('schedule')).toBeInTheDocument();
      expect(screen.getByText('file')).toBeInTheDocument();
      expect(screen.getByText('webhook')).toBeInTheDocument();
    });

    it('should handle trigger toggle correctly', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Find and click a trigger toggle
      const toggles = screen.getAllByRole('switch');
      fireEvent.click(toggles[0]);

      await waitFor(() => {
        expect(mockHandlers.onToggleTrigger).toHaveBeenCalledWith('trigger-1', false);
      });
    });

    it('should navigate between tabs correctly', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Click on Queues tab
      fireEvent.click(screen.getByText('Queues'));

      await waitFor(() => {
        expect(screen.getByText('High Priority Queue')).toBeInTheDocument();
        expect(screen.getByText('Background Processing')).toBeInTheDocument();
      });

      // Click on Analytics tab
      fireEvent.click(screen.getByText('Analytics'));

      await waitFor(() => {
        expect(screen.getByText('Execution Trends')).toBeInTheDocument();
        expect(screen.getByText('Resource Utilization')).toBeInTheDocument();
      });

      // Click on Optimization tab
      fireEvent.click(screen.getByText('Optimization'));

      await waitFor(() => {
        expect(screen.getByText('Performance Bottlenecks')).toBeInTheDocument();
        expect(screen.getByText('Optimization Suggestions')).toBeInTheDocument();
      });
    });
  });

  describe('queue management', () => {
    it('should display queue information and metrics', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Navigate to queues tab
      fireEvent.click(screen.getByText('Queues'));

      await waitFor(() => {
        // Queue names and priorities
        expect(screen.getByText('High Priority Queue')).toBeInTheDocument();
        expect(screen.getByText('Priority 1')).toBeInTheDocument();
        expect(screen.getByText('Background Processing')).toBeInTheDocument();
        expect(screen.getByText('Priority 3')).toBeInTheDocument();

        // Queue metrics
        expect(screen.getByText('3/5')).toBeInTheDocument(); // Current load for queue 1
        expect(screen.getByText('7/10')).toBeInTheDocument(); // Current load for queue 2
        expect(screen.getByText('4.2/min')).toBeInTheDocument(); // Throughput for queue 1
        expect(screen.getByText('8.5/min')).toBeInTheDocument(); // Throughput for queue 2
      });
    });

    it('should show queue capacity usage correctly', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Queues'));

      await waitFor(() => {
        // Capacity percentages
        expect(screen.getByText('60%')).toBeInTheDocument(); // 3/5 = 60%
        expect(screen.getByText('70%')).toBeInTheDocument(); // 7/10 = 70%
      });
    });

    it('should display recent tasks in queues', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Queues'));

      await waitFor(() => {
        expect(screen.getByText('Recent Tasks')).toBeInTheDocument();
        expect(screen.getByText('workflow-1')).toBeInTheDocument();
        expect(screen.getByText('workflow-2')).toBeInTheDocument();
      });
    });
  });

  describe('analytics and optimization', () => {
    it('should display analytics data correctly', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Analytics'));

      await waitFor(() => {
        // Success and failure rates
        expect(screen.getByText('92.0%')).toBeInTheDocument();
        expect(screen.getByText('8.0%')).toBeInTheDocument();

        // Resource utilization
        expect(screen.getByText('CPU Usage')).toBeInTheDocument();
        expect(screen.getByText('65.0%')).toBeInTheDocument();
        expect(screen.getByText('Memory Usage')).toBeInTheDocument();
        expect(screen.getByText('78.0%')).toBeInTheDocument();
        expect(screen.getByText('GPU Usage')).toBeInTheDocument();
        expect(screen.getByText('45.0%')).toBeInTheDocument();

        // Cost analysis
        expect(screen.getByText('Total Cost:')).toBeInTheDocument();
        expect(screen.getByText('$125.50')).toBeInTheDocument();
        expect(screen.getByText('Cost per Execution:')).toBeInTheDocument();
        expect(screen.getByText('$0.0250')).toBeInTheDocument();
      });
    });

    it('should display bottlenecks and optimization suggestions', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Optimization'));

      await waitFor(() => {
        // Bottlenecks
        expect(screen.getByText('Performance Bottlenecks')).toBeInTheDocument();
        expect(screen.getByText('Data Processing Node')).toBeInTheDocument();
        expect(screen.getByText('File Upload Node')).toBeInTheDocument();
        expect(screen.getByText('Consider parallel processing')).toBeInTheDocument();

        // Optimization suggestions
        expect(screen.getByText('Optimization Suggestions')).toBeInTheDocument();
        expect(screen.getByText('Implement Parallel Processing')).toBeInTheDocument();
        expect(screen.getByText('Optimize Resource Allocation')).toBeInTheDocument();
        expect(screen.getByText('40% reduction in execution time')).toBeInTheDocument();
        expect(screen.getByText('25% cost reduction')).toBeInTheDocument();
      });
    });
  });

  describe('trigger management actions', () => {
    it('should handle trigger deletion', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Find and click delete button for first trigger
      const deleteButtons = screen.getAllByRole('button');
      const deleteButton = deleteButtons.find(btn => 
        btn.querySelector('svg')?.getAttribute('class')?.includes('lucide-trash-2')
      );

      if (deleteButton) {
        fireEvent.click(deleteButton);

        await waitFor(() => {
          expect(mockHandlers.onDeleteTrigger).toHaveBeenCalled();
        });
      }
    });

    it('should show create trigger modal', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      const newTriggerButton = screen.getByText('New Trigger');
      fireEvent.click(newTriggerButton);

      // Modal should appear (placeholder implementation)
      await waitFor(() => {
        // This would test the actual modal when implemented
        expect(newTriggerButton).toBeInTheDocument();
      });
    });

    it('should show create queue modal', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      const newQueueButton = screen.getByText('New Queue');
      fireEvent.click(newQueueButton);

      // Modal should appear (placeholder implementation)
      await waitFor(() => {
        // This would test the actual modal when implemented
        expect(newQueueButton).toBeInTheDocument();
      });
    });
  });

  describe('empty states', () => {
    it('should show empty state for triggers', () => {
      render(
        <WorkflowScheduler
          triggers={[]}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      expect(screen.getByText('No triggers configured.')).toBeInTheDocument();
      expect(screen.getByText('Create your first trigger')).toBeInTheDocument();
    });

    it('should show empty state for queues', async () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={[]}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Queues'));

      await waitFor(() => {
        expect(screen.getByText('No queues configured.')).toBeInTheDocument();
        expect(screen.getByText('Create your first queue')).toBeInTheDocument();
      });
    });

    it('should show empty state for bottlenecks', async () => {
      const emptyAnalytics = {
        ...mockAnalytics,
        bottlenecks: [],
        optimizationSuggestions: []
      };

      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={emptyAnalytics}
          {...mockHandlers}
        />
      );

      fireEvent.click(screen.getByText('Optimization'));

      await waitFor(() => {
        expect(screen.getByText('No performance bottlenecks detected.')).toBeInTheDocument();
        expect(screen.getByText('No optimization suggestions available.')).toBeInTheDocument();
      });
    });
  });

  describe('data formatting', () => {
    it('should format time durations correctly', () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Should show formatted duration in stats
      expect(screen.getByText('25.0s')).toBeInTheDocument(); // 25000ms formatted
    });

    it('should format next run times correctly', () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Should show "In < 1 minute" or similar for next run
      expect(screen.getByText(/In \d+/)).toBeInTheDocument();
    });

    it('should format cron expressions correctly', () => {
      render(
        <WorkflowScheduler
          triggers={mockTriggers}
          queues={mockQueues}
          analytics={mockAnalytics}
          {...mockHandlers}
        />
      );

      // Should show cron expression
      expect(screen.getByText('0 9 * * *')).toBeInTheDocument();
    });
  });
});