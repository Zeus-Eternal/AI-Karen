"use client";

import { useMemo } from "react";
import type { ChatMessage, ChatSettings, CopilotAction, ChatContext } from "../types";
import { normalizeCopilotActions, filterActionsForSelection } from "../utils/copilotUtils";

interface UseCopilotIntegrationOptions {
  enabled: boolean;
  actions?: CopilotAction[];
  messages: ChatMessage[];
  settings: ChatSettings;
  context: ChatContext;
}

export const useCopilotIntegration = ({
  enabled,
  actions = [],
  messages,
  settings,
  context,
}: UseCopilotIntegrationOptions) => {
  const availableActions = useMemo(() => {
    if (!enabled || !actions) return [] as CopilotAction[];
    return filterActionsForSelection(normalizeCopilotActions(actions), context);
  }, [actions, context, enabled]);

  const isCopilotReady = enabled && settings.enableSuggestions;
  const supportsCode = enabled && settings.enableCodeAnalysis;

  const lastAssistantMessage = useMemo(
    () => messages?.slice().reverse().find((message) => message.role === "assistant"),
    [messages]
  );

  return {
    isCopilotReady,
    supportsCode,
    availableActions,
    lastAssistantMessage,
  };
};
