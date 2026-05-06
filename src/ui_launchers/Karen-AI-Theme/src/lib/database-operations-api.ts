import { apiClient } from './api';

export type HealthStatus =
  | "healthy"
  | "degraded"
  | "unavailable"
  | "disabled"
  | "unknown";

export type TierName = "postgres" | "redis" | "milvus" | "elasticsearch" | "duckdb" | "leangraph" | "minio";

export interface StorageTierHealth {
  tier: TierName;
  status: HealthStatus;
  enabled: boolean;
  connected: boolean;
  latency_ms?: number | null;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  error_type?: string | null;
  error_message?: string | null;
  circuit_breaker_state?: string | null;
  metadata: Record<string, unknown>;
}

export interface MemoryWritebackHealth {
    status: HealthStatus;
    enabled: boolean;
    queue_depth?: number | null;
    pending_count?: number | null;
    failed_count?: number | null;
    last_write_at?: string | null;
    last_failure_at?: string | null;
    writeback_status?: string | null;
    degraded_reason?: string | null;
}

export interface ProjectionHealth {
    name: string;
    target_tier: TierName;
    status: HealthStatus;
    lag_count?: number | null;
    last_projected_at?: string | null;
    failed_count?: number | null;
    retry_available: boolean;
}

export interface MigrationHealth {
    status: HealthStatus;
    current_version?: string | null;
    latest_version?: string | null;
    pending_count: number;
    failed_count: number;
    validation_status?: string | null;
}

export interface DatabaseOperationsOverview {
  status: HealthStatus;
  generated_at: string;
  correlation_id: string;
  request_id: string;
  storage_tiers: StorageTierHealth[];
  memory_writeback: MemoryWritebackHealth;
  projections: ProjectionHealth[];
  migrations: MigrationHealth;
  warnings: string[];
  actions_available: string[];
}

class DatabaseOperationsApi {
    async getOverview(): Promise<DatabaseOperationsOverview> {
        return await apiClient.get<DatabaseOperationsOverview>('/api/admin/database/overview');
    }

    async runMaintenance(): Promise<{ status: string; message: string }> {
        return await apiClient.post('/api/admin/database/maintenance/run', {});
    }

    async retryProjections(): Promise<{ status: string; message: string }> {
        return await apiClient.post('/api/admin/database/projections/retry', {});
    }

    async validateMigrations(): Promise<{ status: string; message: string }> {
        return await apiClient.post('/api/admin/database/migrations/validate', {});
    }
}

export const databaseOperationsApi = new DatabaseOperationsApi();
