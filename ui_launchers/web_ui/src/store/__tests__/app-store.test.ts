/**
 * App Store Tests
 * 
 * Unit tests for the enhanced app store with Zustand.
 * Based on requirements: 12.2, 12.3
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {  useAppStore, type User, type UserPreferences, selectUser, selectIsAuthenticated, selectTheme, selectIsLoading, selectUnreadNotifications } from '../app-store';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,

describe('App Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAppStore.getState().resetAppState();
    vi.clearAllMocks();

  describe('Authentication State', () => {
    it('should initialize with no user', () => {
      const state = useAppStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.authLoading).toBe(false);
      expect(state.authError).toBeNull();

    it('should set user and authentication state on login', () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          density: 'comfortable',
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      useAppStore.getState().login(mockUser);

      const state = useAppStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.authLoading).toBe(false);
      expect(state.authError).toBeNull();

    it('should clear user state on logout', () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          density: 'comfortable',
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      // Login first
      useAppStore.getState().login(mockUser);
      expect(useAppStore.getState().isAuthenticated).toBe(true);

      // Then logout
      useAppStore.getState().logout();

      const state = useAppStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.authLoading).toBe(false);
      expect(state.authError).toBeNull();
      expect(state.notifications).toEqual([]);
      expect(state.errors).toEqual({});

    it('should update user preferences', () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          density: 'comfortable',
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      useAppStore.getState().login(mockUser);

      const updatedPreferences: Partial<UserPreferences> = {
        theme: 'dark',
        density: 'compact',
      };

      useAppStore.getState().updateUserPreferences(updatedPreferences);

      const state = useAppStore.getState();
      expect(state.user?.preferences.theme).toBe('dark');
      expect(state.user?.preferences.density).toBe('compact');
      expect(state.user?.preferences.language).toBe('en'); // Should remain unchanged


  describe('Layout State', () => {
    it('should initialize with default layout state', () => {
      const state = useAppStore.getState();
      expect(state.layout.sidebarOpen).toBe(true);
      expect(state.layout.sidebarCollapsed).toBe(false);
      expect(state.layout.rightPanelOpen).toBe(false);
      expect(state.layout.rightPanelView).toBe('dashboard');
      expect(state.layout.headerHeight).toBe(64);
      expect(state.layout.footerVisible).toBe(true);
      expect(state.layout.breadcrumbsVisible).toBe(true);

    it('should toggle sidebar state', () => {
      const { toggleSidebar } = useAppStore.getState();
      
      expect(useAppStore.getState().layout.sidebarOpen).toBe(true);
      
      toggleSidebar();
      expect(useAppStore.getState().layout.sidebarOpen).toBe(false);
      
      toggleSidebar();
      expect(useAppStore.getState().layout.sidebarOpen).toBe(true);

    it('should set sidebar collapsed state', () => {
      const { setSidebarCollapsed } = useAppStore.getState();
      
      expect(useAppStore.getState().layout.sidebarCollapsed).toBe(false);
      
      setSidebarCollapsed(true);
      expect(useAppStore.getState().layout.sidebarCollapsed).toBe(true);
      
      setSidebarCollapsed(false);
      expect(useAppStore.getState().layout.sidebarCollapsed).toBe(false);

    it('should toggle right panel state', () => {
      const { toggleRightPanel } = useAppStore.getState();
      
      expect(useAppStore.getState().layout.rightPanelOpen).toBe(false);
      
      toggleRightPanel();
      expect(useAppStore.getState().layout.rightPanelOpen).toBe(true);
      
      toggleRightPanel();
      expect(useAppStore.getState().layout.rightPanelOpen).toBe(false);


  describe('Loading States', () => {
    it('should manage global loading state', () => {
      const { setGlobalLoading } = useAppStore.getState();
      
      expect(useAppStore.getState().globalLoading).toBe(false);
      
      setGlobalLoading(true);
      expect(useAppStore.getState().globalLoading).toBe(true);
      
      setGlobalLoading(false);
      expect(useAppStore.getState().globalLoading).toBe(false);

    it('should manage individual loading states', () => {
      const { setLoading, clearLoading } = useAppStore.getState();
      
      expect(useAppStore.getState().loadingStates).toEqual({});
      
      setLoading('api', true);
      expect(useAppStore.getState().loadingStates.api).toBe(true);
      
      setLoading('chat', true);
      expect(useAppStore.getState().loadingStates.chat).toBe(true);
      
      clearLoading('api');
      expect(useAppStore.getState().loadingStates.api).toBeUndefined();
      expect(useAppStore.getState().loadingStates.chat).toBe(true);

    it('should clear all loading states', () => {
      const { setLoading, setGlobalLoading, clearAllLoading } = useAppStore.getState();
      
      setGlobalLoading(true);
      setLoading('api', true);
      setLoading('chat', true);
      
      clearAllLoading();
      
      const state = useAppStore.getState();
      expect(state.globalLoading).toBe(false);
      expect(state.loadingStates).toEqual({});


  describe('Error States', () => {
    it('should manage individual error states', () => {
      const { setError, clearError } = useAppStore.getState();
      
      expect(useAppStore.getState().errors).toEqual({});
      
      setError('api', 'API Error');
      expect(useAppStore.getState().errors.api).toBe('API Error');
      
      setError('chat', 'Chat Error');
      expect(useAppStore.getState().errors.chat).toBe('Chat Error');
      
      clearError('api');
      expect(useAppStore.getState().errors.api).toBeUndefined();
      expect(useAppStore.getState().errors.chat).toBe('Chat Error');

    it('should clear all error states', () => {
      const { setError, clearAllErrors } = useAppStore.getState();
      
      setError('api', 'API Error');
      setError('chat', 'Chat Error');
      
      clearAllErrors();
      
      expect(useAppStore.getState().errors).toEqual({});


  describe('Connection State', () => {
    it('should manage online/offline state', () => {
      const { setOnline } = useAppStore.getState();
      
      expect(useAppStore.getState().isOnline).toBe(true);
      
      setOnline(false);
      expect(useAppStore.getState().isOnline).toBe(false);
      
      setOnline(true);
      expect(useAppStore.getState().isOnline).toBe(true);

    it('should manage connection quality', () => {
      const { setConnectionQuality } = useAppStore.getState();
      
      expect(useAppStore.getState().connectionQuality).toBe('good');
      
      setConnectionQuality('poor');
      expect(useAppStore.getState().connectionQuality).toBe('poor');
      expect(useAppStore.getState().isOnline).toBe(true);
      
      setConnectionQuality('offline');
      expect(useAppStore.getState().connectionQuality).toBe('offline');
      expect(useAppStore.getState().isOnline).toBe(false);


  describe('Feature Flags', () => {
    it('should manage feature flags', () => {
      const { setFeature, toggleFeature } = useAppStore.getState();
      
      expect(useAppStore.getState().features).toEqual({});
      
      setFeature('newFeature', true);
      expect(useAppStore.getState().features.newFeature).toBe(true);
      
      toggleFeature('newFeature');
      expect(useAppStore.getState().features.newFeature).toBe(false);
      
      toggleFeature('anotherFeature');
      expect(useAppStore.getState().features.anotherFeature).toBe(true);


  describe('Notifications', () => {
    it('should add notifications', () => {
      const { addNotification } = useAppStore.getState();
      
      expect(useAppStore.getState().notifications).toEqual([]);
      
      addNotification({
        type: 'info',
        title: 'Test Notification',
        message: 'This is a test',

      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(1);
      expect(state.notifications[0].title).toBe('Test Notification');
      expect(state.notifications[0].read).toBe(false);
      expect(state.notifications[0].id).toBeDefined();
      expect(state.notifications[0].timestamp).toBeInstanceOf(Date);

    it('should mark notifications as read', () => {
      const { addNotification, markNotificationRead } = useAppStore.getState();
      
      addNotification({
        type: 'info',
        title: 'Test Notification',
        message: 'This is a test',

      const notificationId = useAppStore.getState().notifications[0].id;
      expect(useAppStore.getState().notifications[0].read).toBe(false);
      
      markNotificationRead(notificationId);
      expect(useAppStore.getState().notifications[0].read).toBe(true);

    it('should remove notifications', () => {
      const { addNotification, removeNotification } = useAppStore.getState();
      
      addNotification({
        type: 'info',
        title: 'Test Notification',
        message: 'This is a test',

      const notificationId = useAppStore.getState().notifications[0].id;
      expect(useAppStore.getState().notifications).toHaveLength(1);
      
      removeNotification(notificationId);
      expect(useAppStore.getState().notifications).toHaveLength(0);

    it('should clear all notifications', () => {
      const { addNotification, clearAllNotifications } = useAppStore.getState();
      
      addNotification({
        type: 'info',
        title: 'Test 1',
        message: 'This is a test',

      addNotification({
        type: 'warning',
        title: 'Test 2',
        message: 'This is another test',

      expect(useAppStore.getState().notifications).toHaveLength(2);
      
      clearAllNotifications();
      expect(useAppStore.getState().notifications).toHaveLength(0);

    it('should limit notifications to 50', () => {
      const { addNotification } = useAppStore.getState();
      
      // Add 60 notifications
      for (let i = 0; i < 60; i++) {
        addNotification({
          type: 'info',
          title: `Test ${i}`,
          message: 'This is a test',

      }
      
      const state = useAppStore.getState();
      expect(state.notifications).toHaveLength(50);
      expect(state.notifications[0].title).toBe('Test 59'); // Most recent first


  describe('Selectors', () => {
    it('should select user correctly', () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          density: 'comfortable',
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },
      };

      useAppStore.getState().login(mockUser);

      const state = useAppStore.getState();
      
      expect(selectUser(state)).toEqual(mockUser);
      expect(selectIsAuthenticated(state)).toBe(true);
      expect(selectTheme(state)).toBe('light');

    it('should select loading state correctly', () => {
      const { setLoading } = useAppStore.getState();
      
      setLoading('api', true);
      
      const state = useAppStore.getState();
      expect(selectIsLoading('api')(state)).toBe(true);
      expect(selectIsLoading('chat')(state)).toBe(false);

    it('should select unread notifications correctly', () => {
      const { addNotification, markNotificationRead } = useAppStore.getState();
      
      addNotification({
        type: 'info',
        title: 'Test 1',
        message: 'This is a test',

      addNotification({
        type: 'warning',
        title: 'Test 2',
        message: 'This is another test',

      const state1 = useAppStore.getState();
      expect(selectUnreadNotifications(state1)).toHaveLength(2);
      
      markNotificationRead(state1.notifications[0].id);
      
      const state2 = useAppStore.getState();
      expect(selectUnreadNotifications(state2)).toHaveLength(1);


  describe('State Reset', () => {
    it('should reset app state to initial values', () => {
      const { 
        login, 
        setGlobalLoading, 
        setError, 
        addNotification, 
        setFeature,
        resetAppState 
      } = useAppStore.getState();
      
      // Modify state
      login({
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        preferences: {
          theme: 'light',
          density: 'comfortable',
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            desktop: false,
          },
          accessibility: {
            reducedMotion: false,
            highContrast: false,
            screenReader: false,
          },
        },

      setGlobalLoading(true);
      setError('api', 'Error');
      addNotification({
        type: 'info',
        title: 'Test',
        message: 'Test',

      setFeature('test', true);
      
      // Reset state
      resetAppState();
      
      const state = useAppStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.globalLoading).toBe(false);
      expect(state.errors).toEqual({});
      expect(state.notifications).toEqual([]);
      expect(state.features).toEqual({});


