// Shared Chat Interface Component
// Framework-agnostic chat interface that can be adapted for React, Streamlit, and Tauri

import { 
  IChatComponent, 
  IChatService, 
  IThemeManager,
  ComponentConfig
} from '../../abstractions/interfaces';
import { 
  ChatMessage, 
  ChatState, 
  KarenSettings, 
  Theme,
  HandleUserMessageResult
} from '../../abstractions/types';
import { 
  validator, 
  errorHandler, 
  storageManager, 
  eventEmitter,
  generateId,
  debounce
} from '../../abstractions/utils';
import { DEFAULT_KAREN_SETTINGS, STORAGE_KEYS } from '../../abstractions/config';

export interface ChatInterfaceOptions {
  enableVoice?: boolean;
  enableExport?: boolean;
  enableSearch?: boolean;
  maxMessages?: number;
  autoSave?: boolean;
  placeholder?: string;
}

export class SharedChatInterface implements IChatComponent {
  public id: string;
  public isVisible: boolean = true;
  public isLoading: boolean = false;
  public theme: Theme;
  public state: ChatState;

  private chatService: IChatService;
  private themeManager: IThemeManager;
  private config: ComponentConfig;
  private options: ChatInterfaceOptions;
  private messageCallbacks: Array<(message: ChatMessage) => void> = [];
  private recordingCallbacks: Array<(isRecording: boolean) => void> = [];
  private debouncedSave: () => void;

  constructor(
    containerId: string,
    chatService: IChatService,
    themeManager: IThemeManager,
    config: ComponentConfig,
    options: ChatInterfaceOptions = {}
  ) {
    this.id = containerId;
    this.chatService = chatService;
    this.themeManager = themeManager;
    this.config = config;
    this.theme = themeManager.currentTheme;
    
    this.options = {
      enableVoice: config.enableVoice,
      enableExport: true,
      enableSearch: true,
      maxMessages: config.maxMessageHistory,
      autoSave: config.autoSaveSettings,
      placeholder: 'Ask Karen anything...',
      ...options
    };

    // Initialize state
    this.state = {
      messages: [],
      isLoading: false,
      isRecording: false,
      input: '',
      settings: DEFAULT_KAREN_SETTINGS
    };

    // Create debounced save function
    this.debouncedSave = debounce(() => this.saveState(), 1000);

    // Load initial state
    this.loadState();
    this.loadSettings();

    // Set up theme change listener
    this.themeManager.onThemeChanged((theme) => {
      this.updateTheme(theme);
    });

    // Add initial greeting message
    this.addInitialMessage();
  }

  async render(): Promise<void> {
    // This method would be implemented differently for each framework
    // React: JSX rendering
    // Streamlit: st.* calls
    // Tauri: DOM manipulation
    console.log('Rendering shared chat interface');
  }

  destroy(): void {
    // Clean up resources
    this.saveState();
    eventEmitter.removeAllListeners(`chat-${this.id}`);
    console.log('Destroying shared chat interface');
  }

  updateTheme(theme: Theme): void {
    this.theme = theme;
    // Trigger re-render in framework-specific implementation
    eventEmitter.emit(`chat-${this.id}-theme-changed`, theme);
  }

  async sendMessage(content: string, isVoice: boolean = false): Promise<void> {
    if (!content.trim() || this.state.isLoading) return;

    // Validate message
    const messageErrors = validator.validateChatMessage({
      content,
      role: 'user',
      timestamp: new Date()
    });

    if (messageErrors.length > 0) {
      errorHandler.showUserError(messageErrors.join(', '));
      return;
    }

    // Create user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    // Add user message to state
    this.addMessage(userMessage);
    this.updateState({ input: '', isLoading: true });

    // Notify listeners
    this.messageCallbacks.forEach(callback => {
      try {
        callback(userMessage);
      } catch (error) {
        errorHandler.logError(error as Error, 'message callback');
      }
    });

    try {
      // Prepare conversation history
      const conversationHistory = this.state.messages
        .filter(msg => msg.role !== 'system')
        .map(msg => `${msg.role === 'user' ? 'User' : 'Karen'}: ${msg.content}`)
        .join('\n');

      // Send to backend
      const result: HandleUserMessageResult = await this.chatService.sendMessage(
        content,
        conversationHistory,
        this.state.settings
      );

      // Process response
      await this.processResponse(result, isVoice);

    } catch (error) {
      errorHandler.handleError(error as Error, 'send message');
      
      // Remove user message on error
      this.updateState({
        messages: this.state.messages.filter(msg => msg.id !== userMessage.id)
      });

      // Add error message
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'system',
        content: 'Failed to get a response from Karen. Please try again.',
        timestamp: new Date()
      };
      this.addMessage(errorMessage);

    } finally {
      this.updateState({ isLoading: false });
    }
  }

  addMessage(message: ChatMessage): void {
    // Validate message
    const errors = validator.validateChatMessage(message);
    if (errors.length > 0) {
      errorHandler.logError(new Error(errors.join(', ')), 'add message');
      return;
    }

    const newMessages = [...this.state.messages, message];
    
    // Limit message history
    if (this.options.maxMessages && newMessages.length > this.options.maxMessages) {
      newMessages.splice(0, newMessages.length - this.options.maxMessages);
    }

    this.updateState({ messages: newMessages });

    // Auto-save if enabled
    if (this.options.autoSave) {
      this.debouncedSave();
    }

    // Emit event
    eventEmitter.emit(`chat-${this.id}-message-added`, message);
  }

  clearMessages(): void {
    this.updateState({ messages: [] });
    this.addInitialMessage();
    
    // Clear saved state
    storageManager.remove(`${STORAGE_KEYS.MESSAGES}-${this.id}`);
    
    eventEmitter.emit(`chat-${this.id}-messages-cleared`);
  }

  exportMessages(format: 'text' | 'json'): string {
    if (format === 'json') {
      return JSON.stringify({
        exportTimestamp: new Date().toISOString(),
        conversationLength: this.state.messages.length,
        messages: this.state.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp.toISOString(),
          aiData: msg.aiData
        }))
      }, null, 2);
    } else {
      let exportText = 'AI Karen Conversation Export\n';
      exportText += '='.repeat(40) + '\n\n';
      
      this.state.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'You' : 'AI Karen';
        const timestamp = msg.timestamp.toLocaleString();
        exportText += `[${timestamp}] ${role}: ${msg.content}\n\n`;
      });
      
      return exportText;
    }
  }

  async startRecording(): Promise<void> {
    if (!this.options.enableVoice) {
      errorHandler.showUserWarning('Voice input is not enabled');
      return;
    }

    this.updateState({ isRecording: true });
    this.notifyRecordingStateChanged(true);
    eventEmitter.emit(`chat-${this.id}-recording-started`);
  }

  stopRecording(): void {
    this.updateState({ isRecording: false });
    this.notifyRecordingStateChanged(false);
    eventEmitter.emit(`chat-${this.id}-recording-stopped`);
  }

  async toggleRecording(): Promise<void> {
    if (this.state.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  onMessageSent(callback: (message: ChatMessage) => void): void {
    this.messageCallbacks.push(callback);
  }

  onMessageReceived(callback: (message: ChatMessage) => void): void {
    this.messageCallbacks.push(callback);
  }

  onRecordingStateChanged(callback: (isRecording: boolean) => void): void {
    this.recordingCallbacks.push(callback);
  }

  updateState(newState: Partial<ChatState>): void {
    this.state = { ...this.state, ...newState };
    eventEmitter.emit(`chat-${this.id}-state-changed`, this.state);
  }

  getState(): ChatState {
    return { ...this.state };
  }

  // Search functionality
  searchMessages(query: string): ChatMessage[] {
    if (!query.trim()) return [];
    
    const searchTerm = query.toLowerCase();
    return this.state.messages.filter(message =>
      message.content.toLowerCase().includes(searchTerm) ||
      (message.aiData?.keywords && 
       message.aiData.keywords.some(keyword => 
         keyword.toLowerCase().includes(searchTerm)
       ))
    );
  }

  // Get conversation statistics
  getConversationStats(): {
    totalMessages: number;
    userMessages: number;
    assistantMessages: number;
    averageMessageLength: number;
    conversationDuration: number;
  } {
    const messages = this.state.messages.filter(msg => msg.role !== 'system');
    const userMessages = messages.filter(msg => msg.role === 'user');
    const assistantMessages = messages.filter(msg => msg.role === 'assistant');
    
    const totalLength = messages.reduce((sum, msg) => sum + msg.content.length, 0);
    const averageMessageLength = messages.length > 0 ? totalLength / messages.length : 0;
    
    const firstMessage = messages[0];
    const lastMessage = messages[messages.length - 1];
    const conversationDuration = firstMessage && lastMessage 
      ? lastMessage.timestamp.getTime() - firstMessage.timestamp.getTime()
      : 0;

    return {
      totalMessages: messages.length,
      userMessages: userMessages.length,
      assistantMessages: assistantMessages.length,
      averageMessageLength: Math.round(averageMessageLength),
      conversationDuration
    };
  }

  // Update settings
  updateSettings(newSettings: Partial<KarenSettings>): void {
    const errors = validator.validateSettings(newSettings);
    if (Object.keys(errors).length > 0) {
      errorHandler.showUserError('Invalid settings: ' + Object.values(errors).join(', '));
      return;
    }

    this.state.settings = { ...this.state.settings, ...newSettings };
    this.saveSettings();
    eventEmitter.emit(`chat-${this.id}-settings-changed`, this.state.settings);
  }

  // Private methods
  private async processResponse(result: HandleUserMessageResult, isVoice: boolean): Promise<void> {
    const newMessages: ChatMessage[] = [];

    // Add acknowledgement if present
    if (result.acknowledgement) {
      newMessages.push({
        id: generateId(),
        role: 'assistant',
        content: result.acknowledgement,
        timestamp: new Date(),
        shouldAutoPlay: isVoice
      });
    }

    // Add main response
    newMessages.push({
      id: generateId(),
      role: 'assistant',
      content: result.finalResponse,
      timestamp: new Date(),
      aiData: result.aiDataForFinalResponse,
      shouldAutoPlay: isVoice
    });

    // Add proactive suggestion if present
    if (result.proactiveSuggestion) {
      newMessages.push({
        id: generateId(),
        role: 'assistant',
        content: result.proactiveSuggestion,
        timestamp: new Date(),
        shouldAutoPlay: isVoice
      });
    }

    // Add all messages
    newMessages.forEach(message => this.addMessage(message));

    // Handle suggested facts
    if (result.suggestedNewFacts && result.suggestedNewFacts.length > 0) {
      eventEmitter.emit(`chat-${this.id}-facts-suggested`, result.suggestedNewFacts);
    }

    // Handle summary generation
    if (result.summaryWasGenerated) {
      eventEmitter.emit(`chat-${this.id}-summary-generated`);
    }

    // Notify message received
    newMessages.forEach(message => {
      this.messageCallbacks.forEach(callback => {
        try {
          callback(message);
        } catch (error) {
          errorHandler.logError(error as Error, 'message received callback');
        }
      });
    });
  }

  private addInitialMessage(): void {
    const initialMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: "Hello! I'm Karen, your intelligent assistant. How can I help you today?",
      timestamp: new Date(),
      aiData: {
        knowledgeGraphInsights: "Karen AI aims to be a human-like AI assistant with advanced memory and learning capabilities."
      }
    };

    this.state.messages = [initialMessage];
  }

  private notifyRecordingStateChanged(isRecording: boolean): void {
    this.recordingCallbacks.forEach(callback => {
      try {
        callback(isRecording);
      } catch (error) {
        errorHandler.logError(error as Error, 'recording state callback');
      }
    });
  }

  private saveState(): void {
    try {
      const stateToSave = {
        messages: this.state.messages.slice(-this.options.maxMessages!),
        timestamp: new Date().toISOString()
      };
      storageManager.set(`${STORAGE_KEYS.MESSAGES}-${this.id}`, stateToSave);
    } catch (error) {
      errorHandler.logError(error as Error, 'save chat state');
    }
  }

  private loadState(): void {
    try {
      const savedState = storageManager.get(`${STORAGE_KEYS.MESSAGES}-${this.id}`);
      if (savedState && savedState.messages) {
        // Convert timestamp strings back to Date objects
        const messages = savedState.messages.map((msg: unknown) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        this.state.messages = messages;
      }
    } catch (error) {
      errorHandler.logError(error as Error, 'load chat state');
    }
  }

  private saveSettings(): void {
    try {
      storageManager.set(STORAGE_KEYS.SETTINGS, this.state.settings);
    } catch (error) {
      errorHandler.logError(error as Error, 'save settings');
    }
  }

  private loadSettings(): void {
    try {
      const savedSettings = storageManager.get(STORAGE_KEYS.SETTINGS);
      if (savedSettings) {
        this.state.settings = { ...DEFAULT_KAREN_SETTINGS, ...savedSettings };
      }
    } catch (error) {
      errorHandler.logError(error as Error, 'load settings');
    }
  }
}