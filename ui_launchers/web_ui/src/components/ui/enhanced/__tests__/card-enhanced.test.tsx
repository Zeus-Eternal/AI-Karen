/**
 * Enhanced Card Component Tests
 * 
 * Tests for enhanced card component with design token integration,
 * multiple variants, and accessibility features.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';

import { } from '../card-enhanced';

describe('CardEnhanced', () => {
  describe('Basic Rendering', () => {
    it('should render with default props', () => {
      render(
        <CardEnhanced data-testid="card">
          <div>Card content</div>
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('rounded-lg', 'border', 'bg-card', 'text-card-foreground');

    it('should render with custom className', () => {
      render(
        <CardEnhanced className="custom-class" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('custom-class');

    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <CardEnhanced ref={ref}>
        </CardEnhanced>
      );
      
      expect(ref.current).toBeInstanceOf(HTMLDivElement);


  describe('Variants', () => {
    it('should apply default variant styles', () => {
      render(
        <CardEnhanced variant="default" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('shadow-sm', 'hover:shadow-md', 'border-border');

    it('should apply elevated variant styles', () => {
      render(
        <CardEnhanced variant="elevated" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('shadow-md', 'hover:shadow-lg', 'border-border/50');

    it('should apply outlined variant styles', () => {
      render(
        <CardEnhanced variant="outlined" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('border-2', 'border-dashed', 'border-border');

    it('should apply glass variant styles', () => {
      render(
        <CardEnhanced variant="glass" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('bg-card/80', 'backdrop-blur-sm');

    it('should apply gradient variant styles', () => {
      render(
        <CardEnhanced variant="gradient" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('bg-gradient-to-br', 'from-card', 'to-card/80');


  describe('Interactive State', () => {
    it('should apply interactive styles when interactive is true', () => {
      render(
        <CardEnhanced interactive data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('cursor-pointer');
      expect(card).toHaveClass('hover:scale-[1.01]', 'active:scale-[0.99]');
      expect(card).toHaveAttribute('role', 'button');
      expect(card).toHaveAttribute('tabIndex', '0');

    it('should not apply interactive styles when interactive is false', () => {
      render(
        <CardEnhanced interactive={false} data-testid="card">
          Non-interactive Card
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).not.toHaveClass('cursor-pointer');
      expect(card).not.toHaveAttribute('role', 'button');
      expect(card).not.toHaveAttribute('tabIndex');

    it('should handle click events when interactive', () => {
      const handleClick = vi.fn();
      render(
        <CardEnhanced interactive onClick={handleClick} data-testid="card">
        </CardEnhanced>
      );
      
      fireEvent.click(screen.getByTestId('card'));
      expect(handleClick).toHaveBeenCalledTimes(1);

    it('should handle keyboard events when interactive', () => {
      const handleKeyDown = vi.fn();
      render(
        <CardEnhanced interactive onKeyDown={handleKeyDown} data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      fireEvent.keyDown(card, { key: 'Enter' });
      expect(handleKeyDown).toHaveBeenCalledTimes(1);


  describe('Padding Variants', () => {
    it('should apply no padding', () => {
      render(
        <CardEnhanced padding="none" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-0');

    it('should apply small padding', () => {
      render(
        <CardEnhanced padding="sm" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-4');

    it('should apply default padding', () => {
      render(
        <CardEnhanced padding="default" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-6');

    it('should apply large padding', () => {
      render(
        <CardEnhanced padding="lg" data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-8');


  describe('Accessibility', () => {
    it('should have proper focus styles when interactive', () => {
      render(
        <CardEnhanced interactive data-testid="card">
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveClass(
        'focus-visible:outline-none',
        'focus-visible:ring-2',
        'focus-visible:ring-ring'
      );

    it('should support custom aria attributes', () => {
      render(
        <CardEnhanced 
          interactive
          aria-label="Custom card"
          aria-describedby="description"
          data-testid="card"
        >
        </CardEnhanced>
      );
      
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('aria-label', 'Custom card');
      expect(card).toHaveAttribute('aria-describedby', 'description');



describe('CardHeaderEnhanced', () => {
  it('should render with default styles', () => {
    render(
      <CardHeaderEnhanced data-testid="header">
      </CardHeaderEnhanced>
    );
    
    const header = screen.getByTestId('header');
    expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6', 'pb-4');

  it('should apply padding variants', () => {
    render(
      <CardHeaderEnhanced padding="sm" data-testid="header">
      </CardHeaderEnhanced>
    );
    
    const header = screen.getByTestId('header');
    expect(header).toHaveClass('p-4', 'pb-2');


describe('CardTitleEnhanced', () => {
  it('should render as h3 with proper styles', () => {
    render(<CardTitleEnhanced>Card Title</CardTitleEnhanced>);
    
    const title = screen.getByRole('heading', { level: 3 });
    expect(title).toBeInTheDocument();
    expect(title).toHaveClass(
      'text-2xl',
      'font-semibold',
      'leading-none',
      'tracking-tight',
      'text-card-foreground'
    );

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLHeadingElement>();
    render(<CardTitleEnhanced ref={ref}>Title</CardTitleEnhanced>);
    
    expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
    expect(ref.current?.tagName).toBe('H3');


describe('CardDescriptionEnhanced', () => {
  it('should render with proper styles', () => {
    render(<CardDescriptionEnhanced>Card description</CardDescriptionEnhanced>);
    
    const description = screen.getByText('Card description');
    expect(description).toHaveClass(
      'text-sm',
      'text-muted-foreground',
      'leading-relaxed'
    );

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLParagraphElement>();
    render(<CardDescriptionEnhanced ref={ref}>Description</CardDescriptionEnhanced>);
    
    expect(ref.current).toBeInstanceOf(HTMLParagraphElement);


describe('CardContentEnhanced', () => {
  it('should render with default styles', () => {
    render(
      <CardContentEnhanced data-testid="content">
      </CardContentEnhanced>
    );
    
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('p-6', 'pt-0');

  it('should apply padding variants', () => {
    render(
      <CardContentEnhanced padding="lg" data-testid="content">
      </CardContentEnhanced>
    );
    
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('p-8', 'pt-0');


describe('CardFooterEnhanced', () => {
  it('should render with default styles', () => {
    render(
      <CardFooterEnhanced data-testid="footer">
      </CardFooterEnhanced>
    );
    
    const footer = screen.getByTestId('footer');
    expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-4');

  it('should apply padding variants', () => {
    render(
      <CardFooterEnhanced padding="none" data-testid="footer">
      </CardFooterEnhanced>
    );
    
    const footer = screen.getByTestId('footer');
    expect(footer).toHaveClass('p-0');


describe('Complete Card Example', () => {
  it('should render a complete card with all components', () => {
    render(
      <CardEnhanced interactive data-testid="complete-card">
        <CardHeaderEnhanced>
          <CardTitleEnhanced>Test Card</CardTitleEnhanced>
          <CardDescriptionEnhanced>
          </CardDescriptionEnhanced>
        </CardHeaderEnhanced>
        <CardContentEnhanced>
          <p>This is the card content</p>
        </CardContentEnhanced>
        <CardFooterEnhanced>
          <button aria-label="Button">Action</button>
        </CardFooterEnhanced>
      </CardEnhanced>
    );
    
    expect(screen.getByTestId('complete-card')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Test Card' })).toBeInTheDocument();
    expect(screen.getByText('This is a test card description')).toBeInTheDocument();
    expect(screen.getByText('This is the card content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();

