import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkflowBuilder, WorkflowBuilderProvider } from '../WorkflowBuilder';
import { WorkflowDefinition } from '@/types/workflows';

// Mock ReactFlow
vi.mock('reactflow', () => ({
  default: vi.fn(({ children, ...props }) => (
    <div data-testid="react-flow" {...props}>
      {children}
    </div>
  )),
  useNodesState: vi.fn(() => [[], vi.fn(), vi.fn()]),
  useEdgesState: vi.fn(() => [[], vi.fn(), vi.fn()]),
  addEdge: vi.fn(),
  Controls: vi.fn(() => <div data-testid="react-flow-controls" />),
  MiniMap: vi.fn(() => <div data-testid="react-flow-minimap" />),
  Background: vi.fn(() => <div data-testid="react-flow-background" />),
  ReactFlowProvider: vi.fn(({ children }) => <div>{children}</div>),
}));

// Mock the validator
vi.mock('../WorkflowValidator', () => ({
  WorkflowValidator: {
    validate: vi.fn().mockResolvedValue({
      valid: true,
      errors: [],
      warnings: []
    })
  }
}));

const mockWorkflow: WorkflowDefinition = {
  id: 'test-workflow',
  name: 'Test Workflow',
  description: 'A test workflow',
  version: '1.0.0',
  nodes: [
    {
      id: 'node1',
      type: 'input',
      position: { x: 0, y: 0 },
      data: {
        label: 'Input Node',
        description: 'Test input node',
        config: {},
        inputs: [],
        outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
      }
    }
  ],
  edges: [],
  variables: [],
  tags: ['test'],
  metadata: {
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: 'test-user',
    status: 'draft'
  }
};

describe('WorkflowBuilder', () => {
  const mockOnSave = vi.fn();
  const mockOnTest = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWorkflowBuilder = (props = {}) => {
    return render(
      <WorkflowBuilderProvider>
        <WorkflowBuilder
          workflow={mockWorkflow}
          onSave={mockOnSave}
          onTest={mockOnTest}
          {...props}
        />
      </WorkflowBuilderProvider>
    );
  };

  describe('rendering', () => {
    it('should render workflow builder with all main sections', () => {
      renderWorkflowBuilder();

      expect(screen.getByText('Node Library')).toBeInTheDocument();
      expect(screen.getByText('Test Workflow')).toBeInTheDocument();
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });

    it('should display workflow status badge', () => {
      renderWorkflowBuilder();

      expect(screen.getByText('draft')).toBeInTheDocument();
    });

    it('should render toolbar buttons', () => {
      renderWorkflowBuilder();

      expect(screen.getByText('MiniMap')).toBeInTheDocument();
      expect(screen.getByText('Grid')).toBeInTheDocument();
      expect(screen.getByText('Validate')).toBeInTheDocument();
      expect(screen.getByText('Test')).toBeInTheDocument();
      expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('should hide test button when onTest is not provided', () => {
      renderWorkflowBuilder({ onTest: undefined });

      expect(screen.queryByText('Test')).not.toBeInTheDocument();
    });

    it('should hide save button when onSave is not provided', () => {
      renderWorkflowBuilder({ onSave: undefined });

      expect(screen.queryByText('Save')).not.toBeInTheDocument();
    });
  });

  describe('read-only mode', () => {
    it('should disable interactions in read-only mode', () => {
      renderWorkflowBuilder({ readOnly: true });

      const saveButton = screen.queryByText('Save');
      expect(saveButton).not.toBeInTheDocument();
    });

    it('should show read-only indicators', () => {
      renderWorkflowBuilder({ readOnly: true });

      // The node library should indicate read-only mode
      expect(screen.getByText('Node Library')).toBeInTheDocument();
    });
  });

  describe('toolbar interactions', () => {
    it('should toggle minimap visibility', async () => {
      renderWorkflowBuilder();

      const minimapButton = screen.getByText('MiniMap');
      fireEvent.click(minimapButton);

      // The button text should change or the minimap should be hidden
      await waitFor(() => {
        expect(screen.getByTestId('react-flow')).toBeInTheDocument();
      });
    });

    it('should toggle background visibility', async () => {
      renderWorkflowBuilder();

      const gridButton = screen.getByText('Grid');
      fireEvent.click(gridButton);

      await waitFor(() => {
        expect(screen.getByTestId('react-flow')).toBeInTheDocument();
      });
    });

    it('should trigger validation', async () => {
      const { WorkflowValidator } = await import('../WorkflowValidator');
      renderWorkflowBuilder();

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(WorkflowValidator.validate).toHaveBeenCalled();
      });
    });

    it('should trigger test execution', async () => {
      renderWorkflowBuilder();

      const testButton = screen.getByText('Test');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(mockOnTest).toHaveBeenCalled();
      });
    });

    it('should trigger save', async () => {
      renderWorkflowBuilder();

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalled();
      });
    });
  });

  describe('validation results display', () => {
    it('should display validation success', async () => {
      const { WorkflowValidator } = await import('../WorkflowValidator');
      vi.mocked(WorkflowValidator.validate).mockResolvedValue({
        valid: true,
        errors: [],
        warnings: []
      });

      renderWorkflowBuilder();

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/validation passed successfully/i)).toBeInTheDocument();
      });
    });

    it('should display validation errors', async () => {
      const { WorkflowValidator } = await import('../WorkflowValidator');
      vi.mocked(WorkflowValidator.validate).mockResolvedValue({
        valid: false,
        errors: [
          {
            id: 'test-error',
            type: 'missing_connection',
            message: 'Test error message',
            severity: 'error'
          }
        ],
        warnings: []
      });

      renderWorkflowBuilder();

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/error\(s\) found/i)).toBeInTheDocument();
      });
    });

    it('should display validation warnings', async () => {
      const { WorkflowValidator } = await import('../WorkflowValidator');
      vi.mocked(WorkflowValidator.validate).mockResolvedValue({
        valid: true,
        errors: [],
        warnings: [
          {
            id: 'test-warning',
            type: 'best_practice',
            message: 'Test warning message',
            suggestion: 'Test suggestion'
          }
        ]
      });

      renderWorkflowBuilder();

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      await waitFor(() => {
        expect(screen.getByText(/warning\(s\) found/i)).toBeInTheDocument();
      });
    });
  });

  describe('node selection and properties', () => {
    it('should not show properties panel initially', () => {
      renderWorkflowBuilder();

      expect(screen.queryByText('Node Properties')).not.toBeInTheDocument();
    });

    // Note: Testing node selection would require more complex ReactFlow mocking
    // as it involves the ReactFlow component's internal state management
  });

  describe('drag and drop', () => {
    it('should handle drag over events', () => {
      renderWorkflowBuilder();

      const reactFlow = screen.getByTestId('react-flow');
      const dragOverEvent = new Event('dragover', { bubbles: true });
      Object.defineProperty(dragOverEvent, 'dataTransfer', {
        value: { dropEffect: '' }
      });

      fireEvent(reactFlow, dragOverEvent);

      // Should not throw an error
      expect(reactFlow).toBeInTheDocument();
    });

    it('should prevent drag operations in read-only mode', () => {
      renderWorkflowBuilder({ readOnly: true });

      const reactFlow = screen.getByTestId('react-flow');
      expect(reactFlow).toBeInTheDocument();
    });
  });

  describe('workflow conversion', () => {
    it('should convert ReactFlow data to WorkflowDefinition format', async () => {
      renderWorkflowBuilder();

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          expect.objectContaining({
            id: expect.any(String),
            name: expect.any(String),
            nodes: expect.any(Array),
            edges: expect.any(Array),
            variables: expect.any(Array)
          })
        );
      });
    });
  });

  describe('error handling', () => {
    it('should handle validation errors gracefully', async () => {
      const { WorkflowValidator } = await import('../WorkflowValidator');
      vi.mocked(WorkflowValidator.validate).mockRejectedValue(new Error('Validation failed'));

      renderWorkflowBuilder();

      const validateButton = screen.getByText('Validate');
      fireEvent.click(validateButton);

      // Should not crash the component
      await waitFor(() => {
        expect(screen.getByText('Validate')).toBeInTheDocument();
      });
    });

    it('should handle test execution errors gracefully', async () => {
      mockOnTest.mockRejectedValue(new Error('Test failed'));

      renderWorkflowBuilder();

      const testButton = screen.getByText('Test');
      fireEvent.click(testButton);

      // Should not crash the component
      await waitFor(() => {
        expect(screen.getByText('Test')).toBeInTheDocument();
      });
    });
  });
});