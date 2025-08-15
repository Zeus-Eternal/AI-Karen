import React, { ReactNode } from 'react';
import { renderHook } from '@testing-library/react';
import { useFeature, useFeatures, FeatureFlag } from '../use-feature';
import { FeatureFlagsProvider } from '@/contexts/FeatureFlagsContext';

import { vi } from 'vitest';

// Mock telemetry hook
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn(),
    startSpan: vi.fn(() => ({ end: vi.fn() })),
    setCorrelationId: vi.fn(),
    flush: vi.fn()
  })
}));

const createWrapper = (initialFlags?: Partial<Record<FeatureFlag, boolean>>) => {
  return ({ children }: { children: ReactNode }) => 
    React.createElement(FeatureFlagsProvider, { initialFlags, persistToStorage: false }, children);
};

describe('useFeature', () => {
  it('should return false when used outside FeatureFlagsProvider', () => {
    const { result } = renderHook(() => useFeature('chat.streaming'));
    
    expect(result.current).toBe(false);
  });

  it('should return correct flag value when flag is enabled', () => {
    const wrapper = createWrapper({ 'chat.streaming': true });
    const { result } = renderHook(() => useFeature('chat.streaming'), { wrapper });
    
    expect(result.current).toBe(true);
  });

  it('should return correct flag value when flag is disabled', () => {
    const wrapper = createWrapper({ 'chat.streaming': false });
    const { result } = renderHook(() => useFeature('chat.streaming'), { wrapper });
    
    expect(result.current).toBe(false);
  });

  it('should return false when no flag is provided', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeature(), { wrapper });
    
    expect(result.current).toBe(false);
  });

  it('should return false for undefined flag', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeature(undefined), { wrapper });
    
    expect(result.current).toBe(false);
  });

  it('should return default value for unknown flag', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFeature('unknown.flag' as FeatureFlag), { wrapper });
    
    expect(result.current).toBe(false);
  });
});

describe('useFeatures', () => {
  it('should throw error when used outside FeatureFlagsProvider', () => {
    expect(() => {
      renderHook(() => useFeatures());
    }).toThrow('useFeatures must be used within a FeatureFlagsProvider');
  });

  it('should return feature flags context', () => {
    const wrapper = createWrapper({ 'chat.streaming': true });
    const { result } = renderHook(() => useFeatures(), { wrapper });
    
    expect(result.current).toHaveProperty('flags');
    expect(result.current).toHaveProperty('isEnabled');
    expect(result.current).toHaveProperty('enable');
    expect(result.current).toHaveProperty('disable');
    expect(result.current).toHaveProperty('toggle');
    expect(result.current).toHaveProperty('setFlags');
    expect(result.current).toHaveProperty('reset');
  });

  it('should allow checking flag status', () => {
    const wrapper = createWrapper({ 'chat.streaming': true });
    const { result } = renderHook(() => useFeatures(), { wrapper });
    
    expect(result.current.isEnabled('chat.streaming')).toBe(true);
  });
});