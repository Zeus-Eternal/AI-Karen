/**
 * Tests for Memory AG-UI Components
 * Tests the enhanced memory system with AG-UI components and CopilotKit integration.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MemoryInterface from '../components/memory/MemoryInterface';
import MemoryGrid from '../components/memory/MemoryGrid';
import MemoryEditor from '../components/memory/MemoryEditor';
import MemoryNetworkVisualization from '../components/memory/MemoryNetworkVisualization';

// Mock fetch globally
global.fetch = vi.fn();

// Mock CopilotKit components
vi.mock('@copilotkit/react-core', () => ({
  CopilotKit: ({ children }: { children: React.ReactNode }) => <div data-testid="copilot-provider">{children}</div>,
  useCopilotAction: () => {},
  useCopilotReadable: () => {},
}));

vi.mock('@copilotkit/react-textarea', () => ({
  CopilotTextarea: (props: any) => <textarea data-testid="copilot-textarea" {...props} />,
}));

// Mock AG-Grid components
vi.mock('ag-grid-react', () => ({
  AgGridReact: (props: any) => (
    <div data-testid="ag-grid" role="grid">
      <div role="row">
        <div role="columnheader">Content</div>
        <div role="columnheader">Type</div>
        <div role="columnheader">Confidence</div>
      </div>
      {props.rowData?.map((row: any, index: number) => (
        <div key={index} role="row" onClick={() => props.onRowClicked?.({ data: row })}>
          <div role="gridcell">{row.content}</div>
          <div role="gridcell">{row.type}</div>
          <div role="gridcell">{row.confidence}</div>
        </div>
      ))}
    </div>
  ),
}));

// Mock AG-Charts components
vi.mock('ag-charts-react', () => ({
  AgChartsReact: (props: any) => (
    <div data-testid="ag-chart">
      Chart: {props.options?.title || 'Untitled Chart'}
    </div>
  ),
}));

describe('Memory AG-UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        memories: [
          {
            id: 'mem_1',
            content: 'Python is a programming language',
            type: 'fact',
            confidence: 0.9,
            last_accessed: '2024-01-15T10:30:00',
            relevance_score: 0.85,
            semantic_cluster: 'technical',
            relationships: ['mem_2'],
            timestamp: 1705312200,
            user_id: 'test_user'
          },
          {
            id: 'mem_2',
            content: 'I prefer Python over JavaScript',
            type: 'preference',
            confidence: 0.8,
            last_accessed: '2024-01-15T11:00:00',
            relevance_score: 0.75,
            semantic_cluster: 'personal',
            relationships: ['mem_1'],
            timestamp: 1705314000,
            user_id: 'test_user'
          }
        ]
      })


  describe('MemoryInterface', () => {
    it('renders memory interface with all view modes', async () => {
      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Check if main interface elements are present
      expect(screen.getByText('Memory Management')).toBeInTheDocument();
      expect(screen.getByText('Grid View')).toBeInTheDocument();
      expect(screen.getByText('Network View')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search memories...')).toBeInTheDocument();
      expect(screen.getByText('New Memory')).toBeInTheDocument();

    it('switches between view modes correctly', async () => {
      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Initially should show grid view
      expect(screen.getByTestId('ag-grid')).toBeInTheDocument();

      // Switch to network view
      fireEvent.click(screen.getByText('Network View'));
      await waitFor(() => {
        expect(screen.queryByTestId('ag-grid')).not.toBeInTheDocument();

      // Switch to analytics view
      fireEvent.click(screen.getByText('Analytics'));
      await waitFor(() => {
        expect(screen.getByText('Loading analytics...')).toBeInTheDocument();


    it('handles search functionality', async () => {
      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      const searchInput = screen.getByPlaceholderText('Search memories...');
      const searchButton = screen.getByText('Search');

      // Enter search query
      fireEvent.change(searchInput, { target: { value: 'Python' } });
      expect(searchInput).toHaveValue('Python');

      // Click search button
      fireEvent.click(searchButton);

      // Verify fetch was called with search parameters
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/memory/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: 'test_user',
            tenant_id: 'test_tenant',
            query: 'Python',
            filters: {},
            limit: 50
          })



    it('opens memory editor when creating new memory', async () => {
      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Click new memory button
      fireEvent.click(screen.getByText('New Memory'));

      // Should open memory editor
      await waitFor(() => {
        expect(screen.getByText('Create New Memory')).toBeInTheDocument();



  describe('MemoryGrid', () => {
    it('renders memory grid with data', async () => {
      render(
        <MemoryGrid
          userId="test_user"
          tenantId="test_tenant"
          height={400}
        />
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument();

      // Check if memory data is displayed
      expect(screen.getByText('Python is a programming language')).toBeInTheDocument();
      expect(screen.getByText('I prefer Python over JavaScript')).toBeInTheDocument();

    it('handles row selection', async () => {
      const onMemorySelect = vi.fn();
      
      render(
        <MemoryGrid
          userId="test_user"
          tenantId="test_tenant"
          onMemorySelect={onMemorySelect}
          height={400}
        />
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument();

      // Click on a row
      const firstRow = screen.getByText('Python is a programming language');
      fireEvent.click(firstRow);

      // Verify callback was called
      expect(onMemorySelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'mem_1',
          content: 'Python is a programming language',
          type: 'fact'
        })
      );

    it('displays error state when fetch fails', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(
        <MemoryGrid
          userId="test_user"
          tenantId="test_tenant"
          height={400}
        />
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Error Loading Memory Data')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();



  describe('MemoryEditor', () => {
    const sampleMemory = {
      id: 'mem_1',
      content: 'Python is a programming language',
      type: 'fact' as const,
      confidence: 0.9,
      last_accessed: '2024-01-15T10:30:00',
      relevance_score: 0.85,
      semantic_cluster: 'technical',
      relationships: ['mem_2'],
      timestamp: 1705312200,
      user_id: 'test_user'
    };

    it('renders memory editor when open', () => {
      const onSave = vi.fn();
      const onCancel = vi.fn();

      render(
        <MemoryEditor
          memory={sampleMemory}
          onSave={onSave}
          onCancel={onCancel}
          isOpen={true}
          userId="test_user"
          tenantId="test_tenant"
        />
      );

      expect(screen.getByText('Edit Memory')).toBeInTheDocument();
      expect(screen.getByTestId('copilot-textarea')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Python is a programming language')).toBeInTheDocument();

    it('does not render when closed', () => {
      const onSave = vi.fn();
      const onCancel = vi.fn();

      render(
        <MemoryEditor
          memory={sampleMemory}
          onSave={onSave}
          onCancel={onCancel}
          isOpen={false}
          userId="test_user"
          tenantId="test_tenant"
        />
      );

      expect(screen.queryByText('Edit Memory')).not.toBeInTheDocument();

    it('handles form submission', async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const onCancel = vi.fn();

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })

      render(
        <MemoryEditor
          memory={sampleMemory}
          onSave={onSave}
          onCancel={onCancel}
          isOpen={true}
          userId="test_user"
          tenantId="test_tenant"
        />
      );

      // Modify content
      const textarea = screen.getByTestId('copilot-textarea');
      fireEvent.change(textarea, { target: { value: 'Updated memory content' } });

      // Click save
      fireEvent.click(screen.getByText('Save Memory'));

      // Verify save was called
      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith(
          expect.objectContaining({
            content: 'Updated memory content'
          })
        );


    it('generates AI suggestions', async () => {
      const onSave = vi.fn();
      const onCancel = vi.fn();

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          suggestions: [
            {
              type: 'enhancement',
              content: 'Consider adding version information',
              confidence: 0.8,
              reasoning: 'More specific details would be helpful'
            }
          ]
        })

      render(
        <MemoryEditor
          memory={sampleMemory}
          onSave={onSave}
          onCancel={onCancel}
          isOpen={true}
          userId="test_user"
          tenantId="test_tenant"
        />
      );

      // Click get AI suggestions
      fireEvent.click(screen.getByText('Get AI Suggestions'));

      // Wait for suggestions to load
      await waitFor(() => {
        expect(screen.getByText('Consider adding version information')).toBeInTheDocument();
        expect(screen.getByText('More specific details would be helpful')).toBeInTheDocument();



  describe('MemoryNetworkVisualization', () => {
    beforeEach(() => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          nodes: [
            {
              id: 'node_1',
              label: 'Python Programming',
              type: 'fact',
              confidence: 0.9,
              cluster: 'technical',
              size: 20,
              color: '#FF6B6B'
            },
            {
              id: 'node_2',
              label: 'JavaScript Development',
              type: 'context',
              confidence: 0.8,
              cluster: 'technical',
              size: 18,
              color: '#FF6B6B'
            }
          ],
          edges: [
            {
              source: 'node_1',
              target: 'node_2',
              weight: 0.7,
              type: 'semantic',
              label: 'related'
            }
          ]
        })


    it('renders network visualization', async () => {
      render(
        <MemoryNetworkVisualization
          userId="test_user"
          tenantId="test_tenant"
          height={500}
          width={800}
        />
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Nodes: 2 | Edges: 1')).toBeInTheDocument();

      // Check for canvas element
      const canvas = screen.getByRole('img', { hidden: true }) || document.querySelector('canvas');
      expect(canvas).toBeTruthy();

    it('handles cluster filtering', async () => {
      render(
        <MemoryNetworkVisualization
          userId="test_user"
          tenantId="test_tenant"
          height={500}
          width={800}
        />
      );

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Filter by Cluster:')).toBeInTheDocument();

      // Find and use the cluster filter
      const clusterSelect = screen.getByDisplayValue('All Clusters');
      fireEvent.change(clusterSelect, { target: { value: 'technical' } });

      // Should still show the same data since both nodes are technical
      expect(screen.getByText('Nodes: 2 | Edges: 1')).toBeInTheDocument();

    it('displays error state when network data fails to load', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(
        <MemoryNetworkVisualization
          userId="test_user"
          tenantId="test_tenant"
          height={500}
          width={800}
        />
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Error Loading Network Data')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();



  describe('Integration Tests', () => {
    it('integrates memory grid with editor', async () => {
      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Wait for grid to load
      await waitFor(() => {
        expect(screen.getByTestId('ag-grid')).toBeInTheDocument();

      // Double-click on a memory row to edit
      const memoryRow = screen.getByText('Python is a programming language');
      fireEvent.doubleClick(memoryRow);

      // Should open editor
      await waitFor(() => {
        expect(screen.getByText('Edit Memory')).toBeInTheDocument();


    it('handles memory search and filtering', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ memories: [] }) // Initial grid load
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            results: [
              {
                id: 'mem_1',
                content: 'Python programming language',
                type: 'fact',
                confidence: 0.9,
                relevance_score: 0.95
              }
            ]
          })

      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Perform search
      const searchInput = screen.getByPlaceholderText('Search memories...');
      fireEvent.change(searchInput, { target: { value: 'Python' } });
      fireEvent.click(screen.getByText('Search'));

      // Verify search API was called
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/memory/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 'test_user',
            tenant_id: 'test_tenant',
            query: 'Python',
            filters: {},
            limit: 50
          })



    it('handles analytics view with charts', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ memories: [] }) // Initial grid load
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            total_memories: 100,
            memories_by_type: { fact: 40, preference: 30, context: 30 },
            memories_by_cluster: { technical: 50, personal: 25, work: 25 },
            confidence_distribution: [
              { range: '0.8-1.0', count: 60 },
              { range: '0.6-0.8', count: 30 }
            ],
            access_patterns: [
              { date: '2024-01-15', count: 25 },
              { date: '2024-01-16', count: 30 }
            ],
            relationship_stats: {
              connected_memories: 80,
              isolated_memories: 20
            }
          })

      render(
        <MemoryInterface
          userId="test_user"
          tenantId="test_tenant"
          copilotApiKey="test_key"
        />
      );

      // Switch to analytics view
      fireEvent.click(screen.getByText('Analytics'));

      // Wait for analytics to load
      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument(); // Total memories
        expect(screen.getByText('80')).toBeInTheDocument(); // Connected memories

      // Should show charts
      expect(screen.getAllByTestId('ag-chart')).toHaveLength(3);


