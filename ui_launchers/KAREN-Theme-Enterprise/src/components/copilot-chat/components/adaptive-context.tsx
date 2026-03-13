import React from 'react';
import { ExpertiseLevel } from '../types/copilot';
import { UIAdaptationPolicy, getDefaultPolicy } from './adaptive-utils';

// Context for sharing adaptation policy
export const AdaptiveInterfaceContext = React.createContext<{
  expertiseLevel: ExpertiseLevel;
  adaptationPolicy: UIAdaptationPolicy;
  isTransitioning: boolean;
  updatePolicy: (updates: Partial<UIAdaptationPolicy>) => void;
}>({
  expertiseLevel: 'intermediate',
  adaptationPolicy: getDefaultPolicy('intermediate' as ExpertiseLevel),
  isTransitioning: false,
  updatePolicy: () => {}
});

// Hook for using adaptive interface context
export const useAdaptiveInterface = () => {
  const context = React.useContext(AdaptiveInterfaceContext);
  if (!context) {
    throw new Error('useAdaptiveInterface must be used within an AdaptiveInterface');
  }
  return context;
};