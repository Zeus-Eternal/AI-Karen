/**
 * Action Registry System for Suggested Actions
 * 
 * Features:
 * - Event-driven action system
 * - Support for add_task, pin_memory, open_doc, export_note actions
 * - Wire action suggestions from copilot responses to existing UI service methods
 * - Extensible action registration system
 * - Type-safe action handling
 */

import { useToast } from '@/hooks/use-toast';
import { getMemoryService } from '@/services/memoryService';
import { getChatService } from '@/services/chatService';

export interface SuggestedAction {
  type: 'add_task' | 'pin_memory' | 'open_doc' | 'export_note' | 'search_memory' | 'create_conversation';
  params?: Record<string, any>;
  confidence?: number;
  description?: string;
  icon?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface ActionResult {
  success: boolean;
  message?: string;
  data?: any;
  error?: string;
}

export interface ActionHandler {
  type: string;
  handler: (params: Record<string, any>) => Promise<ActionResult>;
  description: string;
  requiredParams?: string[];
  optionalParams?: string[];
}

/**
 * Action Registry for managing suggested actions
 */
export class ActionRegistry {
  private handlers = new Map<string, ActionHandler>();
  private eventListeners = new Map<string, Set<(event: CustomEvent) => void>>();
  private memoryService = getMemoryService();
  private chatService = getChatService();

  constructor() {
    this.registerDefaultHandlers();
    this.setupEventListeners();
  }

  /**
   * Register default action handlers
   */
  private registerDefaultHandlers(): void {
    // Add Task Action
    this.registerHandler({
      type: 'add_task',
      handler: async (params) => {
        const { title, description, priority = 'medium', dueDate, tags = [] } = params;
        
        if (!title) {
          return { success: false, error: 'Task title is required' };
        }

        try {
          // Store task in memory with appropriate tags
          const taskMemoryId = await this.memoryService.storeMemory(
            `Task: ${title}${description ? ` - ${description}` : ''}`,
            {
              tags: ['task', 'todo', ...tags],
              metadata: {
                type: 'task',
                title,
                description,
                priority,
                dueDate,
                status: 'pending',
                createdAt: new Date().toISOString()
              }
            }
          );

          // Dispatch custom event for UI components
          this.dispatchEvent('kari:task_added', {
            taskId: taskMemoryId,
            title,
            description,
            priority,
            dueDate,
            tags
          });

          return {
            success: true,
            message: `Task "${title}" added successfully`,
            data: { taskId: taskMemoryId, title }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to add task: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Add a new task to the task list',
      requiredParams: ['title'],
      optionalParams: ['description', 'priority', 'dueDate', 'tags']
    });

    // Pin Memory Action
    this.registerHandler({
      type: 'pin_memory',
      handler: async (params) => {
        const { content, title, tags = [], importance = 8 } = params;
        
        if (!content) {
          return { success: false, error: 'Memory content is required' };
        }

        try {
          // Store memory with high importance and pinned tag
          const memoryId = await this.memoryService.storeMemory(
            content,
            {
              tags: ['pinned', 'important', ...tags],
              metadata: {
                type: 'pinned_memory',
                title: title || content.substring(0, 50) + '...',
                importance,
                pinnedAt: new Date().toISOString()
              }
            }
          );

          // Dispatch custom event
          this.dispatchEvent('kari:memory_pinned', {
            memoryId,
            content: content.substring(0, 100) + '...',
            title,
            importance
          });

          return {
            success: true,
            message: 'Memory pinned successfully',
            data: { memoryId, title: title || 'Pinned Memory' }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to pin memory: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Pin important information to memory',
      requiredParams: ['content'],
      optionalParams: ['title', 'tags', 'importance']
    });

    // Open Document Action
    this.registerHandler({
      type: 'open_doc',
      handler: async (params) => {
        const { url, title, type = 'external' } = params;
        
        if (!url) {
          return { success: false, error: 'Document URL is required' };
        }

        try {
          // Dispatch event to open document
          this.dispatchEvent('kari:document_open', {
            url,
            title: title || 'Document',
            type,
            openedAt: new Date().toISOString()
          });

          // Store reference in memory
          await this.memoryService.storeMemory(
            `Opened document: ${title || url}`,
            {
              tags: ['document', 'reference', type],
              metadata: {
                type: 'document_reference',
                url,
                title,
                documentType: type,
                accessedAt: new Date().toISOString()
              }
            }
          );

          return {
            success: true,
            message: `Document "${title || 'Document'}" opened`,
            data: { url, title, type }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to open document: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Open a document or URL',
      requiredParams: ['url'],
      optionalParams: ['title', 'type']
    });

    // Export Note Action
    this.registerHandler({
      type: 'export_note',
      handler: async (params) => {
        const { content, title, format = 'markdown', filename } = params;
        
        if (!content) {
          return { success: false, error: 'Note content is required' };
        }

        try {
          const noteTitle = title || 'Exported Note';
          const noteFilename = filename || `${noteTitle.replace(/[^a-zA-Z0-9]/g, '_')}.${format}`;
          
          // Create downloadable content
          let exportContent = content;
          if (format === 'markdown') {
            exportContent = `# ${noteTitle}\n\n${content}\n\n---\n*Exported from AI Assistant on ${new Date().toLocaleString()}*`;
          } else if (format === 'txt') {
            exportContent = `${noteTitle}\n${'='.repeat(noteTitle.length)}\n\n${content}\n\n---\nExported from AI Assistant on ${new Date().toLocaleString()}`;
          }

          // Create and trigger download
          const blob = new Blob([exportContent], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = noteFilename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);

          // Dispatch event
          this.dispatchEvent('kari:note_exported', {
            title: noteTitle,
            format,
            filename: noteFilename,
            exportedAt: new Date().toISOString()
          });

          // Store export reference in memory
          await this.memoryService.storeMemory(
            `Exported note: ${noteTitle}`,
            {
              tags: ['export', 'note', format],
              metadata: {
                type: 'export_reference',
                title: noteTitle,
                format,
                filename: noteFilename,
                exportedAt: new Date().toISOString()
              }
            }
          );

          return {
            success: true,
            message: `Note "${noteTitle}" exported as ${format.toUpperCase()}`,
            data: { title: noteTitle, format, filename: noteFilename }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to export note: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Export content as a downloadable note',
      requiredParams: ['content'],
      optionalParams: ['title', 'format', 'filename']
    });

    // Search Memory Action
    this.registerHandler({
      type: 'search_memory',
      handler: async (params) => {
        const { query, maxResults = 10, tags, timeRange } = params;
        
        if (!query) {
          return { success: false, error: 'Search query is required' };
        }

        try {
          const searchResults = await this.memoryService.searchMemories(query, {
            tags,
            dateRange: timeRange,
            maxResults
          });

          // Dispatch event with search results
          this.dispatchEvent('kari:memory_searched', {
            query,
            results: searchResults.memories.length,
            searchTime: searchResults.searchTime
          });

          return {
            success: true,
            message: `Found ${searchResults.memories.length} memories`,
            data: {
              memories: searchResults.memories,
              totalFound: searchResults.totalFound,
              searchTime: searchResults.searchTime
            }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to search memories: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Search through stored memories',
      requiredParams: ['query'],
      optionalParams: ['maxResults', 'tags', 'timeRange']
    });

    // Create Conversation Action
    this.registerHandler({
      type: 'create_conversation',
      handler: async (params) => {
        const { title, initialMessage, tags = [] } = params;
        
        try {
          // This would typically create a new conversation
          // For now, we'll dispatch an event for the UI to handle
          this.dispatchEvent('kari:conversation_create', {
            title: title || 'New Conversation',
            initialMessage,
            tags,
            createdAt: new Date().toISOString()
          });

          return {
            success: true,
            message: 'New conversation created',
            data: { title: title || 'New Conversation' }
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to create conversation: ${error instanceof Error ? error.message : 'Unknown error'}`
          };
        }
      },
      description: 'Create a new conversation',
      requiredParams: [],
      optionalParams: ['title', 'initialMessage', 'tags']
    });
  }

  /**
   * Setup event listeners for legacy event names
   */
  private setupEventListeners(): void {
    // Legacy event mappings for backward compatibility
    const legacyEventMap = {
      'kari:add_task': 'add_task',
      'kari:pin_memory': 'pin_memory',
      'kari:open_doc': 'open_doc',
      'kari:export_note': 'export_note'
    };

    Object.entries(legacyEventMap).forEach(([legacyEvent, actionType]) => {
      window.addEventListener(legacyEvent, (event: any) => {
        this.performAction(actionType, event.detail || {});
      });
    });
  }

  /**
   * Register a new action handler
   */
  registerHandler(handler: ActionHandler): void {
    this.handlers.set(handler.type, handler);
  }

  /**
   * Unregister an action handler
   */
  unregisterHandler(type: string): void {
    this.handlers.delete(type);
  }

  /**
   * Get all registered handlers
   */
  getHandlers(): ActionHandler[] {
    return Array.from(this.handlers.values());
  }

  /**
   * Get handler by type
   */
  getHandler(type: string): ActionHandler | undefined {
    return this.handlers.get(type);
  }

  /**
   * Perform a suggested action
   */
  async performAction(type: string, params: Record<string, any> = {}): Promise<ActionResult> {
    const handler = this.handlers.get(type);
    
    if (!handler) {
      return {
        success: false,
        error: `Unknown action type: ${type}`
      };
    }

    // Validate required parameters
    if (handler.requiredParams) {
      const missingParams = handler.requiredParams.filter(param => !(param in params));
      if (missingParams.length > 0) {
        return {
          success: false,
          error: `Missing required parameters: ${missingParams.join(', ')}`
        };
      }
    }

    try {
      const result = await handler.handler(params);
      
      // Log action performance
      console.log(`Action performed: ${type}`, {
        success: result.success,
        params: Object.keys(params),
        message: result.message
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Action failed: ${type}`, error);
      
      return {
        success: false,
        error: `Action execution failed: ${errorMessage}`
      };
    }
  }

  /**
   * Perform multiple suggested actions
   */
  async performActions(actions: SuggestedAction[]): Promise<ActionResult[]> {
    const results: ActionResult[] = [];
    
    // Sort actions by priority
    const sortedActions = actions.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return (priorityOrder[b.priority || 'medium'] || 2) - (priorityOrder[a.priority || 'medium'] || 2);
    });

    for (const action of sortedActions) {
      const result = await this.performAction(action.type, action.params || {});
      results.push(result);
      
      // Stop on first failure if it's a high priority action
      if (!result.success && action.priority === 'high') {
        break;
      }
    }

    return results;
  }

  /**
   * Dispatch custom event
   */
  private dispatchEvent(eventName: string, detail: any): void {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
    
    // Also trigger any registered listeners
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.forEach(listener => listener(event));
    }
  }

  /**
   * Add event listener for action events
   */
  addEventListener(eventName: string, listener: (event: CustomEvent) => void): void {
    if (!this.eventListeners.has(eventName)) {
      this.eventListeners.set(eventName, new Set());
    }
    this.eventListeners.get(eventName)!.add(listener);
  }

  /**
   * Remove event listener
   */
  removeEventListener(eventName: string, listener: (event: CustomEvent) => void): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * Get action suggestions based on context
   */
  getSuggestedActions(context: string, userIntent?: string): SuggestedAction[] {
    const suggestions: SuggestedAction[] = [];
    
    // Simple context-based suggestions
    const lowerContext = context.toLowerCase();
    
    if (lowerContext.includes('task') || lowerContext.includes('todo') || lowerContext.includes('remind')) {
      suggestions.push({
        type: 'add_task',
        params: { title: this.extractTaskTitle(context) },
        confidence: 0.8,
        description: 'Add this as a task',
        icon: 'CheckSquare',
        priority: 'medium'
      });
    }

    if (lowerContext.includes('remember') || lowerContext.includes('important') || lowerContext.includes('note')) {
      suggestions.push({
        type: 'pin_memory',
        params: { content: context },
        confidence: 0.7,
        description: 'Pin this to memory',
        icon: 'Pin',
        priority: 'medium'
      });
    }

    if (lowerContext.includes('export') || lowerContext.includes('save') || lowerContext.includes('download')) {
      suggestions.push({
        type: 'export_note',
        params: { content: context },
        confidence: 0.6,
        description: 'Export as note',
        icon: 'Download',
        priority: 'low'
      });
    }

    if (lowerContext.includes('search') || lowerContext.includes('find') || lowerContext.includes('look for')) {
      const query = this.extractSearchQuery(context);
      if (query) {
        suggestions.push({
          type: 'search_memory',
          params: { query },
          confidence: 0.7,
          description: `Search for "${query}"`,
          icon: 'Search',
          priority: 'medium'
        });
      }
    }

    return suggestions;
  }

  /**
   * Extract task title from context
   */
  private extractTaskTitle(context: string): string {
    // Simple extraction - in a real implementation, this would use NLP
    const taskPatterns = [
      /(?:task|todo|remind me to)\s+(.+)/i,
      /(?:i need to|should)\s+(.+)/i,
      /(.+)(?:\s+task|\s+todo)/i
    ];

    for (const pattern of taskPatterns) {
      const match = context.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    return context.substring(0, 50) + (context.length > 50 ? '...' : '');
  }

  /**
   * Extract search query from context
   */
  private extractSearchQuery(context: string): string | null {
    const searchPatterns = [
      /(?:search for|find|look for)\s+(.+)/i,
      /(.+)(?:\s+search|\s+find)/i
    ];

    for (const pattern of searchPatterns) {
      const match = context.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    return null;
  }
}

// Global instance
let actionRegistry: ActionRegistry | null = null;

/**
 * Get the global action registry instance
 */
export function getActionRegistry(): ActionRegistry {
  if (!actionRegistry) {
    actionRegistry = new ActionRegistry();
  }
  return actionRegistry;
}

/**
 * Initialize action registry with custom handlers
 */
export function initializeActionRegistry(customHandlers?: ActionHandler[]): ActionRegistry {
  actionRegistry = new ActionRegistry();
  
  if (customHandlers) {
    customHandlers.forEach(handler => {
      actionRegistry!.registerHandler(handler);
    });
  }
  
  return actionRegistry;
}

/**
 * Convenience function to perform a suggested action
 */
export async function performSuggestedAction(action: SuggestedAction): Promise<ActionResult> {
  const registry = getActionRegistry();
  return registry.performAction(action.type, action.params || {});
}

/**
 * Convenience function to get action suggestions
 */
export function getActionSuggestions(context: string, userIntent?: string): SuggestedAction[] {
  const registry = getActionRegistry();
  return registry.getSuggestedActions(context, userIntent);
}

// Export types
export type {
  SuggestedAction,
  ActionResult,
  ActionHandler
};