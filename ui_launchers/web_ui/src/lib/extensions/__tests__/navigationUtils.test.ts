/**
 * Tests for navigation utilities and action creators
 */

import { vi } from 'vitest';
import { createBreadcrumbItem, navigationActions, navigationHelpers, navigationValidation } from '../navigationUtils';
import type { NavigationState, ExtensionAction } from '../../../extensions/types';

describe('navigationUtils', () => {
    describe('createBreadcrumbItem', () => {
        it('should create a basic breadcrumb item', () => {
            const item = createBreadcrumbItem('submenu', 'LLM Providers');

            expect(item).toEqual({
                level: 'submenu',
                name: 'LLM Providers',
                category: undefined,
                id: undefined,
                icon: undefined,


        it('should create a breadcrumb item with options', () => {
            const item = createBreadcrumbItem('submenu', 'LLM Providers', {
                category: 'Plugins',
                id: 'llm',
                icon: 'brain',

            expect(item).toEqual({
                level: 'submenu',
                name: 'LLM Providers',
                category: 'Plugins',
                id: 'llm',
                icon: 'brain',



    describe('navigationActions', () => {
        describe('switchCategory', () => {
            it('should create SET_CATEGORY action', () => {
                const action = navigationActions.switchCategory('Extensions');

                expect(action).toEqual({
                    type: 'SET_CATEGORY',
                    category: 'Extensions',



        describe('navigateToPluginProvider', () => {
            it('should create navigation actions for plugin provider', () => {
                const actions = navigationActions.navigateToPluginProvider('llm', 'LLM Providers');

                expect(actions).toHaveLength(2);
                expect(actions[0]).toEqual({
                    type: 'SET_NAVIGATION',
                    navigation: {
                        currentLevel: 'submenu',
                        selectedPluginProvider: 'llm',
                    },

                expect(actions[1]).toEqual({
                    type: 'PUSH_BREADCRUMB',
                    item: {
                        level: 'submenu',
                        name: 'LLM Providers',
                        category: 'Plugins',
                        id: 'llm',
                        icon: 'brain',
                    },



        describe('navigateToExtensionSubmenu', () => {
            it('should create navigation actions for extension submenu', () => {
                const actions = navigationActions.navigateToExtensionSubmenu('agents', 'Agents');

                expect(actions).toHaveLength(2);
                expect(actions[0]).toEqual({
                    type: 'SET_NAVIGATION',
                    navigation: {
                        currentLevel: 'submenu',
                        selectedExtensionSubmenu: 'agents',
                    },

                expect(actions[1]).toEqual({
                    type: 'PUSH_BREADCRUMB',
                    item: {
                        level: 'submenu',
                        name: 'Agents',
                        category: undefined,
                        id: 'agents',
                        icon: 'bot',
                    },



        describe('goBack', () => {
            it('should create GO_BACK action', () => {
                const action = navigationActions.goBack();

                expect(action).toEqual({
                    type: 'GO_BACK',



        describe('resetToCategory', () => {
            it('should create RESET_BREADCRUMBS action', () => {
                const action = navigationActions.resetToCategory();

                expect(action).toEqual({
                    type: 'RESET_BREADCRUMBS',




    describe('navigationHelpers', () => {
        const mockNavigationState: NavigationState = {
            currentCategory: 'Plugins',
            currentLevel: 'items',
            selectedPluginProvider: 'llm',
            selectedProviderItem: 'openai',
            breadcrumb: [
                { level: 'submenu', name: 'LLM Providers', category: 'Plugins', id: 'llm' },
                { level: 'items', name: 'OpenAI', id: 'openai' },
            ],
            canGoBack: true,
        };

        describe('canGoBack', () => {
            it('should return true when navigation can go back', () => {
                expect(navigationHelpers.canGoBack(mockNavigationState)).toBe(true);

            it('should return false when navigation cannot go back', () => {
                const state = { ...mockNavigationState, canGoBack: false, breadcrumb: [] };
                expect(navigationHelpers.canGoBack(state)).toBe(false);


        describe('getCurrentPath', () => {
            it('should return current path for plugins', () => {
                const path = navigationHelpers.getCurrentPath(mockNavigationState);
                expect(path).toBe('Plugins > llm > openai');

            it('should return current path for extensions', () => {
                const extensionState: NavigationState = {
                    currentCategory: 'Extensions',
                    currentLevel: 'items',
                    selectedExtensionSubmenu: 'agents',
                    selectedExtensionCategory: 'automation',
                    breadcrumb: [],
                    canGoBack: false,
                };

                const path = navigationHelpers.getCurrentPath(extensionState);
                expect(path).toBe('Extensions > agents > automation');


        describe('getBreadcrumbTrail', () => {
            it('should return breadcrumb names as array', () => {
                const trail = navigationHelpers.getBreadcrumbTrail(mockNavigationState);
                expect(trail).toEqual(['LLM Providers', 'OpenAI']);


        describe('isAtLevel', () => {
            it('should return true when at specified level', () => {
                expect(navigationHelpers.isAtLevel(mockNavigationState, 'items')).toBe(true);

            it('should return false when not at specified level', () => {
                expect(navigationHelpers.isAtLevel(mockNavigationState, 'settings')).toBe(false);


        describe('isInCategory', () => {
            it('should return true when in specified category', () => {
                expect(navigationHelpers.isInCategory(mockNavigationState, 'Plugins')).toBe(true);

            it('should return false when not in specified category', () => {
                expect(navigationHelpers.isInCategory(mockNavigationState, 'Extensions')).toBe(false);


        describe('getNavigationContext', () => {
            it('should return complete navigation context', () => {
                const context = navigationHelpers.getNavigationContext(mockNavigationState);

                expect(context).toEqual({
                    category: 'Plugins',
                    level: 'items',
                    path: 'Plugins > llm > openai',
                    breadcrumbs: mockNavigationState.breadcrumb,
                    canGoBack: true,




    describe('navigationValidation', () => {
        describe('validateNavigationState', () => {
            it('should validate consistent navigation state', () => {
                const validState: NavigationState = {
                    currentCategory: 'Plugins',
                    currentLevel: 'items',
                    selectedPluginProvider: 'llm',
                    selectedProviderItem: 'openai',
                    breadcrumb: [
                        { level: 'submenu', name: 'LLM Providers' },
                        { level: 'items', name: 'OpenAI' },
                    ],
                    canGoBack: true,
                };

                expect(navigationValidation.validateNavigationState(validState)).toBe(true);

            it('should detect breadcrumb length mismatch', () => {
                const invalidState: NavigationState = {
                    currentCategory: 'Plugins',
                    currentLevel: 'items',
                    selectedPluginProvider: 'llm',
                    selectedProviderItem: 'openai',
                    breadcrumb: [
                        { level: 'submenu', name: 'LLM Providers' },
                        // Missing second breadcrumb item
                    ],
                    canGoBack: true,
                };

                // Mock console.warn to avoid test output
                const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });

                expect(navigationValidation.validateNavigationState(invalidState)).toBe(false);
                expect(consoleSpy).toHaveBeenCalledWith(
                    'Navigation breadcrumb length mismatch',
                    expect.objectContaining({
                        expected: 2,
                        actual: 1
                    })
                );

                consoleSpy.mockRestore();

            it('should detect category-selection mismatch', () => {
                const invalidState: NavigationState = {
                    currentCategory: 'Plugins',
                    currentLevel: 'submenu',
                    selectedPluginProvider: 'llm',
                    selectedExtensionSubmenu: 'agents', // Wrong category selection
                    breadcrumb: [
                        { level: 'submenu', name: 'LLM Providers' },
                    ],
                    canGoBack: true,
                };

                // Mock console.warn to avoid test output
                const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });

                expect(navigationValidation.validateNavigationState(invalidState)).toBe(false);
                expect(consoleSpy).toHaveBeenCalledWith(
                    'Plugin category has extension selections',
                    invalidState
                );

                consoleSpy.mockRestore();



