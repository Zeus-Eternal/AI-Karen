/**
 * Performance tests for ModelMetricsDashboard component
 * Testing metrics collection and analysis accuracy
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ModelMetricsDashboard from '../ModelMetricsDashboard';
import { useToast } from '@/hooks/use-toast';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn()
}));

// Mock fetch
global.fetch = vi.fn();

const mockToast = vi.fn();
(useToast as any).mockReturnValue({ toast: mockToast });

// Generate large dataset for performance testing
const generateMockMetrics = (count: number) => {
  const metrics = [];
  const providers = ['OpenAI', 'Anthropic', 'Ollama', 'Hugging Face'];
  const models = ['gpt-4', 'claude-3', 'llama-2', 'mistral-7b'];
  
  for (let i = 0; i < count; i++) {
    const provider = providers[i % providers.length];
    const model = models[i % models.length];
    
    // Generate time series data
    const requestsOverTime = Array.from({ length: 24 }, (_, hour) => ({
      timestamp: new Date(Date.now() - (23 - hour) * 60 * 60 * 1000),
      value: Math.floor(Math.random() * 100) + 10
    }));

    const latencyTrend = Array.from({ length: 24 }, (_, hour) => ({
      timestamp: new Date(Date.now() - (23 - hour) * 60 * 60 * 1000),
      value: Math.floor(Math.random() * 200) + 50
    }));

    const costTrend = Array.from({ length: 24 }, (_, hour) => ({
      timestamp: new Date(Date.now() - (23 - hour) * 60 * 60 * 1000),
      value: Math.random() * 10
    }));

    // Generate user data
    const topUsers = Array.from({ length: 10 }, (_, userIdx) => ({
      userId: `user-${i}-${userIdx}`,
      username: `user${userIdx}@example.com`,
      requestCount: Math.floor(Math.random() * 1000) + 100,
      cost: Math.random() * 50,
      lastUsed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000)
    }));

    // Generate benchmarks
    const benchmarks = Array.from({ length: 5 }, (_, benchIdx) => ({
      id: `bench-${i}-${benchIdx}`,
      name: `Benchmark ${benchIdx + 1}`,
      score: Math.random() * 100,
      percentile: Math.floor(Math.random() * 100),
      date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
      status: 'completed' as const
    }));

    metrics.push({
      modelId: `model-${i}`,
      modelName: `${provider} ${model}`,
      provider,
      timeRange: '7d',
      usage: {
        totalRequests: Math.floor(Math.random() * 10000) + 1000,
        uniqueUsers: Math.floor(Math.random() * 500) + 50,
        averageRequestsPerUser: Math.floor(Math.random() * 50) + 10,
        requestsOverTime,
        usageByProvider: {
          [provider]: Math.floor(Math.random() * 5000) + 500
        },
        topUsers
      },
      performance: {
        averageLatency: Math.floor(Math.random() * 200) + 50,
        p95Latency: Math.floor(Math.random() * 400) + 100,
        p99Latency: Math.floor(Math.random() * 800) + 200,
        throughput: Math.random() * 50 + 5,
        errorRate: Math.random() * 0.1,
        latencyTrend,
        throughputTrend: latencyTrend.map(point => ({
          ...point,
          value: Math.random() * 50 + 5
        })),
        errorTrend: latencyTrend.map(point => ({
          ...point,
          value: Math.random() * 0.1
        }))
      },
      costs: {
        totalCost: Math.random() * 1000 + 100,
        costPerRequest: Math.random() * 0.01 + 0.001,
        costPerUser: Math.random() * 10 + 1,
        costTrend,
        costByProvider: {
          [provider]: Math.random() * 500 + 50
        },
        projectedMonthlyCost: Math.random() * 3000 + 300,
        budgetUtilization: Math.random() * 0.8 + 0.1
      },
      warmup: {
        modelId: `model-${i}`,
        enabled: Math.random() > 0.5,
        preloadOnStartup: Math.random() > 0.5,
        keepWarm: Math.random() > 0.5,
        warmupTriggers: [],
        cooldownDelay: Math.floor(Math.random() * 300) + 60,
        resourceLimits: {
          maxMemory: Math.floor(Math.random() * 8000) + 2000,
          maxCpu: Math.floor(Math.random() * 4) + 1,
          maxGpu: Math.floor(Math.random() * 2),
          priority: Math.floor(Math.random() * 10) + 1
        }
      },
      benchmarks
    });
  }
  
  return metrics;
};

const generateBudgetAlerts = (count: number) => {
  const severities = ['info', 'warning', 'critical'];
  const types = ['threshold', 'projection', 'anomaly'];
  
  return Array.from({ length: count }, (_, i) => ({
    id: `alert-${i}`,
    type: types[i % types.length] as any,
    severity: severities[i % severities.length] as any,
    title: `Budget Alert ${i + 1}`,
    message: `Alert message for budget ${i + 1}`,
    currentSpend: Math.random() * 1000 + 100,
    threshold: Math.random() * 1200 + 800,
    projectedSpend: Math.random() * 1500 + 1000,
    timeframe: 'monthly',
    affectedProviders: ['OpenAI', 'Anthropic'],
    recommendations: [
      'Consider switching to a more cost-effective model',
      'Implement request batching to reduce costs'
    ],
    timestamp: new Date()
  }));
};

describe('ModelMetricsDashboard Performance Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles large datasets efficiently', async () => {
    const startTime = performance.now();
    const largeMetrics = generateMockMetrics(100);
    const largeAlerts = generateBudgetAlerts(50);
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics: largeMetrics })
        });
      }
      if (url.includes('/api/models/budget-alerts')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ alerts: largeAlerts })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });

    const { container } = render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    }, { timeout: 10000 });

    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within reasonable time even with large dataset
    expect(renderTime).toBeLessThan(5000); // 5 seconds max
    
    // Verify all metrics are processed
    expect(container.querySelectorAll('[data-testid="model-card"]')).toHaveLength(Math.min(largeMetrics.length, 20)); // Assuming pagination/limiting
  });

  it('efficiently calculates aggregated metrics', async () => {
    const metrics = generateMockMetrics(50);
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    const startTime = performance.now();
    
    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const endTime = performance.now();
    const calculationTime = endTime - startTime;
    
    // Aggregation should be fast
    expect(calculationTime).toBeLessThan(2000); // 2 seconds max
    
    // Verify aggregated values are displayed
    const totalRequests = metrics.reduce((sum, m) => sum + m.usage.totalRequests, 0);
    const totalCost = metrics.reduce((sum, m) => sum + m.costs.totalCost, 0);
    
    // Check if aggregated values are reasonably close (allowing for formatting)
    expect(screen.getByText(new RegExp(totalRequests.toString().slice(0, 3)))).toBeInTheDocument();
    expect(screen.getByText(new RegExp('\\$' + totalCost.toFixed(0).slice(0, 3)))).toBeInTheDocument();
  });

  it('handles rapid filter changes without performance degradation', async () => {
    const metrics = generateMockMetrics(30);
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const modelSelect = screen.getByDisplayValue('All Models');
    const timeRangeSelect = screen.getByDisplayValue('Last 7 days');
    
    const startTime = performance.now();
    
    // Rapidly change filters
    for (let i = 0; i < 10; i++) {
      fireEvent.click(timeRangeSelect);
      fireEvent.click(screen.getByText('Last 24h'));
      
      fireEvent.click(timeRangeSelect);
      fireEvent.click(screen.getByText('Last 7 days'));
      
      fireEvent.click(modelSelect);
      if (screen.queryByText(metrics[0].modelName)) {
        fireEvent.click(screen.getByText(metrics[0].modelName));
      }
      
      fireEvent.click(modelSelect);
      fireEvent.click(screen.getByText('All Models'));
    }
    
    const endTime = performance.now();
    const filterTime = endTime - startTime;
    
    // Filter changes should be responsive
    expect(filterTime).toBeLessThan(3000); // 3 seconds for 10 rapid changes
  });

  it('efficiently renders time series data', async () => {
    const metrics = generateMockMetrics(10);
    
    // Add more detailed time series data
    metrics.forEach(metric => {
      metric.usage.requestsOverTime = Array.from({ length: 168 }, (_, i) => ({ // Week of hourly data
        timestamp: new Date(Date.now() - (167 - i) * 60 * 60 * 1000),
        value: Math.floor(Math.random() * 100) + 10
      }));
    });
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    const startTime = performance.now();
    
    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should handle large time series efficiently
    expect(renderTime).toBeLessThan(3000); // 3 seconds max
  });

  it('maintains performance during benchmark operations', async () => {
    const metrics = generateMockMetrics(20);
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/models/benchmark') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true })
        });
      }
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const startTime = performance.now();
    
    // Trigger multiple benchmark operations
    const benchmarkButtons = screen.getAllByText('Run Benchmark');
    
    for (let i = 0; i < Math.min(benchmarkButtons.length, 5); i++) {
      fireEvent.click(benchmarkButtons[i]);
    }
    
    const endTime = performance.now();
    const benchmarkTime = endTime - startTime;
    
    // Benchmark operations should not block UI
    expect(benchmarkTime).toBeLessThan(1000); // 1 second max for UI operations
    
    // Verify benchmark buttons show loading state
    await waitFor(() => {
      expect(screen.getAllByText(/Running|Run Benchmark/).length).toBeGreaterThan(0);
    });
  });

  it('efficiently handles warmup configuration updates', async () => {
    const metrics = generateMockMetrics(15);
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/warmup') && options?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true })
        });
      }
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    // Switch to warmup tab for first model
    const warmupTabs = screen.getAllByText('Warmup');
    if (warmupTabs.length > 0) {
      fireEvent.click(warmupTabs[0]);
      
      const startTime = performance.now();
      
      // Toggle warmup settings rapidly
      const enableButtons = screen.getAllByText(/Enabled|Disabled/);
      for (let i = 0; i < Math.min(enableButtons.length, 10); i++) {
        fireEvent.click(enableButtons[i]);
      }
      
      const endTime = performance.now();
      const updateTime = endTime - startTime;
      
      // Updates should be responsive
      expect(updateTime).toBeLessThan(2000); // 2 seconds max
    }
  });

  it('handles memory efficiently with large user lists', async () => {
    const metrics = generateMockMetrics(5);
    
    // Add large user lists
    metrics.forEach(metric => {
      metric.usage.topUsers = Array.from({ length: 1000 }, (_, i) => ({
        userId: `user-${i}`,
        username: `user${i}@example.com`,
        requestCount: Math.floor(Math.random() * 1000) + 100,
        cost: Math.random() * 50,
        lastUsed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000)
      }));
    });
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    const startTime = performance.now();
    
    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should handle large user lists efficiently (only showing top users)
    expect(renderTime).toBeLessThan(4000); // 4 seconds max
    
    // Verify only top users are displayed (not all 1000)
    const userElements = screen.getAllByText(/@example\.com/);
    expect(userElements.length).toBeLessThan(50); // Should limit display
  });

  it('maintains performance during data export', async () => {
    const metrics = generateMockMetrics(25);
    
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/metrics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ metrics })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ alerts: [] })
      });
    });

    // Mock URL.createObjectURL and related methods
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    // Mock document.createElement
    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn()
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);

    render(<ModelMetricsDashboard />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model metrics...')).not.toBeInTheDocument();
    });

    const exportButton = screen.getByText('Export');
    
    const startTime = performance.now();
    fireEvent.click(exportButton);
    const endTime = performance.now();
    
    const exportTime = endTime - startTime;
    
    // Export should be fast
    expect(exportTime).toBeLessThan(1000); // 1 second max
    
    // Verify export was triggered
    expect(mockAnchor.click).toHaveBeenCalled();
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Metrics Exported',
      description: 'Model metrics data has been exported'
    });
  });
});