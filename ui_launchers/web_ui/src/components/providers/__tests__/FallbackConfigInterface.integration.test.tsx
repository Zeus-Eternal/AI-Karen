/**
 * Integration tests for FallbackConfigInterface component
 * Testing failover scenarios and recovery procedures
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import FallbackConfigInterface from '../FallbackConfigInterface';
import { useToast } from '@/hooks/use-toast';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock fetch
global.fetch = vi.fn();

const mockConfigs = [
  {
    id: 'config-1',
    name: 'Primary Text Generation',
    enabled: true,
    chains: [
      {
        id: 'chain-1',
        name: 'High Performance Chain',
        priority: 1,
        providers: [
          {
            providerId: 'openai-1',
            modelId: 'gpt-4',
            weight: 1.0,
            maxRetries: 3,
            timeout: 30000,
            healthThreshold: 0.9
          },
          {
            providerId: 'anthropic-1',
            modelId: 'claude-3-opus',
            weight: 0.8,
            maxRetries: 2,
            timeout: 25000,
            healthThreshold: 0.8
          },
          {
            providerId: 'ollama-1',
            modelId: 'llama-2',
            weight: 0.6,
            maxRetries: 1,
            timeout: 60000,
            healthThreshold: 0.7
          }
        ],
        conditions: [
          {
            type: 'error',
            operator: 'eq',
            value: 'timeout',
            action: 'fallback'
          },
          {
            type: 'latency',
            operator: 'gt',
            value: 5000,
            action: 'fallback'
          }
        ]
      }
    ],
    healthChecks: [
      {
        id: 'health-1',
        providerId: 'openai-1',
        type: 'ping',
        interval: 30000,
        timeout: 5000,
        retries: 3,
        healthyThreshold: 2,
        unhealthyThreshold: 3
      },
      {
        id: 'health-2',
        providerId: 'anthropic-1',
        type: 'request',
        interval: 60000,
        timeout: 10000,
        retries: 2,
        healthyThreshold: 2,
        unhealthyThreshold: 2
      }
    ],
    failoverRules: [
      {
        id: 'rule-1',
        name: 'High Error Rate Failover',
        trigger: {
          type: 'error_rate',
          threshold: 0.1,
          duration: 60000,
          conditions: ['error_rate > 0.1']
        },
        action: {
          type: 'switch',
          target: 'anthropic-1',
          parameters: {}
        },
        cooldown: 300000,
        maxFailovers: 5
      }
    ],
    recovery: {
      autoRecovery: true,
      recoveryDelay: 120000,
      healthCheckInterval: 30000,
      recoveryThreshold: 0.9,
      maxRecoveryAttempts: 3
    },
    analytics: {
      totalFailovers: 15,
      failoversByProvider: {
        'openai-1': 8,
        'anthropic-1': 5,
        'ollama-1': 2
      },
      averageRecoveryTime: 2500,
      successRate: 0.95,
      impactMetrics: {
        requestsAffected: 1250,
        downtimeAvoided: 45000,
        costImpact: 125.50,
        userImpact: 85
      },
      recentEvents: []
    }
  }
];

const mockAnalytics = {
  totalFailovers: 15,
  failoversByProvider: {
    'openai-1': 8,
    'anthropic-1': 5,
    'ollama-1': 2
  },
  averageRecoveryTime: 2500,
  successRate: 0.95,
  impactMetrics: {
    requestsAffected: 1250,
    downtimeAvoided: 45000,
    costImpact: 125.50,
    userImpact: 85
  },
  recentEvents: []
};

const mockEvents = [
  {
    id: 'event-1',
    timestamp: new Date(Date.now() - 60000),
    type: 'failover',
    providerId: 'openai-1',
    reason: 'High latency detected',
    duration: 2500,
    impact: 'Switched to anthropic-1',
    resolved: true
  },
  {
    id: 'event-2',
    timestamp: new Date(Date.now() - 120000),
    type: 'recovery',
    providerId: 'openai-1',
    reason: 'Health check passed',
    duration: 1500,
    impact: 'Restored to primary provider',
    resolved: true
  },
  {
    id: 'event-3',
    timestamp: new Date(Date.now() - 300000),
    type: 'health_check',
    providerId: 'anthropic-1',
    reason: 'Routine health check',
    duration: 500,
    impact: 'Provider healthy',
    resolved: true
  }
];

describe('FallbackConfigInterface Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/fallback/configs') && !options?.method) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ configs: mockConfigs })
        });
      }
      if (url.includes('/api/fallback/analytics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ analytics: mockAnalytics })
        });
      }
      if (url.includes('/api/fallback/events')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ events: mockEvents })
        });
      }
      if (url.includes('/api/fallback/test') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            chainId: JSON.parse(options.body).chainId,
            success: true,
            failoverTime: 150,
            recoveryTime: 2500,
            details: 'Failover test completed successfully. All providers responded within acceptable limits.'
          })
        });
      }
      if (url.includes('/toggle') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });

  it('loads and displays fallback configurations', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Primary Text Generation')).toBeInTheDocument();
    });

    expect(screen.getByText('1 configuration defined')).toBeInTheDocument();
    expect(screen.getByText('1 chain')).toBeInTheDocument();
    expect(screen.getByText('2 health checks')).toBeInTheDocument();
  });

  it('displays analytics overview correctly', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument(); // Total failovers
      expect(screen.getByText('95.0%')).toBeInTheDocument(); // Success rate
      expect(screen.getByText('2500ms')).toBeInTheDocument(); // Avg recovery time
      expect(screen.getByText('1250')).toBeInTheDocument(); // Requests saved
    });
  });

  it('shows fallback chain configuration details', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    expect(screen.getByText('High Performance Chain')).toBeInTheDocument();
    expect(screen.getByText('Priority 1')).toBeInTheDocument();
    expect(screen.getByText('openai-1')).toBeInTheDocument();
    expect(screen.getByText('anthropic-1')).toBeInTheDocument();
    expect(screen.getByText('ollama-1')).toBeInTheDocument();
  });

  it('tests fallback chain successfully', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const testButton = screen.getByText('Test');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText('Test Passed')).toBeInTheDocument();
      expect(screen.getByText('Failover: 150ms | Recovery: 2500ms')).toBeInTheDocument();
      expect(screen.getByText('Failover test completed successfully. All providers responded within acceptable limits.')).toBeInTheDocument();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Test Complete',
      description: 'Fallback test successful',
      variant: 'default'
    });
  });

  it('handles test failure scenarios', async () => {
    // Mock failed test response
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/fallback/test') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            chainId: JSON.parse(options.body).chainId,
            success: false,
            failoverTime: 5000,
            recoveryTime: 0,
            details: 'Primary provider failed, secondary provider also unavailable'
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ configs: mockConfigs })
      });
    });

    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const testButton = screen.getByText('Test');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText('Test Failed')).toBeInTheDocument();
      expect(screen.getByText('Primary provider failed, secondary provider also unavailable')).toBeInTheDocument();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Test Complete',
      description: 'Fallback test failed',
      variant: 'destructive'
    });
  });

  it('toggles configuration enabled state', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Primary Text Generation')).toBeInTheDocument();
    });

    // Find and click the switch (it should be checked initially)
    const toggleSwitch = screen.getByRole('switch');
    expect(toggleSwitch).toBeChecked();
    
    fireEvent.click(toggleSwitch);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Configuration Disabled',
        description: 'Fallback configuration has been disabled'
      });
    });
  });

  it('displays health check configuration', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const healthTab = screen.getByText('Health Checks');
    fireEvent.click(healthTab);

    expect(screen.getByText('Provider: openai-1')).toBeInTheDocument();
    expect(screen.getByText('Provider: anthropic-1')).toBeInTheDocument();
    expect(screen.getByText('ping')).toBeInTheDocument();
    expect(screen.getByText('request')).toBeInTheDocument();
    expect(screen.getByText('Interval: 30000ms')).toBeInTheDocument();
    expect(screen.getByText('Timeout: 5000ms')).toBeInTheDocument();
  });

  it('displays failover rules', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const rulesTab = screen.getByText('Failover Rules');
    fireEvent.click(rulesTab);

    expect(screen.getByText('High Error Rate Failover')).toBeInTheDocument();
    expect(screen.getByText('error_rate')).toBeInTheDocument();
    expect(screen.getByText('Threshold: 0.1')).toBeInTheDocument();
    expect(screen.getByText('Duration: 60000ms')).toBeInTheDocument();
    expect(screen.getByText('Action: switch')).toBeInTheDocument();
  });

  it('displays recent events with proper formatting', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const eventsTab = screen.getByText('Recent Events');
    fireEvent.click(eventsTab);

    expect(screen.getByText('Failover')).toBeInTheDocument();
    expect(screen.getByText('Recovery')).toBeInTheDocument();
    expect(screen.getByText('Health check')).toBeInTheDocument();
    
    expect(screen.getByText('Provider: openai-1')).toBeInTheDocument();
    expect(screen.getByText('Reason: High latency detected')).toBeInTheDocument();
    expect(screen.getByText('Duration: 2500ms')).toBeInTheDocument();
    expect(screen.getByText('Impact: Switched to anthropic-1')).toBeInTheDocument();
  });

  it('opens chain configuration dialog', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const addChainButton = screen.getByText('Add Chain');
    fireEvent.click(addChainButton);

    expect(screen.getByText('Create Fallback Chain')).toBeInTheDocument();
    expect(screen.getByText('Configure provider fallback order and conditions')).toBeInTheDocument();
    expect(screen.getByLabelText('Chain Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority')).toBeInTheDocument();
  });

  it('creates new fallback chain', async () => {
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/fallback/configs/config-1') && options?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            ...mockConfigs[0],
            chains: [
              ...mockConfigs[0].chains,
              {
                id: 'chain-2',
                name: 'Test Chain',
                priority: 2,
                providers: [
                  {
                    providerId: 'test-provider',
                    modelId: 'test-model',
                    weight: 1.0,
                    maxRetries: 3,
                    timeout: 30000,
                    healthThreshold: 0.8
                  }
                ],
                conditions: []
              }
            ]
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ configs: mockConfigs })
      });
    });

    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const addChainButton = screen.getByText('Add Chain');
    fireEvent.click(addChainButton);

    // Fill in chain details
    const nameInput = screen.getByLabelText('Chain Name');
    fireEvent.change(nameInput, { target: { value: 'Test Chain' } });

    const priorityInput = screen.getByLabelText('Priority');
    fireEvent.change(priorityInput, { target: { value: '2' } });

    // Add a provider
    const addProviderButton = screen.getByText('Add Provider');
    fireEvent.click(addProviderButton);

    // Fill provider details
    const providerIdInput = screen.getByPlaceholderText('openai-1');
    fireEvent.change(providerIdInput, { target: { value: 'test-provider' } });

    const modelIdInput = screen.getByPlaceholderText('gpt-4');
    fireEvent.change(modelIdInput, { target: { value: 'test-model' } });

    // Save the chain
    const saveButton = screen.getByText('Save Chain');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Configuration Saved',
        description: 'Fallback configuration "Primary Text Generation" has been saved'
      });
    });
  });

  it('validates chain configuration before saving', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const addChainButton = screen.getByText('Add Chain');
    fireEvent.click(addChainButton);

    // Try to save without filling required fields
    const saveButton = screen.getByText('Save Chain');
    expect(saveButton).toBeDisabled();

    // Fill name but no providers
    const nameInput = screen.getByLabelText('Chain Name');
    fireEvent.change(nameInput, { target: { value: 'Test Chain' } });

    expect(saveButton).toBeDisabled();
  });

  it('reorders providers in chain configuration', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    // Edit existing chain
    const editButton = screen.getAllByLabelText('')[0]; // Edit button (no accessible label)
    fireEvent.click(editButton);

    // Should show existing providers
    expect(screen.getByDisplayValue('openai-1')).toBeInTheDocument();
    expect(screen.getByDisplayValue('anthropic-1')).toBeInTheDocument();

    // Test reordering (move second provider up)
    const moveUpButtons = screen.getAllByLabelText(''); // Arrow up buttons
    const secondProviderMoveUp = moveUpButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-arrow-up')
    );
    
    if (secondProviderMoveUp) {
      fireEvent.click(secondProviderMoveUp);
    }

    // Verify the order changed in the form
    const providerInputs = screen.getAllByPlaceholderText('openai-1');
    expect(providerInputs[0]).toHaveValue('anthropic-1');
    expect(providerInputs[1]).toHaveValue('openai-1');
  });

  it('removes providers from chain configuration', async () => {
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const addChainButton = screen.getByText('Add Chain');
    fireEvent.click(addChainButton);

    // Add two providers
    const addProviderButton = screen.getByText('Add Provider');
    fireEvent.click(addProviderButton);
    fireEvent.click(addProviderButton);

    // Should have 2 providers
    expect(screen.getAllByText('Provider 1')).toHaveLength(1);
    expect(screen.getAllByText('Provider 2')).toHaveLength(1);

    // Remove first provider
    const removeButtons = screen.getAllByLabelText(''); // Trash buttons
    const trashButton = removeButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-trash-2')
    );
    
    if (trashButton) {
      fireEvent.click(trashButton);
    }

    // Should have 1 provider left
    expect(screen.getAllByText(/Provider \d/)).toHaveLength(1);
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));
    
    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load fallback configurations',
        variant: 'destructive'
      });
    });
  });

  it('deletes configuration with confirmation', async () => {
    // Mock window.confirm
    vi.stubGlobal('confirm', vi.fn(() => true));
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/fallback/configs/config-1') && options?.method === 'DELETE') {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ configs: mockConfigs })
      });
    });

    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Primary Text Generation')).toBeInTheDocument();
    });

    // Click delete button
    const deleteButton = screen.getByLabelText(''); // Trash button
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Configuration Deleted',
        description: 'Fallback configuration has been deleted'
      });
    });

    expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this fallback configuration?');
  });

  it('shows loading state during test execution', async () => {
    // Mock slow test response
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/fallback/test')) {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: () => Promise.resolve({
                chainId: JSON.parse(options.body).chainId,
                success: true,
                failoverTime: 150,
                recoveryTime: 2500,
                details: 'Test completed'
              })
            });
          }, 1000);
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ configs: mockConfigs })
      });
    });

    render(<FallbackConfigInterface />);
    
    await waitFor(() => {
      const configCard = screen.getByText('Primary Text Generation');
      fireEvent.click(configCard);
    });

    const testButton = screen.getByText('Test');
    fireEvent.click(testButton);

    // Should show loading state
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(testButton).toBeDisabled();

    // Wait for test to complete
    await waitFor(() => {
      expect(screen.getByText('Test Passed')).toBeInTheDocument();
    }, { timeout: 2000 });
  });
});