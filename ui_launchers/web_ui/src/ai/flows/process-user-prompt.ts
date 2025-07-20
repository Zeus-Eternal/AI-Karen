// This file is deprecated.
// Its functionality has been split into:
// - src/ai/flows/decide-action-flow.ts
// - src/ai/flows/generate-final-response-flow.ts
// - src/ai/tools/core-tools.ts
//
// It is kept here temporarily to avoid breaking existing imports if any,
// but should be removed once all references are updated.
// The Genkit server (dev.ts) no longer imports this file.
'use server';

/**
 * @deprecated This flow is deprecated. Use decideActionFlow and generateFinalResponseFlow instead.
 */
import {z} from 'genkit';

export const ProcessUserPromptInputSchema = z.object({
  prompt: z.string(),
});
export type ProcessUserPromptInput = z.infer<typeof ProcessUserPromptInputSchema>;

export const ProcessUserPromptOutputSchema = z.object({
  response: z.string(),
});
export type ProcessUserPromptOutput = z.infer<typeof ProcessUserPromptOutputSchema>;

export async function processUserPrompt(input: ProcessUserPromptInput): Promise<ProcessUserPromptOutput> {
  console.warn("DEPRECATED: processUserPrompt flow was called. Please update to use decideAction and generateFinalResponse flows.");
  return { response: "This AI flow is outdated. Please contact support." };
}
