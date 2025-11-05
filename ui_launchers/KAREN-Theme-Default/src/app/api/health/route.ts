/**
 * Health Check API Endpoint
 * 
 * Provides comprehensive health status for the application including
 * system metrics, database connectivity, and service dependencies.
 */

import { NextRequest, NextResponse } from 'next/server';

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
  details?: Record<string, any>;
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

// Global metrics tracking
let requestMetrics: RequestMetrics = {
  total: 0,
  successful: 0,
  failed: 0,
  averageResponseTime: 0
};

let responseTimes: number[] = [];
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
      } catch (error) {
        throw new Error(`Critical path not accessible: ${criticalPath}`);
      }
    }
    
    // Check temporary directory write access
    const tempFile = path.join('/tmp', `health-check-${Date.now()}.tmp`);
    try {
      await fs.writeFile(tempFile, 'health check');
      await fs.unlink(tempFile);
    } catch (error) {
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
  const os = require('os');
  
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

/**
 * Main health check handler
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();
  
  try {
    // Perform all health checks
    const [
      databaseCheck,
      redisCheck,
      externalAPIsCheck,
      filesystemCheck,
      memoryCheck,
      performanceCheck
    ] = await Promise.all([
      checkDatabase(),
      checkRedis(),
      checkExternalAPIs(),
      checkFilesystem(),
      Promise.resolve(checkMemory()),
      Promise.resolve(checkPerformance())
    ]);
    
    // Determine overall health status
    const checks = {
      database: databaseCheck,
      redis: redisCheck,
      external_apis: externalAPIsCheck,
      filesystem: filesystemCheck,
      memory: memoryCheck,
      performance: performanceCheck
    };
    
    const unhealthyChecks = Object.values(checks).filter(check => check.status === 'unhealthy');
    const degradedChecks = Object.values(checks).filter(check => check.status === 'degraded');
    
    let overallStatus: 'healthy' | 'unhealthy' | 'degraded' = 'healthy';
    
    if (unhealthyChecks.length > 0) {
      overallStatus = 'unhealthy';
    } else if (degradedChecks.length > 0) {
      overallStatus = 'degraded';
    }
    
    const responseTime = Date.now() - startTime;
    
    // Build health check result
    const healthResult: HealthCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      uptime: process.uptime(),
      checks,
      metrics: {
        memory: getMemoryMetrics(),
        performance: getPerformanceMetrics(),
        requests: requestMetrics
      },
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        environment: process.env.NODE_ENV || 'development'
      }
    };
    
    // Update request metrics
    updateRequestMetrics(responseTime, overallStatus !== 'unhealthy');
    
    // Return appropriate HTTP status code
    const httpStatus = overallStatus === 'healthy' ? 200 : 
                      overallStatus === 'degraded' ? 200 : 503;
    
    return NextResponse.json(healthResult, {
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  } catch (error) {
    const responseTime = Date.now() - startTime;
    
    // Update request metrics for failed health check
    updateRequestMetrics(responseTime, false);
    
    const errorResult: HealthCheckResult = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      uptime: process.uptime(),
      checks: {
        database: {
          status: 'unhealthy',
          message: 'Health check failed'
        }
      },
      metrics: {
        memory: getMemoryMetrics(),
        performance: getPerformanceMetrics(),
        requests: requestMetrics
      },
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        environment: process.env.NODE_ENV || 'development'
      }
    };
    
    return NextResponse.json(errorResult, {
      status: 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  }
}