import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { HookProvider, useHooks } from '@/contexts/HookContext';
import React from 'react';

// Test wrapper
const wrapper = ({ children }: { children: React.ReactNode }) => (
    <HookProvider>{children}</HookProvider>
);

describe('HookContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();

    describe('Hook Registration', () => {
        it('registers a hook successfully', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                const hookId = result.current.registerHook('test_hook', mockHandler);
                expect(hookId).toMatch(/^test_hook_\d+_[a-z0-9]+$/);


        it('registers hook with options', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                const hookId = result.current.registerHook('test_hook', mockHandler, {
                    priority: 50,
                    conditions: { userId: 'test-user' },
                    sourceType: 'plugin'

                expect(hookId).toMatch(/^test_hook_\d+_[a-z0-9]+$/);


        it('registers grid hook with helper method', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                const hookId = result.current.registerGridHook('testGrid', 'dataLoad', mockHandler);
                expect(hookId).toMatch(/^grid_testGrid_dataLoad_\d+_[a-z0-9]+$/);


        it('registers chart hook with helper method', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                const hookId = result.current.registerChartHook('testChart', 'seriesClick', mockHandler);
                expect(hookId).toMatch(/^chart_testChart_seriesClick_\d+_[a-z0-9]+$/);


        it('registers chat hook with helper method', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                const hookId = result.current.registerChatHook('preMessage', mockHandler);
                expect(hookId).toMatch(/^chat_preMessage_\d+_[a-z0-9]+$/);



    describe('Hook Execution', () => {
        it('triggers hooks successfully', async () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler1 = vi.fn().mockResolvedValue({ data: 'result1' });
            const mockHandler2 = vi.fn().mockResolvedValue({ data: 'result2' });

            let hookId1: string, hookId2: string;

            act(() => {
                hookId1 = result.current.registerHook('test_hook', mockHandler1, { priority: 100 });
                hookId2 = result.current.registerHook('test_hook', mockHandler2, { priority: 50 });

            const context = { message: 'test message' };
            const userContext = { userId: 'test-user' };

            const hookResults = await act(async () => {
                return await result.current.triggerHooks('test_hook', context, userContext);

            expect(hookResults).toHaveLength(2);
            expect(hookResults[0]).toEqual({
                hookId: hookId2, // Lower priority executes first
                result: { data: 'result2' },
                success: true

            expect(hookResults[1]).toEqual({
                hookId: hookId1,
                result: { data: 'result1' },
                success: true

            expect(mockHandler1).toHaveBeenCalledWith(context, userContext);
            expect(mockHandler2).toHaveBeenCalledWith(context, userContext);

        it('handles hook execution errors', async () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockRejectedValue(new Error('Hook execution failed'));

            let hookId: string;

            act(() => {
                hookId = result.current.registerHook('test_hook', mockHandler);

            const context = { message: 'test message' };

            const hookResults = await act(async () => {
                return await result.current.triggerHooks('test_hook', context);

            expect(hookResults).toHaveLength(1);
            expect(hookResults[0]).toEqual({
                hookId,
                error: 'Hook execution failed',
                success: false


        it('respects hook conditions', async () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler1 = vi.fn().mockResolvedValue({ data: 'result1' });
            const mockHandler2 = vi.fn().mockResolvedValue({ data: 'result2' });

            act(() => {
                result.current.registerHook('test_hook', mockHandler1, {
                    conditions: { userId: 'user1' }

                result.current.registerHook('test_hook', mockHandler2, {
                    conditions: { userId: 'user2' }


            const context = { message: 'test message' };
            const userContext = { userId: 'user1' };

            const hookResults = await act(async () => {
                return await result.current.triggerHooks('test_hook', context, userContext);

            expect(hookResults).toHaveLength(1);
            expect(mockHandler1).toHaveBeenCalledWith(context, userContext);
            expect(mockHandler2).not.toHaveBeenCalled();

        it('executes hooks in priority order', async () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const executionOrder: number[] = [];
            const mockHandler1 = vi.fn().mockImplementation(async () => {
                executionOrder.push(1);
                return { data: 'result1' };

            const mockHandler2 = vi.fn().mockImplementation(async () => {
                executionOrder.push(2);
                return { data: 'result2' };

            const mockHandler3 = vi.fn().mockImplementation(async () => {
                executionOrder.push(3);
                return { data: 'result3' };

            act(() => {
                result.current.registerHook('test_hook', mockHandler1, { priority: 100 });
                result.current.registerHook('test_hook', mockHandler2, { priority: 50 });
                result.current.registerHook('test_hook', mockHandler3, { priority: 75 });

            await act(async () => {
                await result.current.triggerHooks('test_hook', {});

            expect(executionOrder).toEqual([2, 3, 1]); // Priority 50, 75, 100


    describe('Hook Management', () => {
        it('unregisters hooks successfully', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            let hookId: string;

            act(() => {
                hookId = result.current.registerHook('test_hook', mockHandler);

            act(() => {
                const unregistered = result.current.unregisterHook(hookId);
                expect(unregistered).toBe(true);

            // Try to unregister again
            act(() => {
                const unregistered = result.current.unregisterHook(hookId);
                expect(unregistered).toBe(false);


        it('gets registered hooks', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler1 = vi.fn().mockResolvedValue({ success: true });
            const mockHandler2 = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerHook('test_hook_1', mockHandler1);
                result.current.registerHook('test_hook_2', mockHandler2);

            const allHooks = result.current.getRegisteredHooks();
            expect(allHooks).toHaveLength(2);

            const type1Hooks = result.current.getRegisteredHooks('test_hook_1');
            expect(type1Hooks).toHaveLength(1);
            expect(type1Hooks[0].type).toBe('test_hook_1');

        it('handles empty hook triggers', async () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const hookResults = await act(async () => {
                return await result.current.triggerHooks('nonexistent_hook', {});

            expect(hookResults).toHaveLength(0);


    describe('Hook Types', () => {
        it('creates proper hook registration objects', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            let hookId: string;

            act(() => {
                hookId = result.current.registerHook('test_hook', mockHandler, {
                    priority: 75,
                    conditions: { test: 'value' },
                    sourceType: 'extension'


            const hooks = result.current.getRegisteredHooks('test_hook');
            expect(hooks).toHaveLength(1);

            const hook = hooks[0];
            expect(hook.id).toBe(hookId);
            expect(hook.type).toBe('test_hook');
            expect(hook.handler).toBe(mockHandler);
            expect(hook.priority).toBe(75);
            expect(hook.conditions).toEqual({ test: 'value' });
            expect(hook.sourceType).toBe('extension');

        it('uses default values for hook options', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerHook('test_hook', mockHandler);

            const hooks = result.current.getRegisteredHooks('test_hook');
            const hook = hooks[0];

            expect(hook.priority).toBe(100);
            expect(hook.conditions).toEqual({});
            expect(hook.sourceType).toBe('custom');


    describe('Context Provider', () => {
        it('throws error when useHooks is used outside provider', () => {
            expect(() => {
                renderHook(() => useHooks());
            }).toThrow('useHooks must be used within a HookProvider');

        it('provides context successfully', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            expect(result.current.registerHook).toBeDefined();
            expect(result.current.triggerHooks).toBeDefined();
            expect(result.current.unregisterHook).toBeDefined();
            expect(result.current.getRegisteredHooks).toBeDefined();
            expect(result.current.registerGridHook).toBeDefined();
            expect(result.current.registerChartHook).toBeDefined();
            expect(result.current.registerChatHook).toBeDefined();


    describe('Specialized Hook Helpers', () => {
        it('registers grid hooks with correct conditions', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerGridHook('testGrid', 'dataLoad', mockHandler);

            const hooks = result.current.getRegisteredHooks('grid_testGrid_dataLoad');
            expect(hooks).toHaveLength(1);
            expect(hooks[0].sourceType).toBe('ui');
            expect(hooks[0].conditions).toEqual({ gridId: 'testGrid' });

        it('registers chart hooks with correct conditions', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerChartHook('testChart', 'seriesClick', mockHandler);

            const hooks = result.current.getRegisteredHooks('chart_testChart_seriesClick');
            expect(hooks).toHaveLength(1);
            expect(hooks[0].sourceType).toBe('ui');
            expect(hooks[0].conditions).toEqual({ chartId: 'testChart' });

        it('registers chat hooks with correct priority', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerChatHook('preMessage', mockHandler);

            const hooks = result.current.getRegisteredHooks('chat_preMessage');
            expect(hooks).toHaveLength(1);
            expect(hooks[0].sourceType).toBe('ui');
            expect(hooks[0].priority).toBe(50); // preMessage has higher priority

        it('registers non-preMessage chat hooks with default priority', () => {
            const { result } = renderHook(() => useHooks(), { wrapper });

            const mockHandler = vi.fn().mockResolvedValue({ success: true });

            act(() => {
                result.current.registerChatHook('postMessage', mockHandler);

            const hooks = result.current.getRegisteredHooks('chat_postMessage');
            expect(hooks).toHaveLength(1);
            expect(hooks[0].priority).toBe(100); // Default priority


