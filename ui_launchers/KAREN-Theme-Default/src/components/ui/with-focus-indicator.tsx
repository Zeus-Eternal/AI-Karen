import * as React from 'react';

import FocusIndicator, { type FocusIndicatorProps } from './focus-indicators';

/**
 * Higher-order component helper that wraps the provided component with the FocusIndicator.
 */
export function withFocusIndicator<P extends object, RefType = unknown>(
  Component: React.ComponentType<P & React.RefAttributes<RefType>>,
  indicatorProps?: Partial<FocusIndicatorProps>
) {
  const WrappedComponent = React.forwardRef<RefType, P>((props, ref) => (
    <FocusIndicator {...indicatorProps}>
      {React.createElement(
        Component as React.ComponentType<P & { ref?: React.Ref<RefType> }>,
        { ...props, ref }
      )}
    </FocusIndicator>
  ));

  const componentName = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withFocusIndicator(${componentName})`;

  return WrappedComponent;
}
