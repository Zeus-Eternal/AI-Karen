import type { SuggestedAction } from '@/lib/agent-ui/service';

// Chat Message Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status: 'pending' | 'completed' | 'failed';
  actions?: SuggestedAction[];
  metadata?: Record<string, unknown>;
  structuredContent?: Record<string, unknown>;
}

// Assist Response Types
export interface AssistResponse {
  answer: string;
  structured_content?: Record<string, unknown>;
  actions?: SuggestedAction[];
  metadata?: Record<string, unknown>;
  correlation_id?: string;
}

// Model Settings Types
export interface ModelDetails {
  id: string;
  name: string;
  source?: string;
}

export interface ProviderDetails {
  id: string;
  display_name: string;
  description?: string;
  provider_type?: string;
  selectable?: boolean;
  requires_api_key?: boolean;
  api_key_configured?: boolean;
  base_url?: string | null;
  default_base_url?: string | null;
  default_model?: string | null;
  selected_model?: string | null;
  supports_base_url_override?: boolean;
  models: ModelDetails[];
}

export interface ModelSettingsResponse {
  selected_provider: string;
  selected_model: string;
  providers: ProviderDetails[];
}

// Streaming Metrics Types
export interface StreamingMetrics {
  chunksReceived: number;
  totalBytes: number;
  connectionHealth: 'excellent' | 'good' | 'poor' | 'critical';
  lastChunkTime: number;
}

// User Preferences Types
export interface UserPreferences {
  preferredAddressName: string;
  fullName: string;
  displayName: string | null;
  firstNameOption: string | null;
  shouldPromptForPreferredName: boolean;
  recentMessages: Array<{
    role: string;
    content: string;
  }>;
}