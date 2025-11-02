/**
 * Dashboard Store Tests
 * 
 * Tests dashboard store functionality including persistence, templates, and filters.
 */

import { renderHook, act } from '@testing-library/react';
import { useDashboardStore } from '../dashboard-store';
import { vi } from 'vitest';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,

describe('Dashboard Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);

  describe('Dashboard Management', () => {
    it('should create a new dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          description: 'A test dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        expect(dashboardId).toBeDefined();
        expect(result.current.dashboards[dashboardId]).toBeDefined();
        expect(result.current.dashboards[dashboardId].name).toBe('Test Dashboard');
        expect(result.current.activeDashboardId).toBe(dashboardId);


    it('should update dashboard configuration', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        result.current.updateDashboard(dashboardId, {
          name: 'Updated Dashboard',
          layout: 'masonry'

        expect(result.current.dashboards[dashboardId].name).toBe('Updated Dashboard');
        expect(result.current.dashboards[dashboardId].layout).toBe('masonry');


    it('should delete dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        result.current.deleteDashboard(dashboardId);

        expect(result.current.dashboards[dashboardId]).toBeUndefined();
        expect(result.current.activeDashboardId).toBeNull();


    it('should duplicate dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const originalId = result.current.createDashboard({
          name: 'Original Dashboard',
          widgets: [
            {
              id: 'widget-1',
              type: 'metric',
              title: 'Test Widget',
              size: 'small',
              position: { x: 0, y: 0, w: 1, h: 1 },
              config: {},
              enabled: true
            }
          ],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const duplicateId = result.current.duplicateDashboard(originalId, 'Duplicate Dashboard');

        expect(duplicateId).toBeDefined();
        expect(duplicateId).not.toBe(originalId);
        expect(result.current.dashboards[duplicateId].name).toBe('Duplicate Dashboard');
        expect(result.current.dashboards[duplicateId].widgets).toHaveLength(1);
        expect(result.current.dashboards[duplicateId].widgets[0].id).not.toBe('widget-1');



  describe('Widget Management', () => {
    it('should add widget to dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const widgetId = result.current.addWidget(dashboardId, {
          type: 'metric',
          title: 'CPU Usage',
          size: 'small',
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: { metric: 'cpu_usage' },
          enabled: true

        expect(widgetId).toBeDefined();
        expect(result.current.dashboards[dashboardId].widgets).toHaveLength(1);
        expect(result.current.dashboards[dashboardId].widgets[0].id).toBe(widgetId);
        expect(result.current.dashboards[dashboardId].widgets[0].title).toBe('CPU Usage');


    it('should update widget configuration', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const widgetId = result.current.addWidget(dashboardId, {
          type: 'metric',
          title: 'CPU Usage',
          size: 'small',
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: { metric: 'cpu_usage' },
          enabled: true

        result.current.updateWidget(dashboardId, widgetId, {
          title: 'Updated CPU Usage',
          size: 'medium'

        const widget = result.current.dashboards[dashboardId].widgets[0];
        expect(widget.title).toBe('Updated CPU Usage');
        expect(widget.size).toBe('medium');


    it('should remove widget from dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const widgetId = result.current.addWidget(dashboardId, {
          type: 'metric',
          title: 'CPU Usage',
          size: 'small',
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: { metric: 'cpu_usage' },
          enabled: true

        result.current.removeWidget(dashboardId, widgetId);

        expect(result.current.dashboards[dashboardId].widgets).toHaveLength(0);


    it('should reorder widgets', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const widget1Id = result.current.addWidget(dashboardId, {
          type: 'metric',
          title: 'Widget 1',
          size: 'small',
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: {},
          enabled: true

        const widget2Id = result.current.addWidget(dashboardId, {
          type: 'metric',
          title: 'Widget 2',
          size: 'small',
          position: { x: 1, y: 0, w: 1, h: 1 },
          config: {},
          enabled: true

        // Reorder widgets
        result.current.reorderWidgets(dashboardId, [widget2Id, widget1Id]);

        const widgets = result.current.dashboards[dashboardId].widgets;
        expect(widgets[0].id).toBe(widget2Id);
        expect(widgets[1].id).toBe(widget1Id);



  describe('Template Management', () => {
    it('should create custom template', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const templateId = result.current.createTemplate({
          name: 'Custom Template',
          description: 'A custom template',
          category: 'user',
          config: {
            name: 'Custom Dashboard',
            widgets: [],
            layout: 'grid',
            refreshInterval: 30000,
            filters: []
          },
          tags: ['custom']

        expect(templateId).toBeDefined();
        expect(result.current.templates[templateId]).toBeDefined();
        expect(result.current.templates[templateId].name).toBe('Custom Template');
        expect(result.current.templates[templateId].category).toBe('user');


    it('should apply template to create new dashboard', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const templateId = result.current.createTemplate({
          name: 'Test Template',
          description: 'A test template',
          category: 'user',
          config: {
            name: 'Template Dashboard',
            widgets: [
              {
                id: 'template-widget',
                type: 'metric',
                title: 'Template Widget',
                size: 'small',
                position: { x: 0, y: 0, w: 1, h: 1 },
                config: {},
                enabled: true
              }
            ],
            layout: 'grid',
            refreshInterval: 30000,
            filters: []
          },
          tags: ['test']

        const dashboardId = result.current.applyTemplate(templateId);

        expect(dashboardId).toBeDefined();
        expect(result.current.dashboards[dashboardId]).toBeDefined();
        expect(result.current.dashboards[dashboardId].name).toBe('Template Dashboard');
        expect(result.current.dashboards[dashboardId].widgets).toHaveLength(1);
        expect(result.current.dashboards[dashboardId].widgets[0].title).toBe('Template Widget');
        expect(result.current.dashboards[dashboardId].widgets[0].id).not.toBe('template-widget');



  describe('Filter Management', () => {
    it('should manage global filters', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const filterId = result.current.addGlobalFilter({
          name: 'Status Filter',
          type: 'status',
          value: 'healthy',
          enabled: true

        expect(filterId).toBeDefined();
        expect(result.current.globalFilters).toHaveLength(1);
        expect(result.current.globalFilters[0].name).toBe('Status Filter');

        result.current.updateGlobalFilter(filterId, { value: 'warning' });
        expect(result.current.globalFilters[0].value).toBe('warning');

        result.current.removeGlobalFilter(filterId);
        expect(result.current.globalFilters).toHaveLength(0);


    it('should manage dashboard-specific filters', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        const dashboardId = result.current.createDashboard({
          name: 'Test Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const filterId = result.current.addDashboardFilter(dashboardId, {
          name: 'Category Filter',
          type: 'category',
          value: 'system',
          enabled: true

        expect(filterId).toBeDefined();
        expect(result.current.dashboards[dashboardId].filters).toHaveLength(1);
        expect(result.current.dashboards[dashboardId].filters[0].name).toBe('Category Filter');

        result.current.updateDashboardFilter(dashboardId, filterId, { value: 'performance' });
        expect(result.current.dashboards[dashboardId].filters[0].value).toBe('performance');

        result.current.removeDashboardFilter(dashboardId, filterId);
        expect(result.current.dashboards[dashboardId].filters).toHaveLength(0);


    it('should manage time range', () => {
      const { result } = renderHook(() => useDashboardStore());

      const newTimeRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-02'),
        preset: 'custom' as const
      };

      act(() => {
        result.current.setGlobalTimeRange(newTimeRange);

      expect(result.current.globalTimeRange.start).toEqual(newTimeRange.start);
      expect(result.current.globalTimeRange.end).toEqual(newTimeRange.end);
      expect(result.current.globalTimeRange.preset).toBe('custom');


  describe('Export/Import', () => {
    it('should export dashboard', async () => {
      const { result } = renderHook(() => useDashboardStore());

      await act(async () => {
        const dashboardId = result.current.createDashboard({
          name: 'Export Test',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const exportData = await result.current.exportDashboard(dashboardId);
        const parsed = JSON.parse(exportData);

        expect(parsed.version).toBe('1.0');
        expect(parsed.type).toBe('dashboard');
        expect(parsed.data.name).toBe('Export Test');


    it('should export all dashboards', async () => {
      const { result } = renderHook(() => useDashboardStore());

      await act(async () => {
        result.current.createDashboard({
          name: 'Dashboard 1',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        result.current.createDashboard({
          name: 'Dashboard 2',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []

        const exportData = await result.current.exportAllDashboards();
        const parsed = JSON.parse(exportData);

        expect(parsed.version).toBe('1.0');
        expect(parsed.type).toBe('dashboard-collection');
        expect(Object.keys(parsed.data.dashboards)).toHaveLength(2);


    it('should import dashboard', async () => {
      const { result } = renderHook(() => useDashboardStore());

      const importData = JSON.stringify({
        version: '1.0',
        type: 'dashboard',
        data: {
          name: 'Imported Dashboard',
          widgets: [
            {
              id: 'imported-widget',
              type: 'metric',
              title: 'Imported Widget',
              size: 'small',
              position: { x: 0, y: 0, w: 1, h: 1 },
              config: {},
              enabled: true
            }
          ],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []
        }

      await act(async () => {
        const dashboardId = await result.current.importDashboard(importData);

        expect(dashboardId).toBeDefined();
        expect(result.current.dashboards[dashboardId]).toBeDefined();
        expect(result.current.dashboards[dashboardId].name).toBe('Imported Dashboard (Imported)');
        expect(result.current.dashboards[dashboardId].widgets).toHaveLength(1);
        expect(result.current.dashboards[dashboardId].widgets[0].title).toBe('Imported Widget');
        expect(result.current.dashboards[dashboardId].widgets[0].id).not.toBe('imported-widget');


    it('should handle invalid import data', async () => {
      const { result } = renderHook(() => useDashboardStore());

      const invalidData = '{ "invalid": "data" }';

      await act(async () => {
        await expect(result.current.importDashboard(invalidData)).rejects.toThrow();



  describe('UI State Management', () => {
    it('should manage editing state', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        result.current.setEditing(true);

      expect(result.current.isEditing).toBe(true);

      act(() => {
        result.current.setEditing(false);

      expect(result.current.isEditing).toBe(false);
      expect(result.current.selectedWidgets).toHaveLength(0);

    it('should manage widget selection', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        result.current.setSelectedWidgets(['widget-1', 'widget-2']);

      expect(result.current.selectedWidgets).toEqual(['widget-1', 'widget-2']);

      act(() => {
        result.current.toggleWidgetSelection('widget-3');

      expect(result.current.selectedWidgets).toEqual(['widget-1', 'widget-2', 'widget-3']);

      act(() => {
        result.current.toggleWidgetSelection('widget-1');

      expect(result.current.selectedWidgets).toEqual(['widget-2', 'widget-3']);

      act(() => {
        result.current.clearSelection();

      expect(result.current.selectedWidgets).toHaveLength(0);


  describe('Persistence', () => {
    it('should persist state to localStorage', () => {
      const { result } = renderHook(() => useDashboardStore());

      act(() => {
        result.current.createDashboard({
          name: 'Persistent Dashboard',
          widgets: [],
          layout: 'grid',
          refreshInterval: 30000,
          filters: []


      // Verify localStorage.setItem was called
      expect(mockLocalStorage.setItem).toHaveBeenCalled();

    it('should restore state from localStorage', () => {
      const persistedState = {
        state: {
          dashboards: {
            'dashboard-1': {
              id: 'dashboard-1',
              name: 'Restored Dashboard',
              widgets: [],
              layout: 'grid',
              refreshInterval: 30000,
              filters: [],
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            }
          },
          templates: {},
          globalTimeRange: {
            start: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            end: new Date().toISOString(),
            preset: 'last-day'
          },
          globalFilters: [],
          autoSave: true,
          saveInterval: 30000
        },
        version: 1
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(persistedState));

      const { result } = renderHook(() => useDashboardStore());

      expect(result.current.dashboards['dashboard-1']).toBeDefined();
      expect(result.current.dashboards['dashboard-1'].name).toBe('Restored Dashboard');


