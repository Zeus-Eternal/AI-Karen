/**
 * Readiness Check API Endpoint
 * 
 * Provides readiness status for the application, indicating whether
 * the application is ready to serve traffic and handle requests.
 */

import { NextRequest, NextResponse } from 'next/server';

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
  };
}

interface ReadinessCheck {
  status: 'ready' | 'not_ready';
  message: string;
  details?: Record<string, any>;
}

// Track application startup state
let applicationStartupComplete = false;
let startupStartTime = Date.now();

// Simulate application initialization
setTimeout(() => {
  applicationStartupComplete = true;
}, 5000); // 5 second startup simulation

/**
 * Check if application is ready
 */
function checkApplication(): ReadinessCheck {
  if (!applicationStartupComplete) {
    return {
      status: 'not_ready',
      message: 'Application still initializing',
      details: {
        startupTime: Date.now() - startupStartTime,
        phase: 'initialization'
      }
    };
  }

  return {
    status: 'ready',
    message: 'Application ready to serve requests',
    details: {
      startupTime: Date.now() - startupStartTime,
      phase: 'ready'
    }
  };
}

/**
 * Check if dependencies are ready
 */
async function checkDependencies(): Promise<ReadinessCheck> {
  try {
    // Check critical dependencies
    const dependencyChecks = await Promise.allSettled([
      // Database readiness
      new Promise((resolve) => {
        // Simulate database readiness check
        setTimeout(() => resolve('database ready'), 100);
      }),
      
      // Cache readiness
      new Promise((resolve) => {
        // Simulate cache readiness check
        setTimeout(() => resolve('cache ready'), 50);
      }),
      
      // External service readiness
      new Promise((resolve) => {
        // Simulate external service readiness check
        setTimeout(() => resolve('external services ready'), 75);
      })
    ]);

    const failedDependencies = dependencyChecks.filter(result => result.status === 'rejected');

    if (failedDependencies.length === 0) {
      return {
        status: 'ready',
        message: 'All dependencies ready',
        details: {
          totalDependencies: dependencyChecks.length,
          readyDependencies: dependencyChecks.length,
          failedDependencies: 0
        }
      };
    } else {
      return {
        status: 'not_ready',
        message: 'Some dependencies not ready',
        details: {
          totalDependencies: dependencyChecks.length,
          readyDependencies: dependencyChecks.length - failedDependencies.length,
          failedDependencies: failedDependencies.length
        }
      };
    }
  } catch (error) {
    return {
      status: 'not_ready',
      message: `Dependency check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Check if configuration is ready
 */
function checkConfiguration(): ReadinessCheck {
  try {
    // Check critical environment variables
    const criticalEnvVars = [
      'NODE_ENV',
      // Add other critical environment variables here
    ];

    const missingEnvVars = criticalEnvVars.filter(envVar => !process.env[envVar]);

    if (missingEnvVars.length > 0) {
      return {
        status: 'not_ready',
        message: 'Missing critical configuration',
        details: {
          missingEnvVars,
          totalRequired: criticalEnvVars.length
        }
      };
    }

    // Check configuration validity
    const nodeEnv = process.env.NODE_ENV;
    const validEnvironments = ['development', 'production', 'test'];

    if (!validEnvironments.includes(nodeEnv || '')) {
      return {
        status: 'not_ready',
        message: 'Invalid NODE_ENV configuration',
        details: {
          currentEnv: nodeEnv,
          validEnvironments
        }
      };
    }

    return {
      status: 'ready',
      message: 'Configuration valid',
      details: {
        environment: nodeEnv,
        configuredVars: criticalEnvVars.length
      }
    };
  } catch (error) {
    return {
      status: 'not_ready',
      message: `Configuration check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
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

    // Check if memory usage is too high for readiness
    if (heapUsagePercent > 95) {
      return {
        status: 'not_ready',
        message: 'Insufficient memory resources',
        details: {
          heapUsagePercent: `${heapUsagePercent.toFixed(2)}%`,
          heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
          heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB`
        }
      };
    }

    // Check uptime (application should be running for at least a few seconds)
    const uptime = process.uptime();
    if (uptime < 2) {
      return {
        status: 'not_ready',
        message: 'Application just started',
        details: {
          uptime: `${uptime.toFixed(2)}s`,
          minimumUptime: '2s'
        }
      };
    }

    return {
      status: 'ready',
      message: 'Resources available',
      details: {
        heapUsagePercent: `${heapUsagePercent.toFixed(2)}%`,
        uptime: `${uptime.toFixed(2)}s`,
        memoryStatus: 'sufficient'
      }
    };
  } catch (error) {
    return {
      status: 'not_ready',
      message: `Resource check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

/**
 * Main readiness check handler
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    // Perform all readiness checks
    const [
      applicationCheck,
      dependenciesCheck,
      configurationCheck,
      resourcesCheck
    ] = await Promise.all([
      Promise.resolve(checkApplication()),
      checkDependencies(),
      Promise.resolve(checkConfiguration()),
      Promise.resolve(checkResources())
    ]);

    const checks = {
      application: applicationCheck,
      dependencies: dependenciesCheck,
      configuration: configurationCheck,
      resources: resourcesCheck
    };

    // Determine overall readiness status
    const notReadyChecks = Object.values(checks).filter(check => check.status === 'not_ready');
    const overallStatus = notReadyChecks.length === 0 ? 'ready' : 'not_ready';

    const readinessResult: ReadinessCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      checks,
      details: {
        startupTime: Date.now() - startupStartTime,
        initializationComplete: applicationStartupComplete,
        criticalServicesReady: dependenciesCheck.status === 'ready'
      }
    };

    // Return appropriate HTTP status code
    const httpStatus = overallStatus === 'ready' ? 200 : 503;

    return NextResponse.json(readinessResult, {
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    const errorResult: ReadinessCheckResult = {
      status: 'not_ready',
      timestamp: new Date().toISOString(),
      checks: {
        application: {
          status: 'not_ready',
          message: 'Readiness check failed'
        },
        dependencies: {
          status: 'not_ready',
          message: 'Unable to check dependencies'
        },
        configuration: {
          status: 'not_ready',
          message: 'Unable to check configuration'
        },
        resources: {
          status: 'not_ready',
          message: 'Unable to check resources'
        }
      },
      details: {
        startupTime: Date.now() - startupStartTime,
        initializationComplete: false,
        criticalServicesReady: false
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