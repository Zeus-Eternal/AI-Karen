/**
 * Action Registry System for Suggested Actions
 *
 * Features:
 * - Event-driven action system
 * - Support for add_task, pin_memory, open_doc, export_note, search_memory, create_conversation
 * - Wires action suggestions to existing services (memory/chat)
 * - Extensible action registration system
 * - Type-safe action handling
 */

import { getMemoryService } from '@/services/memoryService';
import { getChatService } from '@/services/chatService';

export interface SuggestedAction {
  type:
    | 'add_task'
    | 'pin_memory'
    | 'open_doc'
    | 'export_note'
    | 'search_memory'
    | 'create_conversation';
  params?: Record<string, unknown>;
  confidence?: number;
  description?: string;
  icon?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface ActionResult {
  success: boolean;
  message?: string;
  data?: unknown;
  error?: string;
}

export interface ActionHandler {
  type: string;
  handler: (params: Record<string, unknown>) => Promise<ActionResult>;
  description: string;
  requiredParams?: string[];
  optionalParams?: string[];
}

export type EventListenerFn = (event: CustomEvent) => void;

const isBrowser = typeof window !== 'undefined';

const asString = (value: unknown): string | undefined =>
  typeof value === 'string' ? value : undefined;

const asStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === 'string') : [];

const parseDateLike = (value: unknown): Date | undefined => {
  if (value instanceof Date) return value;
  if (typeof value === 'string' || typeof value === 'number') {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? undefined : parsed;
  }
  return undefined;
};

const toIsoDateString = (value: unknown): string | undefined =>
  parseDateLike(value)?.toISOString();

const asDateRange = (value: unknown): [Date, Date] | undefined => {
  if (!Array.isArray(value) || value.length !== 2) return undefined;
  const start = parseDateLike(value[0]);
  const end = parseDateLike(value[1]);
  return start && end ? [start, end] : undefined;
};

type ExportFormat = 'markdown' | 'txt';

/**
 * Action Registry for managing suggested actions
 */
export class ActionRegistry {
  private handlers = new Map<string, ActionHandler>();
  private eventListeners = new Map<string, Set<EventListenerFn>>();
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
    // Add Task
    this.registerHandler({
      type: 'add_task',
      description: 'Add a new task to the task list',
      requiredParams: ['title'],
      optionalParams: ['description', 'priority', 'dueDate', 'tags'],
      handler: async (params) => {
        const title = asString(params.title)?.trim();
        const description = asString(params.description);
        const priority = asString(params.priority) ?? 'medium';
        const dueDate = toIsoDateString(params.dueDate);
        const tags = asStringArray(params.tags);
        if (!title) return { success: false, error: 'Task title is required' };

        try {
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
                createdAt: new Date().toISOString(),
              },
            },
          );

          this.dispatchEvent('kari:task_added', {
            taskId: taskMemoryId,
            title,
            description,
            priority,
            dueDate,
            tags,
          });

          return {
            success: true,
            message: `Task "${title}" added successfully`,
            data: { taskId: taskMemoryId, title },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to add task: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });

    // Pin Memory
    this.registerHandler({
      type: 'pin_memory',
      description: 'Pin important information to memory',
      requiredParams: ['content'],
      optionalParams: ['title', 'tags', 'importance'],
      handler: async (params) => {
        const content = asString(params.content);
        const title = asString(params.title);
        const tags = asStringArray(params.tags);
        const importance =
          typeof params.importance === 'number' ? params.importance : 8;
        if (!content) return { success: false, error: 'Memory content is required' };

        try {
          const memoryId = await this.memoryService.storeMemory(content, {
            tags: ['pinned', 'important', ...tags],
            metadata: {
              type: 'pinned_memory',
              title: title || `${content.substring(0, 50)}...`,
              importance,
              pinnedAt: new Date().toISOString(),
            },
          });

          this.dispatchEvent('kari:memory_pinned', {
            memoryId,
            content: `${content.substring(0, 100)}...`,
            title: title || undefined,
            importance,
          });

          return {
            success: true,
            message: 'Memory pinned successfully',
            data: { memoryId, title: title || 'Pinned Memory' },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to pin memory: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });

    // Open Document
    this.registerHandler({
      type: 'open_doc',
      description: 'Open a document or URL',
      requiredParams: ['url'],
      optionalParams: ['title', 'type'],
      handler: async (params) => {
        const url = asString(params.url);
        const title = asString(params.title);
        const docType = asString(params.type) ?? 'external';
        if (!url) return { success: false, error: 'Document URL is required' };

        const displayTitle = title || 'Document';

        try {
          this.dispatchEvent('kari:document_open', {
            url,
            title: displayTitle,
            type: docType,
            openedAt: new Date().toISOString(),
          });

          await this.memoryService.storeMemory(`Opened document: ${displayTitle || url}`, {
            tags: ['document', 'reference', docType],
            metadata: {
              type: 'document_reference',
              url,
              title: displayTitle,
              documentType: docType,
              accessedAt: new Date().toISOString(),
            },
          });

          return {
            success: true,
            message: `Document "${title || 'Document'}" opened`,
            data: { url, title: displayTitle, type: docType },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to open document: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });

    // Export Note
    this.registerHandler({
      type: 'export_note',
      description: 'Export content as a downloadable note',
      requiredParams: ['content'],
      optionalParams: ['title', 'format', 'filename'],
      handler: async (params) => {
        const content = asString(params.content);
        if (!content) return { success: false, error: 'Note content is required' };
        const title = asString(params.title);
        const rawFormat = asString(params.format);
        const format: ExportFormat = rawFormat === 'txt' ? 'txt' : 'markdown';
        const filename = asString(params.filename);

        try {
          const noteTitle = (title && title.trim()) || 'Exported Note';
          const sanitizedTitle = noteTitle
            .replace(/[^a-zA-Z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '');
          const safeName = sanitizedTitle || 'note';
          const noteFilename = filename || `${safeName}.${format}`;

          // Create file body
          let exportContent = content;
          if (format === 'markdown') {
            exportContent = `# ${noteTitle}\n\n${content}\n\n---\n*Exported on ${new Date().toLocaleString()}*`;
          } else if (format === 'txt') {
            exportContent = `${noteTitle}\n${'='.repeat(noteTitle.length)}\n\n${content}\n\n---\nExported on ${new Date().toLocaleString()}`;
          }

          // Download
          if (isBrowser) {
            const blob = new Blob([exportContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = noteFilename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
          }

          this.dispatchEvent('kari:note_exported', {
            title: noteTitle,
            format,
            filename: noteFilename,
            exportedAt: new Date().toISOString(),
          });

          await this.memoryService.storeMemory(`Exported note: ${noteTitle}`, {
            tags: ['export', 'note', format],
            metadata: {
              type: 'export_reference',
              title: noteTitle,
              format,
              filename: noteFilename,
              exportedAt: new Date().toISOString(),
            },
          });

          return {
            success: true,
            message: `Note "${noteTitle}" exported as ${format.toUpperCase()}`,
            data: { title: noteTitle, format, filename: noteFilename },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to export note: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });

    // Search Memory
    this.registerHandler({
      type: 'search_memory',
      description: 'Search through stored memories',
      requiredParams: ['query'],
      optionalParams: ['maxResults', 'tags', 'timeRange'],
      handler: async (params) => {
        const query = asString(params.query);
        const maxResults =
          typeof params.maxResults === 'number' ? params.maxResults : 10;
        const tags = asStringArray(params.tags);
        const dateRange = asDateRange(params.timeRange);
        if (!query) return { success: false, error: 'Search query is required' };

        try {
          const searchResults = await this.memoryService.searchMemories(query, {
            tags,
            dateRange,
            maxResults,
          });

          this.dispatchEvent('kari:memory_searched', {
            query,
            results: searchResults.memories.length,
            searchTime: searchResults.searchTime,
          });

          return {
            success: true,
            message: `Found ${searchResults.memories.length} memories`,
            data: {
              memories: searchResults.memories,
              totalFound: searchResults.totalFound,
              searchTime: searchResults.searchTime,
            },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to search memories: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });

    // Create Conversation
    this.registerHandler({
      type: 'create_conversation',
      description: 'Create a new conversation',
      requiredParams: [],
      optionalParams: ['title', 'initialMessage', 'tags'],
      handler: async (params) => {
        const title = asString(params.title);
        const initialMessage = asString(params.initialMessage);
        const tags = asStringArray(params.tags);
        try {
          // If your chat service supports creation, prefer doing it here
          // const conv = await this.chatService.createConversation(...)

          this.dispatchEvent('kari:conversation_create', {
            title: title || 'New Conversation',
            initialMessage,
            tags,
            createdAt: new Date().toISOString(),
          });

          return {
            success: true,
            message: 'New conversation created',
            data: { title: title || 'New Conversation' },
          };
        } catch (error) {
          return {
            success: false,
            error: `Failed to create conversation: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        }
      },
    });
  }

  /**
   * Setup event listeners for legacy event names
   */
  private setupEventListeners(): void {
    if (!isBrowser) return;

    // Legacy event mappings for backward compatibility
    const legacyEventMap: Record<string, SuggestedAction['type']> = {
      'kari:add_task': 'add_task',
      'kari:pin_memory': 'pin_memory',
      'kari:open_doc': 'open_doc',
      'kari:export_note': 'export_note',
    };

    Object.entries(legacyEventMap).forEach(([legacyEvent, actionType]) => {
      const listener = (event: Event) => {
        const ce = event as CustomEvent;
        this.performAction(actionType, (ce.detail as Record<string, unknown>) || {});
      };
      window.addEventListener(legacyEvent, listener as EventListener);
      // Track listener so we can re-emit through local listeners too
      this.addEventListener(legacyEvent, listener as unknown as EventListenerFn);
    });
  }

  // Registration APIs
  registerHandler(handler: ActionHandler): void {
    this.handlers.set(handler.type, handler);
  }

  unregisterHandler(type: string): void {
    this.handlers.delete(type);
  }

  getHandlers(): ActionHandler[] {
    return Array.from(this.handlers.values());
  }

  getHandler(type: string): ActionHandler | undefined {
    return this.handlers.get(type);
  }

  /**
   * Perform a suggested action
   */
  async performAction(type: string, params: Record<string, unknown> = {}): Promise<ActionResult> {
    const handler = this.handlers.get(type);
    if (!handler) {
      return { success: false, error: `Unknown action type: ${type}` };
    }

    // Validate required parameters
    if (handler.requiredParams?.length) {
      const missing = handler.requiredParams.filter((p) => !(p in params));
      if (missing.length) {
        return { success: false, error: `Missing required parameters: ${missing.join(', ')}` };
      }
    }

    try {
      const result = await handler.handler(params);
      // Structured log for observability
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.log(`Action performed: ${type}`, {
          success: result.success,
          params: Object.keys(params),
          message: result.message,
        });
      }
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return { success: false, error: `Action execution failed: ${errorMessage}` };
    }
  }

  /**
   * Perform multiple suggested actions
   */
  async performActions(actions: SuggestedAction[]): Promise<ActionResult[]> {
    const results: ActionResult[] = [];

    // Sort by priority (high → low); default = medium
    const rank = { high: 3, medium: 2, low: 1 } as const;
    const sorted = [...actions].sort(
      (a, b) => (rank[b.priority ?? 'medium'] ?? 2) - (rank[a.priority ?? 'medium'] ?? 2),
    );

    for (const action of sorted) {
      const result = await this.performAction(action.type, action.params || {});
      results.push(result);
      if (!result.success && action.priority === 'high') break; // fail-fast on high priority
    }
    return results;
  }

  /**
   * Dispatch custom event and notify local listeners
   */
  private dispatchEvent(eventName: string, detail: unknown): void {
    if (isBrowser) {
      const event = new CustomEvent(eventName, { detail });
      window.dispatchEvent(event);
    }
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(new CustomEvent(eventName, { detail }) as CustomEvent);
        } catch {
          /* no-op */
        }
      });
    }
  }

  /**
   * Add event listener for action events
   */
  addEventListener(eventName: string, listener: EventListenerFn): void {
    if (!this.eventListeners.has(eventName)) {
      this.eventListeners.set(eventName, new Set());
    }
    this.eventListeners.get(eventName)!.add(listener);
  }

  /**
   * Remove event listener
   */
  removeEventListener(eventName: string, listener: EventListenerFn): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * Get action suggestions based on context
   */
  getSuggestedActions(context: string, _userIntent?: string): SuggestedAction[] {
    const suggestions: SuggestedAction[] = [];
    const lower = context.toLowerCase();

    if (/(?:^|\b)(task|todo|remind)(?:\b|:)/i.test(lower) || /remind me to/i.test(lower)) {
      suggestions.push({
        type: 'add_task',
        params: { title: this.extractTaskTitle(context) },
        confidence: 0.8,
        description: 'Add this as a task',
        icon: 'CheckSquare',
        priority: 'medium',
      });
    }

    if (/(remember|important|note)/i.test(lower)) {
      suggestions.push({
        type: 'pin_memory',
        params: { content: context },
        confidence: 0.7,
        description: 'Pin this to memory',
        icon: 'Pin',
        priority: 'medium',
      });
    }

    if (/(export|save|download)/i.test(lower)) {
      suggestions.push({
        type: 'export_note',
        params: { content: context },
        confidence: 0.6,
        description: 'Export as note',
        icon: 'Download',
        priority: 'low',
      });
    }

    if (/(search|find|look for)/i.test(lower)) {
      const query = this.extractSearchQuery(context);
      if (query) {
        suggestions.push({
          type: 'search_memory',
          params: { query },
          confidence: 0.7,
          description: `Search for "${query}"`,
          icon: 'Search',
          priority: 'medium',
        });
      }
    }

    return suggestions;
  }

  // --- Helpers ---------------------------------------------------------------

  private extractTaskTitle(context: string): string {
    const patterns = [
      /(?:task|todo|remind me to)\s+(.+)/i,
      /(?:i need to|should)\s+(.+)/i,
      /(.+)(?:\s+task|\s+todo)$/i,
    ];
    for (const p of patterns) {
      const m = context.match(p);
      if (m?.[1]) return m[1].trim();
    }
    const trimmed = context.trim();
    return trimmed.length > 50 ? `${trimmed.slice(0, 50)}...` : trimmed;
  }

  private extractSearchQuery(context: string): string | null {
    const patterns = [
      /(?:search for|find|look for)\s+(.+)/i,
      /(.+)(?:\s+search|\s+find)$/i,
    ];
    for (const p of patterns) {
      const m = context.match(p);
      if (m?.[1]) return m[1].trim();
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
  customHandlers?.forEach((h) => actionRegistry!.registerHandler(h));
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
