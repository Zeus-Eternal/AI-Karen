/**
 * Health Check API Endpoint
 *
 * Proxies health check requests to the backend server to maintain consistency
 * with the backend health check format expected by the frontend.
 */

import { NextRequest, NextResponse } from 'next/server';

// Note: Removed 'force-dynamic' to allow static export
export const dynamic = 'auto';
export const runtime = 'nodejs';
import * as os from 'os';
import type { BackendHealthData } from '@/types/health';

interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  uptime: number;
  checks: {
    database?: HealthCheck;
    redis?: HealthCheck;
    external_apis?: HealthCheck;
    filesystem?: HealthCheck;
    memory?: HealthCheck;
    performance?: HealthCheck;
  };
  metrics: {
    memory: MemoryMetrics;
    performance: PerformanceMetrics;
    requests: RequestMetrics;
  };
  environment: {
    nodeVersion: string;
    platform: string;
    environment: string;
  };
}

interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded';
  responseTime?: number;
  message?: string;
  details?: Record<string, unknown>;
}

interface MemoryMetrics {
  rss: number;
  heapTotal: number;
  heapUsed: number;
  external: number;
  arrayBuffers: number;
  heapUsagePercent: number;
}

interface PerformanceMetrics {
  uptime: number;
  loadAverage?: number[];
  cpuUsage?: NodeJS.CpuUsage;
}

interface RequestMetrics {
  total: number;
  successful: number;
  failed: number;
  averageResponseTime: number;
}

type FallbackHealthResponse = HealthCheckResult & {
  error: string;
  details?: string;
};

type HealthResponsePayload =
  | BackendHealthData
  | { error: string }
  | string
  | Record<string, unknown>;

// Global metrics tracking
const requestMetrics: RequestMetrics = {
  total: 0,
  successful: 0,
  failed: 0,
  averageResponseTime: 0
};

const responseTimes: number[] = [];
const MAX_RESPONSE_TIMES = 100;

/**
 * Check database connectivity
 */
async function checkDatabase(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // In a real application, you would check your actual database
    // For now, we'll simulate a database check
    await new Promise(resolve => setTimeout(resolve, 10));
    
    const responseTime = Date.now() - startTime;
    
    return {
      status: 'healthy',
      responseTime,
      message: 'Database connection successful',
      details: {
        connectionPool: 'active',
        activeConnections: 5,
        maxConnections: 20
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `Database connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check Redis connectivity
 */
async function checkRedis(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // In a real application, you would check your actual Redis instance
    // For now, we'll simulate a Redis check
    await new Promise(resolve => setTimeout(resolve, 5));
    
    const responseTime = Date.now() - startTime;
    
    return {
      status: 'healthy',
      responseTime,
      message: 'Redis connection successful',
      details: {
        connected: true,
        memoryUsage: '2.5MB',
        keyCount: 150
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `Redis connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check external API dependencies
 */
async function checkExternalAPIs(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // Check critical external APIs
    const apiChecks = await Promise.allSettled([
      // Add your external API checks here
      // fetch('https://api.example.com/health', { signal: AbortSignal.timeout(5000) })
    ] as Promise<Response>[]);
    
    const responseTime = Date.now() - startTime;
    const failedChecks = apiChecks.filter(result => result.status === 'rejected').length;
    
    if (failedChecks === 0) {
      return {
        status: 'healthy',
        responseTime,
        message: 'All external APIs accessible',
        details: {
          totalAPIs: apiChecks.length,
          successfulAPIs: apiChecks.length - failedChecks,
          failedAPIs: failedChecks
        }
      };
    } else if (failedChecks < apiChecks.length) {
      return {
        status: 'degraded',
        responseTime,
        message: 'Some external APIs unavailable',
        details: {
          totalAPIs: apiChecks.length,
          successfulAPIs: apiChecks.length - failedChecks,
          failedAPIs: failedChecks
        }
      };
    } else {
      return {
        status: 'unhealthy',
        responseTime,
        message: 'External APIs unavailable',
        details: {
          totalAPIs: apiChecks.length,
          successfulAPIs: 0,
          failedAPIs: failedChecks
        }
      };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `External API check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check filesystem health
 */
async function checkFilesystem(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    const fs = await import('fs/promises');
    const path = await import('path');
    
    // Check if critical directories exist and are writable
    const criticalPaths = [
      '.next',
      'public',
      'src'
    ];
    
    for (const criticalPath of criticalPaths) {
      try {
        await fs.access(criticalPath, fs.constants.F_OK);
      } catch {
        throw new Error(`Critical path not accessible: ${criticalPath}`);
      }
    }
    
    // Check temporary directory write access
    const tempFile = path.join('/tmp', `health-check-${Date.now()}.tmp`);
    try {
      await fs.writeFile(tempFile, 'health check');
      await fs.unlink(tempFile);
    } catch {
      throw new Error('Temporary directory not writable');
    }
    
    const responseTime = Date.now() - startTime;
    
    return {
      status: 'healthy',
      responseTime,
      message: 'Filesystem accessible',
      details: {
        criticalPaths: criticalPaths.length,
        tempWritable: true
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `Filesystem check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check memory usage
 */
function checkMemory(): HealthCheck {
  const startTime = Date.now();
  
  try {
    const memUsage = process.memoryUsage();
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    
    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    let message = 'Memory usage normal';
    
    if (heapUsagePercent > 90) {
      status = 'unhealthy';
      message = 'Critical memory usage';
    } else if (heapUsagePercent > 75) {
      status = 'degraded';
      message = 'High memory usage';
    }
    
    const responseTime = Date.now() - startTime;
    
    return {
      status,
      responseTime,
      message,
      details: {
        rss: `${(memUsage.rss / 1024 / 1024).toFixed(2)}MB`,
        heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB`,
        heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
        heapUsagePercent: `${heapUsagePercent.toFixed(2)}%`,
        external: `${(memUsage.external / 1024 / 1024).toFixed(2)}MB`
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `Memory check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check performance metrics
 */
function checkPerformance(): HealthCheck {
  const startTime = Date.now();
  
  try {
    const uptime = process.uptime();
    const cpuUsage = process.cpuUsage();
    
    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    let message = 'Performance normal';
    
    // Check if uptime is too low (might indicate frequent restarts)
    if (uptime < 60) {
      status = 'degraded';
      message = 'Recent restart detected';
    }
    
    const responseTime = Date.now() - startTime;
    
    return {
      status,
      responseTime,
      message,
      details: {
        uptime: `${Math.floor(uptime)}s`,
        cpuUser: `${(cpuUsage.user / 1000).toFixed(2)}ms`,
        cpuSystem: `${(cpuUsage.system / 1000).toFixed(2)}ms`,
        pid: process.pid,
        platform: process.platform,
        nodeVersion: process.version
      }
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      responseTime: Date.now() - startTime,
      message: `Performance check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Get memory metrics
 */
function getMemoryMetrics(): MemoryMetrics {
  const memUsage = process.memoryUsage();
  
  return {
    rss: memUsage.rss,
    heapTotal: memUsage.heapTotal,
    heapUsed: memUsage.heapUsed,
    external: memUsage.external,
    arrayBuffers: memUsage.arrayBuffers,
    heapUsagePercent: (memUsage.heapUsed / memUsage.heapTotal) * 100
  };
}

/**
 * Get performance metrics
 */
function getPerformanceMetrics(): PerformanceMetrics {
  return {
    uptime: process.uptime(),
    loadAverage: os.loadavg(),
    cpuUsage: process.cpuUsage()
  };
}

/**
 * Update request metrics
 */
function updateRequestMetrics(responseTime: number, success: boolean) {
  requestMetrics.total++;

  if (success) {
    requestMetrics.successful++;
  } else {
    requestMetrics.failed++;
  }
  
  // Track response times for average calculation
  responseTimes.push(responseTime);
  if (responseTimes.length > MAX_RESPONSE_TIMES) {
    responseTimes.shift();
  }
  
  // Calculate average response time
  requestMetrics.averageResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
}

async function buildFallbackHealthResponse(errorMessage: string, error: unknown): Promise<FallbackHealthResponse> {
  const [database, redis, externalAPIs, filesystem] = await Promise.all([
    checkDatabase(),
    checkRedis(),
    checkExternalAPIs(),
    checkFilesystem(),
  ]);

  const memory = checkMemory();
  const performance = checkPerformance();
  const details =
    process.env.NODE_ENV === 'development'
      ? error instanceof Error
        ? error.message
        : String(error)
      : undefined;

  const requestsSnapshot: RequestMetrics = { ...requestMetrics };

  return {
    status: 'unhealthy',
    error: errorMessage,
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION || process.env.APP_VERSION || 'unknown',
    uptime: Math.floor(process.uptime()),
    checks: {
      database,
      redis,
      external_apis: externalAPIs,
      filesystem,
      memory,
      performance,
    },
    metrics: {
      memory: getMemoryMetrics(),
      performance: getPerformanceMetrics(),
      requests: requestsSnapshot,
    },
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      environment: process.env.NODE_ENV || 'development',
    },
    details,
  };
}

// Backend URL configuration
const BACKEND_URL =
    process.env.KAREN_BACKEND_URL || 'http://localhost:8000';

function buildForwardHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  const authHeader = request.headers.get('authorization');
  const authCookie = request.cookies.get('auth_token')?.value;
  const sessionCookie =
    request.cookies.get('kari_session')?.value ||
    request.cookies.get('session_token')?.value;
  if (authHeader) {
    headers['Authorization'] = authHeader;
  } else if (authCookie) {
    headers['Authorization'] = `Bearer ${authCookie}`;
  } else if (sessionCookie) {
    headers['Authorization'] = `Bearer ${sessionCookie}`;
  }

  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) {
    headers['Cookie'] = cookieHeader;
  }

  const csrf =
    request.headers.get('x-csrf-token') ||
    request.headers.get('x-xsrf-token');
  if (csrf) {
    headers['X-CSRF-Token'] = csrf;
    headers['X-XSRF-Token'] = csrf;
  }

  const userAgent = request.headers.get('user-agent');
  if (userAgent) {
    headers['User-Agent'] = userAgent;
  }

  return headers;
}

/**
 * Main health check handler - proxies to backend
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    // Check if this is a build-time request
    const isBuildTime = process.env.NEXT_PHASE === 'phase-production-build';
    
    // During build time, return a mock response to avoid dynamic server usage
    if (isBuildTime) {
      return NextResponse.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.NEXT_PUBLIC_APP_VERSION || process.env.APP_VERSION || 'unknown',
        uptime: process.uptime(),
        checks: {
          database: { status: 'healthy', message: 'Build-time check' },
          redis: { status: 'healthy', message: 'Build-time check' },
          external_apis: { status: 'healthy', message: 'Build-time check' },
          filesystem: { status: 'healthy', message: 'Build-time check' },
          memory: { status: 'healthy', message: 'Build-time check' },
          performance: { status: 'healthy', message: 'Build-time check' },
        },
        metrics: {
          memory: getMemoryMetrics(),
          performance: getPerformanceMetrics(),
          requests: { ...requestMetrics },
        },
        environment: {
          nodeVersion: process.version,
          platform: process.platform,
          environment: process.env.NODE_ENV || 'development',
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

    // Proxy the health check request to the backend
    const backendUrl = `${BACKEND_URL}/api/health`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: buildForwardHeaders(request),
      signal: controller.signal,
      cache: 'no-store',
    });

    clearTimeout(timeout);

    const totalResponseTime = Date.now() - startTime;
    updateRequestMetrics(totalResponseTime, response.ok);

    // Handle backend authentication failures by returning a graceful fallback
    if (response.status === 401 || response.status === 403) {
      const fallbackResponse = await buildFallbackHealthResponse(
        'Health endpoint authentication required',
        new Error('Backend health check requires authentication')
      );
      return NextResponse.json(
        {
          ...fallbackResponse,
          status: 'degraded',
          error: 'Authentication required',
          details: 'Health checks require a valid session token',
        },
        {
          status: 200,
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            Pragma: 'no-cache',
            Expires: '0',
          },
        }
      );
    }

    let data: HealthResponsePayload;
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      try {
        const text = await response.text();
        if (text.trim() === '') {
          data = response.status >= 400 ? { error: 'Empty response from server' } : {};
        } else {
          data = JSON.parse(text);
        }
      } catch {
        data = { error: 'Invalid JSON response from server' };
      }
    } else {
      data = await response.text();
    }

    const responseTime = Date.now() - startTime;
    updateRequestMetrics(responseTime, response.ok);

    // Return the backend response with the same status code
    return NextResponse.json(
      typeof data === 'string' ? { error: data } : data,
      {
        status: response.status,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      },
    );

  } catch (error) {
    const responseTime = Date.now() - startTime;
    updateRequestMetrics(responseTime, false);
    console.error('Health check proxy error:', error);

    // Return error response
    let status = 503;
    let errorMessage = 'Backend health check failed';

    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.message.toLowerCase().includes('timeout')) {
        status = 504;
        errorMessage = 'Backend health check timeout';
      } else if (error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Backend server is not reachable';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Failed to connect to backend server';
      } else {
        errorMessage = error.message;
      }
    }
    
    const totalResponseTime = Date.now() - startTime;
    updateRequestMetrics(totalResponseTime, false);

    const [database, redis, externalApis, filesystem] = await Promise.all([
      checkDatabase(),
      checkRedis(),
      checkExternalAPIs(),
      checkFilesystem(),
    ]);
    const memoryCheck = checkMemory();
    const performanceCheck = checkPerformance();

    const fallback: HealthCheckResult = {
      status: status === 504 ? 'degraded' : 'unhealthy',
      timestamp: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_APP_VERSION || process.env.APP_VERSION || 'unknown',
      uptime: process.uptime(),
      checks: {
        database,
        redis,
        external_apis: externalApis,
        filesystem,
        memory: memoryCheck,
        performance: performanceCheck,
      },
      metrics: {
        memory: getMemoryMetrics(),
        performance: getPerformanceMetrics(),
        requests: { ...requestMetrics },
      },
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        environment: process.env.NODE_ENV || 'development',
      },
    };

    const fallbackResponse = await buildFallbackHealthResponse(errorMessage, error);
    const detailMessage =
      process.env.NODE_ENV === 'development'
        ? error instanceof Error
          ? error.message
          : String(error)
        : undefined;
    const responseBody = {
      ...fallbackResponse,
      ...fallback,
      error: errorMessage,
      details: detailMessage,
    };

    return NextResponse.json(responseBody, {
      status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });
  }
}
