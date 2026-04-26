import { getRuntimeDisplayName, getRuntimeGroupLabel, isBuiltInRuntimeProvider, isLocalRuntimeProvider } from '@/lib/chat-response';

export interface RuntimeProviderModel {
  id: string;
  name: string;
  source?: string;
}

export interface RuntimeProviderDetails {
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
}

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
  supports_model_discovery: false,
  supports_model_pull: false,
  supports_custom_auth: false,
  supports_manual_model_entry: true,
  supports_base_url_override: false,
  models: [{ id: 'auto', name: 'auto', source: 'builtin' }],
};

const sortRank = (provider: RuntimeProviderDetails): number => {
  if (isBuiltInRuntimeProvider(provider.id)) return 0;
  if (isLocalRuntimeProvider(provider.id)) return 1;
  if (provider.id === 'custom' || provider.provider_type === 'custom' || provider.supports_custom_auth) return 3;
  return 2;
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

export function normalizeModelSettingsResponse(response: RuntimeSettingsResponse): NormalizedRuntimeInventory {
  const providerMap = new Map<string, RuntimeProviderDetails>();
  [...BUILTIN_RUNTIME_SEEDS, ...(response.providers || [])].forEach((provider) => {
    if (provider.id === SYSTEM_FALLBACK_SEED.id) {
      return;
    }
    providerMap.set(provider.id, provider);
  });
  const providers = Array.from(providerMap.values())
    .filter((provider) => provider.selectable !== false)
    .sort((a, b) => sortRank(a) - sortRank(b) || getRuntimeDisplayName(a.id, a.display_name).localeCompare(getRuntimeDisplayName(b.id, b.display_name)))
    .map((provider) => {
      const normalizedModels = normalizeModels(provider, response.selected_provider, response.selected_model);
      return {
        ...provider,
        runtime_display_name: getRuntimeDisplayName(provider.id, provider.display_name),
        runtime_group_label: getRuntimeGroupLabel(provider.id),
        models: normalizedModels,
      };
    });

  const selectableProviders = providers.filter((provider) => provider.selectable !== false && provider.id !== SYSTEM_FALLBACK_SEED.id);
  const builtInProviders = providers.filter((provider) => provider.id === 'builtin_vllm');
  const localProviders = providers.filter((provider) => isLocalRuntimeProvider(provider.id) && !isBuiltInRuntimeProvider(provider.id));
  const customProviders = providers.filter((provider) => provider.id === 'custom' || provider.provider_type === 'custom' || provider.supports_custom_auth);
  const thirdPartyProviders = providers.filter((provider) => !builtInProviders.some((builtIn) => builtIn.id === provider.id) && !localProviders.some((local) => local.id === provider.id) && !customProviders.some((custom) => custom.id === provider.id));
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
  };
}
