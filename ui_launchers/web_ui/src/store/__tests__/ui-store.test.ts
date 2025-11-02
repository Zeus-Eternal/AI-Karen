import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '../ui-store';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,

describe('UIStore', () => {
  beforeEach(() => {
    // Reset the store before each test
    const { result } = renderHook(() => useUIStore());
    act(() => {
      result.current.resetUIState();

    vi.clearAllMocks();

  describe('Layout State', () => {
    it('should toggle sidebar', () => {
      const { result } = renderHook(() => useUIStore());
      
      expect(result.current.sidebarCollapsed).toBe(false);
      
      act(() => {
        result.current.toggleSidebar();

      expect(result.current.sidebarCollapsed).toBe(true);
      
      act(() => {
        result.current.toggleSidebar();

      expect(result.current.sidebarCollapsed).toBe(false);

    it('should set sidebar collapsed state', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setSidebarCollapsed(true);

      expect(result.current.sidebarCollapsed).toBe(true);
      
      act(() => {
        result.current.setSidebarCollapsed(false);

      expect(result.current.sidebarCollapsed).toBe(false);

    it('should set right panel view', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setRightPanelView('settings');

      expect(result.current.rightPanelView).toBe('settings');

    it('should toggle right panel', () => {
      const { result } = renderHook(() => useUIStore());
      
      expect(result.current.rightPanelCollapsed).toBe(false);
      
      act(() => {
        result.current.toggleRightPanel();

      expect(result.current.rightPanelCollapsed).toBe(true);


  describe('Theme State', () => {
    it('should set theme', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setTheme('dark');

      expect(result.current.theme).toBe('dark');
      
      act(() => {
        result.current.setTheme('light');

      expect(result.current.theme).toBe('light');


  describe('Animation State', () => {
    it('should set reduced motion', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setReducedMotion(true);

      expect(result.current.reducedMotion).toBe(true);
      
      act(() => {
        result.current.setReducedMotion(false);

      expect(result.current.reducedMotion).toBe(false);


  describe('Panel State', () => {
    it('should open and close panels', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.openPanel('test-panel', { size: 300, position: 'right' });

      expect(result.current.panelStates['test-panel']).toEqual({
        isOpen: true,
        size: 300,
        position: 'right',

      act(() => {
        result.current.closePanel('test-panel');

      expect(result.current.panelStates['test-panel'].isOpen).toBe(false);

    it('should toggle panels', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.togglePanel('test-panel');

      expect(result.current.panelStates['test-panel'].isOpen).toBe(true);
      
      act(() => {
        result.current.togglePanel('test-panel');

      expect(result.current.panelStates['test-panel'].isOpen).toBe(false);

    it('should set panel size', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.openPanel('test-panel');
        result.current.setPanelSize('test-panel', 400);

      expect(result.current.panelStates['test-panel'].size).toBe(400);


  describe('Modal State', () => {
    it('should open and close modals', () => {
      const { result } = renderHook(() => useUIStore());
      const testData = { id: 1, name: 'test' };
      
      act(() => {
        result.current.openModal('test-modal', testData);

      expect(result.current.modals['test-modal']).toEqual({
        isOpen: true,
        data: testData,

      act(() => {
        result.current.closeModal('test-modal');

      expect(result.current.modals['test-modal'].isOpen).toBe(false);
      expect(result.current.modals['test-modal'].data).toBeUndefined();

    it('should toggle modals', () => {
      const { result } = renderHook(() => useUIStore());
      const testData = { id: 1, name: 'test' };
      
      act(() => {
        result.current.toggleModal('test-modal', testData);

      expect(result.current.modals['test-modal'].isOpen).toBe(true);
      expect(result.current.modals['test-modal'].data).toEqual(testData);
      
      act(() => {
        result.current.toggleModal('test-modal');

      expect(result.current.modals['test-modal'].isOpen).toBe(false);


  describe('Loading State', () => {
    it('should set loading states', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setLoading('test-operation', true);

      expect(result.current.loadingStates['test-operation']).toBe(true);
      
      act(() => {
        result.current.setLoading('test-operation', false);

      expect(result.current.loadingStates['test-operation']).toBe(false);


  describe('Error State', () => {
    it('should set and clear errors', () => {
      const { result } = renderHook(() => useUIStore());
      const errorMessage = 'Test error message';
      
      act(() => {
        result.current.setError('test-error', errorMessage);

      expect(result.current.errors['test-error']).toBe(errorMessage);
      
      act(() => {
        result.current.clearError('test-error');

      expect(result.current.errors['test-error']).toBeUndefined();

    it('should clear all errors', () => {
      const { result } = renderHook(() => useUIStore());
      
      act(() => {
        result.current.setError('error1', 'Error 1');
        result.current.setError('error2', 'Error 2');

      expect(Object.keys(result.current.errors)).toHaveLength(2);
      
      act(() => {
        result.current.clearAllErrors();

      expect(Object.keys(result.current.errors)).toHaveLength(0);


  describe('Reset State', () => {
    it('should reset UI state to initial values', () => {
      const { result } = renderHook(() => useUIStore());
      
      // Modify state
      act(() => {
        result.current.setSidebarCollapsed(true);
        result.current.setTheme('dark');
        result.current.setReducedMotion(true);
        result.current.openPanel('test-panel');
        result.current.setError('test-error', 'Test error');

      // Verify state is modified
      expect(result.current.sidebarCollapsed).toBe(true);
      expect(result.current.theme).toBe('dark');
      expect(result.current.reducedMotion).toBe(true);
      expect(result.current.panelStates['test-panel']).toBeDefined();
      expect(result.current.errors['test-error']).toBe('Test error');
      
      // Reset state
      act(() => {
        result.current.resetUIState();

      // Verify state is reset
      expect(result.current.sidebarCollapsed).toBe(false);
      expect(result.current.theme).toBe('system');
      expect(result.current.reducedMotion).toBe(false);
      expect(Object.keys(result.current.panelStates)).toHaveLength(0);
      expect(Object.keys(result.current.errors)).toHaveLength(0);


