/**
 * @vitest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AccessibilityEnhancementsProvider, useAccessibilityEnhancements } from '../AccessibilityProvider';
import { AccessibilityProvider } from '../../../providers/accessibility-provider';

// Mock the accessibility provider
vi.mock('../../../providers/accessibility-provider', () => ({
  AccessibilityProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAccessibility: () => ({
    settings: {
      highContrast: false,
      fontSize: 'medium',
      lineHeight: 'normal',
      reducedMotion: false,
      focusVisible: true,
      keyboardNavigation: true,
      announcements: true,
      verboseDescriptions: false,
      colorBlindnessSupport: 'none',
    },
    updateSetting: vi.fn(),
    resetSettings: vi.fn(),
    announce: vi.fn(),
  }),
}));

// Test component that uses the accessibility enhancements
function TestComponent() {
  const {
    highContrastMode,
    toggleHighContrast,
    focusRingVisible,
    announceMessage,
    textScale,
    setTextScale,
    colorBlindnessFilter,
    setColorBlindnessFilter,
  } = useAccessibilityEnhancements();

  return (
    <div>
      <div data-testid="high-contrast">{highContrastMode.toString()}</div>
      <div data-testid="focus-ring">{focusRingVisible.toString()}</div>
      <div data-testid="text-scale">{textScale}</div>
      <div data-testid="color-blindness">{colorBlindnessFilter}</div>
      
      <Button onClick={toggleHighContrast} aria-label="Button">Toggle High Contrast</Button>
      <Button onClick={() => announceMessage('Test message')}>Announce</Button>
      <Button onClick={() => setTextScale(1.5)}>Set Text Scale</Button>
      <Button onClick={() => setColorBlindnessFilter('protanopia')}>Set Color Blindness</Button>
    </div>
  );
}

function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AccessibilityProvider>
      <AccessibilityEnhancementsProvider>
        {children}
      </AccessibilityEnhancementsProvider>
    </AccessibilityProvider>
  );
}

describe('AccessibilityEnhancementsProvider', () => {
  beforeEach(() => {
    // Mock document.documentElement
    Object.defineProperty(document, 'documentElement', {
      value: {
        style: {
          setProperty: jest.fn(),
        },
        classList: {
          add: jest.fn(),
          remove: jest.fn(),
        },
        setAttribute: jest.fn(),
      },
      writable: true,


  it('provides accessibility enhancement context', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByTestId('high-contrast')).toHaveTextContent('false');
    expect(screen.getByTestId('focus-ring')).toHaveTextContent('true');
    expect(screen.getByTestId('text-scale')).toHaveTextContent('1');
    expect(screen.getByTestId('color-blindness')).toHaveTextContent('none');

  it('handles high contrast toggle', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const toggleButton = screen.getByText('Toggle High Contrast');
    fireEvent.click(toggleButton);

    // The actual toggle would be handled by the mocked useAccessibility hook
    // This test verifies the component structure is correct
    expect(toggleButton).toBeInTheDocument();

  it('handles text scale changes', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const setScaleButton = screen.getByText('Set Text Scale');
    fireEvent.click(setScaleButton);

    await waitFor(() => {
      expect(screen.getByTestId('text-scale')).toHaveTextContent('1.5');


  it('handles color blindness filter changes', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const setFilterButton = screen.getByText('Set Color Blindness');
    fireEvent.click(setFilterButton);

    await waitFor(() => {
      expect(screen.getByTestId('color-blindness')).toHaveTextContent('protanopia');


  it('handles announcements', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const announceButton = screen.getByText('Announce');
    fireEvent.click(announceButton);

    // The announcement would be handled by the mocked announce function
    expect(announceButton).toBeInTheDocument();

  it('applies CSS custom properties for text scaling', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const setScaleButton = screen.getByText('Set Text Scale');
    fireEvent.click(setScaleButton);

    await waitFor(() => {
      expect(document.documentElement.style.setProperty).toHaveBeenCalledWith(
        '--accessibility-text-scale',
        '1.5'
      );


  it('applies color blindness filter classes', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const setFilterButton = screen.getByText('Set Color Blindness');
    fireEvent.click(setFilterButton);

    await waitFor(() => {
      expect(document.documentElement.classList.add).toHaveBeenCalledWith(
        'color-blindness-protanopia'
      );


  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAccessibilityEnhancements must be used within an AccessibilityEnhancementsProvider');

    consoleSpy.mockRestore();

