"use client";

import { useCallback, useMemo } from "react";
import type { CopilotArtifact } from "../types";

interface UseArtifactManagementOptions {
  artifacts: CopilotArtifact[];
  updateArtifact: (artifactId: string, updates: Partial<CopilotArtifact>) => void;
  removeArtifact: (artifactId: string) => void;
}

export const useArtifactManagement = ({
  artifacts,
  updateArtifact,
  removeArtifact,
}: UseArtifactManagementOptions) => {
  const approveArtifact = useCallback(
    (artifactId: string) => {
      updateArtifact(artifactId, { status: "approved" });
    },
    [updateArtifact]
  );

  const rejectArtifact = useCallback(
    (artifactId: string) => {
      updateArtifact(artifactId, { status: "rejected" });
    },
    [updateArtifact]
  );

  const applyArtifact = useCallback(
    (artifactId: string) => {
      updateArtifact(artifactId, { status: "applied" });
    },
    [updateArtifact]
  );

  const activeArtifacts = useMemo(
    () => artifacts.filter((artifact) => artifact.status !== "rejected"),
    [artifacts]
  );

  return {
    artifacts: activeArtifacts,
    approveArtifact,
    rejectArtifact,
    applyArtifact,
    removeArtifact,
  };
};
