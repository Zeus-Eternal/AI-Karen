/**
 * Mock for @radix-ui/react-progress to resolve module resolution issues
 */

import React from 'react';

interface ProgressRootProps {
  className?: string;
  value?: number;
  [key: string]: any;
}

interface ProgressIndicatorProps {
  className?: string;
  style?: React.CSSProperties;
  [key: string]: any;
}

const Root = React.forwardRef<any, ProgressRootProps>(({ className, value, ...props }, ref) =>
  React.createElement('div', {
      ref,
      className,
      'data-value': value,
      ...props
    })
);

const Indicator = React.forwardRef<any, ProgressIndicatorProps>(({ className, style, ...props }, ref) =>
  React.createElement('div', {
      ref,
      className,
      style,
      ...props
    })
);

const ProgressPrimitive = {
  Root,
  Indicator,
};

// Add displayName to components
ProgressPrimitive.Root.displayName = 'ProgressPrimitive.Root';
ProgressPrimitive.Indicator.displayName = 'ProgressPrimitive.Indicator';

export { ProgressPrimitive };
export default ProgressPrimitive;