/**
 * Dashboard URL State Synchronization Hook
 * 
 * Synchronizes dashboard state with URL parameters for bookmarking and sharing.
 * Implements requirement: 3.3 - URL state synchronization
 */
import { useEffect, useCallback } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useDashboardStore, type TimeRange } from '@/store/dashboard-store';
import type { DashboardFilter } from '@/types/dashboard';

export interface DashboardUrlState {
  dashboardId?: string;
  timeRange?: {
    start: string;
    end: string;
    preset?: string;
  };
  filters?: string; // JSON encoded filters
  layout?: 'grid' | 'masonry' | 'flex';
  editing?: boolean;
}

export const useDashboardUrlSync = () => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const {
    activeDashboardId,
    setActiveDashboard,
    globalTimeRange,
    setGlobalTimeRange,
    globalFilters,
    addGlobalFilter,
    updateGlobalFilter,
    removeGlobalFilter,
    clearGlobalFilters,
    isEditing,
    setEditing,
    dashboards,
    updateDashboard
  } = useDashboardStore();

  // Parse URL parameters into dashboard state
  const parseUrlState = useCallback((): DashboardUrlState => {
    const params = new URLSearchParams(searchParams.toString());
    const state: DashboardUrlState = {};

    // Dashboard ID
    const dashboardId = params.get('dashboard');
    if (dashboardId) {
      state.dashboardId = dashboardId;
    }

    // Time range
    const timeStart = params.get('timeStart');
    const timeEnd = params.get('timeEnd');
    const timePreset = params.get('timePreset');
    if (timeStart && timeEnd) {
      state.timeRange = {
        start: timeStart,
        end: timeEnd,
        preset: timePreset || undefined
      };
    }

    // Filters
    const filtersParam = params.get('filters');
    if (filtersParam) {
      try {
        JSON.parse(decodeURIComponent(filtersParam));
        state.filters = filtersParam;
      } catch (error) {}
    }

    // Layout
    const layout = params.get('layout');
    if (layout && ['grid', 'masonry', 'flex'].includes(layout)) {
      state.layout = layout as 'grid' | 'masonry' | 'flex';
    }

    // Editing mode
    const editing = params.get('editing');
    if (editing === 'true') {
      state.editing = true;
    }

    return state;
  }, [searchParams]);

  // Update URL with current dashboard state
  const updateUrl = useCallback((updates: Partial<DashboardUrlState>) => {
    const params = new URLSearchParams(searchParams.toString());

    // Update dashboard ID
    if (updates.dashboardId !== undefined) {
      if (updates.dashboardId) {
        params.set('dashboard', updates.dashboardId);
      } else {
        params.delete('dashboard');
      }
    }

    // Update time range
    if (updates.timeRange !== undefined) {
      if (updates.timeRange) {
        params.set('timeStart', updates.timeRange.start);
        params.set('timeEnd', updates.timeRange.end);
        if (updates.timeRange.preset) {
          params.set('timePreset', updates.timeRange.preset);
        } else {
          params.delete('timePreset');
        }
      } else {
        params.delete('timeStart');
        params.delete('timeEnd');
        params.delete('timePreset');
      }
    }

    // Update filters
    if (updates.filters !== undefined) {
      if (updates.filters) {
        params.set('filters', updates.filters);
      } else {
        params.delete('filters');
      }
    }

    // Update layout
    if (updates.layout !== undefined) {
      if (updates.layout) {
        params.set('layout', updates.layout);
      } else {
        params.delete('layout');
      }
    }

    // Update editing mode
    if (updates.editing !== undefined) {
      if (updates.editing) {
        params.set('editing', 'true');
      } else {
        params.delete('editing');
      }
    }

    const newUrl = `${pathname}?${params.toString()}`;
    router.replace(newUrl, { scroll: false });
  }, [router, pathname, searchParams]);

  // Sync URL state to store on mount and URL changes
  useEffect(() => {
    const urlState = parseUrlState();

    // Set active dashboard
    if (urlState.dashboardId && urlState.dashboardId !== activeDashboardId) {
      if (dashboards[urlState.dashboardId]) {
        setActiveDashboard(urlState.dashboardId);
      }
    }

    // Set time range
    if (urlState.timeRange) {
      const timeRange: TimeRange = {
        start: new Date(urlState.timeRange.start),
        end: new Date(urlState.timeRange.end),
        preset: urlState.timeRange.preset as any
      };

      // Only update if different
      if (
        timeRange.start.getTime() !== globalTimeRange.start.getTime() ||
        timeRange.end.getTime() !== globalTimeRange.end.getTime() ||
        timeRange.preset !== globalTimeRange.preset
      ) {
        setGlobalTimeRange(timeRange);
      }
    }

    // Set filters
    if (urlState.filters) {
      try {
        const filters: DashboardFilter[] = JSON.parse(decodeURIComponent(urlState.filters));

        // Compare with current filters
        const currentFiltersJson = JSON.stringify(globalFilters);
        const urlFiltersJson = JSON.stringify(filters);

        if (currentFiltersJson !== urlFiltersJson) {
          clearGlobalFilters();
          filters.forEach(filter => {
            addGlobalFilter(filter);
          });
        }
      } catch (error) {}
    }

    // Set layout
    if (urlState.layout && activeDashboardId) {
      const currentDashboard = dashboards[activeDashboardId];
      if (currentDashboard && currentDashboard.layout !== urlState.layout) {
        updateDashboard(activeDashboardId, { layout: urlState.layout });
      }
    }

    // Set editing mode
    if (urlState.editing !== undefined && urlState.editing !== isEditing) {
      setEditing(urlState.editing);
    }
  }, [
    parseUrlState,
    activeDashboardId,
    setActiveDashboard,
    dashboards,
    globalTimeRange,
    setGlobalTimeRange,
    globalFilters,
    addGlobalFilter,
    clearGlobalFilters,
    updateDashboard,
    isEditing,
    setEditing
  ]);

  // Sync store state to URL
  useEffect(() => {
    const urlState = parseUrlState();
    const updates: Partial<DashboardUrlState> = {};

    // Check dashboard ID
    if (activeDashboardId !== urlState.dashboardId) {
      updates.dashboardId = activeDashboardId || undefined;
    }

    // Check time range
    const currentTimeRange = {
      start: globalTimeRange.start.toISOString(),
      end: globalTimeRange.end.toISOString(),
      preset: globalTimeRange.preset
    };

    if (
      !urlState.timeRange ||
      urlState.timeRange.start !== currentTimeRange.start ||
      urlState.timeRange.end !== currentTimeRange.end ||
      urlState.timeRange.preset !== currentTimeRange.preset
    ) {
      updates.timeRange = currentTimeRange;
    }

    // Check filters
    const currentFiltersJson = encodeURIComponent(JSON.stringify(globalFilters));
    if (urlState.filters !== currentFiltersJson) {
      updates.filters = globalFilters.length > 0 ? currentFiltersJson : undefined;
    }

    // Check layout
    if (activeDashboardId) {
      const currentDashboard = dashboards[activeDashboardId];
      if (currentDashboard && currentDashboard.layout !== urlState.layout) {
        updates.layout = currentDashboard.layout;
      }
    }

    // Check editing mode
    if (isEditing !== urlState.editing) {
      updates.editing = isEditing || undefined;
    }

    // Update URL if there are changes
    if (Object.keys(updates).length > 0) {
      updateUrl(updates);
    }
  }, [
    activeDashboardId,
    globalTimeRange,
    globalFilters,
    isEditing,
    dashboards,
    parseUrlState,
    updateUrl
  ]);

  // Utility functions for manual URL updates
  const setDashboardInUrl = useCallback((dashboardId: string | null) => {
    updateUrl({ dashboardId: dashboardId || undefined });
  }, [updateUrl]);

  const setTimeRangeInUrl = useCallback((timeRange: TimeRange) => {
    updateUrl({
      timeRange: {
        start: timeRange.start.toISOString(),
        end: timeRange.end.toISOString(),
        preset: timeRange.preset
      }
    });
  }, [updateUrl]);

  const setFiltersInUrl = useCallback((filters: DashboardFilter[]) => {
    updateUrl({
      filters: filters.length > 0 ? encodeURIComponent(JSON.stringify(filters)) : undefined
    });
  }, [updateUrl]);

  const setLayoutInUrl = useCallback((layout: 'grid' | 'masonry' | 'flex') => {
    updateUrl({ layout });
  }, [updateUrl]);

  const setEditingInUrl = useCallback((editing: boolean) => {
    updateUrl({ editing: editing || undefined });
  }, [updateUrl]);

  const clearUrlState = useCallback(() => {
    router.replace(pathname, { scroll: false });
  }, [router, pathname]);

  return {
    // Current URL state
    urlState: parseUrlState(),
    // Manual URL update functions
    setDashboardInUrl,
    setTimeRangeInUrl,
    setFiltersInUrl,
    setLayoutInUrl,
    setEditingInUrl,
    clearUrlState,
    // Utility to generate shareable URL
    generateShareableUrl: useCallback(() => {
      return `${window.location.origin}${pathname}?${searchParams.toString()}`;
    }, [pathname, searchParams])
  };
};

export default useDashboardUrlSync;
