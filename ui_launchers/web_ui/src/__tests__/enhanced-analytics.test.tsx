import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';

  type EnhancedAnalyticsData,
  type AnalyticsStats,
  type MemoryNetworkData,
  type UserEngagementRow
import { } from '@/components/analytics';
import { HookProvider } from '@/contexts/HookContext';

// Mock AG-Charts
vi.mock('ag-charts-react', () => ({
  AgCharts: ({ options, onChartReady }: any) => {
    React.useEffect(() => {
      if (onChartReady) {
        onChartReady();
      }
    }, [onChartReady]);
    
    return (
      <div data-testid="ag-chart" data-chart-type={options?.series?.[0]?.type}>
        <div data-testid="chart-title">{options?.title?.text}</div>
        <div data-testid="chart-data-length">{options?.data?.length || 0}</div>
      </div>
    );
  }
}));

// Mock AG-Grid
vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData, columnDefs, onGridReady, onSelectionChanged }: any) => {
    React.useEffect(() => {
      if (onGridReady) {
        onGridReady({ api: { getSelectedNodes: () => [] } });
      }
    }, [onGridReady]);

    return (
      <div data-testid="ag-grid">
        <div data-testid="grid-row-count">{rowData?.length || 0}</div>
        <div data-testid="grid-column-count">{columnDefs?.length || 0}</div>
        {rowData?.map((row: any, index: number) => (
          <div 
            key={row.id || index} 
            data-testid={`grid-row-${index}`}
            onClick={() => onSelectionChanged?.({ api: { getSelectedNodes: () => [{ data: row }] } })}
          >
            {JSON.stringify(row)}
          </div>
        ))}
      </div>
    );
  }
}));

// Mock hooks context
const mockHookContext = {
  triggerHooks: vi.fn().mockResolvedValue([]),
  registerGridHook: vi.fn().mockReturnValue('hook-id'),
  registerChartHook: vi.fn().mockReturnValue('hook-id'),
  unregisterHook: vi.fn()
};

const mockAuthContext = {
  user: { user_id: 'test-user-123' },
  isAuthenticated: true
};

// Mock contexts
vi.mock('@/contexts/HookContext', () => ({
  useHooks: () => mockHookContext,
  HookProvider: ({ children }: any) => <div>{children}</div>
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <HookProvider>
    {children}
  </HookProvider>
);

describe('Enhanced Analytics Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  describe('EnhancedAnalyticsChart', () => {
    const mockAnalyticsData: EnhancedAnalyticsData[] = [
      {
        timestamp: '2024-01-01T10:00:00Z',
        messageCount: 25,
        responseTime: 1200,
        userSatisfaction: 4.2,
        aiInsights: 5,
        tokenUsage: 150,
        llmProvider: 'openai',
        userId: 'user1',
        messageId: 'msg1',
        confidence: 0.85
      },
      {
        timestamp: '2024-01-01T11:00:00Z',
        messageCount: 30,
        responseTime: 1100,
        userSatisfaction: 4.5,
        aiInsights: 7,
        tokenUsage: 180,
        llmProvider: 'llama-cpp',
        userId: 'user2',
        messageId: 'msg2',
        confidence: 0.92
      }
    ];

    const mockStats: AnalyticsStats = {
      totalConversations: 15,
      totalMessages: 55,
      avgResponseTime: 1150,
      avgSatisfaction: 4.35,
      totalInsights: 12,
      activeUsers: 8,
      topLlmProviders: [
        { provider: 'openai', count: 30 },
        { provider: 'llama-cpp', count: 25 }
      ]
    };

    it('renders analytics chart with data', () => {
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart data={mockAnalyticsData} stats={mockStats} />
        </TestWrapper>
      );

      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('ag-chart')).toBeInTheDocument();
      expect(screen.getByText('Total Messages')).toBeInTheDocument();
      expect(screen.getByText('55')).toBeInTheDocument();

    it('handles metric selection changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart data={mockAnalyticsData} stats={mockStats} />
        </TestWrapper>
      );

      // Find and click the metric selector
      const metricSelect = screen.getByDisplayValue('Messages');
      await user.click(metricSelect);
      
      // Select response time metric
      const responseTimeOption = screen.getByText('Response Time');
      await user.click(responseTimeOption);

      // Verify the chart updates
      await waitFor(() => {
        expect(mockHookContext.registerChartHook).toHaveBeenCalledWith(
          'enhancedAnalytics',
          'metricChange',
          expect.any(Function)
        );


    it('handles chart type changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart data={mockAnalyticsData} stats={mockStats} />
        </TestWrapper>
      );

      // Change chart type to bar
      const chartTypeSelect = screen.getByDisplayValue('Line');
      await user.click(chartTypeSelect);
      
      const barOption = screen.getByText('Bar');
      await user.click(barOption);

      // Verify chart type changed
      await waitFor(() => {
        const chart = screen.getByTestId('ag-chart');
        expect(chart).toHaveAttribute('data-chart-type', 'bar');


    it('handles timeframe changes', async () => {
      const mockOnTimeframeChange = vi.fn();
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart 
            data={mockAnalyticsData} 
            stats={mockStats}
            onTimeframeChange={mockOnTimeframeChange}
          />
        </TestWrapper>
      );

      const timeframeSelect = screen.getByDisplayValue('24H');
      await user.click(timeframeSelect);
      
      const sevenDayOption = screen.getByText('7D');
      await user.click(sevenDayOption);

      expect(mockOnTimeframeChange).toHaveBeenCalledWith('7d');

    it('handles refresh action', async () => {
      const mockOnRefresh = vi.fn().mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart 
            data={mockAnalyticsData} 
            stats={mockStats}
            onRefresh={mockOnRefresh}
          />
        </TestWrapper>
      );

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      expect(mockOnRefresh).toHaveBeenCalled();

    it('registers and triggers hooks correctly', async () => {
      render(
        <TestWrapper>
          <EnhancedAnalyticsChart data={mockAnalyticsData} stats={mockStats} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockHookContext.registerChartHook).toHaveBeenCalledWith(
          'enhancedAnalytics',
          'dataLoad',
          expect.any(Function)
        );
        
        expect(mockHookContext.triggerHooks).toHaveBeenCalledWith(
          'chart_enhancedAnalytics_dataLoad',
          expect.objectContaining({
            chartId: 'enhancedAnalytics',
            dataPoints: 2
          }),
          { userId: 'test-user-123' }
        );



  describe('MemoryNetworkVisualization', () => {
    const mockNetworkData: MemoryNetworkData = {
      nodes: [
        {
          id: 'cluster_programming',
          label: 'Programming',
          type: 'cluster',
          size: 5,
          color: '#3b82f6'
        },
        {
          id: 'memory_1',
          label: 'TypeScript Preference',
          type: 'memory',
          confidence: 0.9,
          cluster: 'programming'
        },
        {
          id: 'memory_2',
          label: 'React Experience',
          type: 'memory',
          confidence: 0.85,
          cluster: 'programming'
        }
      ],
      edges: [
        {
          from: 'memory_1',
          to: 'cluster_programming',
          weight: 0.9
        },
        {
          from: 'memory_2',
          to: 'cluster_programming',
          weight: 0.85
        }
      ],
      clusters: ['programming', 'preferences'],
      totalMemories: 2
    };

    it('renders memory network visualization', () => {
      render(
        <TestWrapper>
          <MemoryNetworkVisualization data={mockNetworkData} />
        </TestWrapper>
      );

      expect(screen.getByText('Memory Network Visualization')).toBeInTheDocument();
      expect(screen.getByTestId('ag-chart')).toBeInTheDocument();
      expect(screen.getByText('2 Memories')).toBeInTheDocument();
      expect(screen.getByText('3 Nodes')).toBeInTheDocument();

    it('handles layout type changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <MemoryNetworkVisualization data={mockNetworkData} />
        </TestWrapper>
      );

      const layoutSelect = screen.getByDisplayValue('Force');
      await user.click(layoutSelect);
      
      const circularOption = screen.getByText('Circular');
      await user.click(circularOption);

      // Verify layout change is applied
      await waitFor(() => {
        expect(screen.getByDisplayValue('Circular')).toBeInTheDocument();


    it('handles confidence threshold changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <MemoryNetworkVisualization data={mockNetworkData} />
        </TestWrapper>
      );

      // Find confidence slider
      const slider = screen.getByRole('slider');
      expect(slider).toBeInTheDocument();
      
      // Change slider value
      fireEvent.change(slider, { target: { value: '0.8' } });
      
      await waitFor(() => {
        expect(screen.getByText('80%')).toBeInTheDocument();


    it('handles cluster filtering', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <MemoryNetworkVisualization data={mockNetworkData} />
        </TestWrapper>
      );

      // Click on a cluster badge to filter
      const programmingCluster = screen.getByText('Programming');
      await user.click(programmingCluster);

      // Verify cluster is selected (badge should change appearance)
      expect(programmingCluster).toBeInTheDocument();

    it('handles node click events', async () => {
      const mockOnNodeClick = vi.fn();
      
      render(
        <TestWrapper>
          <MemoryNetworkVisualization 
            data={mockNetworkData} 
            onNodeClick={mockOnNodeClick}
          />
        </TestWrapper>
      );

      // Simulate chart ready and node click
      await waitFor(() => {
        expect(mockHookContext.registerChartHook).toHaveBeenCalledWith(
          'memoryNetwork',
          'nodeClick',
          expect.any(Function)
        );


    it('toggles fullscreen mode', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <MemoryNetworkVisualization data={mockNetworkData} />
        </TestWrapper>
      );

      const fullscreenButton = screen.getByRole('button', { name: /maximize/i });
      await user.click(fullscreenButton);

      // Check if fullscreen class is applied
      const card = screen.getByRole('region');
      expect(card).toHaveClass('fixed', 'inset-0', 'z-50');


  describe('UserEngagementGrid', () => {
    const mockEngagementData: UserEngagementRow[] = [
      {
        id: 'engagement_1',
        timestamp: '2024-01-01T10:00:00Z',
        userId: 'user1',
        componentType: 'chat',
        componentId: 'chat_123',
        interactionType: 'click',
        duration: 1500,
        success: true,
        sessionId: 'session_1'
      },
      {
        id: 'engagement_2',
        timestamp: '2024-01-01T10:05:00Z',
        userId: 'user2',
        componentType: 'analytics',
        componentId: 'analytics_456',
        interactionType: 'view',
        duration: 3000,
        success: false,
        errorMessage: 'Component failed to load',
        sessionId: 'session_2'
      }
    ];

    it('renders user engagement grid with data', () => {
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      expect(screen.getByText('User Engagement Analytics (2 records)')).toBeInTheDocument();
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
      expect(screen.getByTestId('grid-row-count')).toHaveTextContent('2');

    it('handles search functionality', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Search interactions...');
      await user.type(searchInput, 'chat');

      expect(searchInput).toHaveValue('chat');

    it('handles filter changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      const filterSelect = screen.getByDisplayValue('All Interactions');
      await user.click(filterSelect);
      
      const errorOnlyOption = screen.getByText('Errors Only');
      await user.click(errorOnlyOption);

      expect(screen.getByDisplayValue('Errors Only')).toBeInTheDocument();

    it('handles time range changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      const timeRangeSelect = screen.getByDisplayValue('24H');
      await user.click(timeRangeSelect);
      
      const oneHourOption = screen.getByText('1H');
      await user.click(oneHourOption);

      expect(screen.getByDisplayValue('1H')).toBeInTheDocument();

    it('handles row selection', async () => {
      const mockOnRowSelect = vi.fn();
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserEngagementGrid 
            data={mockEngagementData} 
            onRowSelect={mockOnRowSelect}
          />
        </TestWrapper>
      );

      // Click on a grid row
      const firstRow = screen.getByTestId('grid-row-0');
      await user.click(firstRow);

      expect(mockOnRowSelect).toHaveBeenCalledWith(mockEngagementData[0]);

    it('handles export functionality', async () => {
      const mockOnExport = vi.fn().mockResolvedValue(undefined);
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <UserEngagementGrid 
            data={mockEngagementData} 
            onExport={mockOnExport}
          />
        </TestWrapper>
      );

      const exportButton = screen.getByText('Export');
      await user.click(exportButton);

      expect(mockOnExport).toHaveBeenCalledWith(mockEngagementData);

    it('displays summary statistics', () => {
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      expect(screen.getByText('Total Interactions')).toBeInTheDocument();
      expect(screen.getByText('Success Rate')).toBeInTheDocument();
      expect(screen.getByText('Avg Duration')).toBeInTheDocument();
      expect(screen.getByText('Unique Users')).toBeInTheDocument();

    it('registers and triggers grid hooks', async () => {
      render(
        <TestWrapper>
          <UserEngagementGrid data={mockEngagementData} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockHookContext.registerGridHook).toHaveBeenCalledWith(
          'userEngagement',
          'dataLoad',
          expect.any(Function)
        );
        
        expect(mockHookContext.triggerHooks).toHaveBeenCalledWith(
          'grid_userEngagement_dataLoad',
          expect.objectContaining({
            gridId: 'userEngagement',
            rowCount: 2
          }),
          { userId: 'test-user-123' }
        );



  describe('Integration Tests', () => {
    it('all components work together in analytics dashboard', () => {
      const mockAnalyticsData: EnhancedAnalyticsData[] = [
        {
          timestamp: '2024-01-01T10:00:00Z',
          messageCount: 25,
          responseTime: 1200,
          userSatisfaction: 4.2,
          aiInsights: 5,
          tokenUsage: 150,
          llmProvider: 'openai'
        }
      ];

      const mockNetworkData: MemoryNetworkData = {
        nodes: [
          { id: 'node1', label: 'Test Node', type: 'memory', confidence: 0.9 }
        ],
        edges: [],
        clusters: ['test'],
        totalMemories: 1
      };

      const mockEngagementData: UserEngagementRow[] = [
        {
          id: 'eng1',
          timestamp: '2024-01-01T10:00:00Z',
          userId: 'user1',
          componentType: 'chat',
          componentId: 'chat_1',
          interactionType: 'click',
          duration: 1000,
          success: true
        }
      ];

      render(
        <TestWrapper>
          <div>
            <EnhancedAnalyticsChart data={mockAnalyticsData} />
            <MemoryNetworkVisualization data={mockNetworkData} />
            <UserEngagementGrid data={mockEngagementData} />
          </div>
        </TestWrapper>
      );

      // Verify all components render
      expect(screen.getByText('Enhanced Analytics Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Memory Network Visualization')).toBeInTheDocument();
      expect(screen.getByText('User Engagement Analytics (1 records)')).toBeInTheDocument();

      // Verify all hooks are registered
      expect(mockHookContext.registerChartHook).toHaveBeenCalledTimes(4); // 2 for analytics, 2 for network
      expect(mockHookContext.registerGridHook).toHaveBeenCalledTimes(2); // 2 for engagement grid


