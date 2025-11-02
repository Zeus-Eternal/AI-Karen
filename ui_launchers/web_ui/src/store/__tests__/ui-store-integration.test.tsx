import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '../ui-store';
import { useUISelectors } from '../ui-selectors';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,

// Mock matchMedia for theme detection
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),

describe('UI Store Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useUIStore.getState().reset?.();

  describe('Store State Management', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useUIStore());
      
      expect(result.current.sidebarCollapsed).toBe(false);
      expect(result.current.rightPanelView).toBe('dashboard');
      expect(result.current.theme).toBe('system');
      expect(result.current.reducedMotion).toBe(false);

    it('should toggle sidebar state', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.toggleSidebar();

      expect(result.current.sidebarCollapsed).toBe(true);
      
      act(() => {
        result.current.toggleSidebar();

      expect(result.current.sidebarCollapsed).toBe(false);

    it('should update right panel view', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setRightPanelView('settings');

      expect(result.current.rightPanelView).toBe('settings');

    it('should update theme preference', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setTheme('dark');

      expect(result.current.theme).toBe('dark');

    it('should update reduced motion preference', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setReducedMotion(true);

      expect(result.current.reducedMotion).toBe(true);


  describe('State Persistence', () => {
    it('should persist sidebar state to localStorage', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.toggleSidebar();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'ui-store',
        expect.stringContaining('"sidebarCollapsed":true')
      );

    it('should persist theme preference to localStorage', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setTheme('dark');

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'ui-store',
        expect.stringContaining('"theme":"dark"')
      );

    it('should restore state from localStorage', () => {
      const savedState = {
        sidebarCollapsed: true,
        rightPanelView: 'analytics',
        theme: 'dark',
        reducedMotion: true,
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(savedState));
      
      const { result } = renderHook(() => useUIStore());
      
      expect(result.current.sidebarCollapsed).toBe(true);
      expect(result.current.rightPanelView).toBe('analytics');
      expect(result.current.theme).toBe('dark');
      expect(result.current.reducedMotion).toBe(true);

    it('should handle corrupted localStorage data gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');
      
      const { result } = renderHook(() => useUIStore());
      
      // Should fall back to default state
      expect(result.current.sidebarCollapsed).toBe(false);
      expect(result.current.theme).toBe('system');


  describe('UI Selectors', () => {
    it('should provide optimized selectors', () => {
      const { result: storeResult } = renderHook(() => useUIStore());
      const { result: selectorsResult } = renderHook(() => useUISelectors());
      
      // Update store state
      act(() => {
        storeResult.current.setTheme('dark');
        storeResult.current.toggleSidebar();

      expect(selectorsResult.current.isDarkTheme).toBe(true);
      expect(selectorsResult.current.isSidebarCollapsed).toBe(true);

    it('should compute derived state correctly', () => {
      const { result: storeResult } = renderHook(() => useUIStore());
      const { result: selectorsResult } = renderHook(() => useUISelectors());
      
      // Test system theme detection
      act(() => {
        storeResult.current.setTheme('system');

      // Mock system dark mode
      window.matchMedia = vi.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));
      
      expect(selectorsResult.current.effectiveTheme).toBe('dark');

    it('should provide layout state selectors', () => {
      const { result: storeResult } = renderHook(() => useUIStore());
      const { result: selectorsResult } = renderHook(() => useUISelectors());
      
      act(() => {
        storeResult.current.setRightPanelView('settings');

      expect(selectorsResult.current.isSettingsView).toBe(true);
      expect(selectorsResult.current.isDashboardView).toBe(false);


  describe('Store Actions', () => {
    it('should batch multiple state updates', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.batchUpdate({
          sidebarCollapsed: true,
          rightPanelView: 'analytics',
          theme: 'dark',


      expect(result.current.sidebarCollapsed).toBe(true);
      expect(result.current.rightPanelView).toBe('analytics');
      expect(result.current.theme).toBe('dark');

    it('should reset store to default state', () => {
      const { result } = renderHook(() => useUIStore());
      
      // Modify state
      act(() => {
        result.current.toggleSidebar();
        result.current.setTheme('dark');
        result.current.setRightPanelView('settings');

      // Reset
      act(() => {
        result.current.reset();

      expect(result.current.sidebarCollapsed).toBe(false);
      expect(result.current.theme).toBe('system');
      expect(result.current.rightPanelView).toBe('dashboard');

    it('should handle concurrent updates correctly', async () => {
      const { result } = renderHook(() => useUIStore());
      
      // Simulate concurrent updates
      const promises = [
        act(async () => {
          result.current.setTheme('dark');
        }),
        act(async () => {
          result.current.toggleSidebar();
        }),
        act(async () => {
          result.current.setRightPanelView('analytics');
        }),
      ];
      
      await Promise.all(promises);
      
      expect(result.current.theme).toBe('dark');
      expect(result.current.sidebarCollapsed).toBe(true);
      expect(result.current.rightPanelView).toBe('analytics');


  describe('Store Subscriptions', () => {
    it('should notify subscribers of state changes', () => {
      const subscriber = vi.fn();
      const { result } = renderHook(() => useUIStore());
      
      // Subscribe to store changes
      const unsubscribe = useUIStore.subscribe(subscriber);
      
      act(() => {
        result.current.toggleSidebar();

      expect(subscriber).toHaveBeenCalled();
      
      unsubscribe();

    it('should allow selective subscriptions', () => {
      const themeSubscriber = vi.fn();
      const sidebarSubscriber = vi.fn();
      
      const { result } = renderHook(() => useUIStore());
      
      // Subscribe to specific state slices
      const unsubscribeTheme = useUIStore.subscribe(
        state => state.theme,
        themeSubscriber
      );
      
      const unsubscribeSidebar = useUIStore.subscribe(
        state => state.sidebarCollapsed,
        sidebarSubscriber
      );
      
      act(() => {
        result.current.setTheme('dark');

      expect(themeSubscriber).toHaveBeenCalled();
      expect(sidebarSubscriber).not.toHaveBeenCalled();
      
      act(() => {
        result.current.toggleSidebar();

      expect(sidebarSubscriber).toHaveBeenCalled();
      
      unsubscribeTheme();
      unsubscribeSidebar();


  describe('Performance Optimizations', () => {
    it('should prevent unnecessary re-renders with shallow equality', () => {
      const renderCount = vi.fn();
      
      const TestComponent = () => {
        renderCount();
        const { sidebarCollapsed } = useUIStore(state => ({
          sidebarCollapsed: state.sidebarCollapsed,
        }));
        return <div>{String(sidebarCollapsed)}</div>;
      };
      
      const { result } = renderHook(() => useUIStore());
      
      // Initial render
      expect(renderCount).toHaveBeenCalledTimes(0);
      
      // Update unrelated state
      act(() => {
        result.current.setTheme('dark');

      // Should not cause re-render since sidebarCollapsed didn't change
      expect(renderCount).toHaveBeenCalledTimes(0);
      
      // Update related state
      act(() => {
        result.current.toggleSidebar();

      // Should cause re-render
      expect(renderCount).toHaveBeenCalledTimes(1);

    it('should handle large state objects efficiently', () => {
      const { result } = renderHook(() => useUIStore());
      
      const startTime = performance.now();
      
      // Perform many state updates
      act(() => {
        for (let i = 0; i < 1000; i++) {
          result.current.toggleSidebar();
        }

      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Should complete within reasonable time (less than 100ms)
      expect(duration).toBeLessThan(100);


  describe('Error Handling', () => {
    it('should handle invalid state updates gracefully', () => {
      const { result } = renderHook(() => useUIStore());
      
      expect(() => {
        act(() => {
          // @ts-expect-error - Testing invalid input
          result.current.setTheme('invalid-theme');

      }).not.toThrow();
      
      // Should maintain valid state
      expect(['light', 'dark', 'system']).toContain(result.current.theme);

    it('should recover from localStorage errors', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded');

      const { result } = renderHook(() => useUIStore());
      
      expect(() => {
        act(() => {
          result.current.setTheme('dark');

      }).not.toThrow();
      
      expect(result.current.theme).toBe('dark');


  describe('Store Middleware', () => {
    it('should apply persistence middleware correctly', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setTheme('dark');

      // Should persist to localStorage
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'ui-store',
        expect.stringContaining('"theme":"dark"')
      );

    it('should apply devtools middleware in development', () => {
      // Mock development environment
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.toggleSidebar();

      // Should work without errors in development
      expect(result.current.sidebarCollapsed).toBe(true);
      
      process.env.NODE_ENV = originalEnv;


