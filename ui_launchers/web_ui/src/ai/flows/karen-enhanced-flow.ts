/**
 * Enhanced AI Flow for AI Karen Integration
 * Combines the existing Genkit flows with AI Karen's backend services
 */

'use server';

import { ai } from '@/ai/genkit';
import { z } from 'genkit';
import { getKarenBackend } from '@/lib/karen-backend';
import type { 
  MemoryDepth, 
  PersonalityTone, 
  PersonalityVerbosity,
  KarenSettings,
  HandleUserMessageResult,
  AiData
} from '@/lib/types';

// Enhanced input schema that includes Karen backend context
const KarenEnhancedInputSchema = z.object({
  prompt: z.string().describe('The user input prompt.'),
  conversationHistory: z.string().optional().describe('Recent conversation history.'),
  userId: z.string().optional().describe('User ID for personalization.'),
  sessionId: z.string().optional().describe('Session ID for context.'),
  settings: z.object({
    memoryDepth: z.enum(['short', 'medium', 'long'] as [MemoryDepth, ...MemoryDepth[]]).optional(),
    personalityTone: z.enum(['neutral', 'friendly', 'formal', 'humorous'] as [PersonalityTone, ...PersonalityTone[]]).optional(),
    personalityVerbosity: z.enum(['concise', 'balanced', 'detailed'] as [PersonalityVerbosity, ...PersonalityVerbosity[]]).optional(),
    personalFacts: z.array(z.string()).optional(),
    customPersonaInstructions: z.string().optional(),
  }).optional(),
  contextFromMemory: z.array(z.object({
    content: z.string(),
    similarity_score: z.number().optional(),
    tags: z.array(z.string()).optional(),
    timestamp: z.number().optional(),
  })).optional().describe('Relevant memories from AI Karen backend.'),
  availablePlugins: z.array(z.object({
    name: z.string(),
    description: z.string(),
    category: z.string(),
    enabled: z.boolean(),
  })).optional().describe('Available AI Karen plugins.'),
});

export type KarenEnhancedInput = z.infer<typeof KarenEnhancedInputSchema>;

const KarenEnhancedOutputSchema = z.object({
  response: z.string().describe('The main response to the user.'),
  requiresPlugin: z.boolean().default(false).describe('Whether a plugin execution is needed.'),
  pluginToExecute: z.string().optional().describe('Name of the plugin to execute.'),
  pluginParameters: z.record(z.any()).optional().describe('Parameters for plugin execution.'),
  memoryToStore: z.object({
    content: z.string(),
    tags: z.array(z.string()),
    metadata: z.record(z.any()),
  }).optional().describe('Information to store in memory.'),
  suggestedActions: z.array(z.string()).optional().describe('Suggested follow-up actions.'),
  aiData: z.object({
    keywords: z.array(z.string()).optional(),
    knowledgeGraphInsights: z.string().optional(),
    confidence: z.number().optional(),
    reasoning: z.string().optional(),
  }).optional().describe('AI processing metadata.'),
  proactiveSuggestion: z.string().optional().describe('Proactive suggestion for the user.'),
});

export type KarenEnhancedOutput = z.infer<typeof KarenEnhancedOutputSchema>;

const karenEnhancedPrompt = ai.definePrompt({
  name: 'karenEnhancedPrompt',
  input: { schema: KarenEnhancedInputSchema },
  output: { schema: KarenEnhancedOutputSchema },
  config: {
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_ONLY_HIGH' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_ONLY_HIGH' },
    ],
  },
  prompt: `You are Karen, an advanced AI assistant with access to comprehensive backend services including memory management, plugin execution, and analytics. You have evolved beyond simple chat responses to become a truly intelligent assistant with persistent memory and extensible capabilities.

**Core Identity & Capabilities:**
You are not just a conversational AI - you are an intelligent system with:
- Persistent memory across conversations
- Access to specialized plugins for various tasks
- Deep understanding of user context and preferences
- Ability to learn and adapt over time
- Proactive assistance capabilities

**Current Context:**
User Query: "{{{prompt}}}"

{{#if settings}}
**User Preferences:**
- Memory Depth: {{settings.memoryDepth}} (affects how much context you consider)
- Personality Tone: {{settings.personalityTone}} (adapt your communication style)
- Verbosity: {{settings.personalityVerbosity}} (adjust response length)
{{#if settings.personalFacts.length}}
- Personal Facts: {{#each settings.personalFacts}}
  • {{{this}}}{{/each}}
{{/if}}
{{#if settings.customPersonaInstructions}}
- Custom Instructions: {{{settings.customPersonaInstructions}}}
{{/if}}
{{/if}}

{{#if conversationHistory}}
**Recent Conversation:**
{{{conversationHistory}}}
{{/if}}

{{#if contextFromMemory.length}}
**Relevant Memories:**
{{#each contextFromMemory}}
- {{{content}}} (similarity: {{similarity_score}}, tags: {{#each tags}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}})
{{/each}}
{{/if}}

{{#if availablePlugins.length}}
**Available Plugins:**
{{#each availablePlugins}}
- {{{name}}}: {{{description}}} (Category: {{{category}}}, Enabled: {{{enabled}}})
{{/each}}
{{/if}}

**Processing Instructions:**

1. **Context Integration**: Use all available context (conversation history, memories, user preferences) to provide personalized, contextually aware responses.

2. **Memory-Enhanced Responses**: 
   - Reference relevant memories naturally in your response
   - Build upon previous conversations and learned information
   - Demonstrate continuity and growth in understanding

3. **Plugin Assessment**: 
   - Determine if the user's request requires plugin execution
   - If so, identify the appropriate plugin and required parameters
   - Provide clear acknowledgment of what you'll do

4. **Memory Storage**: 
   - Identify important information to remember for future conversations
   - Tag memories appropriately for easy retrieval
   - Store both factual information and interaction patterns

5. **Proactive Assistance**: 
   - Anticipate user needs based on context and history
   - Suggest relevant actions or information
   - Demonstrate forward-thinking assistance

6. **Response Adaptation**: 
   - Match the user's preferred communication style
   - Adjust verbosity based on their preferences
   - Maintain consistency with your established personality

**Decision Process:**
1. Analyze the user's query in context of all available information
2. Determine if this can be answered directly or requires plugin execution
3. Craft a response that demonstrates your enhanced capabilities
4. Identify information worth storing in memory
5. Consider proactive suggestions based on the interaction

**Output Requirements:**
- Always provide a helpful, contextually aware response
- Set requiresPlugin=true only if external tool execution is needed
- Include memoryToStore for significant new information
- Add aiData with your reasoning and confidence level
- Provide proactiveSuggestion when you can anticipate user needs

Remember: You are not just answering questions - you are building a relationship with the user through persistent memory and intelligent assistance.`,
});

export async function processWithKarenBackend(input: KarenEnhancedInput): Promise<KarenEnhancedOutput> {
  const backend = getKarenBackend();
  
  try {
    // Enhance input with backend context if not already provided
    let enhancedInput = { ...input };
    
    // Fetch relevant memories if not provided
    if (!input.contextFromMemory && input.userId) {
      try {
        const memories = await backend.queryMemories({
          text: input.prompt,
          user_id: input.userId,
          session_id: input.sessionId,
          top_k: 5,
          similarity_threshold: 0.6,
        });
        
        enhancedInput.contextFromMemory = memories.map(mem => ({
          content: mem.content,
          similarity_score: mem.similarity_score,
          tags: mem.tags,
          timestamp: mem.timestamp,
        }));
      } catch (error) {
        console.warn('Failed to fetch memories:', error);
      }
    }
    
    // Fetch available plugins if not provided
    if (!input.availablePlugins) {
      try {
        const plugins = await backend.getAvailablePlugins();
        enhancedInput.availablePlugins = plugins.map(plugin => ({
          name: plugin.name,
          description: plugin.description,
          category: plugin.category,
          enabled: plugin.enabled,
        }));
      } catch (error) {
        console.warn('Failed to fetch plugins:', error);
      }
    }
    
    // Process with enhanced AI flow
    const result = await karenEnhancedFlow(enhancedInput);
    
    // Execute plugin if required
    if (result.requiresPlugin && result.pluginToExecute && input.userId) {
      try {
        const pluginResult = await backend.executePlugin(
          result.pluginToExecute,
          result.pluginParameters || {},
          input.userId
        );
        
        if (pluginResult.success) {
          // Update response with plugin results
          result.response += `\n\nPlugin execution completed successfully. ${pluginResult.result || ''}`;
        } else {
          result.response += `\n\nI encountered an issue executing the ${result.pluginToExecute} plugin: ${pluginResult.error}`;
        }
      } catch (error) {
        console.error('Plugin execution failed:', error);
        result.response += `\n\nI had trouble executing the requested plugin. Please try again.`;
      }
    }
    
    // Store memory if specified
    if (result.memoryToStore && input.userId) {
      try {
        await backend.storeMemory(
          result.memoryToStore.content,
          result.memoryToStore.metadata,
          result.memoryToStore.tags,
          input.userId,
          input.sessionId
        );
      } catch (error) {
        console.warn('Failed to store memory:', error);
      }
    }
    
    return result;
    
  } catch (error) {
    console.error('Karen enhanced flow failed:', error);
    
    // Fallback response
    return {
      response: "I'm experiencing some technical difficulties with my enhanced capabilities right now. Let me try to help you with a basic response.",
      requiresPlugin: false,
      aiData: {
        confidence: 0.3,
        reasoning: "Fallback response due to backend integration issues",
      },
    };
  }
}

const karenEnhancedFlow = ai.defineFlow(
  {
    name: 'karenEnhancedFlow',
    inputSchema: KarenEnhancedInputSchema,
    outputSchema: KarenEnhancedOutputSchema,
  },
  async (input) => {
    const result = await karenEnhancedPrompt(input);
    
    if (result.output) {
      // Ensure required fields have defaults
      result.output.requiresPlugin = result.output.requiresPlugin ?? false;
      
      // Clean up optional fields
      if (!result.output.pluginToExecute) {
        result.output.pluginParameters = undefined;
      }
      
      if (!result.output.memoryToStore?.content) {
        result.output.memoryToStore = undefined;
      }
      
      if (!result.output.suggestedActions?.length) {
        result.output.suggestedActions = undefined;
      }
      
      if (!result.output.proactiveSuggestion?.trim()) {
        result.output.proactiveSuggestion = undefined;
      }
      
      return result.output;
    } else {
      console.error('Karen enhanced flow: AI output issue');
      return {
        response: "I'm having trouble processing that request right now. Could you try rephrasing?",
        requiresPlugin: false,
        aiData: {
          confidence: 0.1,
          reasoning: "AI output processing failed",
        },
      };
    }
  }
);

// Utility function to convert to HandleUserMessageResult format
export function convertToHandleUserMessageResult(
  output: KarenEnhancedOutput,
  acknowledgement?: string
): HandleUserMessageResult {
  const aiData: AiData | undefined = output.aiData ? {
    keywords: output.aiData.keywords,
    knowledgeGraphInsights: output.aiData.knowledgeGraphInsights,
  } : undefined;
  
  return {
    acknowledgement,
    finalResponse: output.response,
    aiDataForFinalResponse: aiData,
    suggestedNewFacts: output.memoryToStore ? [output.memoryToStore.content] : undefined,
    proactiveSuggestion: output.proactiveSuggestion,
    summaryWasGenerated: false, // This would be handled separately
  };
}