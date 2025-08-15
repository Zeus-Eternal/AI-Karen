import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { 
  FeatureFlagsProvider, 
  useFeatureFlags, 
  FeatureGate 
} from '../FeatureFlagsContext';
import { FeatureFlag } from '@/hooks/use-feature';

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

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

describe('FeatureFlagsProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  it('should provide default feature flags', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    expect(result.current.flags).toHaveProperty('chat.streaming');
    expect(result.current.flags).toHaveProperty('copilot.enabled');
    expect(result.current.flags).toHaveProperty('security.sanitization');
  });

  it('should merge initial flags with defaults', () => {
    const initialFlags = { 'chat.streaming': false };
    
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider initialFlags={initialFlags} persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    expect(result.current.flags['chat.streaming']).toBe(false);
    expect(result.current.flags['copilot.enabled']).toBe(true); // default value
  });

  it('should load flags from localStorage when persistence is enabled', () => {
    const storedConfig = {
      flags: { 'chat.streaming': false, 'voice.input': true },
      environment: 'production',
      version: '1.0.0',
      lastUpdated: '2023-01-01T00:00:00.000Z'
    };
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(storedConfig));

    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={true}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    expect(mockLocalStorage.getItem).toHaveBeenCalledWith('feature_flags');
    expect(result.current.flags['chat.streaming']).toBe(false);
    expect(result.current.flags['voice.input']).toBe(true);
  });

  it('should handle localStorage errors gracefully', () => {
    mockLocalStorage.getItem.mockImplementation(() => {
      throw new Error('localStorage error');
    });

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={true}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to load feature flag configuration:',
      expect.any(Error)
    );
    expect(result.current.flags).toBeDefined();

    consoleSpy.mockRestore();
  });

  it('should enable a feature flag', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    act(() => {
      result.current.enable('voice.input');
    });

    expect(result.current.flags['voice.input']).toBe(true);
  });

  it('should disable a feature flag', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    act(() => {
      result.current.disable('chat.streaming');
    });

    expect(result.current.flags['chat.streaming']).toBe(false);
  });

  it('should toggle a feature flag', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    const initialValue = result.current.flags['voice.input'];

    act(() => {
      result.current.toggle('voice.input');
    });

    expect(result.current.flags['voice.input']).toBe(!initialValue);
  });

  it('should set multiple flags at once', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    const newFlags = {
      'voice.input': true,
      'voice.output': true,
      'debug.mode': true
    };

    act(() => {
      result.current.setFlags(newFlags);
    });

    expect(result.current.flags['voice.input']).toBe(true);
    expect(result.current.flags['voice.output']).toBe(true);
    expect(result.current.flags['debug.mode']).toBe(true);
  });

  it('should reset flags to defaults', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={false}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    // Modify some flags
    act(() => {
      result.current.setFlags({
        'voice.input': true,
        'debug.mode': true
      });
    });

    // Reset to defaults
    act(() => {
      result.current.reset();
    });

    expect(result.current.flags['voice.input']).toBe(false); // default
    expect(result.current.flags['debug.mode']).toBe(false); // default
    expect(result.current.flags['chat.streaming']).toBe(true); // default
  });

  it('should check if flag is enabled', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider 
          initialFlags={{ 'chat.streaming': true, 'voice.input': false }}
          persistToStorage={false}
        >
          {children}
        </FeatureFlagsProvider>
      )
    });

    expect(result.current.isEnabled('chat.streaming')).toBe(true);
    expect(result.current.isEnabled('voice.input')).toBe(false);
  });

  it('should persist flags to localStorage when enabled', () => {
    const { result } = renderHook(() => useFeatureFlags(), {
      wrapper: ({ children }) => (
        <FeatureFlagsProvider persistToStorage={true}>
          {children}
        </FeatureFlagsProvider>
      )
    });

    act(() => {
      result.current.enable('voice.input');
    });

    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'feature_flags',
      expect.stringContaining('"voice.input":true')
    );
  });
});

describe('FeatureGate', () => {
  const TestComponent = () => <div>Feature Content</div>;
  const FallbackComponent = () => <div>Fallback Content</div>;

  it('should render children when feature is enabled', () => {
    render(
      <FeatureFlagsProvider 
        initialFlags={{ 'chat.streaming': true }}
        persistToStorage={false}
      >
        <FeatureGate feature="chat.streaming">
          <TestComponent />
        </FeatureGate>
      </FeatureFlagsProvider>
    );

    expect(screen.getByText('Feature Content')).toBeInTheDocument();
  });

  it('should render fallback when feature is disabled', () => {
    render(
      <FeatureFlagsProvider 
        initialFlags={{ 'chat.streaming': false }}
        persistToStorage={false}
      >
        <FeatureGate feature="chat.streaming" fallback={<FallbackComponent />}>
          <TestComponent />
        </FeatureGate>
      </FeatureFlagsProvider>
    );

    expect(screen.getByText('Fallback Content')).toBeInTheDocument();
    expect(screen.queryByText('Feature Content')).not.toBeInTheDocument();
  });

  it('should render nothing when feature is disabled and no fallback provided', () => {
    render(
      <FeatureFlagsProvider 
        initialFlags={{ 'chat.streaming': false }}
        persistToStorage={false}
      >
        <FeatureGate feature="chat.streaming">
          <TestComponent />
        </FeatureGate>
      </FeatureFlagsProvider>
    );

    expect(screen.queryByText('Feature Content')).not.toBeInTheDocument();
  });

  it('should throw error when used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(
        <FeatureGate feature="chat.streaming">
          <TestComponent />
        </FeatureGate>
      );
    }).toThrow('useFeatureFlags must be used within a FeatureFlagsProvider');

    consoleSpy.mockRestore();
  });
});