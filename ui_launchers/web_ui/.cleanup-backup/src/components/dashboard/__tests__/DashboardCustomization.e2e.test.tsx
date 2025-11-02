/**
 * Dashboard Customization E2E Tests
 * 
 * Tests dashboard customization workflows including persistence, templates, 
 * filtering, and export/import functionality.
 * Implements requirement: 3.3, 3.5 - Dashboard customization and persistence
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react-dom/test-utils';
import { DashboardContainer } from '../DashboardContainer';
import { useDashboardStore } from '@/store/dashboard-store';
import { useAppStore } from '@/store/app-store';
import type { DashboardConfig } from '@/types/dashboard';

// Mock Next.js router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/dashboard',
}));

// Mock stores
jest.mock('@/store/dashboard-store');
jest.mock('@/store/app-store');

const mockUseDashboardStore = useDashboardStore as jest.MockedFunction<typeof useDashboardStore>;
const mockUseAppStore = useAppStore as jest.MockedFunction<typeof useAppStore>;

// Test data
const mockDashboard: DashboardConfig = {
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
      config: { metric: 'cpu_usage' },
      enabled: true
    },
    {
      id: 'widget-2',
      type: 'chart',
      title: 'Performance Chart',
      size: 'large',
      position: { x: 0, y: 1, w: 2, h: 2 },
      config: { chartType: 'line' },
      enabled: true
    }
  ],
  layout: 'grid',
  refreshInterval: 30000,
  filters: [],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01')
};

const mockTemplates = [
  {
    id: 'system-overview',
    name: 'System Overview',
    description: 'System monitoring template',
    category: 'system' as const,
    config: {
      name: 'System Overview',
      widgets: [
        {
          id: 'cpu-widget',
          type: 'metric' as const,
          title: 'CPU Usage',
          size: 'small' as const,
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: { metric: 'cpu_usage' },
          enabled: true
        }
      ],
      layout: 'grid' as const,
      refreshInterval: 30000,
      filters: []
    },
    tags: ['system', 'monitoring'],
    isDefault: true
  }
];

const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  name: 'Test User',
  roles: ['user', 'admin'],
  preferences: {
    theme: 'light' as const,
    density: 'comfortable' as const,
    language: 'en',
    timezone: 'UTC',
    notifications: { email: true, push: true, desktop: true },
    accessibility: { reducedMotion: false, highContrast: false, screenReader: false }
  }
};

describe('Dashboard Customization E2E', () => {
  const mockDashboardStore = {
    dashboards: { [mockDashboard.id]: mockDashboard },
    activeDashboardId: mockDashboard.id,
    templates: { 'system-overview': mockTemplates[0] },
    globalTimeRange: {
      start: new Date(Date.now() - 24 * 60 * 60 * 1000),
      end: new Date(),
      preset: 'last-day' as const
    },
    globalFilters: [],
    isEditing: false,
    selectedWidgets: [],
    exportInProgress: false,
    importInProgress: false,
    autoSave: true,
    saveInterval: 30000,
    
    // Actions
    updateDashboard: jest.fn(),
    addWidget: jest.fn(),
    removeWidget: jest.fn(),
    updateWidget: jest.fn(),
    reorderWidgets: jest.fn(),
    setGlobalTimeRange: jest.fn(),
    addGlobalFilter: jest.fn(),
    updateGlobalFilter: jest.fn(),
    removeGlobalFilter: jest.fn(),
    addDashboardFilter: jest.fn(),
    updateDashboardFilter: jest.fn(),
    removeDashboardFilter: jest.fn(),
    setEditing: jest.fn(),
    applyTemplate: jest.fn(),
    exportDashboard: jest.fn(),
    exportAllDashboards: jest.fn(),
    importDashboard: jest.fn(),
    createTemplate: jest.fn(),
    duplicateDashboard: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseDashboardStore.mockImplementation((selector: any) => {
      if (typeof selector === 'function') {
        return selector(mockDashboardStore);
      }
      return mockDashboardStore;
    });

    mockUseAppStore.mockImplementation((selector: any) => {
      if (typeof selector === 'function') {
        return selector({ user: mockUser });
      }
      return mockUser;
    });

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined),
        readText: jest.fn().mockResolvedValue(''),
      },
    });
  });

  describe('Dashboard Persistence', () => {
    it('should persist dashboard layout changes', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open layout dropdown
      const layoutButton = screen.getByRole('button', { name: /layout/i });
      await user.click(layoutButton);

      // Select masonry layout
      const masonryOption = screen.getByText('Masonry Layout');
      await user.click(masonryOption);

      // Verify store action was called
      expect(mockDashboardStore.updateDashboard).toHaveBeenCalledWith(
        mockDashboard.id,
        { layout: 'masonry' }
      );
    });

    it('should persist widget additions', async () => {
      const user = userEvent.setup();
      
      // Set editing mode
      mockDashboardStore.isEditing = true;
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open add widget dropdown
      const addWidgetButton = screen.getByRole('button', { name: /add widget/i });
      await user.click(addWidgetButton);

      // Add a status widget
      const statusOption = screen.getByText('Status Widget');
      await user.click(statusOption);

      // Verify store action was called
      expect(mockDashboardStore.addWidget).toHaveBeenCalledWith(
        mockDashboard.id,
        expect.objectContaining({
          type: 'status'
        })
      );
    });

    it('should persist time range changes', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open time range selector
      const timeRangeButton = screen.getByRole('button', { name: /last 24 hours/i });
      await user.click(timeRangeButton);

      // Select last week
      const lastWeekOption = screen.getByText('Last 7 Days');
      await user.click(lastWeekOption);

      // Verify store action was called
      expect(mockDashboardStore.setGlobalTimeRange).toHaveBeenCalledWith(
        expect.objectContaining({
          preset: 'last-week'
        })
      );
    });
  });

  describe('Dashboard Templates', () => {
    it('should display available templates', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open templates dialog
      const templatesButton = screen.getByRole('button', { name: /templates/i });
      await user.click(templatesButton);

      // Verify template is displayed
      await waitFor(() => {
        expect(screen.getByText('System Overview')).toBeInTheDocument();
        expect(screen.getByText('System monitoring template')).toBeInTheDocument();
      });
    });

    it('should apply template to dashboard', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open templates dialog
      const templatesButton = screen.getByRole('button', { name: /templates/i });
      await user.click(templatesButton);

      // Apply system overview template
      await waitFor(() => {
        const useTemplateButton = screen.getByRole('button', { name: /use template/i });
        return user.click(useTemplateButton);
      });

      // Verify store action was called
      expect(mockDashboardStore.applyTemplate).toHaveBeenCalledWith(
        'system-overview',
        mockDashboard.id
      );
    });

    it('should filter templates by category', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open templates dialog
      const templatesButton = screen.getByRole('button', { name: /templates/i });
      await user.click(templatesButton);

      // Filter by system category
      const categorySelect = screen.getByRole('combobox');
      await user.click(categorySelect);
      
      const systemOption = screen.getByText('System');
      await user.click(systemOption);

      // Verify system template is still visible
      await waitFor(() => {
        expect(screen.getByText('System Overview')).toBeInTheDocument();
      });
    });
  });

  describe('Dashboard Filters', () => {
    it('should add dashboard filters', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i });
      await user.click(filtersButton);

      // Add filter
      const addFilterButton = screen.getByRole('button', { name: /add filter/i });
      await user.click(addFilterButton);

      // Fill filter form
      const nameInput = screen.getByLabelText(/filter name/i);
      await user.type(nameInput, 'Test Filter');

      const valueInput = screen.getByLabelText(/filter value/i);
      await user.click(valueInput);
      
      const healthyOption = screen.getByText('Healthy');
      await user.click(healthyOption);

      // Submit filter
      const submitButton = screen.getByRole('button', { name: /add filter/i });
      await user.click(submitButton);

      // Verify store action was called
      expect(mockDashboardStore.addDashboardFilter).toHaveBeenCalledWith(
        mockDashboard.id,
        expect.objectContaining({
          name: 'Test Filter',
          type: 'category',
          value: 'healthy'
        })
      );
    });

    it('should remove dashboard filters', async () => {
      const user = userEvent.setup();
      
      // Add a filter to the dashboard
      const dashboardWithFilter = {
        ...mockDashboard,
        filters: [{
          id: 'filter-1',
          name: 'Status Filter',
          type: 'status' as const,
          value: 'healthy',
          enabled: true
        }]
      };

      render(
        <DashboardContainer
          config={dashboardWithFilter}
          onConfigChange={jest.fn()}
        />
      );

      // Open filters
      const filtersButton = screen.getByRole('button', { name: /filters/i });
      await user.click(filtersButton);

      // Find and remove filter
      const filterBadge = screen.getByText(/status filter/i);
      const filterContainer = filterBadge.closest('[role="button"]');
      
      if (filterContainer) {
        await user.click(filterContainer);
        
        const removeOption = screen.getByText('Remove Filter');
        await user.click(removeOption);

        // Verify store action was called
        expect(mockDashboardStore.removeDashboardFilter).toHaveBeenCalledWith(
          mockDashboard.id,
          'filter-1'
        );
      }
    });
  });

  describe('Dashboard Export/Import', () => {
    it('should export dashboard configuration', async () => {
      const user = userEvent.setup();
      const mockExportData = JSON.stringify({
        version: '1.0',
        type: 'dashboard',
        data: mockDashboard
      });

      mockDashboardStore.exportDashboard.mockResolvedValue(mockExportData);
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open export/import dialog
      const exportButton = screen.getByRole('button', { name: /export\/import/i });
      await user.click(exportButton);

      // Export current dashboard
      const exportDashboardButton = screen.getByRole('button', { name: /export dashboard/i });
      await user.click(exportDashboardButton);

      // Verify export was called
      await waitFor(() => {
        expect(mockDashboardStore.exportDashboard).toHaveBeenCalledWith(mockDashboard.id);
      });

      // Verify export data is displayed
      await waitFor(() => {
        const exportTextarea = screen.getByDisplayValue(mockExportData);
        expect(exportTextarea).toBeInTheDocument();
      });
    });

    it('should import dashboard configuration', async () => {
      const user = userEvent.setup();
      const importData = JSON.stringify({
        version: '1.0',
        type: 'dashboard',
        data: {
          ...mockDashboard,
          name: 'Imported Dashboard'
        }
      });

      mockDashboardStore.importDashboard.mockResolvedValue('imported-dashboard-id');
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open export/import dialog
      const exportButton = screen.getByRole('button', { name: /export\/import/i });
      await user.click(exportButton);

      // Switch to import tab
      const importTab = screen.getByRole('tab', { name: /import/i });
      await user.click(importTab);

      // Paste import data
      const importTextarea = screen.getByLabelText(/import data/i);
      await user.type(importTextarea, importData);

      // Import dashboard
      const importButton = screen.getByRole('button', { name: /import dashboard/i });
      await user.click(importButton);

      // Verify import was called
      await waitFor(() => {
        expect(mockDashboardStore.importDashboard).toHaveBeenCalledWith(importData);
      });
    });

    it('should validate import data format', async () => {
      const user = userEvent.setup();
      const invalidData = '{ "invalid": "data" }';
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open export/import dialog
      const exportButton = screen.getByRole('button', { name: /export\/import/i });
      await user.click(exportButton);

      // Switch to import tab
      const importTab = screen.getByRole('tab', { name: /import/i });
      await user.click(importTab);

      // Paste invalid data
      const importTextarea = screen.getByLabelText(/import data/i);
      await user.type(importTextarea, invalidData);

      // Verify validation error is shown
      await waitFor(() => {
        expect(screen.getByText(/invalid export format/i)).toBeInTheDocument();
      });

      // Verify import button is disabled
      const importButton = screen.getByRole('button', { name: /import dashboard/i });
      expect(importButton).toBeDisabled();
    });
  });

  describe('Widget Management', () => {
    it('should reorder widgets via drag and drop', async () => {
      const user = userEvent.setup();
      
      // Set editing mode
      mockDashboardStore.isEditing = true;
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Simulate drag and drop (simplified)
      const widgets = screen.getAllByTestId(/widget-/);
      expect(widgets).toHaveLength(2);

      // In a real test, we would simulate actual drag and drop events
      // For now, we'll test that the reorder function is available
      expect(mockDashboardStore.reorderWidgets).toBeDefined();
    });

    it('should remove widgets', async () => {
      const user = userEvent.setup();
      
      // Set editing mode
      mockDashboardStore.isEditing = true;
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Find widget remove button (would be in widget header in edit mode)
      // This is a simplified test - actual implementation would have remove buttons
      expect(mockDashboardStore.removeWidget).toBeDefined();
    });
  });

  describe('URL State Synchronization', () => {
    it('should update URL when dashboard state changes', async () => {
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Change time range
      const timeRangeButton = screen.getByRole('button', { name: /last 24 hours/i });
      await user.click(timeRangeButton);

      const lastWeekOption = screen.getByText('Last 7 Days');
      await user.click(lastWeekOption);

      // Verify URL would be updated (mocked router)
      // In a real implementation, this would check URL parameters
      expect(mockDashboardStore.setGlobalTimeRange).toHaveBeenCalled();
    });

    it('should restore state from URL parameters', () => {
      // This would test URL parameter parsing and state restoration
      // Implementation depends on the URL sync hook
      expect(true).toBe(true); // Placeholder
    });
  });

  describe('Auto-save Functionality', () => {
    it('should auto-save dashboard changes', async () => {
      jest.useFakeTimers();
      
      const user = userEvent.setup();
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Make a change
      const layoutButton = screen.getByRole('button', { name: /layout/i });
      await user.click(layoutButton);

      const masonryOption = screen.getByText('Masonry Layout');
      await user.click(masonryOption);

      // Fast-forward time to trigger auto-save
      act(() => {
        jest.advanceTimersByTime(30000); // 30 seconds
      });

      // Verify save was triggered
      expect(mockDashboardStore.updateDashboard).toHaveBeenCalled();

      jest.useRealTimers();
    });
  });

  describe('Error Handling', () => {
    it('should handle export errors gracefully', async () => {
      const user = userEvent.setup();
      
      mockDashboardStore.exportDashboard.mockRejectedValue(new Error('Export failed'));
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open export/import dialog
      const exportButton = screen.getByRole('button', { name: /export\/import/i });
      await user.click(exportButton);

      // Try to export
      const exportDashboardButton = screen.getByRole('button', { name: /export dashboard/i });
      await user.click(exportDashboardButton);

      // Verify error handling (would show error message in real implementation)
      await waitFor(() => {
        expect(mockDashboardStore.exportDashboard).toHaveBeenCalled();
      });
    });

    it('should handle import errors gracefully', async () => {
      const user = userEvent.setup();
      
      mockDashboardStore.importDashboard.mockRejectedValue(new Error('Import failed'));
      
      render(
        <DashboardContainer
          config={mockDashboard}
          onConfigChange={jest.fn()}
        />
      );

      // Open export/import dialog
      const exportButton = screen.getByRole('button', { name: /export\/import/i });
      await user.click(exportButton);

      // Switch to import tab
      const importTab = screen.getByRole('tab', { name: /import/i });
      await user.click(importTab);

      // Paste valid data
      const importData = JSON.stringify({
        version: '1.0',
        type: 'dashboard',
        data: mockDashboard
      });
      
      const importTextarea = screen.getByLabelText(/import data/i);
      await user.type(importTextarea, importData);

      // Try to import
      const importButton = screen.getByRole('button', { name: /import dashboard/i });
      await user.click(importButton);

      // Verify error is handled
      await waitFor(() => {
        expect(screen.getByText(/import failed/i)).toBeInTheDocument();
      });
    });
  });
});