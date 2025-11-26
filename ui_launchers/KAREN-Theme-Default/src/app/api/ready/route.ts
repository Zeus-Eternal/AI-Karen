/**
 * Readiness Check API Endpoint
 *
 * Provides readiness status for the application, indicating whether
 * the application is ready to serve traffic and handle requests.
 */

import { NextRequest, NextResponse } from 'next/server';
import os from 'os';
import { performance } from 'perf_hooks';

import { EnvironmentConfigManager } from '@/lib/config/environment-config-manager';
import { safeWarn } from '@/lib/safe-console';

interface ReadinessCheckResult {
  status: 'ready' | 'not_ready';
  timestamp: string;
  checks: {
    application: ReadinessCheck;
    dependencies: ReadinessCheck;
    configuration: ReadinessCheck;
    resources: ReadinessCheck;
  };
  details: {
    startupTime: number;
    initializationComplete: boolean;
    criticalServicesReady: boolean;
    lastHealthyBackend: string | null;
  };
}

interface ReadinessCheck {
  status: 'ready' | 'not_ready';
  message: string;
  details?: Record<string, unknown>;
}

interface BackendHealthResult {
  url: string;
  status: 'healthy' | 'degraded' | 'unreachable';
  responseTime: number;
  statusCode?: number;
  message?: string;
  rawStatus?: string;
}

interface BackendHealthPayload {
  status?: string;
  summary?: string;
  message?: string;
}

interface GlobalReadinessState {
  startupStartTime: number;
  initializationComplete: boolean;
  lastDependencyCheck?: number;
  lastSuccessfulDependencyCheck?: number;
  lastDependencyStatus?: 'ready' | 'not_ready';
  lastHealthyBackend?: string;
  envManager?: EnvironmentConfigManager;
  eventLoopBaseline?: ReturnType<typeof performance.eventLoopUtilization>;
}

const globalScope = globalThis as typeof globalThis & {
  __kariReadinessState?: GlobalReadinessState;
};

function getReadinessState(): GlobalReadinessState {
  if (!globalScope.__kariReadinessState) {
    globalScope.__kariReadinessState = {
      startupStartTime: Date.now(),
      initializationComplete: false,
      eventLoopBaseline:
        typeof performance.eventLoopUtilization === 'function'
          ? performance.eventLoopUtilization()
          : undefined,
    };
  }
  return globalScope.__kariReadinessState;
}

function getEnvironmentManager(): EnvironmentConfigManager {
  const state = getReadinessState();
  if (!state.envManager) {
    state.envManager = new EnvironmentConfigManager();
  }
  return state.envManager;
}

function normalizeUrl(url: string): string {
  return url.replace(/\/+$/, '');
}

async function checkBackendHealth(url: string, timeoutMs: number): Promise<BackendHealthResult> {
  const healthUrl = `${normalizeUrl(url)}/api/health`;
  const controller = new AbortController();
  const startTime = Date.now();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(healthUrl, {
      method: 'GET',
      signal: controller.signal,
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });

    const responseTime = Date.now() - startTime;

    let parsed: BackendHealthPayload | null = null;
    try {
      const json = await response.json();
      if (typeof json === 'object' && json !== null) {
        parsed = json as BackendHealthPayload;
      }
    } catch (parseError) {
      safeWarn('Readiness check received non-JSON response from backend health endpoint', {
        url: healthUrl,
        statusCode: response.status,
        error: parseError instanceof Error ? parseError.message : String(parseError),
      });
    }

    if (!response.ok) {
      return {
        url,
        status: 'degraded',
        responseTime,
        statusCode: response.status,
        message: `HTTP ${response.status}`,
        rawStatus: parsed?.status,
      };
    }

    const backendStatus = parsed?.status ?? 'any';
    const isHealthy = backendStatus === 'healthy' || backendStatus === 'ready';

    return {
      url,
      status: isHealthy ? 'healthy' : 'degraded',
      responseTime,
      statusCode: response.status,
      message: parsed?.summary || parsed?.message,
      rawStatus: backendStatus,
    };
  } catch (error) {
    const responseTime = Date.now() - startTime;

    safeWarn('Backend health check failed', {
      url: healthUrl,
      error: error instanceof Error ? error.message : String(error),
    });

    return {
      url,
      status: 'unreachable',
      responseTime,
      message: error instanceof Error ? error.message : 'any error',
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

function getCriticalEnvVars(): string[] {
  const baseVars = ['NODE_ENV', 'KAREN_BACKEND_URL'];
  const optionalVars = ['NEXT_PUBLIC_KAREN_BACKEND_URL', 'KAREN_FALLBACK_BACKEND_URLS'];
  return [...baseVars, ...optionalVars];
}

/**
 * Check if application is ready
 */
function checkApplication(): ReadinessCheck {
  const readinessState = getReadinessState();
  const uptimeSeconds = process.uptime();
  const initializationComplete = readinessState.initializationComplete;

  const details = {
    startupDurationMs: Date.now() - readinessState.startupStartTime,
    uptimeSeconds: Number(uptimeSeconds.toFixed(2)),
    initializationComplete,
    lastDependencyCheckAt: readinessState.lastDependencyCheck ?? null,
    lastSuccessfulDependencyCheckAt: readinessState.lastSuccessfulDependencyCheck ?? null,
    lastHealthyBackend: readinessState.lastHealthyBackend ?? null,
  };

  if (!initializationComplete) {
    return {
      status: 'not_ready',
      message: 'Application initialization in progress',
      details,
    };
  }

  return {
    status: 'ready',
    message: 'Application runtime stable',
    details,
  };
}

/**
 * Check if dependencies are ready
 */
async function checkDependencies(): Promise<ReadinessCheck> {
  const readinessState = getReadinessState();
  const envManager = getEnvironmentManager();
  const validation = envManager.validateConfiguration();

  if (!validation.isValid) {
    readinessState.initializationComplete = false;
    return {
      status: 'not_ready',
      message: 'Backend configuration invalid',
      details: {
        errors: validation.errors,
        warnings: validation.warnings,
        environment: validation.environment,
      },
    };
  }

  const backendConfig = envManager.getBackendConfig();
  const candidateUrls = envManager.getAllCandidateUrls().map(normalizeUrl).filter(Boolean);

  if (candidateUrls.length === 0) {
    readinessState.initializationComplete = false;
    return {
      status: 'not_ready',
      message: 'No backend endpoints configured',
      details: { backendConfig },
    };
  }

  const timeoutConfig = envManager.getTimeoutConfig();
  const timeoutMs = Math.max(timeoutConfig.healthCheck, 3000);

  const dependencyChecks = await Promise.all(
    candidateUrls.map((url) => checkBackendHealth(url, timeoutMs)),
  );

  const healthy = dependencyChecks.filter((r) => r.status === 'healthy');
  const degraded = dependencyChecks.filter((r) => r.status === 'degraded');
  const unreachable = dependencyChecks.filter((r) => r.status === 'unreachable');

  readinessState.lastDependencyCheck = Date.now();

  if (healthy.length > 0) {
    readinessState.initializationComplete = true;
    readinessState.lastSuccessfulDependencyCheck = readinessState.lastDependencyCheck;
    readinessState.lastDependencyStatus = 'ready';
    readinessState.lastHealthyBackend = healthy[0]?.url;
  } else {
    readinessState.initializationComplete = false;
    readinessState.lastDependencyStatus = 'not_ready';
  }

  const status: 'ready' | 'not_ready' = healthy.length > 0 ? 'ready' : 'not_ready';

  return {
    status,
    message: status === 'ready' ? 'Backend services reachable' : 'Unable to reach required backend services',
    details: {
      attemptedEndpoints: candidateUrls.length,
      healthyEndpoints: healthy.map((r) => ({
        url: r.url,
        responseTimeMs: r.responseTime,
        statusCode: r.statusCode,
        backendStatus: r.rawStatus,
      })),
      degradedEndpoints: degraded.map((r) => ({
        url: r.url,
        responseTimeMs: r.responseTime,
        statusCode: r.statusCode,
        backendStatus: r.rawStatus,
        message: r.message,
      })),
      unreachableEndpoints: unreachable.map((r) => ({
        url: r.url,
        responseTimeMs: r.responseTime,
        message: r.message,
      })),
      backendConfig,
      warnings: validation.warnings,
      environment: validation.environment,
    },
  };
}

/**
 * Check if configuration is ready
 */
function checkConfiguration(): ReadinessCheck {
  try {
    const envManager = getEnvironmentManager();
    const validation = envManager.validateConfiguration();
    const criticalEnvVars = getCriticalEnvVars();

    const missingEnvVars = criticalEnvVars.filter((envVar) => !process.env[envVar]);

    if (missingEnvVars.length > 0) {
      return {
        status: 'not_ready',
        message: 'Missing critical configuration',
        details: {
          missingEnvVars,
          totalRequired: criticalEnvVars.length,
          warnings: validation.warnings,
        },
      };
    }

    if (!validation.isValid) {
      return {
        status: 'not_ready',
        message: 'Configuration validation failed',
        details: {
          errors: validation.errors,
          warnings: validation.warnings,
          environment: validation.environment,
        },
      };
    }

    const nodeEnv = process.env.NODE_ENV || 'production';
    const validEnvironments = ['production', 'staging', 'qa', 'development'];

    if (!validEnvironments.includes(nodeEnv)) {
      return {
        status: 'not_ready',
        message: 'Invalid NODE_ENV configuration',
        details: {
          currentEnv: nodeEnv,
          validEnvironments,
        },
      };
    }

    return {
      status: 'ready',
      message: 'Configuration valid',
      details: {
        environment: nodeEnv,
        configuredVars: criticalEnvVars.length,
        warningsCleared: validation.warnings.length === 0,
      },
    };
  } catch (error) {
    return {
      status: 'not_ready',
      message: `Configuration check failed: ${error instanceof Error ? error.message : 'any error'}`,
      details: { error: error instanceof Error ? error.message : 'any error' },
    };
  }
}

/**
 * Check if resources are ready
 */
function checkResources(): ReadinessCheck {
  try {
    const memUsage = process.memoryUsage();
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const memoryPressure = ((totalMemory - freeMemory) / totalMemory) * 100;
    const [load1, load5, load15] = os.loadavg();
    const cpuCount = os.cpus()?.length ?? 1;
    const normalizedLoad5 = cpuCount > 0 ? load5 / cpuCount : load5;

    let eventLoopUtilization = 0;
    if (typeof performance.eventLoopUtilization === 'function') {
      const state = getReadinessState();
      const stats = performance.eventLoopUtilization(state.eventLoopBaseline);
      eventLoopUtilization = Number(stats.utilization?.toFixed(3) ?? 0);
      state.eventLoopBaseline = stats;
    }

    if (eventLoopUtilization > 0.95) {
      return {
        status: 'not_ready',
        message: 'Event loop utilization critically high',
        details: {
          eventLoopUtilization,
          loadAverage: { load1, load5, load15 },
        },
      };
    }

    if (heapUsagePercent > 95 || memoryPressure > 95 || normalizedLoad5 > 1.5) {
      return {
        status: 'not_ready',
        message: 'Insufficient system resources',
        details: {
          heapUsagePercent: `${heapUsagePercent.toFixed(2)}%`,
          heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
          heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB`,
          memoryPressurePercent: `${memoryPressure.toFixed(2)}%`,
          cpuLoad: {
            load1: Number(load1.toFixed(2)),
            load5: Number(load5.toFixed(2)),
            load15: Number(load15.toFixed(2)),
            cpuCount,
            normalizedLoad5: Number(normalizedLoad5.toFixed(2)),
          },
          eventLoopUtilization,
        },
      };
    }

    const uptime = process.uptime();
    if (uptime < 2) {
      return {
        status: 'not_ready',
        message: 'Application just started',
        details: {
          uptime: `${uptime.toFixed(2)}s`,
          minimumUptime: '2s',
          eventLoopUtilization,
        },
      };
    }

    return {
      status: 'ready',
      message: 'Resources available',
      details: {
        heapUsagePercent: `${heapUsagePercent.toFixed(2)}%`,
        uptime: `${uptime.toFixed(2)}s`,
        memoryStatus: 'sufficient',
        memoryPressurePercent: `${memoryPressure.toFixed(2)}%`,
        cpuLoad: {
          load1: Number(load1.toFixed(2)),
          load5: Number(load5.toFixed(2)),
          load15: Number(load15.toFixed(2)),
          cpuCount,
          normalizedLoad5: Number(normalizedLoad5.toFixed(2)),
        },
        eventLoopUtilization,
      },
    };
  } catch (error) {
    return {
      status: 'not_ready',
      message: `Resource check failed: ${error instanceof Error ? error.message : 'any error'}`,
      details: { error: error instanceof Error ? error.message : 'any error' },
    };
  }
}

/**
 * Main readiness check handler
 */
export async function GET(_request: NextRequest): Promise<NextResponse> {
  try {
    // Check if this is a build-time request
    const isBuildTime = process.env.NEXT_PHASE === 'phase-production-build';
    
    // During build time, return a mock response to avoid dynamic server usage
    if (isBuildTime) {
      return NextResponse.json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        checks: {
          application: { status: 'ready', message: 'Build-time check' },
          dependencies: { status: 'ready', message: 'Build-time check' },
          configuration: { status: 'ready', message: 'Build-time check' },
          resources: { status: 'ready', message: 'Build-time check' },
        },
        details: {
          startupTime: 0,
          initializationComplete: true,
          criticalServicesReady: true,
          lastHealthyBackend: null,
        },
      }, {
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      });
    }

    const [applicationCheck, dependenciesCheck, configurationCheck, resourcesCheck] =
      await Promise.all([
        Promise.resolve(checkApplication()),
        checkDependencies(),
        Promise.resolve(checkConfiguration()),
        Promise.resolve(checkResources()),
      ]);

    const checks = {
      application: applicationCheck,
      dependencies: dependenciesCheck,
      configuration: configurationCheck,
      resources: resourcesCheck,
    };

    const notReadyChecks = Object.values(checks).filter((c) => c.status === 'not_ready');
    const overallStatus: 'ready' | 'not_ready' = notReadyChecks.length === 0 ? 'ready' : 'not_ready';

    const readinessState = getReadinessState();

    const readinessResult: ReadinessCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      checks,
      details: {
        startupTime: Date.now() - readinessState.startupStartTime,
        initializationComplete: readinessState.initializationComplete,
        criticalServicesReady: dependenciesCheck.status === 'ready',
        lastHealthyBackend: readinessState.lastHealthyBackend ?? null,
      },
    };

    const httpStatus = overallStatus === 'ready' ? 200 : 503;

    return NextResponse.json(readinessResult, {
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    safeWarn('Readiness endpoint failed', {
      error: error instanceof Error ? error.message : 'any error',
    });

    const readinessState = getReadinessState();

    const errorResult: ReadinessCheckResult = {
      status: 'not_ready',
      timestamp: new Date().toISOString(),
      checks: {
        application: { status: 'not_ready', message: 'Readiness check failed' },
        dependencies: { status: 'not_ready', message: 'Unable to check dependencies' },
        configuration: { status: 'not_ready', message: 'Unable to check configuration' },
        resources: { status: 'not_ready', message: 'Unable to check resources' },
      },
      details: {
        startupTime: Date.now() - readinessState.startupStartTime,
        initializationComplete: readinessState.initializationComplete,
        criticalServicesReady: false,
        lastHealthyBackend: readinessState.lastHealthyBackend ?? null,
      },
    };

    return NextResponse.json(errorResult, {
      status: 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  }
}
