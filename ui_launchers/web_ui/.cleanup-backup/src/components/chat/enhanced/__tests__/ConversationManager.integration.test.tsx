import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ConversationManager from '../ConversationManager';
import { ConversationThread } from '@/types/enhanced-chat';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date) => '2024-01-01'),
  formatDistanceToNow: vi.fn(() => '2 hours ago')
}));

const mockConversations: ConversationThread[] = [
  {
    id: 'conv-1',
    title: 'React Development Discussion',
    topic: 'React',
    messages: [],
    participants: ['user', 'assistant'],
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-02'),
    status: 'active',
    metadata: {
      messageCount: 15,
      averageResponseTime: 1200,
      topicDrift: 0.1,
      sentiment: 'positive',
      complexity: 'medium',
      tags: ['react', 'development', 'frontend'],
      summary: 'Discussion about React best practices and hooks'
    }
  },
  {
    id: 'conv-2',
    title: 'Python Data Analysis',
    topic: 'Python',
    messages: [],
    participants: ['user', 'assistant'],
    createdAt: new Date('2024-01-03'),
    updatedAt: new Date('2024-01-04'),
    status: 'archived',
    metadata: {
      messageCount: 8,
      averageResponseTime: 800,
      topicDrift: 0.2,
      sentiment: 'neutral',
      complexity: 'complex',
      tags: ['python', 'data-analysis', 'pandas'],
      summary: 'Help with pandas data manipulation and visualization'
    }
  },
  {
    id: 'conv-3',
    title: 'General Questions',
    topic: 'General',
    messages: [],
    participants: ['user', 'assistant'],
    createdAt: new Date('2024-01-05'),
    updatedAt: new Date('2024-01-06'),
    status: 'active',
    metadata: {
      messageCount: 3,
      averageResponseTime: 600,
      topicDrift: 0.05,
      sentiment: 'positive',
      complexity: 'simple',
      tags: ['general', 'questions'],
      summary: 'Various general questions and answers'
    }
  }
];

const mockAnalytics = {
  totalConversations: 3,
  totalMessages: 26,
  averageLength: 8.7,
  topTopics: [
    { topic: 'react', count: 5 },
    { topic: 'python', count: 3 },
    { topic: 'general', count: 2 }
  ],
  sentimentDistribution: {
    positive: 66.7,
    neutral: 33.3,
    negative: 0
  },
  complexityDistribution: {
    simple: 33.3,
    medium: 33.3,
    complex: 33.3
  },
  activityByDay: [
    { date: '2024-01-01', count: 1 },
    { date: '2024-01-02', count: 2 }
  ]
};

describe('ConversationManager Integration', () => {
  const mockOnConversationSelect = vi.fn();
  const mockOnConversationUpdate = vi.fn();
  const mockOnConversationDelete = vi.fn();
  const mockOnConversationArchive = vi.fn();
  const mockOnConversationExport = vi.fn();
  const mockOnConversationShare = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders conversation manager with all conversations', () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        analytics={mockAnalytics}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    expect(screen.getByText('Conversation Manager')).toBeInTheDocument();
    expect(screen.getByText('3 of 3')).toBeInTheDocument();
    expect(screen.getByText('React Development Discussion')).toBeInTheDocument();
    expect(screen.getByText('Python Data Analysis')).toBeInTheDocument();
    expect(screen.getByText('General Questions')).toBeInTheDocument();
  });

  it('handles conversation selection', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    const conversationCard = screen.getByText('React Development Discussion').closest('.cursor-pointer');
    fireEvent.click(conversationCard!);

    expect(mockOnConversationSelect).toHaveBeenCalledWith('conv-1');
  });

  it('filters conversations by search query', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search conversations...');
    fireEvent.change(searchInput, { target: { value: 'React' } });

    await waitFor(() => {
      expect(screen.getByText('React Development Discussion')).toBeInTheDocument();
      expect(screen.queryByText('Python Data Analysis')).not.toBeInTheDocument();
      expect(screen.queryByText('General Questions')).not.toBeInTheDocument();
    });

    expect(screen.getByText('1 of 3')).toBeInTheDocument();
  });

  it('filters conversations by status', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Find and click the status filter dropdown
    const statusFilter = screen.getAllByRole('combobox')[0];
    fireEvent.click(statusFilter);

    // Select "Archived" option
    const archivedOption = screen.getByText('Archived');
    fireEvent.click(archivedOption);

    await waitFor(() => {
      expect(screen.getByText('Python Data Analysis')).toBeInTheDocument();
      expect(screen.queryByText('React Development Discussion')).not.toBeInTheDocument();
      expect(screen.queryByText('General Questions')).not.toBeInTheDocument();
    });

    expect(screen.getByText('1 of 3')).toBeInTheDocument();
  });

  it('handles conversation archiving', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Find the first conversation's dropdown menu
    const dropdownTriggers = screen.getAllByRole('button', { name: /more/i });
    fireEvent.click(dropdownTriggers[0]);

    // Click archive option
    const archiveOption = screen.getByText('Archive');
    fireEvent.click(archiveOption);

    expect(mockOnConversationArchive).toHaveBeenCalledWith('conv-1');
  });

  it('handles conversation deletion', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Find the first conversation's dropdown menu
    const dropdownTriggers = screen.getAllByRole('button', { name: /more/i });
    fireEvent.click(dropdownTriggers[0]);

    // Click delete option
    const deleteOption = screen.getByText('Delete');
    fireEvent.click(deleteOption);

    expect(mockOnConversationDelete).toHaveBeenCalledWith('conv-1');
  });

  it('handles conversation sharing', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Find the first conversation's dropdown menu
    const dropdownTriggers = screen.getAllByRole('button', { name: /more/i });
    fireEvent.click(dropdownTriggers[0]);

    // Click share option
    const shareOption = screen.getByText('Share');
    fireEvent.click(shareOption);

    expect(mockOnConversationShare).toHaveBeenCalledWith('conv-1');
  });

  it('handles bulk selection and operations', async () => {
    const mockToast = vi.fn();
    vi.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({ toast: mockToast });

    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Select first two conversations
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    // Actions button should appear
    await waitFor(() => {
      expect(screen.getByText('Actions (2)')).toBeInTheDocument();
    });

    // Click actions dropdown
    const actionsButton = screen.getByText('Actions (2)');
    fireEvent.click(actionsButton);

    // Click export selected
    const exportOption = screen.getByText('Export Selected');
    fireEvent.click(exportOption);

    expect(mockOnConversationExport).toHaveBeenCalledWith(['conv-1', 'conv-2']);
  });

  it('displays analytics when provided', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        analytics={mockAnalytics}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Switch to analytics tab
    const analyticsTab = screen.getByText('Analytics');
    fireEvent.click(analyticsTab);

    await waitFor(() => {
      expect(screen.getByText('Total Conversations')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Total Messages')).toBeInTheDocument();
      expect(screen.getByText('26')).toBeInTheDocument();
    });
  });

  it('sorts conversations correctly', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Find sort dropdown (should be the last combobox)
    const sortDropdown = screen.getAllByRole('combobox').pop();
    fireEvent.click(sortDropdown!);

    // Select "Message Count" sorting
    const messageCountOption = screen.getByText('Message Count');
    fireEvent.click(messageCountOption);

    await waitFor(() => {
      // Should be sorted by message count (descending)
      const conversationTitles = screen.getAllByText(/Discussion|Analysis|Questions/);
      expect(conversationTitles[0]).toHaveTextContent('React Development Discussion'); // 15 messages
      expect(conversationTitles[1]).toHaveTextContent('Python Data Analysis'); // 8 messages
      expect(conversationTitles[2]).toHaveTextContent('General Questions'); // 3 messages
    });
  });

  it('displays conversation metadata correctly', () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    // Check that metadata is displayed
    expect(screen.getByText('medium')).toBeInTheDocument(); // complexity
    expect(screen.getByText('positive')).toBeInTheDocument(); // sentiment
    expect(screen.getByText('15 messages')).toBeInTheDocument(); // message count
    expect(screen.getByText('react')).toBeInTheDocument(); // tags
  });

  it('handles empty state correctly', () => {
    render(
      <ConversationManager
        conversations={[]}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    expect(screen.getByText('No conversations yet')).toBeInTheDocument();
    expect(screen.getByText('0 of 0')).toBeInTheDocument();
  });

  it('handles filtered empty state correctly', async () => {
    render(
      <ConversationManager
        conversations={mockConversations}
        onConversationSelect={mockOnConversationSelect}
        onConversationUpdate={mockOnConversationUpdate}
        onConversationDelete={mockOnConversationDelete}
        onConversationArchive={mockOnConversationArchive}
        onConversationExport={mockOnConversationExport}
        onConversationShare={mockOnConversationShare}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search conversations...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No conversations match your filters')).toBeInTheDocument();
      expect(screen.getByText('0 of 3')).toBeInTheDocument();
    });
  });
});