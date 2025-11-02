import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DashboardContainer } from '../DashboardContainer';
import type { DashboardConfig } from '@/types/dashboard';

// Mock the drag and drop components
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div data-testid="dnd-context">{children}</div>,
  DragOverlay: ({ children }: any) => <div data-testid="drag-overlay">{children}</div>,
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  PointerSensor: vi.fn(),
  closestCenter: vi.fn(),
}));

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div data-testid="sortable-context">{children}</div>,
  rectSortingStrategy: vi.fn(),
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, variant, size, disabled, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled}
      data-variant={variant}
      data-size={size}
      {...props}
    >
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className, ...props }: any) => (
    <div className={className} data-testid="card" {...props}>{children}</div>
  )
}));

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => (
    <div onClick={onClick} data-testid="dropdown-item">{children}</div>
  ),
  DropdownMenuSeparator: () => <hr data-testid="dropdown-separator" />,
  DropdownMenuTrigger: ({ children }: any) => <div data-testid="dropdown-trigger">{children}</div>
}));

// Mock the widget components
vi.mock('../WidgetBase', () => ({
  WidgetBase: ({ config, children, onRemove, isEditing }: any) => (
    <div 
      data-testid={`widget-${config.id}`}
      data-editing={isEditing}
    >
      <div>{config.title}</div>
      {children}
      {onRemove && (
        <button onClick={() => onRemove()} data-testid={`remove-${config.id}`}>
          Remove
        </button>
      )}
    </div>
  )
}));

vi.mock('../DraggableWidget', () => ({
  DraggableWidget: ({ children, id }: any) => (
    <div data-testid={`draggable-${id}`}>{children}</div>
  )
}));

vi.mock('../WidgetRegistry', () => ({
  getWidgetComponent: vi.fn((type: string) => {
    const MockWidget = ({ config }: any) => (
      <div data-testid={`${type}-widget`}>{config.title} Content</div>
    );
    return MockWidget;
  }),
  getAvailableWidgetTypes: vi.fn(() => ['metric', 'status', 'chart', 'log', 'table']),
  getWidgetInfo: vi.fn((type: string) => ({
    name: `${type.charAt(0).toUpperCase() + type.slice(1)} Widget`,
    description: `${type} widget description`,
    icon: 'Icon'
  })),
  createWidgetConfig: vi.fn((type: string, overrides = {}) => ({
    id: `widget_${type}_${Date.now()}`,
    type,
    title: `${type.charAt(0).toUpperCase() + type.slice(1)} Widget`,
    size: 'medium',
    position: { x: 0, y: 0, w: 2, h: 1 },
    config: {},
    refreshInterval: 30000,
    enabled: true,
    ...overrides
  }))
}));

const mockDashboardConfig: DashboardConfig = {
  id: 'test-dashboard',
  name: 'Test Dashboard',
  description: 'A test dashboard',
  widgets: [
    {
      id: 'widget-1',
      type: 'metric',
      title: 'CPU Usage',
      size: 'small',
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {},
      refreshInterval: 30000,
      enabled: true
    },
    {
      id: 'widget-2',
      type: 'status',
      title: 'System Status',
      size: 'medium',
      position: { x: 1, y: 0, w: 2, h: 1 },
      config: {},
      refreshInterval: 15000,
      enabled: true
    }
  ],
  layout: 'grid',
  refreshInterval: 30000,
  filters: [],
  createdAt: new Date('2023-01-01'),
  updatedAt: new Date('2023-01-01')
};

describe('DashboardContainer', () => {
  const mockOnConfigChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with title and description', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
    expect(screen.getByText('A test dashboard')).toBeInTheDocument();
  });

  it('renders all widgets', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    expect(screen.getByTestId('widget-widget-1')).toBeInTheDocument();
    expect(screen.getByTestId('widget-widget-2')).toBeInTheDocument();
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('System Status')).toBeInTheDocument();
  });

  it('shows empty state when no widgets', () => {
    const emptyConfig = { ...mockDashboardConfig, widgets: [] };
    
    render(
      <DashboardContainer
        config={emptyConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    expect(screen.getByText('No widgets added')).toBeInTheDocument();
    expect(screen.getByText('Add widgets to start building your dashboard')).toBeInTheDocument();
  });

  it('toggles edit mode', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);

    expect(screen.getByText('Save')).toBeInTheDocument();
    
    // Widgets should be in editing mode
    expect(screen.getByTestId('widget-widget-1')).toHaveAttribute('data-editing', 'true');
    expect(screen.getByTestId('widget-widget-2')).toHaveAttribute('data-editing', 'true');
  });

  it('shows add widget button in edit mode', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
        isEditing={true}
      />
    );

    expect(screen.getByText('Add Widget')).toBeInTheDocument();
  });

  it('removes widget when remove button is clicked', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    const removeButton = screen.getByTestId('remove-widget-1');
    fireEvent.click(removeButton);

    expect(mockOnConfigChange).toHaveBeenCalledWith({
      ...mockDashboardConfig,
      widgets: [mockDashboardConfig.widgets[1]], // Only second widget remains
      updatedAt: expect.any(Date)
    });
  });

  it('changes layout when layout option is selected', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
      />
    );

    // Find layout dropdown items
    const masonryLayout = screen.getByText('Masonry Layout');
    fireEvent.click(masonryLayout);

    expect(mockOnConfigChange).toHaveBeenCalledWith({
      ...mockDashboardConfig,
      layout: 'masonry'
    });
  });

  it('applies correct layout classes', () => {
    const { rerender } = render(
      <DashboardContainer
        config={{ ...mockDashboardConfig, layout: 'grid' }}
        onConfigChange={mockOnConfigChange}
      />
    );

    // Check for grid layout classes - look for the sortable context div
    let layoutContainer = screen.getByTestId('sortable-context').querySelector('div');
    expect(layoutContainer).toHaveClass('grid');

    rerender(
      <DashboardContainer
        config={{ ...mockDashboardConfig, layout: 'masonry' }}
        onConfigChange={mockOnConfigChange}
      />
    );

    layoutContainer = screen.getByTestId('sortable-context').querySelector('div');
    expect(layoutContainer).toHaveClass('columns-1');

    rerender(
      <DashboardContainer
        config={{ ...mockDashboardConfig, layout: 'flex' }}
        onConfigChange={mockOnConfigChange}
      />
    );

    layoutContainer = screen.getByTestId('sortable-context').querySelector('div');
    expect(layoutContainer).toHaveClass('flex');
  });

  it('renders draggable widgets in edit mode', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
        isEditing={true}
      />
    );

    expect(screen.getByTestId('draggable-widget-1')).toBeInTheDocument();
    expect(screen.getByTestId('draggable-widget-2')).toBeInTheDocument();
  });

  it('renders non-draggable widgets in view mode', () => {
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
        isEditing={false}
      />
    );

    expect(screen.queryByTestId('draggable-widget-1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('draggable-widget-2')).not.toBeInTheDocument();
    expect(screen.getByTestId('widget-widget-1')).toBeInTheDocument();
    expect(screen.getByTestId('widget-widget-2')).toBeInTheDocument();
  });

  it('handles unknown widget types gracefully', async () => {
    const configWithUnknownWidget = {
      ...mockDashboardConfig,
      widgets: [
        {
          id: 'unknown-widget',
          type: 'unknown' as any,
          title: 'Unknown Widget',
          size: 'small' as const,
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: {},
          refreshInterval: 30000,
          enabled: true
        }
      ]
    };

    // Mock getWidgetComponent to return null for unknown type
    const WidgetRegistry = await import('../WidgetRegistry');
    vi.mocked(WidgetRegistry.getWidgetComponent).mockImplementation((type: string) => 
      type === 'unknown' ? null : vi.fn()
    );

    render(
      <DashboardContainer
        config={configWithUnknownWidget}
        onConfigChange={mockOnConfigChange}
      />
    );

    expect(screen.getByTestId('widget-unknown-widget')).toBeInTheDocument();
  });

  it('updates dashboard config when widget is added', async () => {
    const WidgetRegistry = await import('../WidgetRegistry');
    
    render(
      <DashboardContainer
        config={mockDashboardConfig}
        onConfigChange={mockOnConfigChange}
        isEditing={true}
      />
    );

    // Find and click add widget for metric type
    const metricWidgetOption = screen.getByText('Metric Widget');
    fireEvent.click(metricWidgetOption);

    await waitFor(() => {
      expect(WidgetRegistry.createWidgetConfig).toHaveBeenCalledWith('metric', expect.any(Object));
      expect(mockOnConfigChange).toHaveBeenCalledWith({
        ...mockDashboardConfig,
        widgets: expect.arrayContaining([
          ...mockDashboardConfig.widgets,
          expect.objectContaining({
            type: 'metric',
            title: 'Metric Widget'
          })
        ]),
        updatedAt: expect.any(Date)
      });
    });
  });
});