/**
 * Right Panel Viewport Height Tests
 * 
 * Tests to ensure the right panel properly fits within the viewport
 * and handles different screen sizes correctly.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RightPanel, type RightPanelView } from '../right-panel';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    aside: React.forwardRef<HTMLElement, any>(({ children, ...props }, ref) => (
      <aside ref={ref} {...props}>{children}</aside>
    )),
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    footer: React.forwardRef<HTMLElement, any>(({ children, ...props }, ref) => (
      <footer ref={ref} {...props}>{children}</footer>
    )),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock the useReducedMotion hook
vi.mock('@/hooks/use-reduced-motion', () => ({
  useReducedMotion: vi.fn(() => false),
  useAnimationDuration: vi.fn((normal, reduced) => normal),
  useAnimationVariants: vi.fn((normal, reduced) => normal),
}));

describe('RightPanel Viewport Height', () => {
  const mockViews: RightPanelView[] = [
    {
      id: 'view1',
      title: 'Test View 1',
      content: <div>Test content 1</div>,
    },
    {
      id: 'view2',
      title: 'Test View 2',
      content: <div>Test content 2</div>,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock viewport dimensions
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 800,

    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,


  it('should apply viewport height classes', () => {
    render(
      <RightPanel
        views={mockViews}
        activeView="view1"
        isOpen={true}
      />
    );

    const panel = screen.getByRole('complementary');
    expect(panel).toHaveClass('panel-viewport-height');

  it('should handle mobile viewport correctly', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,

    render(
      <RightPanel
        views={mockViews}
        activeView="view1"
        isOpen={true}
        overlayOnMobile={true}
      />
    );

    const panel = screen.getByRole('complementary');
    expect(panel).toHaveClass('panel-viewport-height');

  it('should ensure content area is scrollable', () => {
    render(
      <RightPanel
        views={mockViews}
        activeView="view1"
        isOpen={true}
      />
    );

    // Check that content area has proper overflow handling
    const contentArea = screen.getByText('Test content 1').closest('.overflow-y-auto');
    expect(contentArea).toBeInTheDocument();
    expect(contentArea).toHaveClass('scrollbar-hide');

  it('should handle long content without breaking viewport', () => {
    const longContentViews: RightPanelView[] = [
      {
        id: 'long-view',
        title: 'Long Content View',
        content: (
          <div>
            {Array.from({ length: 100 }, (_, i) => (
              <div key={i} style={{ height: '50px' }}>
                Long content item {i + 1}
              </div>
            ))}
          </div>
        ),
      },
    ];

    render(
      <RightPanel
        views={longContentViews}
        activeView="long-view"
        isOpen={true}
      />
    );

    const panel = screen.getByRole('complementary');
    expect(panel).toHaveClass('overflow-hidden');
    expect(panel).toHaveClass('panel-viewport-height');

  it('should maintain proper flex layout structure', () => {
    render(
      <RightPanel
        views={mockViews}
        activeView="view1"
        isOpen={true}
        showNavigation={true}
      />
    );

    const panel = screen.getByRole('complementary');
    expect(panel).toHaveClass('flex', 'flex-col');
    
    // Content should be flex-1 to take remaining space
    const contentWrapper = panel.querySelector('.flex-1.min-h-0');
    expect(contentWrapper).toBeInTheDocument();

  it('should handle different panel widths correctly', () => {
    const widths = ['sm', 'md', 'lg', 'xl'] as const;
    
    widths.forEach((width) => {
      const { unmount } = render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width={width}
        />
      );

      const panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('panel-viewport-height');
      
      unmount();


