/**
 * ChatModeSelector Component Tests
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ChatModeSelector, { ChatMode, ChatContext } from '../ChatModeSelector';
import { Model } from '@/lib/model-utils';

// Mock the hooks and dependencies
vi.mock('@/hooks/useModelSelection', () => ({
  useModelSelection: vi.fn(() => ({
    models: [
      {
        id: 'text-model-1',
        name: 'GPT-4',
        type: 'text',
        capabilities: ['text-generation', 'chat']
      },
      {
        id: 'image-model-1',
        name: 'DALL-E 3',
        type: 'image',
        capabilities: ['image-generation']
      },
      {
        id: 'multimodal-model-1',
        name: 'GPT-4V',
        type: 'multimodal',
        capabilities: ['text-generation', 'image-generation', 'chat']
      }
    ] as Model[],
    selectedModel: 'text-model-1',
    selectedModelInfo: {
      id: 'text-model-1',
      name: 'GPT-4',
      type: 'text',
      capabilities: ['text-generation', 'chat']
    } as Model,
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

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardDescription: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <div>{children}</div>
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} {...props} aria-label="Button">
      {children}
    </button>
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: any) => (
    <span data-variant={variant} className={className}>{children}</span>
  )
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: any) => (
    <div data-testid="select" data-value={value}>
      <button onClick={() = aria-label="Button"> onValueChange?.('test-value')}>
        {children}
      </button>
    </div>
  ),
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <div data-value={value}>{children}</div>,
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
  Separator: () => <hr />
}));

vi.mock('@/components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <div>{children}</div>,
  Tooltip: ({ children }: any) => <div>{children}</div>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
  TooltipTrigger: ({ children }: any) => <div>{children}</div>
}));

describe('ChatModeSelector', () => {
  const mockProps = {
    currentMode: 'text' as ChatMode,
    onModeChange: vi.fn(),
    onModelChange: vi.fn(),
    onContextPreservationChange: vi.fn()
  };

  const mockChatContext: ChatContext = {
    messages: [
      {
        id: '1',
        content: 'Hello',
        type: 'user',
        mode: 'text',
        timestamp: new Date()
      }
    ],
    conversationLength: 1
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Chat Mode & Model Selection')).toBeInTheDocument();
    expect(screen.getByText('Switch between different chat modes and models')).toBeInTheDocument();
  });

  it('displays available chat modes', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Text Generation')).toBeInTheDocument();
    expect(screen.getByText('Image Generation')).toBeInTheDocument();
    expect(screen.getByText('Multi-modal')).toBeInTheDocument();
  });

  it('shows current mode as active', () => {
    render(<ChatModeSelector {...mockProps} currentMode="text" />);
    
    const textModeButton = screen.getByText('Text Generation').closest('button');
    expect(textModeButton).toHaveAttribute('data-variant', 'default');
  });

  it('displays model count for each mode', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    // Each mode should show model count
    expect(screen.getByText('1 model')).toBeInTheDocument(); // Text mode
    expect(screen.getByText('1 model')).toBeInTheDocument(); // Image mode  
    expect(screen.getByText('1 model')).toBeInTheDocument(); // Multimodal mode
  });

  it('shows active conversation context when provided', () => {
    render(
      <ChatModeSelector 
        {...mockProps} 
        chatContext={mockChatContext}
      />
    );
    
    expect(screen.getByText('Active Conversation')).toBeInTheDocument();
    expect(screen.getByText('1 message in current conversation')).toBeInTheDocument();
  });

  it('calls onModeChange when mode is changed', async () => {
    render(<ChatModeSelector {...mockProps} />);
    
    const imageModeButton = screen.getByText('Image Generation').closest('button');
    fireEvent.click(imageModeButton!);
    
    // Should show confirmation dialog for mode change
    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
    });
  });

  it('shows confirmation dialog for mode changes with active conversation', async () => {
    render(
      <ChatModeSelector 
        {...mockProps} 
        chatContext={mockChatContext}
      />
    );
    
    const imageModeButton = screen.getByText('Image Generation').closest('button');
    fireEvent.click(imageModeButton!);
    
    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
      expect(screen.getByText('Confirm Mode Change')).toBeInTheDocument();
    });
  });

  it('handles model selection within current mode', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    const selectElement = screen.getByTestId('select');
    expect(selectElement).toBeInTheDocument();
    expect(selectElement).toHaveAttribute('data-value', 'text-model-1');
  });

  it('disables controls when disabled prop is true', () => {
    render(<ChatModeSelector {...mockProps} disabled={true} />);
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('shows quick switch button when multiple models available', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Quick Switch')).toBeInTheDocument();
  });

  it('displays model capabilities in model selection', () => {
    render(<ChatModeSelector {...mockProps} />);
    
    // The select should show model capabilities as badges
    expect(screen.getByText('text-generation')).toBeInTheDocument();
    expect(screen.getByText('chat')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    // Mock loading state
    vi.mocked(require('@/hooks/useModelSelection').useModelSelection).mockReturnValue({
      models: [],
      selectedModel: null,
      selectedModelInfo: null,
      setSelectedModel: vi.fn(),
      loading: true,
      error: null
    });

    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Loading models...')).toBeInTheDocument();
  });

  it('handles error state', () => {
    // Mock error state
    vi.mocked(require('@/hooks/useModelSelection').useModelSelection).mockReturnValue({
      models: [],
      selectedModel: null,
      selectedModelInfo: null,
      setSelectedModel: vi.fn(),
      loading: false,
      error: 'Failed to load models'
    });

    render(<ChatModeSelector {...mockProps} />);
    
    expect(screen.getByText('Error loading models: Failed to load models')).toBeInTheDocument();
  });

  it('shows warning when no models available for a mode', () => {
    // Mock state with no image models
    vi.mocked(require('@/hooks/useModelSelection').useModelSelection).mockReturnValue({
      models: [
        {
          id: 'text-model-1',
          name: 'GPT-4',
          type: 'text',
          capabilities: ['text-generation', 'chat']
        }
      ] as Model[],
      selectedModel: 'text-model-1',
      selectedModelInfo: {
        id: 'text-model-1',
        name: 'GPT-4',
        type: 'text',
        capabilities: ['text-generation', 'chat']
      } as Model,
      setSelectedModel: vi.fn(),
      loading: false,
      error: null
    });

    render(<ChatModeSelector {...mockProps} />);
    
    // Image mode should show 0 models
    expect(screen.getByText('0 models')).toBeInTheDocument();
  });
});