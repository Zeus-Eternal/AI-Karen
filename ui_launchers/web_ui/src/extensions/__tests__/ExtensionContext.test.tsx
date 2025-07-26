/**
 * Tests for ExtensionContext and reducer functionality
 */

import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { ExtensionProvider, useExtensionContext } from '../ExtensionContext';
import type { ExtensionAction, BreadcrumbItem } from '../types';

// Wrapper component for testing hooks
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ExtensionProvider>{children}</ExtensionProvider>
);

describe('ExtensionContext', () => {
  describe('useExtensionContext', () => {
    it('should throw error when used outside provider', () => {
      expect(() => {
        renderHook(() => useExtensionContext());
      }).toThrow('useExtensionContext must be used within an ExtensionProvider');
    });

    it('should provide initial state', () => {
      const { result } = renderHook(() => useExtensionContext(), { wrapper });
      
      expect(result.current.state).toEqual({
        currentCategory: 'Plugins',
        breadcrumbs: [],
        level: 0,
        navigation: {
          currentCategory: 'Plugins',
          currentLevel: 'category',
          breadcrumb: [],
          canGoBack: false,
        },
        loading: false,
        error: null,
        events: [],
      });
    });

    it('should provide dispatch function', () => {
      const { result } = renderHook(() => useExtensionContext(), { wrapper });
      
      expect(typeof result.current.dispatch).toBe('function');
    });
  });

  describe('reducer actions', () => {
    describe('SET_CATEGORY', () => {
      it('should switch category and reset navigation', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        act(() => {
          result.current.dispatch({
            type: 'SET_CATEGORY',
            category: 'Extensions',
          });
        });
        
        expect(result.current.state.currentCategory).toBe('Extensions');
        expect(result.current.state.navigation.currentCategory).toBe('Extensions');
        expect(result.current.state.navigation.currentLevel).toBe('category');
        expect(result.current.state.breadcrumbs).toEqual([]);
        expect(result.current.state.navigation.breadcrumb).toEqual([]);
        expect(result.current.state.navigation.canGoBack).toBe(false);
        expect(result.current.state.error).toBeNull();
      });
    });

    describe('PUSH_BREADCRUMB', () => {
      it('should add breadcrumb and update navigation level', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        const breadcrumbItem: BreadcrumbItem = {
          level: 'submenu',
          name: 'LLM Providers',
          category: 'Plugins',
          id: 'llm',
          icon: 'brain',
        };
        
        act(() => {
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: breadcrumbItem,
          });
        });
        
        expect(result.current.state.breadcrumbs).toEqual([breadcrumbItem]);
        expect(result.current.state.navigation.breadcrumb).toEqual([breadcrumbItem]);
        expect(result.current.state.navigation.currentLevel).toBe('submenu');
        expect(result.current.state.navigation.canGoBack).toBe(true);
        expect(result.current.state.level).toBe(1);
      });
    });

    describe('POP_BREADCRUMB', () => {
      it('should remove last breadcrumb and update level', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        const breadcrumbItem1: BreadcrumbItem = {
          level: 'submenu',
          name: 'LLM Providers',
          category: 'Plugins',
          id: 'llm',
        };
        
        const breadcrumbItem2: BreadcrumbItem = {
          level: 'items',
          name: 'OpenAI',
          id: 'openai',
        };
        
        // Add two breadcrumbs
        act(() => {
          result.current.dispatch({ type: 'PUSH_BREADCRUMB', item: breadcrumbItem1 });
          result.current.dispatch({ type: 'PUSH_BREADCRUMB', item: breadcrumbItem2 });
        });
        
        expect(result.current.state.level).toBe(2);
        expect(result.current.state.navigation.currentLevel).toBe('items');
        
        // Pop one breadcrumb
        act(() => {
          result.current.dispatch({ type: 'POP_BREADCRUMB' });
        });
        
        expect(result.current.state.breadcrumbs).toEqual([breadcrumbItem1]);
        expect(result.current.state.navigation.breadcrumb).toEqual([breadcrumbItem1]);
        expect(result.current.state.navigation.currentLevel).toBe('submenu');
        expect(result.current.state.navigation.canGoBack).toBe(true);
        expect(result.current.state.level).toBe(1);
      });

      it('should clear selections when going back to category level', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Set up navigation state with selections
        act(() => {
          result.current.dispatch({
            type: 'SET_NAVIGATION',
            navigation: {
              selectedPluginProvider: 'llm',
              selectedProviderItem: 'openai',
            },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'submenu', name: 'LLM Providers' },
          });
        });
        
        // Pop breadcrumb to go back to category
        act(() => {
          result.current.dispatch({ type: 'POP_BREADCRUMB' });
        });
        
        expect(result.current.state.navigation.currentLevel).toBe('category');
        expect(result.current.state.navigation.selectedPluginProvider).toBeUndefined();
        expect(result.current.state.navigation.selectedProviderItem).toBeUndefined();
      });
    });

    describe('GO_BACK', () => {
      it('should navigate back one level', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        const breadcrumbItem: BreadcrumbItem = {
          level: 'submenu',
          name: 'LLM Providers',
        };
        
        // Add breadcrumb
        act(() => {
          result.current.dispatch({ type: 'PUSH_BREADCRUMB', item: breadcrumbItem });
        });
        
        expect(result.current.state.level).toBe(1);
        
        // Go back
        act(() => {
          result.current.dispatch({ type: 'GO_BACK' });
        });
        
        expect(result.current.state.breadcrumbs).toEqual([]);
        expect(result.current.state.navigation.breadcrumb).toEqual([]);
        expect(result.current.state.navigation.currentLevel).toBe('category');
        expect(result.current.state.navigation.canGoBack).toBe(false);
        expect(result.current.state.level).toBe(0);
      });
    });

    describe('SET_LEVEL', () => {
      it('should set navigation to specific level', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Add multiple breadcrumbs
        act(() => {
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'submenu', name: 'LLM Providers' },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'items', name: 'OpenAI' },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'settings', name: 'GPT-4 Settings' },
          });
        });
        
        expect(result.current.state.level).toBe(3);
        
        // Set level to 1
        act(() => {
          result.current.dispatch({ type: 'SET_LEVEL', level: 1 });
        });
        
        expect(result.current.state.level).toBe(1);
        expect(result.current.state.breadcrumbs).toHaveLength(1);
        expect(result.current.state.navigation.breadcrumb).toHaveLength(1);
        expect(result.current.state.navigation.currentLevel).toBe('submenu');
      });

      it('should clear selections when setting level to 0', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Set up navigation with selections
        act(() => {
          result.current.dispatch({
            type: 'SET_NAVIGATION',
            navigation: {
              selectedPluginProvider: 'llm',
              selectedProviderItem: 'openai',
              selectedModel: 'gpt-4',
            },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'submenu', name: 'LLM Providers' },
          });
        });
        
        // Set level to 0
        act(() => {
          result.current.dispatch({ type: 'SET_LEVEL', level: 0 });
        });
        
        expect(result.current.state.navigation.selectedPluginProvider).toBeUndefined();
        expect(result.current.state.navigation.selectedProviderItem).toBeUndefined();
        expect(result.current.state.navigation.selectedModel).toBeUndefined();
      });
    });

    describe('RESET_BREADCRUMBS', () => {
      it('should reset all navigation state', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Set up complex navigation state
        act(() => {
          result.current.dispatch({
            type: 'SET_NAVIGATION',
            navigation: {
              selectedPluginProvider: 'llm',
              selectedProviderItem: 'openai',
            },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'submenu', name: 'LLM Providers' },
          });
          result.current.dispatch({
            type: 'PUSH_BREADCRUMB',
            item: { level: 'items', name: 'OpenAI' },
          });
        });
        
        expect(result.current.state.level).toBe(2);
        
        // Reset breadcrumbs
        act(() => {
          result.current.dispatch({ type: 'RESET_BREADCRUMBS' });
        });
        
        expect(result.current.state.breadcrumbs).toEqual([]);
        expect(result.current.state.navigation.breadcrumb).toEqual([]);
        expect(result.current.state.navigation.currentLevel).toBe('category');
        expect(result.current.state.navigation.canGoBack).toBe(false);
        expect(result.current.state.level).toBe(0);
        expect(result.current.state.navigation.selectedPluginProvider).toBeUndefined();
        expect(result.current.state.navigation.selectedProviderItem).toBeUndefined();
      });
    });

    describe('SET_NAVIGATION', () => {
      it('should update navigation state', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        act(() => {
          result.current.dispatch({
            type: 'SET_NAVIGATION',
            navigation: {
              currentLevel: 'submenu',
              selectedPluginProvider: 'llm',
            },
          });
        });
        
        expect(result.current.state.navigation.currentLevel).toBe('submenu');
        expect(result.current.state.navigation.selectedPluginProvider).toBe('llm');
        expect(result.current.state.navigation.currentCategory).toBe('Plugins'); // Should preserve existing values
      });
    });

    describe('SET_LOADING', () => {
      it('should update loading state', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        act(() => {
          result.current.dispatch({ type: 'SET_LOADING', loading: true });
        });
        
        expect(result.current.state.loading).toBe(true);
        
        act(() => {
          result.current.dispatch({ type: 'SET_LOADING', loading: false });
        });
        
        expect(result.current.state.loading).toBe(false);
      });
    });

    describe('SET_ERROR', () => {
      it('should set error and clear loading', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Set loading first
        act(() => {
          result.current.dispatch({ type: 'SET_LOADING', loading: true });
        });
        
        expect(result.current.state.loading).toBe(true);
        
        // Set error
        act(() => {
          result.current.dispatch({ type: 'SET_ERROR', error: 'Test error' });
        });
        
        expect(result.current.state.error).toBe('Test error');
        expect(result.current.state.loading).toBe(false);
      });

      it('should clear error', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Set error
        act(() => {
          result.current.dispatch({ type: 'SET_ERROR', error: 'Test error' });
        });
        
        expect(result.current.state.error).toBe('Test error');
        
        // Clear error
        act(() => {
          result.current.dispatch({ type: 'SET_ERROR', error: null });
        });
        
        expect(result.current.state.error).toBeNull();
      });
    });

    describe('ADD_EVENT', () => {
      it('should add event to events array', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        const event = {
          id: 'test-event',
          type: 'install' as const,
          extensionId: 'test-extension',
          timestamp: '2024-01-01T00:00:00Z',
          message: 'Test event',
        };
        
        act(() => {
          result.current.dispatch({ type: 'ADD_EVENT', event });
        });
        
        expect(result.current.state.events).toEqual([event]);
      });

      it('should limit events to 100 items', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Add 101 events
        act(() => {
          for (let i = 0; i < 101; i++) {
            result.current.dispatch({
              type: 'ADD_EVENT',
              event: {
                id: `event-${i}`,
                type: 'install' as const,
                extensionId: 'test-extension',
                timestamp: '2024-01-01T00:00:00Z',
                message: `Event ${i}`,
              },
            });
          }
        });
        
        expect(result.current.state.events).toHaveLength(100);
        expect(result.current.state.events[0].id).toBe('event-100'); // Most recent first
      });
    });

    describe('CLEAR_EVENTS', () => {
      it('should clear all events', () => {
        const { result } = renderHook(() => useExtensionContext(), { wrapper });
        
        // Add some events
        act(() => {
          result.current.dispatch({
            type: 'ADD_EVENT',
            event: {
              id: 'test-event',
              type: 'install' as const,
              extensionId: 'test-extension',
              timestamp: '2024-01-01T00:00:00Z',
              message: 'Test event',
            },
          });
        });
        
        expect(result.current.state.events).toHaveLength(1);
        
        // Clear events
        act(() => {
          result.current.dispatch({ type: 'CLEAR_EVENTS' });
        });
        
        expect(result.current.state.events).toEqual([]);
      });
    });
  });

  describe('ExtensionProvider', () => {
    it('should accept initial category', () => {
      const customWrapper = ({ children }: { children: React.ReactNode }) => (
        <ExtensionProvider initialCategory="Extensions">{children}</ExtensionProvider>
      );
      
      const { result } = renderHook(() => useExtensionContext(), { wrapper: customWrapper });
      
      expect(result.current.state.currentCategory).toBe('Extensions');
      expect(result.current.state.navigation.currentCategory).toBe('Extensions');
    });
  });
});