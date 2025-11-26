import React from 'react';
import { CopilotArtifact } from '../types/copilot';

interface ArtifactSystemState {
  artifacts: CopilotArtifact[];
  activeArtifacts: string[]; // IDs of active artifacts
  artifactHistory: {
    artifactId: string;
    action: 'created' | 'updated' | 'deleted' | 'viewed';
    timestamp: Date;
    userId?: string;
  }[];
  artifactTemplates: {
    id: string;
    name: string;
    description: string;
    type: CopilotArtifact['type'];
    template: string;
    metadata: Record<string, unknown>;
  }[];
  isLoading: boolean;
  error: string | null;
}

export interface ArtifactSystemContext extends ArtifactSystemState {
  // Artifact management
  createArtifact: (artifact: Omit<CopilotArtifact, 'id'>) => Promise<string>;
  updateArtifact: (id: string, updates: Partial<CopilotArtifact>) => Promise<void>;
  deleteArtifact: (id: string) => Promise<void>;
  viewArtifact: (id: string) => Promise<void>;
  
  // Artifact generation
  generateArtifact: (
    type: CopilotArtifact['type'],
    prompt: string,
    context?: import('../types/copilot').EnhancedContext
  ) => Promise<string>;
  
  // Artifact templates
  getArtifactTemplates: () => ArtifactSystemState['artifactTemplates'];
  createArtifactTemplate: (template: Omit<ArtifactSystemState['artifactTemplates'][0], 'id'>) => Promise<string>;
  updateArtifactTemplate: (id: string, updates: Partial<ArtifactSystemState['artifactTemplates'][0]>) => Promise<void>;
  deleteArtifactTemplate: (id: string) => Promise<void>;
  
  // Artifact collaboration
  shareArtifact: (id: string, userIds: string[]) => Promise<void>;
  unshareArtifact: (id: string, userIds: string[]) => Promise<void>;
  getSharedArtifacts: () => CopilotArtifact[];
  
  // Artifact versioning
  createArtifactVersion: (id: string) => Promise<string>;
  getArtifactVersions: (id: string) => CopilotArtifact[];
  revertArtifactVersion: (id: string, versionId: string) => Promise<void>;
  
  // Artifact state
  getArtifact: (id: string) => CopilotArtifact | undefined;
  getArtifactContent: (id: string) => string;
  isArtifactActive: (id: string) => boolean;
  
  // Artifact history
  getArtifactHistory: (id?: string) => ArtifactSystemState['artifactHistory'];
  clearArtifactHistory: () => void;
  
  // Error handling
  clearError: () => void;
}

const defaultArtifactSystemState: ArtifactSystemState = {
  artifacts: [],
  activeArtifacts: [],
  artifactHistory: [],
  artifactTemplates: [],
  isLoading: false,
  error: null,
};

// Create context
export const ArtifactSystemContext = React.createContext<ArtifactSystemContext>({
  ...defaultArtifactSystemState,
  createArtifact: async () => '',
  updateArtifact: async () => {},
  deleteArtifact: async () => {},
  viewArtifact: async () => {},
  generateArtifact: async () => '',
  getArtifactTemplates: () => [],
  createArtifactTemplate: async () => '',
  updateArtifactTemplate: async () => {},
  deleteArtifactTemplate: async () => {},
  shareArtifact: async () => {},
  unshareArtifact: async () => {},
  getSharedArtifacts: () => [],
  createArtifactVersion: async () => '',
  getArtifactVersions: () => [],
  revertArtifactVersion: async () => {},
  getArtifact: () => undefined,
  getArtifactContent: () => '',
  isArtifactActive: () => false,
  getArtifactHistory: () => [],
  clearArtifactHistory: () => {},
  clearError: () => {},
});