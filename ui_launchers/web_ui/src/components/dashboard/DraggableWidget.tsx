'use client';

import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DraggableWidgetProps {
  id: string;
  children: React.ReactNode;
  className?: string;
}

export const DraggableWidget: React.FC<DraggableWidgetProps> = ({
  id,
  children,
  className
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'relative group',
        isDragging && 'z-50 opacity-50',
        className
      )}
      {...attributes}
    >
      {/* Drag Handle */}
      <div
        {...listeners}
        className={cn(
          'absolute top-2 left-2 z-10 opacity-0 group-hover:opacity-100',
          'transition-opacity duration-200 cursor-grab active:cursor-grabbing',
          'bg-background/80 backdrop-blur-sm rounded p-1 border shadow-sm',
          'hover:bg-accent hover:text-accent-foreground'
        )}
        title="Drag to reorder"
      >
        <GripVertical className="h-3 w-3" />
      </div>

      {/* Widget Content */}
      <div className={cn(
        'transition-all duration-200',
        isDragging && 'shadow-lg ring-2 ring-primary/20'
      )}>
        {children}
      </div>
    </div>
  );
};

export default DraggableWidget;