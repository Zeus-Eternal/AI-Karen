/**
 * AppShell Integration Tests
 * 
 * Tests for responsive layout system and navigation functionality.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AppShell, useAppShell } from '../AppShell';
import { ThemeProvider } from '@/providers/theme-provider';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,

// Mock window.matchMedia
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

// Test component that uses AppShell context
const TestComponent: React.FC = () => {
  const { 
    sidebarOpen, 
    sidebarCollapsed, 
    isMobile, 
    isTablet,
    toggleSidebar, 
    closeSidebar, 
    openSidebar 
  } = useAppShell();

  return (
    <div>
      <div data-testid="sidebar-open">{sidebarOpen.toString()}</div>
      <div data-testid="sidebar-collapsed">{sidebarCollapsed.toString()}</div>
      <div data-testid="is-mobile">{isMobile.toString()}</div>
      <div data-testid="is-tablet">{isTablet.toString()}</div>
      <Button data-testid="toggle-sidebar" onClick={toggleSidebar} aria-label="Button">
      </Button>
      <Button data-testid="close-sidebar" onClick={closeSidebar} aria-label="Button">
      </Button>
      <Button data-testid="open-sidebar" onClick={openSidebar} aria-label="Button">
      </Button>
    </div>
  );
};

const renderAppShell = (props = {}) => {
  return render(
    <ThemeProvider>
      <AppShell
        sidebar={<div data-testid="sidebar">Sidebar Content</div>}
        header={<div data-testid="header">Header Content</div>}
        footer={<div data-testid="footer">Footer Content</div>}
        {...props}
      >
        <TestComponent />
      </AppShell>
    </ThemeProvider>
  );
};

describe('AppShell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,


  describe('Basic Rendering', () => {
    it('renders all sections correctly', () => {
      renderAppShell();

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('header')).toBeInTheDocument();
      expect(screen.getByTestId('footer')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();

    it('applies correct ARIA labels', () => {
      renderAppShell();

      const sidebar = screen.getByLabelText('Main navigation');
      expect(sidebar).toBeInTheDocument();
      expect(sidebar.tagName).toBe('ASIDE');


  describe('Responsive Behavior', () => {
    it('detects mobile viewport correctly', async () => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      renderAppShell({ sidebarBreakpoint: 768 });

      // Trigger resize event
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');


    it('detects tablet viewport correctly', async () => {
      // Set tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 900,

      renderAppShell({ 
        sidebarBreakpoint: 768, 
        tabletBreakpoint: 1024 

      // Trigger resize event
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-tablet')).toHaveTextContent('true');
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('false');


    it('auto-closes sidebar when resizing from desktop to mobile', async () => {
      renderAppShell({ defaultSidebarOpen: true });

      // Initially desktop - sidebar should be open
      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

      // Resize to mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');
        expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');



  describe('Sidebar State Management', () => {
    it('toggles sidebar correctly on desktop', async () => {
      const user = userEvent.setup();
      renderAppShell({ defaultSidebarCollapsed: false });

      const toggleButton = screen.getByTestId('toggle-sidebar');
      
      // Initially expanded
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

      // Toggle to collapsed
      await user.click(toggleButton);
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true');

      // Toggle back to expanded
      await user.click(toggleButton);
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

    it('toggles sidebar correctly on mobile', async () => {
      const user = userEvent.setup();
      
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      renderAppShell({ defaultSidebarOpen: false });

      // Trigger resize to set mobile state
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');

      const toggleButton = screen.getByTestId('toggle-sidebar');
      
      // Initially closed
      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');

      // Toggle to open
      await user.click(toggleButton);
      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

      // Toggle back to closed
      await user.click(toggleButton);
      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');

    it('persists sidebar state to localStorage', async () => {
      const user = userEvent.setup();
      renderAppShell({ persistSidebarState: true });

      const toggleButton = screen.getByTestId('toggle-sidebar');
      await user.click(toggleButton);

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'appshell-sidebar-collapsed',
        'true'
      );

    it('loads sidebar state from localStorage', () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'appshell-sidebar-open') return 'false';
        if (key === 'appshell-sidebar-collapsed') return 'true';
        return null;

      renderAppShell({ persistSidebarState: true });

      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true');


  describe('Keyboard Navigation', () => {
    it('toggles sidebar with Ctrl+B', async () => {
      const user = userEvent.setup();
      renderAppShell({ enableKeyboardShortcuts: true });

      // Initially not collapsed
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

      // Press Ctrl+B
      await user.keyboard('{Control>}b{/Control}');

      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true');

    it('toggles sidebar with Cmd+B on Mac', async () => {
      const user = userEvent.setup();
      renderAppShell({ enableKeyboardShortcuts: true });

      // Initially not collapsed
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

      // Press Cmd+B
      await user.keyboard('{Meta>}b{/Meta}');

      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true');

    it('closes sidebar with Escape on mobile', async () => {
      const user = userEvent.setup();
      
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      renderAppShell({ 
        defaultSidebarOpen: true,
        enableKeyboardShortcuts: true 

      // Trigger resize to set mobile state
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');

      // Press Escape
      await user.keyboard('{Escape}');

      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');

    it('focuses sidebar with Alt+S', async () => {
      const user = userEvent.setup();
      renderAppShell({ enableKeyboardShortcuts: true });

      // Mock querySelector to return a focusable element
      const mockSidebar = {
        focus: vi.fn(),
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
      } as any;
      
      vi.spyOn(document, 'querySelector').mockImplementation((selector) => {
        if (selector === '[role="navigation"]') return mockSidebar;
        return null;

      // Press Alt+S
      await user.keyboard('{Alt>}s{/Alt}');

      expect(mockSidebar.focus).toHaveBeenCalled();

    it('focuses main content with Alt+M', async () => {
      const user = userEvent.setup();
      renderAppShell({ enableKeyboardShortcuts: true });

      // Mock querySelector to return a focusable element
      const mockMain = {
        focus: vi.fn(),
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
      } as any;
      
      vi.spyOn(document, 'querySelector').mockImplementation((selector) => {
        if (selector === 'main') return mockMain;
        return null;

      // Press Alt+M
      await user.keyboard('{Alt>}m{/Alt}');

      expect(mockMain.focus).toHaveBeenCalled();

    it('ignores keyboard shortcuts when typing in inputs', async () => {
      const user = userEvent.setup();
      renderAppShell({ enableKeyboardShortcuts: true });

      // Create and focus an input element
      const input = document.createElement('input');
      document.body.appendChild(input);
      input.focus();

      // Initially not collapsed
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

      // Press Ctrl+B while focused on input
      await user.keyboard('{Control>}b{/Control}');

      // Should not toggle sidebar
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

      // Cleanup
      document.body.removeChild(input);


  describe('Context API', () => {
    it('provides correct context values', () => {
      renderAppShell({
        defaultSidebarOpen: true,
        defaultSidebarCollapsed: false,

      expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

    it('throws error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAppShell must be used within an AppShell');

      consoleSpy.mockRestore();


  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      renderAppShell();

      expect(screen.getByRole('complementary')).toBeInTheDocument(); // aside
      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument(); // main
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer

    it('provides skip links functionality', async () => {
      const user = userEvent.setup();
      renderAppShell();

      // Test that main content is focusable
      const main = screen.getByRole('main');
      expect(main).toHaveAttribute('tabIndex', '-1');


  describe('Mobile Overlay', () => {
    it('shows overlay when sidebar is open on mobile', async () => {
      const user = userEvent.setup();
      
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      renderAppShell({ defaultSidebarOpen: false });

      // Trigger resize to set mobile state
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');

      // Open sidebar manually
      const openButton = screen.getByTestId('open-sidebar');
      await user.click(openButton);

      await waitFor(() => {
        expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

      // Check for overlay (it should be present)
      const overlay = document.querySelector('.fixed.inset-0');
      expect(overlay).toBeInTheDocument();

    it('closes sidebar when clicking overlay', async () => {
      const user = userEvent.setup();
      
      // Start with mobile viewport and closed sidebar
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,

      renderAppShell({ defaultSidebarOpen: false });

      // Trigger resize to set mobile state
      fireEvent.resize(window);

      await waitFor(() => {
        expect(screen.getByTestId('is-mobile')).toHaveTextContent('true');

      // Open sidebar manually
      const openButton = screen.getByTestId('open-sidebar');
      await user.click(openButton);

      await waitFor(() => {
        expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

      // Click overlay
      const overlay = document.querySelector('.fixed.inset-0');
      if (overlay) {
        await user.click(overlay);
        expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
      }


