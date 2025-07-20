
'use server';
/**
 * @fileOverview A conceptual flow for exploring a topic in more depth.
 * It generates related ideas, deeper questions, and potential connections.
 *
 * - exploreConcept - A function to expand on a given concept.
 * - ExploreConceptInput - Input type for the exploreConcept function.
 * - ExploreConceptOutput - Output type for the exploreConcept function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

export const ExploreConceptInputSchema = z.object({
  mainConcept: z.string().describe('The primary concept or topic to explore.'),
  userQueryContext: z.string().optional().describe('The original user query or conversational context related to the concept. This helps tailor the exploration.'),
  existingKnowledge: z.string().optional().describe('Brief summary of existing knowledge or user facts that might be relevant for making connections.'),
});
export type ExploreConceptInput = z.infer<typeof ExploreConceptInputSchema>;

export const ExploreConceptOutputSchema = z.object({
  relatedIdeas: z.array(z.string()).describe('A list of closely related ideas or sub-topics stemming from the main concept.'),
  deeperQuestions: z.array(z.string()).describe('A list of insightful questions a user might have or that could lead to a deeper understanding of the concept.'),
  potentialConnections: z.string().optional().describe('A brief narrative on how this concept might connect to broader themes, other topics, or the provided existing knowledge/user context.'),
});
export type ExploreConceptOutput = z.infer<typeof ExploreConceptOutputSchema>;

export async function exploreConcept(input: ExploreConceptInput): Promise<ExploreConceptOutput> {
  return exploreConceptFlow(input);
}

const explorationPrompt = ai.definePrompt({
  name: 'exploreConceptPrompt',
  input: {schema: ExploreConceptInputSchema},
  output: {schema: ExploreConceptOutputSchema},
  prompt: `You are an AI assistant tasked with exploring a given concept in depth.
Based on the 'mainConcept', 'userQueryContext', and any 'existingKnowledge' provided, perform the following:
1.  Identify and list several 'relatedIdeas' or sub-topics that branch out from the 'mainConcept'.
2.  Formulate a few 'deeperQuestions' that someone interested in the 'mainConcept' (within the 'userQueryContext') might ask to gain a more profound understanding. These should be thought-provoking.
3.  If possible, provide a brief narrative for 'potentialConnections', explaining how the 'mainConcept' might connect to broader themes, other domains, or specifically to the 'userQueryContext' or 'existingKnowledge'. If no strong connections are apparent, this can be omitted.

Main Concept: {{{mainConcept}}}
User Query/Context: {{#if userQueryContext}}"{{{userQueryContext}}}"{{else}}None provided.{{/if}}
Existing Knowledge/Facts: {{#if existingKnowledge}}"{{{existingKnowledge}}}"{{else}}None provided.{{/if}}

Provide your output ONLY in the specified JSON format matching the ExploreConceptOutputSchema.
`,
});

const exploreConceptFlow = ai.defineFlow(
  {
    name: 'exploreConceptFlow',
    inputSchema: ExploreConceptInputSchema,
    outputSchema: ExploreConceptOutputSchema,
  },
  async (input) => {
    const {output} = await explorationPrompt(input);
    if (output) {
      // Ensure optional fields are truly optional if empty
      if (output.potentialConnections === "") {
        output.potentialConnections = undefined;
      }
      return output;
    }
    // Fallback if AI output is problematic
    console.error('Error in exploreConceptFlow: AI output issue. Full result:', {
        input,
        outputFromAI: output,
      });
    return {
        relatedIdeas: ["Could not generate related ideas at this time."],
        deeperQuestions: ["Could not generate deeper questions at this time."],
        potentialConnections: undefined
    };
  }
);
