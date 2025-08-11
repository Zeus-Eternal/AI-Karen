import { getApiClient } from '@/lib/api-client';

export interface AuditLogEntry {
  id: string;
  user_id?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: any;
  created_at?: string;
}

/**
 * Service for retrieving audit log entries from the backend.
 *
 * Uses the shared ApiClient which handles base URL configuration,
 * authentication cookies, and fallback logic.
 */
export class AuditService {
  private apiClient = getApiClient();

  async getAuditLogs(limit = 50): Promise<AuditLogEntry[]> {
    const response = await this.apiClient.get<AuditLogEntry[]>(`/api/audit/logs?limit=${limit}`);
    return response.data;
  }
}
