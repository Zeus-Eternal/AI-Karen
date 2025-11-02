/**
 * Basic Responsive Panel Tests
 * 
 * Tests for basic responsive behavior and CSS classes
 * 
 * Based on requirements: 2.4, 8.1, 8.3
 */


import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, expect, describe, it } from 'vitest';
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

vi.mock('@/hooks/use-responsive-panel', () => ({
  useResponsivePanel: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    shouldOverlay: false,
    shouldCollapse: false,
    getResponsiveClasses: () => 'panel-responsive panel-desktop',
    getTouchProps: () => ({}),
  }),
  usePanelBackdrop: () => ({
    showBackdrop: false,
    backdropProps: {},
  }),
}));

describe('Basic Responsive Panel Behavior', () => {
  const mockViews: RightPanelView[] = [
    {
      id: 'view1',
      title: 'View 1',
      content: <div data-testid="view1-content">View 1 Content</div>,
    },
  ];

  describe('Responsive Width Classes', () => {
    it('should apply responsive width classes for small panels', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width="sm"
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('w-80');
      expect(panel).toHaveClass('max-w-[90vw]');
      expect(panel).toHaveClass('sm:max-w-[85vw]');
      expect(panel).toHaveClass('lg:max-w-[75vw]');

    it('should apply responsive width classes for medium panels', () => {
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
      expect(panel).toHaveClass('w-96');
      expect(panel).toHaveClass('max-w-[90vw]');
      expect(panel).toHaveClass('md:max-w-[80vw]');
      expect(panel).toHaveClass('lg:max-w-[70vw]');

    it('should apply responsive width classes for large panels', () => {
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
      expect(panel).toHaveClass('w-[28rem]');
      expect(panel).toHaveClass('max-w-[90vw]');
      expect(panel).toHaveClass('md:max-w-[75vw]');
      expect(panel).toHaveClass('lg:max-w-[65vw]');


  describe('Responsive Header', () => {
    it('should apply responsive padding to header', () => {
      render(
        <RightPanel
          views={[{
            id: 'view1',
            title: 'Test Title',
            content: <div>Content</div>,
          }]}
          activeView="view1"
          isOpen={true}
        />
      );

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('px-3');
      expect(header).toHaveClass('sm:px-4');
      expect(header).toHaveClass('md:px-6');

    it('should apply responsive text sizing to title', () => {
      render(
        <RightPanel
          views={[{
            id: 'view1',
            title: 'Test Title',
            content: <div>Content</div>,
          }]}
          activeView="view1"
          isOpen={true}
        />
      );

      const title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveClass('text-base');
      expect(title).toHaveClass('sm:text-lg');

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
      expect(closeButton).toHaveClass('min-h-[44px]');
      expect(closeButton).toHaveClass('min-w-[44px]');
      expect(closeButton).toHaveClass('sm:min-h-[32px]');
      expect(closeButton).toHaveClass('sm:min-w-[32px]');


  describe('Responsive Navigation', () => {
    it('should apply responsive padding to navigation', () => {
      render(
        <RightPanel
          views={[
            { id: 'view1', title: 'View 1', content: <div>Content 1</div> },
            { id: 'view2', title: 'View 2', content: <div>Content 2</div> },
          ]}
          activeView="view1"
          isOpen={true}
          showNavigation={true}
        />
      );

      const navigation = screen.getByRole('navigation');
      expect(navigation).toHaveClass('px-3');
      expect(navigation).toHaveClass('sm:px-4');
      expect(navigation).toHaveClass('md:px-6');

    it('should apply touch-optimized button sizing', () => {
      render(
        <RightPanel
          views={[
            { id: 'view1', title: 'View 1', content: <div>Content 1</div> },
            { id: 'view2', title: 'View 2', content: <div>Content 2</div> },
          ]}
          activeView="view1"
          isOpen={true}
          showNavigation={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      const navButtons = buttons.filter(button => 
        button.textContent?.includes('View 1') || button.textContent?.includes('View 2')
      );

      navButtons.forEach(button => {
        expect(button).toHaveClass('min-h-[44px]');
        expect(button).toHaveClass('sm:min-h-[32px]');
        expect(button).toHaveClass('px-2');
        expect(button).toHaveClass('sm:px-3');



  describe('Responsive Content', () => {
    it('should apply responsive padding to content', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      // Check that content container has responsive padding
      const content = screen.getByTestId('view1-content').closest('.p-3');
      expect(content).toBeInTheDocument();

    it('should apply responsive grid gaps', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      const gridContainer = screen.getByTestId('view1-content').closest('.grid');
      expect(gridContainer).toHaveClass('gap-2');
      expect(gridContainer).toHaveClass('sm:gap-3');
      expect(gridContainer).toHaveClass('md:gap-4');


  describe('Data Attributes', () => {
    it('should set proper data attributes for responsive behavior', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          collapsibleOnMobile={true}
          overlayOnMobile={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveAttribute('data-state', 'open');
      expect(panel).toHaveAttribute('data-mobile-overlay', 'false'); // false because mock shows desktop
      expect(panel).toHaveAttribute('data-collapsible', 'false'); // false because mock shows desktop

    it('should apply responsive classes from hook', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('panel-responsive');
      expect(panel).toHaveClass('panel-desktop');


  describe('Touch Optimization', () => {
    it('should have touch gesture support enabled', () => {
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
      // Verify the component renders with touch gestures enabled
      expect(panel).toBeInTheDocument();

    it('should apply performance optimization styles', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      expect(panel).toHaveStyle({
        contain: 'layout style paint',



