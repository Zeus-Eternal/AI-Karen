import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

function getStringField(data: unknown, field: string): string {
  if (typeof data !== 'object' || data === null) return '';
  const value = (data as Record<string, unknown>)[field];
  if (typeof value === 'string') return value;
  if (value === undefined || value === null) return '';
  return String(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  if (typeof value === 'object' && value !== null) {
    return value as Record<string, unknown>;
  }
  return {};
}

function getNumericField(data: Record<string, unknown>, field: string): number {
  const value = data[field];
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? 0 : parsed;
  }
  return 0;
}

function getArrayField(data: unknown, field: string): unknown[] {
  const record = asRecord(data);
  const value = record[field];
  return Array.isArray(value) ? value : [];
}
const CANDIDATE_BACKENDS = getBackendCandidates();
const HEALTH_TIMEOUT_MS = 2000;
export async function GET(request: NextRequest) {
  try {
    // Try multiple backend base URLs to be resilient to Docker/host differences
    const bases = CANDIDATE_BACKENDS;
    let healthResponse: PromiseSettledResult<Response> | null = null;
    let providersResponse: PromiseSettledResult<Response> | null = null;
    const unauthorizedStatus = new Set([401, 403]);
    for (const base of bases) {
      const healthUrl = withBackendPath('/health', base);
      const providersUrl = withBackendPath('/api/providers', base);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
      try {
        // Fetch both health status and provider information in parallel
        [healthResponse, providersResponse] = await Promise.allSettled([
          fetch(healthUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Connection': 'keep-alive',
              ...(request.headers.get('authorization') && {
                'Authorization': request.headers.get('authorization')!
              }),
            },
            signal: controller.signal,
            // keepalive is supported in Node/undici runtimes
            keepalive: true,
            cache: 'no-store',
          }),
          fetch(providersUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Connection': 'keep-alive',
              ...(request.headers.get('authorization') && {
                'Authorization': request.headers.get('authorization')!
              }),
            },
            signal: controller.signal,
            // keepalive is supported in Node/undici runtimes
            keepalive: true,
            cache: 'no-store',
          })
        ]);
        clearTimeout(timeout);
        // If health responded at all (fulfilled), use this base
        if (healthResponse.status === 'fulfilled' || providersResponse.status === 'fulfilled') {
          break;
        }
      } catch {
        clearTimeout(timeout);
        // try next base
        continue;
      }
    }
      // Process health response
      let healthData: unknown = { status: 'unknown' };
      if (healthResponse && healthResponse.status === 'fulfilled') {
        const response = healthResponse.value;
        if (response.ok) {
          const contentType = response.headers.get('content-type') || '';
          if (contentType.includes('application/json')) {
            try {
              healthData = await response.json();
            } catch {
              healthData = { status: 'ok' };
            }
          } else {
            try {
              const text = await response.text();
              healthData = { status: text === 'ok' ? 'ok' : 'degraded' };
            } catch {
              healthData = { status: 'ok' };
            }
          }
        } else if (unauthorizedStatus.has(response.status)) {
          healthData = {
            status: 'healthy',
            ai_status: 'healthy',
            reason: 'Health check requires authentication',
            infrastructure_issues: ['health endpoint authentication']
          };
        }
      }
      // Process providers response
      let providersData: unknown = null;
      if (providersResponse && providersResponse.status === 'fulfilled') {
        if (providersResponse.value.ok) {
          try {
            providersData = await providersResponse.value.json();
          } catch {
            providersData = null;
          }
        } else if (unauthorizedStatus.has(providersResponse.value.status)) {
          providersData = { providers: [], total_providers: 0, auth_required: true };
        }
      }
      const statusValue = (
        getStringField(healthData, 'status') ||
        getStringField(healthData, 'state')
      ).toLowerCase();
      const normalizedStatus = ['ok', 'healthy', 'up'].includes(statusValue) ? 'healthy' : 'degraded';
      const providersRaw = (providersData as { providers?: unknown })?.providers;
      const providers = Array.isArray(providersRaw) ? (providersRaw as unknown[]) : [];
      const typedProviders = providers.map(asRecord);
      const totalModels = typedProviders.reduce((total, provider) => {
        const count =
          getNumericField(provider, 'total_models') ||
          getNumericField(provider, 'cached_models_count');
        return total + count;
      }, 0);
      const localFallbackReady = typedProviders.some((provider) => {
        const providerType = getStringField(provider, 'provider_type');
        const healthStatus = getStringField(provider, 'health_status').toLowerCase();
        return (
          providerType === 'local' &&
          ['healthy', 'degraded', 'unknown'].includes(healthStatus)
        );
      });
      const remoteProviderOutages = typedProviders
        .filter((provider) => {
          const providerType = getStringField(provider, 'provider_type');
          const healthStatus = getStringField(provider, 'health_status').toLowerCase();
          return (
            providerType !== 'local' &&
            ['degraded', 'unhealthy', 'unknown'].includes(healthStatus)
          );
        })
        .map((provider) => getStringField(provider, 'name'));
      const aiStatus = remoteProviderOutages.length > 0 && !localFallbackReady
        ? 'degraded'
        : (getStringField(healthData, 'ai_status') || normalizedStatus);
      const isActive = !(normalizedStatus === 'healthy' && aiStatus === 'healthy');
      const lastErrorMessage =
        getStringField(healthData, 'reason') ||
        getStringField(healthData, 'message') ||
        getStringField(providersData, 'message');
        const degradedReason = normalizedStatus === 'healthy'
          ? ''
          : lastErrorMessage
              ? `System experiencing issues: ${lastErrorMessage}`
              : 'System experiencing issues';

      const compatibilityPayload = asRecord(healthData).payload ?? null;
      const data = {
        degraded_mode: isActive,
        is_active: isActive,
        status: normalizedStatus,
          reason: degradedReason,
        infrastructure_issues: getArrayField(healthData, 'infrastructure_issues'),
        core_helpers_available: {
          fallback_responses: true,
          local_fallback_ready: localFallbackReady,
          total_ai_capabilities: localFallbackReady || totalModels > 0
        },
        ai_status: aiStatus,
        failed_providers: remoteProviderOutages,
        providers,
        total_providers:
          getNumericField(asRecord(providersData), 'total_providers') || providers.length,
        models_available: totalModels,
        timestamp: new Date().toISOString(),
        compatibility_payload: compatibilityPayload
      };
      // Always respond 200; encode degraded state in body
      return NextResponse.json(data, { status: 200 });
  } catch {
    // Normalize to 200 with degraded mode on unexpected errors
    return NextResponse.json(
      {
        is_active: true,
        reason: 'Health check failed',
        infrastructure_issues: ['Health check system'],
        core_helpers_available: {
          fallback_responses: true,
          total_ai_capabilities: false
        },
        ai_status: 'degraded',
        failed_providers: [],
        providers: [],
        total_providers: 0,
        models_available: 0,
        timestamp: new Date().toISOString()
      },
      { status: 200 }
    );
  }
}
