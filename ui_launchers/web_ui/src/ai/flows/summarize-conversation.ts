
'use server';
/**
 * @fileOverview Summarizes a conversation into key points and decisions.
 *
 * - summarizeConversation - A function that summarizes a conversation.
 * - SummarizeConversationInput - The input type for the summarizeConversation function.
 * - SummarizeConversationOutput - The return type for the summarizeConversation function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const SummarizeConversationInputSchema = z.object({
  conversationHistory: z
    .string()
    .describe('The complete conversation history to summarize.'),
});
export type SummarizeConversationInput = z.infer<
  typeof SummarizeConversationInputSchema
>;

const SummarizeConversationOutputSchema = z.object({
  summary: z.string().describe('A concise summary of the conversation.'),
});
export type SummarizeConversationOutput = z.infer<
  typeof SummarizeConversationOutputSchema
>;

export async function summarizeConversation(
  input: SummarizeConversationInput
): Promise<SummarizeConversationOutput> {
  return summarizeConversationFlow(input);
}

const prompt = ai.definePrompt({
  name: 'summarizeConversationPrompt',
  input: {schema: SummarizeConversationInputSchema},
  output: {schema: SummarizeConversationOutputSchema},
  prompt: `Summarize the following conversation into key points and decisions.\n\nConversation History:\n{{{conversationHistory}}}`,
});

const summarizeConversationFlow = ai.defineFlow(
  {
    name: 'summarizeConversationFlow',
    inputSchema: SummarizeConversationInputSchema,
    outputSchema: SummarizeConversationOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    if (!output || !output.summary) {
      console.error("summarizeConversationFlow did not return the expected output format.", {input, output});
      return { summary: "Could not generate a summary at this time." };
    }
    return output;
  }
);
