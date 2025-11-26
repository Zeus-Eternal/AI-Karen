import React from 'react';
import { CopilotWorkflow } from '../types/copilot';
import { EnhancedContext } from '../types/copilot';

interface WorkflowEngineState {
  workflows: CopilotWorkflow[];
  activeWorkflows: string[]; // IDs of active workflows
  completedWorkflows: string[]; // IDs of completed workflows
  workflowHistory: {
    workflowId: string;
    startTime: Date;
    endTime?: Date;
    status: 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
    result?: unknown;
    error?: string;
  }[];
  workflowTemplates: CopilotWorkflow[];
  isLoading: boolean;
  error: string | null;
}

interface WorkflowEngineContextType extends WorkflowEngineState {
  // Workflow management
  startWorkflow: (workflowId: string, context?: EnhancedContext) => Promise<void>;
  cancelWorkflow: (workflowId: string) => Promise<void>;
  pauseWorkflow: (workflowId: string) => Promise<void>;
  resumeWorkflow: (workflowId: string) => Promise<void>;
  
  // Workflow templates
  getWorkflowTemplates: () => CopilotWorkflow[];
  createWorkflowTemplate: (template: Omit<CopilotWorkflow, 'id'>) => Promise<string>;
  updateWorkflowTemplate: (id: string, updates: Partial<CopilotWorkflow>) => Promise<void>;
  deleteWorkflowTemplate: (id: string) => Promise<void>;
  
  // Workflow execution
  executeStep: (workflowId: string, stepIndex: number, context?: EnhancedContext) => Promise<void>;
  retryWorkflow: (workflowId: string) => Promise<void>;
  
  // Workflow state
  getWorkflowStatus: (workflowId: string) => 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  getWorkflowProgress: (workflowId: string) => number; // 0-100
  getWorkflowResult: (workflowId: string) => unknown;
  
  // Workflow history
  getWorkflowHistory: () => WorkflowEngineState['workflowHistory'];
  clearWorkflowHistory: () => void;
  
  // Error handling
  clearError: () => void;
}

const defaultWorkflowEngineState: WorkflowEngineState = {
  workflows: [],
  activeWorkflows: [],
  completedWorkflows: [],
  workflowHistory: [],
  workflowTemplates: [],
  isLoading: false,
  error: null,
};

// Create context
export const WorkflowEngineContext = React.createContext<WorkflowEngineContextType>({
  ...defaultWorkflowEngineState,
  startWorkflow: async () => {},
  cancelWorkflow: async () => {},
  pauseWorkflow: async () => {},
  resumeWorkflow: async () => {},
  getWorkflowTemplates: () => [],
  createWorkflowTemplate: async () => '',
  updateWorkflowTemplate: async () => {},
  deleteWorkflowTemplate: async () => {},
  executeStep: async () => {},
  retryWorkflow: async () => {},
  getWorkflowStatus: () => 'idle',
  getWorkflowProgress: () =>0,
  getWorkflowResult: () => null,
  getWorkflowHistory: () => [],
  clearWorkflowHistory: () => {},
  clearError: () => {},
});

export type { WorkflowEngineState, WorkflowEngineContextType };