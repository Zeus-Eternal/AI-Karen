import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ReasoningVisualization from '../ReasoningVisualization';
import { ReasoningChain } from '@/types/enhanced-chat';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date, format) => {
    if (format === 'HH:mm:ss') return '12:34:56';
    return 'Jan 01, 2024 12:34:56';
  })
}));

const mockReasoningChain: ReasoningChain = {
  steps: [
    {
      id: 'step-1',
      description: 'Analyzed user query for intent and context',
      type: 'analysis',
      confidence: 0.9,
      evidence: ['User message content', 'Conversation history'],
      timestamp: new Date()
    },
    {
      id: 'step-2',
      description: 'Retrieved relevant information from knowledge base',
      type: 'retrieval',
      confidence: 0.85,
      evidence: ['Knowledge base search', 'Semantic matching'],
      timestamp: new Date()
    },
    {
      id: 'step-3',
      description: 'Synthesized response based on analysis',
      type: 'synthesis',
      confidence: 0.87,
      evidence: ['Context analysis', 'Information synthesis'],
      timestamp: new Date()
    }
  ],
  confidence: 0.87,
  sources: [
    {
      id: 'source-1',
      type: 'knowledge_base',
      title: 'AI Reasoning Documentation',
      reliability: 0.9,
      relevance: 0.85,
      snippet: 'AI reasoning involves multiple steps of analysis and synthesis'
    },
    {
      id: 'source-2',
      type: 'memory',
      title: 'Previous User Interactions',
      reliability: 0.8,
      relevance: 0.9,
      snippet: 'User prefers detailed explanations with examples'
    }
  ],
  methodology: 'Multi-step reasoning with evidence-based analysis'
};

describe('ReasoningVisualization', () => {
  const mockOnExport = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders reasoning chain with correct information', () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    expect(screen.getByText('AI Reasoning Chain')).toBeInTheDocument();
    expect(screen.getByText('High (87%)')).toBeInTheDocument();
    expect(screen.getByText('Multi-step reasoning with evidence-based analysis')).toBeInTheDocument();
    expect(screen.getByText('3 steps completed')).toBeInTheDocument();
  });

  it('displays all reasoning steps', () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    expect(screen.getByText('Analyzed user query for intent and context')).toBeInTheDocument();
    expect(screen.getByText('Retrieved relevant information from knowledge base')).toBeInTheDocument();
    expect(screen.getByText('Synthesized response based on analysis')).toBeInTheDocument();
  });

  it('shows step types and confidence levels', () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    expect(screen.getByText('analysis')).toBeInTheDocument();
    expect(screen.getByText('retrieval')).toBeInTheDocument();
    expect(screen.getByText('synthesis')).toBeInTheDocument();
    
    expect(screen.getByText('Very High (90%)')).toBeInTheDocument();
    expect(screen.getByText('High (85%)')).toBeInTheDocument();
    expect(screen.getByText('High (87%)')).toBeInTheDocument();
  });

  it('handles step expansion and collapse', async () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    // Initially, evidence should not be visible
    expect(screen.queryByText('User message content')).not.toBeInTheDocument();

    // Click on first step to expand
    const firstStep = screen.getByText('Analyzed user query for intent and context');
    fireEvent.click(firstStep);

    // Evidence should now be visible
    await waitFor(() => {
      expect(screen.getByText('Evidence')).toBeInTheDocument();
      expect(screen.getByText('User message content')).toBeInTheDocument();
      expect(screen.getByText('Conversation history')).toBeInTheDocument();
    });

    // Click again to collapse
    fireEvent.click(firstStep);

    await waitFor(() => {
      expect(screen.queryByText('User message content')).not.toBeInTheDocument();
    });
  });

  it('displays sources when toggled', async () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    // Sources should not be visible initially
    expect(screen.queryByText('AI Reasoning Documentation')).not.toBeInTheDocument();

    // Click show sources button
    const showSourcesButton = screen.getByText('Show Sources (2)');
    fireEvent.click(showSourcesButton);

    // Sources should now be visible
    await waitFor(() => {
      expect(screen.getByText('AI Reasoning Documentation')).toBeInTheDocument();
      expect(screen.getByText('Previous User Interactions')).toBeInTheDocument();
    });

    // Button text should change
    expect(screen.getByText('Hide Sources (2)')).toBeInTheDocument();
  });

  it('handles export functionality', async () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    expect(mockOnExport).toHaveBeenCalledWith(mockReasoningChain);
  });

  it('handles copy reasoning summary', async () => {
    // Mock clipboard API
    const mockWriteText = vi.fn();
    Object.assign(navigator, {
      clipboard: {
        writeText: mockWriteText,
      },
    });

    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(
        expect.stringContaining('1. Analyzed user query for intent and context (90% confidence)')
      );
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Copied',
        description: 'Reasoning summary copied to clipboard'
      });
    });
  });

  it('renders compact version correctly', () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
        compact={true}
      />
    );

    expect(screen.getByText('87%')).toBeInTheDocument();
    expect(screen.getByText('3 steps')).toBeInTheDocument();
    
    // Full interface should not be visible in compact mode
    expect(screen.queryByText('AI Reasoning Chain')).not.toBeInTheDocument();
  });

  it('shows confidence analysis for expanded steps', async () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    // Expand first step
    const firstStep = screen.getByText('Analyzed user query for intent and context');
    fireEvent.click(firstStep);

    await waitFor(() => {
      expect(screen.getByText('Confidence Analysis')).toBeInTheDocument();
      expect(screen.getByText('Step Confidence')).toBeInTheDocument();
      expect(screen.getByText('90%')).toBeInTheDocument();
    });
  });

  it('displays step timestamps', async () => {
    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
        onExport={mockOnExport}
      />
    );

    // Expand first step to see timestamp details
    const firstStep = screen.getByText('Analyzed user query for intent and context');
    fireEvent.click(firstStep);

    await waitFor(() => {
      expect(screen.getByText(/Processed at/)).toBeInTheDocument();
    });
  });

  it('handles reasoning chain with no sources', () => {
    const reasoningWithoutSources: ReasoningChain = {
      ...mockReasoningChain,
      sources: []
    };

    render(
      <ReasoningVisualization
        reasoning={reasoningWithoutSources}
        onExport={mockOnExport}
      />
    );

    // Sources button should not be present
    expect(screen.queryByText(/Show Sources/)).not.toBeInTheDocument();
  });

  it('handles default export when no onExport provided', async () => {
    // Mock URL.createObjectURL and related APIs
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    // Mock document.createElement and related DOM methods
    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
    };
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
    vi.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild);
    vi.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild);

    render(
      <ReasoningVisualization
        reasoning={mockReasoningChain}
      />
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockAnchor.click).toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Exported',
        description: 'Reasoning chain exported successfully'
      });
    });
  });
});