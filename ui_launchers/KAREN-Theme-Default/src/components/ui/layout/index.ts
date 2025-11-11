/**
 * Modern Layout System Components
 * 
 * Export all layout components for easy importing
 * 
 * Based on requirements: 1.4, 2.1, 3.2, 8.3
 */

// Grid Container Components
export { 
  type GridContainerProps,
  type GridContainerVariants,
  type GridAreas,
  type ResponsiveValue as GridResponsiveValue,
} from './grid-container';

// Flex Container Components
export { 
  type FlexContainerProps,
  type FlexContainerVariants,
  type FlexItemProps,
  type ResponsiveValue as FlexResponsiveValue,
} from './flex-container';

// Responsive Container Components
export {
  type ResponsiveContainerProps,
  type ResponsiveContainerVariants,
  type ContainerBreakpoints,
  type ContainerSize,
  type ResponsiveValue as ContainerResponsiveValue,
} from './responsive-container';

export { useContainerQuery, useContainerSize } from './responsive-container-hooks';
export { defaultContainerBreakpoints, containerSizes } from './responsive-container-constants';

// Re-export common types
export type ResponsiveValue<T> = {
  base?: T;
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
};
