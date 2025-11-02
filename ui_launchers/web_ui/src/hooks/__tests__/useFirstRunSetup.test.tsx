/**
 * Tests for useFirstRunSetup hook
 * Tests first-run detection, setup state management, and integration with API
 */

import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

  useFirstRunSetup,
  useFirstRunSetupWithRedirect,
  useFirstRunSetupProvider,
  shouldBypassFirstRunCheck,
  firstRunSetupStorage
import { } from '../useFirstRunSetup';
import type { AdminApiResponse, FirstRunSetup } from '@/types/admin';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window.location
const mockLocation = {
  href: '',
  pathname: '/'
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true

describe('useFirstRunSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
    mockLocation.pathname = '/';
    
    // Clear localStorage
    localStorage.clear();

  afterEach(() => {
    vi.restoreAllMocks();

  describe('useFirstRunSetup hook', () => {
    it('should initialize with loading state', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false,
            setup_token: 'setup_123_abc'
          }
        })

      const { result } = renderHook(() => useFirstRunSetup());

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isFirstRun).toBe(false);
      expect(result.current.setupCompleted).toBe(false);
      expect(result.current.error).toBe(null);

    it('should detect first-run setup needed', async () => {
      const mockResponse: AdminApiResponse<FirstRunSetup> = {
        success: true,
        data: {
          super_admin_exists: false,
          setup_completed: false,
          setup_token: 'setup_123_abc'
        }
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isFirstRun).toBe(true);
      expect(result.current.setupCompleted).toBe(false);
      expect(result.current.setupToken).toBe('setup_123_abc');
      expect(result.current.error).toBe(null);
      expect(result.current.lastChecked).toBeInstanceOf(Date);

    it('should detect setup already completed', async () => {
      const mockResponse: AdminApiResponse<FirstRunSetup> = {
        success: true,
        data: {
          super_admin_exists: true,
          setup_completed: true
        }
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isFirstRun).toBe(false);
      expect(result.current.setupCompleted).toBe(true);
      expect(result.current.setupToken).toBeUndefined();
      expect(result.current.error).toBe(null);

    it('should handle API errors gracefully', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.error).toBe('HTTP 500: Internal Server Error');
      expect(result.current.isFirstRun).toBe(false);
      expect(result.current.setupCompleted).toBe(false);

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.error).toBe('Network error');

    it('should handle API response errors', async () => {
      const mockResponse: AdminApiResponse<FirstRunSetup> = {
        success: false,
        error: {
          code: 'DATABASE_ERROR',
          message: 'Database connection failed'
        }
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.error).toBe('Database connection failed');

    it('should allow manual refresh', async () => {
      let callCount = 0;
      mockFetch.mockImplementation(() => {
        callCount++;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: {
              super_admin_exists: callCount > 1,
              setup_completed: callCount > 1,
              setup_token: callCount > 1 ? undefined : 'setup_123_abc'
            }
          })


      const { result } = renderHook(() => useFirstRunSetup());

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isFirstRun).toBe(true);
      expect(callCount).toBe(1);

      // Trigger refresh
      await act(async () => {
        await result.current.refresh();

      expect(result.current.isFirstRun).toBe(false);
      expect(result.current.setupCompleted).toBe(true);
      expect(callCount).toBe(2);

    it('should mark setup as completed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false,
            setup_token: 'setup_123_abc'
          }
        })

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isFirstRun).toBe(true);

      act(() => {
        result.current.markSetupCompleted();

      expect(result.current.isFirstRun).toBe(false);
      expect(result.current.setupCompleted).toBe(true);
      expect(result.current.setupToken).toBeUndefined();

    it('should clear errors', async () => {
      mockFetch.mockRejectedValue(new Error('Test error'));

      const { result } = renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(result.current.error).toBe('Test error');

      act(() => {
        result.current.clearError();

      expect(result.current.error).toBe(null);


  describe('useFirstRunSetupWithRedirect hook', () => {
    it('should redirect when setup is needed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false,
            setup_token: 'setup_123_abc'
          }
        })

      mockLocation.pathname = '/dashboard';

      const { result } = renderHook(() => useFirstRunSetupWithRedirect('/setup'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.shouldRedirect).toBe(true);
      
      // Wait for redirect to happen
      await waitFor(() => {
        expect(mockLocation.href).toBe('/setup');


    it('should not redirect when already on setup page', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false,
            setup_token: 'setup_123_abc'
          }
        })

      mockLocation.pathname = '/setup';

      const { result } = renderHook(() => useFirstRunSetupWithRedirect('/setup'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.shouldRedirect).toBe(false);
      expect(mockLocation.href).toBe('');

    it('should not redirect when setup is completed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: true,
            setup_completed: true
          }
        })

      const { result } = renderHook(() => useFirstRunSetupWithRedirect('/setup'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.shouldRedirect).toBe(false);
      expect(mockLocation.href).toBe('');


  describe('useFirstRunSetupProvider hook', () => {
    it('should provide setup required state', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false,
            setup_token: 'setup_123_abc'
          }
        })

      const { result } = renderHook(() => useFirstRunSetupProvider());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isSetupRequired).toBe(true);
      expect(result.current.canProceedWithApp).toBe(false);

    it('should provide can proceed state when setup is completed', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: true,
            setup_completed: true
          }
        })

      const { result } = renderHook(() => useFirstRunSetupProvider());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);

      expect(result.current.isSetupRequired).toBe(false);
      expect(result.current.canProceedWithApp).toBe(true);


  describe('shouldBypassFirstRunCheck utility', () => {
    it('should bypass check for setup routes', () => {
      expect(shouldBypassFirstRunCheck('/setup')).toBe(true);
      expect(shouldBypassFirstRunCheck('/setup/wizard')).toBe(true);

    it('should bypass check for API routes', () => {
      expect(shouldBypassFirstRunCheck('/api/auth/login')).toBe(true);
      expect(shouldBypassFirstRunCheck('/api/admin/setup/check-first-run')).toBe(true);

    it('should bypass check for system routes', () => {
      expect(shouldBypassFirstRunCheck('/health')).toBe(true);
      expect(shouldBypassFirstRunCheck('/_next/static/css/app.css')).toBe(true);
      expect(shouldBypassFirstRunCheck('/favicon.ico')).toBe(true);

    it('should not bypass check for regular routes', () => {
      expect(shouldBypassFirstRunCheck('/dashboard')).toBe(false);
      expect(shouldBypassFirstRunCheck('/profile')).toBe(false);
      expect(shouldBypassFirstRunCheck('/chat')).toBe(false);


  describe('firstRunSetupStorage utilities', () => {
    beforeEach(() => {
      localStorage.clear();

    it('should cache and retrieve setup status', () => {
      const state = {
        isFirstRun: true,
        setupCompleted: false,
        setupToken: 'setup_123_abc'
      };

      firstRunSetupStorage.setCachedStatus(state);
      const retrieved = firstRunSetupStorage.getCachedStatus();

      expect(retrieved).toMatchObject(state);

    it('should return null for expired cache', () => {
      const state = {
        isFirstRun: true,
        setupCompleted: false
      };

      // Manually set expired cache
      const expiredCache = {
        state,
        timestamp: Date.now() - (10 * 60 * 1000) // 10 minutes ago
      };
      localStorage.setItem('first_run_setup_status', JSON.stringify(expiredCache));

      const retrieved = firstRunSetupStorage.getCachedStatus();
      expect(retrieved).toBe(null);
      
      // Should also clear the expired cache
      expect(localStorage.getItem('first_run_setup_status')).toBe(null);

    it('should return null for invalid cache data', () => {
      localStorage.setItem('first_run_setup_status', 'invalid-json');
      
      const retrieved = firstRunSetupStorage.getCachedStatus();
      expect(retrieved).toBe(null);

    it('should clear cached status', () => {
      const state = { isFirstRun: true };
      firstRunSetupStorage.setCachedStatus(state);
      
      expect(firstRunSetupStorage.getCachedStatus()).not.toBe(null);
      
      firstRunSetupStorage.clearCachedStatus();
      expect(firstRunSetupStorage.getCachedStatus()).toBe(null);

    it('should handle localStorage errors gracefully', () => {
      // Mock localStorage to throw errors
      const originalSetItem = localStorage.setItem;
      const originalGetItem = localStorage.getItem;
      
      localStorage.setItem = vi.fn(() => {
        throw new Error('Storage quota exceeded');

      localStorage.getItem = vi.fn(() => {
        throw new Error('Storage access denied');

      // Should not throw errors
      expect(() => {
        firstRunSetupStorage.setCachedStatus({ isFirstRun: true });
      }).not.toThrow();

      expect(() => {
        firstRunSetupStorage.getCachedStatus();
      }).not.toThrow();

      expect(() => {
        firstRunSetupStorage.clearCachedStatus();
      }).not.toThrow();

      // Restore original methods
      localStorage.setItem = originalSetItem;
      localStorage.getItem = originalGetItem;


  describe('API integration', () => {
    it('should call correct API endpoint', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            super_admin_exists: false,
            setup_completed: false
          }
        })

      renderHook(() => useFirstRunSetup());

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/admin/setup/check-first-run', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          cache: 'no-cache'



    it('should handle multiple concurrent calls', async () => {
      let resolveCount = 0;
      mockFetch.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolveCount++;
            resolve({
              ok: true,
              json: () => Promise.resolve({
                success: true,
                data: {
                  super_admin_exists: false,
                  setup_completed: false
                }
              })

          }, 100);


      const { result: result1 } = renderHook(() => useFirstRunSetup());
      const { result: result2 } = renderHook(() => useFirstRunSetup());

      // Trigger manual refresh on both
      act(() => {
        result1.current.refresh();
        result2.current.refresh();

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
        expect(result2.current.isLoading).toBe(false);

      // Should have made multiple API calls
      expect(mockFetch).toHaveBeenCalledTimes(4); // 2 initial + 2 refresh


