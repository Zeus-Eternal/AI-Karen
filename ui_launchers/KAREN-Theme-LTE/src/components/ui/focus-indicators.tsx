import React from 'react';

export type FocusIndicatorVariant = 'default' | 'subtle' | 'strong' | 'outline' | 'glow';
export type FocusIndicatorColor = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

export interface FocusIndicatorProps {
  visible: boolean;
  variant?: FocusIndicatorVariant;
  color?: FocusIndicatorColor;
  className?: string;
  children?: React.ReactNode;
}

export const FocusIndicator: React.FC<FocusIndicatorProps> = ({
  visible,
  variant = 'default',
  color = 'primary',
  className = '',
  children,
}) => {
  if (!visible) {
    return <>{children}</>;
  }

  const getVariantStyles = (): string => {
    switch (variant) {
      case 'subtle':
        return 'focus-indicator-subtle';
      case 'strong':
        return 'focus-indicator-strong';
      case 'outline':
        return 'focus-indicator-outline';
      case 'glow':
        return 'focus-indicator-glow';
      default:
        return 'focus-indicator-default';
    }
  };

  const getColorStyles = (): string => {
    switch (color) {
      case 'primary':
        return 'focus-indicator-primary';
      case 'secondary':
        return 'focus-indicator-secondary';
      case 'success':
        return 'focus-indicator-success';
      case 'warning':
        return 'focus-indicator-warning';
      case 'error':
        return 'focus-indicator-error';
      case 'info':
        return 'focus-indicator-info';
      default:
        return 'focus-indicator-primary';
    }
  };

  const indicatorClassName = [
    'focus-indicator',
    getVariantStyles(),
    getColorStyles(),
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={indicatorClassName} data-focus-visible="true">
      {children}
      <style jsx>{`
        .focus-indicator {
          position: relative;
        }
        
        .focus-indicator:focus-visible {
          outline: 2px solid;
          outline-offset: 2px;
          border-radius: 4px;
        }
        
        .focus-indicator-default:focus-visible {
          outline-color: hsl(211, 98%, 52%);
        }
        
        .focus-indicator-subtle:focus-visible {
          outline-color: hsl(211, 98%, 52%, 0.5);
          outline-width: 1px;
        }
        
        .focus-indicator-strong:focus-visible {
          outline-color: hsl(211, 98%, 52%);
          outline-width: 3px;
          outline-offset: 3px;
        }
        
        .focus-indicator-outline:focus-visible {
          outline-color: hsl(211, 98%, 52%);
          outline-style: dashed;
        }
        
        .focus-indicator-glow:focus-visible {
          box-shadow: 0 0 0 3px hsl(211, 98%, 52%, 0.4),
                      0 0 0 6px hsl(211, 98%, 52%, 0.2);
        }
        
        .focus-indicator-primary:focus-visible {
          outline-color: hsl(211, 98%, 52%);
        }
        
        .focus-indicator-secondary:focus-visible {
          outline-color: hsl(210, 40%, 96%);
        }
        
        .focus-indicator-success:focus-visible {
          outline-color: hsl(142, 76%, 36%);
        }
        
        .focus-indicator-warning:focus-visible {
          outline-color: hsl(38, 92%, 50%);
        }
        
        .focus-indicator-error:focus-visible {
          outline-color: hsl(0, 84%, 60%);
        }
        
        .focus-indicator-info:focus-visible {
          outline-color: hsl(199, 89%, 48%);
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
          .focus-indicator:focus-visible {
            outline-width: 3px;
            outline-color: CanvasText;
            background-color: Canvas;
          }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .focus-indicator-glow:focus-visible {
            box-shadow: none;
            outline-color: hsl(211, 98%, 52%);
            outline-width: 2px;
          }
        }
      `}</style>
    </div>
  );
};

export default FocusIndicator;