import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { MemoryDetails } from '../ui/MemoryDetails';
import { Memory, MemoryType, MemoryStatus, MemoryPriority, MemorySource } from '../types';
import { render as customRender } from '@/lib/__tests__/test-utils';

// Mock the current date for consistent testing
const mockDate = new Date('2024-01-15T12:00:00Z');
vi.setSystemTime(mockDate);

describe('MemoryDetails', () => {
  const mockMemory: Memory = {
    id: 'memory-123',
    title: 'Test Memory',
    content: 'This is a test memory content',
    type: 'conversation' as MemoryType,
    status: 'active' as MemoryStatus,
    priority: 'high' as MemoryPriority,
    createdAt: new Date('2024-01-10T10:00:00Z'),
    updatedAt: new Date('2024-01-12T15:30:00Z'),
    accessedAt: new Date('2024-01-15T09:00:00Z'),
    expiresAt: new Date('2024-02-15T23:59:59Z'),
    metadata: {
      source: 'user-input' as MemorySource,
      context: 'test-context',
      relatedIds: ['memory-456', 'memory-789'],
      conversationId: 'conv-123',
      topics: [{ name: 'test-topic', confidence: 0.9 }],
      extractionMethod: 'manual',
      indexingStatus: 'indexed' as const,
      processingStatus: 'completed' as const,
      processingError: undefined,
      isEncrypted: false,
      confidence: 0.85,
      importance: 0.9,
      tags: ['test', 'important'],
      category: 'test-category',
      folder: 'test-folder',
      collection: 'test-collection',
      accessCount: 5,
    },
    size: 1024,
    hash: 'hash-123',
    version: 1,
    userId: 'user-123',
    tenantId: 'tenant-123',
  };

  const mockOnClose = vi.fn();
  const mockOnAction = vi.fn();
  const mockOnEdit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders memory details correctly', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.getByText('Test Memory')).toBeInTheDocument();
    expect(screen.getByText('This is a test memory content')).toBeInTheDocument();
    expect(screen.getByText('conversation')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
  });

  it('displays metadata correctly', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    // Check for basic metadata fields
    expect(screen.getByText('ID:')).toBeInTheDocument();
    expect(screen.getByText('Version:')).toBeInTheDocument();
    expect(screen.getByText('Size:')).toBeInTheDocument();
    expect(screen.getByText('Hash:')).toBeInTheDocument();
    expect(screen.getByText('User ID:')).toBeInTheDocument();
  });

  it('displays tags correctly', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    const testTag = screen.getByText('test');
    const importantTag = screen.getByText('important');

    expect(testTag).toBeInTheDocument();
    expect(importantTag).toBeInTheDocument();
  });

  it('displays related memories correctly', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.getByText('Related Memories')).toBeInTheDocument();
    expect(screen.getAllByText('memory-456').length).toBeGreaterThan(0);
    expect(screen.getAllByText('memory-789').length).toBeGreaterThan(0);
  });

  it('calls onClose when close button is clicked', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays expiration warning for expired memories', () => {
    const expiredMemory = {
      ...mockMemory,
      expiresAt: new Date('2024-01-10T00:00:00Z'), // Expired
    };
    
    customRender(
      <MemoryDetails
        memory={expiredMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.getByText('Expired')).toBeInTheDocument();
  });

  it('displays encrypted badge for encrypted memories', () => {
    const encryptedMemory = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        isEncrypted: true,
      },
    };
    
    customRender(
      <MemoryDetails
        memory={encryptedMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.getByText('Encrypted')).toBeInTheDocument();
  });

  it('handles memory without tags gracefully', () => {
    const memoryWithoutTags = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: [],
      },
    };
    
    customRender(
      <MemoryDetails
        memory={memoryWithoutTags}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.queryByText('test')).not.toBeInTheDocument();
  });

  it('handles memory without related memories gracefully', () => {
    const memoryWithoutRelated = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        relatedIds: [],
      },
    };
    
    customRender(
      <MemoryDetails
        memory={memoryWithoutRelated}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    expect(screen.queryByText('Related Memories')).not.toBeInTheDocument();
  });

  it('has proper ARIA labels', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    // Check for close button
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    closeButton.focus();
    expect(document.activeElement).toBe(closeButton);
  });

  it('hides actions when showActions is false', () => {
    customRender(
      <MemoryDetails
        memory={mockMemory}
        onClose={mockOnClose}
        onAction={mockOnAction}
        onEdit={mockOnEdit}
        showActions={false}
      />
    );

    expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument();
  });

  describe('Edge Cases', () => {
    it('handles memory with minimal metadata gracefully', () => {
      const memoryWithMinimalMetadata = {
        ...mockMemory,
        metadata: {},
      };
      
      customRender(
        <MemoryDetails
          memory={memoryWithMinimalMetadata}
          onClose={mockOnClose}
          onAction={mockOnAction}
          onEdit={mockOnEdit}
        />
      );

      expect(screen.getByText('Test Memory')).toBeInTheDocument();
      // Check for basic metadata fields
      expect(screen.getByText('ID:')).toBeInTheDocument();
      expect(screen.getByText('Version:')).toBeInTheDocument();
      expect(screen.getByText('Size:')).toBeInTheDocument();
      expect(screen.getByText('Hash:')).toBeInTheDocument();
      expect(screen.getByText('User ID:')).toBeInTheDocument();
    });

    it('handles memory with very long content', () => {
      const longContentMemory = {
        ...mockMemory,
        content: 'A'.repeat(1000), // Very long content
      };
      
      customRender(
        <MemoryDetails
          memory={longContentMemory}
          onClose={mockOnClose}
          onAction={mockOnAction}
          onEdit={mockOnEdit}
        />
      );

      expect(screen.getByText('A'.repeat(1000))).toBeInTheDocument();
    });

    it('displays processing status when available', () => {
      const processingMemory = {
        ...mockMemory,
        status: 'processing' as MemoryStatus,
        metadata: {
          ...mockMemory.metadata,
          processingStatus: 'processing' as const,
        },
      };
      
      customRender(
        <MemoryDetails
          memory={processingMemory}
          onClose={mockOnClose}
          onAction={mockOnAction}
          onEdit={mockOnEdit}
        />
      );

      // Check for processing status in status badge
      const processingElements = screen.getAllByText('processing');
      expect(processingElements.length).toBeGreaterThan(0);
    });

    it('displays indexing status when available', () => {
      const indexingMemory = {
        ...mockMemory,
        metadata: {
          ...mockMemory.metadata,
          indexingStatus: 'indexing' as const,
        },
      };
      
      customRender(
        <MemoryDetails
          memory={indexingMemory}
          onClose={mockOnClose}
          onAction={mockOnAction}
          onEdit={mockOnEdit}
        />
      );

      // Check for indexing status in metadata section
      const indexingElements = screen.getAllByText('indexing');
      expect(indexingElements.length).toBeGreaterThan(0);
    });
  });
});