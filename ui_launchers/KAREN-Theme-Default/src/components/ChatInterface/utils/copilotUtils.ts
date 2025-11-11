import { DEFAULT_COPILOT_ACTION_CATEGORIES } from "../constants";
import type { CopilotAction, ChatContext } from "../types";

export const normalizeCopilotActions = (actions: CopilotAction[]) => {
  const categoryOrder = DEFAULT_COPILOT_ACTION_CATEGORIES;
  return actions.slice().sort((a, b) => {
    const categoryDiff =
      categoryOrder.indexOf(a.category as unknown) -
      categoryOrder.indexOf(b.category as unknown);
    if (categoryDiff !== 0) return categoryDiff;
    return a.title.localeCompare(b.title);
  });
};

export const createActionContextSummary = (context: ChatContext) => {
  if (!context) return "";
  const parts: string[] = [];
  if (context.selectedText) {
    parts.push(`Selected text length: ${context.selectedText.length}`);
  }
  if (context.codeContext?.hasCode) {
    parts.push(`Code language: ${context.codeContext.language ?? "unknown"}`);
  }
  if (context.conversationContext?.intent) {
    parts.push(`Intent: ${context.conversationContext.intent}`);
  }
  return parts.join(" | ");
};

export const injectContextIntoPrompt = (
  action: CopilotAction,
  context: ChatContext
) => {
  if (!context) return action.prompt;
  const contextSummary = createActionContextSummary(context);
  if (!contextSummary) return action.prompt;
  return `${action.prompt}\n\nContext: ${contextSummary}`;
};

export const filterActionsForSelection = (
  actions: CopilotAction[],
  context: ChatContext
) => {
  if (!context?.selectedText) {
    return actions.filter((action) => !action.requiresSelection);
  }
  return actions;
};
