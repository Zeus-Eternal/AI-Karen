/**
 * Tests for AG-UI Memory Components
 * Tests the React components for memory management with AG-UI and CopilotKit integration
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';

// Mock AG-Grid and AG-Charts
vi.mock('ag-grid-react', () => ({
  AgGridReact: ({ rowData, onRowClicked, onRowDoubleClicked }: any) => (
    <div data-testid="ag-grid">
      {rowData?.map((row: any, index: number) => (
        <div
          key={row.id || index}
          data-testid={`grid-row-${index}`}
          onClick={() => onRowClicked?.({ data: row })}
          onDoubleClick={() => onRowDoubleClicked?.({ data: row })}
        >
          {row.content}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('ag-charts-react', () => ({
  AgChartsReact: ({ options }: any) => (
    <div data-testid="ag-chart">
      Chart: {options?.title || 'Untitled'}
    </div>
  ),
}));

// Mock CopilotKit
vi.mock('@copilotkit/react-core', () => ({
  CopilotProvider: ({ children }: any) => <div data-testid="copilot-provider">{children}</div>,
  useCopilotAction: () => {},
  useCopilotReadable: () => {},
}));

vi.mock('@copilotkit/react-textarea', () => ({
  CopilotTextarea: ({ value, onChange, placeholder, ...props }: any) => (
    <textarea
      data-testid="copilot-textarea"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      {...props}
    />
  ),
}));

// Import components after mocking
import MemoryGrid from '../components/memory/MemoryGrid';
import MemoryNetworkVisualization from '../components/memory/MemoryNetworkVisualization';
import MemoryEditor from '../components/memory/MemoryEditor';
import MemoryInterface from '../components/memory/MemoryInterface';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Sample test data
const sampleMemoryData = [
  {
    id: 'mem_1',
    content: 'User prefers Python over JavaScript',
    type: 'preference',
    confidence: 0.9,
    last_accessed: '2024-01-15T10:30:00Z',
    relevance_score: 0.8,
    semantic_cluster: 'technical',
    relationships: ['mem_2'],
    timestamp: 1705312200,
    user_id: 'test_user',
    session_id: 'test_session',
    tenant_id: 'test_tenant'
  },
  {
    id: 'mem_2',
    content: 'Meeting scheduled for tomorrow',
    type: 'fact',
    confidence: 0.95,
    last_accessed: '2024-01-15T11:00:00Z',
    relevance_score: 0.7,
    semantic_cluster: 'work',
    relationships: ['mem_1'],
    timestamp: 1705314000,
    user_id: 'test_user',
    session_id: 'test_session',
    tenant_id: 'test_tenant'
  }
];

const sampleNetworkData = {
  nodes: [
    {
      id: 'mem_1',
      label: 'Python preference',
      type: 'preference',
      confidence: 0.9,
      cluster: 'technical',
      size: 20,
      color: '#FF6B6B'
    },
    {
      id: 'mem_2',
      label: 'Meeting fact',
      type: 'fact',
      confidence: 0.95,
      cluster: 'work',
      size: 22,
      color: '#4ECDC4'
    }
  ],
  edges: [
    {
      source: 'mem_1',
      target: 'mem_2',
      weight: 0.5,
      type: 'semantic',
      label: 'related'
    }
  ]
};

const sampleAnalytics = {
  total_memories: 2,
  memories_by_type: { preference: 1, fact: 1 },
  memories_by_cluster: { technical: 1, work: 1 },
  confidence_distribution: [
    { range: '0.8-1.0', count: 2 },
    { range: '0.6-0.8', count: 0 }
  ],
  access_patterns: [
    { date: '2024-01-15', count: 2 }
  ],
  relationship_stats: {
    total_relationships: 2,
    connected_memories: 2,
    isolated_memories: 0,
    avg_relationships: 1.0
  }
};

describe('MemoryGrid Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders memory grid with data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryGrid
        userId="test_user"
        tenantId="test_tenant"
        height={400}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/memory/grid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'test_user',
        tenant_id: 'test_tenant',
        filters: {}
      })
    });
  });

  it('handles memory selection', async () => {
    const onMemorySelect = vi.fn();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryGrid
        userId="test_user"
        onMemorySelect={onMemorySelect}
        height={400}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('grid-row-0')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('grid-row-0'));
    expect(onMemorySelect).toHaveBeenCalledWith(sampleMemoryData[0]);
  });

  it('handles memory editing on double click', async () => {
    const onMemoryEdit = vi.fn();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryGrid
        userId="test_user"
        onMemoryEdit={onMemoryEdit}
        height={400}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('grid-row-0')).toBeInTheDocument();
    });

    fireEvent.doubleClick(screen.getByTestId('grid-row-0'));
    expect(onMemoryEdit).toHaveBeenCalledWith(sampleMemoryData[0]);
  });

  it('displays error state when fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryGrid
        userId="test_user"
        height={400}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Error Loading Memory Data/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('retries fetch on error', async () => {
    mockFetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ memories: sampleMemoryData })
      });

    render(
      <MemoryGrid
        userId="test_user"
        height={400}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Retry'));

    await waitFor(() => {
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});

describe('MemoryNetworkVisualization Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders network visualization with data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => sampleNetworkData
    });

    render(
      <MemoryNetworkVisualization
        userId="test_user"
        tenantId="test_tenant"
        height={500}
        width={800}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Nodes: 2/)).toBeInTheDocument();
      expect(screen.getByText(/Edges: 1/)).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/memory/network', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'test_user',
        tenant_id: 'test_tenant',
        max_nodes: 50
      })
    });
  });

  it('handles cluster filtering', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => sampleNetworkData
    });

    render(
      <MemoryNetworkVisualization
        userId="test_user"
        height={500}
        width={800}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('All Clusters')).toBeInTheDocument();
    });

    const select = screen.getByDisplayValue('All Clusters');
    fireEvent.change(select, { target: { value: 'technical' } });

    expect(select).toHaveValue('technical');
  });

  it('refreshes network data', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleNetworkData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleNetworkData
      });

    render(
      <MemoryNetworkVisualization
        userId="test_user"
        height={500}
        width={800}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Refresh'));

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('displays error state when network fetch fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryNetworkVisualization
        userId="test_user"
        height={500}
        width={800}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Error Loading Network Data/i)).toBeInTheDocument();
    });
  });
});

describe('MemoryEditor Component', () => {
  const sampleMemory = sampleMemoryData[0];

  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders editor when open', () => {
    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    expect(screen.getByText('Edit Memory')).toBeInTheDocument();
    expect(screen.getByTestId('copilot-textarea')).toBeInTheDocument();
    expect(screen.getByDisplayValue('preference')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={false}
        userId="test_user"
      />
    );

    expect(screen.queryByText('Edit Memory')).not.toBeInTheDocument();
  });

  it('renders create mode when no memory provided', () => {
    render(
      <MemoryEditor
        memory={null}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    expect(screen.getByText('Create New Memory')).toBeInTheDocument();
    expect(screen.getByTestId('copilot-textarea')).toHaveValue('');
  });

  it('handles content editing', async () => {
    const user = userEvent.setup();

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    const textarea = screen.getByTestId('copilot-textarea');
    await user.clear(textarea);
    await user.type(textarea, 'Updated memory content');

    expect(textarea).toHaveValue('Updated memory content');
  });

  it('handles type selection', async () => {
    const user = userEvent.setup();

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    const typeSelect = screen.getByDisplayValue('preference');
    await user.selectOptions(typeSelect, 'fact');

    expect(typeSelect).toHaveValue('fact');
  });

  it('handles confidence adjustment', async () => {
    const user = userEvent.setup();

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    const confidenceSlider = screen.getByDisplayValue('0.9');
    await user.clear(confidenceSlider);
    await user.type(confidenceSlider, '0.7');

    expect(confidenceSlider).toHaveValue('0.7');
  });

  it('generates AI suggestions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        suggestions: [
          {
            type: 'enhancement',
            content: 'Enhanced content suggestion',
            confidence: 0.8,
            reasoning: 'This would make the memory clearer'
          }
        ],
        processing_time_ms: 150
      })
    });

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    fireEvent.click(screen.getByText('Get AI Suggestions'));

    await waitFor(() => {
      expect(screen.getByText('Enhanced content suggestion')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/memory/ai-suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: expect.stringContaining('"content":"User prefers Python over JavaScript"')
    });
  });

  it('applies AI suggestions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        suggestions: [
          {
            type: 'enhancement',
            content: 'Enhanced content suggestion',
            confidence: 0.8,
            reasoning: 'This would make the memory clearer'
          }
        ]
      })
    });

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    fireEvent.click(screen.getByText('Get AI Suggestions'));

    await waitFor(() => {
      expect(screen.getByText('Apply')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Apply'));

    const textarea = screen.getByTestId('copilot-textarea');
    expect(textarea).toHaveValue('Enhanced content suggestion');
  });

  it('handles save operation', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={onSave}
        onCancel={vi.fn()}
        isOpen={true}
        userId="test_user"
      />
    );

    fireEvent.click(screen.getByText('Save Memory'));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith({
        content: 'User prefers Python over JavaScript',
        type: 'preference',
        confidence: 0.9,
        semantic_cluster: 'technical',
        last_accessed: expect.any(String)
      });
    });
  });

  it('handles cancel operation', () => {
    const onCancel = vi.fn();

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={onCancel}
        isOpen={true}
        userId="test_user"
      />
    );

    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalled();
  });

  it('handles delete operation', async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined);
    window.confirm = vi.fn().mockReturnValue(true);

    render(
      <MemoryEditor
        memory={sampleMemory}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        onDelete={onDelete}
        isOpen={true}
        userId="test_user"
      />
    );

    fireEvent.click(screen.getByText('Delete Memory'));

    await waitFor(() => {
      expect(onDelete).toHaveBeenCalledWith('mem_1');
    });
  });
});

describe('MemoryInterface Component', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders memory interface with default grid view', () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryInterface
        userId="test_user"
        tenantId="test_tenant"
        height={600}
      />
    );

    expect(screen.getByText('Memory Management')).toBeInTheDocument();
    expect(screen.getByText('Grid View')).toBeInTheDocument();
    expect(screen.getByText('Network View')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('switches between view modes', async () => {
    const user = userEvent.setup();

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => sampleNetworkData
    });

    render(
      <MemoryInterface
        userId="test_user"
        height={600}
      />
    );

    // Switch to network view
    await user.click(screen.getByText('Network View'));
    
    await waitFor(() => {
      expect(screen.getByText(/Nodes:/)).toBeInTheDocument();
    });

    // Switch to analytics view
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => sampleAnalytics
    });

    await user.click(screen.getByText('Analytics'));

    await waitFor(() => {
      expect(screen.getByText('Total Memories')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ memories: sampleMemoryData })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ results: [sampleMemoryData[0]] })
      });

    render(
      <MemoryInterface
        userId="test_user"
        height={600}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search memories...');
    await user.type(searchInput, 'Python');

    const searchButton = screen.getByText('Search');
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: expect.stringContaining('"query":"Python"')
      });
    });
  });

  it('opens memory editor for new memory', async () => {
    const user = userEvent.setup();

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryInterface
        userId="test_user"
        height={600}
      />
    );

    await user.click(screen.getByText('New Memory'));

    expect(screen.getByText('Create New Memory')).toBeInTheDocument();
  });

  it('loads analytics data when switching to analytics view', async () => {
    const user = userEvent.setup();

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ memories: sampleMemoryData })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleAnalytics
      });

    render(
      <MemoryInterface
        userId="test_user"
        height={600}
      />
    );

    await user.click(screen.getByText('Analytics'));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/memory/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'test_user',
          tenant_id: undefined,
          timeframe_days: 30
        })
      });
    });

    expect(screen.getByText('2')).toBeInTheDocument(); // Total memories
    expect(screen.getByText('2')).toBeInTheDocument(); // Connected memories
  });

  it('renders with CopilotKit provider', () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ memories: sampleMemoryData })
    });

    render(
      <MemoryInterface
        userId="test_user"
        copilotApiKey="test-api-key"
        height={600}
      />
    );

    expect(screen.getByTestId('copilot-provider')).toBeInTheDocument();
  });
});

// Test utilities and helpers
describe('Memory Component Utilities', () => {
  it('formats memory data correctly for AG-Grid', () => {
    const rawMemory = sampleMemoryData[0];
    
    // Test that the memory data has all required fields for AG-Grid
    expect(rawMemory).toHaveProperty('id');
    expect(rawMemory).toHaveProperty('content');
    expect(rawMemory).toHaveProperty('type');
    expect(rawMemory).toHaveProperty('confidence');
    expect(rawMemory).toHaveProperty('semantic_cluster');
    expect(rawMemory).toHaveProperty('relationships');
    
    // Test data types
    expect(typeof rawMemory.id).toBe('string');
    expect(typeof rawMemory.content).toBe('string');
    expect(['fact', 'preference', 'context']).toContain(rawMemory.type);
    expect(typeof rawMemory.confidence).toBe('number');
    expect(rawMemory.confidence).toBeGreaterThanOrEqual(0);
    expect(rawMemory.confidence).toBeLessThanOrEqual(1);
  });

  it('validates network data structure', () => {
    const networkData = sampleNetworkData;
    
    // Test nodes structure
    expect(networkData).toHaveProperty('nodes');
    expect(networkData).toHaveProperty('edges');
    expect(Array.isArray(networkData.nodes)).toBe(true);
    expect(Array.isArray(networkData.edges)).toBe(true);
    
    // Test node properties
    const node = networkData.nodes[0];
    expect(node).toHaveProperty('id');
    expect(node).toHaveProperty('label');
    expect(node).toHaveProperty('type');
    expect(node).toHaveProperty('confidence');
    expect(node).toHaveProperty('cluster');
    expect(node).toHaveProperty('size');
    expect(node).toHaveProperty('color');
    
    // Test edge properties
    const edge = networkData.edges[0];
    expect(edge).toHaveProperty('source');
    expect(edge).toHaveProperty('target');
    expect(edge).toHaveProperty('weight');
    expect(edge).toHaveProperty('type');
    expect(edge).toHaveProperty('label');
  });

  it('validates analytics data structure', () => {
    const analytics = sampleAnalytics;
    
    expect(analytics).toHaveProperty('total_memories');
    expect(analytics).toHaveProperty('memories_by_type');
    expect(analytics).toHaveProperty('memories_by_cluster');
    expect(analytics).toHaveProperty('confidence_distribution');
    expect(analytics).toHaveProperty('access_patterns');
    expect(analytics).toHaveProperty('relationship_stats');
    
    // Test data types
    expect(typeof analytics.total_memories).toBe('number');
    expect(typeof analytics.memories_by_type).toBe('object');
    expect(typeof analytics.memories_by_cluster).toBe('object');
    expect(Array.isArray(analytics.confidence_distribution)).toBe(true);
    expect(Array.isArray(analytics.access_patterns)).toBe(true);
    expect(typeof analytics.relationship_stats).toBe('object');
  });
});