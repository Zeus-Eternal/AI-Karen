import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskCreation } from '../TaskCreation';
import { Task } from '../../../types/task';

// Mock the Task type
const mockTask: Task = {
  id: 'test-task-id',
  sessionId: 'test-session-id',
  type: 'text_transform',
  title: 'Test Task',
  description: 'Test task description',
  parameters: {},
  executionMode: 'native',
  priority: 'medium',
  status: 'pending',
  createdAt: new Date(),
};

describe('TaskCreation Component', () => {
  const mockOnTaskCreated = jest.fn();
  const mockSessionId = 'test-session-id';

  beforeEach(() => {
    mockOnTaskCreated.mockClear();
  });

  it('renders without crashing', () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    expect(screen.getByText('Create New Task')).toBeInTheDocument();
  });

  it('renders form fields correctly', () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    expect(screen.getByLabelText(/Task Title \*/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description \*/)).toBeInTheDocument();
    expect(screen.getByLabelText('Task Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Execution Mode')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority')).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    const submitButton = screen.getByText('Create Task');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
      expect(screen.getByText('Description is required')).toBeInTheDocument();
    });
  });

  it('calls onTaskCreated when form is submitted with valid data', async () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/Task Title \*/), {
      target: { value: 'Test Task Title' }
    });
    
    fireEvent.change(screen.getByLabelText(/Description \*/), {
      target: { value: 'Test task description' }
    });
    
    // Submit the form
    const submitButton = screen.getByText('Create Task');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnTaskCreated).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Task Title',
          description: 'Test task description',
          sessionId: mockSessionId,
          type: 'text_transform',
          executionMode: 'native',
          priority: 'medium',
          status: 'pending',
        })
      );
    });
  });

  it('allows adding and removing tags', () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    const tagInput = screen.getByPlaceholderText('Add a tag and press Enter');
    
    // Add a tag
    fireEvent.change(tagInput, { target: { value: 'urgent' } });
    fireEvent.keyDown(tagInput, { key: 'Enter' });
    
    expect(screen.getByText('urgent')).toBeInTheDocument();
    
    // Remove the tag
    const removeButton = screen.getByLabelText('Remove urgent tag');
    fireEvent.click(removeButton);
    
    expect(screen.queryByText('urgent')).not.toBeInTheDocument();
  });

  it('disables form fields during submission', async () => {
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    // Fill in the form
    fireEvent.change(screen.getByLabelText(/Task Title \*/), {
      target: { value: 'Test Task Title' }
    });
    
    fireEvent.change(screen.getByLabelText(/Description \*/), {
      target: { value: 'Test task description' }
    });
    
    // Submit the form
    const submitButton = screen.getByText('Create Task');
    fireEvent.click(submitButton);
    
    // Check that the button is disabled during submission
    expect(screen.getByText('Creating...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('handles default parameters correctly', () => {
    const defaultParameters = { param1: 'value1', param2: 'value2' };
    
    render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated}
        defaultParameters={defaultParameters}
      />
    );
    
    expect(screen.getByDisplayValue('value1')).toBeInTheDocument();
    expect(screen.getByDisplayValue('value2')).toBeInTheDocument();
  });

  it('is accessible', () => {
    const { container } = render(
      <TaskCreation 
        sessionId={mockSessionId} 
        onTaskCreated={mockOnTaskCreated} 
      />
    );
    
    // Check for proper ARIA attributes
    expect(screen.getByLabelText(/Task Title \*/)).toHaveAttribute('aria-required', 'true');
    expect(screen.getByLabelText(/Description \*/)).toHaveAttribute('aria-required', 'true');
    
    // Check for form accessibility
    const form = container.querySelector('form');
    expect(form).toHaveAttribute('novalidate');
  });
});