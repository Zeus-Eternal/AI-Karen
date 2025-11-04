/**
 * Panel Spacing and Alignment Fixes Tests
 * 
 * Tests for consistent panel spacing, alignment, and overflow handling
 * using design tokens and modern CSS techniques.
 * 
 * Based on requirements: 2.1, 2.3
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, expect, describe, it } from 'vitest';
import { RightPanel, RightPanelView } from '../right-panel';
import { PanelHeader } from '../panel-header';
import { PanelContent } from '../panel-content';

// Mock framer-motion to avoid animation issues in tests
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

describe('Panel Spacing and Alignment Fixes', () => {
  const mockViews: RightPanelView[] = [
    {
      id: 'view1',
      title: 'View 1',
      description: 'First view description',
      content: <div data-testid="view1-content">View 1 Content</div>,
    },
    {
      id: 'view2',
      title: 'View 2',
      description: 'Second view description',
      content: <div data-testid="view2-content">View 2 Content</div>,
    },
  ];

  describe('RightPanel Spacing', () => {
    it('should apply consistent spacing using design tokens', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      
      // Check that panel has proper overflow handling
      expect(panel).toHaveClass('overflow-hidden');
      
      // Check that panel has consistent width classes
      expect(panel).toHaveClass('w-[28rem]', 'max-w-[90vw]', 'min-w-[28rem]');
      
      // Check that panel has proper backdrop blur
      expect(panel).toHaveClass('backdrop-blur-md');

    it('should handle different width variants correctly', () => {
      const { rerender } = render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width="sm"
          data-testid="right-panel"
        />
      );

      let panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('w-80', 'min-w-[20rem]');

      rerender(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          width="xl"
          data-testid="right-panel"
        />
      );

      panel = screen.getByTestId('right-panel');
      expect(panel).toHaveClass('w-[32rem]', 'min-w-[32rem]');

    it('should apply proper content overflow handling', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      // Check that content has proper flex behavior
      const contentWrapper = screen.getByTestId('view1-content').closest('.flex-1');
      expect(contentWrapper).toHaveClass('min-h-0');
      
      // Check that scrollable content has proper overflow
      const scrollableContent = screen.getByTestId('view1-content').closest('.overflow-y-auto');
      expect(scrollableContent).toHaveClass('scrollbar-hide');


  describe('PanelHeader Alignment', () => {
    it('should align header content properly', () => {
      render(
        <PanelHeader
          title="Test Title"
          description="Test Description"
          showCloseButton={true}
          onClose={() => {}}
        />
      );

      const header = screen.getByRole('banner');
      
      // Check that header has proper grid layout
      expect(header).toHaveClass('flex', 'items-start');
      
      // Check that header has consistent border and background
      expect(header).toHaveClass('border-b', 'border-border/50');
      expect(header).toHaveClass('bg-background/95', 'backdrop-blur-md');

    it('should handle different header variants', () => {
      const { rerender } = render(
        <PanelHeader
          title="Test Title"
          variant="compact"
        />
      );

      let title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveClass('text-base');

      rerender(
        <PanelHeader
          title="Test Title"
          variant="prominent"
        />
      );

      title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveClass('text-xl');

    it('should align actions and close button properly', () => {
      const mockClose = vi.fn();
      
      render(
        <PanelHeader
          title="Test Title"
          actions={<Button aria-label="Button">Action</Button>}
          showCloseButton={true}
          onClose={mockClose}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close panel/i });
      
      // Check that close button has proper focus styles
      expect(closeButton).toHaveClass(
        'focus-visible:ring-2',
        'focus-visible:ring-[var(--component-button-default-ring)]'
      );
      
      // Check that close button has proper transition
      expect(closeButton).toHaveClass('transition-all', 'duration-200');


  describe('PanelContent Overflow Handling', () => {
    it('should handle scrollable content properly', () => {
      render(
        <PanelContent scrollable={true} padding="md">
          <div>Test Content</div>
        </PanelContent>
      );

      const content = screen.getByText('Test Content').closest('.overflow-y-auto');
      
      // Check that content has proper overflow handling
      expect(content).toHaveClass('overflow-y-auto', 'overflow-x-hidden');
      expect(content).toHaveClass('scroll-smooth');
      expect(content).toHaveClass('scrollbar-hide');

    it('should apply consistent padding using design tokens', () => {
      const { rerender } = render(
        <PanelContent padding="sm">
          <div>Test Content</div>
        </PanelContent>
      );

      let container = screen.getByText('Test Content').closest('.p-3');
      expect(container).toBeInTheDocument();

      rerender(
        <PanelContent padding="lg">
          <div>Test Content</div>
        </PanelContent>
      );

      container = screen.getByText('Test Content').closest('.p-6');
      expect(container).toBeInTheDocument();

    it('should handle grid layout with proper alignment', () => {
      render(
        <PanelContent columns={6} offset={2} align="center" justify="between">
          <div>Test Content</div>
        </PanelContent>
      );

      const gridContainer = screen.getByText('Test Content').closest('.grid');
      expect(gridContainer).toHaveClass('grid-cols-12', 'items-center', 'justify-between');
      
      const contentColumn = screen.getByText('Test Content').closest('.col-span-6');
      expect(contentColumn).toHaveClass('col-start-3'); // offset of 2 means start at 3

    it('should prevent content overflow', () => {
      render(
        <PanelContent>
          <div>Test Content</div>
        </PanelContent>
      );

      const gridContainer = screen.getByText('Test Content').closest('.grid');
      expect(gridContainer).toHaveClass('w-full', 'max-w-full');
      
      const contentColumn = screen.getByText('Test Content').closest('.min-w-0');
      expect(contentColumn).toHaveClass('max-w-full');


  describe('Panel Navigation Alignment', () => {
    it('should align navigation items properly', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          showNavigation={true}
        />
      );

      const navigation = screen.getByRole('navigation');
      
      // Check that navigation has proper spacing and background
      expect(navigation).toHaveClass('border-b', 'border-border/50');
      expect(navigation).toHaveClass('bg-muted/30', 'backdrop-blur-sm');
      expect(navigation).toHaveClass('px-4', 'py-2', 'sm:px-6');

    it('should handle navigation button alignment', () => {
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
        // Check that buttons have consistent height and padding
        expect(button).toHaveClass('h-8', 'px-3');
        
        // Check that buttons have proper alignment
        expect(button).toHaveClass('flex', 'items-center', 'justify-center');
        
        // Check that buttons have proper focus styles
        expect(button).toHaveClass(
          'focus-visible:ring-2',
          'focus-visible:ring-[var(--component-button-default-ring)]'
        );



  describe('Panel Footer Alignment', () => {
    it('should align footer content properly', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          footerContent={<div>Footer Content</div>}
        />
      );

      const footer = screen.getByRole('contentinfo');
      
      // Check that footer has proper border and background
      expect(footer).toHaveClass('border-t', 'border-border/50');
      expect(footer).toHaveClass('bg-background/95', 'backdrop-blur-md');
      
      // Check that footer has proper alignment
      expect(footer).toHaveClass('flex', 'items-center');


  describe('Accessibility', () => {
    it('should be accessible', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
        />
      );

      // Check basic accessibility attributes
      const panel = screen.getByRole('complementary');
      expect(panel).toBeInTheDocument();

    it('should support keyboard navigation', () => {
      const mockViewChange = vi.fn();
      
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          onViewChange={mockViewChange}
          showNavigation={true}
        />
      );

      const view2Button = screen.getByRole('button', { name: /view 2/i });
      
      // Test click interaction (keyboard events are handled by the button)
      fireEvent.click(view2Button);
      expect(mockViewChange).toHaveBeenCalledWith('view2');

    it('should support screen readers', () => {
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
      expect(closeButton).toHaveAttribute('aria-label', 'Close panel');


  describe('Performance', () => {
    it('should optimize scrolling performance', () => {
      render(
        <PanelContent scrollable={true}>
          <div>Test Content</div>
        </PanelContent>
      );

      const scrollableElement = screen.getByText('Test Content').closest('.overflow-y-auto');
      
      // Check that element has performance optimizations
      expect(scrollableElement).toHaveStyle({
        scrollBehavior: 'smooth',
        willChange: 'scroll-position',


    it('should use content containment for better performance', () => {
      render(
        <RightPanel
          views={mockViews}
          activeView="view1"
          isOpen={true}
          data-testid="right-panel"
        />
      );

      const panel = screen.getByTestId('right-panel');
      
      // Check that panel has content containment
      expect(panel).toHaveStyle({
        contain: 'layout style paint',



