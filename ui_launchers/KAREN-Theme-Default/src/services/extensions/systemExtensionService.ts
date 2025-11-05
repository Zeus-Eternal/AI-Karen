import { extensionAPI } from './extensionAPI';
import type {
  ExtensionAPIResponse,
  ExtensionHealthSummary,
  ExtensionRegistrySummaryResponse,
} from './types';

export async function listSystemExtensions(): Promise<
  ExtensionAPIResponse<ExtensionRegistrySummaryResponse>
> {
  return extensionAPI<ExtensionRegistrySummaryResponse>({
    method: 'GET',
    endpoint: '/api/extensions/registry/summary',
  });
}

export async function getSystemExtensionHealth(): Promise<
  ExtensionAPIResponse<ExtensionHealthSummary>
> {
  return extensionAPI<ExtensionHealthSummary>({
    method: 'GET',
    endpoint: '/api/extensions/health',
  });
}

export async function updateSystemExtensionState(
  name: string,
  enabled: boolean,
): Promise<ExtensionAPIResponse<{ message?: string; status?: string }>> {
  const action = enabled ? 'load' : 'unload';
  return extensionAPI({
    method: 'POST',
    endpoint: `/api/extensions/${encodeURIComponent(name)}/${action}`,
  });
}
