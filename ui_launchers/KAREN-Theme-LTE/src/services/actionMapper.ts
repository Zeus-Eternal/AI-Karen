/**
 * Action Mapper Service
 * 
 * Provides a registry system for mapping actions to handlers
 * and managing action execution with proper error handling
 */

export interface SuggestedAction {
  id: string;
  type: string;
  title: string;
  description?: string;
  params?: Record<string, unknown>;
  priority?: number;
  category?: string;
}

export interface ActionResult {
  success: boolean;
  message?: string;
  error?: string;
  data?: unknown;
  metadata?: Record<string, unknown>;
}

export interface ActionHandler {
  type: string;
  handler: (params?: Record<string, unknown>) => Promise<ActionResult>;
  description?: string;
  category?: string;
}

class ActionRegistry {
  private handlers: Map<string, ActionHandler> = new Map();
  private eventListeners: Map<string, Set<(event: Event) => void>> = new Map();

  /**
   * Register an action handler
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
   * Perform a single action
   */
  async performAction(type: string, params?: Record<string, unknown>): Promise<ActionResult> {
    const handler = this.handlers.get(type);
    if (!handler) {
      return {
        success: false,
        error: `No handler registered for action type: ${type}`
      };
    }

    try {
      return await handler.handler(params);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Perform multiple actions
   */
  async performActions(actions: SuggestedAction[]): Promise<ActionResult[]> {
    const results: ActionResult[] = [];
    
    for (const action of actions) {
      const result = await this.performAction(action.type, action.params);
      results.push(result);
    }

    return results;
  }

  /**
   * Get suggested actions based on context
   */
  getSuggestedActions(context: string, userIntent?: string): SuggestedAction[] {
    // This is a simplified implementation
    // In a real implementation, you would use AI/ML to suggest actions
    const suggestions: SuggestedAction[] = [];

    // Basic context-based suggestions
    if (context.includes('error') || context.includes('problem')) {
      suggestions.push({
        id: 'refresh',
        type: 'refresh',
        title: 'Refresh Page',
        description: 'Reload the current page to resolve temporary issues',
        priority: 1
      });
    }

    if (context.includes('form') || context.includes('input')) {
      suggestions.push({
        id: 'validate-form',
        type: 'validate-form',
        title: 'Validate Form',
        description: 'Check form for validation errors',
        priority: 2
      });
    }

    if (context.includes('navigation') || context.includes('menu')) {
      suggestions.push({
        id: 'navigate-home',
        type: 'navigate',
        title: 'Go to Home',
        description: 'Navigate to the home page',
        params: { destination: 'home' },
        priority: 3
      });
    }

    // User intent-based suggestions
    if (userIntent) {
      if (userIntent.includes('help') || userIntent.includes('support')) {
        suggestions.push({
          id: 'open-help',
          type: 'open-help',
          title: 'Open Help',
          description: 'Open the help documentation',
          priority: 1
        });
      }

      if (userIntent.includes('settings') || userIntent.includes('preferences')) {
        suggestions.push({
          id: 'open-settings',
          type: 'open-settings',
          title: 'Open Settings',
          description: 'Open the settings page',
          priority: 1
        });
      }
    }

    return suggestions.sort((a, b) => (a.priority || 999) - (b.priority || 999));
  }

  /**
   * Add event listener
   */
  addEventListener(eventName: string, listener: (event: Event) => void): void {
    if (!this.eventListeners.has(eventName)) {
      this.eventListeners.set(eventName, new Set());
    }
    this.eventListeners.get(eventName)!.add(listener);
  }

  /**
   * Remove event listener
   */
  removeEventListener(eventName: string, listener: (event: Event) => void): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.delete(listener);
      if (listeners.size === 0) {
        this.eventListeners.delete(eventName);
      }
    }
  }

  /**
   * Emit event to listeners
   */
  private emit(eventName: string, event: Event): void {
    const listeners = this.eventListeners.get(eventName);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event);
        } catch (error) {
          console.error(`Error in event listener for ${eventName}:`, error);
        }
      });
    }
  }
}

// Singleton instance
const actionRegistry = new ActionRegistry();

// Register some default handlers
actionRegistry.registerHandler({
  type: 'refresh',
  description: 'Refresh the current page',
  handler: async () => {
    window.location.reload();
    return {
      success: true,
      message: 'Page refreshed'
    };
  }
});

actionRegistry.registerHandler({
  type: 'validate-form',
  description: 'Validate form inputs',
  handler: async () => {
    const forms = document.querySelectorAll('form');
    let valid = true;
    let message = 'Form validation completed';

    forms.forEach(form => {
      if (!(form as HTMLFormElement).checkValidity()) {
        valid = false;
        message = 'Form has validation errors';
      }
    });

    return {
      success: valid,
      message
    };
  }
});

actionRegistry.registerHandler({
  type: 'navigate',
  description: 'Navigate to a destination',
  handler: async (params) => {
    const destination = params?.destination as string;
    if (destination) {
      window.location.href = `/${destination}`;
      return {
        success: true,
        message: `Navigating to ${destination}`
      };
    }
    return {
      success: false,
      error: 'No destination specified'
    };
  }
});

actionRegistry.registerHandler({
  type: 'open-help',
  description: 'Open help documentation',
  handler: async () => {
    window.open('/help', '_blank');
    return {
      success: true,
      message: 'Help documentation opened'
    };
  }
});

actionRegistry.registerHandler({
  type: 'open-settings',
  description: 'Open settings page',
  handler: async () => {
    window.location.href = '/settings';
    return {
      success: true,
      message: 'Settings page opened'
    };
  }
});

/**
 * Get the action registry instance
 */
export function getActionRegistry(): ActionRegistry {
  return actionRegistry;
}

/**
 * Export types for external use
 */
export type { ActionRegistry };

export default actionRegistry;