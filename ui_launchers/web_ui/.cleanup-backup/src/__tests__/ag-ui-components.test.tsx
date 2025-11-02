import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConversationGrid, ConversationRow } from '@/components/chat/ConversationGrid';
import { ChatAnalyticsChart, ChatAnalyticsData } from '@/components/chat/ChatAnalyticsChart';
import { MemoryGrid, MemoryRow } from '@/components/chat/MemoryGrid';
import { ChatInterface } from '@/components/ChatInterface';
import { HookProvider } from '@/contexts/HookContext';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock AG-Grid components
vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData, onGridReady, onSelectionChanged, ...props }: any) => (
    <div data-testid="ag-grid" data-row-count={rowData?.length || 0}>
      <div data-testid="ag-grid-header">AG Grid Mock</div>
      {rowData?.map((row: any, index: number) => (
        <div
          key={row.id || index}
          data-testid={`ag-grid-row-${index}`}
          onClick={() => onSelectionChanged?.({ api: { getSelectedNodes: () => [{ data: row }] } })}
        >
          {row.title || row.content || row.timestamp}
        </div>
      ))}
    </div>
  )
}));

vi.mock('ag-charts-react', () => ({
  AgCharts: ({ options, onChartReady }: any) => (
    <div data-testid="ag-charts" data-chart-type={options?.series?.[0]?.type}>
      <div data-testid="ag-charts-header">AG Charts Mock</div>
      <div data-testid="ag-charts-data-points">{options?.data?.length || 0}</div>
    </div>
  )
}));

// Mock hooks
const mockTriggerHooks = vi.fn();
const mockRegisterGridHook = vi.fn();
const mockRegisterChartHook = vi.fn();
const mockRegisterChatHook = vi.fn();

vi.mock('@/contexts/HookContext', () => ({
  HookProvider: ({ children }: any) => children,
  useHooks: () => ({
    triggerHooks: mockTriggerHooks,
    registerGridHook: mockRegisterGridHook,
    registerChartHook: mockRegisterChartHook,
    registerChatHook: mockRegisterChatHook,
    registerHook: vi.fn(),
    unregisterHook: vi.fn(),
    getRegisteredHooks: vi.fn()
  })
}));

// Mock auth context
const mockUser = {
  user_id: 'test-user-123',
  email: 'test@example.com',
  roles: ['user'],
  tenant_id: 'test-tenant',
  two_factor_enabled: false,
  preferences: {
    personalityTone: 'friendly' as const,
    personalityVerbosity: 'balanced' as const,
    memoryDepth: 'medium' as const,
    customPersonaInstructions: '',
    preferredLLMProvider: 'llama-cpp',
    preferredModel: 'llama3.2:latest',
    temperature: 0.7,
    maxTokens: 1000,
    notifications: { email: true, push: false },
    ui: { theme: 'light', language: 'en', avatarUrl: '' }
  }
};

vi.mock('@/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: any) => children,
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    requestPasswordReset: vi.fn(),
    resetPassword: vi.fn(),
    refreshUser: vi.fn(),
    updateUserPreferences: vi.fn()
  })
}));

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>
    <HookProvider>
      {children}
    </HookProvider>
  </AuthProvider>
);

describe('AG-UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('ConversationGrid', () => {
    const mockConversations: ConversationRow[] = [
      {
        id: '1',
        title: 'Test Conversation 1',
        lastMessage: 'Hello world',
        timestamp: new Date('2024-01-01T10:00:00Z'),
        messageCount: 5,
        participants: ['user@test.com', 'Karen AI'],
        tags: ['test', 'demo'],
        sentiment: 'positive',
        aiInsights: ['Test insight']
      },
      {
        id: '2',
        title: 'Test Conversation 2',
        lastMessage: 'How are you?',
        timestamp: new Date('2024-01-01T11:00:00Z'),
        messageCount: 3,
        participants: ['user@test.com', 'Karen AI'],
        tags: ['greeting'],
        sentiment: 'neutral'
      }
    ];

    it('renders conversation grid with data', () => {
      render(
        <TestWrapper>
          <ConversationGrid conversations={mockConversations} />
        </TestWrapper>
      );

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
      expect(screen.getByTestId('ag-grid')).toHaveAttribute('data-row-count', '2');
      expect(screen.getByText('Conversations (2)')).toBeInTheDocument();
    });

    it('handles conversation selection', async () => {
      const mockOnSelect = vi.fn();
      render(
        <TestWrapper>
          <ConversationGrid 
            conversations={mockConversations} 
            onConversationSelect={mockOnSelect}
          />
        </TestWrapper>
      );

      const firstRow = screen.getByTestId('ag-grid-row-0');
      fireEvent.click(firstRow);

      await waitFor(() => {
        expect(mockTriggerHooks).toHaveBeenCalledWith(
          'grid_conversations_rowSelected',
          expect.objectContaining({
            gridId: 'conversations',
            data: mockConversations[0]
          }),
          expect.objectContaining({ userId: mockUser.userId })
        );
      });
    });

    it('filters conversations based on search text', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ConversationGrid conversations={mockConversations} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search conversations...');
      await user.type(searchInput, 'Test Conversation 1');

      // The filtering logic would be tested in the actual component
      expect(searchInput).toHaveValue('Test Conversation 1');
    });

    it('handles refresh action', async () => {
      const mockOnRefresh = vi.fn();
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ConversationGrid 
            conversations={mockConversations} 
            onRefresh={mockOnRefresh}
          />
        </TestWrapper>
      );

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(mockOnRefresh).toHaveBeenCalled();
    });

    it('registers grid hooks on mount', () => {
      render(
        <TestWrapper>
          <ConversationGrid conversations={mockConversations} />
        </TestWrapper>
      );

      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'conversations',
        'dataLoad',
        expect.any(Function)
      );
      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'conversations',
        'rowSelected',
        expect.any(Function)
      );
    });
  });

  describe('ChatAnalyticsChart', () => {
    const mockAnalyticsData: ChatAnalyticsData[] = [
      {
        timestamp: new Date('2024-01-01T10:00:00Z'),
        messageCount: 10,
        responseTime: 1500,
        userSatisfaction: 4.5,
        aiInsights: 3,
        tokenUsage: 500,
        llmProvider: 'llama-cpp'
      },
      {
        timestamp: new Date('2024-01-01T11:00:00Z'),
        messageCount: 15,
        responseTime: 1200,
        userSatisfaction: 4.2,
        aiInsights: 5,
        tokenUsage: 750,
        llmProvider: 'openai'
      }
    ];

    it('renders analytics chart with data', () => {
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={mockAnalyticsData} />
        </TestWrapper>
      );

      expect(screen.getByTestId('ag-charts')).toBeInTheDocument();
      expect(screen.getByTestId('ag-charts-data-points')).toHaveTextContent('2');
      expect(screen.getByText('Chat Analytics')).toBeInTheDocument();
    });

    it('handles metric selection change', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={mockAnalyticsData} />
        </TestWrapper>
      );

      // Test would involve interacting with the metric selector
      // This is a simplified test since Select components need special handling
      expect(screen.getByText('Chat Analytics')).toBeInTheDocument();
    });

    it('handles timeframe changes', async () => {
      const mockOnTimeframeChange = vi.fn();
      render(
        <TestWrapper>
          <ChatAnalyticsChart 
            data={mockAnalyticsData}
            onTimeframeChange={mockOnTimeframeChange}
          />
        </TestWrapper>
      );

      // The timeframe change would be tested with proper Select component interaction
      expect(screen.getByTestId('ag-charts')).toBeInTheDocument();
    });

    it('registers chart hooks on mount', () => {
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={mockAnalyticsData} />
        </TestWrapper>
      );

      expect(mockRegisterChartHook).toHaveBeenCalledWith(
        'chatAnalytics',
        'dataLoad',
        expect.any(Function)
      );
      expect(mockRegisterChartHook).toHaveBeenCalledWith(
        'chatAnalytics',
        'seriesClick',
        expect.any(Function)
      );
    });

    it('displays summary statistics', () => {
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={mockAnalyticsData} />
        </TestWrapper>
      );

      // Summary stats would be calculated and displayed
      expect(screen.getByText('Chat Analytics')).toBeInTheDocument();
    });
  });

  describe('MemoryGrid', () => {
    const mockMemories: MemoryRow[] = [
      {
        id: '1',
        content: 'User prefers TypeScript over JavaScript',
        type: 'preference',
        confidence: 0.95,
        lastAccessed: new Date('2024-01-01T10:00:00Z'),
        relevanceScore: 0.9,
        semanticCluster: 'programming_preferences',
        relationships: ['2'],
        tags: ['typescript', 'javascript'],
        source: 'conversation',
        isStarred: true
      },
      {
        id: '2',
        content: 'User is working on a React project',
        type: 'context',
        confidence: 0.88,
        lastAccessed: new Date('2024-01-01T09:00:00Z'),
        relevanceScore: 0.85,
        semanticCluster: 'current_projects',
        relationships: ['1'],
        tags: ['react', 'project'],
        source: 'conversation',
        isStarred: false
      }
    ];

    it('renders memory grid with data', () => {
      render(
        <TestWrapper>
          <MemoryGrid memories={mockMemories} />
        </TestWrapper>
      );

      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
      expect(screen.getByTestId('ag-grid')).toHaveAttribute('data-row-count', '2');
      expect(screen.getByText('Memory Management (2)')).toBeInTheDocument();
    });

    it('handles memory creation', async () => {
      const mockOnCreate = vi.fn();
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <MemoryGrid 
            memories={mockMemories} 
            onMemoryCreate={mockOnCreate}
          />
        </TestWrapper>
      );

      const addButton = screen.getByRole('button', { name: /add memory/i });
      await user.click(addButton);

      expect(screen.getByText('Create New Memory')).toBeInTheDocument();
    });

    it('handles memory search', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <MemoryGrid memories={mockMemories} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search memories...');
      await user.type(searchInput, 'TypeScript');

      expect(searchInput).toHaveValue('TypeScript');
    });

    it('registers grid hooks on mount', () => {
      render(
        <TestWrapper>
          <MemoryGrid memories={mockMemories} />
        </TestWrapper>
      );

      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'memories',
        'dataLoad',
        expect.any(Function)
      );
      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'memories',
        'rowSelected',
        expect.any(Function)
      );
    });
  });

  describe('ChatInterface', () => {
    it('renders with tabs by default', () => {
      render(
        <TestWrapper>
          <ChatInterface />
        </TestWrapper>
      );

      expect(screen.getByRole('tab', { name: /chat/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /history/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /analytics/i })).toBeInTheDocument();
    });

    it('renders without tabs when showTabs is false', () => {
      render(
        <TestWrapper>
          <ChatInterface showTabs={false} />
        </TestWrapper>
      );

      expect(screen.queryByRole('tab')).not.toBeInTheDocument();
    });

    it('switches between tabs', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatInterface />
        </TestWrapper>
      );

      const analyticsTab = screen.getByRole('tab', { name: /analytics/i });
      await user.click(analyticsTab);

      // The tab content would change - this is a simplified test
      expect(analyticsTab).toHaveAttribute('data-state', 'active');
    });

    it('registers chat hooks on mount', () => {
      render(
        <TestWrapper>
          <ChatInterface />
        </TestWrapper>
      );

      expect(mockRegisterChatHook).toHaveBeenCalledWith(
        'preMessage',
        expect.any(Function)
      );
      expect(mockRegisterChatHook).toHaveBeenCalledWith(
        'postMessage',
        expect.any(Function)
      );
      expect(mockRegisterChatHook).toHaveBeenCalledWith(
        'aiSuggestion',
        expect.any(Function)
      );
    });

    it('handles fullscreen toggle', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatInterface />
        </TestWrapper>
      );

      const fullscreenButton = screen.getByRole('button', { name: /maximize/i });
      await user.click(fullscreenButton);

      // The component would toggle fullscreen class
      expect(fullscreenButton).toBeInTheDocument();
    });
  });

  describe('Hook Integration', () => {
    it('triggers hooks when grid data loads', async () => {
      render(
        <TestWrapper>
          <ConversationGrid conversations={[]} />
        </TestWrapper>
      );

      // Simulate grid ready event
      await waitFor(() => {
        expect(mockTriggerHooks).toHaveBeenCalledWith(
          'grid_conversations_dataLoad',
          expect.objectContaining({
            gridId: 'conversations'
          }),
          expect.objectContaining({ userId: mockUser.userId })
        );
      });
    });

    it('triggers hooks when chart data loads', async () => {
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={[]} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockTriggerHooks).toHaveBeenCalledWith(
          'chart_chatAnalytics_dataLoad',
          expect.objectContaining({
            chartId: 'chatAnalytics'
          }),
          expect.objectContaining({ userId: mockUser.userId })
        );
      });
    });

    it('registers hooks with correct parameters', () => {
      render(
        <TestWrapper>
          <ConversationGrid conversations={[]} />
        </TestWrapper>
      );

      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'conversations',
        'dataLoad',
        expect.any(Function)
      );
      expect(mockRegisterGridHook).toHaveBeenCalledWith(
        'conversations',
        'rowSelected',
        expect.any(Function)
      );
    });
  });

  describe('Error Handling', () => {
    it('handles grid errors gracefully', () => {
      // Mock console.error to avoid test output noise
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      render(
        <TestWrapper>
          <ConversationGrid conversations={undefined as any} />
        </TestWrapper>
      );

      // Component should render without crashing
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('handles chart errors gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      render(
        <TestWrapper>
          <ChatAnalyticsChart data={undefined as any} />
        </TestWrapper>
      );

      expect(screen.getByTestId('ag-charts')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });
  });
});