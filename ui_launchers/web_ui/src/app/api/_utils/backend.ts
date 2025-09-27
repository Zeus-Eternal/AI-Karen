/**
 * Backend endpoint resolution utilities for Next.js API routes.
 *
 * Centralizes logic for determining which backend base URL to use so that
 * development (localhost) and container deployments (Docker hostnames) both
 * work without manual tweaks.
 */

const DEFAULT_PORT = process.env.KAREN_BACKEND_PORT || process.env.BACKEND_PORT || '8000';

const ENV_CANDIDATES = [
  process.env.KAREN_BACKEND_URL,
  process.env.API_BASE_URL,
  process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
  process.env.NEXT_PUBLIC_API_BASE_URL,
];

const DEFAULT_HOST_CANDIDATES = [
  `http://localhost:${DEFAULT_PORT}`,
  `http://127.0.0.1:${DEFAULT_PORT}`,
  `http://0.0.0.0:${DEFAULT_PORT}`,
  `http://ai-karen-api:${DEFAULT_PORT}`,
  `http://api:${DEFAULT_PORT}`,
];

function normalizeUrl(url: string): string {
  return url.replace(/\/+$/, '');
}

function buildCandidateList(extra: (string | undefined)[] = []): string[] {
  const ordered = [...extra, ...ENV_CANDIDATES, ...DEFAULT_HOST_CANDIDATES]
    .filter((value): value is string => Boolean(value && value.trim()))
    .map((value) => normalizeUrl(value.trim()));

  return Array.from(new Set(ordered));
}

/**
 * Return the preferred backend base URL. The first valid candidate wins.
 */
export function getBackendBaseUrl(): string {
  const candidates = buildCandidateList();
  return candidates[0] ?? 'http://localhost:8000';
}

/**
 * Return every backend candidate URL in priority order. Useful for health
 * checks that want to probe multiple potential hosts (e.g. localhost and
 * Docker service names).
 */
export function getBackendCandidates(additional: (string | undefined)[] = []): string[] {
  return buildCandidateList(additional);
}

/**
 * Helper that joins a path onto the resolved backend base URL.
 */
export function withBackendPath(path: string, baseUrl = getBackendBaseUrl()): string {
  const normalizedBase = normalizeUrl(baseUrl);
  if (!path.startsWith('/')) {
    return `${normalizedBase}/${path}`;
  }
  return `${normalizedBase}${path}`;
}
