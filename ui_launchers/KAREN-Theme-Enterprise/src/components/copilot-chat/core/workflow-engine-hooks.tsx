import React from 'react';
import { WorkflowEngineContext } from './workflow-engine-context';

/**
 * Hook to use the WorkflowEngine
 */
export const useWorkflowEngine = () => {
  const context = React.useContext(WorkflowEngineContext);
  if (!context) {
    throw new Error('useWorkflowEngine must be used within a WorkflowEngineProvider');
  }
  return context;
};

/**
 * Hook to get workflow status
 */
export const useWorkflowStatus = (workflowId: string) => {
  const { getWorkflowStatus } = useWorkflowEngine();
  return getWorkflowStatus(workflowId);
};

/**
 * Hook to get workflow progress
 */
export const useWorkflowProgress = (workflowId: string) => {
  const { getWorkflowProgress } = useWorkflowEngine();
  return getWorkflowProgress(workflowId);
};

/**
 * Hook to get workflow result
 */
export const useWorkflowResult = (workflowId: string) => {
  const { getWorkflowResult } = useWorkflowEngine();
  return getWorkflowResult(workflowId);
};

/**
 * Hook to get workflow templates
 */
export const useWorkflowTemplates = () => {
  const { getWorkflowTemplates } = useWorkflowEngine();
  return getWorkflowTemplates();
};

/**
 * Hook to get workflow history
 */
export const useWorkflowHistory = () => {
  const { getWorkflowHistory } = useWorkflowEngine();
  return getWorkflowHistory();
};