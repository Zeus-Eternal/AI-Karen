
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { MicroInteractionProvider, useMicroInteractions } from '../micro-interaction-provider';
import { vi } from 'vitest';

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),

const TestComponent = () => {
  const { reducedMotion, enableHaptics, animationDuration, updateConfig } = useMicroInteractions();
  
  return (
    <div>
      <div data-testid="reduced-motion">{reducedMotion.toString()}</div>
      <div data-testid="enable-haptics">{enableHaptics.toString()}</div>
      <div data-testid="animation-duration">{animationDuration}</div>
      <Button 
        onClick={() => updateConfig({ enableHaptics: false })}
        data-testid="update-config"
      >
      </Button>
    </div>
  );
};

describe('MicroInteractionProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  it('provides default configuration', () => {
    render(
      <MicroInteractionProvider>
        <TestComponent />
      </MicroInteractionProvider>
    );
    
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('false');
    expect(screen.getByTestId('enable-haptics')).toHaveTextContent('true');
    expect(screen.getByTestId('animation-duration')).toHaveTextContent('normal');

  it('accepts custom default configuration', () => {
    render(
      <MicroInteractionProvider defaultConfig={{ enableHaptics: false, animationDuration: 'fast' }}>
        <TestComponent />
      </MicroInteractionProvider>
    );
    
    expect(screen.getByTestId('enable-haptics')).toHaveTextContent('false');
    expect(screen.getByTestId('animation-duration')).toHaveTextContent('fast');

  it('updates configuration when updateConfig is called', () => {
    render(
      <MicroInteractionProvider>
        <TestComponent />
      </MicroInteractionProvider>
    );
    
    expect(screen.getByTestId('enable-haptics')).toHaveTextContent('true');
    
    act(() => {
      screen.getByTestId('update-config').click();

    expect(screen.getByTestId('enable-haptics')).toHaveTextContent('false');

  it('detects reduced motion preference', () => {
    // Mock matchMedia to return reduced motion preference
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(
      <MicroInteractionProvider>
        <TestComponent />
      </MicroInteractionProvider>
    );
    
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('true');

  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useMicroInteractions must be used within a MicroInteractionProvider');
    
    consoleSpy.mockRestore();

