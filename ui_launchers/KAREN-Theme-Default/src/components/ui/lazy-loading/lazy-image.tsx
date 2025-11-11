"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ImageIcon, AlertCircle } from 'lucide-react';

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

const DefaultPlaceholder: React.FC<{ className?: string }> = ({ className }) => (
  <div className={`flex items-center justify-center bg-muted ${className}`}>
    <ImageIcon className="h-8 w-8 text-muted-foreground " />
  </div>
);

const DefaultErrorFallback: React.FC<{ className?: string }> = ({ className }) => (
  <div className={`flex items-center justify-center bg-muted ${className}`}>
    <AlertCircle className="h-8 w-8 text-destructive " />
  </div>
);

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  fallback,
  errorFallback,
  threshold = 0.1,
  rootMargin = '50px',
  placeholder,
  blurDataURL,
  onLoad,
  onError,
  className = '',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Intersection Observer for lazy loading
  useEffect(() => {
    const currentImgRef = imgRef.current;
    
    if (!currentImgRef) return;

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          setIsLoading(true);
          observerRef.current?.unobserve(currentImgRef);
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    observerRef.current.observe(currentImgRef);

    return () => {
      if (observerRef.current && currentImgRef) {
        observerRef.current.unobserve(currentImgRef);
      }
    };
  }, [threshold, rootMargin]);

  const handleLoad = () => {
    setIsLoaded(true);
    setIsLoading(false);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
    onError?.();
  };

  const showPlaceholder = !isInView || (!isLoaded && !hasError);
  const showError = hasError && isInView;
  const showImage = isInView && !hasError;

  const resolvedPlaceholder =
    fallback ??
    (placeholder ? (
      <div className="flex h-full w-full items-center justify-center bg-muted text-muted-foreground">
        {placeholder}
      </div>
    ) : (
      <DefaultPlaceholder className="w-full h-full" />
    ));

  return (
    <div className={`relative overflow-hidden ${className}`} ref={imgRef}>
      {/* Placeholder */}
      {showPlaceholder && (
        <motion.div
          className="absolute inset-0"
          initial={{ opacity: 1 }}
          animate={{ opacity: isLoading ? 0.7 : 1 }}
          transition={{ duration: 0.2 }}
        >
          {resolvedPlaceholder}
          {blurDataURL && (
            <img
              src={blurDataURL}
              alt=""
              className="absolute inset-0 w-full h-full object-cover blur-sm"
              aria-hidden="true"
            />
          )}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin " />
            </div>
          )}
        </motion.div>
      )}

      {/* Error fallback */}
      {showError && (
        <motion.div
          className="absolute inset-0"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {errorFallback || <DefaultErrorFallback className="w-full h-full" />}
        </motion.div>
      )}

      {/* Actual image */}
      {showImage && (
        <motion.img
          src={src}
          alt={alt}
          className={`w-full h-full object-cover ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={handleLoad}
          onError={handleError}
          initial={{ opacity: 0 }}
          animate={{ opacity: isLoaded ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          {...(Object.fromEntries(
            Object.entries(props).filter(([key]) => 
              !key.startsWith('onDrag') && 
              !key.startsWith('onDrop') && 
              key !== 'draggable'
            )
          ))}
        />
      )}
    </div>
  );
};

export default LazyImage;
