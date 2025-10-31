/**
 * Tests for IntelligentModelSelector component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import IntelligentModelSelector from '../IntelligentModelSelector';
import { useToast } from '@/hooks/use-toast';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock fetch
global.fetch = vi.fn();

const mockModels = [
  {
    id: 'model-1',
    name: 'GPT-4 Turbo',
    description: 'Advanced language model for complex tasks',
    provider: 'OpenAI',
    type: 'text',
    status: 'local',
    capabilities: ['text-generation', 'reasoning', 'code'],
    recommendation: {
      modelId: 'model-1',
      score: 0.95,
      reasons: [
        {
          type: 'performance',
          weight: 0.4,
          description: 'Excellent performance for complex reasoning tasks',
          evidence: {}
        },
        {
          type: 'capability',
          weight: 0.3,
          description: 'Strong capabilities in text generation and code',
          evidence: {}
        }
      ],
      taskSuitability: {
        taskType: 'general',
        suitabilityScore: 0.9,
        strengths: ['Complex reasoning', 'Code generation', 'Multi-step tasks'],
        limitations: ['Higher cost', 'Slower for simple tasks'],
        alternatives: ['model-2']
      },
      performanceMetrics: {
        latency: {
          p50: 150,
          p95: 300,
          p99: 500,
          average: 180,
          trend: 'stable'
        },
        throughput: {
          requestsPerSecond: 10,
          tokensPerSecond: 50,
          maxConcurrency: 5,
          queueTime: 20
        },
        accuracy: {
          overallScore: 0.92,
          taskSpecificScores: { 'text-generation': 0.95, 'reasoning': 0.90 },
          benchmarkResults: [],
          userRatings: []
        },
        reliability: {
          uptime: 0.99,
          errorRate: 0.01,
          failureTypes: {},
          recoveryTime: 30
        },
        resourceUsage: {
          cpuUsage: 0.7,
          memoryUsage: 0.8,
          gpuUsage: 0.9,
          networkBandwidth: 100,
          storageUsage: 50
        }
      },
      costEstimate: {
        perRequest: 0.002,
        perToken: 0.00001,
        monthly: 50.0,
        currency: 'USD',
        breakdown: {
          compute: 40.0,
          storage: 5.0,
          network: 3.0,
          licensing: 2.0,
          other: 0.0
        },
        comparison: [
          {
            modelId: 'model-2',
            costDifference: 0.001,
            percentageDifference: 50.0
          }
        ]
      }
    },
    performanceMetrics: {
      latency: {
        p50: 150,
        p95: 300,
        p99: 500,
        average: 180,
        trend: 'stable'
      },
      throughput: {
        requestsPerSecond: 10,
        tokensPerSecond: 50,
        maxConcurrency: 5,
        queueTime: 20
      },
      accuracy: {
        overallScore: 0.92,
        taskSpecificScores: { 'text-generation': 0.95 },
        benchmarkResults: [],
        userRatings: []
      },
      reliability: {
        uptime: 0.99,
        errorRate: 0.01,
        failureTypes: {},
        recoveryTime: 30
      },
      resourceUsage: {
        cpuUsage: 0.7,
        memoryUsage: 0.8,
        networkBandwidth: 100,
        storageUsage: 50
      }
    },
    usageAnalytics: {
      popularityScore: 0.9,
      userRating: 4.5,
      successRate: 0.95,
      recentUsage: 1000,
      trendDirection: 'up'
    }
  },
  {
    id: 'model-2',
    name: 'Claude 3 Sonnet',
    description: 'Balanced model for general tasks',
    provider: 'Anthropic',
    type: 'text',
    status: 'available',
    capabilities: ['text-generation', 'analysis'],
    recommendation: {
      modelId: 'model-2',
      score: 0.85,
      reasons: [
        {
          type: 'cost',
          weight: 0.4,
          description: 'Cost-effective for general tasks',
          evidence: {}
        }
      ],
      taskSuitability: {
        taskType: 'general',
        suitabilityScore: 0.8,
        strengths: ['Cost-effective', 'Good general performance'],
        limitations: ['Less capable for complex reasoning'],
        alternatives: ['model-1']
      },
      performanceMetrics: {
        latency: {
          p50: 100,
          p95: 200,
          p99: 350,
          average: 120,
          trend: 'improving'
        },
        throughput: {
          requestsPerSecond: 15,
          tokensPerSecond: 60,
          maxConcurrency: 8,
          queueTime: 15
        },
        accuracy: {
          overallScore: 0.88,
          taskSpecificScores: { 'text-generation': 0.90 },
          benchmarkResults: [],
          userRatings: []
        },
        reliability: {
          uptime: 0.98,
          errorRate: 0.02,
          failureTypes: {},
          recoveryTime: 45
        },
        resourceUsage: {
          cpuUsage: 0.5,
          memoryUsage: 0.6,
          networkBandwidth: 80,
          storageUsage: 30
        }
      },
      costEstimate: {
        perRequest: 0.001,
        perToken: 0.000005,
        monthly: 25.0,
        currency: 'USD',
        breakdown: {
          compute: 20.0,
          storage: 2.5,
          network: 1.5,
          licensing: 1.0,
          other: 0.0
        },
        comparison: []
      }
    },
    usageAnalytics: {
      popularityScore: 0.7,
      userRating: 4.2,
      successRate: 0.92,
      recentUsage: 800,
      trendDirection: 'stable'
    }
  }
];

const mockApiResponse = {
  models: mockModels,
  recommendations: mockModels.map(m => m.recommendation).filter(Boolean)
};

describe('IntelligentModelSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockApiResponse)
    });
  });

  it('renders loading state initially', () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    expect(screen.getByText('Analyzing models for your task...')).toBeInTheDocument();
    expect(screen.getByText('Generating intelligent recommendations')).toBeInTheDocument();
  });

  it('renders models after loading', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument();
      expect(screen.getByText('Claude 3 Sonnet')).toBeInTheDocument();
    });
  });

  it('displays recommendation scores', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      expect(screen.getByText('95% - Excellent')).toBeInTheDocument();
      expect(screen.getByText('85% - Excellent')).toBeInTheDocument();
    });
  });

  it('shows top pick badge for highly recommended models', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      expect(screen.getByText('Top Pick')).toBeInTheDocument();
    });
  });

  it('calls onModelSelect when a model is selected', async () => {
    const onModelSelect = vi.fn();
    render(<IntelligentModelSelector onModelSelect={onModelSelect} />);
    
    await waitFor(() => {
      const selectButton = screen.getAllByText('Select')[0];
      fireEvent.click(selectButton);
    });

    expect(onModelSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'model-1' }),
      expect.objectContaining({ modelId: 'model-1' })
    );
  });

  it('filters models by search query', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search models...');
      fireEvent.change(searchInput, { target: { value: 'GPT' } });
    });

    await waitFor(() => {
      expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument();
      expect(screen.queryByText('Claude 3 Sonnet')).not.toBeInTheDocument();
    });
  });

  it('sorts models by different criteria', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const sortSelect = screen.getByDisplayValue('Recommendation');
      fireEvent.click(sortSelect);
    });

    const costOption = screen.getByText('Cost');
    fireEvent.click(costOption);

    // Models should be reordered by cost
    await waitFor(() => {
      const modelCards = screen.getAllByRole('button', { name: /Select/ });
      expect(modelCards).toHaveLength(2);
    });
  });

  it('filters models by category', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const filterSelect = screen.getByDisplayValue('All Models');
      fireEvent.click(filterSelect);
    });

    const localOption = screen.getByText('Local Only');
    fireEvent.click(localOption);

    await waitFor(() => {
      expect(screen.getByText('GPT-4 Turbo')).toBeInTheDocument();
      expect(screen.queryByText('Claude 3 Sonnet')).not.toBeInTheDocument();
    });
  });

  it('handles model comparison selection', async () => {
    const onCompareModels = vi.fn();
    render(
      <IntelligentModelSelector 
        onModelSelect={vi.fn()} 
        onCompareModels={onCompareModels}
      />
    );
    
    await waitFor(() => {
      const compareButtons = screen.getAllByText('Compare');
      fireEvent.click(compareButtons[0]);
      fireEvent.click(compareButtons[1]);
    });

    const compareModelsButton = screen.getByText('Compare Models');
    fireEvent.click(compareModelsButton);

    expect(onCompareModels).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ id: 'model-1' }),
        expect.objectContaining({ id: 'model-2' })
      ])
    );
  });

  it('displays performance metrics in tabs', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const performanceTab = screen.getAllByText('Performance')[0];
      fireEvent.click(performanceTab);
    });

    expect(screen.getByText('180ms')).toBeInTheDocument(); // Average latency
    expect(screen.getByText('10.0')).toBeInTheDocument(); // Requests per second
  });

  it('displays cost analysis in tabs', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const costTab = screen.getAllByText('Cost')[0];
      fireEvent.click(costTab);
    });

    expect(screen.getByText('$0.0020')).toBeInTheDocument(); // Per request cost
    expect(screen.getByText('$50.00')).toBeInTheDocument(); // Monthly estimate
  });

  it('shows recommendation reasons', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const recommendationTab = screen.getAllByText('Recommendation')[0];
      fireEvent.click(recommendationTab);
    });

    expect(screen.getByText('Excellent performance for complex reasoning tasks')).toBeInTheDocument();
    expect(screen.getByText('Strong capabilities in text generation and code')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as any).mockRejectedValue(new Error('API Error'));
    
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load model recommendations',
        variant: 'destructive'
      });
    });
  });

  it('refreshes models when refresh button is clicked', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const refreshButton = screen.getByRole('button', { name: /Scan & Refresh/ });
      fireEvent.click(refreshButton);
    });

    expect(global.fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
  });

  it('limits comparison selection to 4 models', async () => {
    // Add more models to test the limit
    const manyModels = [...mockModels, ...mockModels, ...mockModels];
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        models: manyModels,
        recommendations: manyModels.map(m => m.recommendation).filter(Boolean)
      })
    });

    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const compareButtons = screen.getAllByText('Compare');
      // Try to select 5 models
      for (let i = 0; i < 5; i++) {
        fireEvent.click(compareButtons[i]);
      }
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Comparison Limit',
      description: 'You can compare up to 4 models at once',
      variant: 'destructive'
    });
  });

  it('clears filters when clear filters button is clicked', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      // Set some filters first
      const searchInput = screen.getByPlaceholderText('Search models...');
      fireEvent.change(searchInput, { target: { value: 'GPT' } });
      
      const clearButton = screen.getByText('Clear All');
      fireEvent.click(clearButton);
    });

    const searchInput = screen.getByPlaceholderText('Search models...');
    expect(searchInput).toHaveValue('');
  });

  it('displays task suitability information', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      const recommendationTab = screen.getAllByText('Recommendation')[0];
      fireEvent.click(recommendationTab);
    });

    expect(screen.getByText('Complex reasoning')).toBeInTheDocument();
    expect(screen.getByText('Code generation')).toBeInTheDocument();
    expect(screen.getByText('Higher cost')).toBeInTheDocument();
  });

  it('shows usage analytics in overview tab', async () => {
    render(<IntelligentModelSelector onModelSelect={vi.fn()} />);
    
    await waitFor(() => {
      expect(screen.getByText('Popularity: 0.9')).toBeInTheDocument();
      expect(screen.getByText('Rating: 4.5/5')).toBeInTheDocument();
    });
  });
});