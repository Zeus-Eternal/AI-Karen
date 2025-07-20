
'use server';

import { decideAction, type DecideActionInput, type DecideActionOutput } from '@/ai/flows/decide-action-flow';
import { generateFinalResponse, type GenerateFinalResponseInput, type GenerateFinalResponseOutput } from '@/ai/flows/generate-final-response-flow';
import { generateInitialPrompt, type GenerateInitialPromptInput, type GenerateInitialPromptOutput } from '@/ai/flows/generate-initial-prompt';
import { summarizeConversation, type SummarizeConversationInput, type SummarizeConversationOutput } from '@/ai/flows/summarize-conversation';
import { 
  getCurrentDate, 
  getCurrentTime, 
  getWeather, 
  mockQueryBookDatabase, 
  mockCheckGmailUnread, 
  mockComposeGmail,
  executeKarenPlugin,
  queryKarenMemory,
  storeKarenMemory,
  getKarenSystemStatus,
  getKarenAnalytics
} from '@/ai/tools/core-tools'; 
import { 
  processWithKarenBackend, 
  convertToHandleUserMessageResult,
  type KarenEnhancedInput 
} from '@/ai/flows/karen-enhanced-flow';
import { getKarenBackend } from '@/lib/karen-backend';

import type { AiData, KarenSettings, HandleUserMessageResult, ChatMessage } from '@/lib/types';
import { DEFAULT_KAREN_SETTINGS } from '@/lib/constants';


export async function handleUserMessage(
  prompt: string,
  conversationHistory: string,
  settings: KarenSettings | null,
  totalMessagesSoFar: number 
): Promise<HandleUserMessageResult> {
  try {
    const currentSettings = settings || DEFAULT_KAREN_SETTINGS;

    const derivedKeywords = prompt.toLowerCase().split(' ').filter(w => w.length > 4 && !['the', 'a', 'is', 'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'an'].includes(w)).slice(0, 5);
    let derivedKnowledgeGraphInsights = "No specific knowledge graph insights for this query.";
    if (prompt.toLowerCase().includes("memory")) {
        derivedKnowledgeGraphInsights = "Memory functions involve encoding, storage, and retrieval processes in the brain.";
    }

    const decideActionInput: DecideActionInput = {
      prompt,
      shortTermMemory: conversationHistory,
      keywords: derivedKeywords.length > 0 ? derivedKeywords : undefined,
      knowledgeGraphInsights: derivedKeywords.length > 0 ? derivedKnowledgeGraphInsights : undefined,
      memoryDepth: currentSettings.memoryDepth,
      personalityTone: currentSettings.personalityTone,
      personalityVerbosity: currentSettings.personalityVerbosity,
      personalFacts: currentSettings.personalFacts.length > 0 ? currentSettings.personalFacts : undefined,
      customPersonaInstructions: currentSettings.customPersonaInstructions || undefined,
    };

    const decision: DecideActionOutput = await decideAction(decideActionInput);

    let acknowledgement: string | undefined = undefined;
    let finalResponse: string;
    let aiDataForFinalResponse: AiData | undefined = undefined;
    let allSuggestedNewFacts: string[] = decision.suggestedNewFacts || [];
    let proactiveSuggestion: string | undefined = decision.proactiveSuggestion;
    let summaryWasGenerated = false;

    const askedForBookTitle = decision.toolToCall === 'queryBookDatabase' && !decision.toolInput?.bookTitle && decision.intermediateResponse.toLowerCase().includes("which book");
    const askedForWeatherLocation = decision.toolToCall === 'getWeather' && !decision.toolInput?.location && decision.intermediateResponse.toLowerCase().includes("what location");
    const askedForGmailDetails = decision.toolToCall === 'composeGmail' && 
                                 (!decision.toolInput?.gmailRecipient || !decision.toolInput?.gmailSubject || !decision.toolInput?.gmailBody) && 
                                 (decision.intermediateResponse.toLowerCase().includes("recipient") || decision.intermediateResponse.toLowerCase().includes("subject") || decision.intermediateResponse.toLowerCase().includes("body"));
    
    if (decision.toolToCall && decision.toolToCall !== 'none' && (askedForBookTitle || askedForWeatherLocation || askedForGmailDetails)) {
        finalResponse = decision.intermediateResponse;
    } else if (decision.toolToCall && decision.toolToCall !== 'none') {
        acknowledgement = decision.intermediateResponse; 
        let toolOutput: string | null = null;

        try {
            switch (decision.toolToCall) {
            case 'getCurrentDate':
                toolOutput = await getCurrentDate();
                break;
            case 'getCurrentTime':
                toolOutput = await getCurrentTime(decision.toolInput?.location);
                break;
            case 'getWeather':
                toolOutput = await getWeather(
                  decision.toolInput?.location, 
                  currentSettings.temperatureUnit,
                  currentSettings.weatherService,
                  currentSettings.weatherApiKey,
                  currentSettings.defaultWeatherLocation
                ); 
                break;
            case 'queryBookDatabase':
                toolOutput = await mockQueryBookDatabase(decision.toolInput?.bookTitle);
                break;
            case 'checkGmailUnread':
                toolOutput = await mockCheckGmailUnread();
                break;
            case 'composeGmail':
                toolOutput = await mockComposeGmail({ 
                    gmailRecipient: decision.toolInput?.gmailRecipient, 
                    gmailSubject: decision.toolInput?.gmailSubject, 
                    gmailBody: decision.toolInput?.gmailBody 
                });
                break;
            default:
                console.warn("Unknown tool or unexpected tool state:", decision.toolToCall);
                toolOutput = "I was about to use a tool, but something went wrong with choosing which one or its input.";
            }
        } catch (toolError) {
            console.error(`Error executing tool ${decision.toolToCall}:`, toolError);
            toolOutput = `I tried to use my ${decision.toolToCall} tool, but it ran into an issue.`;
        }
        
        if (toolOutput !== null) {
            const finalResponseInput: GenerateFinalResponseInput = {
            originalPrompt: prompt,
            toolUsed: decision.toolToCall as any, 
            toolOutput: toolOutput,
            shortTermMemory: conversationHistory,
            memoryDepth: currentSettings.memoryDepth,
            personalityTone: currentSettings.personalityTone,
            personalityVerbosity: currentSettings.personalityVerbosity,
            personalFacts: currentSettings.personalFacts.length > 0 ? currentSettings.personalFacts : undefined,
            customPersonaInstructions: currentSettings.customPersonaInstructions || undefined,
            };
            const finalResult: GenerateFinalResponseOutput = await generateFinalResponse(finalResponseInput);
            finalResponse = finalResult.finalResponse;
            if (finalResult.suggestedNewFacts && finalResult.suggestedNewFacts.length > 0) {
               allSuggestedNewFacts = [...new Set([...allSuggestedNewFacts, ...finalResult.suggestedNewFacts])];
            }
            proactiveSuggestion = finalResult.proactiveSuggestion || proactiveSuggestion; 
        } else {
            finalResponse = "I tried to use one of my tools, but something went wrong in the process of getting its result.";
        }
    } else { 
      finalResponse = decision.intermediateResponse;
    }
    
    if (derivedKeywords.length > 0 && finalResponse && !askedForBookTitle && !askedForWeatherLocation && !askedForGmailDetails) {
      aiDataForFinalResponse = {
        keywords: derivedKeywords,
        knowledgeGraphInsights: derivedKnowledgeGraphInsights,
      };
    }

    const messagesInThisExchange = (acknowledgement ? 1 : 0) + 1 + (proactiveSuggestion ? 1 : 0); 
    const futureTotalMessages = totalMessagesSoFar + messagesInThisExchange;

    if (currentSettings.notifications.enabled && currentSettings.notifications.alertOnSummaryReady && futureTotalMessages > 0 && futureTotalMessages % 7 === 0) {
      try {
        const fullConversationForSummary = conversationHistory + `\nUser: ${prompt}\nKaren: ${acknowledgement ? acknowledgement + '\nKaren: ' : ''}${finalResponse}${proactiveSuggestion ? '\nKaren: ' + proactiveSuggestion : ''}`;
        const summaryInput: SummarizeConversationInput = { conversationHistory: fullConversationForSummary };
        const summaryResult: SummarizeConversationOutput = await summarizeConversation(summaryInput);
        console.log("AI Generated Conversation Summary:", summaryResult.summary);
        summaryWasGenerated = true;
      } catch (summaryError) {
        console.error("Error generating conversation summary:", summaryError);
      }
    }

    return {
      acknowledgement,
      finalResponse,
      aiDataForFinalResponse,
      suggestedNewFacts: allSuggestedNewFacts.length > 0 ? allSuggestedNewFacts : undefined,
      proactiveSuggestion: proactiveSuggestion || undefined,
      summaryWasGenerated, 
    };

  } catch (error) {
    console.error('Error in handleUserMessage orchestrator:', error);
    let displayMessage = 'Karen: I apologize, but I encountered an issue while processing your request. Please try again.';
    
    if (error instanceof Error && error.message) {
      if (error.message.includes("API key not valid") || error.message.includes("API_KEY_INVALID")) {
        displayMessage = `Karen: There seems to be an issue with the Google AI API key. Please go to Settings > API Key for detailed setup instructions. The key needs to be in a .env file at your project root, and the Genkit server must be restarted.`;
      } else if (
        error.message.includes("INVALID_ARGUMENT") &&
        error.message.includes("Schema validation failed") &&
        /Provided data:\s*null/.test(error.message) && 
        (error.message.includes("(root): must be object") || error.message.includes("Expected object")) 
      ) {
        displayMessage = `Karen: I'm having a little trouble formulating a response right now. This can sometimes happen if the request is very complex or if content filters are active. Could you try rephrasing your request?`;
      } else if (error.message.startsWith("Karen: ")) { 
        displayMessage = error.message;
      } else {
        displayMessage = `Karen: I encountered an issue processing your request. Details: ${error.message.substring(0,200)}... Please try again.`;
      }
    }
    return { 
      finalResponse: displayMessage, 
      suggestedNewFacts: undefined,
      proactiveSuggestion: undefined,
      summaryWasGenerated: false,
    };
  }
}

export async function getSuggestedStarter(assistantType: string): Promise<string> {
  try {
    const input: GenerateInitialPromptInput = { assistantType };
    const result: GenerateInitialPromptOutput = await generateInitialPrompt(input);
    return result.initialPrompt;
  } catch (error) {
    console.error('Error getting suggested starter:', error);
    return "I had trouble thinking of a starter prompt right now. How about you start with 'Tell me something interesting'?";
  }
}


// Enhanced AI Karen Backend Integration
export async function handleUserMessageWithKarenBackend(
  prompt: string,
  conversationHistory: ChatMessage[],
  settings: KarenSettings | null,
  userId?: string,
  sessionId?: string
): Promise<HandleUserMessageResult> {
  try {
    const currentSettings = settings || DEFAULT_KAREN_SETTINGS;
    
    // Try to use the enhanced Karen backend integration first
    const karenInput: KarenEnhancedInput = {
      prompt,
      conversationHistory: conversationHistory
        .map(msg => `${msg.role === 'user' ? 'User' : 'Karen'}: ${msg.content}`)
        .join('\n'),
      userId,
      sessionId,
      settings: {
        memoryDepth: currentSettings.memoryDepth,
        personalityTone: currentSettings.personalityTone,
        personalityVerbosity: currentSettings.personalityVerbosity,
        personalFacts: currentSettings.personalFacts.length > 0 ? currentSettings.personalFacts : undefined,
        customPersonaInstructions: currentSettings.customPersonaInstructions || undefined,
      },
    };
    
    try {
      // Process with enhanced Karen backend
      const karenOutput = await processWithKarenBackend(karenInput);
      
      // Convert to the expected format
      const result = convertToHandleUserMessageResult(karenOutput);
      
      // Add summary generation if needed
      const totalMessages = conversationHistory.length + 1;
      if (currentSettings.notifications.enabled && 
          currentSettings.notifications.alertOnSummaryReady && 
          totalMessages > 0 && totalMessages % 7 === 0) {
        try {
          const fullConversation = karenInput.conversationHistory + `\nUser: ${prompt}\nKaren: ${result.finalResponse}`;
          const summaryInput: SummarizeConversationInput = { conversationHistory: fullConversation };
          const summaryResult: SummarizeConversationOutput = await summarizeConversation(summaryInput);
          console.log("AI Generated Conversation Summary:", summaryResult.summary);
          result.summaryWasGenerated = true;
        } catch (summaryError) {
          console.error("Error generating conversation summary:", summaryError);
        }
      }
      
      return result;
      
    } catch (karenError) {
      console.warn('Karen backend integration failed, falling back to standard processing:', karenError);
      
      // Fallback to the original handleUserMessage function
      const conversationHistoryString = conversationHistory
        .map(msg => `${msg.role === 'user' ? 'User' : 'Karen'}: ${msg.content}`)
        .join('\n');
      
      return await handleUserMessage(
        prompt,
        conversationHistoryString,
        settings,
        conversationHistory.length
      );
    }
    
  } catch (error) {
    console.error('Error in handleUserMessageWithKarenBackend:', error);
    return {
      finalResponse: "I'm experiencing some technical difficulties right now. Please try again in a moment.",
      summaryWasGenerated: false,
    };
  }
}

// Karen Backend System Integration Functions
export async function getKarenSystemHealth(): Promise<{
  status: string;
  services: Record<string, any>;
  metrics: Record<string, any>;
}> {
  try {
    const backend = getKarenBackend();
    const [health, metrics] = await Promise.all([
      backend.healthCheck(),
      backend.getSystemMetrics()
    ]);
    
    return {
      status: health.status,
      services: health.services,
      metrics: {
        cpu_usage: metrics.cpu_usage,
        memory_usage: metrics.memory_usage,
        active_sessions: metrics.active_sessions,
        uptime_hours: metrics.uptime_hours,
        response_time_avg: metrics.response_time_avg,
      }
    };
  } catch (error) {
    console.error('Failed to get Karen system health:', error);
    return {
      status: 'error',
      services: {},
      metrics: {}
    };
  }
}

export async function getKarenPlugins(): Promise<Array<{
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  version: string;
}>> {
  try {
    const backend = getKarenBackend();
    return await backend.getAvailablePlugins();
  } catch (error) {
    console.error('Failed to get Karen plugins:', error);
    return [];
  }
}

export async function executeKarenPluginAction(
  pluginName: string,
  parameters: Record<string, any>,
  userId?: string
): Promise<{
  success: boolean;
  result?: any;
  error?: string;
}> {
  try {
    const backend = getKarenBackend();
    const result = await backend.executePlugin(pluginName, parameters, userId);
    
    return {
      success: result.success,
      result: result.result,
      error: result.error,
    };
  } catch (error) {
    console.error(`Failed to execute Karen plugin ${pluginName}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

export async function searchKarenMemories(
  query: string,
  userId?: string,
  sessionId?: string,
  options: {
    topK?: number;
    similarityThreshold?: number;
    tags?: string[];
  } = {}
): Promise<Array<{
  content: string;
  similarity_score?: number;
  tags: string[];
  timestamp: number;
}>> {
  try {
    const backend = getKarenBackend();
    return await backend.queryMemories({
      text: query,
      user_id: userId,
      session_id: sessionId,
      top_k: options.topK || 10,
      similarity_threshold: options.similarityThreshold || 0.6,
      tags: options.tags,
    });
  } catch (error) {
    console.error('Failed to search Karen memories:', error);
    return [];
  }
}

export async function getKarenAnalyticsData(timeRange: string = '24h'): Promise<{
  total_interactions: number;
  unique_users: number;
  popular_features: Array<{ name: string; usage_count: number }>;
  user_satisfaction: number;
}> {
  try {
    const backend = getKarenBackend();
    return await backend.getUsageAnalytics(timeRange);
  } catch (error) {
    console.error('Failed to get Karen analytics:', error);
    return {
      total_interactions: 0,
      unique_users: 0,
      popular_features: [],
      user_satisfaction: 0,
    };
  }
}