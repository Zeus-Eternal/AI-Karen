import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import ModelLibrary from '../ModelLibrary';
import { useToast } from '@/hooks/use-toast';

// Mock the hooks
vi.mock('@/hooks/use-toast', () => ({
  useToast: vi.fn(),
}));

vi.mock('@/hooks/use-download-status', () => ({
  useDownloadStatus: vi.fn(),
}));

// Mock API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockToast = vi.fn();
(useToast as any).mockReturnValue({ toast: mockToast });

const mockModels = [
  {
    id: 'tinyllama-1.1b-chat-q4',
    name: 'TinyLlama 1.1B Chat Q4_K_M',
    provider: 'llama-cpp',
    size: 669000000,
    description: 'A compact 1.1B parameter language model optimized for chat applications',
    capabilities: ['text-generation', 'chat', 'local-inference'],
    status: 'available',
    metadata: {
      parameters: '1.1B',
      quantization: 'Q4_K_M',
      memory_requirement: '~1GB',
      context_length: 2048,
      license: 'Apache 2.0',
      tags: ['chat', 'small', 'efficient']
    }
  },
  {
    id: 'local-model-1',
    name: 'Local Model 1',
    provider: 'llama-cpp',
    size: 1000000000,
    description: 'A locally installed model',
    capabilities: ['text-generation'],
    status: 'local',
    local_path: '/path/to/local/model.gguf',
    disk_usage: 1000000000
  },
  {
    id: 'phi-2-q4',
    name: 'Microsoft Phi-2 Q4_K_M',
    provider: 'llama-cpp',
    size: 1600000000,
    description: 'Microsoft\'s Phi-2 model with 2.7B parameters',
    capabilities: ['text-generation', 'code-generation', 'reasoning'],
    status: 'available',
    metadata: {
      parameters: '2.7B',
      quantization: 'Q4_K_M',
      memory_requirement: '~2GB',
      context_length: 2048,
      license: 'MIT',
      tags: ['reasoning', 'code', 'efficient']
    }
  }
];

describe('ModelLibrary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock successful API responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/models/library')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ models: mockModels })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  it('renders loading state initially', () => {
    render(<ModelLibrary />);
    
    expect(screen.getByText('Loading models...')).toBeInTheDocument();
  });

  it('renders models after loading', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('Local Model 1')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Phi-2 Q4_K_M')).toBeInTheDocument();
    });
  });

  it('categorizes models by provider type', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      // Should have sections for local and cloud providers
      expect(screen.getByText('Local Models')).toBeInTheDocument();
      expect(screen.getByText('Available Models')).toBeInTheDocument();
    });
  });

  it('displays model metadata correctly', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      // Check TinyLlama metadata
      expect(screen.getByText('1.1B')).toBeInTheDocument();
      expect(screen.getByText('Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('~1GB')).toBeInTheDocument();
      expect(screen.getByText('Apache 2.0')).toBeInTheDocument();
    });
  });

  it('shows download button for available models', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const tinyllamaCard = screen.getByText('TinyLlama 1.1B Chat Q4_K_M').closest('[data-testid="model-card"]');
      expect(tinyllamaCard).toBeInTheDocument();
      
      if (tinyllamaCard) {
        const downloadButton = within(tinyllamaCard).getByRole('button', { name: /download/i });
        expect(downloadButton).toBeInTheDocument();
      }
    });
  });

  it('shows delete button for local models', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const localModelCard = screen.getByText('Local Model 1').closest('[data-testid="model-card"]');
      expect(localModelCard).toBeInTheDocument();
      
      if (localModelCard) {
        const deleteButton = within(localModelCard).getByRole('button', { name: /delete/i });
        expect(deleteButton).toBeInTheDocument();
      }
    });
  });

  it('initiates download when download button is clicked', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const downloadButton = screen.getByRole('button', { name: /download.*tinyllama/i });
      fireEvent.click(downloadButton);
    });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/models/download',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model_id: 'tinyllama-1.1b-chat-q4' })
        })
      );
    });
  });

  it('shows confirmation dialog before deleting model', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const deleteButton = screen.getByRole('button', { name: /delete.*local model 1/i });
      fireEvent.click(deleteButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Delete Model')).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
    });
  });

  it('deletes model when confirmed', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const deleteButton = screen.getByRole('button', { name: /delete.*local model 1/i });
      fireEvent.click(deleteButton);
    });
    
    await waitFor(() => {
      const confirmButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(confirmButton);
    });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/models/local-model-1',
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  it('filters models by search term', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search models/i);
      fireEvent.change(searchInput, { target: { value: 'tinyllama' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.queryByText('Microsoft Phi-2 Q4_K_M')).not.toBeInTheDocument();
    });
  });

  it('filters models by capability', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const capabilityFilter = screen.getByRole('combobox', { name: /filter by capability/i });
      fireEvent.click(capabilityFilter);
    });
    
    await waitFor(() => {
      const chatOption = screen.getByText('chat');
      fireEvent.click(chatOption);
    });
    
    await waitFor(() => {
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.queryByText('Microsoft Phi-2 Q4_K_M')).not.toBeInTheDocument();
    });
  });

  it('filters models by provider', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const providerFilter = screen.getByRole('combobox', { name: /filter by provider/i });
      fireEvent.click(providerFilter);
    });
    
    await waitFor(() => {
      const llamaCppOption = screen.getByText('llama-cpp');
      fireEvent.click(llamaCppOption);
    });
    
    await waitFor(() => {
      // All models in our mock are llama-cpp, so all should be visible
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Phi-2 Q4_K_M')).toBeInTheDocument();
    });
  });

  it('sorts models by size', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const sortSelect = screen.getByRole('combobox', { name: /sort by/i });
      fireEvent.click(sortSelect);
    });
    
    await waitFor(() => {
      const sizeOption = screen.getByText('Size (smallest first)');
      fireEvent.click(sizeOption);
    });
    
    await waitFor(() => {
      const modelCards = screen.getAllByTestId('model-card');
      const firstModelName = within(modelCards[0]).getByRole('heading').textContent;
      expect(firstModelName).toBe('TinyLlama 1.1B Chat Q4_K_M'); // Smallest model
    });
  });

  it('displays disk usage for local models', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const localModelCard = screen.getByText('Local Model 1').closest('[data-testid="model-card"]');
      expect(localModelCard).toBeInTheDocument();
      
      if (localModelCard) {
        expect(within(localModelCard).getByText(/953.67 MB/)).toBeInTheDocument(); // 1GB formatted
      }
    });
  });

  it('shows model capabilities as badges', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      expect(screen.getByText('text-generation')).toBeInTheDocument();
      expect(screen.getByText('chat')).toBeInTheDocument();
      expect(screen.getByText('code-generation')).toBeInTheDocument();
      expect(screen.getByText('reasoning')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'));
    
    render(<ModelLibrary />);
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'Failed to load models. Please try again.',
        variant: 'destructive'
      });
    });
  });

  it('shows empty state when no models available', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/models/library')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ models: [] })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    
    render(<ModelLibrary />);
    
    await waitFor(() => {
      expect(screen.getByText('No models available')).toBeInTheDocument();
      expect(screen.getByText('No models match your current filters')).toBeInTheDocument();
    });
  });

  it('refreshes models when refresh button is clicked', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);
    });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });

  it('shows model details dialog when info button is clicked', async () => {
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const infoButton = screen.getByRole('button', { name: /info.*tinyllama/i });
      fireEvent.click(infoButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Model Details')).toBeInTheDocument();
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
    });
  });

  it('displays download progress for downloading models', async () => {
    const downloadingModels = [
      ...mockModels,
      {
        id: 'downloading-model',
        name: 'Downloading Model',
        provider: 'llama-cpp',
        size: 1000000000,
        description: 'A model being downloaded',
        capabilities: ['text-generation'],
        status: 'downloading',
        download_progress: 45.5
      }
    ];
    
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/models/library')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ models: downloadingModels })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    
    render(<ModelLibrary />);
    
    await waitFor(() => {
      expect(screen.getByText('Downloading Model')).toBeInTheDocument();
      expect(screen.getByText('45.5%')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  it('cancels download when cancel button is clicked', async () => {
    const downloadingModels = [
      ...mockModels,
      {
        id: 'downloading-model',
        name: 'Downloading Model',
        provider: 'llama-cpp',
        size: 1000000000,
        description: 'A model being downloaded',
        capabilities: ['text-generation'],
        status: 'downloading',
        download_progress: 45.5
      }
    ];
    
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/api/models/library')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ models: downloadingModels })
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    
    render(<ModelLibrary />);
    
    await waitFor(() => {
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);
    });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/download/'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  it('clears filters when clear button is clicked', async () => {
    render(<ModelLibrary />);
    
    // Apply some filters first
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search models/i);
      fireEvent.change(searchInput, { target: { value: 'tinyllama' } });
    });
    
    await waitFor(() => {
      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);
    });
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search models/i) as HTMLInputElement;
      expect(searchInput.value).toBe('');
      
      // All models should be visible again
      expect(screen.getByText('TinyLlama 1.1B Chat Q4_K_M')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Phi-2 Q4_K_M')).toBeInTheDocument();
    });
  });
});