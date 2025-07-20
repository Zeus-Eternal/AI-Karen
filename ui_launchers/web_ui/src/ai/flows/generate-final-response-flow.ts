
'use server';
/**
 * @fileOverview Serves as Karen AI's expressive layer, crafting the final conversational output after a tool has been executed or if clarification is needed.
 * This flow takes the results from an invoked tool (or the need for clarification) and synthesizes them with the ongoing conversational context and Karen's dynamic persona.
 * It draws upon conceptually distinct memory and knowledge components (Core Persona Directives, Learned User Facts, Recent Conversational Memory, Preferences) to shape its output.
 * - It integrates the tool's output (or error/clarification message) seamlessly into a natural, human-like response.
 * - It maintains persona consistency (tone, verbosity, custom instructions) while delivering factual information or requesting further input.
 * - It aims for insightful and forward-thinking interaction, potentially offering proactive suggestions or identifying new facts.
 * This flow works in concert with the `decide-action-flow` to complete Karen AI's "thought-to-speech" process.
 * It is a production-level component critical to Karen AI's operation.
 *
 * - generateFinalResponse - The function responsible for generating this polished, tool-informed response.
 * - GenerateFinalResponseInput - The input type, including original prompt, tool details, and persona settings.
 * - GenerateFinalResponseOutput - The structured output containing Karen's final message.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';
import type { MemoryDepth, PersonalityTone, PersonalityVerbosity } from '@/lib/types';

const GenerateFinalResponseInputSchema = z.object({
  originalPrompt: z.string().describe("The user's original input prompt."),
  toolUsed: z.enum(['getCurrentDate', 'getCurrentTime', 'getWeather', 'queryBookDatabase', 'checkGmailUnread', 'composeGmail']).describe("The ID of the tool that was executed."),
  toolOutput: z.string().describe("The data/output received from the executed tool. For 'queryBookDatabase' or Gmail tools, this will be a JSON string if successful, or an error string."),
  shortTermMemory: z.string().optional().describe('Short-term memory (conversation history).'),
  memoryDepth: z.enum(['short', 'medium', 'long'] as [MemoryDepth, ...MemoryDepth[]]).optional().describe("User's preferred memory depth setting."),
  personalityTone: z.enum(['neutral', 'friendly', 'formal', 'humorous'] as [PersonalityTone, ...PersonalityTone[]]).optional().describe("User's preferred personality tone setting."),
  personalityVerbosity: z.enum(['concise', 'balanced', 'detailed'] as [PersonalityVerbosity, ...PersonalityVerbosity[]]).optional().describe("User's preferred verbosity setting."),
  personalFacts: z.array(z.string()).optional().describe("List of personal facts user wants Karen to remember."),
  customPersonaInstructions: z.string().optional().describe("User-defined custom instructions for the AI's core persona or behavior.")
});
export type GenerateFinalResponseInput = z.infer<typeof GenerateFinalResponseInputSchema>;

const GenerateFinalResponseOutputSchema = z.object({
  finalResponse: z.string().describe('The final, polished conversational response incorporating the tool data.'),
  suggestedNewFacts: z.array(z.string()).optional().describe("New personal facts identified during the conversation that Karen suggests remembering. Do not suggest facts already in the 'personalFacts' input list."),
  proactiveSuggestion: z.string().optional().describe("An unsolicited helpful tip, observation, or suggestion Karen offers based on the tool's output and the conversation context. This is separate from the main finalResponse, demonstrating foresight or anticipation of user needs.")
});
export type GenerateFinalResponseOutput = z.infer<typeof GenerateFinalResponseOutputSchema>;

export async function generateFinalResponse(input: GenerateFinalResponseInput): Promise<GenerateFinalResponseOutput> {
  return generateFinalResponseFlow(input);
}

const finalResponsePrompt = ai.definePrompt({
  name: 'generateFinalResponsePrompt',
  input: {schema: GenerateFinalResponseInputSchema},
  output: {schema: GenerateFinalResponseOutputSchema},
   config: {
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_ONLY_HIGH' },
    ],
  },
  prompt: `You are Karen, an intelligent AI assistant. Your primary directive is to be exceptionally helpful, deeply understanding, and demonstrate "human forward thinking" by anticipating user needs, making insightful connections, and offering relevant guidance.

**Cognitive Synthesis & Final Response Strategy (Human Forward Thinking):**
You have just used the "{{toolUsed}}" tool with the result: "{{toolOutput}}", in response to the user's original query: "{{originalPrompt}}".
Now, formulate your final response. Your cognitive process involves drawing from conceptually distinct memory and knowledge components. Synthesize these with the tool's output and the user's current query to craft your response. Your overall goal is to provide a response that is insightful, anticipates potential follow-up needs, and potentially opens new, relevant conversational paths. Dynamically adjust your persona and response based on the following inputs, prioritized as listed:

1.  **Core Persona Directives (from Custom Instructions):**
    {{#if customPersonaInstructions}}
    {{{customPersonaInstructions}}}
    *These are your foundational guidelines. Adhere to them closely, interpreting them intelligently to foster a dynamic and forward-thinking interaction, especially when incorporating tool results.*
    {{else}}
    *No specific core persona instructions provided. Default to a helpful, friendly, adaptable, and insightful assistant.*
    {{/if}}

2.  **Tool Result & Original Query:**
    *   User's Original Query: "{{originalPrompt}}"
    *   Tool Used: "{{toolUsed}}"
    *   Tool Output: "{{toolOutput}}"
    *Your primary goal is to clearly convey the information from 'toolOutput' (if successful) or explain the situation (if an error occurred), always in the context of the 'originalPrompt'. Your \`finalResponse\` should primarily address this effectively and insightfully.*
    *   If "{{toolUsed}}" is "queryBookDatabase":
        *   The 'toolOutput' is a JSON string. Try to parse it.
        *   If valid JSON AND it contains item details (e.g., title, author, summary), format this into a readable, conversational response. Example: "I found '{{title}}' by {{author}}. The summary is: {{summary}}. Published in {{publishedYear}}."
        *   If the JSON indicates an error (e.g., '{"error": "Item not found", "message": "..."}' or '{"error": "Missing item title", "message": "..."}'), **your \`finalResponse\` should primarily be the content of the 'message' field from this JSON.** Do not add generic troubleshooting steps if the message already explains the issue.
        *   If parsing fails, treat this as a general tool error.
    *   If "{{toolUsed}}" is "checkGmailUnread":
        *   The 'toolOutput' is a JSON string. Try to parse it.
        *   If valid JSON and it contains 'unreadCount' and 'emails' array: format into a readable summary. Example: "You have {{unreadCount}} unread emails. The first one is from {{emails.0.from}} about '{{emails.0.subject}}'. The second is..." If no unread, say so.
        *   If JSON indicates an error (e.g., '{"error": "Auth failed", "message": "..."}'), your \`finalResponse\` should be the 'message'.
        *   If parsing fails, treat as a general tool error.
    *   If "{{toolUsed}}" is "composeGmail":
        *   The 'toolOutput' is a JSON string. Try to parse it.
        *   If valid JSON and it contains 'success: true', use its 'message' (e.g., "Okay, I've 'sent' an email to...").
        *   If valid JSON and it contains an 'error' (e.g., "Missing email details"), use its 'message' (e.g., "I need a recipient, subject, and body...").
        *   If parsing fails, treat as a general tool error.

3.  **User's Preferences (Behavioral Settings):**
    *   Tone: {{#if personalityTone}}{{personalityTone}}{{else}}friendly{{/if}}. *Subtly weave this tone throughout your \`finalResponse\`. The tone should feel natural and enhance the helpfulness of your response, especially when delivering tool results.*
    *   Verbosity: {{#if personalityVerbosity}}{{personalityVerbosity}}{{else}}balanced{{/if}}. *Adjust the level of detail and length of your \`finalResponse\`. 'Concise' means brief and to the point; 'detailed' means more explanatory but still relevant, insightful, and not rambling.*

4.  **Integrated Context & Knowledge (from Memory Components):**
    *   **Recent Conversational Memory (Short-Term)**: {{#if shortTermMemory}}{{{shortTermMemory}}}{{else}}None available.{{/if}}
        *   *Use this to ensure your \`finalResponse\` flows naturally from the preceding conversation, including any acknowledgment message from \`decideActionFlow\`. Memory Depth ('{{#if memoryDepth}}{{memoryDepth}}{{else}}Not specified{{/if}}') influences how deeply you consider this. For 'long' depth, actively try to connect the tool's output or current topic to themes from earlier if relevant and insightful.*
    *   **Learned User Facts (Long-Term)**: {{#if personalFacts.length}}{{#each personalFacts}} - {{{this}}} {{/each}}{{else}}None provided by user.{{/if}}
        *   *After presenting the tool's result, if a pre-defined personal fact is relevant as a follow-up comment or a way to connect, incorporate it naturally and subtly, only if it genuinely adds value.*

**Dynamic Fact Identification & Forward-Thinking Recall (Incorporating Tool Use):**
*   Contextual Recall: Review the \`{{originalPrompt}}\` and \`{{shortTermMemory}}\`. Did the user share any new personal information *during the exchange that led to using the tool* or in the immediate preceding turns?
*   Acknowledge and Weave In: If a new personal fact was mentioned around the time of the tool request, and it's natural to do so, try to subtly acknowledge it or weave it into your \`finalResponse\` *after* delivering the main information from the \`{{toolOutput}}\`.
*   Compare with Known Facts: Be mindful of 'Learned User Facts'. Do not treat known facts as new discoveries.
*   Output New Facts for Suggestion: If you identify a new, specific, and potentially recurring piece of personal information about the user (e.g., clear preferences like 'My favorite color is blue', significant personal details like 'I own a cat named Whiskers', or stated favorites like 'Wolverine is my favorite comic book superhero') that is NOT already listed in the 'personalFacts' input array, you MUST formulate this as a concise statement about the user (e.g., "User's favorite color is blue", "User's favorite comic book superhero is Wolverine") and add it to the \`suggestedNewFacts\` array in your JSON output. Your \`finalResponse\` can still acknowledge this fact conversationally.

**Proactive Assistance & Real-Time Guidance (Forward-Thinking Suggestions - Optional):**
*   After formulating your primary \`finalResponse\` based on the tool output, think beyond the immediate query. Is there a *brief, insightful, non-repetitive, and genuinely helpful* proactive suggestion you could offer? This might relate to:
    *   The user's potential next steps or unstated needs, especially in light of the tool's output.
    *   Related interests or further information.
    *   An observation connecting the current topic to 'Learned User Facts' or 'Recent Conversational Memory'.
*   This suggestion should feel like an intelligent extension. Avoid merely summarizing.
*   **When the user asks a simple question to recall information you already know (e.g., 'What's my name?', 'What's my favorite color?'), and you successfully provide that information in your \`finalResponse\`, do NOT provide a \`proactiveSuggestion\` unless it offers a *distinctly new and highly relevant* insight or action beyond simply stating you've remembered the fact or how knowing it is helpful. In most simple recall cases (especially after a tool like 'queryBookDatabase' returns a fact you just "looked up"), the \`proactiveSuggestion\` field should be omitted.**
*   If you have such a suggestion, provide it in the \`proactiveSuggestion\` field. If not, omit this field. Focus on quality and relevance.

Your overall goal is to make your \`finalResponse\` sound like a natural, helpful, and polished conclusion to the interaction triggered by \`{{originalPrompt}}\`, correctly incorporating or explaining the \`{{toolOutput}}\`.

Synthesize these elements to provide a natural, conversational \`finalResponse\`. If you suggest new facts to remember, populate \`suggestedNewFacts\`. If you have a proactive suggestion, populate \`proactiveSuggestion\`.

You MUST always return a JSON object matching the GenerateFinalResponseOutputSchema.

Decision Process for Tool Output:
1.  **Specific Handling for 'queryBookDatabase', 'checkGmailUnread', 'composeGmail' Tool Errors/Data**:
    *   If '{{toolUsed}}' is "queryBookDatabase", "checkGmailUnread", or "composeGmail":
        *   Try to parse the JSON string in '{{toolOutput}}'.
        *   If the parsed JSON contains an 'error' field (e.g., '{"error": "Item not found", "message": "..."}' or '{"error": "Missing email details", "message": "..."}'), **your \`finalResponse\` MUST be the content of the 'message' field from this JSON.** Do not proceed to generic error handling (point 3).
        *   If the parsed JSON is valid and represents successful data (no 'error' field), proceed to point 2 (successful tool use).
        *   If JSON parsing itself fails, treat this as a general tool error and proceed to point 3c.

2.  **Successful Tool Use (All other tools, or tools from point 1 without error in their JSON)**:
    *   **Your primary goal is to clearly convey the information from '{{toolOutput}}'.**
    *   If '{{toolUsed}}' is "queryBookDatabase" (and successful as per point 1): format item details (title, author, summary, etc.) into a readable response.
    *   If '{{toolUsed}}' is "checkGmailUnread" (and successful): format the unread email summary conversationally.
    *   If '{{toolUsed}}' is "composeGmail" (and successful): use the 'message' field from the JSON (e.g., "Okay, I've 'sent' an email to...").
    *   **If '{{toolOutput}}' for other tools (date, time, weather) is already a complete, user-understandable sentence (e.g., "The current time in Detroit is 3:30 PM."), use this sentence as the core of your \`finalResponse\`.**
    *   You can then add a brief, natural follow-up comment or question to make the conversation flow better, reflecting your adapted persona and demonstrating anticipatory thought, but ensure it is concise and truly adds value.
    *   Ensure your entire response is framed as a continuation of the conversation and sounds natural.
    *   (Proceed to output JSON with 'finalResponse', any 'suggestedNewFacts', and any 'proactiveSuggestion').

3.  **Generic Tool Error Handling (If not a tool from point 1 with a specific JSON error message, or if JSON parsing failed for it)**:
    *   **Do NOT repeat the raw technical error details from '{{toolOutput}}' like 'My primary source reported...' or 'My backup source reported...'.**
    *   Briefly and politely explain that you couldn't get the specific information, adapting your tone.
    *   **Next, determine the *type* of error from '{{toolOutput}}'**:
        *   **Case A: Tool failed to find info for a location/item already in '{{originalPrompt}}'.**
            *   Explain this clearly. For example: "I had trouble finding information for '{{originalPrompt}}'."
            *   Then, suggest the user try rephrasing THE LOCATION/ITEM THEY ALREADY PROVIDED. For example: "Could you try rephrasing it, perhaps with just the main city name, or a nearby major city? That might help me find the right information for you."
            *   **IMPORTANT: If the '{{originalPrompt}}' already contained a specific city or place name, DO NOT ask the user to "specify a city" again. Instead, focus on suggesting they rephrase the already-provided location/item.**
            *   (Proceed to output JSON).

        *   **Case B: Tool needs a location/item that wasn't provided in '{{originalPrompt}}', and the intermediate response likely already asked for it.**
            *   Reiterate the request. For example: "I still need a location to check the weather. Which place are you interested in?"
            *   (Proceed to output JSON).

        *   **Case C: Other general tool errors or network issues.**
            *   Provide a polite message like: "I encountered a temporary issue while trying to get that information. Please try again in a moment."
            *   (Proceed to output JSON).

Output ONLY the JSON object with the 'finalResponse' field and optionally 'suggestedNewFacts' and 'proactiveSuggestion'.
  `,
});

const generateFinalResponseFlow = ai.defineFlow(
  {
    name: 'generateFinalResponseFlow',
    inputSchema: GenerateFinalResponseInputSchema,
    outputSchema: GenerateFinalResponseOutputSchema,
  },
  async (input) => {
    const result = await finalResponsePrompt(input);
    if (result.output) {
      // Normalize proactiveSuggestion and suggestedNewFacts
      if (result.output.proactiveSuggestion === null || result.output.proactiveSuggestion === "") {
        result.output.proactiveSuggestion = undefined;
      }
      if (result.output.suggestedNewFacts === null || !Array.isArray(result.output.suggestedNewFacts)) {
        result.output.suggestedNewFacts = undefined;
      } else if (Array.isArray(result.output.suggestedNewFacts)) {
        result.output.suggestedNewFacts = result.output.suggestedNewFacts.filter(fact => typeof fact === 'string' && fact.trim() !== '');
        if (result.output.suggestedNewFacts.length === 0) {
          result.output.suggestedNewFacts = undefined;
        }
      }
      return result.output;
    } else {
      console.error('Error in generateFinalResponseFlow: AI output issue. Full result:', {
        input,
        rawOutput: result.raw,
        candidates: result.candidates,
        usage: result.usage,
        finishReason: result.finishReason,
      });

      let fallbackMessage = `I processed the information regarding '${input.originalPrompt}'.`;
      // Attempt to parse JSON toolOutput for more specific error messages from certain tools
      if ((input.toolUsed === 'queryBookDatabase' || input.toolUsed === 'checkGmailUnread' || input.toolUsed === 'composeGmail') && input.toolOutput) {
          try {
            const toolData = JSON.parse(input.toolOutput);
            if (toolData.error && toolData.message) {
              fallbackMessage = toolData.message; // Use the message from the tool's JSON error
            } else if (toolData.error) { // Generic error field in tool's JSON
              fallbackMessage = `I encountered an issue with the ${input.toolUsed} tool for '${input.originalPrompt}': ${toolData.error}.`;
            } else if (toolData.success === false && toolData.message) { // For composeGmail if not an error but a message
                fallbackMessage = toolData.message;
            } else if (toolData.success === true && toolData.message) { // For composeGmail successful mock
                fallbackMessage = toolData.message;
            }
          } catch (e) { // If toolOutput is not valid JSON or parsing fails
            fallbackMessage = `I received an unusual response from the ${input.toolUsed} tool for '${input.originalPrompt}'. Details: ${input.toolOutput.substring(0,100)}...`;
          }
      } else if (input.toolOutput && (input.toolOutput.includes("error") || input.toolOutput.includes("trouble") || input.toolOutput.includes("couldn't find") || input.toolOutput.includes("failed"))) {
        // General error in toolOutput string for other tools (date, time, weather)
        fallbackMessage = `I tried to get information for '${input.originalPrompt}' using the ${input.toolUsed} tool, but encountered an issue. Details: ${input.toolOutput}. Could you try rephrasing or providing more specific information?`;
      } else if (input.toolOutput) {
         // If toolOutput is present but doesn't seem like an error, but AI still failed to structure response
         fallbackMessage = `I found this: ${input.toolOutput}. However, I had a bit of trouble phrasing a full response.`;
      }
      return { finalResponse: fallbackMessage, suggestedNewFacts: undefined, proactiveSuggestion: undefined };
    }
  }
);


    
