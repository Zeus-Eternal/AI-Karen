// Framework-agnostic component interfaces
// These interfaces define the contract that each framework adapter must implement

import { 
  ChatMessage, 
  ChatState, 
  ChatEvent,
  KarenSettings, 
  SettingsState, 
  SettingsEvent,
  Theme,
  PluginInfo,
  PluginExecutionRequest,
  PluginExecutionResult,
  MemoryEntry,
  MemoryQuery,
  AnalyticsEvent,
  AnalyticsMetrics
} from './types';

// Base component interface that all components must implement
export interface BaseComponent {
  id: string;
  isVisible: boolean;
  isLoading: boolean;
  theme: Theme;
  
  render(): void | Promise<void>;
  destroy(): void;
  updateTheme(theme: Theme): void;
}

// Chat component interface
export interface IChatComponent extends BaseComponent {
  state: ChatState;
  
  // Message handling
  sendMessage(content: string, isVoice?: boolean): Promise<void>;
  addMessage(message: ChatMessage): void;
  clearMessages(): void;
  exportMessages(format: 'text' | 'json'): string;
  
  // Voice functionality
  startRecording(): Promise<void>;
  stopRecording(): void;
  toggleRecording(): Promise<void>;
  
  // Event handling
  onMessageSent(callback: (message: ChatMessage) => void): void;
  onMessageReceived(callback: (message: ChatMessage) => void): void;
  onRecordingStateChanged(callback: (isRecording: boolean) => void): void;
  
  // State management
  updateState(newState: Partial<ChatState>): void;
  getState(): ChatState;
}

// Settings component interface
export interface ISettingsComponent extends BaseComponent {
  state: SettingsState;
  
  // Settings management
  loadSettings(): Promise<KarenSettings>;
  saveSettings(settings: KarenSettings): Promise<void>;
  resetSettings(): Promise<void>;
  validateSettings(settings: Partial<KarenSettings>): Record<string, string>;
  
  // Individual setting updates
  updateSetting<K extends keyof KarenSettings>(key: K, value: KarenSettings[K]): void;
  getSetting<K extends keyof KarenSettings>(key: K): KarenSettings[K];
  
  // Event handling
  onSettingChanged(callback: (key: string, value: unknown) => void): void;
  onSettingsSaved(callback: (settings: KarenSettings) => void): void;
  
  // State management
  updateState(newState: Partial<SettingsState>): void;
  getState(): SettingsState;
}

// Plugin management interface
export interface IPluginComponent extends BaseComponent {
  // Plugin discovery and management
  listPlugins(): Promise<PluginInfo[]>;
  getPluginInfo(pluginName: string): Promise<PluginInfo | null>;
  enablePlugin(pluginName: string): Promise<void>;
  disablePlugin(pluginName: string): Promise<void>;
  
  // Plugin execution
  executePlugin(request: PluginExecutionRequest): Promise<PluginExecutionResult>;
  validatePluginParameters(pluginName: string, parameters: Record<string, unknown>): boolean;
  
  // Event handling
  onPluginExecuted(callback: (result: PluginExecutionResult) => void): void;
  onPluginStateChanged(callback: (pluginName: string, enabled: boolean) => void): void;
}

// Memory management interface
export interface IMemoryComponent extends BaseComponent {
  // Memory operations
  storeMemory(content: string, metadata: Record<string, unknown>, tags: string[]): Promise<string>;
  queryMemories(query: MemoryQuery): Promise<MemoryEntry[]>;
  getMemoryStats(userId: string): Promise<Record<string, unknown>>;
  deleteMemory(memoryId: string): Promise<void>;
  
  // Memory visualization
  renderMemoryGraph(): void;
  renderMemoryTimeline(): void;
  
  // Event handling
  onMemoryStored(callback: (memory: MemoryEntry) => void): void;
  onMemoryQueried(callback: (results: MemoryEntry[]) => void): void;
}

// Analytics interface
export interface IAnalyticsComponent extends BaseComponent {
  // Analytics data
  getMetrics(timeRange?: [Date, Date]): Promise<AnalyticsMetrics>;
  trackEvent(event: AnalyticsEvent): Promise<void>;
  
  // Visualization
  renderUsageChart(): void;
  renderEngagementMetrics(): void;
  renderPluginUsage(): void;
  
  // Export
  exportAnalytics(format: 'csv' | 'json'): Promise<string>;
}

// Theme management interface
export interface IThemeManager {
  currentTheme: Theme;
  availableThemes: Theme[];
  
  // Theme operations
  setTheme(themeName: string): void;
  getTheme(themeName: string): Theme | null;
  registerTheme(theme: Theme): void;
  
  // CSS generation
  generateCSS(theme: Theme): string;
  generateTailwindConfig(theme: Theme): Record<string, unknown>;
  generateStreamlitCSS(theme: Theme): string;
  
  // Event handling
  onThemeChanged(callback: (theme: Theme) => void): void;
}

// Service interfaces for backend communication
export interface IChatService {
  sendMessage(content: string, conversationHistory: string, settings: KarenSettings): Promise<unknown>;
  getSuggestedStarter(context: string): Promise<string>;
}

export interface IMemoryService {
  storeMemory(content: string, metadata: Record<string, unknown>, tags: string[], userId: string, sessionId: string): Promise<string>;
  queryMemories(query: MemoryQuery): Promise<MemoryEntry[]>;
  buildContext(query: string, userId: string, sessionId: string): Promise<Record<string, unknown>>;
  getMemoryStats(userId: string): Promise<Record<string, unknown>>;
}

export interface IPluginService {
  listPlugins(): Promise<PluginInfo[]>;
  executePlugin(request: PluginExecutionRequest): Promise<PluginExecutionResult>;
  getPluginInfo(pluginName: string): Promise<PluginInfo | null>;
  validatePlugin(pluginName: string, parameters: Record<string, unknown>): Promise<boolean>;
}

export interface IAnalyticsService {
  trackEvent(event: AnalyticsEvent): Promise<void>;
  getMetrics(timeRange?: [Date, Date]): Promise<AnalyticsMetrics>;
  exportData(format: 'csv' | 'json', timeRange?: [Date, Date]): Promise<string>;
}

// Framework adapter interface
export interface IFrameworkAdapter {
  framework: 'react' | 'streamlit' | 'tauri';
  
  // Component creation
  createChatComponent(containerId: string, options?: unknown): IChatComponent;
  createSettingsComponent(containerId: string, options?: unknown): ISettingsComponent;
  createPluginComponent(containerId: string, options?: unknown): IPluginComponent;
  createMemoryComponent(containerId: string, options?: unknown): IMemoryComponent;
  createAnalyticsComponent(containerId: string, options?: unknown): IAnalyticsComponent;
  
  // Theme management
  getThemeManager(): IThemeManager;
  
  // Service creation
  createChatService(): IChatService;
  createMemoryService(): IMemoryService;
  createPluginService(): IPluginService;
  createAnalyticsService(): IAnalyticsService;
  
  // Framework-specific utilities
  createElement(type: string, props: Record<string, unknown>, children?: unknown[]): unknown;
  renderComponent(component: unknown, container: string | Element): void;
  destroyComponent(component: unknown): void;
}

// Configuration interface
export interface ComponentConfig {
  apiBaseUrl: string;
  enableVoice: boolean;
  enableAnalytics: boolean;
  defaultTheme: string;
  maxMessageHistory: number;
  autoSaveSettings: boolean;
  debugMode: boolean;
}

// Error handling interface
export interface IErrorHandler {
  handleError(error: Error, context: string): void;
  logError(error: Error, context: string): void;
  showUserError(message: string, title?: string): void;
  showUserWarning(message: string, title?: string): void;
  showUserSuccess(message: string, title?: string): void;
}

// Validation interface
export interface IValidator {
  validateChatMessage(message: Partial<ChatMessage>): string[];
  validateSettings(settings: Partial<KarenSettings>): Record<string, string>;
  validatePluginRequest(request: Partial<PluginExecutionRequest>): string[];
  validateMemoryQuery(query: Partial<MemoryQuery>): string[];
}