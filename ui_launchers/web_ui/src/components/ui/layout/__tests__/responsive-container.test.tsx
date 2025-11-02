/**
 * ResponsiveContainer Component Tests
 * 
 * Unit tests for the ResponsiveContainer component and its variants
 * 
 * Based on requirements: 1.4, 8.3
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { } from '../responsive-container';

describe('ResponsiveContainer', () => {
  it('renders with default props', () => {
    render(
      <ResponsiveContainer data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('w-full');
    expect(container).toHaveClass('max-w-full');
    expect(container.children).toHaveLength(1);

  it('applies size configuration correctly', () => {
    render(
      <ResponsiveContainer size="lg" data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('max-w-lg');

  it('applies center configuration', () => {
    render(
      <ResponsiveContainer center={true} data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('mx-auto');

  it('applies fluid configuration', () => {
    render(
      <ResponsiveContainer fluid={true} data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('max-w-none');

  it('applies padding configuration', () => {
    render(
      <ResponsiveContainer padding="2rem" data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container.style.padding).toBe('2rem');

  it('applies margin configuration', () => {
    render(
      <ResponsiveContainer margin="1rem" data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container.style.margin).toBe('1rem');

  it('applies container queries configuration', () => {
    render(
      <ResponsiveContainer 
        containerQueries={true} 
        containerName="test-container" 
        data-testid="responsive-container"
      >
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('container-responsive');
    expect(container.style.containerType).toBe('inline-size');
    expect(container.style.containerName).toBe('test-container');

  it('applies dimensions', () => {
    render(
      <ResponsiveContainer 
        minHeight="200px" 
        maxHeight="800px"
        data-testid="responsive-container"
      >
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container.style.minHeight).toBe('200px');
    expect(container.style.maxHeight).toBe('800px');

  it('applies visual properties', () => {
    render(
      <ResponsiveContainer 
        background="blue" 
        borderRadius="8px"
        shadow="0 2px 4px rgba(0,0,0,0.1)"
        data-testid="responsive-container"
      >
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container.style.backgroundColor).toBe('blue');
    expect(container.style.borderRadius).toBe('8px');
    expect(container.style.boxShadow).toBe('0 2px 4px rgba(0,0,0,0.1)');

  it('applies responsive configuration', () => {
    render(
      <ResponsiveContainer responsive={true} data-testid="responsive-container">
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('responsive-container');

  it('applies custom breakpoints', () => {
    const customBreakpoints = {
      sm: '500px',
      md: '900px',
      lg: '1200px',
    };
    
    render(
      <ResponsiveContainer 
        breakpoints={customBreakpoints} 
        data-testid="responsive-container"
      >
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container.style.getPropertyValue('--breakpoint-sm')).toBe('500px');
    expect(container.style.getPropertyValue('--breakpoint-md')).toBe('900px');
    expect(container.style.getPropertyValue('--breakpoint-lg')).toBe('1200px');

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>();
    render(
      <ResponsiveContainer ref={ref}>
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement);

  it('applies custom className and styles', () => {
    render(
      <ResponsiveContainer 
        className="custom-class" 
        style={{ backgroundColor: 'red' }}
        data-testid="responsive-container"
      >
        <div>Content</div>
      </ResponsiveContainer>
    );
    
    const container = screen.getByTestId('responsive-container');
    expect(container).toHaveClass('custom-class');
    expect(container).toHaveClass('w-full'); // Should still have base class
    expect(container.style.backgroundColor).toBe('red');


describe('PageContainer', () => {
  it('renders with page container configuration', () => {
    render(
      <PageContainer data-testid="page-container">
        <div>Page content</div>
      </PageContainer>
    );
    
    const container = screen.getByTestId('page-container');
    expect(container).toHaveClass('mx-auto');
    expect(container).toHaveClass('responsive-container');


describe('SectionContainer', () => {
  it('renders with section container configuration', () => {
    render(
      <SectionContainer data-testid="section-container">
        <div>Section content</div>
      </SectionContainer>
    );
    
    const container = screen.getByTestId('section-container');
    expect(container).toHaveClass('mx-auto');
    expect(container).toHaveClass('responsive-container');


describe('CardContainer', () => {
  it('renders with card container configuration', () => {
    render(
      <CardContainer data-testid="card-container">
        <div>Card content</div>
      </CardContainer>
    );
    
    const container = screen.getByTestId('card-container');
    expect(container).toHaveClass('container-responsive');
    expect(container.style.containerType).toBe('inline-size');
    expect(container.style.borderRadius).toBe('var(--radius-lg)');
    expect(container.style.boxShadow).toBe('var(--shadow-md)');
    expect(container.style.padding).toBe('var(--space-lg)');
    expect(container.style.backgroundColor).toBe('var(--color-neutral-50)');


describe('SidebarContainer', () => {
  it('renders with sidebar container configuration', () => {
    render(
      <SidebarContainer data-testid="sidebar-container">
        <div>Sidebar content</div>
      </SidebarContainer>
    );
    
    const container = screen.getByTestId('sidebar-container');
    expect(container).toHaveClass('responsive-container');
    expect(container.style.minHeight).toBe('100vh');


describe('ContentContainer', () => {
  it('renders with content container configuration', () => {
    render(
      <ContentContainer data-testid="content-container">
        <div>Content</div>
      </ContentContainer>
    );
    
    const container = screen.getByTestId('content-container');
    expect(container).toHaveClass('mx-auto');
    expect(container).toHaveClass('responsive-container');

