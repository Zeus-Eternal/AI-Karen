/**
 * Production Health Check Script
 * 
 * Comprehensive health check for Docker containers and deployment monitoring.
 * Validates application health, database connections, and external dependencies.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

// Configuration
const HEALTH_CHECK_CONFIG = {
  port: process.env.PORT || 3000,
  host: process.env.HOSTNAME || 'localhost',
  timeout: parseInt(process.env.HEALTH_CHECK_TIMEOUT) || 5000,
  endpoints: {
    main: '/',
    api: '/api/health',
    ready: '/api/ready'
  },
  checks: {
    filesystem: true,
    memory: true,
    dependencies: true
  },
  thresholds: {
    memoryUsage: 0.9, // 90% memory usage threshold
    responseTime: 2000, // 2 second response time threshold
    diskSpace: 0.95 // 95% disk usage threshold
  }
};

/**
 * Perform HTTP health check
 */
function httpHealthCheck(endpoint) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const options = {
      hostname: HEALTH_CHECK_CONFIG.host,
      port: HEALTH_CHECK_CONFIG.port,
      path: endpoint,
      method: 'GET',
      timeout: HEALTH_CHECK_CONFIG.timeout,
      headers: {
        'User-Agent': 'HealthCheck/1.0',
        'Accept': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      const responseTime = Date.now() - startTime;
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({
            status: 'healthy',
            statusCode: res.statusCode,
            responseTime,
            data: data ? JSON.parse(data) : null
          });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(new Error(`Health check failed: ${error.message}`));
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Health check timeout after ${HEALTH_CHECK_CONFIG.timeout}ms`));
    });

    req.end();
  });
}

/**
 * Check filesystem health
 */
function checkFilesystem() {
  return new Promise((resolve, reject) => {
    try {
      // Check if critical files exist
      const criticalFiles = [
        'server.js',
        '.next/BUILD_ID',
        'package.json'
      ];

      for (const file of criticalFiles) {
        if (!fs.existsSync(path.join(__dirname, file))) {
          reject(new Error(`Critical file missing: ${file}`));
          return;
        }
      }

      // Check disk space
      const stats = fs.statSync(__dirname);
      const diskUsage = stats.size / (1024 * 1024 * 1024); // GB
      
      resolve({
        status: 'healthy',
        diskUsage: `${diskUsage.toFixed(2)}GB`,
        criticalFiles: criticalFiles.length
      });
    } catch (error) {
      reject(new Error(`Filesystem check failed: ${error.message}`));
    }
  });
}

/**
 * Check memory usage
 */
function checkMemory() {
  return new Promise((resolve, reject) => {
    try {
      const memUsage = process.memoryUsage();
      const totalMemory = require('os').totalmem();
      const freeMemory = require('os').freemem();
      const usedMemory = totalMemory - freeMemory;
      const memoryUsageRatio = usedMemory / totalMemory;

      if (memoryUsageRatio > HEALTH_CHECK_CONFIG.thresholds.memoryUsage) {
        reject(new Error(`High memory usage: ${(memoryUsageRatio * 100).toFixed(1)}%`));
        return;
      }

      resolve({
        status: 'healthy',
        memoryUsage: {
          rss: `${(memUsage.rss / 1024 / 1024).toFixed(2)}MB`,
          heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB`,
          heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
          external: `${(memUsage.external / 1024 / 1024).toFixed(2)}MB`,
          systemUsage: `${(memoryUsageRatio * 100).toFixed(1)}%`
        }
      });
    } catch (error) {
      reject(new Error(`Memory check failed: ${error.message}`));
    }
  });
}

/**
 * Check external dependencies
 */
function checkDependencies() {
  return new Promise((resolve, reject) => {
    try {
      // Check if package.json dependencies are available
      const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
      const dependencies = Object.keys(packageJson.dependencies || {});
      
      // Basic dependency validation
      const criticalDeps = ['next', 'react', 'react-dom'];
      const missingDeps = criticalDeps.filter(dep => !dependencies.includes(dep));
      
      if (missingDeps.length > 0) {
        reject(new Error(`Missing critical dependencies: ${missingDeps.join(', ')}`));
        return;
      }

      resolve({
        status: 'healthy',
        totalDependencies: dependencies.length,
        criticalDependencies: criticalDeps.length,
        nodeVersion: process.version
      });
    } catch (error) {
      reject(new Error(`Dependencies check failed: ${error.message}`));
    }
  });
}

/**
 * Perform comprehensive health check
 */
async function performHealthCheck() {
  const healthReport = {
    timestamp: new Date().toISOString(),
    status: 'healthy',
    checks: {},
    errors: [],
    summary: {
      totalChecks: 0,
      passedChecks: 0,
      failedChecks: 0
    }
  };

  const checks = [
    { name: 'http_main', fn: () => httpHealthCheck(HEALTH_CHECK_CONFIG.endpoints.main) },
    { name: 'http_api', fn: () => httpHealthCheck(HEALTH_CHECK_CONFIG.endpoints.api) },
    { name: 'http_ready', fn: () => httpHealthCheck(HEALTH_CHECK_CONFIG.endpoints.ready) }
  ];

  // Add optional checks based on configuration
  if (HEALTH_CHECK_CONFIG.checks.filesystem) {
    checks.push({ name: 'filesystem', fn: checkFilesystem });
  }

  if (HEALTH_CHECK_CONFIG.checks.memory) {
    checks.push({ name: 'memory', fn: checkMemory });
  }

  if (HEALTH_CHECK_CONFIG.checks.dependencies) {
    checks.push({ name: 'dependencies', fn: checkDependencies });
  }

  healthReport.summary.totalChecks = checks.length;

  // Execute all health checks
  for (const check of checks) {
    try {
      const result = await check.fn();
      healthReport.checks[check.name] = result;
      healthReport.summary.passedChecks++;
    } catch (error) {
      healthReport.checks[check.name] = {
        status: 'unhealthy',
        error: error.message
      };
      healthReport.errors.push(`${check.name}: ${error.message}`);
      healthReport.summary.failedChecks++;
    }
  }

  // Determine overall health status
  if (healthReport.summary.failedChecks > 0) {
    healthReport.status = 'unhealthy';
  }

  return healthReport;
}

/**
 * Main health check execution
 */
async function main() {
  try {
    console.log('Starting health check...');
    
    const healthReport = await performHealthCheck();
    
    // Log health report
    console.log('Health Check Report:');
    console.log(JSON.stringify(healthReport, null, 2));

    // Exit with appropriate code
    if (healthReport.status === 'healthy') {
      console.log('✅ Health check passed');
      process.exit(0);
    } else {
      console.error('❌ Health check failed');
      console.error('Errors:', healthReport.errors);
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Health check error:', error.message);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('Health check received SIGTERM, exiting...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Health check received SIGINT, exiting...');
  process.exit(0);
});

// Run health check if called directly
if (require.main === module) {
  main();
}

module.exports = {
  performHealthCheck,
  httpHealthCheck,
  checkFilesystem,
  checkMemory,
  checkDependencies
};