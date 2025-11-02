/**
 * Model Provider Management Hub Integration Tests
 * Tests for the main orchestrator component
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ModelProviderManagementHub from '../ModelProviderManagementHub';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock fetch globally
global.fetch = vi.fn();

// Mock child components to avoid complex dependencies
vi.mock('../EnhancedModelSelector', () => ({
  default: ({ onModelChange }: any) => (
    <div data-testid="enhanced-model-selector">
      Enhanced Model Selector
      <button onClick={() => onModelChange?.({ id: 'test-model', name: 'Test Model' })}>
        Select Model
      </button>
    </div>
  )
}));

vi.mock('../ModelMetricsDashboard', () => ({
  default: () => <div data-testid="model-metrics-dashboard">Model Metrics Dashboard</div>
}));

vi.mock('../CostTrackingSystem', () => ({
  default: () => <div data-testid="cost-tracking-system">Cost Tracking System</div>
}));

vi.mock('../providers/ProviderConfigInterface', () => ({
  ProviderConfigInterface: () => <div data-testid="provider-config-interface">Provider Config Interface</div>
}));

vi.mock('../providers/FallbackConfigInterface', () => ({
  FallbackConfigInterface: () => <div data-testid="fallback-config-interface">Fallback Config Interface</div>
}));

vi.mock('../ModelComparisonInterface', () => ({
  default: () => <div data-testid="model-comparison-interface">Model Comparison Interface</div>
}));

vi.mock('../IntelligentModelSelector', () => ({
  default: () => <div data-testid="intelligent-model-selector">Intelligent Model Selector</div>
}));

describe('ModelProviderManagementHub', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock successful API responses
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/models/system-status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: {
              models: { total: 10, active: 8, healthy: 7, issues: 1 },
              providers: { total: 5, connected: 4, healthy: 4, issues: 0 },
              performance: { averageLatency: 150, successRate: 0.98, requestsPerMinute: 120, errorRate: 0.02 },
              costs: { totalSpend: 45.67, budgetUtilization: 0.65, projectedSpend: 70.23, topProvider: 'OpenAI' },
              fallback: { totalFailovers: 3, successRate: 0.95, averageRecoveryTime: 250, activeChains: 2 }
            }
          })
        });
      }
      
      if (url.includes('/api/models/recent-activity')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            activities: [
              {
                id: '1',
                type: 'model_selected',
                title: 'Model Selected',
                description: 'GPT-4 selected for text generation',
                timestamp: new Date(),
                severity: 'info'
              }
            ]
          })
        });
      }
      
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });

  it('renders the main hub interface', async () => {
    render(<ModelProviderManagementHub />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    // Check main title
    expect(screen.getByText('Model & Provider Management Hub')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive management of AI models, providers, and system performance')).toBeInTheDocument();
  });

  it('displays system status metrics', async () => {
    render(<ModelProviderManagementHub />);
    
    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument(); // Active models
      expect(screen.getByText('4')).toBeInTheDocument(); // Connected providers
      expect(screen.getByText('98.0%')).toBeInTheDocument(); // Success rate
      expect(screen.getByText('$45.67')).toBeInTheDocument(); // Total spend
      expect(screen.getByText('3')).toBeInTheDocument(); // Failovers
    });
  });

  it('shows recent activity', async () => {
    render(<ModelProviderManagementHub />);
    
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Model Selected')).toBeInTheDocument();
      expect(screen.getByText('GPT-4 selected for text generation')).toBeInTheDocument();
    });
  });

  it('handles tab navigation', async () => {
    render(<ModelProviderManagementHub />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    // Check that all tab buttons exist by role
    const tabButtons = screen.getAllByRole('tab');
    expect(tabButtons).toHaveLength(6);
    
    // Check default tab (overview) content
    expect(screen.getByText('Intelligent Model Selection')).toBeInTheDocument();
    expect(screen.getByTestId('intelligent-model-selector')).toBeInTheDocument();
    
    // Test that tabs are clickable by finding specific tab buttons
    const modelsTab = tabButtons.find(tab => tab.textContent === 'Models');
    const providersTab = tabButtons.find(tab => tab.textContent === 'Providers');
    const metricsTab = tabButtons.find(tab => tab.textContent === 'Metrics');
    const costsTab = tabButtons.find(tab => tab.textContent === 'Costs');
    const fallbackTab = tabButtons.find(tab => tab.textContent === 'Fallback');
    const overviewTab = tabButtons.find(tab => tab.textContent === 'Overview');
    
    expect(modelsTab).toBeInTheDocument();
    expect(providersTab).toBeInTheDocument();
    expect(metricsTab).toBeInTheDocument();
    expect(costsTab).toBeInTheDocument();
    expect(fallbackTab).toBeInTheDocument();
    expect(overviewTab).toBeInTheDocument();
    
    // Test clicking tabs
    if (modelsTab) fireEvent.click(modelsTab);
    if (providersTab) fireEvent.click(providersTab);
    if (metricsTab) fireEvent.click(metricsTab);
    if (costsTab) fireEvent.click(costsTab);
    if (fallbackTab) fireEvent.click(fallbackTab);
    
    // Switch back to overview
    if (overviewTab) fireEvent.click(overviewTab);
    expect(screen.getByText('Intelligent Model Selection')).toBeInTheDocument();
  });

  it('handles refresh functionality', async () => {
    render(<ModelProviderManagementHub />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should show refreshing state
    expect(screen.getByText('Refreshing...')).toBeInTheDocument();
    
    // Wait for refresh to complete
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (global.fetch as any).mockImplementationOnce(() => 
      Promise.resolve({
        ok: false,
        status: 500
      })
    );
    
    render(<ModelProviderManagementHub />);
    
    // Should still render the interface even with API errors
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    expect(screen.getByText('Model & Provider Management Hub')).toBeInTheDocument();
  });

  it('displays model comparison interface in overview', async () => {
    render(<ModelProviderManagementHub />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    expect(screen.getByText('Model Performance Comparison')).toBeInTheDocument();
    expect(screen.getByTestId('model-comparison-interface')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(<ModelProviderManagementHub />);
    
    expect(screen.getByText('Loading model and provider management...')).toBeInTheDocument();
  });

  it('applies custom className', async () => {
    const { container } = render(<ModelProviderManagementHub className="custom-class" />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading model and provider management...')).not.toBeInTheDocument();
    });
    
    expect(container.firstChild).toHaveClass('custom-class');
  });
});