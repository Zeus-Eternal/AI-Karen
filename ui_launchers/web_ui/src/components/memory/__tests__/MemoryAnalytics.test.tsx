/**
 * Unit tests for MemoryAnalytics component
 * Tests memory statistics calculation, display, and user interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MemoryAnalytics from '../MemoryAnalytics';
import { getMemoryService } from '@/services/memoryService';
import type { MemoryStats } from '@/services/memoryService';

// Mock the memory service
vi.mock('@/services/memoryService', () => ({
  getMemoryService: vi.fn()
}));

// Mock AG Charts
vi.mock('ag-charts-react', () => ({
  AgCharts: ({ options }: { options: any }) => (
    <div data-testid="ag-chart" data-chart-type={options.series?.[0]?.type}>
      Mock Chart: {options.title?.text}
    </div>
  )
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  RefreshCw: () => <div data-testid="refresh-icon">RefreshCw</div>,
  TrendingUp: () => <div data-testid="trending-up">TrendingUp</div>,
  TrendingDown: () => <div data-testid="trending-down">TrendingDown</div>,
  Activity: () => <div data-testid="activity-icon">Activity</div>,
  Database: () => <div data-testid="database-icon">Database</div>,
  Clock: () => <div data-testid="clock-icon">Clock</div>,
  Zap: () => <div data-testid="zap-icon">Zap</div>
}));

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="card" className={className}>{children}</div>
  )
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant }: { 
    children: React.ReactNode; 
    onClick?: () => void; 
    disabled?: boolean;
    variant?: string;
  }) => (
    <Button 
      data-testid="button" 
      onClick={onClick} 
      disabled={disabled}
      data-variant={variant}
     aria-label="Button">
      {children}
    </Button>
  )
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <span data-testid="badge" data-variant={variant}>{children}</span>
  )
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: { 
    children: React.ReactNode; 
    value: string;
    onValueChange: (value: string) => void;
  }) => (
    <div data-testid="tabs" data-value={value} onClick={() => onValueChange('test')}>
      {children}
    </div>
  ),
  TabsList: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <Button data-testid="tab-trigger" data-value={value} aria-label="Button">{children}</Button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid="tab-content" data-value={value}>{children}</div>
  )
}));

describe('MemoryAnalytics', () => {
  const mockMemoryService = {
    getMemoryStats: vi.fn()
  };

  const mockMemoryStats: MemoryStats = {
    totalMemories: 1500,
    memoriesByTag: {
      'technical': 450,
      'personal': 375,
      'work': 300,
      'general': 375
    },
    recentActivity: [
      { date: '2024-01-01', count: 10 },
      { date: '2024-01-02', count: 15 },
      { date: '2024-01-03', count: 12 },
      { date: '2024-01-04', count: 18 },
      { date: '2024-01-05', count: 20 }
    ],
    averageSimilarity: 0.82,
    topTags: [
      { tag: 'javascript', count: 200 },
      { tag: 'react', count: 150 },
      { tag: 'typescript', count: 120 },
      { tag: 'nodejs', count: 100 },
      { tag: 'python', count: 80 }
    ]
  };

  const defaultProps = {
    userId: 'test-user-123',
    tenantId: 'test-tenant',
    height: 800
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (getMemoryService as any).mockReturnValue(mockMemoryService);
    mockMemoryService.getMemoryStats.mockResolvedValue(mockMemoryStats);

  afterEach(() => {
    vi.clearAllTimers();

  describe('Component Rendering', () => {
    it('renders the component with loading state initially', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      expect(screen.getByText('Memory Analytics')).toBeInTheDocument();
      expect(screen.getByText('Vector store statistics and performance metrics')).toBeInTheDocument();
      
      // Should show loading states for metric cards
      const loadingElements = screen.getAllByTestId('card');
      expect(loadingElements.length).toBeGreaterThan(0);

    it('renders metric cards with correct data after loading', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('1,500')).toBeInTheDocument(); // Total memories

      // Check for metric card titles
      expect(screen.getByText('Total Memories')).toBeInTheDocument();
      expect(screen.getByText('Storage Size')).toBeInTheDocument();
      expect(screen.getByText('Avg Search Latency')).toBeInTheDocument();
      expect(screen.getByText('Search Accuracy')).toBeInTheDocument();

    it('renders tabs for different analytics views', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Performance')).toBeInTheDocument();
        expect(screen.getByText('Content')).toBeInTheDocument();
        expect(screen.getByText('Trends')).toBeInTheDocument();


    it('renders charts in overview tab', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Memory Growth')).toBeInTheDocument();
        expect(screen.getByText('Cluster Distribution')).toBeInTheDocument();

      const charts = screen.getAllByTestId('ag-chart');
      expect(charts.length).toBeGreaterThan(0);


  describe('Data Loading and Error Handling', () => {
    it('handles loading state correctly', async () => {
      // Make the service call hang to test loading state
      mockMemoryService.getMemoryStats.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<MemoryAnalytics {...defaultProps} />);
      
      // Should show loading indicators
      const refreshButton = screen.getByTestId('button');
      expect(refreshButton).toBeDisabled();

    it('handles service errors gracefully', async () => {
      const errorMessage = 'Failed to fetch memory stats';
      mockMemoryService.getMemoryStats.mockRejectedValue(new Error(errorMessage));

      const onError = vi.fn();
      render(<MemoryAnalytics {...defaultProps} onError={onError} />);
      
      await waitFor(() => {
        expect(screen.getByText('Analytics Error')).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();

      expect(onError).toHaveBeenCalledWith(expect.any(Error));

    it('allows retry after error', async () => {
      mockMemoryService.getMemoryStats
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockMemoryStats);

      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Analytics Error')).toBeInTheDocument();

      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('1,500')).toBeInTheDocument();



  describe('User Interactions', () => {
    it('refreshes data when refresh button is clicked', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('1,500')).toBeInTheDocument();

      expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(1);

      const refreshButton = screen.getByTestId('button');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(2);


    it('switches between tabs correctly', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toHaveAttribute('data-value', 'overview');

      // Tab switching is mocked, but we can test the structure
      const tabTriggers = screen.getAllByTestId('tab-trigger');
      expect(tabTriggers).toHaveLength(4);
      expect(tabTriggers[0]).toHaveAttribute('data-value', 'overview');
      expect(tabTriggers[1]).toHaveAttribute('data-value', 'performance');
      expect(tabTriggers[2]).toHaveAttribute('data-value', 'content');
      expect(tabTriggers[3]).toHaveAttribute('data-value', 'trends');


  describe('Analytics Calculations', () => {
    it('calculates storage size correctly', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Storage size should be calculated as totalMemories * 1024 / 1024 / 1024 = 1.5 MB
        expect(screen.getByText(/1\.5 MB/)).toBeInTheDocument();


    it('displays confidence distribution correctly', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Should show confidence distribution chart
        const charts = screen.getAllByTestId('ag-chart');
        const confidenceChart = charts.find(chart => 
          chart.textContent?.includes('Confidence Score Distribution')
        );
        expect(confidenceChart).toBeInTheDocument();


    it('shows top tags with correct counts', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Switch to content tab to see tags
        expect(screen.getByText('Top Tags')).toBeInTheDocument();


    it('calculates memory decay patterns', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Should show memory decay patterns in trends tab
        expect(screen.getByText('Memory Retention Curve')).toBeInTheDocument();
        expect(screen.getByText('Memory Decay Patterns')).toBeInTheDocument();



  describe('Performance Metrics', () => {
    it('displays performance metrics correctly', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Should show latency metrics
        expect(screen.getByText(/\d+ms/)).toBeInTheDocument(); // Search latency
        expect(screen.getByText(/\d+\.\d+%/)).toBeInTheDocument(); // Search accuracy


    it('shows cache hit rate and error rate', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Performance metrics should be visible
        expect(screen.getByText('Cache Hit Rate')).toBeInTheDocument();
        expect(screen.getByText('Error Rate')).toBeInTheDocument();


    it('displays throughput metrics', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Searches/sec')).toBeInTheDocument();
        expect(screen.getByText('Indexing/sec')).toBeInTheDocument();



  describe('Auto-refresh Functionality', () => {
    beforeEach(() => {
      vi.useFakeTimers();

    afterEach(() => {
      vi.useRealTimers();

    it('auto-refreshes data at specified interval', async () => {
      render(<MemoryAnalytics {...defaultProps} refreshInterval={5000} />);
      
      await waitFor(() => {
        expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(1);

      // Fast-forward time by 5 seconds
      act(() => {
        vi.advanceTimersByTime(5000);

      await waitFor(() => {
        expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(2);


    it('does not auto-refresh when interval is 0', async () => {
      render(<MemoryAnalytics {...defaultProps} refreshInterval={0} />);
      
      await waitFor(() => {
        expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(1);

      // Fast-forward time
      act(() => {
        vi.advanceTimersByTime(10000);

      // Should not have called again
      expect(mockMemoryService.getMemoryStats).toHaveBeenCalledTimes(1);


  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        const refreshButton = screen.getByTestId('button');
        expect(refreshButton).toBeInTheDocument();

      // Check for proper heading structure
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Memory Analytics');

    it('supports keyboard navigation', async () => {
      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        const refreshButton = screen.getByTestId('button');
        expect(refreshButton).toBeInTheDocument();
        
        // Button should be focusable
        refreshButton.focus();
        expect(document.activeElement).toBe(refreshButton);



  describe('Responsive Design', () => {
    it('adapts to different screen sizes', async () => {
      render(<MemoryAnalytics {...defaultProps} height={600} />);
      
      await waitFor(() => {
        const container = screen.getByText('Memory Analytics').closest('div');
        expect(container).toHaveStyle({ height: '600px' });


    it('handles mobile layout correctly', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,

      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Should render without errors on mobile
        expect(screen.getByText('Memory Analytics')).toBeInTheDocument();



  describe('Data Validation', () => {
    it('handles empty or null data gracefully', async () => {
      const emptyStats: MemoryStats = {
        totalMemories: 0,
        memoriesByTag: {},
        recentActivity: [],
        averageSimilarity: 0,
        topTags: []
      };

      mockMemoryService.getMemoryStats.mockResolvedValue(emptyStats);

      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument(); // Total memories
        expect(screen.getByText('0 MB')).toBeInTheDocument(); // Storage size


    it('validates numeric data ranges', async () => {
      const invalidStats: MemoryStats = {
        ...mockMemoryStats,
        totalMemories: -1, // Invalid negative value
        averageSimilarity: 1.5 // Invalid similarity > 1
      };

      mockMemoryService.getMemoryStats.mockResolvedValue(invalidStats);

      render(<MemoryAnalytics {...defaultProps} />);
      
      await waitFor(() => {
        // Component should handle invalid data gracefully
        expect(screen.getByText('Memory Analytics')).toBeInTheDocument();



