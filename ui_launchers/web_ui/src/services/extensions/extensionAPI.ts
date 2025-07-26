import type { ExtensionAPIRequest, ExtensionAPIResponse } from './types';

export async function extensionAPI<T = any>(
  req: ExtensionAPIRequest,
): Promise<ExtensionAPIResponse<T>> {
  try {
    const res = await fetch(req.endpoint, {
      method: req.method,
      headers: { 'Content-Type': 'application/json', ...(req.headers || {}) },
      body: req.data ? JSON.stringify(req.data) : undefined,
    });
    const data = await res.json();
    return { success: res.ok, data };
  } catch (error: any) {
    return {
      success: false,
      error: { code: 'network_error', message: error.message, details: error },
    };
  }
}
