import type { ExtensionAPIRequest, ExtensionAPIResponse } from './types';

function buildEndpointUrl(endpoint: string, params?: Record<string, unknown>): string {
  if (!params || Object.keys(params).length === 0) {
    return endpoint;
  }

  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => query.append(key, String(item)));
      continue;
    }

    query.append(key, String(value));
  }

  const separator = endpoint.includes('?') ? '&' : '?';
  return `${endpoint}${separator}${query.toString()}`;
}

async function parseResponseBody(response: Response): Promise<any> {
  const contentType = response.headers.get('content-type') ?? '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  if (!text) {
    return undefined;
  }

  try {
    return JSON.parse(text);
  } catch (error) {
    return text;
  }
}

export async function extensionAPI<T = unknown>(
  req: ExtensionAPIRequest,
): Promise<ExtensionAPIResponse<T>> {
  try {
    const url = buildEndpointUrl(req.endpoint, req.params);
    const response = await fetch(url, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...(req.headers ?? {}),
      },
      body: req.data ? JSON.stringify(req.data) : undefined,
    });

    const payload = await parseResponseBody(response);

    if (!response.ok) {
      return {
        success: false,
        error: {
          code: `http_${response.status}`,
          message:
            (payload && typeof payload === 'object'
              ? payload.detail || payload.message
              : undefined) ?? response.statusText,
          details: payload,
        },
      };
    }

    const meta: ExtensionAPIResponse['meta'] = {};
    const totalHeader = response.headers.get('x-total-count');
    const pageHeader = response.headers.get('x-page');
    const limitHeader = response.headers.get('x-limit');

    if (totalHeader) {
      meta.total = Number(totalHeader);
    }
    if (pageHeader) {
      meta.page = Number(pageHeader);
    }
    if (limitHeader) {
      meta.limit = Number(limitHeader);
    }

    return {
      success: true,
      data: payload as T,
      meta: Object.keys(meta).length > 0 ? meta : undefined,
    };
  } catch (error: any) {
    return {
      success: false,
      error: {
        code: 'network_error',
        message: error?.message ?? 'Network request failed',
        details: error,
      },
    };
  }
}
