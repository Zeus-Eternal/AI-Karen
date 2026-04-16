export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
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
  models: Array<{
    id: string;
    name: string;
    source?: string;
  }>;
}