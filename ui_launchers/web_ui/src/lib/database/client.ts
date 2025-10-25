/**
 * Database Client Interface and Implementation
 * 
 * This file provides a database client interface that can be implemented
 * with different database drivers (pg, mysql, etc.)
 */

// Database client interface
export interface DatabaseClient {
  query(sql: string, params?: any[]): Promise<QueryResult>;
  transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T>;
}

// Query result interface
export interface QueryResult {
  rows: any[];
  rowCount: number;
  fields?: any[];
}

// Mock database client for development/testing
export class MockDatabaseClient implements DatabaseClient {
  async query(sql: string, params?: any[]): Promise<QueryResult> {
    console.log('Mock DB Query:', sql, params);
    
    // Handle specific queries for testing
    if (sql.includes('log_audit_event')) {
      return {
        rows: [{ audit_id: 'mock-audit-id-123' }],
        rowCount: 1
      };
    }
    
    if (sql.includes('user_has_permission')) {
      return {
        rows: [{ has_permission: false }],
        rowCount: 1
      };
    }
    
    if (sql.includes('get_user_permissions')) {
      return {
        rows: [],
        rowCount: 0
      };
    }
    
    // Return mock data based on query patterns and parameters
    if (sql.includes('auth_users')) {
      // Check if this is a query for a non-existent user
      if (params && params[0] === 'non-existent') {
        return {
          rows: [],
          rowCount: 0
        };
      }
      
      return {
        rows: [{
          user_id: '123e4567-e89b-12d3-a456-426614174000',
          email: 'admin@ai-karen.local',
          full_name: 'System Administrator',
          role: 'super_admin',
          roles: ['admin', 'user'],
          tenant_id: 'default',
          preferences: {},
          is_verified: true,
          is_active: true,
          created_at: new Date(),
          updated_at: new Date(),
          two_factor_enabled: false
        }],
        rowCount: 1
      };
    }
    
    if (sql.includes('audit_logs')) {
      return {
        rows: [],
        rowCount: 0
      };
    }
    
    if (sql.includes('system_config')) {
      return {
        rows: [],
        rowCount: 0
      };
    }
    
    if (sql.includes('COUNT(*)')) {
      return {
        rows: [{ total: 0, count: 0 }],
        rowCount: 1
      };
    }
    
    return {
      rows: [],
      rowCount: 0
    };
  }

  async transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T> {
    console.log('Mock DB Transaction started');
    try {
      const result = await callback(this);
      console.log('Mock DB Transaction committed');
      return result;
    } catch (error) {
      console.log('Mock DB Transaction rolled back');
      throw error;
    }
  }
}

// PostgreSQL client implementation (to be implemented when needed)
export class PostgreSQLClient implements DatabaseClient {
  private pool: any; // pg.Pool instance

  constructor(connectionConfig: any) {
    // Initialize PostgreSQL connection pool
    // This would use the 'pg' library when implemented
    console.log('PostgreSQL client initialized with config:', connectionConfig);
  }

  async query(sql: string, params?: any[]): Promise<QueryResult> {
    // Implementation would use this.pool.query()
    throw new Error('PostgreSQL client not yet implemented');
  }

  async transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T> {
    // Implementation would use this.pool.connect() and client.query('BEGIN')
    throw new Error('PostgreSQL client not yet implemented');
  }
}

// Database client factory
export class DatabaseClientFactory {
  static create(type: 'mock' | 'postgresql', config?: any): DatabaseClient {
    switch (type) {
      case 'mock':
        return new MockDatabaseClient();
      case 'postgresql':
        return new PostgreSQLClient(config);
      default:
        throw new Error(`Unsupported database client type: ${type}`);
    }
  }
}

// Singleton database client instance
let dbClient: DatabaseClient | null = null;

export function getDatabaseClient(): DatabaseClient {
  if (!dbClient) {
    // For now, use mock client. This can be configured based on environment
    dbClient = DatabaseClientFactory.create('mock');
  }
  return dbClient;
}

export function setDatabaseClient(client: DatabaseClient): void {
  dbClient = client;
}