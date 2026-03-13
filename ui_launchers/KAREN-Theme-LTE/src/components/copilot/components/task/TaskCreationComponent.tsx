import React, { useState, useEffect } from 'react';
import { TaskPriority, TaskFormData, Theme } from './types';

interface TaskCreationComponentProps {
  theme: Theme;
  onCreateTask: (taskData: TaskFormData) => void;
  onCancel?: () => void;
  className?: string;
  initialData?: Partial<TaskFormData>;
  assignedToOptions?: string[];
  tagOptions?: string[];
  dependencyOptions?: { id: string; title: string }[];
}

export const TaskCreationComponent: React.FC<TaskCreationComponentProps> = ({
  theme,
  onCreateTask,
  onCancel,
  className = '',
  initialData = {},
  assignedToOptions = [],
  tagOptions = [],
  dependencyOptions = []
}) => {
  const [formData, setFormData] = useState<TaskFormData>({
    title: (initialData as TaskFormData).title || '',
    description: (initialData as TaskFormData).description || '',
    priority: (initialData as TaskFormData).priority || TaskPriority.MEDIUM,
    dueDate: (initialData as TaskFormData).dueDate || undefined,
    assignedTo: (initialData as TaskFormData).assignedTo || undefined,
    estimatedDuration: (initialData as TaskFormData).estimatedDuration || undefined,
    tags: (initialData as TaskFormData).tags || [],
    dependencies: (initialData as TaskFormData).dependencies || []
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [newTag, setNewTag] = useState('');
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onCreateTask(formData);
      
      // Reset form after submission
      setFormData({
        title: '',
        description: '',
        priority: TaskPriority.MEDIUM,
        dueDate: undefined,
        assignedTo: undefined,
        estimatedDuration: undefined,
        tags: [],
        dependencies: []
      });
      
      setErrors({});
    }
  };

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Handle priority change
  const handlePriorityChange = (priority: TaskPriority) => {
    setFormData(prev => ({
      ...prev,
      priority
    }));
  };

  // Handle due date change
  const handleDueDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData(prev => ({
      ...prev,
      dueDate: value ? new Date(value) : undefined
    }));
  };

  // Handle tag addition
  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags?.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), newTag.trim()]
      }));
      setNewTag('');
    }
  };

  // Handle tag removal
  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags?.filter(tag => tag !== tagToRemove) || []
    }));
  };

  // Handle tag selection from predefined options
  const handleTagSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const tag = e.target.value;
    if (tag && !formData.tags?.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tag]
      }));
      e.target.value = ''; // Reset select
    }
  };

  // Handle dependency toggle
  const handleDependencyToggle = (dependencyId: string) => {
    setFormData(prev => {
      const dependencies = prev.dependencies || [];
      if (dependencies.includes(dependencyId)) {
        return {
          ...prev,
          dependencies: dependencies.filter(id => id !== dependencyId)
        };
      } else {
        return {
          ...prev,
          dependencies: [...dependencies, dependencyId]
        };
      }
    });
  };

  // Format date for input
  const formatDateForInput = (date?: Date): string => {
    if (!date) return '';
    const isoString = date.toISOString();
    const parts = isoString.split('T');
    return parts[0] || '';
  };

  const formStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.md,
    padding: theme.spacing.lg,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.md
  };

  const inputStyle: React.CSSProperties = {
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    border: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base
  };

  const labelStyle: React.CSSProperties = {
    fontWeight: theme.typography.fontWeight.medium,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text
  };

  const errorStyle: React.CSSProperties = {
    color: theme.colors.error,
    fontSize: theme.typography.fontSize.xs,
    marginTop: theme.spacing.xs
  };

  const buttonStyle: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.borderRadius,
    border: 'none',
    cursor: 'pointer',
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base,
    fontWeight: theme.typography.fontWeight.medium,
    transition: 'all 0.2s ease'
  };

  const primaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: 'transparent',
    color: theme.colors.text,
    border: `1px solid ${theme.colors.border}`
  };

  const priorityButtonStyle = (priority: TaskPriority, isActive: boolean): React.CSSProperties => ({
    ...buttonStyle,
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    fontSize: theme.typography.fontSize.sm,
    backgroundColor: isActive ? theme.colors.primary : 'transparent',
    color: isActive ? 'white' : theme.colors.text,
    border: isActive ? 'none' : `1px solid ${theme.colors.border}`
  });

  const tagStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    backgroundColor: `${theme.colors.primary}20`,
    color: theme.colors.primary,
    borderRadius: '16px',
    fontSize: theme.typography.fontSize.xs,
    marginRight: theme.spacing.xs,
    marginBottom: theme.spacing.xs
  };

  return (
    <div className={`copilot-task-creation ${className}`} style={formStyle} role="form" aria-label="Create new task">
      <h2 style={{ margin: 0, marginBottom: theme.spacing.md, color: theme.colors.text }}>
        {(initialData as TaskFormData).title ? 'Edit Task' : 'Create New Task'}
      </h2>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.md }}>
        {/* Title */}
        <div>
          <label htmlFor="task-title" style={labelStyle}>
            Title *
          </label>
          <input
            id="task-title"
            type="text"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            style={inputStyle}
            placeholder="Enter task title"
            aria-required="true"
            aria-invalid={!!errors.title}
            aria-describedby={errors.title ? "title-error" : undefined}
          />
          {errors.title && (
            <div id="title-error" style={errorStyle} role="alert">
              {errors.title}
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label htmlFor="task-description" style={labelStyle}>
            Description *
          </label>
          <textarea
            id="task-description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            style={{ ...inputStyle, minHeight: '100px', resize: 'vertical' }}
            placeholder="Enter task description"
            aria-required="true"
            aria-invalid={!!errors.description}
            aria-describedby={errors.description ? "description-error" : undefined}
          />
          {errors.description && (
            <div id="description-error" style={errorStyle} role="alert">
              {errors.description}
            </div>
          )}
        </div>

        {/* Priority */}
        <div>
          <label style={labelStyle}>Priority</label>
          <div style={{ display: 'flex', gap: theme.spacing.sm }}>
            {Object.values(TaskPriority).map(priority => (
              <button
                key={priority}
                type="button"
                style={priorityButtonStyle(priority, formData.priority === priority)}
                onClick={() => handlePriorityChange(priority)}
                aria-pressed={formData.priority === priority}
              >
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Due Date */}
        <div>
          <label htmlFor="task-due-date" style={labelStyle}>
            Due Date
          </label>
          <div style={{ position: 'relative' }}>
            <input
              id="task-due-date"
              type="date"
              value={formatDateForInput(formData.dueDate)}
              onChange={handleDueDateChange}
              style={inputStyle}
              onFocus={() => setShowDatePicker(true)}
              onBlur={() => setTimeout(() => setShowDatePicker(false), 200)}
            />
          </div>
        </div>

        {/* Assigned To */}
        {assignedToOptions.length > 0 && (
          <div>
            <label htmlFor="task-assigned-to" style={labelStyle}>
              Assigned To
            </label>
            <select
              id="task-assigned-to"
              name="assignedTo"
              value={formData.assignedTo || ''}
              onChange={handleInputChange}
              style={inputStyle}
            >
              <option value="">Select assignee</option>
              {assignedToOptions.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Estimated Duration */}
        <div>
          <label htmlFor="task-duration" style={labelStyle}>
            Estimated Duration (minutes)
          </label>
          <input
            id="task-duration"
            type="number"
            name="estimatedDuration"
            value={formData.estimatedDuration || ''}
            onChange={handleInputChange}
            style={inputStyle}
            min="1"
            placeholder="Enter estimated duration in minutes"
          />
        </div>

        {/* Tags */}
        <div>
          <label style={labelStyle}>Tags</label>
          
          {tagOptions.length > 0 && (
            <select
              value=""
              onChange={handleTagSelect}
              style={{ ...inputStyle, marginBottom: theme.spacing.sm }}
            >
              <option value="">Add a predefined tag</option>
              {tagOptions.map(tag => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          )}
          
          <div style={{ display: 'flex', marginBottom: theme.spacing.sm }}>
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              style={{ ...inputStyle, flex: 1, marginRight: theme.spacing.sm }}
              placeholder="Add a custom tag"
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
            />
            <button
              type="button"
              onClick={handleAddTag}
              style={secondaryButtonStyle}
              disabled={!newTag.trim()}
            >
              Add
            </button>
          </div>
          
          <div>
            {formData.tags?.map(tag => (
              <span key={tag} style={tagStyle}>
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: theme.colors.primary,
                    marginLeft: theme.spacing.xs,
                    cursor: 'pointer',
                    fontSize: theme.typography.fontSize.sm,
                    padding: 0
                  }}
                  aria-label={`Remove tag: ${tag}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Dependencies */}
        {dependencyOptions.length > 0 && (
          <div>
            <label style={labelStyle}>Dependencies</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
              {dependencyOptions.map((option) => (
                <div key={option.id} style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="checkbox"
                    id={`dependency-${option.id}`}
                    checked={formData.dependencies?.includes(option.id) || false}
                    onChange={() => handleDependencyToggle(option.id)}
                    style={{ marginRight: theme.spacing.sm }}
                  />
                  <label htmlFor={`dependency-${option.id}`} style={{ margin: 0 }}>
                    {option.title}
                  </label>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: theme.spacing.sm, marginTop: theme.spacing.md }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              style={secondaryButtonStyle}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            style={primaryButtonStyle}
          >
            {initialData.title ? 'Update Task' : 'Create Task'}
          </button>
        </div>
      </form>
    </div>
  );
};