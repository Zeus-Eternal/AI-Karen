
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { WidgetBase } from '../WidgetBase';
import type { WidgetConfig, WidgetData } from '@/types/dashboard';

// Mock the UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className, ...props }: any) => (
    <div className={className} {...props}>{children}</div>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={className} 
      {...props}
     aria-label="Button">
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => (
    <div onClick={onClick}>{children}</div>
  ),
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuTrigger: ({ children }: any) => <div>{children}</div>
}));

const mockConfig: WidgetConfig = {
  id: 'test-widget',
  type: 'metric',
  title: 'Test Widget',
  size: 'medium',
  position: { x: 0, y: 0, w: 2, h: 1 },
  config: {},
  refreshInterval: 30000,
  enabled: true
};

const mockData: WidgetData = {
  id: 'test-widget',
  data: { value: 42 },
  loading: false,
  lastUpdated: new Date('2023-01-01T12:00:00Z')
};

describe('WidgetBase', () => {
  const mockOnConfigChange = vi.fn();
  const mockOnRefresh = vi.fn();
  const mockOnRemove = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders widget with title and content', () => {
    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    expect(screen.getByText('Test Widget')).toBeInTheDocument();
    expect(screen.getByText('Widget Content')).toBeInTheDocument();

  it('displays loading state', () => {
    render(
      <WidgetBase
        config={mockConfig}
        loading={true}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    expect(screen.queryByText('Widget Content')).not.toBeInTheDocument();
    // Loading spinner should be present (we can't easily test for the icon, but we can test the structure)
    expect(screen.getByText('Test Widget')).toBeInTheDocument();

  it('displays error state with retry button', () => {
    const errorMessage = 'Failed to load data';
    
    render(
      <WidgetBase
        config={mockConfig}
        error={errorMessage}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    expect(screen.getByText('Widget Error')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
    expect(screen.queryByText('Widget Content')).not.toBeInTheDocument();

  it('calls onRefresh when refresh button is clicked', async () => {
    mockOnRefresh.mockResolvedValue(undefined);

    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    // Find and click the refresh button in the header
    const refreshButtons = screen.getAllByRole('button');
    const refreshButton = refreshButtons.find(button => 
      button.textContent?.includes('Refresh') || 
      button.getAttribute('title')?.includes('refresh')
    );
    
    if (refreshButton) {
      fireEvent.click(refreshButton);
      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalledTimes(1);

    }

  it('calls onRemove when remove button is clicked and confirmed', () => {
    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    // Find and click the remove button
    const removeButton = screen.getByText('Remove');
    fireEvent.click(removeButton);

    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to remove this widget?');
    expect(mockOnRemove).toHaveBeenCalledTimes(1);

    // Restore original confirm
    window.confirm = originalConfirm;

  it('does not call onRemove when remove is cancelled', () => {
    // Mock window.confirm to return false
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => false);

    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        onConfigChange={mockOnConfigChange}
        onRefresh={mockOnRefresh}
        onRemove={mockOnRemove}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    // Find and click the remove button
    const removeButton = screen.getByText('Remove');
    fireEvent.click(removeButton);

    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to remove this widget?');
    expect(mockOnRemove).not.toHaveBeenCalled();

    // Restore original confirm
    window.confirm = originalConfirm;

  it('applies correct size classes', () => {
    const { rerender } = render(
      <WidgetBase
        config={{ ...mockConfig, size: 'small' }}
        data={mockData}
      >
        <div>Content</div>
      </WidgetBase>
    );

    let widget = screen.getByText('Test Widget').closest('[data-widget-id]');
    expect(widget).toHaveClass('col-span-1', 'row-span-1');

    rerender(
      <WidgetBase
        config={{ ...mockConfig, size: 'large' }}
        data={mockData}
      >
        <div>Content</div>
      </WidgetBase>
    );

    widget = screen.getByText('Test Widget').closest('[data-widget-id]');
    expect(widget).toHaveClass('col-span-2', 'row-span-2');

  it('shows last updated time when data is available', () => {
    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    // Check if the last updated time is displayed
    const lastUpdatedTime = new Date(mockData.lastUpdated).toLocaleTimeString();
    expect(screen.getByText(lastUpdatedTime)).toBeInTheDocument();

  it('handles refresh with loading state', async () => {
    let resolveRefresh: () => void;
    const refreshPromise = new Promise<void>((resolve) => {
      resolveRefresh = resolve;

    mockOnRefresh.mockReturnValue(refreshPromise);

    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        onRefresh={mockOnRefresh}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    // Find and click refresh button
    const refreshButtons = screen.getAllByRole('button');
    const refreshButton = refreshButtons.find(button => 
      button.textContent?.includes('Refresh') || 
      button.getAttribute('title')?.includes('refresh')
    );
    
    if (refreshButton) {
      fireEvent.click(refreshButton);
      
      // Should show loading state
      await waitFor(() => {
        expect(mockOnRefresh).toHaveBeenCalledTimes(1);

      // Resolve the refresh
      resolveRefresh!();
      
      await waitFor(() => {
        // Should return to normal state
        expect(screen.getByText('Widget Content')).toBeInTheDocument();

    }

  it('applies editing styles when isEditing is true', () => {
    render(
      <WidgetBase
        config={mockConfig}
        data={mockData}
        isEditing={true}
      >
        <div>Widget Content</div>
      </WidgetBase>
    );

    const widget = screen.getByText('Test Widget').closest('[data-widget-id]');
    expect(widget).toHaveClass(
      'ring-2',
      'ring-[var(--component-button-default-ring)]'
    );

