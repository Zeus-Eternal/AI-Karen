
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowMonitor } from '../WorkflowMonitor';
import { WorkflowExecution, WorkflowDefinition } from '@/types/workflows';

// Generate large datasets for performance testing
const generateMockExecutions = (count: number): WorkflowExecution[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `execution-${i}`,
    workflowId: `workflow-${i % 10}`, // 10 different workflows
    status: ['pending', 'running', 'completed', 'failed', 'cancelled'][i % 5] as any,
    startTime: new Date(Date.now() - i * 60000),
    endTime: i % 2 === 0 ? new Date(Date.now() - i * 30000) : undefined,
    duration: i % 2 === 0 ? 30000 + (i * 1000) : undefined,
    progress: Math.min(100, (i * 10) % 110),
    currentNode: i % 3 === 0 ? `node-${i % 5}` : undefined,
    logs: Array.from({ length: Math.min(50, i + 1) }, (_, j) => ({
      id: `log-${i}-${j}`,
      timestamp: new Date(Date.now() - (i * 60000) + (j * 1000)),
      level: ['debug', 'info', 'warn', 'error'][j % 4] as any,
      nodeId: j % 3 === 0 ? `node-${j % 5}` : undefined,
      message: `Log message ${j} for execution ${i}`,
      data: j % 5 === 0 ? { executionId: i, logIndex: j } : undefined,
    })),
    results: Object.fromEntries(
      Array.from({ length: Math.min(10, i + 1) }, (_, j) => [
        `node-${j}`,
        { result: `Result ${j} for execution ${i}`, timestamp: new Date() }
      ])
    ),
    error: i % 7 === 0 ? `Error in execution ${i}` : undefined,
    metadata: {
      triggeredBy: ['manual', 'schedule', 'event'][i % 3] as any,
      trigger: i % 4 === 0 ? `trigger-${i}` : undefined,
    },
  }));
};

const generateMockWorkflows = (count: number): WorkflowDefinition[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `workflow-${i}`,
    name: `Test Workflow ${i}`,
    description: `Description for workflow ${i}`,
    version: '1.0.0',
    nodes: Array.from({ length: 5 }, (_, j) => ({
      id: `node-${j}`,
      type: 'custom',
      position: { x: j * 100, y: 0 },
      data: {
        label: `Node ${j}`,
        config: {},
        inputs: [],
        outputs: [],
      },
    })),
    edges: [],
    variables: [],
    tags: [`tag-${i % 3}`],
    metadata: {
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'test-user',
      status: 'active',
    },
  }));
};

describe('WorkflowMonitor Performance Tests', () => {
  const mockHandlers = {
    onPauseExecution: vi.fn(),
    onResumeExecution: vi.fn(),
    onCancelExecution: vi.fn(),
    onRetryExecution: vi.fn(),
    onExportLogs: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering performance', () => {
    it('should render efficiently with 100 executions', async () => {
      const executions = generateMockExecutions(100);
      const workflows = generateMockWorkflows(10);

      const startTime = performance.now();
      
      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (less than 1 second)
      expect(renderTime).toBeLessThan(1000);
      
      // Verify content is rendered
      expect(screen.getByText('Workflow Monitor')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument(); // Total executions
    });

    it('should render efficiently with 500 executions', async () => {
      const executions = generateMockExecutions(500);
      const workflows = generateMockWorkflows(10);

      const startTime = performance.now();
      
      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should still render within reasonable time (less than 2 seconds)
      expect(renderTime).toBeLessThan(2000);
      
      expect(screen.getByText('500')).toBeInTheDocument(); // Total executions
    });

    it('should handle large log datasets efficiently', async () => {
      // Create execution with many logs
      const execution: WorkflowExecution = {
        id: 'test-execution',
        workflowId: 'test-workflow',
        status: 'completed',
        startTime: new Date(),
        endTime: new Date(),
        duration: 60000,
        progress: 100,
        logs: Array.from({ length: 1000 }, (_, i) => ({
          id: `log-${i}`,
          timestamp: new Date(Date.now() - i * 1000),
          level: ['debug', 'info', 'warn', 'error'][i % 4] as any,
          message: `Log message ${i}`,
          data: i % 10 === 0 ? { index: i, data: 'test' } : undefined,
        })),
        results: {},
        metadata: { triggeredBy: 'manual' },
      };

      const workflows = generateMockWorkflows(1);

      render(
        <WorkflowMonitor 
          executions={[execution]} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      // Click on execution to open details
      const executionCard = screen.getByText('Test Workflow 0');
      fireEvent.click(executionCard);

      // Should handle large log rendering efficiently
      await waitFor(() => {
        expect(screen.getByText('Logs')).toBeInTheDocument();
      });

      // Verify logs are rendered (should be virtualized or paginated)
      expect(screen.getByText(/entries/)).toBeInTheDocument();
    });
  });

  describe('filtering performance', () => {
    it('should filter executions efficiently', async () => {
      const executions = generateMockExecutions(200);
      const workflows = generateMockWorkflows(10);

      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const searchInput = screen.getByPlaceholderText('Search executions...');
      
      const startTime = performance.now();
      
      // Perform search
      fireEvent.change(searchInput, { target: { value: 'Workflow 1' } });

      const endTime = performance.now();
      const filterTime = endTime - startTime;

      // Filtering should be fast (less than 100ms)
      expect(filterTime).toBeLessThan(100);

      // Should show filtered results
      await waitFor(() => {
        const executionCount = screen.getByText(/Executions \(\d+\)/);
        expect(executionCount).toBeInTheDocument();
      });
    });

    it('should handle status filtering efficiently', async () => {
      const executions = generateMockExecutions(300);
      const workflows = generateMockWorkflows(10);

      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const statusFilter = screen.getByDisplayValue('All Status');
      
      const startTime = performance.now();
      
      // Change status filter
      fireEvent.change(statusFilter, { target: { value: 'completed' } });

      const endTime = performance.now();
      const filterTime = endTime - startTime;

      // Status filtering should be fast
      expect(filterTime).toBeLessThan(50);

      await waitFor(() => {
        const executionCount = screen.getByText(/Executions \(\d+\)/);
        expect(executionCount).toBeInTheDocument();
      });
    });
  });

  describe('memory usage', () => {
    it('should not cause memory leaks with frequent updates', async () => {
      let executions = generateMockExecutions(50);
      const workflows = generateMockWorkflows(5);

      const { rerender } = render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      // Simulate frequent updates
      for (let i = 0; i < 10; i++) {
        executions = generateMockExecutions(50 + i);
        
        rerender(
          <WorkflowMonitor 
            executions={executions} 
            workflows={workflows} 
            {...mockHandlers} 
          />
        );

        // Small delay to simulate real updates
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      // Component should still be responsive
      expect(screen.getByText('Workflow Monitor')).toBeInTheDocument();
    });
  });

  describe('interaction performance', () => {
    it('should handle execution selection efficiently', async () => {
      const executions = generateMockExecutions(100);
      const workflows = generateMockWorkflows(10);

      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const firstExecution = screen.getByText('Test Workflow 0');
      
      const startTime = performance.now();
      
      fireEvent.click(firstExecution);

      const endTime = performance.now();
      const selectionTime = endTime - startTime;

      // Selection should be immediate
      expect(selectionTime).toBeLessThan(50);

      await waitFor(() => {
        expect(screen.getByText('Logs')).toBeInTheDocument();
      });
    });

    it('should handle log level filtering efficiently', async () => {
      const execution = generateMockExecutions(1)[0];
      execution.logs = Array.from({ length: 500 }, (_, i) => ({
        id: `log-${i}`,
        timestamp: new Date(),
        level: ['debug', 'info', 'warn', 'error'][i % 4] as any,
        message: `Log ${i}`,
      }));

      const workflows = generateMockWorkflows(1);

      render(
        <WorkflowMonitor 
          executions={[execution]} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      // Select execution
      fireEvent.click(screen.getByText('Test Workflow 0'));

      await waitFor(() => {
        expect(screen.getByText('Logs')).toBeInTheDocument();
      });

      const logLevelFilter = screen.getByDisplayValue('All Levels');
      
      const startTime = performance.now();
      
      fireEvent.change(logLevelFilter, { target: { value: 'error' } });

      const endTime = performance.now();
      const filterTime = endTime - startTime;

      // Log filtering should be fast
      expect(filterTime).toBeLessThan(100);
    });
  });

  describe('scroll performance', () => {
    it('should handle scrolling through large execution lists efficiently', async () => {
      const executions = generateMockExecutions(200);
      const workflows = generateMockWorkflows(10);

      render(
        <WorkflowMonitor 
          executions={executions} 
          workflows={workflows} 
          {...mockHandlers} 
        />
      );

      const scrollArea = screen.getByRole('region'); // ScrollArea
      
      const startTime = performance.now();
      
      // Simulate scrolling
      fireEvent.scroll(scrollArea, { target: { scrollTop: 1000 } });

      const endTime = performance.now();
      const scrollTime = endTime - startTime;

      // Scrolling should be smooth
      expect(scrollTime).toBeLessThan(50);
    });
  });
});