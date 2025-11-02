/**
 * Theme Provider Tests
 * 
 * Tests for theme switching and design token application
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { ThemeProvider, useTheme } from '../../providers/theme-provider';
import { useUIStore } from '../../store';

// Mock the UI store
jest.mock('../../store', () => ({
  useUIStore: jest.fn(),
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),

// Test component that uses the theme
const TestComponent = () => {
  const { theme, resolvedTheme, setTheme, density, setDensity, toggleTheme } = useTheme();
  
  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="resolved-theme">{resolvedTheme}</div>
      <div data-testid="density">{density}</div>
      <button onClick={() => setTheme('light')} data-testid="set-light">
      </button>
      <button onClick={() => setTheme('dark')} data-testid="set-dark">
      </button>
      <button onClick={() => setTheme('system')} data-testid="set-system">
      </button>
      <button onClick={() => setDensity('compact')} data-testid="set-compact">
      </button>
      <button onClick={() => setDensity('comfortable')} data-testid="set-comfortable">
      </button>
      <button onClick={() => setDensity('spacious')} data-testid="set-spacious">
      </button>
      <button onClick={toggleTheme} data-testid="toggle-theme">
      </button>
    </div>
  );
};

describe('ThemeProvider', () => {
  const mockSetTheme = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
    
    (useUIStore as jest.Mock).mockReturnValue({
      theme: 'system',
      setTheme: mockSetTheme,


  it('should provide default theme and density values', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toHaveTextContent('system');
    expect(screen.getByTestId('density')).toHaveTextContent('comfortable');

  it('should allow theme switching', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('set-light'));
    
    await waitFor(() => {
      expect(mockSetTheme).toHaveBeenCalledWith('light');


  it('should allow density switching', async () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('set-compact'));
    
    await waitFor(() => {
      expect(screen.getByTestId('density')).toHaveTextContent('compact');


  it('should persist density to localStorage', async () => {
    render(
      <ThemeProvider densityStorageKey="test-density">
        <TestComponent />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('set-spacious'));
    
    await waitFor(() => {
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('test-density', 'spacious');


  it('should toggle theme correctly', async () => {
    (useUIStore as jest.Mock).mockReturnValue({
      theme: 'system',
      setTheme: mockSetTheme,

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('toggle-theme'));
    
    await waitFor(() => {
      expect(mockSetTheme).toHaveBeenCalledWith('light');


  it('should handle system theme detection', () => {
    // Mock system dark theme
    (window.matchMedia as jest.Mock).mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark');

  it('should apply CSS classes to document element', async () => {
    const mockRoot = {
      setAttribute: jest.fn(),
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
      style: {},
    };

    Object.defineProperty(document, 'documentElement', {
      value: mockRoot,
      writable: true,

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    // Wait for effects to run
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));

    expect(mockRoot.classList.add).toHaveBeenCalledWith('light');
    expect(mockRoot.classList.add).toHaveBeenCalledWith('density-comfortable');

  it('should disable transitions when requested', async () => {
    const mockRoot = {
      setAttribute: jest.fn(),
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
      },
      style: {},
    };

    Object.defineProperty(document, 'documentElement', {
      value: mockRoot,
      writable: true,

    render(
      <ThemeProvider disableTransitionOnChange>
        <TestComponent />
      </ThemeProvider>
    );

    // Wait for effects to run
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));

    expect(mockRoot.classList.add).toHaveBeenCalledWith('disable-transitions');

  it('should load persisted preferences', () => {
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'ui-theme') return 'dark';
      if (key === 'ui-density') return 'compact';
      return null;

    (useUIStore as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    expect(screen.getByTestId('density')).toHaveTextContent('compact');

  it('should inject CSS tokens when enabled', () => {
    const mockHead = {
      appendChild: jest.fn(),
    };

    const mockStyleElement = {
      id: '',
      textContent: '',
    };

    Object.defineProperty(document, 'head', {
      value: mockHead,
      writable: true,

    Object.defineProperty(document, 'createElement', {
      value: jest.fn().mockReturnValue(mockStyleElement),
      writable: true,

    Object.defineProperty(document, 'getElementById', {
      value: jest.fn().mockReturnValue(null),
      writable: true,

    render(
      <ThemeProvider enableCSSInjection>
        <TestComponent />
      </ThemeProvider>
    );

    expect(document.createElement).toHaveBeenCalledWith('style');
    expect(mockHead.appendChild).toHaveBeenCalledWith(mockStyleElement);
    expect(mockStyleElement.id).toBe('design-tokens-css');

  it('should not inject CSS when disabled', () => {
    const mockHead = {
      appendChild: jest.fn(),
    };

    Object.defineProperty(document, 'head', {
      value: mockHead,
      writable: true,

    render(
      <ThemeProvider enableCSSInjection={false}>
        <TestComponent />
      </ThemeProvider>
    );

    expect(mockHead.appendChild).not.toHaveBeenCalled();

  it('should throw error when useTheme is used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useTheme must be used within a ThemeProvider');

    consoleSpy.mockRestore();

