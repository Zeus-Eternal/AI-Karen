import React, { useState, useEffect } from 'react';
import { Task, TaskType, ExecutionMode, TaskPriority, TaskCreationParams } from '../../types/task';

/**
 * TaskCreation Component
 * 
 * Provides an interface for users to create new tasks with various
 * parameters including task type, title, description, and execution mode.
 * 
 * @component
 * @example
 * ```tsx
 * <TaskCreation 
 *   sessionId="user-session-123"
 *   onTaskCreated={(task) => console.log('Task created:', task)}
 * />
 * ```
 */
export const TaskCreation: React.FC<TaskCreationProps> = ({ 
  sessionId,
  onTaskCreated,
  className = '',
  defaultParameters = {}
}) => {
  const [formState, setFormState] = useState({
    type: 'text_transform' as TaskType,
    title: '',
    description: '',
    parameters: defaultParameters,
    executionMode: 'native' as ExecutionMode,
    priority: 'medium' as TaskPriority,
    tags: [] as string[],
    errors: {} as Record<string, string>,
    isSubmitting: false
  });

  const [tagInput, setTagInput] = useState('');

  const handleInputChange = (field: string, value: any) => {
    setFormState(prev => ({
      ...prev,
      [field]: value,
      errors: { ...prev.errors, [field]: '' }
    }));
  };

  const handleParameterChange = (key: string, value: any) => {
    setFormState(prev => ({
      ...prev,
      parameters: { ...prev.parameters, [key]: value }
    }));
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formState.tags.includes(tagInput.trim())) {
      setFormState(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormState(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!formState.title.trim()) {
      errors.title = 'Title is required';
    }
    
    if (!formState.description.trim()) {
      errors.description = 'Description is required';
    }
    
    setFormState(prev => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setFormState(prev => ({ ...prev, isSubmitting: true }));
    
    try {
      const newTask: Task = {
        id: `task-${Date.now()}`,
        sessionId,
        type: formState.type,
        title: formState.title,
        description: formState.description,
        parameters: formState.parameters,
        executionMode: formState.executionMode,
        priority: formState.priority,
        status: 'pending',
        createdAt: new Date(),
        tags: formState.tags
      };
      
      // In a real implementation, this would call an API to create the task
      // For now, we'll simulate the API call with a timeout
      await new Promise(resolve => setTimeout(resolve, 500));
      
      onTaskCreated(newTask);
      
      // Reset form
      setFormState(prev => ({
        ...prev,
        title: '',
        description: '',
        parameters: defaultParameters,
        tags: [],
        isSubmitting: false
      }));
    } catch (error) {
      console.error('Error creating task:', error);
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        errors: { ...prev.errors, submit: 'Failed to create task' }
      }));
    }
  };

  return (
    <div className={`task-creation ${className}`}>
      <h3>Create New Task</h3>
      
      <form onSubmit={handleSubmit} className="task-creation-form" noValidate>
        <div className="form-group">
          <label htmlFor="task-title">Task Title *</label>
          <input
            id="task-title"
            type="text"
            value={formState.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            className={formState.errors.title ? 'error' : ''}
            aria-required="true"
            aria-invalid={!!formState.errors.title}
            aria-describedby={formState.errors.title ? 'title-error' : undefined}
            disabled={formState.isSubmitting}
          />
          {formState.errors.title && (
            <div id="title-error" className="error-message" role="alert">
              {formState.errors.title}
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="task-description">Description *</label>
          <textarea
            id="task-description"
            value={formState.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            className={formState.errors.description ? 'error' : ''}
            aria-required="true"
            aria-invalid={!!formState.errors.description}
            aria-describedby={formState.errors.description ? 'description-error' : undefined}
            disabled={formState.isSubmitting}
            rows={3}
          />
          {formState.errors.description && (
            <div id="description-error" className="error-message" role="alert">
              {formState.errors.description}
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="task-type">Task Type</label>
          <select
            id="task-type"
            value={formState.type}
            onChange={(e) => handleInputChange('type', e.target.value as TaskType)}
            disabled={formState.isSubmitting}
          >
            <option value="text_transform">Text Transform</option>
            <option value="code_analysis">Code Analysis</option>
            <option value="file_operation">File Operation</option>
            <option value="data_processing">Data Processing</option>
            <option value="research">Research</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="execution-mode">Execution Mode</label>
          <select
            id="execution-mode"
            value={formState.executionMode}
            onChange={(e) => handleInputChange('executionMode', e.target.value as ExecutionMode)}
            disabled={formState.isSubmitting}
          >
            <option value="native">Native Mode</option>
            <option value="deepagents">DeepAgents Mode</option>
            <option value="langgraph">LangGraph Mode</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="task-priority">Priority</label>
          <select
            id="task-priority"
            value={formState.priority}
            onChange={(e) => handleInputChange('priority', e.target.value as TaskPriority)}
            disabled={formState.isSubmitting}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="form-group">
          <label>Parameters</label>
          <div className="task-parameters">
            {Object.entries(formState.parameters).map(([key, value]) => (
              <div key={key} className="parameter-input">
                <label htmlFor={`param-${key}`}>{key}</label>
                <input
                  id={`param-${key}`}
                  type="text"
                  value={String(value)}
                  onChange={(e) => handleParameterChange(key, e.target.value)}
                  disabled={formState.isSubmitting}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="tag-input">Tags</label>
          <div className="tag-input-container">
            <input
              id="tag-input"
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
              placeholder="Add a tag and press Enter"
              disabled={formState.isSubmitting}
            />
            <button
              type="button"
              onClick={handleAddTag}
              disabled={!tagInput.trim() || formState.tags.includes(tagInput.trim()) || formState.isSubmitting}
              aria-label="Add tag"
            >
              Add
            </button>
          </div>
          <div className="tag-list">
            {formState.tags.map(tag => (
              <span key={tag} className="tag">
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  aria-label={`Remove ${tag} tag`}
                  disabled={formState.isSubmitting}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {formState.errors.submit && (
          <div className="error-message" role="alert">
            {formState.errors.submit}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={formState.isSubmitting}
            aria-busy={formState.isSubmitting}
          >
            {formState.isSubmitting ? 'Creating...' : 'Create Task'}
          </button>
        </div>
      </form>
    </div>
  );
};

interface TaskCreationProps {
  /** Unique identifier for the user session */
  sessionId: string;
  /** Callback when a task is created */
  onTaskCreated: (task: Task) => void;
  /** Additional CSS classes for styling */
  className?: string;
  /** Default parameters for the task */
  defaultParameters?: Record<string, any>;
}