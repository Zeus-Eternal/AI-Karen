/**
 * GridContainer Component Tests
 * 
 * Unit tests for the GridContainer component and its variants
 * 
 * Based on requirements: 1.4, 3.2
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  GridContainer,
  TwoColumnGrid,
  ThreeColumnGrid,
  AutoFitGrid,
  ResponsiveCardGrid,
  DashboardGrid,
} from '../grid-container';

describe('GridContainer', () => {
  it('renders with default props', () => {
    render(
      <GridContainer data-testid="grid-container">
        <div>Child 1</div>
        <div>Child 2</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('grid');
    expect(container.children).toHaveLength(2);
  });
  
  it('applies column configuration correctly', () => {
    render(
      <GridContainer columns={3} data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateColumns).toBe('repeat(3, 1fr)');
  });
  
  it('applies string column configuration', () => {
    render(
      <GridContainer columns="200px 1fr 100px" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateColumns).toBe('200px 1fr 100px');
  });
  
  it('applies row configuration correctly', () => {
    render(
      <GridContainer rows={2} data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateRows).toBe('repeat(2, 1fr)');
  });
  
  it('applies gap configuration', () => {
    render(
      <GridContainer gap="1rem" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gap).toBe('1rem');
  });
  
  it('applies column and row gaps separately', () => {
    render(
      <GridContainer columnGap="1rem" rowGap="2rem" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.columnGap).toBe('1rem');
    expect(container.style.rowGap).toBe('2rem');
  });
  
  it('applies grid areas correctly', () => {
    render(
      <GridContainer areas="header main footer" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateAreas).toBe('"header main footer"');
  });
  
  it('applies grid areas array correctly', () => {
    render(
      <GridContainer areas={['header header', 'main sidebar']} data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateAreas).toBe('"header header" "main sidebar"');
  });
  
  it('applies auto-fit configuration', () => {
    render(
      <GridContainer autoFit="250px" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateColumns).toBe('repeat(auto-fit, minmax(250px, 1fr))');
  });
  
  it('applies auto-fill configuration', () => {
    render(
      <GridContainer autoFill="200px" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.gridTemplateColumns).toBe('repeat(auto-fill, minmax(200px, 1fr))');
  });
  
  it('applies alignment properties', () => {
    render(
      <GridContainer 
        justifyItems="center" 
        alignItems="start"
        justifyContent="space-between"
        alignContent="end"
        data-testid="grid-container"
      >
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toHaveClass('justify-items-center');
    expect(container).toHaveClass('items-start');
    expect(container).toHaveClass('justify-between');
    expect(container).toHaveClass('content-end');
  });
  
  it('applies auto-flow configuration', () => {
    render(
      <GridContainer autoFlow="column" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toHaveClass('grid-flow-col');
  });
  
  it('applies container queries configuration', () => {
    render(
      <GridContainer containerQueries={true} containerName="grid-test" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toHaveClass('container-grid');
    expect(container.style.containerType).toBe('inline-size');
    expect(container.style.containerName).toBe('grid-test');
  });
  
  it('applies min and max height', () => {
    render(
      <GridContainer minHeight="200px" maxHeight="800px" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.minHeight).toBe('200px');
    expect(container.style.maxHeight).toBe('800px');
  });
  
  it('applies responsive configuration', () => {
    render(
      <GridContainer responsive={true} data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toHaveClass('responsive-grid');
  });
  
  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>();
    render(
      <GridContainer ref={ref}>
        <div>Child</div>
      </GridContainer>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });
  
  it('applies custom className', () => {
    render(
      <GridContainer className="custom-class" data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container).toHaveClass('custom-class');
    expect(container).toHaveClass('grid'); // Should still have base class
  });
  
  it('applies custom styles', () => {
    render(
      <GridContainer style={{ backgroundColor: 'red' }} data-testid="grid-container">
        <div>Child</div>
      </GridContainer>
    );
    
    const container = screen.getByTestId('grid-container');
    expect(container.style.backgroundColor).toBe('red');
  });
});

describe('TwoColumnGrid', () => {
  it('renders with two columns', () => {
    render(
      <TwoColumnGrid data-testid="two-column-grid">
        <div>Child 1</div>
        <div>Child 2</div>
      </TwoColumnGrid>
    );
    
    const container = screen.getByTestId('two-column-grid');
    expect(container.style.gridTemplateColumns).toBe('repeat(2, 1fr)');
    expect(container.style.gap).toBe('var(--space-lg)');
  });
});

describe('ThreeColumnGrid', () => {
  it('renders with three columns', () => {
    render(
      <ThreeColumnGrid data-testid="three-column-grid">
        <div>Child 1</div>
        <div>Child 2</div>
        <div>Child 3</div>
      </ThreeColumnGrid>
    );
    
    const container = screen.getByTestId('three-column-grid');
    expect(container.style.gridTemplateColumns).toBe('repeat(3, 1fr)');
    expect(container.style.gap).toBe('var(--space-lg)');
  });
});

describe('AutoFitGrid', () => {
  it('renders with auto-fit configuration', () => {
    render(
      <AutoFitGrid minColumnWidth="250px" data-testid="auto-fit-grid">
        <div>Child 1</div>
        <div>Child 2</div>
      </AutoFitGrid>
    );
    
    const container = screen.getByTestId('auto-fit-grid');
    expect(container.style.gridTemplateColumns).toBe('repeat(auto-fit, minmax(250px, 1fr))');
    expect(container.style.gap).toBe('var(--space-lg)');
  });
});

describe('ResponsiveCardGrid', () => {
  it('renders with responsive configuration', () => {
    render(
      <ResponsiveCardGrid data-testid="responsive-card-grid">
        <div>Card 1</div>
        <div>Card 2</div>
      </ResponsiveCardGrid>
    );
    
    const container = screen.getByTestId('responsive-card-grid');
    expect(container).toHaveClass('responsive-grid');
    expect(container.style.gap).toBe('var(--space-lg)');
  });
});

describe('DashboardGrid', () => {
  it('renders with dashboard layout', () => {
    render(
      <DashboardGrid data-testid="dashboard-grid">
        <div>Header</div>
        <div>Main</div>
        <div>Sidebar</div>
        <div>Footer</div>
      </DashboardGrid>
    );
    
    const container = screen.getByTestId('dashboard-grid');
    expect(container.style.gridTemplateColumns).toBe('1fr 300px');
    expect(container.style.gridTemplateRows).toBe('auto 1fr auto');
    expect(container.style.gridTemplateAreas).toBe('"header header" "main sidebar" "footer footer"');
    expect(container.style.minHeight).toBe('100vh');
  });
});