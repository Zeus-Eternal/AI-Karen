import * as React from 'react';

import FocusIndicator, { type FocusIndicatorProps } from './focus-indicators';

/**
 * Higher-order component helper that wraps the provided component with the FocusIndicator.
 */
type ComponentWithRef<P, RefType> = React.ForwardRefExoticComponent<
  React.PropsWithoutRef<P> & React.RefAttributes<RefType>
>;

export function withFocusIndicator<P extends object, RefType = unknown>(
  Component: ComponentWithRef<P, RefType>,
  indicatorProps?: Partial<FocusIndicatorProps>
) {
  const WrappedComponent = React.forwardRef<RefType, React.PropsWithoutRef<P>>((props, ref) => (
    <FocusIndicator {...indicatorProps}>
      <Component {...props} ref={ref} />
    </FocusIndicator>
  ));

  const componentName = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withFocusIndicator(${componentName})`;

  return WrappedComponent as React.ComponentType<any>;
}
