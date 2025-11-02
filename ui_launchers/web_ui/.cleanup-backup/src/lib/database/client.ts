/**
 * Database Client Interface and Implementation
 * 
 * This file provides a database client interface that can be implemented
 * with different database drivers (pg, mysql, etc.)
 */

// Only import pg on server-side
let Pool: any, PoolClient: any, PoolConfig: any;
if (typeof window === 'undefined') {
  try {
    const pg = require('pg');
    Pool = pg.Pool;
    PoolClient = pg.PoolClient;
    PoolConfig = pg.PoolConfig;
  } catch (error) {
    console.warn('pg library not available:', error);
  }
}

// Database client interface
export interface DatabaseClient {
  query(sql: string, params?: any[]): Promise<QueryResult>;
  transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T>;
  close?(): Promise<void>;
}

// Query result interface
export interface QueryResult {
  rows: any[];
  rowCount: number;
  fields?: any[];
}

// PostgreSQL client implementation
export class PostgreSQLClient implements DatabaseClient {
  private pool: any;

  constructor(connectionConfig: string | any) {
    if (typeof window !== 'undefined') {
      throw new Error('PostgreSQL client can only be used on the server side');
    }

    if (!Pool) {
      throw new Error('pg library is not available');
    }

    const config = typeof connectionConfig === 'string' 
      ? { connectionString: connectionConfig }
      : connectionConfig;

    // Set reasonable defaults for connection pooling
    this.pool = new Pool({
      ...config,
      max: config.max || 20,
      idleTimeoutMillis: config.idleTimeoutMillis || 30000,
      connectionTimeoutMillis: config.connectionTimeoutMillis || 2000,
    });

    // Handle pool errors
    this.pool.on('error', (err: any) => {
      console.error('Unexpected error on idle client', err);
    });
  }

  async query(sql: string, params?: any[]): Promise<QueryResult> {
    try {
      const result = await this.pool.query(sql, params);
      return {
        rows: result.rows,
        rowCount: result.rowCount || 0,
        fields: result.fields
      };
    } catch (error) {
      console.error('Database query error:', error);
      throw error;
    }
  }

  async transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T> {
    const poolClient = await this.pool.connect();
    
    try {
      await poolClient.query('BEGIN');
      
      // Create a transaction client wrapper
      const transactionClient: DatabaseClient = {
        query: async (sql: string, params?: any[]) => {
          const result = await poolClient.query(sql, params);
          return {
            rows: result.rows,
            rowCount: result.rowCount || 0,
            fields: result.fields
          };
        },
        transaction: async () => {
          throw new Error('Nested transactions are not supported');
        }
      };

      const result = await callback(transactionClient);
      await poolClient.query('COMMIT');
      return result;
    } catch (error) {
      await poolClient.query('ROLLBACK');
      throw error;
    } finally {
      poolClient.release();
    }
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}

// Database client factory
export class DatabaseClientFactory {
  static create(type: 'postgresql', config: string | any): DatabaseClient {
    if (typeof window !== 'undefined') {
      throw new Error('Database client can only be created on the server side');
    }

    switch (type) {
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
  if (typeof window !== 'undefined') {
    throw new Error('Database client can only be accessed on the server side');
  }

  if (!dbClient) {
    // Get database URL from environment
    const databaseUrl = process.env.DATABASE_URL || process.env.POSTGRES_URL;
    
    if (!databaseUrl) {
      throw new Error('DATABASE_URL or POSTGRES_URL environment variable is required');
    }

    try {
      console.log('Initializing PostgreSQL database client');
      dbClient = DatabaseClientFactory.create('postgresql', databaseUrl);
    } catch (error) {
      console.error('Failed to create PostgreSQL client:', error);
      throw new Error(`Database connection failed: ${error}`);
    }
  }
  return dbClient;
}

// Function to safely close the database connection
export async function closeDatabaseClient(): Promise<void> {
  if (dbClient && 'close' in dbClient && typeof dbClient.close === 'function') {
    await dbClient.close();
    dbClient = null;
  }
}

export function setDatabaseClient(client: DatabaseClient): void {
  dbClient = client;
}