import React, { useState } from 'react';
import { CopilotWorkflowSummary, SecurityContext } from '../types/backend';
import { useCopilotExecuteWorkflow, useCopilotDismissWorkflow } from '../hooks/useCopilot';

/**
 * WorkflowAutomation component
 * Provides UI for backend-provided workflows
 */
interface WorkflowAutomationProps {
  workflows: CopilotWorkflowSummary[];
  _onExecuteWorkflow: (workflow: CopilotWorkflowSummary) => void;
  _onDismissWorkflow: (workflowId: string) => void;
  securityContext: SecurityContext;
  className?: string;
}

export function WorkflowAutomation({
  workflows,
  _onExecuteWorkflow,
  _onDismissWorkflow,
  securityContext,
  className = ''
}: WorkflowAutomationProps) {
  const [selectedWorkflow, setSelectedWorkflow] = useState<CopilotWorkflowSummary | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionProgress, setExecutionProgress] = useState<number>(0);
  const [executionStatus, setExecutionStatus] = useState<string>('');
  
  const executeWorkflowHook = useCopilotExecuteWorkflow();
  const dismissWorkflowHook = useCopilotDismissWorkflow();

  // Filter workflows based on security context
  const filteredWorkflows = workflows.filter(workflow => {
    // Filter out workflows that require higher privileges than user has
    if (workflow.riskLevel === 'evil-mode-only' && securityContext.securityMode !== 'evil') {
      return false;
    }
    
    if (workflow.riskLevel === 'privileged' && !securityContext.canAccessSensitive) {
      return false;
    }
    
    return true;
  });

  // Handle workflow execution
  const handleExecuteWorkflow = async (workflow: CopilotWorkflowSummary) => {
    setIsExecuting(true);
    setExecutionProgress(0);
    setExecutionStatus('Initializing workflow...');
    
    try {
      // Simulate workflow execution progress
      const steps = workflow.steps || ['Executing workflow'];
      for (let i = 0; i < steps.length; i++) {
        setExecutionStatus(steps[i]);
        setExecutionProgress(((i + 1) / steps.length) * 100);
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Execute the actual workflow
      await executeWorkflowHook(workflow);
      setExecutionStatus('Workflow completed successfully!');
    } catch (error) {
      console.error('Error executing workflow:', error);
      setExecutionStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsExecuting(false);
      
      // Reset status after a delay
      setTimeout(() => {
        setExecutionStatus('');
        setExecutionProgress(0);
        setSelectedWorkflow(null);
      }, 3000);
    }
  };

  // Handle workflow dismissal
  const handleDismissWorkflow = (workflowId: string) => {
    dismissWorkflowHook(workflowId);
    if (selectedWorkflow && selectedWorkflow.id === workflowId) {
      setSelectedWorkflow(null);
    }
  };

  // Group workflows by risk level
  const workflowsByRisk = filteredWorkflows.reduce((groups, workflow) => {
    if (!groups[workflow.riskLevel]) {
      groups[workflow.riskLevel] = [];
    }
    groups[workflow.riskLevel].push(workflow);
    return groups;
  }, {} as Record<string, CopilotWorkflowSummary[]>);

  return (
    <div className={`workflow-automation ${className}`}>
      <div className="workflow-automation__header">
        <h2 className="workflow-automation__title">Workflow Automation</h2>
        <p className="workflow-automation__description">
          Execute automated workflows to streamline your tasks
        </p>
      </div>

      {/* Workflow Execution Status */}
      {isExecuting && selectedWorkflow && (
        <div className="workflow-automation__execution">
          <div className="workflow-automation__execution-header">
            <h3 className="workflow-automation__execution-title">
              Executing: {selectedWorkflow.name}
            </h3>
            <span className="workflow-automation__execution-risk">
              Risk: {selectedWorkflow.riskLevel}
            </span>
          </div>
          
          <div className="workflow-automation__progress-bar">
            <div 
              className="workflow-automation__progress-fill"
              style={{ width: `${executionProgress}%` }}
            ></div>
          </div>
          
          <div className="workflow-automation__execution-status">
            {executionStatus}
          </div>
        </div>
      )}

      {/* Workflow Categories */}
      <div className="workflow-automation__categories">
        {/* Safe Workflows */}
        {workflowsByRisk.safe && workflowsByRisk.safe.length > 0 && (
          <div className="workflow-automation__category">
            <h3 className="workflow-automation__category-title">Safe Workflows</h3>
            <div className="workflow-automation__category-description">
              These workflows are safe to run and will not modify critical systems
            </div>
            
            <div className="workflow-automation__workflow-list">
              {workflowsByRisk.safe.map(workflow => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  isSelected={selectedWorkflow?.id === workflow.id}
                  isExecuting={isExecuting}
                  onSelect={() => setSelectedWorkflow(workflow)}
                  onExecute={() => handleExecuteWorkflow(workflow)}
                  onDismiss={() => handleDismissWorkflow(workflow.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Privileged Workflows */}
        {workflowsByRisk.privileged && workflowsByRisk.privileged.length > 0 && (
          <div className="workflow-automation__category">
            <h3 className="workflow-automation__category-title">Privileged Workflows</h3>
            <div className="workflow-automation__category-description">
              These workflows require elevated privileges and may modify sensitive data
            </div>
            
            <div className="workflow-automation__workflow-list">
              {workflowsByRisk.privileged.map(workflow => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  isSelected={selectedWorkflow?.id === workflow.id}
                  isExecuting={isExecuting}
                  onSelect={() => setSelectedWorkflow(workflow)}
                  onExecute={() => handleExecuteWorkflow(workflow)}
                  onDismiss={() => handleDismissWorkflow(workflow.id)}
                  disabled={!securityContext.canAccessSensitive}
                />
              ))}
            </div>
          </div>
        )}

        {/* Evil Mode Workflows */}
        {workflowsByRisk['evil-mode-only'] && workflowsByRisk['evil-mode-only'].length > 0 && (
          <div className="workflow-automation__category">
            <h3 className="workflow-automation__category-title">Evil Mode Workflows</h3>
            <div className="workflow-automation__category-description">
              These workflows are highly dangerous and can cause irreversible changes
            </div>
            
            <div className="workflow-automation__workflow-list">
              {workflowsByRisk['evil-mode-only'].map(workflow => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  isSelected={selectedWorkflow?.id === workflow.id}
                  isExecuting={isExecuting}
                  onSelect={() => setSelectedWorkflow(workflow)}
                  onExecute={() => handleExecuteWorkflow(workflow)}
                  onDismiss={() => handleDismissWorkflow(workflow.id)}
                  disabled={securityContext.securityMode !== 'evil'}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* No Workflows Message */}
      {filteredWorkflows.length === 0 && (
        <div className="workflow-automation__empty">
          <p className="workflow-automation__empty-message">
            No workflows available for your current security context.
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * WorkflowCard component
 * Represents a single workflow in the list
 */
interface WorkflowCardProps {
  workflow: CopilotWorkflowSummary;
  isSelected: boolean;
  isExecuting: boolean;
  onSelect: () => void;
  onExecute: () => void;
  onDismiss: () => void;
  disabled?: boolean;
}

function WorkflowCard({ 
  workflow, 
  isSelected, 
  isExecuting, 
  onSelect, 
  onExecute, 
  onDismiss,
  disabled = false 
}: WorkflowCardProps) {
  return (
    <div 
      className={`workflow-card ${isSelected ? 'workflow-card--selected' : ''} workflow-card--${workflow.riskLevel}`}
      onClick={onSelect}
    >
      <div className="workflow-card__header">
        <h4 className="workflow-card__title">{workflow.name}</h4>
        <span className={`workflow-card__risk workflow-card__risk--${workflow.riskLevel}`}>
          {workflow.riskLevel}
        </span>
      </div>
      
      <p className="workflow-card__description">
        {workflow.description}
      </p>
      
      <div className="workflow-card__details">
        <div className="workflow-card__plugin">
          Plugin: {workflow.pluginId}
        </div>
        <div className="workflow-card__steps">
          Steps: {workflow.steps?.length || 0}
        </div>
        <div className="workflow-card__time">
          Est. time: {formatTime(workflow.estimatedTime)}
        </div>
      </div>
      
      {isSelected && (
        <div className="workflow-card__actions">
          <button
            className="workflow-card__execute-button"
            onClick={(e) => {
              e.stopPropagation();
              onExecute();
            }}
            disabled={disabled || isExecuting}
          >
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
          <button
            className="workflow-card__dismiss-button"
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
            disabled={isExecuting}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Format time in a human-readable way
 */
function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}