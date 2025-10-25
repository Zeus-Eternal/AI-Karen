import { NextRequest, NextResponse } from 'next/server';

import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const CANDIDATE_BACKENDS = getBackendCandidates();
const HEALTH_TIMEOUT_MS = 2000;

export async function GET(request: NextRequest) {
  try {
    // Try multiple backend base URLs to be resilient to Docker/host differences
    const bases = CANDIDATE_BACKENDS;
    let lastErr: any = null;
    let healthResponse: PromiseSettledResult<Response> | null = null;
    let providersResponse: PromiseSettledResult<Response> | null = null;
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
            // @ts-ignore Node/undici hints
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
            // @ts-ignore Node/undici hints
            keepalive: true,
            cache: 'no-store',
          })
        ]);
        clearTimeout(timeout);
        // If health responded at all (fulfilled), use this base
        if (healthResponse.status === 'fulfilled' || providersResponse.status === 'fulfilled') {
          break;
        }
      } catch (err) {
        clearTimeout(timeout);
        lastErr = err;
        // try next base
        continue;
      }
    }
      
      // Process health response
      let healthData: any = { status: 'unknown' };
      if (healthResponse && healthResponse.status === 'fulfilled' && healthResponse.value.ok) {
        const contentType = healthResponse.value.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          try {
            healthData = await healthResponse.value.json();
          } catch {
            healthData = { status: 'ok' };
          }
        } else {
          try {
            const text = await healthResponse.value.text();
            healthData = { status: text === 'ok' ? 'ok' : 'degraded' };
          } catch {
            healthData = { status: 'ok' };
          }
        }
      }

      // Process providers response
      let providersData: any = null;
      if (providersResponse && providersResponse.status === 'fulfilled' && providersResponse.value.ok) {
        try {
          providersData = await providersResponse.value.json();
        } catch {
          providersData = null;
        }
      }

      const statusValue = (healthData.status || healthData.state || '').toString().toLowerCase();
      const normalizedStatus = ['ok', 'healthy', 'up'].includes(statusValue) ? 'healthy' : 'degraded';

      const providers = providersData?.providers || [];
      const totalModels = providers.reduce((total: number, provider: any) =>
        total + (provider.total_models || provider.cached_models_count || 0), 0);

      const localFallbackReady = providers.some((provider: any) =>
        provider.provider_type === 'local' &&
        ['healthy', 'degraded', 'unknown'].includes((provider.health_status || '').toLowerCase())
      );

      const remoteProviderOutages = providers
        .filter((provider: any) =>
          provider.provider_type !== 'local' &&
          ['degraded', 'unhealthy', 'unknown'].includes((provider.health_status || '').toLowerCase())
        )
        .map((provider: any) => provider.name);

      const aiStatus = remoteProviderOutages.length > 0 && !localFallbackReady
        ? 'degraded'
        : (healthData.ai_status || normalizedStatus);

      const isActive = !(normalizedStatus === 'healthy' && aiStatus === 'healthy');

      const data = {
        degraded_mode: isActive,
        is_active: isActive,
        status: normalizedStatus,
        reason: normalizedStatus === 'healthy' ? '' : 'System experiencing issues',
        infrastructure_issues: healthData.infrastructure_issues || [],
        core_helpers_available: {
          fallback_responses: true,
          local_fallback_ready: localFallbackReady,
          total_ai_capabilities: localFallbackReady || totalModels > 0
        },
        ai_status: aiStatus,
        failed_providers: remoteProviderOutages,
        providers,
        total_providers: providersData?.total_providers || providers.length,
        models_available: totalModels,
        timestamp: new Date().toISOString(),
        compatibility_payload: healthData.payload || null
      };

      // Always respond 200; encode degraded state in body
      return NextResponse.json(data, { status: 200 });
    
  } catch (error) {
    console.error('Degraded mode check error:', error);
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
