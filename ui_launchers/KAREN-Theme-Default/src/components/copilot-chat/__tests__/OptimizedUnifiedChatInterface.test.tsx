import { render, screen, fireEvent, act } from '@testing-library/react';
import { ChatInterface } from '../ChatInterface';
import { useCopilotEngine } from '../core/CopilotEngine';
import { usePerformance } from '../hooks/usePerformance';

// Mock the hooks
jest.mock('../core/CopilotEngine');
jest.mock('../hooks/usePerformance');
jest.mock('../hooks/usePerformance', () => ({
  usePerformance: jest.fn(),
  useVirtualScroll: jest.fn(),
  useDebounce: jest.fn(),
  useThrottle: jest.fn(),
  useLazyLoadImage: jest.fn(),
  useMemoize: jest.fn(),
  useRenderTime: jest.fn(),
  useShouldUpdate: jest.fn()
}));

// Import the types
import type { CopilotState } from '../types/copilot';

// Mock the performance utilities
jest.mock('../utils/performance', () => ({
  VirtualListUtils: {
    calculateVisibleRange: jest.fn(),
    calculateTotalHeight: jest.fn(),
    getItemOffset: jest.fn()
  },
  ImageOptimizer: {
    optimizeImage: jest.fn(),
    preloadImage: jest.fn()
  },
  CodeHighlighter: {
    highlightCode: jest.fn()
  },
  ComponentOptimizer: {
    shouldComponentUpdate: jest.fn()
  }
}));

// Mock the optimized components
jest.mock('../components/VirtualizedMessageList', () => ({
  VirtualizedMessageList: jest.fn(() => <div data-testid="virtualized-message-list">Mocked VirtualizedMessageList</div>)
}));

jest.mock('../components/OptimizedImage', () => ({
  OptimizedImage: jest.fn(({ src, alt }) => <img src={src} alt={alt} data-testid="optimized-image" />)
}));

jest.mock('../components/OptimizedCodeBlock', () => ({
  OptimizedCodeBlock: jest.fn(({ code, language }) => (
    <div data-testid="optimized-code-block" data-language={language}>
      {code}
    </div>
  ))
}));

describe('ChatInterface', () => {
  const mockUseCopilotEngine = useCopilotEngine as jest.MockedFunction<typeof useCopilotEngine>;
  const mockUsePerformance = usePerformance as jest.MockedFunction<typeof usePerformance>;
  
  const mockCopilotEngine = {
    state: {
      messages: [],
      suggestions: [],
      actions: [],
      workflows: [],
      artifacts: [],
      isLoading: false,
      error: null,
      memoryOps: null,
      activePanel: 'chat' as const,
      inputModality: 'text' as const,
      availableLNMs: [],
      activeLNM: null,
      availablePlugins: [],
      securityContext: {
        userRoles: [],
        securityMode: 'safe' as const,
        canAccessSensitive: false,
        redactionLevel: 'none' as const
      },
      uiConfig: {
        theme: 'auto' as const,
        fontSize: 'medium' as const,
        showTimestamps: true,
        showMemoryOps: false,
        showDebugInfo: false,
        maxMessageHistory: 100,
        enableAnimations: true,
        enableSoundEffects: false,
        enableKeyboardShortcuts: true,
        autoScroll: true,
        markdownSupport: true,
        codeHighlighting: true,
        imagePreview: true
      }
    } as CopilotState,
    sendMessage: jest.fn(),
    executeAction: jest.fn(),
    executeWorkflow: jest.fn(),
    generateArtifact: jest.fn(),
    openArtifact: jest.fn(),
    changePanel: jest.fn(),
    changeModality: jest.fn(),
    selectLNM: jest.fn(),
    togglePlugin: jest.fn(),
    updateUIConfig: jest.fn(),
    clearError: jest.fn(),
    retry: jest.fn(),
    dismissAction: jest.fn(),
    dismissSuggestion: jest.fn(),
    dismissWorkflow: jest.fn(),
    dismissArtifact: jest.fn(),
    refreshState: jest.fn(),
    togglePanel: jest.fn(),
    toggleModality: jest.fn(),
    retryLastAction: jest.fn(),
    isInitialized: true
  };
  
  const mockPerformance = {
    renderCount: 0,
    mountTime: Date.now(),
    lastRenderTime: 0,
    getAverageRenderTime: jest.fn(() => 0),
    getMaxRenderTime: jest.fn(() => 0)
  };
  
  beforeEach(() => {
    mockUseCopilotEngine.mockReturnValue(mockCopilotEngine);
    mockUsePerformance.mockReturnValue(mockPerformance);
    
    // Mock the performance hooks
    const { useVirtualScroll, useDebounce, useThrottle, useLazyLoadImage, useMemoize, useRenderTime, useShouldUpdate } = require('../hooks/usePerformance');
    
    useVirtualScroll.mockReturnValue({
      visibleItems: [],
      totalHeight: 0,
      getItemOffset: jest.fn(),
      handleScroll: jest.fn()
    });
    
    useDebounce.mockImplementation(<T>(value: T) => value);
    useThrottle.mockImplementation(<T extends (...args: unknown[]) => unknown>(fn: T) => fn);
    useLazyLoadImage.mockReturnValue({ loaded: true, error: null });
    useMemoize.mockImplementation(<T extends (...args: unknown[]) => unknown>(fn: T) => fn);
    useRenderTime.mockReturnValue({
      getAverageRenderTime: jest.fn(() => 0),
      getMaxRenderTime: jest.fn(() => 0),
      renderCount: 0
    });
    useShouldUpdate.mockReturnValue(false);
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  it('should render without crashing', () => {
    render(<ChatInterface />);
    expect(screen.getByTestId('optimized-unified-chat-interface')).toBeInTheDocument();
  });
  
  it('should display messages when available', () => {
    const messages = [
      { id: '1', content: 'Hello', role: 'user', timestamp: new Date() },
      { id: '2', content: 'Hi there!', role: 'assistant', timestamp: new Date() }
    ];
    
    (mockCopilotEngine.state as any).messages = messages;
    
    render(<ChatInterface />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });
  
  it('should display loading indicator when loading', () => {
    (mockCopilotEngine.state as any).isLoading = true;
    
    render(<ChatInterface />);
    
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });
  
  it('should display error when present', () => {
    (mockCopilotEngine.state as any).error = 'An error occurred';
    
    render(<ChatInterface />);
    
    expect(screen.getByText('An error occurred')).toBeInTheDocument();
  });
  
  it('should call sendMessage when sending a message', () => {
    render(<ChatInterface />);
    
    const input = screen.getByTestId('message-input');
    const sendButton = screen.getByTestId('send-button');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    expect(mockCopilotEngine.sendMessage).toHaveBeenCalledWith('Test message');
  });
  
  it('should call executeAction when an action is executed', () => {
    const actions = [
      { id: '1', title: 'Test Action', description: 'A test action', execute: jest.fn() }
    ];
    
    (mockCopilotEngine.state as any).actions = actions;
    
    render(<ChatInterface />);
    
    const actionButton = screen.getByText('Test Action');
    fireEvent.click(actionButton);
    
    expect(mockCopilotEngine.executeAction).toHaveBeenCalledWith('1');
  });
  
  it('should call executeWorkflow when a workflow is executed', () => {
    const workflows = [
      { id: '1', title: 'Test Workflow', description: 'A test workflow', execute: jest.fn() }
    ];
    
    (mockCopilotEngine.state as any).workflows = workflows;
    
    render(<ChatInterface />);
    
    const workflowButton = screen.getByText('Test Workflow');
    fireEvent.click(workflowButton);
    
    expect(mockCopilotEngine.executeWorkflow).toHaveBeenCalledWith('1');
  });
  
  it('should call generateArtifact when an artifact is generated', () => {
    const artifacts = [
      { id: '1', title: 'Test Artifact', description: 'A test artifact', generate: jest.fn() }
    ];
    
    (mockCopilotEngine.state as any).artifacts = artifacts;
    
    render(<ChatInterface />);
    
    const artifactButton = screen.getByText('Test Artifact');
    fireEvent.click(artifactButton);
    
    expect(mockCopilotEngine.generateArtifact).toHaveBeenCalledWith('1');
  });
  
  it('should call dismissSuggestion when a suggestion is dismissed', () => {
    const suggestions = [
      { id: '1', text: 'Test Suggestion', confidence: 0.8, dismiss: jest.fn() }
    ];
    
    (mockCopilotEngine.state as any).suggestions = suggestions;
    
    render(<ChatInterface />);
    
    const dismissButton = screen.getByTestId('dismiss-suggestion-1');
    fireEvent.click(dismissButton);
    
    expect(mockCopilotEngine.dismissSuggestion).toHaveBeenCalledWith('1');
  });
  
  it('should call retryLastAction when retry is clicked', () => {
    render(<ChatInterface />);
    
    const retryButton = screen.getByTestId('retry-button');
    fireEvent.click(retryButton);
    
    expect(mockCopilotEngine.retryLastAction).toHaveBeenCalled();
  });
  
  it('should call refreshState when refresh is clicked', () => {
    render(<ChatInterface />);
    
    const refreshButton = screen.getByTestId('refresh-button');
    fireEvent.click(refreshButton);
    
    expect(mockCopilotEngine.refreshState).toHaveBeenCalled();
  });
  
  it('should call togglePanel when panel toggle is clicked', () => {
    render(<ChatInterface />);
    
    const panelToggle = screen.getByTestId('panel-toggle');
    fireEvent.click(panelToggle);
    
    expect(mockCopilotEngine.togglePanel).toHaveBeenCalledWith('suggestions');
  });
  
  it('should call toggleModality when modality is changed', () => {
    render(<ChatInterface />);
    
    const modalitySelect = screen.getByTestId('modality-select');
    fireEvent.change(modalitySelect, { target: { value: 'voice' } });
    
    expect(mockCopilotEngine.toggleModality).toHaveBeenCalledWith('voice');
  });
  
  it('should call updateUIConfig when UI config is changed', () => {
    render(<ChatInterface />);
    
    const themeSelect = screen.getByTestId('theme-select');
    fireEvent.change(themeSelect, { target: { value: 'dark' } });
    
    expect(mockCopilotEngine.updateUIConfig).toHaveBeenCalledWith({ theme: 'dark' });
  });
  
  it('should use performance optimizations', () => {
    render(<ChatInterface />);
    
    // Check if performance hooks were called
    expect(usePerformance).toHaveBeenCalledWith('ChatInterface');
    
    const { useVirtualScroll, useDebounce, useThrottle, useLazyLoadImage, useMemoize, useRenderTime, useShouldUpdate } = require('../hooks/usePerformance');
    
    expect(useVirtualScroll).toHaveBeenCalled();
    expect(useDebounce).toHaveBeenCalled();
    expect(useThrottle).toHaveBeenCalled();
    expect(useLazyLoadImage).toHaveBeenCalled();
    expect(useMemoize).toHaveBeenCalled();
    expect(useRenderTime).toHaveBeenCalled();
    expect(useShouldUpdate).toHaveBeenCalled();
  });
  
  it('should render optimized components', () => {
    render(<ChatInterface />);
    
    // Check if optimized components are rendered
    expect(screen.getByTestId('virtualized-message-list')).toBeInTheDocument();
    expect(screen.getByTestId('optimized-image')).toBeInTheDocument();
    expect(screen.getByTestId('optimized-code-block')).toBeInTheDocument();
  });
  
  it('should handle empty state', () => {
    render(<ChatInterface />);
    
    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('No messages yet. Start a conversation!')).toBeInTheDocument();
  });
  
  it('should handle large message lists efficiently', () => {
    // Create a large number of messages
    const messages = Array.from({ length: 1000 }, (_, i) => ({
      id: `message-${i}`,
      content: `Message ${i}`,
      role: i % 2 === 0 ? 'user' : 'assistant',
      timestamp: new Date()
    }));
    
    (mockCopilotEngine.state as any).messages = messages;
    
    render(<ChatInterface />);
    
    // Check if virtual scrolling is used
    expect(screen.getByTestId('virtualized-message-list')).toBeInTheDocument();
  });
  
  it('should debounce input changes', () => {
    const { useDebounce } = require('../hooks/usePerformance');
    const mockDebounce = jest.fn((value: string) => value);
    useDebounce.mockImplementation(mockDebounce);
    
    render(<ChatInterface />);
    
    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    
    expect(mockDebounce).toHaveBeenCalled();
  });
  
  it('should throttle scroll events', () => {
    const { useThrottle } = require('../hooks/usePerformance');
    const mockThrottle = jest.fn((fn: (...args: unknown[]) => unknown) => fn);
    useThrottle.mockImplementation(mockThrottle);
    
    render(<ChatInterface />);
    
    const scrollContainer = screen.getByTestId('scroll-container');
    fireEvent.scroll(scrollContainer);
    
    expect(mockThrottle).toHaveBeenCalled();
  });
  
  it('should lazy load images', () => {
    const { useLazyLoadImage } = require('../hooks/usePerformance');
    const mockLazyLoadImage = jest.fn(() => ({ loaded: true, error: null }));
    useLazyLoadImage.mockImplementation(mockLazyLoadImage);
    
    render(<ChatInterface />);
    
    expect(mockLazyLoadImage).toHaveBeenCalled();
  });
  
  it('should memoize expensive calculations', () => {
    const { useMemoize } = require('../hooks/usePerformance');
    const mockMemoize = jest.fn((fn: (...args: unknown[]) => unknown) => fn);
    useMemoize.mockImplementation(mockMemoize);
    
    render(<ChatInterface />);
    
    expect(mockMemoize).toHaveBeenCalled();
  });
  
  it('should track render time', () => {
    const { useRenderTime } = require('../hooks/usePerformance');
    const mockRenderTime = jest.fn(() => ({
      getAverageRenderTime: jest.fn(() => 0),
      getMaxRenderTime: jest.fn(() => 0),
      renderCount: 0
    }));
    useRenderTime.mockImplementation(mockRenderTime);
    
    render(<ChatInterface />);
    
    expect(mockRenderTime).toHaveBeenCalled();
  });
  
  it('should check if component should update', () => {
    const { useShouldUpdate } = require('../hooks/usePerformance');
    const mockShouldUpdate = jest.fn(() => false);
    useShouldUpdate.mockImplementation(mockShouldUpdate);
    
    render(<ChatInterface />);
    
    expect(mockShouldUpdate).toHaveBeenCalled();
  });
});
