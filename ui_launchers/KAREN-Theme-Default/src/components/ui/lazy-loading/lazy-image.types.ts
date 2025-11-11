import type React from 'react';

export interface LazyImageProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'loading'> {
  src: string;
  alt: string;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  placeholder?: string;
  blurDataURL?: string;
  onLoad?: () => void;
  onError?: () => void;
  className?: string;
}
