/**
 * Enhanced Select Component Tests
 * 
 * Tests for enhanced select component with design token integration.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import { } from '../select';

describe('EnhancedSelect', () => {
  const defaultProps = {
    children: (
      <>
        <EnhancedSelectItem value="option1">Option 1</EnhancedSelectItem>
        <EnhancedSelectItem value="option2">Option 2</EnhancedSelectItem>
        <EnhancedSelectItem value="option3">Option 3</EnhancedSelectItem>
      </>
    ),
  };

  it('should render with default props', () => {
    render(<EnhancedSelect {...defaultProps} />);
    
    const trigger = screen.getByRole('combobox');
    expect(trigger).toBeInTheDocument();
    expect(trigger).toHaveClass('flex', 'h-10', 'w-full');

  it('should render with label', () => {
    render(
      <EnhancedSelect {...defaultProps} label="Select an option" />
    );
    
    expect(screen.getByText('Select an option')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toHaveAccessibleName('Select an option');

  it('should render with required indicator', () => {
    render(
      <EnhancedSelect {...defaultProps} label="Required field" required />
    );
    
    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByText('*')).toHaveAttribute('aria-label', 'required');

  it('should render with helper text', () => {
    render(
      <EnhancedSelect {...defaultProps} helperText="Choose your preferred option" />
    );
    
    expect(screen.getByText('Choose your preferred option')).toBeInTheDocument();

  it('should render with error text', () => {
    render(
      <EnhancedSelect {...defaultProps} errorText="This field is required" />
    );
    
    const errorText = screen.getByText('This field is required');
    expect(errorText).toBeInTheDocument();
    expect(errorText).toHaveAttribute('role', 'alert');
    
    const trigger = screen.getByRole('combobox');
    expect(trigger).toHaveAttribute('aria-invalid', 'true');

  it('should apply size variants correctly', () => {
    const { rerender } = render(<EnhancedSelect {...defaultProps} size="sm" />);
    
    let trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('h-8', 'px-[var(--space-xs)]');

    rerender(<EnhancedSelect {...defaultProps} size="lg" />);
    trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('h-12', 'px-[var(--space-md)]');

  it('should apply variant styles correctly', () => {
    const { rerender } = render(<EnhancedSelect {...defaultProps} variant="filled" />);
    
    let trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('bg-[var(--color-neutral-100)]', 'border-transparent');

    rerender(<EnhancedSelect {...defaultProps} variant="ghost" />);
    trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('border-transparent', 'bg-transparent');

  it('should apply state styles correctly', () => {
    const { rerender } = render(<EnhancedSelect {...defaultProps} state="error" />);
    
    let trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('border-[var(--color-error-400)]');

    rerender(<EnhancedSelect {...defaultProps} state="success" />);
    trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('border-[var(--color-success-400)]');

    rerender(<EnhancedSelect {...defaultProps} state="warning" />);
    trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('border-[var(--color-warning-400)]');

  it('should handle value changes', async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    
    render(
      <EnhancedSelect {...defaultProps} onValueChange={onValueChange} />
    );
    
    const trigger = screen.getByRole('combobox');
    await user.click(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Option 1')).toBeInTheDocument();

    await user.click(screen.getByText('Option 1'));
    
    expect(onValueChange).toHaveBeenCalledWith('option1');

  it('should render placeholder', () => {
    render(
      <EnhancedSelect {...defaultProps} placeholder="Select an option..." />
    );
    
    expect(screen.getByText('Select an option...')).toBeInTheDocument();

  it('should handle disabled state', () => {
    render(<EnhancedSelect {...defaultProps} disabled />);
    
    const trigger = screen.getByRole('combobox');
    expect(trigger).toBeDisabled();
    expect(trigger).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');

  it('should apply design token classes', () => {
    render(<EnhancedSelect {...defaultProps} />);
    
    const trigger = screen.getByRole('combobox');
    expect(trigger).toHaveClass('rounded-[var(--radius-md)]');
    expect(trigger).toHaveClass('border-[var(--color-neutral-300)]');
    expect(trigger).toHaveClass('bg-[var(--color-neutral-50)]');
    expect(trigger).toHaveClass('text-[var(--color-neutral-900)]');
    expect(trigger).toHaveClass('[transition-duration:var(--duration-fast)]');

  it('should render with groups and separators', async () => {
    const user = userEvent.setup();
    
    render(
      <EnhancedSelect>
        <EnhancedSelectLabel>Group 1</EnhancedSelectLabel>
        <EnhancedSelectItem value="option1">Option 1</EnhancedSelectItem>
        <EnhancedSelectItem value="option2">Option 2</EnhancedSelectItem>
        <EnhancedSelectSeparator />
        <EnhancedSelectLabel>Group 2</EnhancedSelectLabel>
        <EnhancedSelectItem value="option3">Option 3</EnhancedSelectItem>
      </EnhancedSelect>
    );
    
    const trigger = screen.getByRole('combobox');
    await user.click(trigger);
    
    await waitFor(() => {
      expect(screen.getByText('Group 1')).toBeInTheDocument();
      expect(screen.getByText('Group 2')).toBeInTheDocument();


  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    
    render(
      <EnhancedSelect {...defaultProps} onValueChange={onValueChange} />
    );
    
    const trigger = screen.getByRole('combobox');
    
    // Open with Enter key
    await user.click(trigger);
    await user.keyboard('{Enter}');
    
    await waitFor(() => {
      expect(screen.getByText('Option 1')).toBeInTheDocument();

    // Navigate with arrow keys and select with Enter
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{Enter}');
    
    expect(onValueChange).toHaveBeenCalledWith('option2');

  it('should have proper accessibility attributes', () => {
    render(
      <EnhancedSelect 
        {...defaultProps} 
        label="Accessible select"
        helperText="This is a helper text"
      />
    );
    
    const trigger = screen.getByRole('combobox');
    expect(trigger).toHaveAccessibleName('Accessible select');
    expect(trigger).toHaveAccessibleDescription('This is a helper text');


describe('EnhancedSelectItem', () => {
  it('should render with correct classes', () => {
    render(
      <EnhancedSelectItem value="test">Test Item</EnhancedSelectItem>
    );
    
    const item = screen.getByText('Test Item');
    expect(item).toHaveClass('relative', 'flex', 'w-full');
    expect(item).toHaveClass('rounded-[var(--radius-sm)]');
    expect(item).toHaveClass('focus:bg-[var(--color-primary-100)]');

  it('should handle disabled state', () => {
    render(
      <EnhancedSelectItem value="test" disabled>
      </EnhancedSelectItem>
    );
    
    const item = screen.getByText('Disabled Item');
    expect(item).toHaveClass('data-[disabled]:pointer-events-none', 'data-[disabled]:opacity-50');


describe('EnhancedSelectLabel', () => {
  it('should render with correct styling', () => {
    render(<EnhancedSelectLabel>Group Label</EnhancedSelectLabel>);
    
    const label = screen.getByText('Group Label');
    expect(label).toHaveClass('py-[var(--space-xs)]', 'pl-8', 'pr-2');
    expect(label).toHaveClass('text-[var(--text-sm)]', 'font-semibold');


describe('EnhancedSelectSeparator', () => {
  it('should render with correct styling', () => {
    render(<EnhancedSelectSeparator />);
    
    const separator = document.querySelector('[role="separator"]');
    expect(separator).toHaveClass('-mx-1', 'my-1', 'h-px');
    expect(separator).toHaveClass('bg-[var(--color-neutral-200)]');

