import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ContextPanel from '../ContextPanel';
import {
  ConversationContext,
  ConversationThread,
  MemoryReference,
  ContextSuggestion
} from '@/types/enhanced-chat';

// Mock the date-fns functions
vi.mock('date-fns', () => ({
  format: vi.fn((date) => '2024-01-01'),
  formatDistanceToNow: vi.fn(() => '2 hours ago')
}));

const mockConversationContext: ConversationContext = {
  currentThread: {
    id: 'current-thread',
    title: 'Current Discussion',
    topic: 'AI Development',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        content: 'How do I implement context awareness?',
        timestamp: new Date(),
        metadata: {
          suggestions: [
            {
              id: 'sug-1',
              type: 'follow_up',
              text: 'Would you like examples of context-aware systems?',
              confidence: 0.85,
              reasoning: 'User asking about implementation details'
            }
          ]
        }
      }
    ],
    participants: ['user', 'assistant'],
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
    metadata: {
      messageCount: 1,
      averageResponseTime: 1200,
      topicDrift: 0.1,
      sentiment: 'neutral',
      complexity: 'medium',
      tags: ['ai', 'development'],
      summary: 'Discussion about AI context awareness'
    }
  },
  relatedThreads: [
    {
      id: 'related-thread-1',
      title: 'Previous AI Discussion',
      topic: 'Machine Learning',
      messages: [],
      participants: ['user', 'assistant'],
      createdAt: new Date(Date.now() - 86400000),
      updatedAt: new Date(Date.now() - 3600000),
      status: 'archived',
      metadata: {
        messageCount: 10,
        averageResponseTime: 800,
        topicDrift: 0.2,
        sentiment: 'positive',
        complexity: 'complex',
        tags: ['ml', 'algorithms'],
        summary: 'Detailed discussion about ML algorithms'
      }
    }
  ],
  userPatterns: [
    {
      type: 'preference',
      pattern: 'detailed technical explanations',
      confidence: 0.9,
      frequency: 15,
      lastSeen: new Date()
    }
  ],
  sessionContext: {
    sessionId: 'session-123',
    startTime: new Date(),
    duration: 1800000,
    messageCount: 1,
    topics: ['ai', 'context'],
    mood: 'curious',
    focus: ['learning']
  },
  memoryContext: {
    recentMemories: [
      {
        id: 'mem-1',
        type: 'episodic',
        content: 'User prefers step-by-step explanations',
        relevance: 0.9,
        timestamp: new Date(),
        source: 'conversation-analysis'
      }
    ],
    relevantMemories: [
      {
        id: 'mem-2',
        type: 'semantic',
        content: 'Context awareness in AI systems involves maintaining state',
        relevance: 0.85,
        timestamp: new Date(Date.now() - 86400000),
        source: 'knowledge-base'
      }
    ],
    memoryStats: {
      totalMemories: 50,
      relevantCount: 12,
      averageRelevance: 0.75
    }
  }
};

describe('ContextPanel', () => {
  const mockOnThreadSelect = vi.fn();
  const mockOnMemorySelect = vi.fn();
  const mockOnSuggestionSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders context panel with all tabs', () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    expect(screen.getByText('Context')).toBeInTheDocument();
    expect(screen.getByText('Threads')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Ideas')).toBeInTheDocument();
    expect(screen.getByText('Patterns')).toBeInTheDocument();
  });

  it('displays related threads correctly', () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Should show the related thread
    expect(screen.getByText('Previous AI Discussion')).toBeInTheDocument();
    expect(screen.getByText('Machine Learning')).toBeInTheDocument();
    expect(screen.getByText('complex')).toBeInTheDocument();
  });

  it('handles thread selection', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    const threadItem = screen.getByText('Previous AI Discussion').closest('div');
    fireEvent.click(threadItem!);

    await waitFor(() => {
      expect(mockOnThreadSelect).toHaveBeenCalledWith('related-thread-1');
    });
  });

  it('displays memory information in memory tab', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to memory tab
    fireEvent.click(screen.getByText('Memory'));

    await waitFor(() => {
      expect(screen.getByText('Relevant Memories')).toBeInTheDocument();
      expect(screen.getByText('Context awareness in AI systems involves maintaining state')).toBeInTheDocument();
    });
  });

  it('handles memory selection', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to memory tab
    fireEvent.click(screen.getByText('Memory'));

    await waitFor(() => {
      const memoryItem = screen.getByText('Context awareness in AI systems involves maintaining state').closest('div');
      fireEvent.click(memoryItem!);
    });

    expect(mockOnMemorySelect).toHaveBeenCalledWith('mem-2');
  });

  it('displays suggestions in suggestions tab', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to suggestions tab
    fireEvent.click(screen.getByText('Ideas'));

    await waitFor(() => {
      expect(screen.getByText('Smart Suggestions')).toBeInTheDocument();
      expect(screen.getByText('Would you like examples of context-aware systems?')).toBeInTheDocument();
    });
  });

  it('handles suggestion selection', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to suggestions tab
    fireEvent.click(screen.getByText('Ideas'));

    await waitFor(() => {
      const suggestionButton = screen.getByText('Would you like examples of context-aware systems?');
      fireEvent.click(suggestionButton);
    });

    expect(mockOnSuggestionSelect).toHaveBeenCalledWith({
      id: 'sug-1',
      type: 'follow_up',
      text: 'Would you like examples of context-aware systems?',
      confidence: 0.85,
      reasoning: 'User asking about implementation details'
    });
  });

  it('displays user patterns in patterns tab', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to patterns tab
    fireEvent.click(screen.getByText('Patterns'));

    await waitFor(() => {
      expect(screen.getByText('User Patterns')).toBeInTheDocument();
      expect(screen.getByText('detailed technical explanations')).toBeInTheDocument();
    });
  });

  it('filters content based on search query', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search context...');
    fireEvent.change(searchInput, { target: { value: 'Machine Learning' } });

    await waitFor(() => {
      expect(screen.getByText('Previous AI Discussion')).toBeInTheDocument();
    });

    // Search for something that doesn't exist
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.queryByText('Previous AI Discussion')).not.toBeInTheDocument();
    });
  });

  it('displays memory statistics', async () => {
    render(
      <ContextPanel
        conversation={mockConversationContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Switch to memory tab
    fireEvent.click(screen.getByText('Memory'));

    await waitFor(() => {
      expect(screen.getByText('Relevant Memories')).toBeInTheDocument();
      // Check for memory stats in a more flexible way
      expect(screen.getByText(/Total/)).toBeInTheDocument();
      expect(screen.getByText(/Avg Relevance/)).toBeInTheDocument();
    });
  });

  it('handles empty states correctly', () => {
    const emptyContext: ConversationContext = {
      ...mockConversationContext,
      relatedThreads: [],
      userPatterns: [],
      memoryContext: {
        ...mockConversationContext.memoryContext,
        relevantMemories: [],
        recentMemories: []
      },
      currentThread: {
        ...mockConversationContext.currentThread,
        messages: []
      }
    };

    render(
      <ContextPanel
        conversation={emptyContext}
        onThreadSelect={mockOnThreadSelect}
        onMemorySelect={mockOnMemorySelect}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    expect(screen.getByText('No related conversations found')).toBeInTheDocument();
  });
});