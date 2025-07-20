// Implemented the Genkit flow for the LocalAiResponse story, enabling local AI processing for privacy.
'use server';
/**
 * @fileOverview A local AI response agent.
 *
 * - localAiResponse - A function that handles the local AI response process.
 * - LocalAiResponseInput - The input type for the localAiResponse function.
 * - LocalAiResponseOutput - The return type for the localAiResponse function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const LocalAiResponseInputSchema = z.object({
  prompt: z.string().describe('The prompt for the local AI assistant.'),
});
export type LocalAiResponseInput = z.infer<typeof LocalAiResponseInputSchema>;

const LocalAiResponseOutputSchema = z.object({
  response: z.string().describe('The response from the local AI assistant.'),
});
export type LocalAiResponseOutput = z.infer<typeof LocalAiResponseOutputSchema>;

export async function localAiResponse(input: LocalAiResponseInput): Promise<LocalAiResponseOutput> {
  return localAiResponseFlow(input);
}

const prompt = ai.definePrompt({
  name: 'localAiResponsePrompt',
  input: {schema: LocalAiResponseInputSchema},
  output: {schema: LocalAiResponseOutputSchema},
  prompt: `You are a local AI assistant processing the following prompt: {{{prompt}}}.\nGenerate a response based on the prompt.`,
});

const localAiResponseFlow = ai.defineFlow(
  {
    name: 'localAiResponseFlow',
    inputSchema: LocalAiResponseInputSchema,
    outputSchema: LocalAiResponseOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
