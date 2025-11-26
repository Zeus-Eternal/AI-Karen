import { useContext } from 'react';
import { ArtifactSystemContext } from './artifact-system-context';
import { CopilotArtifact } from '../types/copilot';

/**
 * Hook for using artifact system context
 * @returns The artifact system context value
 */
export const useArtifactSystem = () => {
  const context = useContext(ArtifactSystemContext);
  if (!context) {
    throw new Error('useArtifactSystem must be used within an ArtifactSystemProvider');
  }
  return context;
};

/**
 * Hook for getting all artifacts
 * @returns Array of all artifacts
 */
export const useArtifacts = (): CopilotArtifact[] => {
  const { artifacts } = useArtifactSystem();
  return artifacts;
};

/**
 * Hook for getting active artifacts
 * @returns Array of active artifact IDs
 */
export const useActiveArtifacts = (): string[] => {
  const { activeArtifacts } = useArtifactSystem();
  return activeArtifacts;
};

/**
 * Hook for getting shared artifacts
 * @returns Array of shared artifacts
 */
export const useSharedArtifacts = (): CopilotArtifact[] => {
  const { getSharedArtifacts } = useArtifactSystem();
  return getSharedArtifacts();
};