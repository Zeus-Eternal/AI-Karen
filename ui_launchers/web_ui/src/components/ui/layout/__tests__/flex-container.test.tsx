/**
 * FlexContainer Component Tests
 * 
 * Unit tests for the FlexContainer component and its variants
 * 
 * Based on requirements: 1.4, 3.2
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { } from '../flex-container';

describe('FlexContainer', () => {
  it('renders with default props', () => {
    render(
      <FlexContainer data-testid="flex-container">
        <div>Child 1</div>
        <div>Child 2</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('flex');
    expect(container).toHaveClass('flex-row');
    expect(container).toHaveClass('items-stretch');
    expect(container).toHaveClass('justify-start');
    expect(container.children).toHaveLength(2);

  it('applies direction configuration correctly', () => {
    render(
      <FlexContainer direction="column" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('flex-col');

  it('applies alignment properties', () => {
    render(
      <FlexContainer 
        align="center" 
        justify="between"
        data-testid="flex-container"
      >
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('items-center');
    expect(container).toHaveClass('justify-between');

  it('applies wrap configuration', () => {
    render(
      <FlexContainer wrap={true} data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('flex-wrap');

  it('applies wrap reverse configuration', () => {
    render(
      <FlexContainer wrap="reverse" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('flex-wrap-reverse');

  it('applies gap configuration', () => {
    render(
      <FlexContainer gap="1rem" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.gap).toBe('1rem');

  it('applies row and column gaps separately', () => {
    render(
      <FlexContainer rowGap="1rem" columnGap="2rem" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.rowGap).toBe('1rem');
    expect(container.style.columnGap).toBe('2rem');

  it('applies flex grow and shrink', () => {
    render(
      <FlexContainer grow={true} shrink={false} data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('flex-grow');
    expect(container).toHaveClass('flex-shrink-0');

  it('applies numeric flex grow and shrink', () => {
    render(
      <FlexContainer grow={2} shrink={0} data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.flexGrow).toBe('2');
    expect(container.style.flexShrink).toBe('0');

  it('applies flex basis', () => {
    render(
      <FlexContainer basis="200px" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.flexBasis).toBe('200px');

  it('applies numeric flex basis', () => {
    render(
      <FlexContainer basis={300} data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.flexBasis).toBe('300px');

  it('applies container queries configuration', () => {
    render(
      <FlexContainer containerQueries={true} containerName="flex-test" data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('container-flex');
    expect(container.style.containerType).toBe('inline-size');
    expect(container.style.containerName).toBe('flex-test');

  it('applies dimensions', () => {
    render(
      <FlexContainer 
        minHeight="200px" 
        maxHeight="800px"
        minWidth="300px"
        maxWidth="1200px"
        data-testid="flex-container"
      >
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container.style.minHeight).toBe('200px');
    expect(container.style.maxHeight).toBe('800px');
    expect(container.style.minWidth).toBe('300px');
    expect(container.style.maxWidth).toBe('1200px');

  it('applies responsive configuration', () => {
    render(
      <FlexContainer responsive={true} data-testid="flex-container">
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('responsive-flex');

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>();
    render(
      <FlexContainer ref={ref}>
        <div>Child</div>
      </FlexContainer>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement);

  it('applies custom className and styles', () => {
    render(
      <FlexContainer 
        className="custom-class" 
        style={{ backgroundColor: 'blue' }}
        data-testid="flex-container"
      >
        <div>Child</div>
      </FlexContainer>
    );
    
    const container = screen.getByTestId('flex-container');
    expect(container).toHaveClass('custom-class');
    expect(container).toHaveClass('flex'); // Should still have base class
    expect(container.style.backgroundColor).toBe('blue');


describe('HStack', () => {
  it('renders as horizontal stack with gap', () => {
    render(
      <HStack data-testid="hstack">
        <div>Child 1</div>
        <div>Child 2</div>
      </HStack>
    );
    
    const container = screen.getByTestId('hstack');
    expect(container).toHaveClass('flex-row');
    expect(container.style.gap).toBe('var(--space-md)');

  it('accepts custom gap', () => {
    render(
      <HStack gap="2rem" data-testid="hstack">
        <div>Child 1</div>
        <div>Child 2</div>
      </HStack>
    );
    
    const container = screen.getByTestId('hstack');
    expect(container.style.gap).toBe('2rem');


describe('VStack', () => {
  it('renders as vertical stack with gap', () => {
    render(
      <VStack data-testid="vstack">
        <div>Child 1</div>
        <div>Child 2</div>
      </VStack>
    );
    
    const container = screen.getByTestId('vstack');
    expect(container).toHaveClass('flex-col');
    expect(container.style.gap).toBe('var(--space-md)');


describe('Center', () => {
  it('renders with center alignment', () => {
    render(
      <Center data-testid="center">
        <div>Centered content</div>
      </Center>
    );
    
    const container = screen.getByTestId('center');
    expect(container).toHaveClass('items-center');
    expect(container).toHaveClass('justify-center');


describe('SpaceBetween', () => {
  it('renders with space-between justification', () => {
    render(
      <SpaceBetween data-testid="space-between">
        <div>Left</div>
        <div>Right</div>
      </SpaceBetween>
    );
    
    const container = screen.getByTestId('space-between');
    expect(container).toHaveClass('justify-between');
    expect(container).toHaveClass('items-center');


describe('ResponsiveFlex', () => {
  it('renders with responsive configuration', () => {
    render(
      <ResponsiveFlex data-testid="responsive-flex">
        <div>Item 1</div>
        <div>Item 2</div>
      </ResponsiveFlex>
    );
    
    const container = screen.getByTestId('responsive-flex');
    expect(container).toHaveClass('responsive-flex');
    expect(container.style.gap).toBe('var(--space-lg)');


describe('FlexItem', () => {
  it('renders with default props', () => {
    render(
      <FlexItem data-testid="flex-item">
        <div>Content</div>
      </FlexItem>
    );
    
    const item = screen.getByTestId('flex-item');
    expect(item).toBeInTheDocument();
    expect(item).toHaveClass('flex-shrink');
    expect(item).toHaveClass('flex-grow-0');

  it('applies flex grow and shrink', () => {
    render(
      <FlexItem grow={true} shrink={false} data-testid="flex-item">
        <div>Content</div>
      </FlexItem>
    );
    
    const item = screen.getByTestId('flex-item');
    expect(item).toHaveClass('flex-grow');
    expect(item).toHaveClass('flex-shrink-0');

  it('applies numeric flex values', () => {
    render(
      <FlexItem grow={2} shrink={0} basis="200px" data-testid="flex-item">
        <div>Content</div>
      </FlexItem>
    );
    
    const item = screen.getByTestId('flex-item');
    expect(item.style.flexGrow).toBe('2');
    expect(item.style.flexShrink).toBe('0');
    expect(item.style.flexBasis).toBe('200px');

  it('applies align self', () => {
    render(
      <FlexItem alignSelf="center" data-testid="flex-item">
        <div>Content</div>
      </FlexItem>
    );
    
    const item = screen.getByTestId('flex-item');
    expect(item).toHaveClass('self-center');

  it('applies order', () => {
    render(
      <FlexItem order={2} data-testid="flex-item">
        <div>Content</div>
      </FlexItem>
    );
    
    const item = screen.getByTestId('flex-item');
    expect(item.style.order).toBe('2');

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>();
    render(
      <FlexItem ref={ref}>
        <div>Content</div>
      </FlexItem>
    );
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement);

