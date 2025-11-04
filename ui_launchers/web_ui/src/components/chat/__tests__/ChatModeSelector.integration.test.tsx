/**
 * ChatModeSelector Integration Test
 * Simple test to verify the component renders and basic functionality works
 */


import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import ChatModeSelector, { ChatMode } from '../ChatModeSelector';

// Mock the hooks with minimal implementation
vi.mock('@/hooks/useModelSelection', () => ({
  useModelSelection: vi.fn(() => ({
    models: [],
    selectedModel: null,
    selectedModelInfo: null,
    setSelectedModel: vi.fn(),
    loading: false,
    error: null
  }))
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock all UI components with simple implementations
vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: any) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div data-testid="card-title">{children}</div>
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled }: any) => (
    <Button onClick={onClick} disabled={disabled} data-testid="button" aria-label="Button">
      {children}
    </Button>
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: any) => <span data-testid="badge">{children}</span>
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: any) => <div data-testid="select">{children}</div>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <div>{placeholder}</div>
}));

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: any) => open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }: any) => <div>{children}</div>,
  DialogDescription: ({ children }: any) => <div>{children}</div>,
  DialogFooter: ({ children }: any) => <div>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <div>{children}</div>
}));

vi.mock('@/components/ui/separator', () => ({
  Separator: () => <hr data-testid="separator" />
}));

vi.mock('@/components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <div>{children}</div>,
  Tooltip: ({ children }: any) => <div>{children}</div>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
  TooltipTrigger: ({ children }: any) => <div>{children}</div>
}));

describe('ChatModeSelector Integration', () => {
  const mockProps = {
    currentMode: 'text' as ChatMode,
    onModeChange: vi.fn(),
    onModelChange: vi.fn()
  };

  it('renders the component without crashing', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    // Check that main elements are present
    expect(screen.getByTestId('card')).toBeInTheDocument();
    expect(screen.getByTestId('card-title')).toBeInTheDocument();
    expect(screen.getByTestId('card-description')).toBeInTheDocument();

  it('displays the component title and description', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Chat Mode & Model Selection')).toBeInTheDocument();
    expect(screen.getByText('Switch between different chat modes and models')).toBeInTheDocument();

  it('shows mode selection section', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Chat Mode')).toBeInTheDocument();

  it('displays mode buttons', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Text Generation')).toBeInTheDocument();
    expect(screen.getByText('Image Generation')).toBeInTheDocument();
    expect(screen.getByText('Multi-modal')).toBeInTheDocument();

  it('shows model selection section', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText(/Model for/)).toBeInTheDocument();
    expect(screen.getByTestId('select')).toBeInTheDocument();

  it('displays current mode badge', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    const badges = screen.getAllByTestId('badge');
    expect(badges.length).toBeGreaterThan(0);

  it('shows separator between sections', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByTestId('separator')).toBeInTheDocument();

  it('handles disabled state', () => {
    render(<ChatModeSelector {...mockProps} disabled={true} />);
    
    const buttons = screen.getAllByTestId('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();


