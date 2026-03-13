import { extensionAPI } from './extensionAPI';
import type { ExtensionAPIResponse, ExtensionQueryParams } from './types';

export async function listPlugins(params: ExtensionQueryParams = {}): Promise<ExtensionAPIResponse> {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue;
    }
    searchParams.append(key, String(value));
  }

  const query = searchParams.toString();
  const endpoint = query ? `/api/plugins?${query}` : '/api/plugins';
  return extensionAPI({ method: 'GET', endpoint });
}
