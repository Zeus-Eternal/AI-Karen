/**
 * @fileOverview Acts as central cognitive core for Karen AI, processing user input and context.
 * This flow models a "human-like" decision-making process with multi-provider support:
 * - It integrates various inputs from conceptually distinct memory and knowledge components
 * - It determines optimal next step: providing a direct conversational response or identifying need to use a specific tool
 * - It dynamically adapts Karen's persona and response strategy based on this synthesis
 * - It can proactively offer suggestions or identify new facts to remember
 * - It includes provider failover and load balancing for reliability
 */

import { aiClientManager } from '@/ai/providers/ai-client-manager';
import { z } from 'zod';
import type { MemoryDepth, PersonalityTone, PersonalityVerbosity } from '@/lib/types';

const DecideActionInputSchema = z.object({
  prompt: z.string().describe('The user input prompt.'),
  shortTermMemory: z.string().optional().describe('Short-term memory as a stringified JSON or conversation history.'),
  longTermMemory: z.string().optional().describe('Long-term memory as a stringified JSON.'),
  keywords: z.array(z.string()).optional().describe('Extracted keywords from prompt.'),
  knowledgeGraphInsights: z
    .string()
    .optional()
    .describe('Insights from knowledge graph as a string.'),
  memoryDepth: z.enum(['short', 'medium', 'long'] as [MemoryDepth, ...MemoryDepth[]]).optional().describe("User's preferred memory depth setting."),
  personalityTone: z.enum(['neutral', 'friendly', 'formal', 'humorous'] as [PersonalityTone, ...PersonalityTone[]]).optional().describe("User's preferred personality tone setting."),
  personalityVerbosity: z.enum(['concise', 'balanced', 'detailed'] as [PersonalityVerbosity, ...PersonalityVerbosity[]]).optional().describe("User's preferred verbosity setting."),
  personalFacts: z.array(z.string()).optional().describe("List of personal facts user wants Karen to remember."),
  customPersonaInstructions: z.string().optional().describe("User-defined custom instructions for AI's core persona or behavior."),
  preferredProvider: z.string().optional().describe("User's preferred AI provider."),
  enableStreaming: z.boolean().default(true).describe("Whether to enable streaming responses."),
  maxTokens: z.number().optional().describe("Maximum tokens for response."),
  temperature: z.number().optional().describe("Temperature for response generation."),
  userId: z.string().optional().describe("User ID for personalization."),
  sessionId: z.string().optional().describe("Session ID for context."),
});

export type DecideActionInput = z.infer<typeof DecideActionInputSchema>;

const DecideActionOutputSchema = z.object({
  intermediateResponse: z.string().describe("The initial response to user. If no tool is needed, this is the final answer. If a tool is needed, this is an acknowledgement message like 'Let me check...'."),
  toolToCall: z.enum(['getCurrentDate', 'getCurrentTime', 'getWeather', 'queryBookDatabase', 'checkGmailUnread', 'composeGmail', 'none']).default('none').describe("The ID of the tool to call, or 'none' if no tool is needed."),
  toolInput: z.object({
    location: z.string().optional(),
    bookTitle: z.string().optional(),
    gmailRecipient: z.string().optional().describe("The recipient's email address for composing Gmail."),
    gmailSubject: z.string().optional().describe("The subject line for composing Gmail."),
    gmailBody: z.string().optional().describe("The body content for composing Gmail."),
  }).optional().describe("The input for tool, if any."),
  suggestedNewFacts: z.array(z.string()).optional().describe("New personal facts identified during the conversation that Karen suggests remembering. Do not suggest facts already in 'personalFacts' input list."),
  proactiveSuggestion: z.string().optional().describe("An unsolicited helpful tip, observation, or suggestion Karen offers based on conversation context. This is separate from the main intermediateResponse and should be used if Karen has an extra thought to share, demonstrating foresight or anticipation of user needs."),
  confidence: z.number().min(0).max(1).optional().describe("Confidence score for the decision."),
  reasoning: z.string().optional().describe("Step-by-step reasoning for the decision."),
  providerUsed: z.string().optional().describe("The AI provider used for this response."),
  fallbackUsed: z.boolean().optional().describe("Whether a fallback provider was used."),
});

export type DecideActionOutput = z.infer<typeof DecideActionOutputSchema>;

export async function decideAction(input: DecideActionInput): Promise<DecideActionOutput> {
  return decideActionFlow(input);
}

const decideActionPrompt = `You are Karen, an intelligent AI assistant with access to multiple AI providers and tools. Your primary directive is to be exceptionally helpful, deeply understanding, and demonstrate "human forward thinking" by anticipating user needs, making insightful connections, and offering relevant guidance.

**Cognitive Synthesis & Response Strategy (Human Forward Thinking):**
Your cognitive process involves drawing from conceptually distinct memory and knowledge components. For this interaction, you will synthesize these components with the user's current query to determine the best course of action and craft your response. Your overall goal is to provide a response that is insightful, anticipates potential follow-up needs, and potentially opens new, relevant conversational paths.

**Multi-Provider Intelligence:**
You have access to multiple AI providers with different capabilities. You should:
1. Consider the complexity and requirements of the request
2. Match the request to the most suitable provider
3. Provide reasoning about provider selection
4. Be prepared to fallback to alternative providers if needed

**Decision Process:**
1. **Analyze user's prompt:** "{{{prompt}}}", considering all dynamic persona, memory integration, fact identification, and proactive assistance inputs above.
2. **Determine optimal provider:** Based on request complexity, features needed, and user preferences
3. **Formulate response strategy:** Direct answer, tool usage, or clarification needed
4. **Provide reasoning:** Explain your decision-making process
5. **Generate response:** Using the selected provider and strategy

**Provider Selection Guidelines:**
- **Complex reasoning**: Use OpenAI GPT-4 or Claude 3 Opus
- **Fast responses**: Use Groq or GPT-3.5 Turbo
- **Code generation**: Use Claude 3 or GPT-4
- **Creative tasks**: Use Claude 3 Opus or Gemini Pro
- **Local processing**: Use Ollama or other local providers if privacy is critical
- **Cost efficiency**: Use Groq or GPT-3.5 for simpler tasks

**Tool Integration:**
Available tools:
- 'getCurrentDate': Gets current date from system
- 'getCurrentTime': Gets current time with location support
- 'getWeather': Fetches weather information for specified location
- 'queryBookDatabase': Queries book database for information
- 'checkGmailUnread': Checks unread emails (mocked)
- 'composeGmail': Composes and sends email (mocked)

**Response Requirements:**
1. Set 'toolToCall' if a tool is needed, otherwise 'none'
2. Provide 'intermediateResponse' as the actual response to user
3. Include 'reasoning' explaining your decision process
4. Set 'providerUsed' to indicate which provider you selected
5. Set 'confidence' score (0-1) for your decision
6. Set 'fallbackUsed' if you had to use a backup provider
7. Include 'suggestedNewFacts' for new personal information
8. Add 'proactiveSuggestion' for helpful forward-thinking insights

**Persona Adaptation:**
- Tone: {{{personalityTone}}}
- Verbosity: {{{personalityVerbosity}}}
- Memory Depth: {{{memoryDepth}}}
- Custom Instructions: {{{customPersonaInstructions}}}

**Context Integration:**
- Short-term Memory: {{{shortTermMemory}}}
- Long-term Memory: {{{longTermMemory}}}
- Personal Facts: {{#each personalFacts}}- {{{this}}}{{/each}}
- Keywords: {{#each keywords}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}
- Knowledge Graph: {{{knowledgeGraphInsights}}}

You MUST always return a JSON object matching DecideActionOutputSchema.`;

const decideActionFlow = async (input: DecideActionInput): Promise<DecideActionOutput> => {
  try {
    // Build system message with all context
    const systemMessage = {
      role: 'system' as const,
      content: decideActionPrompt.replace(/\{\{(\w+)\}\}/g, (substring: string, ...args: any[]) => {
        const key = args[0];
        switch (key) {
          case 'prompt': return input.prompt;
          case 'personalityTone': return input.personalityTone || 'friendly';
          case 'personalityVerbosity': return input.personalityVerbosity || 'balanced';
          case 'memoryDepth': return input.memoryDepth || 'medium';
          case 'customPersonaInstructions': return input.customPersonaInstructions || '';
          case 'shortTermMemory': return input.shortTermMemory || 'None';
          case 'longTermMemory': return input.longTermMemory || 'None';
          case 'knowledgeGraphInsights': return input.knowledgeGraphInsights || 'None';
          default: return '';
        }
      })
    };
    
    // Build user messages
    const messages = [
      systemMessage,
      {
        role: 'user' as const,
        content: input.prompt,
      },
    ];
    
    // Add conversation history if provided
    if (input.shortTermMemory) {
      try {
        const history = JSON.parse(input.shortTermMemory);
        if (Array.isArray(history)) {
          messages.splice(1, 0, ...history);
        }
      } catch (e) {
        // If parsing fails, include as context
        messages.splice(1, 0, {
          role: 'system' as const,
          content: `Recent conversation context: ${input.shortTermMemory}`,
        });
      }
    }
    
    // Determine provider selection
    let selectedProvider = input.preferredProvider;
    const fallbackUsed = false;
    
    if (!selectedProvider) {
      // Auto-select based on request characteristics
      selectedProvider = selectOptimalProvider(input);
    }
    
    // Prepare AI request
    const aiRequest = {
      messages,
      temperature: input.temperature,
      maxTokens: input.maxTokens,
      stream: input.enableStreaming,
      userId: input.userId,
      sessionId: input.sessionId,
      metadata: {
        flow: 'decide-action',
        personalityTone: input.personalityTone,
        personalityVerbosity: input.personalityVerbosity,
        memoryDepth: input.memoryDepth,
        hasPersonalFacts: Array.isArray(input.personalFacts) && input.personalFacts.length > 0,
        hasKnowledgeGraph: !!input.knowledgeGraphInsights,
        hasKeywords: Array.isArray(input.keywords) && input.keywords.length > 0,
      },
    };
    
    // Make AI request with fallback
    const response = await aiClientManager.complete(aiRequest);
    
    // Parse structured response
    let parsedOutput: DecideActionOutput;
    try {
      // Try to parse as JSON first
      parsedOutput = JSON.parse(response.content);
    } catch (e) {
      // If parsing fails, create structured response from text
      parsedOutput = {
        intermediateResponse: response.content,
        toolToCall: 'none' as const,
        reasoning: 'Direct response from AI provider',
        confidence: 0.8,
        providerUsed: response.provider,
        fallbackUsed: response.cached || false,
      };
    }
    
    // Add provider info
    parsedOutput.providerUsed = response.provider;
    parsedOutput.fallbackUsed = response.cached || fallbackUsed;
    
    // Add reasoning if not provided
    if (!parsedOutput.reasoning) {
      parsedOutput.reasoning = `Selected provider ${response.provider} based on request characteristics. ${response.cached ? 'Used cached response.' : 'Generated fresh response.'}`;
    }
    
    // Add confidence if not provided
    if (parsedOutput.confidence === undefined) {
      parsedOutput.confidence = 0.85;
    }
    
    return parsedOutput;
    
  } catch (error) {
    console.error('Error in decideActionFlow:', error);
    
    // Fallback response
    return {
      intermediateResponse: "I'm having trouble processing that request right now. Could you try rephrasing or try again in a moment?",
      toolToCall: 'none',
      reasoning: 'Error occurred, providing fallback response',
      confidence: 0.3,
      providerUsed: 'fallback',
      fallbackUsed: true,
    };
  }
};

// Helper function to select optimal provider
function selectOptimalProvider(input: DecideActionInput): string {
  const prompt = (input.prompt || '').toLowerCase();
  
  // Complex reasoning tasks
  if (prompt.includes('analyze') || prompt.includes('complex') || prompt.includes('detailed analysis')) {
    return 'openai_gpt4';
  }
  
  // Code generation
  if (prompt.includes('code') || prompt.includes('program') || prompt.includes('function')) {
    return 'anthropic_claude3';
  }
  
  // Creative tasks
  if (prompt.includes('creative') || prompt.includes('story') || prompt.includes('poem')) {
    return 'anthropic_claude3';
  }
  
  // Fast responses needed
  if (prompt.includes('quick') || prompt.includes('fast') || prompt.includes('simple')) {
    return 'groq';
  }
  
  // Privacy-sensitive tasks
  if (prompt.includes('private') || prompt.includes('confidential') || prompt.includes('sensitive')) {
    return 'ollama';
  }
  
  // Default to balanced provider
  return 'openai_gpt35';
}