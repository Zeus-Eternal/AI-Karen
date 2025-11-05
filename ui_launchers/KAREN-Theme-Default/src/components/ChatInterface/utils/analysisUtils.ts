import { ChatMessage, CopilotArtifact } from "../types";

export interface AnalysisSummary {
  hasArtifacts: boolean;
  artifactCount: number;
  hasErrors: boolean;
  latestArtifact?: CopilotArtifact;
}

export const summarizeAnalysisState = (
  messages: ChatMessage[],
  artifacts: CopilotArtifact[]
): AnalysisSummary => {
  const latestArtifact = artifacts[artifacts.length - 1];
  const hasErrors = messages.some(
    (message) => message.metadata?.codeAnalysis?.issues.some((issue) => issue.severity === "error")
  );
  return {
    hasArtifacts: artifacts.length > 0,
    artifactCount: artifacts.length,
    hasErrors,
    latestArtifact,
  };
};
