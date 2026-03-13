import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryCard } from '../ui/MemoryCard';
import { Memory } from '../types';
import { createMockMemory } from '../../../lib/__tests__/test-utils';

describe('MemoryCard', () => {
  const mockMemory = createMockMemory();
  const mockOnSelect = vi.fn();
  const mockOnAction = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with default props', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    // Should render the card with title and content
    expect(screen.getByText(mockMemory.title || 'Memory Details')).toBeInTheDocument();
    expect(screen.getByText(mockMemory.content.substring(0, 200))).toBeInTheDocument();
    
    // Should render type, status, and priority badges
    expect(screen.getByText(mockMemory.type)).toBeInTheDocument();
    expect(screen.getByText(mockMemory.status)).toBeInTheDocument();
    expect(screen.getByText(mockMemory.priority)).toBeInTheDocument();
  });

  it('displays memory type with correct styling', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const typeBadge = screen.getByText(mockMemory.type);
    expect(typeBadge).toBeInTheDocument();
    expect(typeBadge).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  it('displays memory status with correct styling', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const statusBadge = screen.getByText(mockMemory.status);
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('displays memory priority with correct styling', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const priorityBadge = screen.getByText(mockMemory.priority);
    expect(priorityBadge).toBeInTheDocument();
    expect(priorityBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('shows metadata when showMetadata is true', () => {
    const memoryWithMetadata = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: ['tag1', 'tag2', 'tag3'],
        category: 'test-category',
        folder: 'test-folder',
        collection: 'test-collection',
        confidence: 0.8,
        importance: 0.7,
        accessCount: 5
      }
    };
    
    render(<MemoryCard memory={memoryWithMetadata} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={true} />);
    
    // Should show tags
    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
    expect(screen.getByText('tag3')).toBeInTheDocument();
    
    // Should show category, folder, and collection
    expect(screen.getByText('test-category')).toBeInTheDocument();
    expect(screen.getByText('test-folder')).toBeInTheDocument();
    expect(screen.getByText('test-collection')).toBeInTheDocument();
    
    // Should show confidence and importance
    expect(screen.getByText('80% conf.')).toBeInTheDocument();
    expect(screen.getByText('70% imp.')).toBeInTheDocument();
    
    // Should show access count
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('hides metadata when showMetadata is false', () => {
    const memoryWithMetadata = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: ['tag1', 'tag2'],
        category: 'test-category'
      }
    };
    
    render(<MemoryCard memory={memoryWithMetadata} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={false} />);
    
    // Should not show tags, category, etc.
    expect(screen.queryByText('tag1')).not.toBeInTheDocument();
    expect(screen.queryByText('test-category')).not.toBeInTheDocument();
  });

  it('applies compact styling when compact is true', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} compact={true} />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    expect(card).toHaveClass('p-3');
    
    // Should not show priority badge in compact mode
    expect(screen.queryByText(mockMemory.priority)).not.toBeInTheDocument();
  });

  it('applies selected styling when isSelected is true', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} isSelected={true} />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    expect(card).toHaveClass('ring-2', 'ring-primary');
  });

  it('applies expired styling when memory is expired', () => {
    const expiredMemory = {
      ...mockMemory,
      expiresAt: new Date(Date.now() - 1000) // Expired 1 second ago
    };
    
    render(<MemoryCard memory={expiredMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    expect(card).toHaveClass('opacity-60');
    expect(screen.getByText('Expired')).toBeInTheDocument();
  });

  it('shows near expiry warning when memory is near expiry', () => {
    const nearExpiryMemory = {
      ...mockMemory,
      expiresAt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000) // Expires in 3 days
    };
    
    render(<MemoryCard memory={nearExpiryMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    expect(screen.getByText(/Expires/i)).toBeInTheDocument();
  });

  it('shows encryption indicator when memory is encrypted', () => {
    const encryptedMemory = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        isEncrypted: true
      }
    };
    
    render(<MemoryCard memory={encryptedMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    // Check for encryption icon (no text, just icon)
    const encryptionIcon = document.querySelector('svg[viewBox="0 0 24 24"] path[d*="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"]');
    expect(encryptionIcon).toBeInTheDocument();
  });

  it('calls onSelect when card is clicked', async () => {
    const user = userEvent.setup();
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    if (card) {
      await user.click(card);
    }
    
    expect(mockOnSelect).toHaveBeenCalledWith(mockMemory);
  });

  it('shows action menu when onAction is provided', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    // Should show the more options button
    const moreButton = screen.getByRole('button', { name: '' });
    expect(moreButton).toBeInTheDocument();
  });

  it('handles different memory types', () => {
    const conversationMemory = { ...mockMemory, type: 'conversation' as const };
    render(<MemoryCard memory={conversationMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const typeBadge = screen.getByText('conversation');
    expect(typeBadge).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  it('handles different memory statuses', () => {
    const archivedMemory = { ...mockMemory, status: 'archived' as const };
    render(<MemoryCard memory={archivedMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const statusBadge = screen.getByText('archived');
    expect(statusBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('handles different memory priorities', () => {
    const criticalMemory = { ...mockMemory, priority: 'critical' as const };
    render(<MemoryCard memory={criticalMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const priorityBadge = screen.getByText('critical');
    expect(priorityBadge).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('truncates content in compact mode', () => {
    const longContentMemory = {
      ...mockMemory,
      content: 'A'.repeat(300) // Long content
    };
    
    render(<MemoryCard memory={longContentMemory} onSelect={mockOnSelect} onAction={mockOnAction} compact={true} />);
    
    // Should truncate to 100 characters in compact mode
    const contentElement = screen.getByText(/A+/);
    expect(contentElement.textContent).toContain('...');
    expect(contentElement.textContent?.length).toBeLessThanOrEqual(103); // 100 chars + "..."
  });

  it('truncates content in normal mode', () => {
    const longContentMemory = {
      ...mockMemory,
      content: 'A'.repeat(300) // Long content
    };
    
    render(<MemoryCard memory={longContentMemory} onSelect={mockOnSelect} onAction={mockOnAction} compact={false} />);
    
    // Should truncate to 200 characters in normal mode
    const contentElement = screen.getByText(/A+/);
    expect(contentElement.textContent).toContain('...');
    expect(contentElement.textContent?.length).toBeLessThanOrEqual(203); // 200 chars + "..."
  });

  it('limits tags displayed in compact mode', () => {
    const memoryWithManyTags = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5']
      }
    };
    
    render(<MemoryCard memory={memoryWithManyTags} onSelect={mockOnSelect} onAction={mockOnAction} compact={true} showMetadata={true} />);
    
    // Should show only first 2 tags in compact mode
    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
    expect(screen.queryByText('tag3')).not.toBeInTheDocument();
    
    // Should show "+3 more" indicator
    expect(screen.getByText('+3')).toBeInTheDocument();
  });

  it('limits tags displayed in normal mode', () => {
    const memoryWithManyTags = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5']
      }
    };
    
    render(<MemoryCard memory={memoryWithManyTags} onSelect={mockOnSelect} onAction={mockOnAction} compact={false} showMetadata={true} />);
    
    // Should show only first 3 tags in normal mode
    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
    expect(screen.getByText('tag3')).toBeInTheDocument();
    expect(screen.queryByText('tag4')).not.toBeInTheDocument();
    
    // Should show "+2 more" indicator
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('displays size information correctly', () => {
    const largeMemory = {
      ...mockMemory,
      size: 2048 // 2KB
    };
    
    render(<MemoryCard memory={largeMemory} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={true} />);
    
    expect(screen.getByText('2.0KB')).toBeInTheDocument();
  });

  it('displays version information when version > 1', () => {
    const versionedMemory = {
      ...mockMemory,
      version: 2
    };
    
    render(<MemoryCard memory={versionedMemory} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={true} />);
    
    expect(screen.getByText('v2')).toBeInTheDocument();
  });

  it('is accessible with proper ARIA attributes', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('cursor-pointer');
  });

  it('applies custom className', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} className="custom-class" />);
    
    const card = screen.getByText(mockMemory.title || 'Memory Details').closest('.rounded-lg');
    expect(card).toHaveClass('custom-class');
  });

  it('handles missing title gracefully', () => {
    const memoryWithoutTitle = {
      ...mockMemory,
      title: undefined
    };
    
    render(<MemoryCard memory={memoryWithoutTitle} onSelect={mockOnSelect} onAction={mockOnAction} />);
    
    // Should not crash and should not show title
    expect(screen.queryByText(mockMemory.title || 'Memory Details')).not.toBeInTheDocument();
  });

  it('handles empty tags array gracefully', () => {
    const memoryWithEmptyTags = {
      ...mockMemory,
      metadata: {
        ...mockMemory.metadata,
        tags: []
      }
    };
    
    render(<MemoryCard memory={memoryWithEmptyTags} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={true} />);
    
    // Should not show any tags
    expect(screen.queryByText(/\+/)).not.toBeInTheDocument();
  });

  it('displays relative time for updatedAt', () => {
    render(<MemoryCard memory={mockMemory} onSelect={mockOnSelect} onAction={mockOnAction} showMetadata={true} />);
    
    // Should show a relative time (exact text depends on current time)
    const timeElement = document.querySelector('svg[viewBox="0 0 24 24"] + span');
    expect(timeElement).toBeInTheDocument();
    expect(timeElement?.textContent).toMatch(/\d+ \w+ ago/);
  });
});