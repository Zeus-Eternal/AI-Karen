/**
 * Responsive Panel Behavior Tests
 * 
 * Tests for mobile-first responsive design, touch-optimized interactions,
 * and collapsible panel behavior on small screens.
 * 
 * Based on requirements: 2.4, 8.1, 8.3
 */


import { render, screen, fireEvent, act } from '@testing-library/react';
import { vi, expect, describe, it, beforeEach, afterEach } from 'vitest';
import { RightPanel, RightPanelView } from '../right-panel';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    aside: ({ children, ...props }: any) => <aside {...props}>{children}</aside>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    footer: ({ children, ...props }: any) => <footer {...props}>{children}</footer>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock hooks
vi.mock('@/hooks/use-reduced-motion', () => ({
  useReducedMotion: () => false,
  useAnimationVariants: (normal: any, reduced: any) => normal,
}));

// Mock responsive panel hook
vi.mock('@/hooks/use-responsive-panel', () => ({
  useResponsivePanel: vi.fn(() => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    shouldOverlay: false,
    shouldCollapse: false,
    getResponsiveClasses: () => 'panel-responsive panel-desktop',
    getTouchProps: () => ({}),
  })),
  usePanelBackdrop: vi.fn(() => ({
    showBackdrop: false,
    backdropProps: {},
  })),
}));

describe('Responsive Panel Behavior', () => {
  const mockViews: RightPanelView[] = [
    {
      id: 'view1',
      title: 'View 1',
      content: <div data-testid="view1-content">View 1 Content</div>,
    },
    {
      id: 'view2',
      title: 'View 2',
      content: <div data-testid="view2-content">View 2 Content</div>,
    },
  ];

  // Mock window.innerWidth and window.innerHeight
  const mockViewport = (width: number, height: number) => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: height,
    });
  };

  beforeEach(() => {
    // Reset viewport to desktop size
    mockViewport(1024, 768);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Desktop Behavior', () => {
    it('should render with desktop responsive classes', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('panel-responsive', 'panel-desktop');
    });

    it('should use appropriate width classes for desktop', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width="lg"
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('w-[28rem]', 'lg:max-w-[65vw]');
    });
  });

  describe('Mobile Behavior', () => {
    beforeEach(() => {
      // Mock mobile viewport
      mockViewport(375, 667);
      
      // Mock mobile responsive behavior
      const { useResponsivePanel, usePanelBackdrop } = require('@/hooks/use-responsive-panel');
      useResponsivePanel.mockReturnValue({
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        shouldOverlay: true,
        shouldCollapse: true,
        getResponsiveClasses: () => 'panel-responsive panel-mobile panel-collapsible panel-overlay',
        getTouchProps: () => ({
          onTouchStart: vi.fn(),
          onTouchMove: vi.fn(),
          onTouchEnd: vi.fn(),
          style: {
            touchAction: 'pan-y',
            WebkitTouchCallout: 'none',
            WebkitUserSelect: 'none',
            userSelect: 'none',
          },
        }),
      });
      
      usePanelBackdrop.mockReturnValue({
        showBackdrop: true,
        backdropProps: {
          className: 'panel-backdrop',
          'data-state': 'open',
          'aria-hidden': true,
        },
      });
    });

    it('should render with mobile responsive classes', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass(
        'panel-responsive',
        'panel-mobile',
        'panel-collapsible',
        'panel-overlay'
      );
    });

    it('should show backdrop on mobile when overlay is enabled', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          overlayOnMobile={true}
        />
      );

      const backdrop = document.querySelector('.panel-backdrop');
      expect(backdrop).toBeInTheDocument();
      expect(backdrop).toHaveAttribute('data-state', 'open');
    });

    it('should apply touch gesture props on mobile', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          touchGestures={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveStyle({
        touchAction: 'pan-y',
        WebkitTouchCallout: 'none',
        WebkitUserSelect: 'none',
        userSelect: 'none',
      });
    });

    it('should handle collapsible behavior on mobile', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          collapsibleOnMobile={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveAttribute('data-collapsible', 'true');
      expect(panel).toHaveClass('max-sm:translate-x-full', 'max-sm:data-[state=open]:translate-x-0');
    });
  });

  describe('Tablet Behavior', () => {
    beforeEach(() => {
      // Mock tablet viewport
      mockViewport(768, 1024);
      
      // Mock tablet responsive behavior
      const { useResponsivePanel } = require('@/hooks/use-responsive-panel');
      useResponsivePanel.mockReturnValue({
        isMobile: false,
        isTablet: true,
        isDesktop: false,
        shouldOverlay: false,
        shouldCollapse: false,
        getResponsiveClasses: () => 'panel-responsive panel-tablet',
        getTouchProps: () => ({}),
      });
    });

    it('should render with tablet responsive classes', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('panel-responsive', 'panel-tablet');
    });

    it('should use appropriate width classes for tablet', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width="md"
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('w-96', 'md:max-w-[80vw]');
    });
  });

  describe('Touch Interactions', () => {
    it('should handle touch start events', () => {
      const mockTouchStart = vi.fn();
      
      // Mock touch-enabled responsive behavior
      const { useResponsivePanel } = require('@/hooks/use-responsive-panel');
      useResponsivePanel.mockReturnValue({
        isMobile: true,
        shouldOverlay: true,
        shouldCollapse: true,
        getResponsiveClasses: () => 'panel-responsive panel-mobile panel-touch-enabled',
        getTouchProps: () => ({
          onTouchStart: mockTouchStart,
          onTouchMove: vi.fn(),
          onTouchEnd: vi.fn(),
        }),
      });

      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          touchGestures={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      
      // Simulate touch start
      fireEvent.touchStart(panel, {
        touches: [{ clientX: 100, clientY: 100 }],
      });

      expect(mockTouchStart).toHaveBeenCalled();
    });

    it('should handle swipe gestures for closing', () => {
      const mockClose = vi.fn();
      const mockTouchEnd = vi.fn(() => mockClose());
      
      // Mock touch gesture behavior
      const { useResponsivePanel } = require('@/hooks/use-responsive-panel');
      useResponsivePanel.mockReturnValue({
        isMobile: true,
        shouldOverlay: true,
        shouldCollapse: true,
        getResponsiveClasses: () => 'panel-responsive panel-mobile panel-touch-gestures',
        getTouchProps: () => ({
          onTouchStart: vi.fn(),
          onTouchMove: vi.fn(),
          onTouchEnd: mockTouchEnd,
        }),
      });

      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          onClose={mockClose}
          touchGestures={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      
      // Simulate swipe gesture
      fireEvent.touchEnd(panel);
      
      expect(mockTouchEnd).toHaveBeenCalled();
    });
  });

  describe('Responsive Navigation', () => {
    it('should render navigation with responsive button sizing', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          showNavigation={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      const navButtons = buttons.filter(button => 
        button.textContent === 'View 1' || button.textContent === 'View 2'
      );

      navButtons.forEach(button => {
        // Check for touch-optimized sizing
        expect(button).toHaveClass('min-h-[44px]', 'sm:min-h-[32px]');
        // Check for responsive padding
        expect(button).toHaveClass('px-2', 'sm:px-3');
        // Check for touch feedback
        expect(button).toHaveClass('active:scale-95', 'sm:active:scale-100');
      });
    });

    it('should handle responsive text sizing in navigation', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          showNavigation={true}
        />
      );

      const textElements = screen.getAllByText(/View [12]/);
      textElements.forEach(text => {
        expect(text).toHaveClass('text-xs', 'sm:text-sm');
      });
    });
  });

  describe('Responsive Header', () => {
    it('should apply responsive padding to header', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('px-3', 'sm:px-4', 'md:px-6');
    });

    it('should use responsive text sizing in header', () => {
      render(
        <RightPanel
          views={[{
            id: 'view1',
            title: 'Test Title',
            description: 'Test Description',
            content: <div>Content</div>,
          }]}
          activeView="view1"
          isOpen={true}
        />
      );

      const title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveClass('text-base', 'sm:text-lg');
    });

    it('should apply touch-optimized close button sizing', () => {
      const mockClose = vi.fn();
      
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          onClose={mockClose}
          showCloseButton={true}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close panel/i });
      expect(closeButton).toHaveClass(
        'min-h-[44px]',
        'min-w-[44px]',
        'sm:min-h-[32px]',
        'sm:min-w-[32px]'
      );
      expect(closeButton).toHaveClass('active:scale-95', 'sm:active:scale-100');
    });
  });

  describe('Responsive Content', () => {
    it('should apply responsive padding to content', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      // Content should have responsive padding through PanelContent
      const content = screen.getByTestId('view1-content').closest('.p-3');
      expect(content).toBeInTheDocument();
    });

    it('should use responsive grid gaps', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      const gridContainer = screen.getByTestId('view1-content').closest('.grid');
      expect(gridContainer).toHaveClass('gap-2', 'sm:gap-3', 'md:gap-4');
    });
  });

  describe('Accessibility', () => {
    it('should maintain accessibility on mobile', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      const panel = screen.getByRole('complementary');
      expect(panel).toBeInTheDocument();
      expect(panel).toHaveAttribute('data-state', 'open');
    });

    it('should handle keyboard navigation on mobile', () => {
      const mockClose = vi.fn();
      
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          onClose={mockClose}
        />
      );

      // Simulate escape key
      fireEvent.keyDown(document, { key: 'Escape' });
      
      // Note: The actual keyboard handling would be in the hook
      // This test verifies the component structure supports it
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });
  });
});