// app/api/metrics/route.ts
/**
 * Prometheus Metrics API Endpoint
 *
 * Exposes text/plain; version=0.0.4 metrics for Prometheus.
 * - Strict HELP/TYPE ordering per metric name
 * - Zero-safe defaults for optional collectors
 * - Histogram compliance: cumulative buckets, _sum, _count
 * - Fast, single-pass string build
 * - No caching
 */

import { NextRequest, NextResponse } from 'next/server';
import { MetricsCollector } from '../../../lib/monitoring/metrics-collector';
import type {
  ApplicationMetrics,
  BusinessMetrics,
  SystemMetrics,
} from '../../../lib/monitoring/metrics-collector';
import { PerformanceTracker } from '../../../lib/monitoring/performance-tracker';
import type { PerformanceMetrics as TrackerMetrics } from '../../../lib/monitoring/performance-tracker';
import { ErrorMetricsCollector } from '../../../lib/monitoring/error-metrics-collector';
import type { ErrorMetrics } from '../../../lib/monitoring/error-metrics-collector';

// Initialize collectors once (process-lifetime singletons)
const metricsCollector = new MetricsCollector();
const performanceTracker = new PerformanceTracker();
const errorMetricsCollector = new ErrorMetricsCollector();

type Num = number | null | undefined;
const n = (v: Num, d = 0): number => (Number.isFinite(v as number) ? (v as number) : d);

/** Escapes label values per Prometheus text exposition rules */
function esc(value: string): string {
  return String(value)
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/"/g, '\\"');
}

/** Ensure histogram buckets are cumulative (as Prometheus expects) */
function cumulativeize(buckets: Record<string, number> | undefined, sortedBounds: number[]) {
  const out: Record<string, number> = {};
  let running = 0;
  for (const b of sortedBounds) {
    const key = String(b);
    running += n(buckets?.[key], 0);
    out[key] = running;
  }
  // +Inf must equal total observations
  running += n(buckets?.['+Inf'], 0);
  out['+Inf'] = running;
  return out;
}

/** Emit a histogram block (buckets + sum + count) */
function emitHistogram(
  lines: string[],
  baseName: string,
  help: string,
  labelsBase: Record<string, string>,
  // input: { buckets: { bound->count } [may be non-cumulative], sum, count }
  data: { buckets?: Record<string, number>; sum?: number; count?: number } | undefined,
  sortedBounds: number[]
) {
  const metricName = baseName;
  lines.push(`# HELP ${metricName} ${help}`);
  lines.push(`# TYPE ${metricName} histogram`);

  const buckets = cumulativeize(data?.buckets ?? {}, sortedBounds);
  const labelStr = (extra: Record<string, string> = {}) => {
    const all = { ...labelsBase, ...extra };
    const inner = Object.entries(all)
      .map(([k, v]) => `${k}="${esc(v)}"`)
      .join(',');
    return `{${inner}}`;
  };

  for (const b of sortedBounds) {
    lines.push(`${metricName}_bucket${labelStr({ le: String(b) })} ${n(buckets[String(b)], 0)}`);
  }
  lines.push(`${metricName}_bucket${labelStr({ le: '+Inf' })} ${n(buckets['+Inf'], 0)}`);
  lines.push(`${metricName}_sum${labelStr()} ${n(data?.sum, 0)}`);
  lines.push(`${metricName}_count${labelStr()} ${n(data?.count, 0)}`);
}

export async function GET(_request: NextRequest): Promise<NextResponse> {
  const start = Date.now();

  try {
    // Collect in parallel
    const [
      applicationMetrics,
      performanceMetrics,
      errorMetrics,
      systemMetrics,
      businessMetrics,
    ] = (await Promise.all([
      metricsCollector.getApplicationMetrics(),
      performanceTracker.getPerformanceMetrics(),
      errorMetricsCollector.getErrorMetrics(),
      metricsCollector.getSystemMetrics(),
      metricsCollector.getBusinessMetrics(),
    ])) as [
      ApplicationMetrics,
      TrackerMetrics,
      ErrorMetrics,
      SystemMetrics,
      BusinessMetrics,
    ];

    const appHttpEntries = Object.entries(applicationMetrics?.httpRequests ?? {}) as Array<
      [string, ApplicationMetrics['httpRequests'][string]]
    >;
    const requestDurationEntries = Object.entries(applicationMetrics?.requestDurations ?? {}) as Array<
      [string, ApplicationMetrics['requestDurations'][string]]
    >;
    const pluginExecutionEntries = Object.entries(applicationMetrics?.pluginExecutions ?? {}) as Array<
      [string, ApplicationMetrics['pluginExecutions'][string]]
    >;
    const modelResponseTimeEntries = Object.entries(applicationMetrics?.modelResponseTimes ?? {}) as Array<
      [string, ApplicationMetrics['modelResponseTimes'][string]]
    >;

    const systemHealthEntries = Object.entries(systemMetrics?.healthChecks ?? {}) as Array<
      [string, SystemMetrics['healthChecks'][string]]
    >;
    const queryDurationEntries = Object.entries(systemMetrics?.database?.queryDurations ?? {}) as Array<
      [string, SystemMetrics['database']['queryDurations'][string]]
    >;

    const errorCountEntries = Object.entries(errorMetrics?.errorCounts ?? {}) as Array<
      [string, ErrorMetrics['errorCounts'][string]]
    >;
    const errorBoundaryEntries = Object.entries(errorMetrics?.errorBoundaries ?? {}) as Array<
      [string, ErrorMetrics['errorBoundaries'][string]]
    >;

    const failedLoginEntries = Object.entries(businessMetrics?.failedLogins ?? {}) as Array<
      [string, BusinessMetrics['failedLogins'][string]]
    >;

    const collectionTimeMs = Date.now() - start;
    metricsCollector.recordMetricsCollectionTime(collectionTimeMs);

    const lines: string[] = [];
    lines.push(`# Metrics collected at ${new Date().toISOString()}`, '');

    // ----------------------
    // APPLICATION METRICS
    // ----------------------
    // kari_http_requests_total (counter with path/method)
    lines.push('# HELP kari_http_requests_total Total number of HTTP requests');
    lines.push('# TYPE kari_http_requests_total counter');
    appHttpEntries.forEach(([path, data]) => {
      Object.entries(data.methods ?? {}).forEach(([method, count]) => {
        const numericCount = typeof count === 'number' ? count : Number(count ?? 0);
        lines.push(`kari_http_requests_total{path="${esc(path)}",method="${esc(method)}"} ${n(numericCount)}`);
      });
    });

    // kari_http_request_duration_seconds (histogram with path)
    const httpBounds = [0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    requestDurationEntries.forEach(([path, d]) => {
      emitHistogram(
        lines,
        'kari_http_request_duration_seconds',
        'HTTP request duration in seconds',
        { path: esc(path) },
        {
          buckets: durationMetrics.buckets,
          sum: n(durationMetrics.sum),
          count: n(durationMetrics.count),
        },
        httpBounds,
      );
    }

    // kari_active_sessions_total (gauge)
    lines.push('# HELP kari_active_sessions_total Number of active user sessions');
    lines.push('# TYPE kari_active_sessions_total gauge');
    const activeSessions =
      typeof applicationMetrics?.activeSessions === 'number'
        ? applicationMetrics.activeSessions
        : Number(applicationMetrics?.activeSessions ?? 0);
    lines.push(`kari_active_sessions_total ${n(activeSessions)}`);

    // kari_websocket_connections_total (gauge)
    lines.push('# HELP kari_websocket_connections_total Number of active WebSocket connections');
    lines.push('# TYPE kari_websocket_connections_total gauge');
    const websocketConnections =
      typeof applicationMetrics?.websocketConnections === 'number'
        ? applicationMetrics.websocketConnections
        : Number(applicationMetrics?.websocketConnections ?? 0);
    lines.push(`kari_websocket_connections_total ${n(websocketConnections)}`);

    // Feature usage (counter by feature)
    lines.push('# HELP kari_feature_usage_total Total usage count for application features');
    lines.push('# TYPE kari_feature_usage_total counter');
    const featureUsage = applicationMetrics.featureUsage;
    for (const feature of Object.keys(featureUsage)) {
      const count = featureUsage[feature];
      lines.push(`kari_feature_usage_total{feature="${esc(feature)}"} ${n(count)}`);
    }

    // Plugin executions (counter by plugin/status)
    lines.push('# HELP kari_plugin_executions_total Total number of plugin executions');
    lines.push('# TYPE kari_plugin_executions_total counter');
    pluginExecutionEntries.forEach(([plugin, d]) => {
      const successCount = typeof d.success === 'number' ? d.success : Number(d.success ?? 0);
      const failureCount = typeof d.failure === 'number' ? d.failure : Number(d.failure ?? 0);
      lines.push(`kari_plugin_executions_total{plugin="${esc(plugin)}",status="success"} ${n(successCount)}`);
      lines.push(`kari_plugin_executions_total{plugin="${esc(plugin)}",status="failure"} ${n(failureCount)}`);
    });

    // Model requests (counter by model)
    lines.push('# HELP kari_model_requests_total Total number of model requests');
    lines.push('# TYPE kari_model_requests_total counter');
    const modelRequests = applicationMetrics.modelRequests;
    for (const model of Object.keys(modelRequests)) {
      lines.push(`kari_model_requests_total{model="${esc(model)}"} ${n(modelRequests[model])}`);
    }

    // Model response time (histogram by model)
    const modelBounds = [0.1, 0.5, 1, 2, 5, 10, 30, 60];
    modelResponseTimeEntries.forEach(([model, d]) => {
      emitHistogram(
        lines,
        'kari_model_response_time_seconds',
        'Model response time in seconds',
        { model: esc(model) },
        {
          buckets: responseMetrics.buckets,
          sum: n(responseMetrics.sum),
          count: n(responseMetrics.count),
        },
        modelBounds,
      );
    }

    // ----------------------
    // PERFORMANCE METRICS
    // ----------------------
    lines.push('# HELP kari_memory_usage_bytes Memory usage in bytes');
    lines.push('# TYPE kari_memory_usage_bytes gauge');
    lines.push(`kari_memory_usage_bytes{type="rss"} ${n(performanceMetrics?.memory?.rss)}`);
    lines.push(`kari_memory_usage_bytes{type="heap_total"} ${n(performanceMetrics?.memory?.heapTotal)}`);
    lines.push(`kari_memory_usage_bytes{type="heap_used"} ${n(performanceMetrics?.memory?.heapUsed)}`);
    lines.push(`kari_memory_usage_bytes{type="external"} ${n(performanceMetrics?.memory?.external)}`);

    lines.push('# HELP kari_cpu_usage_percent CPU usage percentage');
    lines.push('# TYPE kari_cpu_usage_percent gauge');
    lines.push(`kari_cpu_usage_percent ${n(performanceMetrics?.cpu?.usage)}`);

    lines.push('# HELP kari_uptime_seconds Application uptime in seconds');
    lines.push('# TYPE kari_uptime_seconds gauge');
    lines.push(`kari_uptime_seconds ${process.uptime()}`);

    // ----------------------
    // ERROR METRICS
    // ----------------------
    lines.push('# HELP kari_errors_total Total number of errors');
    lines.push('# TYPE kari_errors_total counter');
    errorCountEntries.forEach(([type, count]) => {
      lines.push(`kari_errors_total{type="${esc(String(type))}"} ${n(count)}`);
    });

    lines.push('# HELP kari_error_boundary_triggered_total Total number of error boundary triggers');
    lines.push('# TYPE kari_error_boundary_triggered_total counter');
    errorBoundaryEntries.forEach(([component, count]) => {
      lines.push(`kari_error_boundary_triggered_total{component="${esc(String(component))}"} ${n(count)}`);
    });

    lines.push('# HELP kari_error_recovery_attempts_total Total number of error recovery attempts');
    lines.push('# TYPE kari_error_recovery_attempts_total counter');
    lines.push(`kari_error_recovery_attempts_total ${n(errorMetrics?.recoveryAttempts)}`);

    lines.push('# HELP kari_error_recovery_success_total Total number of successful error recoveries');
    lines.push('# TYPE kari_error_recovery_success_total counter');
    lines.push(`kari_error_recovery_success_total ${n(errorMetrics?.recoverySuccesses)}`);

    // ----------------------
    // SYSTEM METRICS
    // ----------------------
    lines.push('# HELP kari_health_check_status Health check status (1 = healthy, 0 = unhealthy)');
    lines.push('# TYPE kari_health_check_status gauge');
    systemHealthEntries.forEach(([check, status]) => {
      let val = 0;
      if (status === 'healthy') {
        val = 1;
      } else if (status === 'degraded') {
        val = 0.5;
      }
      lines.push(`kari_health_check_status{check_name="${esc(String(check))}"} ${val}`);
    });

    lines.push('# HELP kari_database_connections_total Number of database connections');
    lines.push('# TYPE kari_database_connections_total gauge');
    lines.push(`kari_database_connections_total{state="active"} ${n(systemMetrics?.database?.activeConnections)}`);
    lines.push(`kari_database_connections_total{state="idle"} ${n(systemMetrics?.database?.idleConnections)}`);

    lines.push('# HELP kari_database_connections_failed_total Total number of failed database connections');
    lines.push('# TYPE kari_database_connections_failed_total counter');
    lines.push(`kari_database_connections_failed_total ${n(systemMetrics?.database?.failedConnections)}`);

    lines.push('# HELP kari_redis_connections_total Number of Redis connections');
    lines.push('# TYPE kari_redis_connections_total gauge');
    lines.push(`kari_redis_connections_total ${n(systemMetrics?.redis?.connections)}`);

    lines.push('# HELP kari_redis_connections_failed_total Total number of failed Redis connections');
    lines.push('# TYPE kari_redis_connections_failed_total counter');
    lines.push(`kari_redis_connections_failed_total ${n(systemMetrics?.redis?.failedConnections)}`);

    // Database query duration (histogram by query label)
    const dbBounds = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    queryDurationEntries.forEach(([query, d]) => {
      emitHistogram(
        lines,
        'kari_database_query_duration_seconds',
        'Database query duration in seconds',
        { query: esc(query) },
        {
          buckets: queryMetrics.buckets,
          sum: n(queryMetrics.sum),
          count: n(queryMetrics.count),
        },
        dbBounds,
      );
    }

    // ----------------------
    // BUSINESS METRICS
    // ----------------------
    lines.push('# HELP kari_user_sessions_total Total number of user sessions created');
    lines.push('# TYPE kari_user_sessions_total counter');
    lines.push(`kari_user_sessions_total ${n(businessMetrics?.userSessions)}`);

    lines.push('# HELP kari_user_conversions_total Total number of user conversions');
    lines.push('# TYPE kari_user_conversions_total counter');
    lines.push(`kari_user_conversions_total ${n(businessMetrics?.conversions)}`);

    lines.push('# HELP kari_user_bounces_total Total number of user bounces');
    lines.push('# TYPE kari_user_bounces_total counter');
    lines.push(`kari_user_bounces_total ${n(businessMetrics?.bounces)}`);

    lines.push('# HELP kari_api_rate_limit_exceeded_total Total number of API rate limit exceeded events');
    lines.push('# TYPE kari_api_rate_limit_exceeded_total counter');
    lines.push(`kari_api_rate_limit_exceeded_total ${n(businessMetrics?.rateLimitExceeded)}`);

    lines.push('# HELP kari_failed_login_attempts_total Total number of failed login attempts');
    lines.push('# TYPE kari_failed_login_attempts_total counter');
    failedLoginEntries.forEach(([sourceIp, count]) => {
      lines.push(`kari_failed_login_attempts_total{source_ip="${esc(String(sourceIp))}"} ${n(count)}`);
    });

    lines.push('# HELP kari_evil_mode_activations_total Total number of Evil Mode activations');
    lines.push('# TYPE kari_evil_mode_activations_total counter');
    lines.push(`kari_evil_mode_activations_total ${n(businessMetrics?.evilModeActivations)}`);

    // ----------------------
    // COLLECTION META
    // ----------------------
    lines.push('# HELP kari_metrics_collection_duration_seconds Time spent collecting metrics');
    lines.push('# TYPE kari_metrics_collection_duration_seconds gauge');
    lines.push(`kari_metrics_collection_duration_seconds ${collectionTimeMs / 1000}`);

    lines.push('# HELP kari_metrics_collection_timestamp_seconds Timestamp of metrics collection');
    lines.push('# TYPE kari_metrics_collection_timestamp_seconds gauge');
    lines.push(`kari_metrics_collection_timestamp_seconds ${Date.now() / 1000}`);

    // Final body
    const body = lines.join('\n') + '\n';
    return new NextResponse(body, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    console.error('Metrics collection failed', error);
    // Minimal but valid fallback payload for Prometheus
    const fallback =
      '# HELP kari_metrics_collection_errors_total Total number of metrics collection errors\n' +
      '# TYPE kari_metrics_collection_errors_total counter\n' +
      'kari_metrics_collection_errors_total 1\n' +
      '# HELP kari_metrics_collection_timestamp_seconds Timestamp of last metrics collection attempt\n' +
      '# TYPE kari_metrics_collection_timestamp_seconds gauge\n' +
      `kari_metrics_collection_timestamp_seconds ${Date.now() / 1000}\n`;
    return new NextResponse(fallback, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
      },
    });
  }
}
