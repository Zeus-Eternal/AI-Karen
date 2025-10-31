/**
 * Integration tests for ProviderConfigInterface component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ProviderConfigInterface from '../ProviderConfigInterface';
import { useToast } from '@/hooks/use-toast';

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

// Mock fetch
global.fetch = vi.fn();

const mockProviders = [
  {
    id: 'openai-1',
    name: 'OpenAI Production',
    type: 'openai',
    enabled: true,
    configuration: {
      apiKey: 'sk-test123',
      organization: 'org-123',
      baseUrl: 'https://api.openai.com/v1',
      timeout: 30
    },
    credentials: {
      apiKey: 'sk-test123'
    },
    metadata: {
      version: '1.0.0',
      description: 'OpenAI GPT models and APIs',
      tags: ['cloud']
    },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    id: 'ollama-1',
    name: 'Local Ollama',
    type: 'ollama',
    enabled: false,
    configuration: {
      host: 'localhost',
      port: 11434,
      ssl: false
    },
    credentials: {},
    metadata: {
      version: '1.0.0',
      description: 'Local Ollama server',
      tags: ['local']
    },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  }
];

const mockHealth = {
  'openai-1': {
    status: 'healthy' as const,
    lastCheck: new Date(),
    responseTime: 150,
    uptime: 0.99,
    errorRate: 0.01,
    issues: [],
    metrics: {
      requestCount: 1000,
      successRate: 0.99,
      averageLatency: 150,
      errorCount: 10,
      throughput: 10.5,
      concurrentRequests: 5
    }
  },
  'ollama-1': {
    status: 'unhealthy' as const,
    lastCheck: new Date(),
    responseTime: 0,
    uptime: 0,
    errorRate: 1,
    issues: [
      {
        id: 'conn-1',
        severity: 'critical' as const,
        message: 'Connection refused',
        details: 'Unable to connect to localhost:11434',
        timestamp: new Date(),
        resolved: false
      }
    ],
    metrics: {
      requestCount: 0,
      successRate: 0,
      averageLatency: 0,
      errorCount: 5,
      throughput: 0,
      concurrentRequests: 0
    }
  }
};

describe('ProviderConfigInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/providers/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ health: mockHealth })
        });
      }
      if (url.includes('/api/providers')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ providers: mockProviders })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  });

  it('renders loading state initially', () => {
    render(<ProviderConfigInterface />);
    
    expect(screen.getByText('Loading provider configurations...')).toBeInTheDocument();
  });

  it('loads and displays providers', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('OpenAI Production')).toBeInTheDocument();
      expect(screen.getByText('Local Ollama')).toBeInTheDocument();
    });
  });

  it('displays provider health status', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Healthy')).toBeInTheDocument();
      expect(screen.getByText('Unhealthy')).toBeInTheDocument();
    });
  });

  it('shows provider metrics', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      // Check for response time and success rate
      expect(screen.getByText('150ms')).toBeInTheDocument();
      expect(screen.getByText('99.0%')).toBeInTheDocument();
    });
  });

  it('opens configuration form when provider is clicked', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const providerCard = screen.getByText('OpenAI Production');
      fireEvent.click(providerCard);
    });

    expect(screen.getByText('Edit OpenAI Provider')).toBeInTheDocument();
    expect(screen.getByDisplayValue('OpenAI Production')).toBeInTheDocument();
  });

  it('opens new provider form when add button is clicked', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    expect(screen.getByText('Add OpenAI Provider')).toBeInTheDocument();
    expect(screen.getByDisplayValue('OpenAI Provider')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Clear the API key field
    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: '' } });

    // Try to save
    const saveButton = screen.getByText('Save Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('API key is required')).toBeInTheDocument();
    });
  });

  it('validates API key format for OpenAI', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Enter invalid API key
    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'invalid-key' } });

    // Try to save
    const saveButton = screen.getByText('Save Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('API key must start with sk-')).toBeInTheDocument();
    });
  });

  it('validates number fields', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Ollama');
      fireEvent.click(addButton);
    });

    // Enter invalid port
    const portInput = screen.getByLabelText(/Port/);
    fireEvent.change(portInput, { target: { value: 'invalid' } });

    // Try to save
    const saveButton = screen.getByText('Save Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Port must be a number')).toBeInTheDocument();
    });
  });

  it('validates number ranges', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Ollama');
      fireEvent.click(addButton);
    });

    // Enter port out of range
    const portInput = screen.getByLabelText(/Port/);
    fireEvent.change(portInput, { target: { value: '70000' } });

    // Try to save
    const saveButton = screen.getByText('Save Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Port must be at most 65535')).toBeInTheDocument();
    });
  });

  it('tests provider connection', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/providers/test')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'Connection successful' })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ providers: mockProviders })
      });
    });

    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Fill in valid API key
    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

    // Test connection
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText('Connection successful')).toBeInTheDocument();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Test Successful',
      description: 'Provider connection is working correctly'
    });
  });

  it('handles test connection failure', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/providers/test')) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ message: 'Invalid API key' })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ providers: mockProviders })
      });
    });

    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Fill in invalid API key
    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'sk-invalid' } });

    // Test connection
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid API key')).toBeInTheDocument();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Test Failed',
      description: 'Invalid API key',
      variant: 'destructive'
    });
  });

  it('saves new provider', async () => {
    const onProviderSaved = vi.fn();
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/providers') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            id: 'new-provider',
            ...JSON.parse(options.body)
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ providers: mockProviders })
      });
    });

    render(<ProviderConfigInterface onProviderSaved={onProviderSaved} />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Fill in form
    const nameInput = screen.getByLabelText(/Provider Name/);
    fireEvent.change(nameInput, { target: { value: 'Test Provider' } });

    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: 'sk-test123' } });

    // Save
    const saveButton = screen.getByText('Save Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(onProviderSaved).toHaveBeenCalled();
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Provider Saved',
      description: expect.stringContaining('has been saved successfully')
    });
  });

  it('updates existing provider', async () => {
    const onProviderSaved = vi.fn();
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/providers/openai-1') && options?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            ...mockProviders[0],
            ...JSON.parse(options.body)
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ providers: mockProviders })
      });
    });

    render(<ProviderConfigInterface onProviderSaved={onProviderSaved} />);
    
    await waitFor(() => {
      const providerCard = screen.getByText('OpenAI Production');
      fireEvent.click(providerCard);
    });

    // Update name
    const nameInput = screen.getByDisplayValue('OpenAI Production');
    fireEvent.change(nameInput, { target: { value: 'Updated OpenAI' } });

    // Save
    const saveButton = screen.getByText('Update Provider');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(onProviderSaved).toHaveBeenCalled();
    });
  });

  it('deletes provider', async () => {
    const onProviderDeleted = vi.fn();
    
    // Mock window.confirm
    vi.stubGlobal('confirm', vi.fn(() => true));
    
    (global.fetch as any).mockImplementation((url: string, options: any) => {
      if (url.includes('/api/providers/openai-1') && options?.method === 'DELETE') {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ providers: mockProviders })
      });
    });

    render(<ProviderConfigInterface onProviderDeleted={onProviderDeleted} />);
    
    await waitFor(() => {
      const providerCard = screen.getByText('OpenAI Production');
      fireEvent.click(providerCard);
    });

    // Delete
    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(onProviderDeleted).toHaveBeenCalledWith('openai-1');
    });

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Provider Deleted',
      description: 'OpenAI Production has been deleted'
    });
  });

  it('toggles sensitive field visibility', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    const apiKeyInput = screen.getByLabelText(/API Key/) as HTMLInputElement;
    expect(apiKeyInput.type).toBe('password');

    // Toggle visibility
    const toggleButton = screen.getByRole('button', { name: '' }); // Eye icon button
    fireEvent.click(toggleButton);

    expect(apiKeyInput.type).toBe('text');
  });

  it('displays supported models and capabilities', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Switch to models tab
    const modelsTab = screen.getByText('Supported Models');
    fireEvent.click(modelsTab);

    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
    expect(screen.getByText('text-embedding-ada-002')).toBeInTheDocument();

    expect(screen.getByText('text-generation')).toBeInTheDocument();
    expect(screen.getByText('embedding')).toBeInTheDocument();
    expect(screen.getByText('chat')).toBeInTheDocument();
  });

  it('displays health metrics in health tab', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const providerCard = screen.getByText('OpenAI Production');
      fireEvent.click(providerCard);
    });

    // Switch to health tab
    const healthTab = screen.getByText('Health & Metrics');
    fireEvent.click(healthTab);

    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
    expect(screen.getByText('99.00%')).toBeInTheDocument();
    expect(screen.getByText('1.00%')).toBeInTheDocument();
  });

  it('displays health issues for unhealthy providers', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const providerCard = screen.getByText('Local Ollama');
      fireEvent.click(providerCard);
    });

    // Switch to health tab
    const healthTab = screen.getByText('Health & Metrics');
    fireEvent.click(healthTab);

    expect(screen.getByText('Connection refused')).toBeInTheDocument();
    expect(screen.getByText('Unable to connect to localhost:11434')).toBeInTheDocument();
    expect(screen.getByText('critical')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));
    
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load provider configurations',
        variant: 'destructive'
      });
    });
  });

  it('prevents test without valid form', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    // Clear API key
    const apiKeyInput = screen.getByLabelText(/API Key/);
    fireEvent.change(apiKeyInput, { target: { value: '' } });

    // Try to test
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Validation Error',
      description: 'Please fix the form errors before testing',
      variant: 'destructive'
    });
  });

  it('cancels form editing', async () => {
    render(<ProviderConfigInterface />);
    
    await waitFor(() => {
      const addButton = screen.getByText('OpenAI');
      fireEvent.click(addButton);
    });

    expect(screen.getByText('Add OpenAI Provider')).toBeInTheDocument();

    // Cancel
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(screen.queryByText('Add OpenAI Provider')).not.toBeInTheDocument();
    expect(screen.getByText('Select a Provider')).toBeInTheDocument();
  });
});