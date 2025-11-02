/**
 * Prometheus Metrics API Endpoint
 * 
 * Provides comprehensive metrics collection for Prometheus monitoring
 * including custom application metrics, performance data, and business metrics.
 */

import { NextRequest, NextResponse } from 'next/server';
import { MetricsCollector } from '../../../lib/monitoring/metrics-collector';
import { PerformanceTracker } from '../../../lib/monitoring/performance-tracker';
import { ErrorMetricsCollector } from '../../../lib/monitoring/error-metrics-collector';

// Initialize metrics collectors
const metricsCollector = new MetricsCollector();
const performanceTracker = new PerformanceTracker();
const errorMetricsCollector = new ErrorMetricsCollector();

/**
 * GET /api/metrics
 * Returns Prometheus-formatted metrics
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const startTime = Date.now();
    
    // Collect all metrics
    const [
      applicationMetrics,
      performanceMetrics,
      errorMetrics,
      systemMetrics,
      businessMetrics
    ] = await Promise.all([
      metricsCollector.getApplicationMetrics(),
      performanceTracker.getPerformanceMetrics(),
      errorMetricsCollector.getErrorMetrics(),
      metricsCollector.getSystemMetrics(),
      metricsCollector.getBusinessMetrics()
    ]);

    // Format metrics for Prometheus
    const prometheusMetrics = formatPrometheusMetrics({
      application: applicationMetrics,
      performance: performanceMetrics,
      errors: errorMetrics,
      system: systemMetrics,
      business: businessMetrics
    });

    // Track metrics collection time
    const collectionTime = Date.now() - startTime;
    metricsCollector.recordMetricsCollectionTime(collectionTime);

    return new NextResponse(prometheusMetrics, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    console.error('Failed to collect metrics:', error);
    
    // Return basic error metrics
    const errorMetrics = `
# HELP kari_metrics_collection_errors_total Total number of metrics collection errors
# TYPE kari_metrics_collection_errors_total counter
kari_metrics_collection_errors_total 1

# HELP kari_metrics_collection_timestamp_seconds Timestamp of last metrics collection attempt
# TYPE kari_metrics_collection_timestamp_seconds gauge
kari_metrics_collection_timestamp_seconds ${Date.now() / 1000}
`;

    return new NextResponse(errorMetrics, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
      }
    });
  }
}

/**
 * Format metrics in Prometheus format
 */
function formatPrometheusMetrics(metrics: any): string {
  const lines: string[] = [];
  
  // Add timestamp
  lines.push(`# Metrics collected at ${new Date().toISOString()}`);
  lines.push('');

  // Application Metrics
  lines.push('# HELP kari_http_requests_total Total number of HTTP requests');
  lines.push('# TYPE kari_http_requests_total counter');
  Object.entries(metrics.application.httpRequests || {}).forEach(([path, data]: [string, any]) => {
    Object.entries(data.methods || {}).forEach(([method, count]) => {
      lines.push(`kari_http_requests_total{path="${path}",method="${method}"} ${count}`);
    });
  });
  lines.push('');

  lines.push('# HELP kari_http_request_duration_seconds HTTP request duration in seconds');
  lines.push('# TYPE kari_http_request_duration_seconds histogram');
  Object.entries(metrics.application.requestDurations || {}).forEach(([path, data]: [string, any]) => {
    const buckets = [0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    buckets.forEach(bucket => {
      const count = data.buckets?.[bucket] || 0;
      lines.push(`kari_http_request_duration_seconds_bucket{path="${path}",le="${bucket}"} ${count}`);
    });
    lines.push(`kari_http_request_duration_seconds_bucket{path="${path}",le="+Inf"} ${data.total || 0}`);
    lines.push(`kari_http_request_duration_seconds_sum{path="${path}"} ${data.sum || 0}`);
    lines.push(`kari_http_request_duration_seconds_count{path="${path}"} ${data.count || 0}`);
  });
  lines.push('');

  lines.push('# HELP kari_active_sessions_total Number of active user sessions');
  lines.push('# TYPE kari_active_sessions_total gauge');
  lines.push(`kari_active_sessions_total ${metrics.application.activeSessions || 0}`);
  lines.push('');

  lines.push('# HELP kari_websocket_connections_total Number of active WebSocket connections');
  lines.push('# TYPE kari_websocket_connections_total gauge');
  lines.push(`kari_websocket_connections_total ${metrics.application.websocketConnections || 0}`);
  lines.push('');

  // Performance Metrics
  lines.push('# HELP kari_memory_usage_bytes Memory usage in bytes');
  lines.push('# TYPE kari_memory_usage_bytes gauge');
  lines.push(`kari_memory_usage_bytes{type="rss"} ${metrics.performance.memory?.rss || 0}`);
  lines.push(`kari_memory_usage_bytes{type="heap_total"} ${metrics.performance.memory?.heapTotal || 0}`);
  lines.push(`kari_memory_usage_bytes{type="heap_used"} ${metrics.performance.memory?.heapUsed || 0}`);
  lines.push(`kari_memory_usage_bytes{type="external"} ${metrics.performance.memory?.external || 0}`);
  lines.push('');

  lines.push('# HELP kari_cpu_usage_percent CPU usage percentage');
  lines.push('# TYPE kari_cpu_usage_percent gauge');
  lines.push(`kari_cpu_usage_percent ${metrics.performance.cpu?.usage || 0}`);
  lines.push('');

  lines.push('# HELP kari_uptime_seconds Application uptime in seconds');
  lines.push('# TYPE kari_uptime_seconds gauge');
  lines.push(`kari_uptime_seconds ${process.uptime()}`);
  lines.push('');

  // Error Metrics
  lines.push('# HELP kari_errors_total Total number of errors');
  lines.push('# TYPE kari_errors_total counter');
  Object.entries(metrics.errors.errorCounts || {}).forEach(([type, count]) => {
    lines.push(`kari_errors_total{type="${type}"} ${count}`);
  });
  lines.push('');

  lines.push('# HELP kari_error_boundary_triggered_total Total number of error boundary triggers');
  lines.push('# TYPE kari_error_boundary_triggered_total counter');
  Object.entries(metrics.errors.errorBoundaries || {}).forEach(([component, count]) => {
    lines.push(`kari_error_boundary_triggered_total{component="${component}"} ${count}`);
  });
  lines.push('');

  lines.push('# HELP kari_error_recovery_attempts_total Total number of error recovery attempts');
  lines.push('# TYPE kari_error_recovery_attempts_total counter');
  lines.push(`kari_error_recovery_attempts_total ${metrics.errors.recoveryAttempts || 0}`);
  lines.push('');

  lines.push('# HELP kari_error_recovery_success_total Total number of successful error recoveries');
  lines.push('# TYPE kari_error_recovery_success_total counter');
  lines.push(`kari_error_recovery_success_total ${metrics.errors.recoverySuccesses || 0}`);
  lines.push('');

  // System Metrics
  lines.push('# HELP kari_health_check_status Health check status (1 = healthy, 0 = unhealthy)');
  lines.push('# TYPE kari_health_check_status gauge');
  Object.entries(metrics.system.healthChecks || {}).forEach(([check, status]) => {
    lines.push(`kari_health_check_status{check_name="${check}"} ${status === 'healthy' ? 1 : 0}`);
  });
  lines.push('');

  lines.push('# HELP kari_database_connections_total Number of database connections');
  lines.push('# TYPE kari_database_connections_total gauge');
  lines.push(`kari_database_connections_total{state="active"} ${metrics.system.database?.activeConnections || 0}`);
  lines.push(`kari_database_connections_total{state="idle"} ${metrics.system.database?.idleConnections || 0}`);
  lines.push('');

  lines.push('# HELP kari_database_connections_failed_total Total number of failed database connections');
  lines.push('# TYPE kari_database_connections_failed_total counter');
  lines.push(`kari_database_connections_failed_total ${metrics.system.database?.failedConnections || 0}`);
  lines.push('');

  lines.push('# HELP kari_redis_connections_total Number of Redis connections');
  lines.push('# TYPE kari_redis_connections_total gauge');
  lines.push(`kari_redis_connections_total ${metrics.system.redis?.connections || 0}`);
  lines.push('');

  lines.push('# HELP kari_redis_connections_failed_total Total number of failed Redis connections');
  lines.push('# TYPE kari_redis_connections_failed_total counter');
  lines.push(`kari_redis_connections_failed_total ${metrics.system.redis?.failedConnections || 0}`);
  lines.push('');

  // Business Metrics
  lines.push('# HELP kari_user_sessions_total Total number of user sessions created');
  lines.push('# TYPE kari_user_sessions_total counter');
  lines.push(`kari_user_sessions_total ${metrics.business.userSessions || 0}`);
  lines.push('');

  lines.push('# HELP kari_user_conversions_total Total number of user conversions');
  lines.push('# TYPE kari_user_conversions_total counter');
  lines.push(`kari_user_conversions_total ${metrics.business.conversions || 0}`);
  lines.push('');

  lines.push('# HELP kari_user_bounces_total Total number of user bounces');
  lines.push('# TYPE kari_user_bounces_total counter');
  lines.push(`kari_user_bounces_total ${metrics.business.bounces || 0}`);
  lines.push('');

  lines.push('# HELP kari_api_rate_limit_exceeded_total Total number of API rate limit exceeded events');
  lines.push('# TYPE kari_api_rate_limit_exceeded_total counter');
  lines.push(`kari_api_rate_limit_exceeded_total ${metrics.business.rateLimitExceeded || 0}`);
  lines.push('');

  lines.push('# HELP kari_failed_login_attempts_total Total number of failed login attempts');
  lines.push('# TYPE kari_failed_login_attempts_total counter');
  Object.entries(metrics.business.failedLogins || {}).forEach(([sourceIp, count]) => {
    lines.push(`kari_failed_login_attempts_total{source_ip="${sourceIp}"} ${count}`);
  });
  lines.push('');

  lines.push('# HELP kari_evil_mode_activations_total Total number of Evil Mode activations');
  lines.push('# TYPE kari_evil_mode_activations_total counter');
  lines.push(`kari_evil_mode_activations_total ${metrics.business.evilModeActivations || 0}`);
  lines.push('');

  // Database Query Metrics
  lines.push('# HELP kari_database_query_duration_seconds Database query duration in seconds');
  lines.push('# TYPE kari_database_query_duration_seconds histogram');
  Object.entries(metrics.system.database?.queryDurations || {}).forEach(([query, data]: [string, any]) => {
    const buckets = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    buckets.forEach(bucket => {
      const count = data.buckets?.[bucket] || 0;
      lines.push(`kari_database_query_duration_seconds_bucket{query="${query}",le="${bucket}"} ${count}`);
    });
    lines.push(`kari_database_query_duration_seconds_bucket{query="${query}",le="+Inf"} ${data.total || 0}`);
    lines.push(`kari_database_query_duration_seconds_sum{query="${query}"} ${data.sum || 0}`);
    lines.push(`kari_database_query_duration_seconds_count{query="${query}"} ${data.count || 0}`);
  });
  lines.push('');

  // Custom Application Metrics
  lines.push('# HELP kari_feature_usage_total Total usage count for application features');
  lines.push('# TYPE kari_feature_usage_total counter');
  Object.entries(metrics.application.featureUsage || {}).forEach(([feature, count]) => {
    lines.push(`kari_feature_usage_total{feature="${feature}"} ${count}`);
  });
  lines.push('');

  lines.push('# HELP kari_plugin_executions_total Total number of plugin executions');
  lines.push('# TYPE kari_plugin_executions_total counter');
  Object.entries(metrics.application.pluginExecutions || {}).forEach(([plugin, data]: [string, any]) => {
    lines.push(`kari_plugin_executions_total{plugin="${plugin}",status="success"} ${data.success || 0}`);
    lines.push(`kari_plugin_executions_total{plugin="${plugin}",status="failure"} ${data.failure || 0}`);
  });
  lines.push('');

  lines.push('# HELP kari_model_requests_total Total number of model requests');
  lines.push('# TYPE kari_model_requests_total counter');
  Object.entries(metrics.application.modelRequests || {}).forEach(([model, count]) => {
    lines.push(`kari_model_requests_total{model="${model}"} ${count}`);
  });
  lines.push('');

  lines.push('# HELP kari_model_response_time_seconds Model response time in seconds');
  lines.push('# TYPE kari_model_response_time_seconds histogram');
  Object.entries(metrics.application.modelResponseTimes || {}).forEach(([model, data]: [string, any]) => {
    const buckets = [0.1, 0.5, 1, 2, 5, 10, 30, 60];
    buckets.forEach(bucket => {
      const count = data.buckets?.[bucket] || 0;
      lines.push(`kari_model_response_time_seconds_bucket{model="${model}",le="${bucket}"} ${count}`);
    });
    lines.push(`kari_model_response_time_seconds_bucket{model="${model}",le="+Inf"} ${data.total || 0}`);
    lines.push(`kari_model_response_time_seconds_sum{model="${model}"} ${data.sum || 0}`);
    lines.push(`kari_model_response_time_seconds_count{model="${model}"} ${data.count || 0}`);
  });
  lines.push('');

  // Metrics collection metadata
  lines.push('# HELP kari_metrics_collection_duration_seconds Time spent collecting metrics');
  lines.push('# TYPE kari_metrics_collection_duration_seconds gauge');
  lines.push(`kari_metrics_collection_duration_seconds ${(metrics.collectionTime || 0) / 1000}`);
  lines.push('');

  lines.push('# HELP kari_metrics_collection_timestamp_seconds Timestamp of metrics collection');
  lines.push('# TYPE kari_metrics_collection_timestamp_seconds gauge');
  lines.push(`kari_metrics_collection_timestamp_seconds ${Date.now() / 1000}`);

  return lines.join('\n');
}