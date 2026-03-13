/**
 * Enhanced Chat Types for Production KAREN Chat System
 * Extends base types with conversation management, provider support, and advanced features
 */

import { ChatMessage } from '@/lib/types';

// Enhanced Message Types
export interface EnhancedChatMessage extends ChatMessage {
  // Additional metadata for production features
  conversationId?: string;
  messageId: string;
  parentId?: string; // For threaded conversations
  threadId?: string; // For conversation threads
  
  // Message status tracking
  status: MessageStatus;
  deliveryStatus?: DeliveryStatus;
  
  // Attachments and media
  attachments?: MessageAttachment[];
  
  // Voice and transcription
  voiceData?: VoiceData;
  transcription?: TranscriptionData;
  
  // Provider information
  provider?: string;
  model?: string;
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
  
  // Reactions and interactions
  reactions?: MessageReaction[];
  isEdited?: boolean;
  editedAt?: Date;
  
  // Search and filtering
  tags?: string[];
  isBookmarked?: boolean;
}

export enum MessageStatus {
  SENDING = 'sending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  RETRYING = 'retrying'
}

export enum DeliveryStatus {
  PENDING = 'pending',
  DELIVERED = 'delivered',
  READ = 'read',
  FAILED = 'failed'
}

export interface MessageAttachment {
  id: string;
  name: string;
  type: AttachmentType;
  size: number;
  url: string;
  thumbnailUrl?: string;
  metadata?: Record<string, unknown>;
  uploadedAt: Date;
  status: AttachmentStatus;
}

export enum AttachmentType {
  IMAGE = 'image',
  VIDEO = 'video',
  AUDIO = 'audio',
  DOCUMENT = 'document',
  CODE = 'code',
  DATA = 'data'
}

export enum AttachmentStatus {
  UPLOADING = 'uploading',
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  FAILED = 'failed'
}

export interface VoiceData {
  duration: number;
  audioUrl?: string;
  waveform?: number[];
  format: string;
  size: number;
}

export interface TranscriptionData {
  text: string;
  confidence: number;
  language: string;
  timestamps?: TranscriptionTimestamp[];
}

export interface TranscriptionTimestamp {
  start: number;
  end: number;
  text: string;
  confidence: number;
}

export interface MessageReaction {
  id: string;
  emoji: string;
  userId: string;
  timestamp: Date;
}

// Conversation Management Types
export interface Conversation {
  id: string;
  title: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  lastMessageAt?: Date;
  
  // Message counts and stats
  messageCount: number;
  unreadCount: number;
  
  // Participants
  participants: ConversationParticipant[];
  
  // Settings and configuration
  settings: ConversationSettings;
  
  // Provider configuration
  provider: string;
  model?: string;
  
  // Metadata and tags
  tags?: string[];
  isPinned?: boolean;
  isArchived?: boolean;
  metadata?: Record<string, unknown>;
  
  // Status and health
  status: ConversationStatus;
  healthScore?: number;
}

export interface ConversationParticipant {
  id: string;
  name: string;
  avatar?: string;
  role: ParticipantRole;
  joinedAt: Date;
  lastSeen?: Date;
  isOnline: boolean;
  permissions: ParticipantPermissions;
}

export enum ParticipantRole {
  OWNER = 'owner',
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  MEMBER = 'member',
  GUEST = 'guest'
}

export interface ParticipantPermissions {
  canRead: boolean;
  canWrite: boolean;
  canDelete: boolean;
  canManageSettings: boolean;
  canManageParticipants: boolean;
}

export interface ConversationSettings {
  // General settings
  title: string;
  description?: string;
  isPublic: boolean;
  
  // Message settings
  allowAttachments: boolean;
  maxAttachmentSize: number;
  allowedAttachmentTypes: AttachmentType[];
  
  // AI settings
  provider: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  
  // Voice settings
  enableVoice: boolean;
  autoTranscribe: boolean;
  voiceLanguage: string;
  
  // Privacy and security
  encryptionEnabled: boolean;
  retentionDays?: number;
  
  // Notifications
  enableNotifications: boolean;
  notificationTypes: NotificationType[];
}

export enum NotificationType {
  NEW_MESSAGE = 'new_message',
  MENTION = 'mention',
  REPLY = 'reply',
  SYSTEM = 'system'
}

export enum ConversationStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
  SUSPENDED = 'suspended'
}

// Provider Configuration Types
export interface LLMProvider {
  id: string;
  name: string;
  displayName: string;
  description: string;
  version: string;

  // Provider capabilities
  capabilities: ProviderCapabilities;

  // Models available
  models: LLMModel[];

  // Configuration schema
  configSchema: ProviderConfigSchema;

  // Status and health
  status: ProviderStatus;
  healthCheck?: ProviderHealthCheck;

  // Pricing and limits
  pricing?: ProviderPricing;
  rateLimits?: ProviderRateLimits;

  // Authentication
  authType: AuthType;
  requiredConfig: string[];

  // UI configuration
  icon?: string;
  theme?: ProviderTheme;
  documentation?: string;

  // Additional properties
  priority?: number;
  config?: Record<string, unknown>;
}

export interface ProviderCapabilities {
  textGeneration: boolean;
  streaming: boolean;
  functionCalling: boolean;
  imageGeneration: boolean;
  voiceInput: boolean;
  voiceOutput: boolean;
  fileUpload: boolean;
  codeExecution: boolean;
  webSearch: boolean;
  memory: boolean;
  vision: boolean;
  contextWindow: number;
  maxTokens: number;
}

export interface LLMModel {
  id: string;
  name: string;
  displayName: string;
  description: string;
  
  // Model capabilities
  capabilities: ModelCapabilities;
  
  // Performance characteristics
  contextWindow: number;
  maxTokens: number;
  temperature: ModelRange;
  performance?: {
    averageResponseTime: number;
    successRate: number;
  };
  
  // Pricing
  inputTokenPrice: number;
  outputTokenPrice: number;
  
  // Availability
  status?: 'available' | 'loading' | 'unavailable';
  isAvailable: boolean;
  isBeta?: boolean;
  deprecated?: boolean;
  
  // Specialized features
  specializations?: string[];
  recommendedFor?: string[];
}

export interface ModelCapabilities {
  textGeneration: boolean;
  codeGeneration: boolean;
  codeExecution: boolean;  // Added for code execution capability
  reasoning: boolean;
  mathematics: boolean;
  multilingual: boolean;
  vision: boolean;
  audio: boolean;
  functionCalling: boolean;
  streaming: boolean;
  jsonMode: boolean;
}

export interface ModelRange {
  min: number;
  max: number;
  default: number;
  step?: number;
}

export interface ProviderConfigSchema {
  type: 'object';
  properties: Record<string, ConfigProperty>;
  required: string[];
}

export interface ConfigProperty {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'select';
  title: string;
  description?: string;
  default?: unknown;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  step?: number;
  format?: string;
  pattern?: string;
  secret?: boolean;
}

export enum ProviderStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  MAINTENANCE = 'maintenance',
  ERROR = 'error',
  DEPRECATED = 'deprecated'
}

export interface ProviderHealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  lastChecked: Date;
  responseTime: number;
  errorRate: number;
  uptime: number;
  issues?: string[];
}

export interface ProviderPricing {
  currency: string;
  inputTokenPrice: number;
  outputTokenPrice: number;
  requestPrice?: number;
  freeQuota?: number;
  billingCycle: 'monthly' | 'annual' | 'pay-as-you-go';
}

export interface ProviderRateLimits {
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  tokensPerMinute: number;
  tokensPerHour: number;
  tokensPerDay: number;
  concurrentRequests: number;
}

export enum AuthType {
  API_KEY = 'api_key',
  OAUTH = 'oauth',
  BEARER_TOKEN = 'bearer_token',
  BASIC_AUTH = 'basic_auth',
  CUSTOM = 'custom'
}

export interface ProviderTheme {
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  textColor: string;
  borderColor: string;
  logo?: string;
}

// Real-time Communication Types
export interface StreamingChunk {
  id: string;
  content: string;
  delta?: string;
  isComplete: boolean;
  metadata?: Record<string, unknown>;
  timestamp: Date;
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: unknown;
  timestamp: Date;
  id?: string;
}

export enum WebSocketMessageType {
  MESSAGE = 'message',
  TYPING = 'typing',
  STATUS = 'status',
  ERROR = 'error',
  PROVIDER_CHANGE = 'provider_change',
  CONVERSATION_UPDATE = 'conversation_update',
  USER_PRESENCE = 'user_presence'
}

export interface ConnectionStatus {
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  lastConnected?: Date;
  connectionAttempts: number;
  error?: string;
}

// Search and Filtering Types
export interface ConversationFilter {
  query?: string;
  tags?: string[];
  providers?: string[];
  status?: ConversationStatus[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  participants?: string[];
  isPinned?: boolean;
  isArchived?: boolean;
}

export interface MessageFilter {
  query?: string;
  role?: ChatMessage['role'][];
  status?: MessageStatus[];
  hasAttachments?: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  tags?: string[];
  provider?: string;
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// File Upload Types
export interface UploadProgress {
  id: string;
  file: File;
  progress: number;
  status: UploadStatus;
  error?: string;
  url?: string;
}

export enum UploadStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// Voice Recording Types
export interface VoiceRecording {
  id: string;
  blob: Blob;
  duration: number;
  format: string;
  size: number;
  waveform?: number[];
  status: RecordingStatus;
  transcription?: string;
  error?: string;
}

export enum RecordingStatus {
  IDLE = 'idle',
  RECORDING = 'recording',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// Error Types
export interface ChatError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: Date;
  context?: ErrorContext;
}

export interface ErrorContext {
  conversationId?: string;
  messageId?: string;
  provider?: string;
  action?: string;
  userId?: string;
}

// Analytics and Metrics Types
export interface ChatMetrics {
  conversationId: string;
  messageCount: number;
  userMessageCount: number;
  assistantMessageCount: number;
  averageResponseTime: number;
  totalTokensUsed: number;
  averageTokensPerMessage: number;
  providerUsage: Record<string, number>;
  errorRate: number;
  satisfactionScore?: number;
  engagementMetrics: EngagementMetrics;
}

export interface EngagementMetrics {
  messagesPerSession: number;
  sessionDuration: number;
  returnRate: number;
  bookmarkRate: number;
  shareRate: number;
}

// UI State Types
export interface ChatUIState {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  providerSettingsOpen: boolean;
  newConversationDialogOpen: boolean;
  conversationActionsOpen: boolean;
  
  // View settings
  viewMode: 'chat' | 'list' | 'grid';
  sortBy: 'recent' | 'name' | 'messageCount' | 'lastActivity';
  sortOrder: 'asc' | 'desc';
  
  // Display settings
  showTimestamps: boolean;
  showMetadata: boolean;
  showAvatars: boolean;
  showReactions: boolean;
  showAttachments: boolean;
  
  // Theme and layout
  theme: 'light' | 'dark' | 'auto';
  density: 'compact' | 'normal' | 'spacious';
  
  // Accessibility
  fontSize: 'small' | 'medium' | 'large';
  highContrast: boolean;
  reducedMotion: boolean;
  screenReaderOptimized: boolean;
}

// Export all types for easy importing
export type {
  EnhancedChatMessage as ChatMessage
};

