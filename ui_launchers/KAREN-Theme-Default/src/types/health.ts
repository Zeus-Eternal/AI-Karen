/**
 * Shared health monitoring types consumed by server routes and UI components.
 */

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | string;
  response_time_ms: number;
  last_check: string;
  error?: string;
}

export interface BackendHealthData {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | string;
  timestamp: string;
  response_time_ms: number;
  services: {
    database: ServiceHealth;
    redis: ServiceHealth;
    ai_providers: ServiceHealth;
    system_resources: ServiceHealth;
    [key: string]: ServiceHealth;
  };
  summary: {
    healthy_services: number;
    degraded_services: number;
    unhealthy_services: number;
    total_services: number;
  };
}
