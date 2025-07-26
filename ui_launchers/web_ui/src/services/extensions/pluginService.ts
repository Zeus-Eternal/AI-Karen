import { extensionAPI } from './extensionAPI';
import type { ExtensionAPIResponse, ExtensionQueryParams } from './types';

export async function listPlugins(params: ExtensionQueryParams = {}): Promise<ExtensionAPIResponse> {
  const query = new URLSearchParams(params as any).toString();
  return extensionAPI({ method: 'GET', endpoint: `/api/plugins?${query}` });
}
