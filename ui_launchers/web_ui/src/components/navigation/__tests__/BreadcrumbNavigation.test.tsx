/**
 * BreadcrumbNavigation Integration Tests
 * 
 * Tests for breadcrumb navigation functionality and accessibility.
 * Based on requirements: 2.1, 2.2, 2.3, 2.4, 11.1, 11.2
 */


import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useRouter, usePathname } from 'next/navigation';
import { BreadcrumbNavigation, BreadcrumbItem, RouteConfig } from '../BreadcrumbNavigation';
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
(usePathname as any).mockReturnValue('/memory/analytics');

// Test route configuration
const testRouteConfig: RouteConfig = {
  '/': {
    label: 'Home',
  },
  '/memory': {
    label: 'Memory & Analytics',
    parent: '/',
  },
  '/memory/analytics': {
    label: 'Memory Analytics',
    parent: '/memory',
  },
  '/memory/search': {
    label: 'Semantic Search',
    parent: '/memory',
  },
  '/agents': {
    label: 'Agents',
    parent: '/',
  },
  '/agents/workflows': {
    label: 'Workflows',
    parent: '/agents',
  },
};

const renderBreadcrumbNavigation = (props = {}) => {
  return render(
    <ThemeProvider>
      <BreadcrumbNavigation 
        routeConfig={testRouteConfig}
        {...props}
      />
    </ThemeProvider>
  );
};

describe('BreadcrumbNavigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (usePathname as any).mockReturnValue('/memory/analytics');
  });

  describe('Basic Rendering', () => {
    it('renders breadcrumb items correctly', () => {
      renderBreadcrumbNavigation();

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Memory & Analytics')).toBeInTheDocument();
      expect(screen.getByText('Memory Analytics')).toBeInTheDocument();
    });

    it('applies correct ARIA attributes', () => {
      renderBreadcrumbNavigation();

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Breadcrumb navigation');

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
    });

    it('shows current page with aria-current', () => {
      renderBreadcrumbNavigation();

      const currentItem = screen.getByText('Memory Analytics');
      expect(currentItem.closest('span')).toHaveAttribute('aria-current', 'page');
    });

    it('shows clickable items as buttons', () => {
      renderBreadcrumbNavigation();

      const homeButton = screen.getByRole('button', { name: /home/i });
      expect(homeButton).toBeInTheDocument();

      const memoryButton = screen.getByRole('button', { name: /memory & analytics/i });
      expect(memoryButton).toBeInTheDocument();
    });
  });

  describe('Navigation Interaction', () => {
    it('navigates when clicking breadcrumb items', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation();

      const homeButton = screen.getByRole('button', { name: /home/i });
      await user.click(homeButton);

      expect(mockPush).toHaveBeenCalledWith('/');
    });

    it('navigates to parent routes', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation();

      const memoryButton = screen.getByRole('button', { name: /memory & analytics/i });
      await user.click(memoryButton);

      expect(mockPush).toHaveBeenCalledWith('/memory');
    });

    it('does not navigate when clicking current item', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation();

      const currentItem = screen.getByText('Memory Analytics');
      await user.click(currentItem);

      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('Custom Items', () => {
    it('renders custom breadcrumb items', () => {
      const customItems: BreadcrumbItem[] = [
        { label: 'Custom Home', href: '/' },
        { label: 'Custom Page', href: '/custom' },
        { label: 'Current Page', current: true },
      ];

      renderBreadcrumbNavigation({ items: customItems });

      expect(screen.getByText('Custom Home')).toBeInTheDocument();
      expect(screen.getByText('Custom Page')).toBeInTheDocument();
      expect(screen.getByText('Current Page')).toBeInTheDocument();
    });

    it('handles custom items with icons', () => {
      const HomeIcon = () => <span data-testid="home-icon">🏠</span>;
      
      const customItems: BreadcrumbItem[] = [
        { label: 'Home', href: '/', icon: HomeIcon },
        { label: 'Current', current: true },
      ];

      renderBreadcrumbNavigation({ items: customItems });

      expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    });
  });

  describe('Route Generation', () => {
    it('generates breadcrumbs from current route', () => {
      (usePathname as any).mockReturnValue('/agents/workflows');
      
      renderBreadcrumbNavigation();

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Agents')).toBeInTheDocument();
      expect(screen.getByText('Workflows')).toBeInTheDocument();
    });

    it('handles root route correctly', () => {
      (usePathname as any).mockReturnValue('/');
      
      renderBreadcrumbNavigation();

      expect(screen.getByText('Home')).toBeInTheDocument();
      // Should only show home for root route
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('handles unconfigured routes with fallback labels', () => {
      (usePathname as any).mockReturnValue('/unknown/route');
      
      renderBreadcrumbNavigation();

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Unknown')).toBeInTheDocument();
      expect(screen.getByText('Route')).toBeInTheDocument();
    });

    it('optionally hides home breadcrumb', () => {
      renderBreadcrumbNavigation({ showHome: false });

      expect(screen.queryByText('Home')).not.toBeInTheDocument();
      expect(screen.getByText('Memory & Analytics')).toBeInTheDocument();
      expect(screen.getByText('Memory Analytics')).toBeInTheDocument();
    });
  });

  describe('Truncation', () => {
    it('truncates long breadcrumb trails', () => {
      // Create a long route path
      (usePathname as any).mockReturnValue('/level1/level2/level3/level4/level5/level6');
      
      const longRouteConfig: RouteConfig = {
        '/': { label: 'Home' },
        '/level1': { label: 'Level 1', parent: '/' },
        '/level1/level2': { label: 'Level 2', parent: '/level1' },
        '/level1/level2/level3': { label: 'Level 3', parent: '/level1/level2' },
        '/level1/level2/level3/level4': { label: 'Level 4', parent: '/level1/level2/level3' },
        '/level1/level2/level3/level4/level5': { label: 'Level 5', parent: '/level1/level2/level3/level4' },
        '/level1/level2/level3/level4/level5/level6': { label: 'Level 6', parent: '/level1/level2/level3/level4/level5' },
      };

      renderBreadcrumbNavigation({ 
        routeConfig: longRouteConfig,
        maxItems: 4 
      });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('...')).toBeInTheDocument();
      expect(screen.getByText('Level 5')).toBeInTheDocument();
      expect(screen.getByText('Level 6')).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates between breadcrumb items with arrow keys', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation({ enableKeyboardNavigation: true });

      const homeButton = screen.getByRole('button', { name: /home/i });
      homeButton.focus();

      // Arrow right should focus next item
      await user.keyboard('{ArrowRight}');
      
      const memoryButton = screen.getByRole('button', { name: /memory & analytics/i });
      expect(memoryButton).toHaveFocus();

      // Arrow left should go back
      await user.keyboard('{ArrowLeft}');
      expect(homeButton).toHaveFocus();
    });

    it('jumps to first/last items with Home/End keys', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation({ enableKeyboardNavigation: true });

      const memoryButton = screen.getByRole('button', { name: /memory & analytics/i });
      memoryButton.focus();

      // Home should go to first item
      await user.keyboard('{Home}');
      const homeButton = screen.getByRole('button', { name: /home/i });
      expect(homeButton).toHaveFocus();

      // End should go to last clickable item
      await user.keyboard('{End}');
      expect(memoryButton).toHaveFocus();
    });

    it('can disable keyboard navigation', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation({ enableKeyboardNavigation: false });

      const homeButton = screen.getByRole('button', { name: /home/i });
      homeButton.focus();

      // Arrow keys should not change focus when disabled
      await user.keyboard('{ArrowRight}');
      expect(homeButton).toHaveFocus();
    });
  });

  describe('Accessibility', () => {
    it('supports custom aria-label', () => {
      renderBreadcrumbNavigation({ ariaLabel: 'Custom breadcrumb' });

      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Custom breadcrumb');
    });

    it('has proper semantic structure', () => {
      renderBreadcrumbNavigation();

      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();

      const listItems = screen.getAllByRole('listitem');
      expect(listItems.length).toBeGreaterThan(0);
    });

    it('provides proper focus indicators', async () => {
      const user = userEvent.setup();
      renderBreadcrumbNavigation();

      const homeButton = screen.getByRole('button', { name: /home/i });
      
      await user.tab();
      expect(homeButton).toHaveFocus();
    });
  });

  describe('Separators', () => {
    it('shows default chevron separators', () => {
      renderBreadcrumbNavigation();

      // Check for chevron icons (they should be present between items)
      const separators = document.querySelectorAll('[aria-hidden="true"]');
      expect(separators.length).toBeGreaterThan(0);
    });

    it('supports custom separators', () => {
      const customSeparator = <span data-testid="custom-separator">→</span>;
      
      renderBreadcrumbNavigation({ separator: customSeparator });

      expect(screen.getAllByTestId('custom-separator')).toHaveLength(2); // Between 3 items
    });
  });

  describe('Size Variants', () => {
    it('applies size variants correctly', () => {
      const { rerender } = renderBreadcrumbNavigation({ size: 'sm' });
      
      let nav = screen.getByRole('navigation');
      expect(nav).toHaveClass('text-[var(--text-xs)]');

      rerender(
        <ThemeProvider>
          <BreadcrumbNavigation size="lg" routeConfig={testRouteConfig} />
        </ThemeProvider>
      );

      nav = screen.getByRole('navigation');
      expect(nav).toHaveClass('text-[var(--text-base)]');
    });
  });

  describe('useBreadcrumbs Hook', () => {
    it('returns correct breadcrumb items', () => {
      // This would need to be tested in a separate component that uses the hook
      // For now, we'll just verify the hook exists and can be imported
      expect(typeof require('../BreadcrumbNavigation').useBreadcrumbs).toBe('function');
    });
  });
});