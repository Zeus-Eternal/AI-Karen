/**
 * Database Connection Utility for KAREN Chat System
 * Provides PostgreSQL connection for Next.js API routes
 */

import { Pool, PoolClient } from 'pg';

// Database configuration from environment variables
const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'ai_karen',
  user: process.env.POSTGRES_USER || 'karen_user',
  password: process.env.POSTGRES_PASSWORD || '',
  max: parseInt(process.env.DB_POOL_SIZE || '10'),
  idleTimeoutMillis: parseInt(process.env.DB_POOL_TIMEOUT || '30000'),
  connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT || '45000'),
};

// Create connection pool
let pool: Pool;

/**
 * Initialize database connection pool
 */
export function initializeDatabase(): Pool {
  if (!pool) {
    pool = new Pool(dbConfig);
    
    // Handle pool errors
    pool.on('error', (err) => {
      console.error('Unexpected error on idle client', err);
    });
    
    console.log('Database connection pool initialized');
  }
  return pool;
}

/**
 * Get database connection pool
 */
export function getDatabasePool(): Pool {
  if (!pool) {
    return initializeDatabase();
  }
  return pool;
}

/**
 * Execute a database query with error handling
 */
export async function executeQuery<T = unknown>(
  text: string,
  params?: unknown[]
): Promise<{ rows: T[]; rowCount: number }> {
  const start = Date.now();
  const pool = getDatabasePool();
  let client: PoolClient | null = null;
  
  try {
    client = await pool.connect();
    const result = await client.query(text, params);
    const duration = Date.now() - start;
    
    // Log slow queries
    if (duration > 1000) {
      console.warn(`Slow query (${duration}ms): ${text.substring(0, 100)}...`);
    }
    
    return {
      rows: result.rows,
      rowCount: result.rowCount || 0,
    };
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  } finally {
    if (client) {
      client.release();
    }
  }
}

/**
 * Execute a database transaction
 */
export async function executeTransaction<T = unknown>(
  queries: Array<{ text: string; params?: unknown[] }>
): Promise<T[]> {
  const pool = getDatabasePool();
  let client: PoolClient | null = null;
  
  try {
    client = await pool.connect();
    await client.query('BEGIN');
    
    const results: T[] = [];
    for (const query of queries) {
      const result = await client.query(query.text, query.params);
      results.push(result.rows as T);
    }
    
    await client.query('COMMIT');
    return results;
  } catch (error) {
    if (client) {
      await client.query('ROLLBACK');
    }
    console.error('Database transaction error:', error);
    throw error;
  } finally {
    if (client) {
      client.release();
    }
  }
}

/**
 * Test database connection
 */
export async function testConnection(): Promise<boolean> {
  try {
    await executeQuery('SELECT 1');
    return true;
  } catch (error) {
    console.error('Database connection test failed:', error);
    return false;
  }
}

/**
 * Close database connection pool
 */
export async function closeDatabase(): Promise<void> {
  if (pool) {
    await pool.end();
    console.log('Database connection pool closed');
  }
}

// Initialize database on module import
initializeDatabase();