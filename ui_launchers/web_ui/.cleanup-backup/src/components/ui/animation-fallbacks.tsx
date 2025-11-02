'use client';

import React, { ReactNode, CSSProperties } from 'react';
import { useProgressiveEnhancement } from '@/utils/progressive-enhancement';

interface AnimationFallbackProps {
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
  style?: CSSProperties;
}

/**
 * Wrapper component that provides animation fallbacks for unsupported features
 */
export function AnimationFallback({ 
  children, 
  fallback, 
  className, 
  style 
}: AnimationFallbackProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransitions && fallback) {
    return <div className={className} style={style}>{fallback}</div>;
  }

  return <div className={className} style={style}>{children}</div>;
}

/**
 * Fade animation with fallback
 */
interface FadeProps extends AnimationFallbackProps {
  show: boolean;
  duration?: number;
}

export function FadeAnimation({ 
  children, 
  show, 
  duration = 250, 
  className = '',
  style = {} 
}: FadeProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransitions) {
    // Simple show/hide fallback
    return show ? <div className={className} style={style}>{children}</div> : null;
  }

  const fadeStyle: CSSProperties = {
    ...style,
    opacity: show ? 1 : 0,
    transition: `opacity ${animation.useReducedMotion ? 0 : duration}ms ${animation.animationEasing}`,
    pointerEvents: show ? 'auto' : 'none',
  };

  return (
    <div className={className} style={fadeStyle}>
      {children}
    </div>
  );
}

/**
 * Slide animation with fallback
 */
interface SlideProps extends AnimationFallbackProps {
  show: boolean;
  direction: 'up' | 'down' | 'left' | 'right';
  distance?: number;
  duration?: number;
}

export function SlideAnimation({ 
  children, 
  show, 
  direction, 
  distance = 20, 
  duration = 250,
  className = '',
  style = {} 
}: SlideProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransforms) {
    // Simple show/hide fallback
    return show ? <div className={className} style={style}>{children}</div> : null;
  }

  const getTransform = () => {
    if (show) return 'translate3d(0, 0, 0)';
    
    switch (direction) {
      case 'up': return `translate3d(0, ${distance}px, 0)`;
      case 'down': return `translate3d(0, -${distance}px, 0)`;
      case 'left': return `translate3d(${distance}px, 0, 0)`;
      case 'right': return `translate3d(-${distance}px, 0, 0)`;
      default: return 'translate3d(0, 0, 0)';
    }
  };

  const slideStyle: CSSProperties = {
    ...style,
    opacity: show ? 1 : 0,
    transform: getTransform(),
    transition: animation.useReducedMotion 
      ? 'none' 
      : `opacity ${duration}ms ${animation.animationEasing}, transform ${duration}ms ${animation.animationEasing}`,
  };

  return (
    <div className={className} style={slideStyle}>
      {children}
    </div>
  );
}

/**
 * Scale animation with fallback
 */
interface ScaleProps extends AnimationFallbackProps {
  show: boolean;
  scale?: number;
  duration?: number;
}

export function ScaleAnimation({ 
  children, 
  show, 
  scale = 0.95, 
  duration = 200,
  className = '',
  style = {} 
}: ScaleProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransforms) {
    // Simple show/hide fallback
    return show ? <div className={className} style={style}>{children}</div> : null;
  }

  const scaleStyle: CSSProperties = {
    ...style,
    opacity: show ? 1 : 0,
    transform: show ? 'scale(1)' : `scale(${scale})`,
    transition: animation.useReducedMotion 
      ? 'none' 
      : `opacity ${duration}ms ${animation.animationEasing}, transform ${duration}ms ${animation.animationEasing}`,
  };

  return (
    <div className={className} style={scaleStyle}>
      {children}
    </div>
  );
}

/**
 * Collapse animation with fallback
 */
interface CollapseProps extends AnimationFallbackProps {
  show: boolean;
  duration?: number;
}

export function CollapseAnimation({ 
  children, 
  show, 
  duration = 300,
  className = '',
  style = {} 
}: CollapseProps) {
  const { animation } = useProgressiveEnhancement();
  const [height, setHeight] = React.useState<number | 'auto'>(show ? 'auto' : 0);
  const contentRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!animation.useTransitions) {
      setHeight(show ? 'auto' : 0);
      return;
    }

    if (show) {
      // Measure content height
      if (contentRef.current) {
        const scrollHeight = contentRef.current.scrollHeight;
        setHeight(scrollHeight);
        
        // Set to auto after animation completes
        const timer = setTimeout(() => setHeight('auto'), duration);
        return () => clearTimeout(timer);
      }
    } else {
      // First set to measured height, then to 0
      if (contentRef.current) {
        setHeight(contentRef.current.scrollHeight);
        requestAnimationFrame(() => setHeight(0));
      }
    }
  }, [show, animation.useTransitions, duration]);

  if (!animation.useTransitions) {
    // Simple show/hide fallback
    return show ? <div className={className} style={style}>{children}</div> : null;
  }

  const collapseStyle: CSSProperties = {
    ...style,
    height,
    overflow: 'hidden',
    transition: animation.useReducedMotion 
      ? 'none' 
      : `height ${duration}ms ${animation.animationEasing}`,
  };

  return (
    <div className={className} style={collapseStyle}>
      <div ref={contentRef}>
        {children}
      </div>
    </div>
  );
}

/**
 * Loading spinner with fallback
 */
interface SpinnerProps {
  size?: number;
  className?: string;
  style?: CSSProperties;
}

export function SpinnerAnimation({ 
  size = 24, 
  className = '',
  style = {} 
}: SpinnerProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransitions) {
    // Static loading indicator fallback
    return (
      <div 
        className={`inline-block ${className}`}
        style={{
          ...style,
          width: size,
          height: size,
          border: '2px solid currentColor',
          borderRadius: '50%',
          borderTopColor: 'transparent',
        }}
        aria-label="Loading"
      />
    );
  }

  const spinnerStyle: CSSProperties = {
    ...style,
    width: size,
    height: size,
    border: '2px solid currentColor',
    borderRadius: '50%',
    borderTopColor: 'transparent',
    animation: animation.useReducedMotion 
      ? 'none' 
      : 'spin 1s linear infinite',
  };

  return (
    <>
      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
      <div 
        className={`inline-block ${className}`}
        style={spinnerStyle}
        aria-label="Loading"
      />
    </>
  );
}

/**
 * Pulse animation with fallback
 */
interface PulseProps extends AnimationFallbackProps {
  duration?: number;
  intensity?: number;
}

export function PulseAnimation({ 
  children, 
  duration = 2000, 
  intensity = 0.7,
  className = '',
  style = {} 
}: PulseProps) {
  const { animation } = useProgressiveEnhancement();

  if (!animation.useTransitions) {
    // Static fallback
    return <div className={className} style={style}>{children}</div>;
  }

  const pulseStyle: CSSProperties = {
    ...style,
    animation: animation.useReducedMotion 
      ? 'none' 
      : `pulse ${duration}ms ease-in-out infinite`,
  };

  return (
    <>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: ${intensity};
          }
        }
      `}</style>
      <div className={className} style={pulseStyle}>
        {children}
      </div>
    </>
  );
}

/**
 * Bounce animation with fallback
 */
interface BounceProps extends AnimationFallbackProps {
  trigger: boolean;
  duration?: number;
}

export function BounceAnimation({ 
  children, 
  trigger, 
  duration = 600,
  className = '',
  style = {} 
}: BounceProps) {
  const { animation } = useProgressiveEnhancement();
  const [isAnimating, setIsAnimating] = React.useState(false);

  React.useEffect(() => {
    if (trigger && animation.useTransforms && !animation.useReducedMotion) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), duration);
      return () => clearTimeout(timer);
    }
  }, [trigger, animation.useTransforms, animation.useReducedMotion, duration]);

  if (!animation.useTransforms) {
    // Static fallback
    return <div className={className} style={style}>{children}</div>;
  }

  const bounceStyle: CSSProperties = {
    ...style,
    animation: isAnimating && !animation.useReducedMotion
      ? `bounce ${duration}ms ease-in-out`
      : 'none',
  };

  return (
    <>
      <style jsx>{`
        @keyframes bounce {
          0%, 20%, 53%, 80%, 100% {
            transform: translate3d(0, 0, 0);
          }
          40%, 43% {
            transform: translate3d(0, -8px, 0);
          }
          70% {
            transform: translate3d(0, -4px, 0);
          }
          90% {
            transform: translate3d(0, -2px, 0);
          }
        }
      `}</style>
      <div className={className} style={bounceStyle}>
        {children}
      </div>
    </>
  );
}
