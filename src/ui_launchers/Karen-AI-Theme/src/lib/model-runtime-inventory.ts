import { apiClient } from '@/lib/api';
import { getRuntimeDisplayName, getRuntimeGroupLabel, isBuiltInRuntimeProvider } from '@/lib/chat-response';

export interface RuntimeProviderModel {
  id: string;
  name: string;
  family?: string;
  source?: string;
  size_bytes?: number | null;
  capabilities?: string[];
  preferred_runtime?: string | null;
  compatible_runtimes?: string[];
}

export interface RuntimeProviderDetails {
  id: string;
  display_name: string;
  description?: string;
  provider_type?: string;
  selectable?: boolean;
  requires_api_key?: boolean;
  api_key_configured?: boolean;
  api_key_masked?: string | null;
  api_key_header?: string;
  api_key_prefix?: string;
  custom_headers?: Record<string, string>;
  docs_url?: string | null;
  base_url?: string | null;
  default_base_url?: string | null;
  default_model?: string | null;
  selected_model?: string | null;
  supports_base_url_override?: boolean;
  supports_model_discovery?: boolean;
  supports_model_pull?: boolean;
  supports_custom_auth?: boolean;
  supports_manual_model_entry?: boolean;
  runtime_source?: 'host' | 'container' | null;
  runtime_options?: Array<{
    source: 'host' | 'container';
    label: string;
    base_url: string;
    available: boolean;
    active?: boolean;
    status: string;
    message: string;
    setup_required?: boolean;
    setup_command?: string | null;
    install_supported?: boolean;
  }>;
  models: RuntimeProviderModel[];
}

export interface RuntimeSettingsResponse {
  selected_provider: string;
  selected_model: string;
  providers: RuntimeProviderDetails[];
  timeout_seconds?: number;
  auto_download?: boolean;
}

export interface NormalizedRuntimeProvider extends RuntimeProviderDetails {
  runtime_display_name: string;
  runtime_group_label: string;
  models: RuntimeProviderModel[];
}

export interface NormalizedRuntimeInventory {
  selected_provider: string;
  selected_model: string;
  providers: NormalizedRuntimeProvider[];
  selectableProviders: NormalizedRuntimeProvider[];
  builtInProviders: NormalizedRuntimeProvider[];
  localProviders: NormalizedRuntimeProvider[];
  thirdPartyProviders: NormalizedRuntimeProvider[];
  customProviders: NormalizedRuntimeProvider[];
  systemFallbackProvider: NormalizedRuntimeProvider | null;
  timeout_seconds?: number;
  auto_download?: boolean;
}

export type RuntimeProviderBucket = 'builtIn' | 'local' | 'thirdParty' | 'custom';

export const isVllmCompatibleModel = (model: RuntimeProviderModel | Record<string, unknown>): boolean => {
  const preferredRuntime = String(model.preferred_runtime || '').toLowerCase();

  if (preferredRuntime === 'vllm' || preferredRuntime === 'builtin_vllm') {
    return true;
  }

  const compatibleRuntimes = Array.isArray(model.compatible_runtimes)
    ? model.compatible_runtimes.map((runtime) => String(runtime).toLowerCase())
    : [];

  return (
    compatibleRuntimes.includes('vllm') ||
    compatibleRuntimes.includes('builtin_vllm')
  );
};

export const sortProviderModels = <T extends RuntimeProviderModel>(
  models: T[],
): T[] => {
  return [...models].sort((left, right) => {
    const leftVllm = isVllmCompatibleModel(left) ? 0 : 1;
    const rightVllm = isVllmCompatibleModel(right) ? 0 : 1;

    if (leftVllm !== rightVllm) {
      return leftVllm - rightVllm;
    }

    const leftRuntime = String(
      (left as { preferred_runtime?: unknown; model_format?: unknown }).preferred_runtime ||
      (left as { preferred_runtime?: unknown; model_format?: unknown }).model_format ||
      '',
    ).toLowerCase();
    const rightRuntime = String(
      (right as { preferred_runtime?: unknown; model_format?: unknown }).preferred_runtime ||
      (right as { preferred_runtime?: unknown; model_format?: unknown }).model_format ||
      '',
    ).toLowerCase();

    if (leftRuntime !== rightRuntime) {
      return leftRuntime.localeCompare(rightRuntime);
    }

    const leftName = String(
      (left as { display_name?: unknown }).display_name || left.name || left.id || '',
    ).toLowerCase();
    const rightName = String(
      (right as { display_name?: unknown }).display_name || right.name || right.id || '',
    ).toLowerCase();

    return leftName.localeCompare(rightName);
  });
};

const BUILTIN_RUNTIME_SEEDS: RuntimeProviderDetails[] = [
  {
    id: 'builtin_vllm',
    display_name: 'vLLM',
    description: 'Primary high-throughput text runtime.',
    provider_type: 'builtin',
    selectable: true,
    default_model: 'auto',
    selected_model: 'auto',
    supports_model_discovery: false,
    supports_model_pull: false,
    supports_custom_auth: false,
    supports_manual_model_entry: true,
    supports_base_url_override: false,
    models: [{ id: 'auto', name: 'auto', source: 'builtin' }],
  },
];

const SYSTEM_FALLBACK_SEED: RuntimeProviderDetails = {
  id: 'builtin_transformers',
  display_name: 'Transformers',
  description: 'Automatic fallback runtime for embeddings and emergency generation.',
  provider_type: 'builtin',
  selectable: false,
  default_model: 'auto',
  selected_model: 'auto',
  supports_model_discovery: true,  // Enable dynamic model discovery
  supports_model_pull: false,
  supports_custom_auth: false,
  supports_manual_model_entry: false,
  supports_base_url_override: false,
  models: [],  // Models will be loaded dynamically from /api/local/transformers/models
};

export const getRuntimeProviderBucket = (
  provider: RuntimeProviderDetails,
): RuntimeProviderBucket => {
  const providerType = String(provider.provider_type || '').toLowerCase();

  if (isBuiltInRuntimeProvider(provider.id)) return 'builtIn';
  if (provider.id === 'custom' || providerType === 'custom' || provider.supports_custom_auth) return 'custom';
  if (providerType === 'local') return 'local';
  return 'thirdParty';
};

const sortRank = (provider: RuntimeProviderDetails): number => {
  switch (getRuntimeProviderBucket(provider)) {
    case 'builtIn':
      return 0;
    case 'local':
      return 1;
    case 'thirdParty':
      return 2;
    case 'custom':
      return 3;
  }
};

const normalizeModels = (
  provider: RuntimeProviderDetails,
  selectedProvider: string,
  selectedModel: string,
): RuntimeProviderModel[] => {
  const seen = new Set<string>();
  const models = (provider.models || []).filter((model) => {
    if (!model.id) return false;
    if (seen.has(model.id)) return false;
    seen.add(model.id);
    return true;
  });
  const fallbackModelId =
    provider.selected_model ||
    provider.default_model ||
    (selectedProvider === provider.id ? selectedModel : null) ||
    '';

  return models.length > 0
    ? models
      : fallbackModelId
        ? [{ id: fallbackModelId, name: fallbackModelId, source: 'saved' }]
        : [];
};

/**
 * Dynamically load models from the transformers directory
 * This scans the backend /api/local/transformers/models endpoint
 * which returns all downloaded models.
 */
export async function loadDynamicTransformersModels(): Promise<RuntimeProviderModel[]> {
  try {
    const response = await apiClient.get<{ models: string[] }>(
      '/api/local/transformers/models'
    );

    return response.models.map((modelName: string) => ({
      id: modelName,
      name: modelName,
      family: 'transformers',
      source: 'runtime',
    }));
  } catch (error) {
    console.error('Failed to load transformers models:', error);
    return [];
  }
}

export function normalizeModelSettingsResponse(response: RuntimeSettingsResponse): NormalizedRuntimeInventory {
  const providerMap = new Map<string, RuntimeProviderDetails>();
  [...BUILTIN_RUNTIME_SEEDS, ...(response.providers || [])].forEach((provider) => {
    if (provider.id === SYSTEM_FALLBACK_SEED.id) {
      return;
    }
    providerMap.set(provider.id, provider);
  });
  const providers = Array.from(providerMap.values())
    .sort((a, b) => sortRank(a) - sortRank(b) || getRuntimeDisplayName(a.id, a.display_name).localeCompare(getRuntimeDisplayName(b.id, b.display_name)))
    .map((provider) => {
      // For transformers, load models dynamically from backend
      const normalizedModels = provider.id === SYSTEM_FALLBACK_SEED.id && provider.supports_model_discovery
        ? []
        : normalizeModels(provider, response.selected_provider, response.selected_model);
      return {
        ...provider,
        runtime_display_name: getRuntimeDisplayName(provider.id, provider.display_name),
        runtime_group_label: getRuntimeGroupLabel(provider.id),
        models: normalizedModels,
      };
    });

  const selectableProviders = providers.filter((provider) => provider.selectable !== false && provider.id !== SYSTEM_FALLBACK_SEED.id);
  const builtInProviders = providers.filter((provider) => getRuntimeProviderBucket(provider) === 'builtIn');
  const localProviders = providers.filter((provider) => getRuntimeProviderBucket(provider) === 'local');
  const customProviders = providers.filter((provider) => getRuntimeProviderBucket(provider) === 'custom');
  const thirdPartyProviders = providers.filter((provider) => getRuntimeProviderBucket(provider) === 'thirdParty');
  const systemFallbackProvider = {
    ...SYSTEM_FALLBACK_SEED,
    runtime_display_name: getRuntimeDisplayName(SYSTEM_FALLBACK_SEED.id, SYSTEM_FALLBACK_SEED.display_name),
    runtime_group_label: getRuntimeGroupLabel(SYSTEM_FALLBACK_SEED.id),
    models: normalizeModels(SYSTEM_FALLBACK_SEED, response.selected_provider, response.selected_model),
  } satisfies NormalizedRuntimeProvider;

  const selectedProvider =
    providers.find((provider) => provider.id === response.selected_provider)?.id ||
    providers[0]?.id ||
    '';
  const selectedModel =
    providers.find((provider) => provider.id === selectedProvider)?.selected_model ||
    providers.find((provider) => provider.id === selectedProvider)?.models[0]?.id ||
    response.selected_model ||
    '';

  return {
    selected_provider: selectedProvider,
    selected_model: selectedModel,
    providers,
    selectableProviders,
    builtInProviders,
    localProviders,
    thirdPartyProviders,
    customProviders,
    systemFallbackProvider,
    timeout_seconds: response.timeout_seconds,
    auto_download: response.auto_download,
  };
}
