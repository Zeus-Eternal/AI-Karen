import { useContext } from 'react';
import { AdaptiveLayoutContext } from './adaptive-layout-context';

/**
 * Hook to access the adaptive layout context
 * @returns The adaptive layout context value
 */
export const useAdaptiveLayout = () => {
  const context = useContext(AdaptiveLayoutContext);
  if (!context) {
    throw new Error('useAdaptiveLayout must be used within an AdaptiveLayout');
  }
  return context;
};