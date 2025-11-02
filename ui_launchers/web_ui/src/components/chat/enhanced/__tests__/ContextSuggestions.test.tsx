
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ContextSuggestions from '../ContextSuggestions';
import {
  EnhancedChatMessage,
  ConversationContext,
  ContextSuggestion
} from '@/types/enhanced-chat';

const mockMessages: EnhancedChatMessage[] = [
  {
    id: 'msg-1',
    role: 'user',
    content: 'How do I implement error handling in React?',
    timestamp: new Date(),
    type: 'text',
    status: 'sent'
  },
  {
    id: 'msg-2',
    role: 'assistant',
    content: 'Here\'s a code example for error handling in React components...',
    timestamp: new Date(),
    type: 'code',
    status: 'completed',
    confidence: 0.9,
    metadata: {
      suggestions: [
        {
          id: 'existing-sug-1',
          type: 'follow_up',
          text: 'Would you like to see more error handling patterns?',
          confidence: 0.8,
          reasoning: 'User received code example'
        }
      ]
    }
  }
];

const mockConversationContext: ConversationContext = {
  currentThread: {
    id: 'thread-1',
    title: 'React Development',
    topic: 'Error Handling',
    messages: mockMessages,
    participants: ['user', 'assistant'],
    createdAt: new Date(),
    updatedAt: new Date(),
    status: 'active',
    metadata: {
      messageCount: 2,
      averageResponseTime: 1200,
      topicDrift: 0.1,
      sentiment: 'neutral',
      complexity: 'medium',
      tags: ['react', 'error-handling'],
      summary: 'Discussion about React error handling'
    }
  },
  relatedThreads: [],
  userPatterns: [
    {
      type: 'preference',
      pattern: 'detailed code examples',
      confidence: 0.85,
      frequency: 10,
      lastSeen: new Date()
    },
    {
      type: 'behavior',
      pattern: 'asks for best practices',
      confidence: 0.9,
      frequency: 8,
      lastSeen: new Date()
    }
  ],
  sessionContext: {
    sessionId: 'session-123',
    startTime: new Date(),
    duration: 1800000,
    messageCount: 2,
    topics: ['react', 'error-handling'],
    mood: 'focused',
    focus: ['learning', 'implementation']
  },
  memoryContext: {
    recentMemories: [],
    relevantMemories: [
      {
        id: 'mem-1',
        type: 'semantic',
        content: 'User prefers practical examples over theory',
        relevance: 0.8,
        timestamp: new Date(),
        source: 'user-behavior'
      }
    ],
    memoryStats: {
      totalMemories: 25,
      relevantCount: 5,
      averageRelevance: 0.7
    }
  }
};

describe('ContextSuggestions', () => {
  const mockOnSuggestionSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders suggestions based on conversation context', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Wait for suggestions to be generated
    await waitFor(() => {
      expect(screen.getByText('Smart Suggestions')).toBeInTheDocument();
    });

    // Should show suggestions based on the code response
    await waitFor(() => {
      expect(screen.getByText('Can you explain this code in more detail?')).toBeInTheDocument();
    });
  });

  it('generates follow-up suggestions for code responses', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Can you explain this code in more detail?')).toBeInTheDocument();
      expect(screen.getByText('How can I modify this code for my use case?')).toBeInTheDocument();
    });
  });

  it('generates pattern-based suggestions from user behavior', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Would you like help with detailed code examples?')).toBeInTheDocument();
    });
  });

  it('handles suggestion selection', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      const suggestionButton = screen.getByText('Can you explain this code in more detail?');
      fireEvent.click(suggestionButton);
    });

    expect(mockOnSuggestionSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        text: 'Can you explain this code in more detail?',
        type: 'follow_up',
        confidence: 0.85
      })
    );
  });

  it('shows loading state while generating suggestions', () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    expect(screen.getByText('Generating...')).toBeInTheDocument();
  });

  it('limits suggestions to maxSuggestions prop', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
        maxSuggestions={2}
      />
    );

    await waitFor(() => {
      const suggestionButtons = screen.getAllByRole('button');
      // Should have at most 2 suggestion buttons (plus any UI buttons)
      const suggestionTexts = suggestionButtons.filter(button => 
        button.textContent?.includes('Can you') || 
        button.textContent?.includes('Would you') ||
        button.textContent?.includes('What are')
      );
      expect(suggestionTexts.length).toBeLessThanOrEqual(2);
    });
  });

  it('generates action suggestions based on user queries', async () => {
    const messagesWithHowQuery: EnhancedChatMessage[] = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'How do I create a tutorial for beginners?',
        timestamp: new Date(),
        type: 'text',
        status: 'sent'
      }
    ];

    render(
      <ContextSuggestions
        messages={messagesWithHowQuery}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Would you like a step-by-step tutorial?')).toBeInTheDocument();
    });
  });

  it('generates memory-based suggestions when relevant memories exist', async () => {
    const contextWithMemories: ConversationContext = {
      ...mockConversationContext,
      memoryContext: {
        ...mockConversationContext.memoryContext,
        relevantMemories: [
          {
            id: 'mem-1',
            type: 'episodic',
            content: 'Previous discussion about React patterns',
            relevance: 0.9,
            timestamp: new Date(),
            source: 'conversation-history'
          }
        ]
      }
    };

    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={contextWithMemories}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('This reminds me of something we discussed before...')).toBeInTheDocument();
    });
  });

  it('displays confidence scores for suggestions', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      // Should show confidence percentages
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('categorizes suggestions by type', async () => {
    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={mockConversationContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText('follow up')).toHaveLength(2);
      expect(screen.getByText('action')).toBeInTheDocument();
    });
  });

  it('handles complex conversation context for suggestion generation', async () => {
    const complexContext: ConversationContext = {
      ...mockConversationContext,
      currentThread: {
        ...mockConversationContext.currentThread,
        metadata: {
          ...mockConversationContext.currentThread.metadata,
          complexity: 'complex'
        }
      }
    };

    render(
      <ContextSuggestions
        messages={mockMessages}
        conversationContext={complexContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Can you break this down into simpler steps?')).toBeInTheDocument();
    });
  });

  it('does not render when no suggestions are available', async () => {
    const emptyMessages: EnhancedChatMessage[] = [];
    const emptyContext: ConversationContext = {
      ...mockConversationContext,
      currentThread: {
        ...mockConversationContext.currentThread,
        topic: '', // Remove topic to prevent topic-based suggestions
        messages: []
      },
      userPatterns: [],
      memoryContext: {
        ...mockConversationContext.memoryContext,
        relevantMemories: []
      }
    };

    const { container } = render(
      <ContextSuggestions
        messages={emptyMessages}
        conversationContext={emptyContext}
        onSuggestionSelect={mockOnSuggestionSelect}
      />
    );

    // Wait for the component to process and potentially render nothing
    await waitFor(() => {
      // The component might still render with empty suggestions, so check for no suggestion buttons
      const suggestionButtons = container.querySelectorAll('button');
      expect(suggestionButtons.length).toBe(0);
    }, { timeout: 1000 });
  });
});