// ui_launchers/KAREN-Theme-Default/src/lib/database/client.ts
/**
 * Database Client Interface and Implementation
 *
 * This file provides a database client interface that can be implemented
 * with different database drivers (pg, mysql, etc.)
 */

import type {
  Pool as PgPool,
  PoolClient,
  PoolConfig,
  QueryResult as PgQueryResult,
  QueryResultRow,
} from "pg";

type PoolConstructor = typeof import("pg").Pool;
type ConnectionConfig = PoolConfig & { connectionString?: string };

let PoolClass: PoolConstructor | undefined;
if (typeof window === "undefined") {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pg = require("pg") as { Pool: PoolConstructor };
    PoolClass = pg.Pool;
  } catch (error) {
    console.warn(
      "pg module is not available; database operations are disabled.",
      error,
    );
  }
}

// Database client interface
export interface DatabaseClient {
  query(sql: string, params?: unknown[]): Promise<QueryResult>;
  transaction<T>(callback: (client: DatabaseClient) => Promise<T>): Promise<T>;
  close?(): Promise<void>;
}

// Query result interface
export interface QueryResult {
  rows: unknown[];
  rowCount: number;
  fields?: unknown[];
}

// PostgreSQL client implementation
export class PostgreSQLClient implements DatabaseClient {
  private pool: PgPool;

  constructor(connectionConfig: string | ConnectionConfig) {
    if (typeof window !== "undefined") {
      throw new Error("PostgreSQL client can only be used on the server side");
    }
    if (!PoolClass) {
      throw new Error("pg library is not available");
    }

    const config: ConnectionConfig =
      typeof connectionConfig === "string"
        ? { connectionString: connectionConfig }
        : connectionConfig;

    // Set reasonable defaults for connection pooling
    const poolConfig: ConnectionConfig = {
      ...config,
      max: config.max ?? 20,
      idleTimeoutMillis: config.idleTimeoutMillis ?? 30000,
      connectionTimeoutMillis: config.connectionTimeoutMillis ?? 2000,
    };

    this.pool = new PoolClass(poolConfig);

    // Handle pool errors
    this.pool.on("error", (err: Error) => {
      console.error("Database pool error:", err);
    });
  }

  async query(sql: string, params?: unknown[]): Promise<QueryResult> {
    try {
      const result: PgQueryResult<QueryResultRow> = await this.pool.query(
        sql,
        params,
      );
      return {
        rows: result.rows,
        rowCount: result.rowCount || 0,
        fields: result.fields,
      };
    } catch (error) {
      // Add context to the error before re-throwing
      throw new Error(
        `Database query failed: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      );
    }
  }

  async transaction<T>(
    callback: (client: DatabaseClient) => Promise<T>,
  ): Promise<T> {
    const poolClient: PoolClient = await this.pool.connect();
    try {
      await poolClient.query("BEGIN");
      // Create a transaction client wrapper
      const transactionClient: DatabaseClient = {
        query: async (sql: string, params?: unknown[]) => {
          const result: PgQueryResult<QueryResultRow> = await poolClient.query(
            sql,
            params,
          );
          return {
            rows: result.rows,
            rowCount: result.rowCount || 0,
            fields: result.fields,
          };
        },
        transaction: async () => {
          throw new Error("Nested transactions are not supported");
        },
      };

      const result = await callback(transactionClient);
      await poolClient.query("COMMIT");
      return result;
    } catch (error) {
      await poolClient.query("ROLLBACK");
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
  static create(
    type: "postgresql",
    config: string | ConnectionConfig,
  ): DatabaseClient {
    if (typeof window !== "undefined") {
      throw new Error("Database client can only be created on the server side");
    }

    switch (type) {
      case "postgresql":
        return new PostgreSQLClient(config);
      default:
        throw new Error(`Unsupported database client type: ${type}`);
    }
  }
}

// Singleton database client instance
let dbClient: DatabaseClient | null = null;

export function getDatabaseClient(): DatabaseClient {
  if (typeof window !== "undefined") {
    throw new Error("Database client can only be accessed on the server side");
  }

  if (!dbClient) {
    // Get database URL from environment
    const databaseUrl = process.env.DATABASE_URL || process.env.POSTGRES_URL;
    if (!databaseUrl) {
      throw new Error(
        "DATABASE_URL or POSTGRES_URL environment variable is required",
      );
    }

    try {
      dbClient = DatabaseClientFactory.create("postgresql", databaseUrl);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Database connection failed: ${message}`);
    }
  }

  return dbClient;
}

// Function to safely close the database connection
export async function closeDatabaseClient(): Promise<void> {
  if (dbClient && "close" in dbClient && typeof dbClient.close === "function") {
    await dbClient.close();
    dbClient = null;
  }
}

export function setDatabaseClient(client: DatabaseClient): void {
  dbClient = client;
}
