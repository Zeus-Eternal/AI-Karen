export interface AuditLogEntry {
  id: string;
  user_id?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: any;
  created_at?: string;
}

export class AuditService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async getAuditLogs(limit = 50): Promise<AuditLogEntry[]> {
    const resp = await fetch(`${this.baseUrl}/api/audit/logs?limit=${limit}`, {
      credentials: 'include',
    });
    if (!resp.ok) {
      const error = await resp.text();
      throw new Error(`Failed to fetch audit logs: ${error}`);
    }
    return resp.json();
  }
}
