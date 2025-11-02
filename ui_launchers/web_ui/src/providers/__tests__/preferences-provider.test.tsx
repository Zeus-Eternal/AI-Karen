
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PreferencesProvider, usePreferences } from '../preferences-provider';

// Mock the UI store
const mockSetTheme = vi.fn();
const mockSetReducedMotion = vi.fn();

vi.mock('../../store', () => ({
  useUIStore: vi.fn(() => ({
    theme: 'system',
    reducedMotion: false,
    setTheme: mockSetTheme,
    setReducedMotion: mockSetReducedMotion,
  })),
  selectPreferencesState: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),

function TestComponent() {
  const { preferences, updatePreference, resetPreferences, isLoading, error } = usePreferences();
  
  return (
    <div>
      <div data-testid="theme">{preferences.theme}</div>
      <div data-testid="reduced-motion">{preferences.reducedMotion.toString()}</div>
      <div data-testid="loading">{isLoading.toString()}</div>
      <div data-testid="error">{error || 'no-error'}</div>
      <button onClick={() => updatePreference('theme', 'dark')}>Set Dark Theme</button>
      <button onClick={() => updatePreference('reducedMotion', true)}>Enable Reduced Motion</button>
      <button onClick={resetPreferences}>Reset</button>
    </div>
  );
}

describe('PreferencesProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);

  it('should provide preferences context', async () => {
    render(
      <PreferencesProvider>
        <TestComponent />
      </PreferencesProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');

    expect(screen.getByTestId('theme')).toHaveTextContent('system');
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('false');
    expect(screen.getByTestId('error')).toHaveTextContent('no-error');

  it('should update preferences', async () => {
    const user = userEvent.setup();
    
    render(
      <PreferencesProvider>
        <TestComponent />
      </PreferencesProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');

    await user.click(screen.getByText('Set Dark Theme'));
    
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    expect(mockSetTheme).toHaveBeenCalledWith('dark');

  it('should reset preferences', async () => {
    const user = userEvent.setup();
    
    render(
      <PreferencesProvider>
        <TestComponent />
      </PreferencesProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');

    // Change a preference
    await user.click(screen.getByText('Set Dark Theme'));
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');

    // Reset preferences
    await user.click(screen.getByText('Reset'));
    expect(screen.getByTestId('theme')).toHaveTextContent('system');

  it('should load preferences from localStorage', async () => {
    const storedPreferences = JSON.stringify({
      theme: 'dark',
      reducedMotion: true,

    localStorageMock.getItem.mockReturnValue(storedPreferences);

    render(
      <PreferencesProvider>
        <TestComponent />
      </PreferencesProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');

    // Verify localStorage was called
    expect(localStorageMock.getItem).toHaveBeenCalledWith('user-preferences');

  it('should throw error when used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('usePreferences must be used within a PreferencesProvider');
    
    consoleSpy.mockRestore();

