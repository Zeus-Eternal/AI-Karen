import { extensionAPI } from './extensionAPI';
import type { ExtensionAPIResponse, ExtensionQueryParams, ExtensionInstallRequest, ExtensionUpdateRequest } from './types';

export async function listMarketplaceExtensions(
  params: ExtensionQueryParams = {},
): Promise<ExtensionAPIResponse> {
  const query = new URLSearchParams(params as any).toString();
  return extensionAPI({ method: 'GET', endpoint: `/api/marketplace?${query}` });
}

export async function installExtension(data: ExtensionInstallRequest): Promise<ExtensionAPIResponse> {
  return extensionAPI({ method: 'POST', endpoint: '/api/marketplace/install', data });
}

export async function updateExtension(data: ExtensionUpdateRequest): Promise<ExtensionAPIResponse> {
  return extensionAPI({ method: 'POST', endpoint: '/api/marketplace/update', data });
}
