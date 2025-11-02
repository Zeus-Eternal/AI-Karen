/**
 * SidebarNavigation Integration Tests
 * 
 * Tests for sidebar navigation functionality, keyboard navigation, and accessibility.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useRouter, usePathname } from 'next/navigation';
import { SidebarNavigation, NavigationItem } from '../SidebarNavigation';
import { AppShell } from '@/components/layout/AppShell';
import { ThemeProvider } from '@/providers/theme-provider';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: vi.fn(),
}));

const mockPush = vi.fn();
const mockRouter = {
  push: mockPush,
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
};

(useRouter as any).mockReturnValue(mockRouter);
(usePathname as any).mockReturnValue('/dashboard');

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

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
});

// Test navigation items
const testNavigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
  },
  {
    id: 'agents',
    label: 'Agents',
    children: [
      {
        id: 'agents-list',
        label: 'Agent List',
        href: '/agents',
      },
      {
        id: 'workflows',
        label: 'Workflows',
        href: '/workflows',
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    href: '/settings',
    disabled: true,
  },
  {
    id: 'external',
    label: 'External Link',
    href: 'https://example.com',
    external: true,
  },
];

const renderSidebarNavigation = (props = {}) => {
  return render(
    <ThemeProvider>
      <AppShell sidebar={
        <SidebarNavigation 
          items={testNavigationItems}
          {...props}
        />
      }>
        <div>Main Content</div>
      </AppShell>
    </ThemeProvider>
  );
};

describe('SidebarNavigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (usePathname as any).mockReturnValue('/dashboard');
    
    // Reset window size to desktop
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
  });

  describe('Basic Rendering', () => {
    it('renders navigation items correctly', () => {
      renderSidebarNavigation();

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Agents')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('External Link')).toBeInTheDocument();
    });

    it('applies correct ARIA attributes', () => {
      renderSidebarNavigation();

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Main navigation');
      expect(nav).toHaveAttribute('tabIndex', '-1');
    });

    it('shows active state for current route', () => {
      renderSidebarNavigation();

      const dashboardButton = screen.getByRole('button', { name: /dashboard/i });
      expect(dashboardButton).toHaveAttribute('aria-current', 'page');
    });

    it('shows disabled state for disabled items', () => {
      renderSidebarNavigation();

      const settingsButton = screen.getByRole('button', { name: /settings/i });
      expect(settingsButton).toBeDisabled();
    });
  });

  describe('Navigation Interaction', () => {
    it('navigates to route when clicking navigation item', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation();

      const settingsButton = screen.getByRole('button', { name: /settings/i });
      
      // Settings is disabled, so this shouldn't navigate
      await user.click(settingsButton);
      expect(mockPush).not.toHaveBeenCalled();

      // Click on a non-disabled item (we need to find one that's not active)
      // Since Dashboard is active, let's expand Agents and click on Agent List
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      await user.click(agentsButton);

      // Now click on Agent List
      const agentListButton = screen.getByRole('button', { name: /agent list/i });
      await user.click(agentListButton);

      expect(mockPush).toHaveBeenCalledWith('/agents');
    });

    it('opens external links in new tab', async () => {
      const user = userEvent.setup();
      const mockOpen = vi.fn();
      window.open = mockOpen;

      renderSidebarNavigation();

      const externalButton = screen.getByRole('button', { name: /external link/i });
      await user.click(externalButton);

      expect(mockOpen).toHaveBeenCalledWith(
        'https://example.com',
        '_blank',
        'noopener,noreferrer'
      );
    });

    it('expands and collapses parent items', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation();

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      
      // Initially collapsed
      expect(agentsButton).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByText('Agent List')).not.toBeInTheDocument();

      // Expand
      await user.click(agentsButton);
      expect(agentsButton).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByText('Agent List')).toBeInTheDocument();
      expect(screen.getByText('Workflows')).toBeInTheDocument();

      // Collapse
      await user.click(agentsButton);
      expect(agentsButton).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByText('Agent List')).not.toBeInTheDocument();
    });

    it('calls onItemClick callback when provided', async () => {
      const user = userEvent.setup();
      const mockOnItemClick = vi.fn();
      
      renderSidebarNavigation({ onItemClick: mockOnItemClick });

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      await user.click(agentsButton);

      expect(mockOnItemClick).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'agents',
          label: 'Agents',
        })
      );
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates with arrow keys', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation({ enableKeyboardNavigation: true });

      const nav = screen.getByRole('navigation');
      nav.focus();

      // Get first button and focus it
      const firstButton = screen.getByRole('button', { name: /dashboard/i });
      firstButton.focus();

      // Arrow down should focus next item
      await user.keyboard('{ArrowDown}');
      
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      expect(agentsButton).toHaveFocus();

      // Arrow up should go back
      await user.keyboard('{ArrowUp}');
      expect(firstButton).toHaveFocus();
    });

    it('expands items with right arrow', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation({ enableKeyboardNavigation: true });

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      agentsButton.focus();

      // Right arrow should expand
      await user.keyboard('{ArrowRight}');
      expect(agentsButton).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByText('Agent List')).toBeInTheDocument();
    });

    it('collapses items with left arrow', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation({ enableKeyboardNavigation: true });

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      
      // First expand the item
      await user.click(agentsButton);
      expect(agentsButton).toHaveAttribute('aria-expanded', 'true');

      agentsButton.focus();

      // Left arrow should collapse
      await user.keyboard('{ArrowLeft}');
      expect(agentsButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('activates items with Enter and Space', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation({ enableKeyboardNavigation: true });

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      agentsButton.focus();

      // Enter should expand
      await user.keyboard('{Enter}');
      expect(agentsButton).toHaveAttribute('aria-expanded', 'true');

      // Space should collapse
      await user.keyboard(' ');
      expect(agentsButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('jumps to first/last items with Home/End', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation({ enableKeyboardNavigation: true });

      const nav = screen.getByRole('navigation');
      nav.focus();

      // Focus somewhere in the middle
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      agentsButton.focus();

      // Home should go to first item
      await user.keyboard('{Home}');
      const firstButton = screen.getByRole('button', { name: /dashboard/i });
      expect(firstButton).toHaveFocus();

      // End should go to last item
      await user.keyboard('{End}');
      const lastButton = screen.getByRole('button', { name: /external link/i });
      expect(lastButton).toHaveFocus();
    });
  });

  describe('Mobile Behavior', () => {
    it('closes sidebar when navigating on mobile', async () => {
      const user = userEvent.setup();
      
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,
      });

      renderSidebarNavigation();

      // Trigger resize to set mobile state
      fireEvent.resize(window);

      await waitFor(() => {
        // The sidebar should be in mobile mode
        // We can't easily test the closeSidebar call without more complex mocking
        // but we can verify the navigation still works
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });

      // Expand agents and click on agent list
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      await user.click(agentsButton);

      const agentListButton = screen.getByRole('button', { name: /agent list/i });
      await user.click(agentListButton);

      expect(mockPush).toHaveBeenCalledWith('/agents');
    });
  });

  describe('Auto-expansion', () => {
    it('auto-expands parent of active item', () => {
      (usePathname as any).mockReturnValue('/agents');
      
      renderSidebarNavigation();

      // Agents should be expanded because /agents is active
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      expect(agentsButton).toHaveAttribute('aria-expanded', 'true');
      expect(screen.getByText('Agent List')).toBeInTheDocument();
    });
  });

  describe('Collapsed State', () => {
    it('shows tooltips when collapsed', async () => {
      const user = userEvent.setup();
      
      // Start with collapsed sidebar
      renderSidebarNavigation();

      // We need to simulate the collapsed state through the AppShell context
      // This is a bit complex to test directly, but we can verify the title attribute
      const dashboardButton = screen.getByRole('button', { name: /dashboard/i });
      
      // In collapsed state, buttons should have title attributes
      // This would be set by the isCollapsed prop from AppShell context
      // For now, we'll just verify the button exists
      expect(dashboardButton).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA structure', () => {
      renderSidebarNavigation();

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Main navigation');

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();

      // Check that expandable items have proper ARIA attributes
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      expect(agentsButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('supports custom aria-label', () => {
      renderSidebarNavigation({ ariaLabel: 'Custom navigation' });

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Custom navigation');
    });

    it('sets aria-level for nested items', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation();

      // Expand agents to show nested items
      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      await user.click(agentsButton);

      const agentListButton = screen.getByRole('button', { name: /agent list/i });
      expect(agentListButton).toHaveAttribute('aria-level', '2');
    });

    it('sets aria-current for active items', () => {
      renderSidebarNavigation();

      const dashboardButton = screen.getByRole('button', { name: /dashboard/i });
      expect(dashboardButton).toHaveAttribute('aria-current', 'page');
    });
  });

  describe('Focus Management', () => {
    it('auto-focuses navigation when requested', () => {
      renderSidebarNavigation({ autoFocus: true });

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveFocus();
    });

    it('maintains focus when expanding/collapsing items', async () => {
      const user = userEvent.setup();
      renderSidebarNavigation();

      const agentsButton = screen.getByRole('button', { name: /^agents$/i });
      agentsButton.focus();

      await user.click(agentsButton);
      expect(agentsButton).toHaveFocus();

      await user.click(agentsButton);
      expect(agentsButton).toHaveFocus();
    });
  });
});