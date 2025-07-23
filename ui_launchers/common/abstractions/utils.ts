// Utility functions for shared UI components
// These utilities provide common functionality across all frameworks

import { 
  ChatMessage, 
  KarenSettings, 
  PluginExecutionRequest, 
  MemoryQuery,
  Theme,
  ComponentConfig
} from './types';
import { IValidator, IErrorHandler } from './interfaces';

// Validation utilities
export class Validator implements IValidator {
  validateChatMessage(message: Partial<ChatMessage>): string[] {
    const errors: string[] = [];
    
    if (!message.content || typeof message.content !== 'string' || message.content.trim() === '') {
      errors.push('Message content is required and must be a non-empty string');
    }
    
    if (!message.role || !['user', 'assistant', 'system'].includes(message.role)) {
      errors.push('Message role must be one of: user, assistant, system');
    }
    
    if (message.timestamp && !(message.timestamp instanceof Date)) {
      errors.push('Message timestamp must be a Date object');
    }
    
    if (message.aiData) {
      if (message.aiData.keywords && !Array.isArray(message.aiData.keywords)) {
        errors.push('AI data keywords must be an array');
      }
      
      if (message.aiData.confidence && (typeof message.aiData.confidence !== 'number' || message.aiData.confidence < 0 || message.aiData.confidence > 1)) {
        errors.push('AI data confidence must be a number between 0 and 1');
      }
    }
    
    return errors;
  }

  validateSettings(settings: Partial<KarenSettings>): Record<string, string> {
    const errors: Record<string, string> = {};
    
    if (settings.memoryDepth && !['short', 'medium', 'long'].includes(settings.memoryDepth)) {
      errors.memoryDepth = 'Memory depth must be one of: short, medium, long';
    }
    
    if (settings.personalityTone && !['neutral', 'friendly', 'formal', 'humorous'].includes(settings.personalityTone)) {
      errors.personalityTone = 'Personality tone must be one of: neutral, friendly, formal, humorous';
    }
    
    if (settings.personalityVerbosity && !['concise', 'balanced', 'detailed'].includes(settings.personalityVerbosity)) {
      errors.personalityVerbosity = 'Personality verbosity must be one of: concise, balanced, detailed';
    }
    
    if (settings.personalFacts && !Array.isArray(settings.personalFacts)) {
      errors.personalFacts = 'Personal facts must be an array';
    }
    
    if (settings.temperatureUnit && !['C', 'F'].includes(settings.temperatureUnit)) {
      errors.temperatureUnit = 'Temperature unit must be C or F';
    }
    
    if (settings.weatherService && !['wttr_in', 'custom_api'].includes(settings.weatherService)) {
      errors.weatherService = 'Weather service must be wttr_in or custom_api';
    }
    
    if (settings.customPersonaInstructions && typeof settings.customPersonaInstructions !== 'string') {
      errors.customPersonaInstructions = 'Custom persona instructions must be a string';
    }
    
    return errors;
  }

  validatePluginRequest(request: Partial<PluginExecutionRequest>): string[] {
    const errors: string[] = [];
    
    if (!request.pluginName || typeof request.pluginName !== 'string' || request.pluginName.trim() === '') {
      errors.push('Plugin name is required and must be a non-empty string');
    }
    
    if (!request.parameters || typeof request.parameters !== 'object') {
      errors.push('Plugin parameters must be an object');
    }
    
    if (request.timeout && (typeof request.timeout !== 'number' || request.timeout <= 0)) {
      errors.push('Plugin timeout must be a positive number');
    }
    
    return errors;
  }

  validateMemoryQuery(query: Partial<MemoryQuery>): string[] {
    const errors: string[] = [];
    
    if (!query.text || typeof query.text !== 'string' || query.text.trim() === '') {
      errors.push('Query text is required and must be a non-empty string');
    }
    
    if (query.topK && (typeof query.topK !== 'number' || query.topK <= 0)) {
      errors.push('Top K must be a positive number');
    }
    
    if (query.similarityThreshold && (typeof query.similarityThreshold !== 'number' || query.similarityThreshold < 0 || query.similarityThreshold > 1)) {
      errors.push('Similarity threshold must be a number between 0 and 1');
    }
    
    if (query.tags && !Array.isArray(query.tags)) {
      errors.push('Tags must be an array');
    }
    
    if (query.timeRange && (!Array.isArray(query.timeRange) || query.timeRange.length !== 2 || !(query.timeRange[0] instanceof Date) || !(query.timeRange[1] instanceof Date))) {
      errors.push('Time range must be an array of two Date objects');
    }
    
    return errors;
  }
}

// Error handling utilities
export class ErrorHandler implements IErrorHandler {
  private debugMode: boolean;

  constructor(debugMode: boolean = false) {
    this.debugMode = debugMode;
  }

  handleError(error: Error, context: string): void {
    this.logError(error, context);
    
    // In production, show user-friendly error
    if (!this.debugMode) {
      this.showUserError('An unexpected error occurred. Please try again.');
    } else {
      this.showUserError(`Error in ${context}: ${error.message}`);
    }
  }

  logError(error: Error, context: string): void {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown'
    };
    
    console.error('Karen UI Error:', errorInfo);
    
    // In a real implementation, you might send this to an error tracking service
    if (typeof window !== 'undefined' && (window as any).karenErrorTracker) {
      (window as any).karenErrorTracker.track(errorInfo);
    }
  }

  showUserError(message: string, title: string = 'Error'): void {
    this.showNotification('error', title, message);
  }

  showUserWarning(message: string, title: string = 'Warning'): void {
    this.showNotification('warning', title, message);
  }

  showUserSuccess(message: string, title: string = 'Success'): void {
    this.showNotification('success', title, message);
  }

  private showNotification(type: 'error' | 'warning' | 'success', title: string, message: string): void {
    // This would integrate with the framework's notification system
    if (typeof window !== 'undefined') {
      // Try to use existing toast/notification system
      if ((window as any).karenToast) {
        (window as any).karenToast({ type, title, message });
      } else {
        // Fallback to alert for now
        alert(`${title}: ${message}`);
      }
    } else {
      // Server-side or non-browser environment
      console.log(`${type.toUpperCase()}: ${title} - ${message}`);
    }
  }
}

// Utility functions for common operations
export function generateId(): string {
  return `karen-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function formatTimestamp(date: Date): string {
  return date.toLocaleString();
}

export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

export function sanitizeHtml(html: string): string {
  // Basic HTML sanitization - in production, use a proper library like DOMPurify
  return html
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
}

export function parseMarkdown(markdown: string): string {
  // Basic markdown parsing - in production, use a proper markdown library
  return markdown
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
}

export function mergeDeep<T extends Record<string, any>>(target: T, source: Partial<T>): T {
  const result = { ...target };
  
  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      const sourceValue = source[key];
      const targetValue = result[key];
      
      if (
        sourceValue &&
        typeof sourceValue === 'object' &&
        !Array.isArray(sourceValue) &&
        targetValue &&
        typeof targetValue === 'object' &&
        !Array.isArray(targetValue)
      ) {
        result[key] = mergeDeep(targetValue, sourceValue);
      } else {
        result[key] = sourceValue as T[Extract<keyof T, string>];
      }
    }
  }
  
  return result;
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function getFileExtension(filename: string): string {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

export function getMimeType(filename: string): string {
  const ext = getFileExtension(filename).toLowerCase();
  const mimeTypes: Record<string, string> = {
    'txt': 'text/plain',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'json': 'application/json',
    'xml': 'application/xml',
    'pdf': 'application/pdf',
    'zip': 'application/zip',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'mp4': 'video/mp4',
    'avi': 'video/avi'
  };
  
  return mimeTypes[ext] || 'application/octet-stream';
}

// Storage utilities
export class StorageManager {
  private prefix: string;

  constructor(prefix: string = 'karen-ui') {
    this.prefix = prefix;
  }

  set(key: string, value: any): void {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(`${this.prefix}-${key}`, serialized);
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  }

  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(`${this.prefix}-${key}`);
      if (item === null) return defaultValue || null;
      return JSON.parse(item);
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return defaultValue || null;
    }
  }

  remove(key: string): void {
    try {
      localStorage.removeItem(`${this.prefix}-${key}`);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  }

  clear(): void {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(`${this.prefix}-`)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  }

  exists(key: string): boolean {
    return localStorage.getItem(`${this.prefix}-${key}`) !== null;
  }
}

// Event emitter for component communication
export class EventEmitter {
  private events: Record<string, Function[]> = {};

  on(event: string, callback: Function): void {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  }

  off(event: string, callback: Function): void {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(cb => cb !== callback);
  }

  emit(event: string, ...args: any[]): void {
    if (!this.events[event]) return;
    this.events[event].forEach(callback => {
      try {
        callback(...args);
      } catch (error) {
        console.error(`Error in event callback for ${event}:`, error);
      }
    });
  }

  once(event: string, callback: Function): void {
    const onceCallback = (...args: any[]) => {
      callback(...args);
      this.off(event, onceCallback);
    };
    this.on(event, onceCallback);
  }

  removeAllListeners(event?: string): void {
    if (event) {
      delete this.events[event];
    } else {
      this.events = {};
    }
  }
}

// Configuration manager
export class ConfigManager {
  private config: ComponentConfig;
  private storage: StorageManager;

  constructor(defaultConfig: ComponentConfig) {
    this.config = defaultConfig;
    this.storage = new StorageManager('karen-config');
    this.loadConfig();
  }

  get<K extends keyof ComponentConfig>(key: K): ComponentConfig[K] {
    return this.config[key];
  }

  set<K extends keyof ComponentConfig>(key: K, value: ComponentConfig[K]): void {
    this.config[key] = value;
    this.saveConfig();
  }

  getAll(): ComponentConfig {
    return { ...this.config };
  }

  update(updates: Partial<ComponentConfig>): void {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
  }

  reset(): void {
    this.storage.clear();
    // Reset to default config would require the original default config
  }

  private loadConfig(): void {
    const savedConfig = this.storage.get<Partial<ComponentConfig>>('config');
    if (savedConfig) {
      this.config = { ...this.config, ...savedConfig };
    }
  }

  private saveConfig(): void {
    this.storage.set('config', this.config);
  }
}

// Export singleton instances
export const validator = new Validator();
export const errorHandler = new ErrorHandler();
export const storageManager = new StorageManager();
export const eventEmitter = new EventEmitter();