import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

// Simple mock that just returns the basic structure
vi.mock('@dnd-kit/sortable', () => ({
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: () => {},
    transform: null,
    transition: undefined,
    isDragging: false,
  })
}));

vi.mock('@dnd-kit/utilities', () => ({
  CSS: {
    Transform: {
      toString: () => 'transform: none'
    }
  }
}));

// Import after mocking
const { DraggableWidget } = await import('../DraggableWidget');

describe('DraggableWidget', () => {
  it('renders children content', () => {
    render(
      <DraggableWidget id="test-widget">
        <div>Widget Content</div>
      </DraggableWidget>
    );

    expect(screen.getByText('Widget Content')).toBeInTheDocument();
  });

  it('applies drag handle with correct attributes', () => {
    render(
      <DraggableWidget id="test-widget">
        <div>Widget Content</div>
      </DraggableWidget>
    );

    // Check for drag handle (GripVertical icon would be rendered)
    const dragHandle = screen.getByTitle('Drag to reorder');
    expect(dragHandle).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <DraggableWidget id="test-widget" className="custom-class">
        <div>Widget Content</div>
      </DraggableWidget>
    );

    const container = screen.getByText('Widget Content').closest('.group');
    expect(container).toHaveClass('custom-class');
  });

  it('shows drag handle on hover', () => {
    render(
      <DraggableWidget id="test-widget">
        <div>Widget Content</div>
      </DraggableWidget>
    );

    const dragHandle = screen.getByTitle('Drag to reorder');
    
    // The drag handle should have opacity-0 by default and opacity-100 on group hover
    expect(dragHandle).toHaveClass('opacity-0', 'group-hover:opacity-100');
  });

  it('applies correct cursor styles to drag handle', () => {
    render(
      <DraggableWidget id="test-widget">
        <div>Widget Content</div>
      </DraggableWidget>
    );

    const dragHandle = screen.getByTitle('Drag to reorder');
    expect(dragHandle).toHaveClass('cursor-grab', 'active:cursor-grabbing');
  });
});