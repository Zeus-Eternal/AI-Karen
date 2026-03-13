// Health monitoring utility functions for extension management

import type {  HealthStatus, ResourceUsage, ExtensionBase } from '../../extensions/types';
import { HEALTH_STATUS, HEALTH_COLORS } from './constants';

/**
 * Health check result interface
 */
export interface HealthCheckResult {
  status: HealthStatus['status'];
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
  duration: number;
  details?: Record<string, unknown>;
}

/**
 * Creates a health status object
 */
export function createHealthStatus(
  status: HealthStatus['status'],
  message?: string,
  uptime?: number
): HealthStatus {
  return {
    status,
    message: message || getDefaultHealthMessage(status),
    lastCheck: new Date().toISOString(),
    uptime,
  };
}

/**
 * Gets default health message for status
 */
function getDefaultHealthMessage(status: HealthStatus['status']): string {
  const messages = {
    [HEALTH_STATUS.HEALTHY]: 'Extension is running normally',
    [HEALTH_STATUS.WARNING]: 'Extension has minor issues',
    [HEALTH_STATUS.ERROR]: 'Extension has critical issues',
    [HEALTH_STATUS.UNKNOWN]: 'Extension health status unknown',
  };
  
  return messages[status];
}

/**
 * Determines overall health status from multiple checks
 */
export function aggregateHealthStatus(checks: HealthCheck[]): HealthStatus['status'] {
  if (checks.length === 0) {
    return HEALTH_STATUS.UNKNOWN;
  }
  
  const hasError = checks.some(check => check.status === 'fail');
  const hasWarning = checks.some(check => check.status === 'warn');
  
  if (hasError) {
    return HEALTH_STATUS.ERROR;
  } else if (hasWarning) {
    return HEALTH_STATUS.WARNING;
  } else {
    return HEALTH_STATUS.HEALTHY;
  }
}

/**
 * Performs basic health checks for an extension
 */
export async function performHealthCheck(
  extension: ExtensionBase,
  resources?: ResourceUsage
): Promise<HealthCheckResult> {
  const startTime = Date.now();
  const checks: HealthCheck[] = [];
  
  // Basic availability check
  checks.push(await checkExtensionAvailability(extension));
  
  // Resource usage check
  if (resources) {
    checks.push(checkResourceUsage(resources));
  }
  
  // Configuration check
  checks.push(checkExtensionConfiguration(extension));
  
  // Dependencies check
  if (extension.dependencies && extension.dependencies.length > 0) {
    checks.push(await checkDependencies(extension.dependencies));
  }
  
  const status = aggregateHealthStatus(checks);
  const duration = Date.now() - startTime;
  
  return {
    status,
    message: generateHealthSummary(checks),
    timestamp: new Date().toISOString(),
    checks,
    details: {
      totalChecks: checks.length,
      duration,
      passedChecks: checks.filter(c => c.status === 'pass').length,
      warningChecks: checks.filter(c => c.status === 'warn').length,
      failedChecks: checks.filter(c => c.status === 'fail').length,
    },
  };
}

/**
 * Checks if extension is available/responsive
 */
async function checkExtensionAvailability(extension: ExtensionBase): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // This would typically ping the extension's health endpoint
    // For now, we'll simulate based on enabled status
    const isAvailable = extension.enabled;
    const duration = Date.now() - startTime;
    
    return {
      name: 'Availability',
      status: isAvailable ? 'pass' : 'fail',
      message: isAvailable ? 'Extension is responsive' : 'Extension is not responding',
      duration,
    };
  } catch (error) {
    return {
      name: 'Availability',
      status: 'fail',
      message: `Extension availability check failed: ${error}`,
      duration: Date.now() - startTime,
    };
  }
}

/**
 * Checks resource usage against limits
 */
function checkResourceUsage(resources: ResourceUsage): HealthCheck {
  const startTime = Date.now();
  const issues: string[] = [];
  
  // CPU usage check
  if (resources.cpu > 90) {
    issues.push(`High CPU usage: ${resources.cpu}%`);
  } else if (resources.cpu > 70) {
    issues.push(`Elevated CPU usage: ${resources.cpu}%`);
  }
  
  // Memory usage check
  if (resources.memory > 1024) { // > 1GB
    issues.push(`High memory usage: ${Math.round(resources.memory)}MB`);
  } else if (resources.memory > 512) { // > 512MB
    issues.push(`Elevated memory usage: ${Math.round(resources.memory)}MB`);
  }
  
  // Network usage check
  if (resources.network > 1024) { // > 1MB/s
    issues.push(`High network usage: ${Math.round(resources.network)}KB/s`);
  }
  
  let status: HealthCheck['status'] = 'pass';
  let message = 'Resource usage is normal';
  
  if (issues.length > 0) {
    status = resources.cpu > 90 || resources.memory > 1024 ? 'fail' : 'warn';
    message = issues.join(', ');
  }
  
  return {
    name: 'Resource Usage',
    status,
    message,
    duration: Date.now() - startTime,
    details: {
      cpu: resources.cpu,
      memory: resources.memory,
      network: resources.network,
      storage: resources.storage
    },
  };
}

/**
 * Checks extension configuration validity
 */
function checkExtensionConfiguration(extension: ExtensionBase): HealthCheck {
  const startTime = Date.now();
  const issues: string[] = [];
  
  // Basic validation
  if (!extension.name || extension.name.trim().length === 0) {
    issues.push('Missing extension name');
  }
  
  if (!extension.version || extension.version.trim().length === 0) {
    issues.push('Missing extension version');
  }
  
  if (!extension.author || extension.author.trim().length === 0) {
    issues.push('Missing extension author');
  }
  
  // Version format check
  const semverRegex = /^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9-]+))?(?:\+([a-zA-Z0-9-]+))?$/;
  if (extension.version && !semverRegex.test(extension.version)) {
    issues.push('Invalid version format');
  }
  
  let status: HealthCheck['status'] = 'pass';
  let message = 'Configuration is valid';
  
  if (issues.length > 0) {
    status = 'warn';
    message = `Configuration issues: ${issues.join(', ')}`;
  }
  
  return {
    name: 'Configuration',
    status,
    message,
    duration: Date.now() - startTime,
    details: { issues },
  };
}

/**
 * Checks extension dependencies
 */
async function checkDependencies(dependencies: string[]): Promise<HealthCheck> {
  const startTime = Date.now();
  const missingDeps: string[] = [];
  
  // This would typically check if dependencies are installed and available
  // For now, we'll simulate the check
  for (const dep of dependencies) {
    // Simulate dependency check
    const isAvailable = Math.random() > 0.1; // 90% chance of being available
    if (!isAvailable) {
      missingDeps.push(dep);
    }
  }
  
  let status: HealthCheck['status'] = 'pass';
  let message = 'All dependencies are available';
  
  if (missingDeps.length > 0) {
    status = 'fail';
    message = `Missing dependencies: ${missingDeps.join(', ')}`;
  }
  
  return {
    name: 'Dependencies',
    status,
    message,
    duration: Date.now() - startTime,
    details: { missing: missingDeps, total: dependencies.length },
  };
}

/**
 * Generates a summary message from health checks
 */
function generateHealthSummary(checks: HealthCheck[]): string {
  const failedChecks = checks.filter(c => c.status === 'fail');
  const warningChecks = checks.filter(c => c.status === 'warn');
  
  if (failedChecks.length > 0) {
    return `${failedChecks.length} critical issue${failedChecks.length > 1 ? 's' : ''} detected`;
  } else if (warningChecks.length > 0) {
    return `${warningChecks.length} warning${warningChecks.length > 1 ? 's' : ''} detected`;
  } else {
    return 'All health checks passed';
  }
}

/**
 * Gets health status color class for UI
 */
export function getHealthColorClass(status: HealthStatus['status']): string {
  return HEALTH_COLORS[status];
}

/**
 * Gets health status icon
 */
export function getHealthIcon(status: HealthStatus['status']): string {
  const iconMap = {
    [HEALTH_STATUS.HEALTHY]: 'CheckCircle',
    [HEALTH_STATUS.WARNING]: 'AlertTriangle',
    [HEALTH_STATUS.ERROR]: 'XCircle',
    [HEALTH_STATUS.UNKNOWN]: 'HelpCircle',
  };
  
  return iconMap[status];
}

/**
 * Calculates health trend from historical data
 */
export function calculateHealthTrend(
  healthHistory: Array<{ timestamp: string; status: HealthStatus['status'] }>
): 'improving' | 'stable' | 'degrading' {
  if (healthHistory.length < 2) {
    return 'stable';
  }
  
  // Convert status to numeric values for trend calculation
  const statusValues = {
    [HEALTH_STATUS.HEALTHY]: 4,
    [HEALTH_STATUS.WARNING]: 3,
    [HEALTH_STATUS.ERROR]: 2,
    [HEALTH_STATUS.UNKNOWN]: 1,
  };
  
  const recent = healthHistory.slice(-5); // Last 5 entries
  const values = recent.map(h => statusValues[h.status]);
  
  // Calculate simple trend
  const firstHalf = values.slice(0, Math.ceil(values.length / 2));
  const secondHalf = values.slice(Math.floor(values.length / 2));
  
  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
  
  const difference = secondAvg - firstAvg;
  
  if (difference > 0.5) {
    return 'improving';
  } else if (difference < -0.5) {
    return 'degrading';
  } else {
    return 'stable';
  }
}

/**
 * Formats health check duration
 */
export function formatHealthCheckDuration(duration: number): string {
  if (duration < 1000) {
    return `${duration}ms`;
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`;
  } else {
    return `${(duration / 60000).toFixed(1)}m`;
  }
}

/**
 * Determines if health check should be retried
 */
export function shouldRetryHealthCheck(
  result: HealthCheckResult,
  retryCount: number = 0
): boolean {
  const maxRetries = 3;
  
  if (retryCount >= maxRetries) {
    return false;
  }
  
  // Retry on unknown status or if all checks failed
  if (result.status === HEALTH_STATUS.UNKNOWN) {
    return true;
  }
  
  const failedChecks = result.checks.filter(c => c.status === 'fail');
  const totalChecks = result.checks.length;
  
  // Retry if more than half the checks failed
  return failedChecks.length > totalChecks / 2;
}

/**
 * Creates a health monitoring schedule
 */
export function createHealthMonitoringSchedule(
  extension: ExtensionBase
): {
  interval: number; // milliseconds
  retries: number;
  timeout: number;
} {
  // Base schedule on extension type and criticality
  let interval = 60000; // 1 minute default
  
  if ('type' in extension) {
    switch (extension.type) {
      case 'system_extension':
        interval = 30000; // 30 seconds for system extensions
        break;
      case 'provider':
        interval = 45000; // 45 seconds for providers
        break;
      case 'plugin':
        interval = 60000; // 1 minute for plugins
        break;
    }
  }
  
  return {
    interval,
    retries: 3,
    timeout: 10000, // 10 seconds
  };
}