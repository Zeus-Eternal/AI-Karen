/**
 * Theme Toggle Component Tests
 * 
 * Tests for the enhanced theme toggle component
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeToggle } from '../theme-toggle';
import { useTheme } from '../../../providers/theme-provider';

// Mock the theme provider hook
jest.mock('../../../providers/theme-provider', () => ({
  useTheme: jest.fn(),
}));

// Mock Lucide icons
jest.mock('lucide-react', () => ({
  Moon: ({ className }: { className?: string }) => <div data-testid="moon-icon" className={className} />,
  Sun: ({ className }: { className?: string }) => <div data-testid="sun-icon" className={className} />,
  Monitor: ({ className }: { className?: string }) => <div data-testid="monitor-icon" className={className} />,
  Palette: ({ className }: { className?: string }) => <div data-testid="palette-icon" className={className} />,
}));

// Mock dropdown menu components
jest.mock('../dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuTrigger: ({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) => 
    <div data-testid="dropdown-trigger">{children}</div>,
  DropdownMenuContent: ({ children, align, className }: { children: React.ReactNode; align?: string; className?: string }) => 
    <div data-testid="dropdown-content" data-align={align} className={className}>{children}</div>,
  DropdownMenuItem: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => 
    <div data-testid="dropdown-item" onClick={onClick} className={className}>{children}</div>,
  DropdownMenuSeparator: () => <div data-testid="dropdown-separator" />,
  DropdownMenuLabel: ({ children, className }: { children: React.ReactNode; className?: string }) => 
    <div data-testid="dropdown-label" className={className}>{children}</div>,
}));

describe('ThemeToggle', () => {
  const mockSetTheme = jest.fn();
  const mockSetDensity = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'system',
      setTheme: mockSetTheme,
      density: 'comfortable',
      setDensity: mockSetDensity,
      resolvedTheme: 'light',
      isSystemTheme: true,


  it('should render theme toggle button', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByTestId('dropdown-trigger')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();

  it('should show monitor icon for system theme', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByTestId('monitor-icon')).toBeInTheDocument();

  it('should show sun icon for light theme', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
      density: 'comfortable',
      setDensity: mockSetDensity,
      resolvedTheme: 'light',
      isSystemTheme: false,

    render(<ThemeToggle />);
    
    expect(screen.getByTestId('sun-icon')).toBeInTheDocument();

  it('should show moon icon for dark theme', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
      density: 'comfortable',
      setDensity: mockSetDensity,
      resolvedTheme: 'dark',
      isSystemTheme: false,

    render(<ThemeToggle />);
    
    expect(screen.getByTestId('moon-icon')).toBeInTheDocument();

  it('should have proper aria-label', () => {
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Current theme: System (light)');

  it('should render dropdown menu content', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByTestId('dropdown-content')).toBeInTheDocument();
    expect(screen.getByTestId('dropdown-content')).toHaveAttribute('data-align', 'end');
    expect(screen.getByTestId('dropdown-content')).toHaveClass('w-48');

  it('should render appearance label with palette icon', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByTestId('dropdown-label')).toBeInTheDocument();
    expect(screen.getByTestId('palette-icon')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();

  it('should render all theme options', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Dark')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();

  it('should render all density options', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByText('Compact')).toBeInTheDocument();
    expect(screen.getByText('Comfortable')).toBeInTheDocument();
    expect(screen.getByText('Spacious')).toBeInTheDocument();

  it('should highlight current theme option', () => {
    render(<ThemeToggle />);
    
    const systemItem = screen.getByText('System').closest('[data-testid="dropdown-item"]');
    expect(systemItem).toHaveClass('bg-[var(--color-primary-100)] text-[var(--color-primary-900)]');
    
    const lightItem = screen.getByText('Light').closest('[data-testid="dropdown-item"]');
    expect(lightItem).not.toHaveClass('bg-[var(--color-primary-100)] text-[var(--color-primary-900)]');

  it('should highlight current density option', () => {
    render(<ThemeToggle />);
    
    const comfortableItem = screen.getByText('Comfortable').closest('[data-testid="dropdown-item"]');
    expect(comfortableItem).toHaveClass('bg-[var(--color-primary-100)] text-[var(--color-primary-900)]');
    
    const compactItem = screen.getByText('Compact').closest('[data-testid="dropdown-item"]');
    expect(compactItem).not.toHaveClass('bg-[var(--color-primary-100)] text-[var(--color-primary-900)]');

  it('should show checkmarks for current selections', () => {
    render(<ThemeToggle />);
    
    // System theme should have checkmark
    const systemItem = screen.getByText('System').closest('[data-testid="dropdown-item"]');
    expect(systemItem).toHaveTextContent('✓');
    
    // Comfortable density should have checkmark
    const comfortableItem = screen.getByText('Comfortable').closest('[data-testid="dropdown-item"]');
    expect(comfortableItem).toHaveTextContent('✓');

  it('should call setTheme when theme option is clicked', async () => {
    render(<ThemeToggle />);
    
    const lightItem = screen.getByText('Light').closest('[data-testid="dropdown-item"]');
    fireEvent.click(lightItem!);
    
    await waitFor(() => {
      expect(mockSetTheme).toHaveBeenCalledWith('light');


  it('should call setDensity when density option is clicked', async () => {
    render(<ThemeToggle />);
    
    const compactItem = screen.getByText('Compact').closest('[data-testid="dropdown-item"]');
    fireEvent.click(compactItem!);
    
    await waitFor(() => {
      expect(mockSetDensity).toHaveBeenCalledWith('compact');


  it('should render separators', () => {
    render(<ThemeToggle />);
    
    const separators = screen.getAllByTestId('dropdown-separator');
    expect(separators).toHaveLength(2); // One after theme options, one before density options

  it('should render density label', () => {
    render(<ThemeToggle />);
    
    expect(screen.getByText('Density')).toBeInTheDocument();

  it('should render density icons', () => {
    render(<ThemeToggle />);
    
    // Check for density visual indicators (using text content as they're text-based icons)
    expect(screen.getByText('◾')).toBeInTheDocument(); // Compact
    expect(screen.getByText('◼')).toBeInTheDocument(); // Comfortable
    expect(screen.getByText('⬛')).toBeInTheDocument(); // Spacious

  it('should update aria-label based on theme state', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
      density: 'compact',
      setDensity: mockSetDensity,
      resolvedTheme: 'dark',
      isSystemTheme: false,

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Current theme: Dark');

  it('should handle system theme with dark preference', () => {
    (useTheme as jest.Mock).mockReturnValue({
      theme: 'system',
      setTheme: mockSetTheme,
      density: 'comfortable',
      setDensity: mockSetDensity,
      resolvedTheme: 'dark',
      isSystemTheme: true,

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Current theme: System (dark)');

