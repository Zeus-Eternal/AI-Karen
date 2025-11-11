import { extensionAPI } from './extensionAPI';
import type { ExtensionAPIResponse, ExtensionQueryParams, ExtensionInstallRequest, ExtensionUpdateRequest } from './types';

export async function listMarketplaceExtensions(
  params: ExtensionQueryParams = {},
): Promise<ExtensionAPIResponse> {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue;
    }
    searchParams.append(key, String(value));
  }

  const query = searchParams.toString();
  const endpoint = query ? `/api/marketplace?${query}` : '/api/marketplace';
  return extensionAPI({ method: 'GET', endpoint });
}

export async function installExtension(data: ExtensionInstallRequest): Promise<ExtensionAPIResponse> {
  return extensionAPI({ method: 'POST', endpoint: '/api/marketplace/install', data });
}

export async function updateExtension(data: ExtensionUpdateRequest): Promise<ExtensionAPIResponse> {
  return extensionAPI({ method: 'POST', endpoint: '/api/marketplace/update', data });
}
