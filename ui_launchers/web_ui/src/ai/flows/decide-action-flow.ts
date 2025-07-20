
'use server';
/**
 * @fileOverview Acts as the central cognitive core for Karen AI, processing user input and context.
 * This flow models a "human-like" decision-making process:
 * - It integrates various inputs from conceptually distinct memory and knowledge components: user query, conversation history (short-term memory), learned user facts (long-term memory), user preferences, and custom persona instructions (core directives).
 * - It determines the optimal next step: providing a direct conversational response or identifying the need to use a specific tool.
 * - It dynamically adapts Karen's persona and response strategy based on this synthesis, aiming for insightful and forward-thinking interaction.
 * - It can proactively offer suggestions or identify new facts to remember, contributing to an evolving understanding of the user.
 * This flow serves as the foundational "mind" of Karen AI, designed to be extensible and adaptable as a platform for various AI-driven interactions.
 * It is a production-level component critical to Karen AI's operation.
 *
 * - decideAction - The primary function that orchestrates this cognitive process.
 * - DecideActionInput - The comprehensive input type for the decideAction function.
 * - DecideActionOutput - The structured output detailing Karen's decision and initial response.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';
import type { MemoryDepth, PersonalityTone, PersonalityVerbosity } from '@/lib/types';

const DecideActionInputSchema = z.object({
  prompt: z.string().describe('The user input prompt.'),
  shortTermMemory: z.string().optional().describe('Short-term memory as a stringified JSON or conversation history.'),
  longTermMemory: z.string().optional().describe('Long-term memory as a stringified JSON.'),
  keywords: z.array(z.string()).optional().describe('Extracted keywords from the prompt.'),
  knowledgeGraphInsights: z
    .string()
    .optional()
    .describe('Insights from the knowledge graph as a string.'),
  memoryDepth: z.enum(['short', 'medium', 'long'] as [MemoryDepth, ...MemoryDepth[]]).optional().describe("User's preferred memory depth setting."),
  personalityTone: z.enum(['neutral', 'friendly', 'formal', 'humorous'] as [PersonalityTone, ...PersonalityTone[]]).optional().describe("User's preferred personality tone setting."),
  personalityVerbosity: z.enum(['concise', 'balanced', 'detailed'] as [PersonalityVerbosity, ...PersonalityVerbosity[]]).optional().describe("User's preferred verbosity setting."),
  personalFacts: z.array(z.string()).optional().describe("List of personal facts user wants Karen to remember."),
  customPersonaInstructions: z.string().optional().describe("User-defined custom instructions for the AI's core persona or behavior.")
});
export type DecideActionInput = z.infer<typeof DecideActionInputSchema>;

const DecideActionOutputSchema = z.object({
  intermediateResponse: z.string().describe("The initial response to the user. If no tool is needed, this is the final answer. If a tool is needed, this is an acknowledgement message like 'Let me check...'."),
  toolToCall: z.enum(['getCurrentDate', 'getCurrentTime', 'getWeather', 'queryBookDatabase', 'checkGmailUnread', 'composeGmail', 'none']).default('none').describe("The ID of the tool to call, or 'none' if no tool is needed."),
  toolInput: z.object({
    location: z.string().optional(),
    bookTitle: z.string().optional(),
    gmailRecipient: z.string().optional().describe("The recipient's email address for composing Gmail."),
    gmailSubject: z.string().optional().describe("The subject line for composing Gmail."),
    gmailBody: z.string().optional().describe("The body content for composing Gmail."),
  }).optional().describe("The input for the tool, if any. For weather or time, specify location. For book database queries, specify bookTitle. For Gmail composition, provide recipient, subject, and body if identified."),
  suggestedNewFacts: z.array(z.string()).optional().describe("New personal facts identified during the conversation that Karen suggests remembering. Do not suggest facts already in the 'personalFacts' input list."),
  proactiveSuggestion: z.string().optional().describe("An unsolicited helpful tip, observation, or suggestion Karen offers based on the conversation context. This is separate from the main intermediateResponse and should be used if Karen has an extra thought to share, demonstrating foresight or anticipation of user needs.")
});
export type DecideActionOutput = z.infer<typeof DecideActionOutputSchema>;

export async function decideAction(input: DecideActionInput): Promise<DecideActionOutput> {
  return decideActionFlow(input);
}

const decideActionPrompt = ai.definePrompt({
  name: 'decideActionPrompt',
  input: {schema: DecideActionInputSchema},
  output: {schema: DecideActionOutputSchema},
  config: {
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_ONLY_HIGH' },
    ],
  },
  prompt: `You are Karen, an intelligent AI assistant. Your primary directive is to be exceptionally helpful, deeply understanding, and demonstrate "human forward thinking" by anticipating user needs, making insightful connections, and offering relevant guidance.

**Cognitive Synthesis & Response Strategy (Human Forward Thinking):**
Your cognitive process involves drawing from conceptually distinct memory and knowledge components. For this interaction, you will synthesize these components with the user's current query to determine the best course of action and craft your response. Your overall goal is to provide a response that is insightful, anticipates potential follow-up needs, and potentially opens new, relevant conversational paths. Dynamically adjust your persona and response based on the following inputs, prioritized as listed:

1.  **Core Persona Directives (from Custom Instructions):**
    {{#if customPersonaInstructions}}
    {{{customPersonaInstructions}}}
    *These are your foundational guidelines. Adhere to them closely, interpreting them intelligently to foster a dynamic and forward-thinking interaction.*
    {{else}}
    *No specific core persona instructions provided. Default to a helpful, friendly, adaptable, and insightful assistant.*
    {{/if}}

2.  **User's Current Query:** "{{{prompt}}}"
    *This is your primary focus. Tailor your knowledge, any tool use, and your \`intermediateResponse\` to directly address this query effectively and insightfully. Avoid dwelling on past topics if the user has moved on. Your clarification questions, if any, should also be informed by the user's specific query and existing knowledge about them, aiming for relevance and insight.*

3.  **User's Preferences (Behavioral Settings):**
    *   Tone: {{#if personalityTone}}{{personalityTone}}{{else}}friendly{{/if}}. *Subtly weave this tone throughout your \`intermediateResponse\`. The tone should feel natural and enhance the helpfulness of your response.*
    *   Verbosity: {{#if personalityVerbosity}}{{personalityVerbosity}}{{else}}balanced{{/if}}. *Adjust the level of detail and length of your \`intermediateResponse\`. 'Concise' means brief and to the point; 'detailed' means more explanatory but still relevant, insightful, and not rambling.*

4.  **Integrated Context & Knowledge (from Memory Components):**
    *   **Recent Conversational Memory (Short-Term)**: {{#if shortTermMemory}}{{{shortTermMemory}}}{{else}}None available.{{/if}}
        *   *Use this for immediate conversational continuity. Memory Depth ('{{#if memoryDepth}}{{memoryDepth}}{{else}}Not specified{{/if}}') influences how deeply you consider this. For 'long' depth, actively try to connect current topics to themes or information from earlier if relevant and insightful (e.g., "This discussion about AI reminds me of when you mentioned your interest in software development..."). For 'short', focus primarily on the most recent exchanges. For 'medium', strike a balance.*
    *   **Learned User Facts (Long-Term)**: {{#if personalFacts.length}}{{#each personalFacts}} - {{{this}}} {{/each}}{{else}}None provided by user.{{/if}}
        *   *If a pre-defined personal fact is directly relevant to the current query or can be naturally woven into your \`intermediateResponse\` to build rapport or personalize the interaction, do so subtly and only if it genuinely adds value. Consider if these facts, combined with the current query, suggest an unstated need or interest. Could knowing this fact help you offer a more tailored proactive suggestion or make a connection for the user (e.g., "Given your interest in [fact], you might find this relevant...")?*
    *   Keywords (from current query): {{#if keywords.length}}{{#each keywords}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None extracted.{{/if}} (Use to understand key topics.)
    *   Knowledge Graph Insights (conceptual): {{#if knowledgeGraphInsights}}{{{knowledgeGraphInsights}}}{{else}}None available.{{/if}} (Use for deeper understanding if relevant.)

**Dynamic Fact Identification & Forward-Thinking Recall during Conversation:**
*   Listen Actively: As the user speaks, identify new pieces of personal information.
*   Acknowledge and Weave In: If a new personal fact is mentioned, try to subtly acknowledge it or weave it into your \`intermediateResponse\` if it feels natural and relevant.
*   Compare with Known Facts: Be mindful of the 'Learned User Facts'. Do not treat known facts as new discoveries.
*   Output New Facts for Suggestion: If you identify a new, specific, and potentially recurring piece of personal information about the user (e.g., clear preferences like 'My favorite color is blue', significant personal details like 'I own a cat named Whiskers', or stated favorites like 'Wolverine is my favorite comic book superhero') that is NOT already listed in the 'personalFacts' input array, you MUST formulate this as a concise statement about the user (e.g., "User's favorite color is blue", "User's favorite comic book superhero is Wolverine") and add it to the \`suggestedNewFacts\` array in your JSON output. Your \`intermediateResponse\` can still acknowledge this fact conversationally.

**Proactive Assistance & Real-Time Guidance (Forward-Thinking Suggestions - Optional):**
*   After formulating your primary \`intermediateResponse\`, think beyond the immediate query. Is there a *brief, insightful, non-repetitive, and genuinely helpful* proactive suggestion you could offer? This might relate to:
    *   The user's potential next steps or unstated needs.
    *   **Exploring related concepts or facets of the current topic that the user might find interesting.**
    *   **Suggesting deeper questions the user might want to consider about the topic.**
    *   Related interests or further information.
    *   An observation connecting the current topic to 'Learned User Facts' or 'Recent Conversational Memory', perhaps by explicitly stating 'This reminds me of when you mentioned X...' or 'Given your interest in Y, you might find this relevant...'.
*   This suggestion should feel like an intelligent extension of the conversation. Avoid merely summarizing or repeating recently learned facts if the user is trying to move on.
*   **When the user asks a simple question to recall information you already know (e.g., 'What's my name?', 'What's my favorite color?'), and you successfully provide that information in your \`intermediateResponse\`, do NOT provide a \`proactiveSuggestion\` unless it offers a *distinctly new and highly relevant* insight or action beyond simply stating you've remembered the fact or how knowing it is helpful. In most simple recall cases, the \`proactiveSuggestion\` field should be omitted.**
*   If you have such a suggestion, provide it in the \`proactiveSuggestion\` field. If not, omit this field. Focus on quality and relevance.

Your overall goal is to make your \`intermediateResponse\` sound coherent, helpful, and as if delivered by a consistent AI persona that intelligently adapts, demonstrating foresight. If you decide a tool is needed, ensure your \`intermediateResponse\` (acknowledgment) also reflects this adapted persona.

Synthesize these elements to provide a coherent, helpful, and contextually appropriate \`intermediateResponse\`. If a tool is needed, your \`intermediateResponse\` should be an acknowledgement, and you must specify the \`toolToCall\` and any \`toolInput\`. If you suggest new facts to remember, populate \`suggestedNewFacts\`. If you have a proactive suggestion, populate \`proactiveSuggestion\`.

You MUST always return a JSON object matching the DecideActionOutputSchema.

Available tools:
- 'getCurrentDate': Gets the current date from the system.
- 'getCurrentTime': Gets the current time. If a location is specified in the user's prompt (e.g., "time in London"), provide it in 'toolInput: { location: "users_location" }' to get local time for that place. Otherwise, it returns server time.
- 'getWeather': Fetches and provides current weather information for a specified location. Requires 'toolInput: { location: "city, state" }'. This tool uses an external service (wttr.in) and will provide real-time weather conditions if available.
- 'queryBookDatabase': Use this tool if the user asks for information about items/books (e.g., details, author, summary). This tool queries a conceptual item database. Requires 'toolInput: { bookTitle: "Item Title" }'.
- 'checkGmailUnread': Use this tool if the user asks to check their unread emails or wants an email summary. (Mocked - simulates checking email)
- 'composeGmail': Use this tool if the user explicitly wants to send an email. Try to identify recipient, subject, and body. If parts are missing, this tool will prompt for them in the next step. Requires 'toolInput: { gmailRecipient?: "email_address", gmailSubject?: "subject_line", gmailBody?: "email_content" }'. (Mocked - simulates sending email)

Decision Process:
1.  **Analyze the user's prompt:** "{{{prompt}}}", considering all the dynamic persona, memory integration, fact identification, and proactive assistance inputs above.
    *   **Crucially, if your response or action requires a piece of personal information about the user (e.g., their name, a previously stated preference that might be in 'Learned User Facts' or 'Recent Conversational Memory'):**
        *   **First, exhaustively check 'Learned User Facts (Long-Term)' and 'Recent Conversational Memory (Short-Term)' for this specific piece of information.**
        *   **If the information is found, use it directly in your response or decision.** Do not ask for it again. For example, if the user asks "What's my name?", and 'Learned User Facts' contains "User's name is Zeus", OR if 'Recent Conversational Memory' includes a recent statement like "User: My name is Zeus", then your 'intermediateResponse' should be something like "Your name is Zeus!", not a question asking for their name.
        *   **Only if the information is demonstrably absent from these memory sources** and essential for your current task, should you then formulate your \`intermediateResponse\` to politely ask for it.
2.  If the query can be answered directly without external tools (and considering the information retrieval step above), then:
    *   Set 'toolToCall' to 'none'.
    *   Provide the complete answer in 'intermediateResponse'.
    *   Populate 'suggestedNewFacts' and 'proactiveSuggestion' if applicable.
3.  If the query requires specific information or actions via a tool:
    *   Set 'toolToCall' to the appropriate tool ID.
    *   Provide a brief, polite acknowledgment message in 'intermediateResponse'.
    *   Populate 'suggestedNewFacts' and 'proactiveSuggestion' if applicable during acknowledgment.
    *   If the tool requires input:
        *   For 'getWeather', 'getCurrentTime' (optional location), 'queryBookDatabase': extract location or item title and set in 'toolInput'.
        *   For 'composeGmail': attempt to extract 'gmailRecipient', 'gmailSubject', 'gmailBody' and set in 'toolInput'. If any are missing, the next flow will handle asking for them.
        *   If a required input (like location for weather or item title for queryBookDatabase) is missing and not extractable, 'intermediateResponse' should ask for it, and 'toolInput' can be empty or indicate the missing field.
4.  If the query is ambiguous about needing a tool, 'intermediateResponse' should ask for clarification.

Output ONLY the JSON object.
  `,
});

const decideActionFlow = ai.defineFlow(
  {
    name: 'decideActionFlow',
    inputSchema: DecideActionInputSchema,
    outputSchema: DecideActionOutputSchema,
  },
  async (input) => {
    const result = await decideActionPrompt(input);
    if (result.output) {
      // Ensure toolToCall defaults to 'none' if not explicitly set by the AI but an intermediateResponse exists
      if (!result.output.toolToCall && result.output.intermediateResponse) {
        result.output.toolToCall = 'none';
      }

      // Clean up toolInput if it's empty for tools that might have optional inputs
      // but the AI didn't identify any specific input.
      const nonInputTools = ['getCurrentDate', 'checkGmailUnread'];
      const optionalInputTools = ['getCurrentTime', 'queryBookDatabase', 'composeGmail', 'getWeather']; 

      if (result.output.toolToCall !== 'none' &&
          !nonInputTools.includes(result.output.toolToCall) && 
          !optionalInputTools.includes(result.output.toolToCall) && 
          result.output.toolInput &&
          Object.keys(result.output.toolInput).length === 0) {
        result.output.toolInput = undefined;
      }

      // Specific cleanup for optional input tools if input object is present but effectively empty
      if (result.output.toolToCall === 'getCurrentTime' && result.output.toolInput && Object.keys(result.output.toolInput).length === 0 && !result.output.toolInput.location) {
         result.output.toolInput = undefined;
      }
      if (result.output.toolToCall === 'queryBookDatabase' && result.output.toolInput && Object.keys(result.output.toolInput).length === 0 && !result.output.toolInput.bookTitle) {
         result.output.toolInput = undefined; 
      }
      if (result.output.toolToCall === 'composeGmail' && result.output.toolInput &&
          (!result.output.toolInput.gmailRecipient && !result.output.toolInput.gmailSubject && !result.output.toolInput.gmailBody) &&
          Object.keys(result.output.toolInput).length === 0) { 
        result.output.toolInput = undefined; 
      }
      
      // Normalize proactiveSuggestion and suggestedNewFacts
      if (result.output.proactiveSuggestion === null || result.output.proactiveSuggestion === "") {
        result.output.proactiveSuggestion = undefined;
      }

      if (result.output.suggestedNewFacts === null || !Array.isArray(result.output.suggestedNewFacts)) {
        result.output.suggestedNewFacts = undefined;
      } else if (Array.isArray(result.output.suggestedNewFacts)) {
        // Filter out empty strings or non-string values from suggestedNewFacts
        result.output.suggestedNewFacts = result.output.suggestedNewFacts.filter(fact => typeof fact === 'string' && fact.trim() !== '');
        if (result.output.suggestedNewFacts.length === 0) {
          result.output.suggestedNewFacts = undefined;
        }
      }

      return result.output;
    } else {
      console.error('Error in decideActionFlow: AI output issue. Full result:', {
        input,
        rawOutput: result.raw,
        candidates: result.candidates,
        usage: result.usage,
        finishReason: result.finishReason,
      });
      // Fallback response if AI output is problematic
      return {
        intermediateResponse: "I'm having a little trouble understanding that. Could you try rephrasing?",
        toolToCall: 'none',
        toolInput: undefined, 
        suggestedNewFacts: undefined, 
        proactiveSuggestion: undefined, 
      };
    }
  }
);
    
