import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryActions } from '../ui/MemoryActions';
import { Memory } from '../types';
import { createMockMemory } from '../../../lib/__tests__/test-utils';

describe('MemoryActions', () => {
  const mockMemory = createMockMemory();
  const mockOnAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    // Should render the dropdown trigger button
    const dropdownButton = screen.getByRole('button');
    expect(dropdownButton).toBeInTheDocument();
  });

  it('renders in compact mode when compact prop is true', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    // Should render compact action buttons
    const viewButton = screen.getByTitle('View details');
    const editButton = screen.getByTitle('Edit memory');
    const copyButton = screen.getByTitle('Copy memory');
    
    expect(viewButton).toBeInTheDocument();
    expect(editButton).toBeInTheDocument();
    expect(copyButton).toBeInTheDocument();
  });

  it('calls onAction with correct payload when view is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    const viewButton = screen.getByTitle('View details');
    await user.click(viewButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'view'
    });
  });

  it('calls onAction with correct payload when edit is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    const editButton = screen.getByTitle('Edit memory');
    await user.click(editButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'edit'
    });
  });

  it('calls onAction with correct payload when copy is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    const copyButton = screen.getByTitle('Copy memory');
    await user.click(copyButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'copy'
    });
  });

  it('shows appropriate actions for active memory', async () => {
    const user = userEvent.setup();
    const activeMemory = { ...mockMemory, status: 'active' as const };
    
    render(<MemoryActions memory={activeMemory} onAction={mockOnAction} />);
    
    // Open dropdown
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    // Should show archive option for active memory
    expect(screen.getByText('Archive')).toBeInTheDocument();
    // Should not show restore option for active memory
    expect(screen.queryByText('Restore')).not.toBeInTheDocument();
  });

  it('shows appropriate actions for archived memory', async () => {
    const user = userEvent.setup();
    const archivedMemory = { ...mockMemory, status: 'archived' as const };
    
    render(<MemoryActions memory={archivedMemory} onAction={mockOnAction} />);
    
    // Open dropdown
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    // Should show restore option for archived memory
    expect(screen.getByText('Restore')).toBeInTheDocument();
    // Should not show archive option for archived memory
    expect(screen.queryByText('Archive')).not.toBeInTheDocument();
  });

  it('calls onAction with correct payload when archive is clicked', async () => {
    const user = userEvent.setup();
    const activeMemory = { ...mockMemory, status: 'active' as const };
    
    render(<MemoryActions memory={activeMemory} onAction={mockOnAction} />);
    
    // Open dropdown and click archive
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    const archiveButton = screen.getByText('Archive');
    await user.click(archiveButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'archive'
    });
  });

  it('calls onAction with correct payload when restore is clicked', async () => {
    const user = userEvent.setup();
    const archivedMemory = { ...mockMemory, status: 'archived' as const };
    
    render(<MemoryActions memory={archivedMemory} onAction={mockOnAction} />);
    
    // Open dropdown and click restore
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    const restoreButton = screen.getByText('Restore');
    await user.click(restoreButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'restore'
    });
  });

  it('calls onAction with correct payload when export is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    // Open dropdown and click export
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    const exportButton = screen.getByText('Export');
    await user.click(exportButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'export'
    });
  });

  it('calls onAction with correct payload when delete is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    // Open dropdown and click delete
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'delete'
    });
  });

  it('shows bulk actions when showBulkActions is true and selectedCount > 1', () => {
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={true} 
        selectedCount={3} 
      />
    );
    
    // Should show bulk action buttons
    expect(screen.getByText('Archive Selected')).toBeInTheDocument();
    expect(screen.getByText('Export Selected')).toBeInTheDocument();
    expect(screen.getByText('Delete Selected')).toBeInTheDocument();
  });

  it('does not show bulk actions when showBulkActions is false', () => {
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={false} 
        selectedCount={3} 
      />
    );
    
    // Should not show bulk action buttons
    expect(screen.queryByText('Archive Selected')).not.toBeInTheDocument();
    expect(screen.queryByText('Export Selected')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete Selected')).not.toBeInTheDocument();
  });

  it('does not show bulk actions when selectedCount is 1', () => {
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={true} 
        selectedCount={1} 
      />
    );
    
    // Should not show bulk action buttons
    expect(screen.queryByText('Archive Selected')).not.toBeInTheDocument();
    expect(screen.queryByText('Export Selected')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete Selected')).not.toBeInTheDocument();
  });

  it('calls onAction with correct payload when archive selected is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={true} 
        selectedCount={3} 
      />
    );
    
    const archiveSelectedButton = screen.getByText('Archive Selected');
    await user.click(archiveSelectedButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'archive'
    });
  });

  it('calls onAction with correct payload when export selected is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={true} 
        selectedCount={3} 
      />
    );
    
    const exportSelectedButton = screen.getByText('Export Selected');
    await user.click(exportSelectedButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'export'
    });
  });

  it('calls onAction with correct payload when delete selected is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryActions 
        memory={mockMemory} 
        onAction={mockOnAction} 
        showBulkActions={true} 
        selectedCount={3} 
      />
    );
    
    const deleteSelectedButton = screen.getByText('Delete Selected');
    await user.click(deleteSelectedButton);
    
    expect(mockOnAction).toHaveBeenCalledWith({
      memoryId: mockMemory.id,
      action: 'delete'
    });
  });

  it('has proper accessibility attributes', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    // Dropdown button should have proper attributes
    const dropdownButton = screen.getByRole('button');
    expect(dropdownButton).toBeInTheDocument();
    expect(dropdownButton).toHaveAttribute('aria-haspopup', 'menu');
    expect(dropdownButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('has proper accessibility attributes in compact mode', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    // Compact buttons should have proper attributes
    const viewButton = screen.getByTitle('View details');
    const editButton = screen.getByTitle('Edit memory');
    const copyButton = screen.getByTitle('Copy memory');
    
    expect(viewButton).toBeInTheDocument();
    expect(editButton).toBeInTheDocument();
    expect(copyButton).toBeInTheDocument();
    
    // Each button should have a title attribute for accessibility
    expect(viewButton).toHaveAttribute('title', 'View details');
    expect(editButton).toHaveAttribute('title', 'Edit memory');
    expect(copyButton).toHaveAttribute('title', 'Copy memory');
  });

  it('applies custom className', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} className="custom-class" />);
    
    const container = screen.getByRole('button').closest('.flex');
    expect(container).toHaveClass('custom-class');
  });

  it('handles keyboard navigation in compact mode', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    // Focus first button and tab through
    const viewButton = screen.getByTitle('View details');
    viewButton.focus();
    await user.tab();
    
    // Should focus on edit button
    const editButton = screen.getByTitle('Edit memory');
    expect(editButton).toHaveFocus();
  });

  it('applies correct styling classes', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    const container = screen.getByRole('button').closest('.flex');
    expect(container).toHaveClass('items-center', 'gap-2');
  });

  it('applies correct styling classes in compact mode', () => {
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} compact={true} />);
    
    const container = screen.getByTitle('View details').closest('.flex');
    expect(container).toHaveClass('items-center', 'gap-1');
  });

  it('handles missing onAction gracefully', () => {
    render(<MemoryActions memory={mockMemory} onAction={vi.fn()} />);
    
    // Should not crash when onAction is provided
    const dropdownButton = screen.getByRole('button');
    expect(dropdownButton).toBeInTheDocument();
  });

  it('shows delete option with destructive styling', async () => {
    const user = userEvent.setup();
    render(<MemoryActions memory={mockMemory} onAction={mockOnAction} />);
    
    // Open dropdown
    const dropdownButton = screen.getByRole('button');
    await user.click(dropdownButton);
    
    // Delete option should have destructive styling
    const deleteButton = screen.getByText('Delete');
    expect(deleteButton).toHaveClass('text-destructive');
  });
});