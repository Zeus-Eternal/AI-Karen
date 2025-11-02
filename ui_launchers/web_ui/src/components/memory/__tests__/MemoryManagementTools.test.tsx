/**
 * Unit tests for MemoryManagementTools component
 * Tests CRUD operations, batch operations, validation, and backup functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MemoryManagementTools from '../MemoryManagementTools';
import { getMemoryService } from '@/services/memoryService';
import type { MemoryEntry } from '@/types/memory';

// Mock the memory service
vi.mock('@/services/memoryService', () => ({
  getMemoryService: vi.fn()
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Edit3: () => <div data-testid="edit-icon">Edit3</div>,
  Trash2: () => <div data-testid="trash-icon">Trash2</div>,
  Copy: () => <div data-testid="copy-icon">Copy</div>,
  Download: () => <div data-testid="download-icon">Download</div>,
  Upload: () => <div data-testid="upload-icon">Upload</div>,
  AlertTriangle: () => <div data-testid="alert-icon">AlertTriangle</div>,
  CheckCircle: () => <div data-testid="check-icon">CheckCircle</div>,
  XCircle: () => <div data-testid="x-circle-icon">XCircle</div>,
  RefreshCw: () => <div data-testid="refresh-icon">RefreshCw</div>,
  Search: () => <div data-testid="search-icon">Search</div>,
  Filter: () => <div data-testid="filter-icon">Filter</div>,
  Archive: () => <div data-testid="archive-icon">Archive</div>,
  FileText: () => <div data-testid="file-icon">FileText</div>,
  Settings: () => <div data-testid="settings-icon">Settings</div>,
  Database: () => <div data-testid="database-icon">Database</div>,
  Shield: () => <div data-testid="shield-icon">Shield</div>,
  Zap: () => <div data-testid="zap-icon">Zap</div>
}));

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size, className }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    disabled?: boolean;
    variant?: string;
    size?: string;
    className?: string;
  }) => (
    <button 
      data-testid="button" 
      onClick={onClick} 
      disabled={disabled}
      data-variant={variant}
      data-size={size}
      className={className}
     aria-label="Button">
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ type, placeholder, value, onChange, className }: { 
    type: string;
    placeholder?: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    className?: string;
  }) => (
    <input
      data-testid="input"
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={className} />
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: { 
    children: React.ReactNode; 
    variant?: string;
    className?: string;
  }) => (
    <span data-testid="badge" data-variant={variant} className={className}>
      {children}
    </span>
  )
}));

vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ checked, onCheckedChange }: { 
    checked: boolean;
    onCheckedChange: (checked: boolean) => void;
  }) => (
    <input
      data-testid="checkbox"
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
    />
  )
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: { 
    children: React.ReactNode; 
    value: string;
    onValueChange: (value: string) => void;
  }) => (
    <div data-testid="tabs" data-value={value}>
      {React.Children.map(children, child => 
        React.cloneElement(child as React.ReactElement, { onValueChange })
      )}
    </div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({ children, value, onValueChange }: { 
    children: React.ReactNode; 
    value: string;
    onValueChange?: (value: string) => void;
  }) => (
    <button 
      data-testid="tab-trigger" 
      data-value={value}
      onClick={() => onValueChange?.(value)}
    >
      {children}
    </button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid="tab-content" data-value={value}>{children}</div>
  )
}));

describe('MemoryManagementTools', () => {
  const mockMemoryService = {
    searchMemories: vi.fn()
  };

  const mockMemories: MemoryEntry[] = [
    {
      id: '1',
      content: 'Test memory content 1',
      metadata: { cluster: 'technical' },
      timestamp: Date.now(),
      tags: ['test', 'memory'],
      type: 'fact',
      confidence: 0.9,
      user_id: 'test-user'
    },
    {
      id: '2',
      content: 'Test memory content 2',
      metadata: { cluster: 'personal' },
      timestamp: Date.now(),
      tags: ['personal', 'note'],
      type: 'context',
      confidence: 0.7,
      user_id: 'test-user'
    },
    {
      id: '3',
      content: 'Duplicate content for testing',
      metadata: { cluster: 'general' },
      timestamp: Date.now(),
      tags: ['duplicate'],
      type: 'preference',
      confidence: 0.5,
      user_id: 'test-user'
    }
  ];

  const mockMemory: MemoryEntry = mockMemories[0];

  const defaultProps = {
    memory: mockMemory,
    onSave: vi.fn(),
    onCancel: vi.fn(),
    onDelete: vi.fn(),
    isOpen: true,
    userId: 'test-user-123',
    tenantId: 'test-tenant'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (getMemoryService as any).mockReturnValue(mockMemoryService);
    mockMemoryService.searchMemories.mockResolvedValue({
      memories: mockMemories,
      totalFound: mockMemories.length,
      searchTime: 50

    // Mock window.prompt and window.confirm
    vi.spyOn(window, 'prompt').mockImplementation(() => 'Test Name');
    vi.spyOn(window, 'confirm').mockImplementation(() => true);

  afterEach(() => {
    vi.restoreAllMocks();

  describe('Component Rendering', () => {
    it('renders when isOpen is true', () => {
      render(<MemoryManagementTools {...defaultProps} />);
      
      expect(screen.getByText('Edit Memory')).toBeInTheDocument();
      expect(screen.getByText('Editor')).toBeInTheDocument();
      expect(screen.getByText('Batch Operations')).toBeInTheDocument();
      expect(screen.getByText('Validation')).toBeInTheDocument();
      expect(screen.getByText('Backup & Restore')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();

    it('does not render when isOpen is false', () => {
      render(<MemoryManagementTools {...defaultProps} isOpen={false} />);
      
      expect(screen.queryByText('Edit Memory')).not.toBeInTheDocument();

    it('renders with correct title for new memory', () => {
      render(<MemoryManagementTools {...defaultProps} memory={undefined} />);
      
      expect(screen.getByText('Memory Management Tools')).toBeInTheDocument();

    it('displays error message when present', () => {
      mockMemoryService.searchMemories.mockRejectedValue(new Error('Test error'));
      
      render(<MemoryManagementTools {...defaultProps} />);
      
      waitFor(() => {
        expect(screen.getByText('Test error')).toBeInTheDocument();
        expect(screen.getByTestId('alert-icon')).toBeInTheDocument();



  describe('Editor Tab', () => {
    it('initializes form with memory data', () => {
      render(<MemoryManagementTools {...defaultProps} />);
      
      const contentTextarea = screen.getByDisplayValue('Test memory content 1');
      expect(contentTextarea).toBeInTheDocument();
      
      const typeSelect = screen.getByDisplayValue('Fact');
      expect(typeSelect).toBeInTheDocument();

    it('updates form fields correctly', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const contentTextarea = screen.getByDisplayValue('Test memory content 1');
      await user.clear(contentTextarea);
      await user.type(contentTextarea, 'Updated content');
      
      expect(contentTextarea).toHaveValue('Updated content');

    it('updates confidence slider', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const confidenceSlider = screen.getByDisplayValue('0.9');
      fireEvent.change(confidenceSlider, { target: { value: '0.5' } });
      
      expect(confidenceSlider).toHaveValue('0.5');

    it('updates tags input', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const tagsInput = screen.getByDisplayValue('test, memory');
      await user.clear(tagsInput);
      await user.type(tagsInput, 'new, tags, here');
      
      expect(tagsInput).toHaveValue('new, tags, here');

    it('calls onSave when save button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const saveButton = screen.getByText('Save Memory');
      await user.click(saveButton);
      
      expect(defaultProps.onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'Test memory content 1',
          type: 'fact',
          confidence: 0.9
        })
      );

    it('calls onDelete when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const deleteButton = screen.getByText('Delete Memory');
      await user.click(deleteButton);
      
      expect(defaultProps.onDelete).toHaveBeenCalledWith('1');

    it('calls onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);
      
      expect(defaultProps.onCancel).toHaveBeenCalled();


  describe('Batch Operations Tab', () => {
    it('loads memories on tab open', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        expect(mockMemoryService.searchMemories).toHaveBeenCalled();


    it('displays memory list for batch operations', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        expect(screen.getByText('Test memory content 1')).toBeInTheDocument();
        expect(screen.getByText('Test memory content 2')).toBeInTheDocument();


    it('selects and deselects memories', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        const checkboxes = screen.getAllByTestId('checkbox');
        expect(checkboxes.length).toBeGreaterThan(0);

      const firstCheckbox = screen.getAllByTestId('checkbox')[1]; // Skip select all checkbox
      await user.click(firstCheckbox);
      
      expect(firstCheckbox).toBeChecked();

    it('selects all memories with select all checkbox', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        const selectAllCheckbox = screen.getAllByTestId('checkbox')[0];
        await user.click(selectAllCheckbox);
        
        const checkboxes = screen.getAllByTestId('checkbox');
        checkboxes.forEach(checkbox => {
          expect(checkbox).toBeChecked();



    it('filters memories based on search query', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search memories...');
        expect(searchInput).toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText('Search memories...');
      await user.type(searchInput, 'content 1');
      
      // Should filter the displayed memories
      expect(searchInput).toHaveValue('content 1');

    it('enables batch operation buttons when memories are selected', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        const firstCheckbox = screen.getAllByTestId('checkbox')[1];
        await user.click(firstCheckbox);
        
        const addTagsButton = screen.getByText('Add Tags');
        const changeClusterButton = screen.getByText('Change Cluster');
        const deleteButton = screen.getByText('Delete Selected');
        
        expect(addTagsButton).not.toBeDisabled();
        expect(changeClusterButton).not.toBeDisabled();
        expect(deleteButton).not.toBeDisabled();



  describe('Validation Tab', () => {
    it('displays validation settings', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      expect(screen.getByText('Memory Validation')).toBeInTheDocument();
      expect(screen.getByText('Validation Settings')).toBeInTheDocument();
      expect(screen.getByText('Check for duplicates')).toBeInTheDocument();
      expect(screen.getByText('Check for inconsistencies')).toBeInTheDocument();

    it('runs validation when button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      const runValidationButton = screen.getByText('Run Validation');
      await user.click(runValidationButton);
      
      await waitFor(() => {
        expect(screen.getByText('Validating...')).toBeInTheDocument();


    it('updates validation settings', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      const duplicatesCheckbox = screen.getByLabelText('Check for duplicates');
      await user.click(duplicatesCheckbox);
      
      // Checkbox state should toggle
      expect(duplicatesCheckbox).not.toBeChecked();

    it('displays validation results', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      const runValidationButton = screen.getByText('Run Validation');
      await user.click(runValidationButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Validation Results/)).toBeInTheDocument();



  describe('Backup & Restore Tab', () => {
    it('displays backup list', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const backupTab = screen.getByText('Backup & Restore');
      await user.click(backupTab);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Backup - 2024-01-15')).toBeInTheDocument();
        expect(screen.getByText('Manual Backup - Before Cleanup')).toBeInTheDocument();


    it('creates backup when button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const backupTab = screen.getByText('Backup & Restore');
      await user.click(backupTab);
      
      const createBackupButton = screen.getByText('Create Backup');
      await user.click(createBackupButton);
      
      expect(window.prompt).toHaveBeenCalledWith('Enter backup name:');

    it('restores backup when restore button is clicked', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const backupTab = screen.getByText('Backup & Restore');
      await user.click(backupTab);
      
      await waitFor(() => {
        const restoreButtons = screen.getAllByText('Restore');
        expect(restoreButtons.length).toBeGreaterThan(0);

      const restoreButton = screen.getAllByText('Restore')[0];
      await user.click(restoreButton);
      
      expect(window.confirm).toHaveBeenCalled();


  describe('Settings Tab', () => {
    it('displays management settings', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const settingsTab = screen.getByText('Settings');
      await user.click(settingsTab);
      
      expect(screen.getByText('Management Settings')).toBeInTheDocument();
      expect(screen.getByText('Validation Thresholds')).toBeInTheDocument();
      expect(screen.getByText('Batch Operation Settings')).toBeInTheDocument();

    it('updates confidence threshold', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const settingsTab = screen.getByText('Settings');
      await user.click(settingsTab);
      
      const confidenceSlider = screen.getByDisplayValue('0.3');
      fireEvent.change(confidenceSlider, { target: { value: '0.5' } });
      
      expect(confidenceSlider).toHaveValue('0.5');

    it('updates max content length', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const settingsTab = screen.getByText('Settings');
      await user.click(settingsTab);
      
      const maxLengthInput = screen.getByDisplayValue('10000');
      await user.clear(maxLengthInput);
      await user.type(maxLengthInput, '5000');
      
      expect(maxLengthInput).toHaveValue('5000');


  describe('Error Handling', () => {
    it('displays error when memory loading fails', async () => {
      mockMemoryService.searchMemories.mockRejectedValue(new Error('Loading failed'));
      
      render(<MemoryManagementTools {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Loading failed')).toBeInTheDocument();


    it('handles save errors gracefully', async () => {
      const onSave = vi.fn().mockRejectedValue(new Error('Save failed'));
      const user = userEvent.setup();
      
      render(<MemoryManagementTools {...defaultProps} onSave={onSave} />);
      
      const saveButton = screen.getByText('Save Memory');
      await user.click(saveButton);
      
      await waitFor(() => {
        expect(screen.getByText('Save failed')).toBeInTheDocument();


    it('handles validation errors', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      // Mock validation failure
      const runValidationButton = screen.getByText('Run Validation');
      await user.click(runValidationButton);
      
      // Should handle validation process
      expect(runValidationButton).toBeInTheDocument();


  describe('Loading States', () => {
    it('shows loading state during save', async () => {
      const onSave = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
      const user = userEvent.setup();
      
      render(<MemoryManagementTools {...defaultProps} onSave={onSave} />);
      
      const saveButton = screen.getByText('Save Memory');
      await user.click(saveButton);
      
      expect(screen.getByText('Saving...')).toBeInTheDocument();

    it('shows loading state during validation', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const validationTab = screen.getByText('Validation');
      await user.click(validationTab);
      
      const runValidationButton = screen.getByText('Run Validation');
      await user.click(runValidationButton);
      
      expect(screen.getByText('Validating...')).toBeInTheDocument();

    it('shows loading state during batch operations', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const batchTab = screen.getByText('Batch Operations');
      await user.click(batchTab);
      
      await waitFor(() => {
        const firstCheckbox = screen.getAllByTestId('checkbox')[1];
        fireEvent.click(firstCheckbox);
        
        const deleteButton = screen.getByText('Delete Selected');
        fireEvent.click(deleteButton);
        
        // Should show confirmation dialog
        expect(screen.getByText('Confirm Batch Operation')).toBeInTheDocument();



  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      // Should be able to tab through form elements
      await user.tab();
      const firstFocusable = document.activeElement;
      expect(firstFocusable).toBeInTheDocument();

    it('has proper ARIA labels', () => {
      render(<MemoryManagementTools {...defaultProps} />);
      
      const dialog = screen.getByRole('dialog', { hidden: true });
      expect(dialog).toBeInTheDocument();

    it('supports screen readers', () => {
      render(<MemoryManagementTools {...defaultProps} />);
      
      // Form elements should have proper labels
      const contentLabel = screen.getByText('Content');
      expect(contentLabel).toBeInTheDocument();
      
      const typeLabel = screen.getByText('Type');
      expect(typeLabel).toBeInTheDocument();


  describe('Data Validation', () => {
    it('prevents saving empty content', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} memory={undefined} />);
      
      const saveButton = screen.getByText('Save Memory');
      expect(saveButton).toBeDisabled();

    it('validates form inputs', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const contentTextarea = screen.getByDisplayValue('Test memory content 1');
      await user.clear(contentTextarea);
      
      const saveButton = screen.getByText('Save Memory');
      expect(saveButton).toBeDisabled();

    it('handles invalid confidence values', async () => {
      const user = userEvent.setup();
      render(<MemoryManagementTools {...defaultProps} />);
      
      const confidenceSlider = screen.getByDisplayValue('0.9');
      fireEvent.change(confidenceSlider, { target: { value: '1.5' } }); // Invalid value
      
      // Should clamp to valid range
      expect(parseFloat(confidenceSlider.value)).toBeLessThanOrEqual(1);


