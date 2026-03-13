/**
 * @fileOverview Core tool functions for Karen AI.
 * These are plain TypeScript functions that can be called directly.
 * Enhanced with provider-agnostic implementation and error handling.
 */

import type { TemperatureUnit, WeatherServiceOption } from '@/lib/types';
import { aiClientManager } from '@/ai/providers/ai-client-manager';

// Tool execution interface
export interface ToolResult {
  success: boolean;
  data?: any;
  error?: string;
  provider?: string;
  executionTime?: number;
}

// Tool registry for dynamic function calling
const TOOL_REGISTRY = {
  getCurrentDate: {
    name: 'getCurrentDate',
    description: 'Get the current date',
    parameters: {},
    execute: getCurrentDate,
  },
  getCurrentTime: {
    name: 'getCurrentTime',
    description: 'Get the current time, optionally for a specific location',
    parameters: {
      location: {
        type: 'string',
        description: 'Location to get time for (optional)',
        required: false,
      },
    },
    execute: getCurrentTime,
  },
  getWeather: {
    name: 'getWeather',
    description: 'Get current weather information for a location',
    parameters: {
      location: {
        type: 'string',
        description: 'Location to get weather for',
        required: true,
      },
      temperatureUnit: {
        type: 'string',
        description: 'Temperature unit (C or F)',
        required: false,
      },
    },
    execute: getWeather,
  },
  queryBookDatabase: {
    name: 'queryBookDatabase',
    description: 'Query the book database for information',
    parameters: {
      bookTitle: {
        type: 'string',
        description: 'Title of the book to search for',
        required: true,
      },
    },
    execute: queryBookDatabase,
  },
  checkGmailUnread: {
    name: 'checkGmailUnread',
    description: 'Check for unread Gmail messages',
    parameters: {},
    execute: checkGmailUnread,
  },
  composeGmail: {
    name: 'composeGmail',
    description: 'Compose and send a Gmail message',
    parameters: {
      recipient: {
        type: 'string',
        description: 'Email address of the recipient',
        required: true,
      },
      subject: {
        type: 'string',
        description: 'Email subject line',
        required: true,
      },
      body: {
        type: 'string',
        description: 'Email body content',
        required: true,
      },
    },
    execute: composeGmail,
  },
  // Memory management tools
  searchMemory: {
    name: 'searchMemory',
    description: 'Search through stored memories',
    parameters: {
      query: {
        type: 'string',
        description: 'Search query for memories',
        required: true,
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results to return',
        required: false,
      },
    },
    execute: searchMemory,
  },
  addMemory: {
    name: 'addMemory',
    description: 'Add a new memory item',
    parameters: {
      content: {
        type: 'string',
        description: 'Memory content to store',
        required: true,
      },
      type: {
        type: 'string',
        description: 'Type of memory (fact, preference, context)',
        required: true,
      },
      confidence: {
        type: 'number',
        description: 'Confidence score for this memory',
        required: false,
      },
    },
    execute: addMemory,
  },
  // File management tools
  uploadFile: {
    name: 'uploadFile',
    description: 'Upload and process a file',
    parameters: {
      file: {
        type: 'file',
        description: 'File to upload',
        required: true,
      },
      description: {
        type: 'string',
        description: 'File description',
        required: false,
      },
    },
    execute: uploadFile,
  },
  analyzeFile: {
    name: 'analyzeFile',
    description: 'Analyze content of an uploaded file',
    parameters: {
      fileId: {
        type: 'string',
        description: 'ID of the file to analyze',
        required: true,
      },
      analysisType: {
        type: 'string',
        description: 'Type of analysis to perform',
        required: false,
      },
    },
    execute: analyzeFile,
  },
};

// Enhanced tool implementations with error handling and logging
export async function getCurrentDate(): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    const result = new Date().toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    
    return {
      success: true,
      data: result,
      executionTime: Date.now() - startTime,
    };
  } catch (error) {
    console.error('Error in getCurrentDate:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      executionTime: Date.now() - startTime,
    };
  }
}

export async function getCurrentTime(location?: string): Promise<ToolResult> {
  const startTime = Date.now();
  const logs: string[] = [];
  logs.push(`getCurrentTime called with location: "${location || 'none'}"`);
  
  try {
    const originalLocation = location?.trim();
    
    if (!originalLocation) {
      const serverTime = new Date().toLocaleTimeString(undefined, {
        hour: 'numeric',
        minute: '2-digit',
      });
      const result = `The current time (for me) is ${serverTime}. If you'd like time for a specific place, please tell me location.`;
      logs.push(`getCurrentTime: No location provided, returning server time: ${result}`);
      console.log(logs.join('\n'));
      
      return {
        success: true,
        data: result,
        executionTime: Date.now() - startTime,
      };
    }
    
    // Try multiple time APIs with fallback
    const timeApis = [
      {
        name: 'timeapi.io',
        url: (loc: string) => `https://timeapi.io/api/Time/current/zone?timeZone=${encodeURIComponent(loc.replace(/, /g, '/').replace(/ /g, '_'))}`,
        parseResponse: (data: any) => {
          if (data && data.dateTime && data.timeZone) {
            const timeInLocation = new Date(data.dateTime);
            return {
              time: timeInLocation.toLocaleTimeString(undefined, {
                hour: 'numeric',
                minute: '2-digit',
              }),
              location: data.timeZone.replace(/_/g, ' '),
            };
          }
          return null;
        },
      },
    {
      name: 'WorldTimeAPI',
      url: (loc: string) => `https://worldtimeapi.org/api/timezone/${encodeURIComponent(loc)}`,
      parseResponse: (data: any) => {
        if (data && data.datetime && data.timezone) {
          const timeInLocation = new Date(data.datetime);
          return {
            time: timeInLocation.toLocaleTimeString(undefined, {
              hour: 'numeric',
              minute: '2-digit',
            }),
            location: data.timezone.replace(/_/g, ' '),
          };
        }
        return null;
      },
    },
  ];
    
    // Try each API in sequence
    for (const api of timeApis) {
      try {
        const apiUrl = api.url(originalLocation);
        logs.push(`getCurrentTime: Attempting ${api.name}: ${apiUrl}`);
        
        const response = await fetch(apiUrl);
        const responseText = await response.text();
        logs.push(`getCurrentTime: ${api.name} response status: ${response.status}, body: ${responseText.substring(0, 200)}`);
        
        if (!response.ok) {
          let errorDetail = `${api.name} error: Status ${response.status}.`;
          try {
            const errorData = JSON.parse(responseText);
            if (errorData && (errorData.message || errorData.Message)) {
              errorDetail += ` Message: ${errorData.message || errorData.Message}`;
            }
            if (responseText.includes("not found") || responseText.includes("Invalid timeZone")) {
              errorDetail += ` Location "${originalLocation}" likely not recognized by ${api.name}.`;
            }
          } catch (e) { /* ignore if not json */ }
          throw new Error(errorDetail);
        }
        
        const data = JSON.parse(responseText);
        const parsed = api.parseResponse(data);
        
        if (parsed) {
          const successMsg = `The current time in ${parsed.location} is ${parsed.time}.`;
          logs.push(`getCurrentTime: ${api.name} Success for "${originalLocation}": ${successMsg}`);
          console.log(logs.join('\n'));
          
          return {
            success: true,
            data: successMsg,
            executionTime: Date.now() - startTime,
          };
        }
        
        throw new Error(`${api.name} returned unexpected data for "${originalLocation}".`);
      } catch (error) {
        logs.push(`getCurrentTime: ${api.name} Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        continue;
      }
    }
    
    // All APIs failed
    const errorMessage = `I couldn't get time for "${originalLocation}". All attempts failed. Please check the location name and format or try a nearby major city.`;
    logs.push(`getCurrentTime: All attempts failed for "${originalLocation}". Final log: ${logs.join(' --- ')}`);
    console.warn(logs.join('\n'));
    
    return {
      success: false,
      error: errorMessage,
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Unexpected error in getCurrentTime:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unexpected error occurred',
      executionTime: Date.now() - startTime,
    };
  }
}

export async function getWeather(
  locationFromPrompt?: string,
  temperatureUnit: TemperatureUnit = 'C',
  service: WeatherServiceOption = 'wttr_in',
  apiKey?: string | null,
  defaultLocationFromSettings?: string | null
): Promise<ToolResult> {
  const startTime = Date.now();
  const logs: string[] = [];
  const locationToUse = locationFromPrompt?.trim() || defaultLocationFromSettings?.trim();
  
  logs.push(`getWeather called with: locationFromPrompt="${locationFromPrompt}", temperatureUnit="${temperatureUnit}", service="${service}", defaultLocationFromSettings="${defaultLocationFromSettings}"`);
  logs.push(`Effective locationToUse: "${locationToUse}"`);
  
  try {
    if (!locationToUse || locationToUse.trim() === "") {
      logs.push("getWeather: No location specified.");
      console.log(logs.join('\n'));
      
      return {
        success: false,
        error: "Please specify a location for weather. For example, you can ask 'what's the weather in London?'",
        executionTime: Date.now() - startTime,
      };
    }
    
    const wttrUrl = `https://wttr.in/${encodeURIComponent(locationToUse)}?format=j1`;
    logs.push(`getWeather: Attempting to fetch weather from wttr.in: ${wttrUrl}`);
    
    const response = await fetch(wttrUrl);
    const responseText = await response.text();
    logs.push(`getWeather: wttr.in response status: ${response.status}, body: ${responseText.substring(0, 300)}`);
    
    if (!response.ok) {
      let errorInfo = `HTTP error ${response.status}`;
      if (responseText.includes("Unknown location")) {
        errorInfo = `Unknown location "${locationToUse}" according to wttr.in.`;
      } else if (responseText.length > 0 && responseText.length < 100) {
        errorInfo += ` - Server message: ${responseText}`;
      }
      throw new Error(`Failed to fetch weather for "${locationToUse}". ${errorInfo}`);
    }
    
    const data = JSON.parse(responseText);
    
    if (data && data.current_condition && data.current_condition[0]) {
      const currentCondition = data.current_condition[0];
      const description = currentCondition.weatherDesc && currentCondition.weatherDesc[0] ? currentCondition.weatherDesc[0].value : "Not available";
      
      let temp = parseFloat(currentCondition.temp_C);
      let feelsLike = parseFloat(currentCondition.FeelsLikeC);
      let unitSymbol = '°C';
      
      if (temperatureUnit === 'F') {
        temp = (temp * 9/5) + 32;
        feelsLike = (feelsLike * 9/5) + 32;
        unitSymbol = '°F';
      }
      
      const tempStr = temp.toFixed(0);
      const feelsLikeStr = feelsLike.toFixed(0);
      
      const humidity = currentCondition.humidity;
      const windSpeedKmph = currentCondition.windspeedKmph;
      
      let weatherString = `Currently in ${locationToUse}: ${description}. The temperature is ${tempStr}${unitSymbol} (feels like ${feelsLikeStr}${unitSymbol}).`;
      if (humidity) {
        weatherString += ` Humidity is at ${humidity}%.`;
      }
      if (windSpeedKmph) {
        weatherString += ` Wind speed is ${windSpeedKmph} km/h.`;
      }
      
      logs.push(`getWeather: Success for "${locationToUse}": ${weatherString}`);
      console.log(logs.join('\n'));
      
      return {
        success: true,
        data: weatherString,
        executionTime: Date.now() - startTime,
      };
      
    } else if (data && data.nearest_area && data.nearest_area[0] && data.nearest_area[0].areaName && data.nearest_area[0].areaName[0].value.toLowerCase().includes("unknown")) {
      logs.push(`getWeather: Unknown location indicated by nearest_area for "${locationToUse}"`);
      throw new Error(`Sorry, I couldn't find weather data for "${locationToUse}". Please ensure the location is correct.`);
    } else if (data && data.weather && data.weather[0] && data.weather[0].maxtempC === "0" && data.weather[0].mintempC === "0") {
      logs.push(`getWeather: Weather data for "${locationToUse}" seems invalid.`);
      throw new Error(`Sorry, I couldn't find reliable weather data for "${locationToUse}". Please check if the location is correct.`);
    } else {
      logs.push(`getWeather: Unexpected data structure from wttr.in for location: ${locationToUse}`);
      throw new Error(`Sorry, I received an unexpected response when fetching weather for "${locationToUse}".`);
    }
    
  } catch (error) {
    logs.push(`getWeather: Network or other error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    console.warn(logs.join('\n'));
    
    const baseErrorMessage = error instanceof Error && (error.message.startsWith("Sorry, I couldn't find") || error.message.startsWith("Failed to fetch weather"))
      ? error.message
      : `Sorry, I encountered an error while trying to fetch weather for "${locationToUse}". Please check your connection or try again.`;
    
    return {
      success: false,
      error: baseErrorMessage,
      executionTime: Date.now() - startTime,
    };
  }
}

export async function queryBookDatabase(bookTitle?: string): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log(`queryBookDatabase: Called for bookTitle="${bookTitle || 'none'}"`);
    
    if (!bookTitle || bookTitle.trim() === "") {
      return {
        success: false,
        error: "I need a book title to look up details. Which book are you interested in?",
        executionTime: Date.now() - startTime,
      };
    }
    
    // Simulate database lookup delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock book database
    const bookDatabase = {
      "dune": {
        title: bookTitle,
        author: "Frank Herbert",
        genre: "Science Fiction",
        summary: "Dune is a 1965 science fiction novel by American author Frank Herbert, originally published as two separate serials in Analog magazine. It tied with Roger Zelazny's This Immortal for Hugo Award in 1966 and it won the inaugural Nebula Award for Best Novel.",
        publishedYear: 1965
      },
      "gatsby": {
        title: bookTitle,
        author: "F. Scott Fitzgerald",
        genre: "Novel",
        summary: "The Great Gatsby is a 1925 novel by American writer F. Scott Fitzgerald. Set in the Jazz Age on Long Island, near New York, the novel depicts first-person narrator Nick Carraway's interactions with mysterious millionaire Jay Gatsby and Gatsby's obsession to reunite with his former lover, Daisy Buchanan.",
        publishedYear: 1925
      },
    };
    
    const normalizedTitle = bookTitle.toLowerCase();
    let result = null;
    
    for (const [key, book] of Object.entries(bookDatabase)) {
      if (normalizedTitle.includes(key)) {
        result = book;
        break;
      }
    }
    
    if (result) {
      return {
        success: true,
        data: result,
        executionTime: Date.now() - startTime,
      };
    } else {
      return {
        success: false,
        error: `Sorry, I couldn't find detailed information for item titled "${bookTitle}" in the database.`,
        executionTime: Date.now() - startTime,
      };
    }
    
  } catch (error) {
    console.error('Error in queryBookDatabase:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      executionTime: Date.now() - startTime,
    };
  }
}

// Mocked Gmail Tools with enhanced error handling
export async function checkGmailUnread(): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log("checkGmailUnread: Called");
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 700));
    
    const mockData = {
      unreadCount: 2,
      emails: [
        { from: "Alice Wonderland", subject: "Tea Party Invitation", snippet: "You're invited to a mad tea party!" },
        { from: "Hacker News Digest", subject: "Top Stories for Today", snippet: "Check out the latest in tech..." }
      ]
    };
    
    return {
      success: true,
      data: mockData,
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in checkGmailUnread:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to check Gmail',
      executionTime: Date.now() - startTime,
    };
  }
}

export async function composeGmail(input: {
  recipient?: string;
  subject?: string;
  body?: string;
}): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log("composeGmail: Called with input:", input);
    
    // Validate required fields
    const missing: string[] = [];
    if (!input.recipient) missing.push("recipient");
    if (!input.subject) missing.push("subject");
    if (!input.body) missing.push("body");
    
    if (missing.length > 0) {
      return {
        success: false,
        error: `I'm missing some details to compose the email. I still need ${missing.join(', ')}. Could you provide them?`,
        executionTime: Date.now() - startTime,
      };
    }
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      success: true,
      data: `Okay, I've "sent" an email to ${input.recipient} with the subject "${input.subject}".`,
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in composeGmail:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to compose email',
      executionTime: Date.now() - startTime,
    };
  }
}

// Memory management tools
export async function searchMemory(query: string, limit: number = 10): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log(`searchMemory: Called with query="${query}", limit=${limit}`);
    
    // This would integrate with actual memory system
    // For now, return mock results
    const mockMemories = [
      { id: '1', content: 'User prefers dark mode', relevance: 0.9, timestamp: '2024-01-15' },
      { id: '2', content: 'User works in software development', relevance: 0.8, timestamp: '2024-01-10' },
      { id: '3', content: 'User mentioned they have a cat named Whiskers', relevance: 0.7, timestamp: '2024-01-05' },
    ];
    
    const filteredMemories = mockMemories
      .filter(memory => 
        memory.content.toLowerCase().includes(query.toLowerCase())
      )
      .slice(0, limit);
    
    return {
      success: true,
      data: filteredMemories,
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in searchMemory:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to search memory',
      executionTime: Date.now() - startTime,
    };
  }
}

export async function addMemory(content: string, type: string, confidence: number = 0.8): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log(`addMemory: Called with content="${content}", type="${type}", confidence=${confidence}`);
    
    // This would integrate with actual memory system
    const memoryId = `memory_${Date.now()}`;
    
    return {
      success: true,
      data: {
        id: memoryId,
        content,
        type,
        confidence,
        timestamp: new Date().toISOString(),
      },
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in addMemory:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to add memory',
      executionTime: Date.now() - startTime,
    };
  }
}

// File management tools
export async function uploadFile(file: File, description?: string): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log(`uploadFile: Called with file="${file.name}", description="${description}"`);
    
    // This would integrate with actual file storage system
    // For now, simulate upload
    const fileId = `file_${Date.now()}_${file.name}`;
    
    return {
      success: true,
      data: {
        id: fileId,
        name: file.name,
        size: file.size,
        type: file.type,
        description,
        uploadedAt: new Date().toISOString(),
      },
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in uploadFile:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to upload file',
      executionTime: Date.now() - startTime,
    };
  }
}

export async function analyzeFile(fileId: string, analysisType: string = 'summary'): Promise<ToolResult> {
  const startTime = Date.now();
  
  try {
    console.log(`analyzeFile: Called with fileId="${fileId}", analysisType="${analysisType}"`);
    
    // This would integrate with actual file analysis system
    // For now, simulate analysis
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockAnalysis = {
      summary: 'This document contains important information about...',
      keyPoints: ['Point 1', 'Point 2', 'Point 3'],
      sentiment: 'neutral',
      confidence: 0.85,
    };
    
    return {
      success: true,
      data: mockAnalysis,
      executionTime: Date.now() - startTime,
    };
    
  } catch (error) {
    console.error('Error in analyzeFile:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to analyze file',
      executionTime: Date.now() - startTime,
    };
  }
}

// Tool execution helper
export async function executeTool(toolName: string, parameters: any = {}): Promise<ToolResult> {
  const tool = TOOL_REGISTRY[toolName as keyof typeof TOOL_REGISTRY];
  
  if (!tool) {
    return {
      success: false,
      error: `Unknown tool: ${toolName}`,
      executionTime: 0,
    };
  }
  
  try {
    // Handle different function signatures
    switch (toolName) {
      case 'getCurrentDate':
        return await getCurrentDate();
      case 'getCurrentTime':
        return await getCurrentTime(parameters?.location);
      case 'getWeather':
        return await getWeather(
          parameters?.locationFromPrompt,
          parameters?.temperatureUnit,
          parameters?.service,
          parameters?.apiKey,
          parameters?.defaultLocationFromSettings
        );
      case 'queryBookDatabase':
        return await queryBookDatabase(parameters?.bookTitle);
      case 'checkGmailUnread':
        return await checkGmailUnread();
      case 'composeGmail':
        return await composeGmail(parameters);
      case 'searchMemory':
        return await searchMemory(parameters?.query, parameters?.limit);
      case 'addMemory':
        return await addMemory(parameters?.content, parameters?.type, parameters?.confidence);
      case 'uploadFile':
        return await uploadFile(parameters?.file, parameters?.description);
      case 'analyzeFile':
        return await analyzeFile(parameters?.fileId, parameters?.analysisType);
    }
    
    // Should never reach here, but TypeScript needs a return
    return {
      success: false,
      error: `Unknown tool: ${toolName}`,
      executionTime: 0,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Tool execution failed',
      executionTime: 0,
    };
  }
}