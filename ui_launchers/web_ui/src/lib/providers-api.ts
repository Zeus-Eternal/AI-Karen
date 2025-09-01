// Lightweight client for provider discovery and model listings

export interface ProviderDiscoveryItem {
  id: string;
  title: string;
  group: 'local' | 'cloud';
  canListModels: boolean;
  canInfer: boolean;
  available: boolean;
}

export interface ContractModelInfo {
  id: string;
  provider: string;
  displayName: string;
  family: string;
  installed: boolean;
  remote: boolean;
  size?: string;
  quant?: string;
  contextWindow?: number;
  tags?: string[];
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  // Get auth headers from session
  const authHeaders: Record<string, string> = {};
  
  // Try to get the access token from localStorage (set by AuthContext)
  if (typeof window !== 'undefined') {
    const accessToken = localStorage.getItem('karen_access_token');
    if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
      authHeaders['Authorization'] = `Bearer ${accessToken}`;
    }
  }

  const res = await fetch(path, {
    method: 'GET',
    credentials: 'include',
    headers: { 
      'Accept': 'application/json',
      ...authHeaders
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText} at ${path}${text ? `: ${text}` : ''}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchProviderDiscovery(): Promise<ProviderDiscoveryItem[]> {
  try {
    const result = await getJson<ProviderDiscoveryItem[]>('/api/providers/discovery');
    return Array.isArray(result) ? result : [];
  } catch (err) {
    // Fallback to public endpoint if auth is required
    try {
      const result = await getJson<ProviderDiscoveryItem[]>('/api/public/providers/discovery');
      return Array.isArray(result) ? result : [];
    } catch {
      return [];
    }
  }
}

export async function listLlamaModels(): Promise<ContractModelInfo[]> {
  try {
    const result = await getJson<ContractModelInfo[]>('/api/providers/local/llama/models');
    return Array.isArray(result) ? result : [];
  } catch {
    try {
      const result = await getJson<ContractModelInfo[]>('/api/public/providers/local/llama/models');
      return Array.isArray(result) ? result : [];
    } catch {
      return [];
    }
  }
}

export async function listTransformersModels(): Promise<ContractModelInfo[]> {
  try {
    const result = await getJson<ContractModelInfo[]>('/api/providers/local/transformers/models');
    return Array.isArray(result) ? result : [];
  } catch {
    try {
      const result = await getJson<ContractModelInfo[]>('/api/public/providers/local/transformers/models');
      return Array.isArray(result) ? result : [];
    } catch {
      return [];
    }
  }
}

export async function listSpacyPipelines(): Promise<string[]> {
  try {
    const result = await getJson<string[]>('/api/providers/local/spacy/pipelines');
    return Array.isArray(result) ? result : [];
  } catch {
    return await getJson<string[]>('/api/public/providers/local/spacy/pipelines');
  }
}

export async function openaiPing(): Promise<{ ok: boolean }> {
  return getJson<{ ok: boolean }>('/api/providers/cloud/openai/ping');
}

export async function listOpenaiModels(): Promise<ContractModelInfo[]> {
  try {
    const result = await getJson<ContractModelInfo[]>('/api/providers/cloud/openai/models');
    return Array.isArray(result) ? result : [];
  } catch {
    return [];
  }
}
