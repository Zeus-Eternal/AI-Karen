import React from 'react';
import { ArtifactSystemContext } from './artifact-system-context';

/**
 * Hook to use the ArtifactSystem
 */
export const useArtifactSystem = () => {
  const context = React.useContext(ArtifactSystemContext);
  if (!context) {
    throw new Error('useArtifactSystem must be used within an ArtifactSystemProvider');
  }
  return context;
};

/**
 * Hook to get artifacts
 */
export const useArtifacts = () => {
  const { artifacts } = useArtifactSystem();
  return artifacts;
};

/**
 * Hook to get active artifacts
 */
export const useActiveArtifacts = () => {
  const { activeArtifacts } = useArtifactSystem();
  return activeArtifacts;
};

/**
 * Hook to get artifact templates
 */
export const useArtifactTemplates = () => {
  const { getArtifactTemplates } = useArtifactSystem();
  return getArtifactTemplates();
};

/**
 * Hook to get artifact history
 */
export const useArtifactHistory = () => {
  const { getArtifactHistory } = useArtifactSystem();
  return getArtifactHistory();
};