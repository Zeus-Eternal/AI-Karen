/**
 * Enhanced UI Components
 * 
 * Extended shadcn/ui components with design token integration,
 * enhanced accessibility, and modern interaction patterns.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

// Button components
export { type ButtonProps as ButtonEnhancedProps } from './button-enhanced';
export { ButtonEnhanced } from './button-enhanced';
export { buttonVariants as buttonEnhancedVariants } from './button-enhanced-variants';

// Card components
export {
  CardEnhanced,
  CardHeaderEnhanced,
  CardContentEnhanced,
  CardFooterEnhanced,
  CardTitleEnhanced,
  CardDescriptionEnhanced,
  type CardEnhancedComponentProps,
  type CardHeaderEnhancedProps,
  type CardContentEnhancedProps,
  type CardFooterEnhancedProps,
} from './card-enhanced';
export { cardEnhancedVariants } from './card-enhanced-variants';

// Input components
export { type InputEnhancedProps } from './input-enhanced';
export { InputEnhanced } from './input-enhanced';
export { inputVariants } from './input-enhanced-variants';
