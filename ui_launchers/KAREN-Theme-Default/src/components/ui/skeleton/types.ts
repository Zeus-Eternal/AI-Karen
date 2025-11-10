import type { ReactNode } from 'react';

export interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: 'default' | 'rounded' | 'circular';
  animated?: boolean;
  children?: ReactNode;
}

export interface SkeletonTextProps {
  lines?: number;
  className?: string;
  animated?: boolean;
  variant?: 'paragraph' | 'heading' | 'caption';
}

export interface SkeletonCardProps {
  className?: string;
  animated?: boolean;
  showImage?: boolean;
  showAvatar?: boolean;
  showActions?: boolean;
  imageHeight?: string;
}

export interface SkeletonAvatarProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  animated?: boolean;
}

export interface SkeletonButtonProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'outline' | 'ghost';
  className?: string;
  animated?: boolean;
  width?: string | number;
}

export interface SkeletonTableProps {
  rows?: number;
  columns?: number;
  className?: string;
  animated?: boolean;
  showHeader?: boolean;
}
