/**
 * Layout Demo Component Tests
 * 
 * Tests to verify the layout demo component renders correctly
 * and showcases responsive behavior across devices.
 * 
 * Based on requirements: 1.4, 8.3
 */


import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LayoutDemo from './layout-demo';

describe('LayoutDemo', () => {
  it('renders without crashing', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('Modern Layout System Demo')).toBeInTheDocument();
  });
  
  it('renders all section headers', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('Grid Container Examples')).toBeInTheDocument();
    expect(screen.getByText('Flex Container Examples')).toBeInTheDocument();
    expect(screen.getByText('Container Queries Example')).toBeInTheDocument();
    expect(screen.getByText('Mixed Layout Example')).toBeInTheDocument();
  });
  
  it('renders grid container items', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('Grid Item 1')).toBeInTheDocument();
    expect(screen.getByText('Grid Item 2')).toBeInTheDocument();
    expect(screen.getByText('Grid Item 3')).toBeInTheDocument();
  });
  
  it('renders flex container items', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('HStack Item 1')).toBeInTheDocument();
    expect(screen.getByText('VStack Item 1')).toBeInTheDocument();
    expect(screen.getByText('Responsive Flex 1')).toBeInTheDocument();
  });
  
  it('renders container query items', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('Container Query 1')).toBeInTheDocument();
    expect(screen.getByText('Container Query 2')).toBeInTheDocument();
  });
  
  it('renders mixed layout content', () => {
    render(<LayoutDemo />);
    
    expect(screen.getByText('Main Content')).toBeInTheDocument();
    expect(screen.getByText('Sidebar')).toBeInTheDocument();
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.getByText('Sidebar Item 1')).toBeInTheDocument();
  });
});