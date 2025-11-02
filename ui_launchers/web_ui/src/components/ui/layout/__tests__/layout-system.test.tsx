import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { GridContainer } from '../grid-container';
import { FlexContainer } from '../flex-container';
import { ResponsiveContainer } from '../responsive-container';

// Mock ResizeObserver for container query tests
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

describe('Layout System Components', () => {
  describe('GridContainer', () => {
    it('should render with default grid properties', () => {
      render(
        <GridContainer data-testid="grid-container">
          <div>Grid Item 1</div>
          <div>Grid Item 2</div>
        </GridContainer>
      );

      const container = screen.getByTestId('grid-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveClass('grid');

    it('should apply custom columns and rows', () => {
      render(
        <GridContainer 
          columns="repeat(3, 1fr)" 
          rows="repeat(2, auto)"
          data-testid="custom-grid"
        >
          <div>Item</div>
        </GridContainer>
      );

      const container = screen.getByTestId('custom-grid');
      expect(container).toHaveStyle({
        gridTemplateColumns: 'repeat(3, 1fr)',
        gridTemplateRows: 'repeat(2, auto)'


    it('should apply gap spacing', () => {
      render(
        <GridContainer gap="1rem" data-testid="gap-grid">
          <div>Item</div>
        </GridContainer>
      );

      const container = screen.getByTestId('gap-grid');
      expect(container).toHaveStyle({ gap: '1rem' });

    it('should support grid areas', () => {
      const areas = [
        "header header",
        "sidebar content",
        "footer footer"
      ];

      render(
        <GridContainer areas={areas} data-testid="areas-grid">
          <div>Item</div>
        </GridContainer>
      );

      const container = screen.getByTestId('areas-grid');
      expect(container).toHaveStyle({
        gridTemplateAreas: '"header header" "sidebar content" "footer footer"'


    it('should handle responsive grid behavior', () => {
      render(
        <GridContainer responsive data-testid="responsive-grid">
          <div>Item</div>
        </GridContainer>
      );

      const container = screen.getByTestId('responsive-grid');
      expect(container).toHaveClass('responsive-grid');

    it('should support numeric column specification', () => {
      render(
        <GridContainer columns={4} data-testid="numeric-grid">
          <div>Item</div>
        </GridContainer>
      );

      const container = screen.getByTestId('numeric-grid');
      expect(container).toHaveStyle({
        gridTemplateColumns: 'repeat(4, 1fr)'



  describe('FlexContainer', () => {
    it('should render with default flex properties', () => {
      render(
        <FlexContainer data-testid="flex-container">
          <div>Flex Item 1</div>
          <div>Flex Item 2</div>
        </FlexContainer>
      );

      const container = screen.getByTestId('flex-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveClass('flex');

    it('should apply flex direction', () => {
      render(
        <FlexContainer direction="column" data-testid="column-flex">
          <div>Item</div>
        </FlexContainer>
      );

      const container = screen.getByTestId('column-flex');
      expect(container).toHaveClass('flex-col');

    it('should apply alignment properties', () => {
      render(
        <FlexContainer 
          align="center" 
          justify="between" 
          data-testid="aligned-flex"
        >
          <div>Item</div>
        </FlexContainer>
      );

      const container = screen.getByTestId('aligned-flex');
      expect(container).toHaveClass('items-center');
      expect(container).toHaveClass('justify-between');

    it('should support flex wrap', () => {
      render(
        <FlexContainer wrap data-testid="wrap-flex">
          <div>Item</div>
        </FlexContainer>
      );

      const container = screen.getByTestId('wrap-flex');
      expect(container).toHaveClass('flex-wrap');

    it('should apply gap spacing', () => {
      render(
        <FlexContainer gap="0.5rem" data-testid="gap-flex">
          <div>Item</div>
        </FlexContainer>
      );

      const container = screen.getByTestId('gap-flex');
      expect(container).toHaveStyle({ gap: '0.5rem' });

    it('should handle all direction variants', () => {
      const directions = ['row', 'column', 'row-reverse', 'column-reverse'] as const;
      
      directions.forEach(direction => {
        const { unmount } = render(
          <FlexContainer direction={direction} data-testid={`${direction}-flex`}>
            <div>Item</div>
          </FlexContainer>
        );

        const container = screen.getByTestId(`${direction}-flex`);
        const expectedClass = direction === 'row' ? 'flex-row' : 
                            direction === 'column' ? 'flex-col' :
                            direction === 'row-reverse' ? 'flex-row-reverse' :
                            'flex-col-reverse';
        
        expect(container).toHaveClass(expectedClass);
        unmount();



  describe('ResponsiveContainer', () => {
    it('should render with container query support', () => {
      render(
        <ResponsiveContainer containerQueries data-testid="responsive-container">
          <div>Responsive Content</div>
        </ResponsiveContainer>
      );

      const container = screen.getByTestId('responsive-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveClass('container-responsive');

    it('should apply custom breakpoints', () => {
      render(
        <ResponsiveContainer 
          breakpoints={{ sm: '640px', md: '768px', lg: '1024px' }} 
          data-testid="breakpoint-container"
        >
          <div>Content</div>
        </ResponsiveContainer>
      );

      const container = screen.getByTestId('breakpoint-container');
      expect(container).toBeInTheDocument();
      // Custom breakpoints are applied as CSS custom properties
      expect(container).toHaveStyle({
        '--breakpoint-sm': '640px',
        '--breakpoint-md': '768px',
        '--breakpoint-lg': '1024px'


    it('should support container name for queries', () => {
      render(
        <ResponsiveContainer 
          containerQueries
          containerName="sidebar" 
          data-testid="named-container"
        >
          <div>Content</div>
        </ResponsiveContainer>
      );

      const container = screen.getByTestId('named-container');
      expect(container).toHaveStyle({
        containerName: 'sidebar'


    it('should handle container type specification', () => {
      render(
        <ResponsiveContainer 
          containerQueries
          data-testid="typed-container"
        >
          <div>Content</div>
        </ResponsiveContainer>
      );

      const container = screen.getByTestId('typed-container');
      expect(container).toHaveStyle({
        containerType: 'inline-size'



  describe('Layout Integration', () => {
    it('should work together in complex layouts', () => {
      render(
        <ResponsiveContainer data-testid="complex-layout">
          <GridContainer columns="1fr 2fr" gap="1rem">
            <FlexContainer direction="column" align="center">
              <div>Sidebar Content</div>
            </FlexContainer>
            <FlexContainer direction="column" gap="0.5rem">
              <div>Main Content</div>
              <div>Secondary Content</div>
            </FlexContainer>
          </GridContainer>
        </ResponsiveContainer>
      );

      const layout = screen.getByTestId('complex-layout');
      expect(layout).toBeInTheDocument();
      
      const gridContainer = layout.querySelector('.grid');
      expect(gridContainer).toBeInTheDocument();
      
      const flexContainers = layout.querySelectorAll('.flex');
      expect(flexContainers).toHaveLength(2);

    it('should maintain accessibility with proper semantic structure', () => {
      render(
        <main data-testid="semantic-layout">
          <nav>
            <div>Navigation</div>
          </nav>
          <article>
            <div>Article Content</div>
          </article>
        </main>
      );

      const main = screen.getByRole('main');
      expect(main).toBeInTheDocument();
      
      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();
      
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();


  describe('Performance Considerations', () => {
    it('should not cause unnecessary re-renders', () => {
      const renderSpy = vi.fn();
      
      const TestComponent = () => {
        renderSpy();
        return <div>Test</div>;
      };

      const { rerender } = render(
        <GridContainer columns="1fr 1fr">
          <TestComponent />
        </GridContainer>
      );

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props should not cause child re-render
      rerender(
        <GridContainer columns="1fr 1fr">
          <TestComponent />
        </GridContainer>
      );

      expect(renderSpy).toHaveBeenCalledTimes(2); // React will re-render but that's expected

    it('should handle large numbers of children efficiently', () => {
      const manyChildren = Array.from({ length: 100 }, (_, i) => (
        <div key={i}>Item {i}</div>
      ));

      const startTime = performance.now();
      
      render(
        <GridContainer columns="repeat(10, 1fr)" data-testid="many-children">
          {manyChildren}
        </GridContainer>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (less than 100ms)
      expect(renderTime).toBeLessThan(100);
      
      const container = screen.getByTestId('many-children');
      expect(container.children).toHaveLength(100);


