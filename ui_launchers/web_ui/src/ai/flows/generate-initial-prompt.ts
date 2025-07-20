// src/ai/flows/generate-initial-prompt.ts
'use server';

/**
 * @fileOverview Generates an initial prompt for a new user based on their desired AI assistant type.
 *
 * - generateInitialPrompt - A function that generates the initial prompt.
 * - GenerateInitialPromptInput - The input type for the generateInitialPrompt function.
 * - GenerateInitialPromptOutput - The return type for the generateInitialPrompt function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateInitialPromptInputSchema = z.object({
  assistantType: z
    .string()
    .describe("The desired type of AI assistant (e.g., 'a helpful coding assistant' or 'a creative writing partner')."),
});
export type GenerateInitialPromptInput = z.infer<typeof GenerateInitialPromptInputSchema>;

const GenerateInitialPromptOutputSchema = z.object({
  initialPrompt: z.string().describe('The generated initial prompt for the assistant.'),
});
export type GenerateInitialPromptOutput = z.infer<typeof GenerateInitialPromptOutputSchema>;

export async function generateInitialPrompt(input: GenerateInitialPromptInput): Promise<GenerateInitialPromptOutput> {
  return generateInitialPromptFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateInitialPromptPrompt',
  input: {schema: GenerateInitialPromptInputSchema},
  output: {schema: GenerateInitialPromptOutputSchema},
  prompt: `You are an AI assistant that helps users get started with their AI assistant.
Based on the type of AI assistant the user wants, generate an engaging and open-ended initial prompt that they can use to start interacting with the assistant.
The response should ONLY be the prompt itself, with no additional conversational text.

Assistant Type: {{{assistantType}}}

Initial Prompt:`,
});

const generateInitialPromptFlow = ai.defineFlow(
  {
    name: 'generateInitialPromptFlow',
    inputSchema: GenerateInitialPromptInputSchema,
    outputSchema: GenerateInitialPromptOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    if (!output || !output.initialPrompt) {
      console.error("GenerateInitialPromptFlow did not return the expected output format.", {input, output});
      return { initialPrompt: "Tell me about your day." }; // Fallback
    }
    return output;
  }
);
