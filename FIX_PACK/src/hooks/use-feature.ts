'use client';

import { useContext } from 'react';
import { FeatureFlagsContext } from '@/contexts/FeatureFlagsContext';

export type FeatureFlag = 
  | 'chat.streaming'
  | 'chat.tools'
  | 'chat.edit'
  | 'chat.quick_actions'
  | 'copilot.enabled'
  | 'voice.input'
  | 'voice.output'
  | 'attachments.enabled'
  | 'emoji.picker'
  | 'analytics.detailed'
  | 'security.sanitization'
  | 'security.rbac'
  | 'performance.virtualization'
  | 'accessibility.enhanced'
  | 'telemetry.enabled'
  | 'debug.mode';

export const useFeature = (flag?: string): boolean => {
  const context = useContext(FeatureFlagsContext);
  
  if (!context) {
    console.warn('useFeature must be used within a FeatureFlagsProvider');
    return false;
  }
  
  if (!flag) {
    return false;
  }
  
  return context.isEnabled(flag as FeatureFlag);
};

export const useFeatures = () => {
  const context = useContext(FeatureFlagsContext);
  
  if (!context) {
    throw new Error('useFeatures must be used within a FeatureFlagsProvider');
  }
  
  return context;
};

export default useFeature;