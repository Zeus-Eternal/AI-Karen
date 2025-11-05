/**
 * HTTP Connection Pool Manager
 * 
 * Implements connection pooling and keep-alive for HTTP requests to improve performance.
 * Provides connection reuse, request queuing, and connection lifecycle management.
 * 
 * Requirements: 1.4, 4.4
 */
import { getEnvironmentConfigManager } from '../config/index';
import { getTimeoutManager, OperationType } from '../connection/timeout-manager';

export interface ConnectionPoolConfig {
  maxConnections: number;
  maxConnectionsPerHost: number;
  connectionTimeout: number;
  keepAliveTimeout: number;
  maxIdleTime: number;
  enableKeepAlive: boolean;
  enableHttp2: boolean;
  retryOnConnectionFailure: boolean;
}

export interface ConnectionMetrics {
  totalConnections: number;
  activeConnections: number;
  idleConnections: number;
  queuedRequests: number;
  connectionReuse: number;
  connectionCreations: number;
  connectionTimeouts: number;
  averageConnectionTime: number;
  averageRequestTime: number;
}

export interface PooledConnection {
  id: string;
  url: string;
  createdAt: Date;
  lastUsed: Date;
  requestCount: number;
  isActive: boolean;
  controller: AbortController;
}

export interface QueuedRequest {
  id: string;
  url: string;
  options: RequestInit;
  resolve: (response: Response) => void;
  reject: (error: Error) => void;
  queuedAt: Date;
  timeout: number;
}

/**
 * HTTP Connection Pool Manager
 * 
 * Manages a pool of HTTP connections with keep-alive support for improved performance.
 */
export class HttpConnectionPool {
  private config: ConnectionPoolConfig;
  private connections: Map<string, PooledConnection[]> = new Map();
  private requestQueue: QueuedRequest[] = [];
  private metrics: ConnectionMetrics;
  private cleanupInterval: NodeJS.Timeout | null = null;
  private isShuttingDown = false;

  constructor(config?: Partial<ConnectionPoolConfig>) {
    this.config = {
      maxConnections: 50,
      maxConnectionsPerHost: 10,
      connectionTimeout: 30000,
      keepAliveTimeout: 60000,
      maxIdleTime: 300000, // 5 minutes
      enableKeepAlive: true,
      enableHttp2: false, // Not widely supported in browsers yet
      retryOnConnectionFailure: true,
      ...config,
    };

    this.metrics = {
      totalConnections: 0,
      activeConnections: 0,
      idleConnections: 0,
      queuedRequests: 0,
      connectionReuse: 0,
      connectionCreations: 0,
      connectionTimeouts: 0,
      averageConnectionTime: 0,
      averageRequestTime: 0,
    };
    
    this.startCleanupTimer();
  }

  /**
   * Make an HTTP request using the connection pool
   */
  async request(url: string, options: RequestInit = {}): Promise<Response> {
    const startTime = Date.now();
    const host = this.getHostFromUrl(url);

    try {
      // Try to get an existing connection
      let connection = this.getAvailableConnection(host);
      if (!connection) {
        // Check if we can create a new connection
        if (this.canCreateNewConnection(host)) {
          connection = await this.createConnection(host, url);
        } else {
          // Queue the request if pool is full
          return this.queueRequest(url, options);
        }
      }

      // Mark connection as active
      connection.isActive = true;
      connection.lastUsed = new Date();
      connection.requestCount++;
      this.metrics.activeConnections++;
      this.metrics.connectionReuse++;

      // Configure request with keep-alive headers
      const requestOptions = this.configureRequestOptions(options, connection);
      // Make the request
      const response = await fetch(url, requestOptions);

      // Update metrics
      const requestTime = Date.now() - startTime;
      this.updateRequestMetrics(requestTime);

      // Mark connection as idle
      connection.isActive = false;
      this.metrics.activeConnections--;
      this.metrics.idleConnections++;

      // Process queued requests if any
      this.processQueuedRequests();

      return response;
    } catch (error) {
      // Handle connection errors
      this.handleConnectionError(host, error as Error);
      throw error;
    }
  }

  /**
   * Get connection pool metrics
   */
  getMetrics(): ConnectionMetrics {
    this.updateConnectionCounts();
    return { ...this.metrics };
  }

  /**
   * Get connection pool configuration
   */
  getConfig(): ConnectionPoolConfig {
    return { ...this.config };
  }

  /**
   * Shutdown the connection pool
   */
  async shutdown(): Promise<void> {
    this.isShuttingDown = true;

    // Stop cleanup timer
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }

    // Abort all active connections
    for (const hostConnections of this.connections.values()) {
      for (const connection of hostConnections) {
        if (connection.isActive) {
          connection.controller.abort();
        }
      }
    }

    // Reject all queued requests
    for (const queuedRequest of this.requestQueue) {
      queuedRequest.reject(new Error('Connection pool shutting down'));
    }

    // Clear all data structures
    this.connections.clear();
    this.requestQueue.length = 0;
  }

  /**
   * Get available connection for host
   */
  private getAvailableConnection(host: string): PooledConnection | null {
    const hostConnections = this.connections.get(host) || [];

    // Find an idle connection
    for (const connection of hostConnections) {
      if (!connection.isActive && !this.isConnectionExpired(connection)) {
        return connection;
      }
    }

    return null;
  }

  /**
   * Check if we can create a new connection
   */
  private canCreateNewConnection(host: string): boolean {
    if (this.isShuttingDown) {
      return false;
    }

    const hostConnections = this.connections.get(host) || [];
    const totalConnections = Array.from(this.connections.values())
      .reduce((sum, conns) => sum + conns.length, 0);

    return (
      hostConnections.length < this.config.maxConnectionsPerHost &&
      totalConnections < this.config.maxConnections
    );
  }

  /**
   * Create a new connection
   */
  private async createConnection(host: string, url: string): Promise<PooledConnection> {
    const connection: PooledConnection = {
      id: `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      url: host,
      createdAt: new Date(),
      lastUsed: new Date(),
      requestCount: 0,
      isActive: false,
      controller: new AbortController(),
    };

    // Add to connections map
    if (!this.connections.has(host)) {
      this.connections.set(host, []);
    }

    this.connections.get(host)!.push(connection);

    // Update metrics
    this.metrics.connectionCreations++;
    this.metrics.totalConnections++;

    return connection;
  }

  /**
   * Queue a request when pool is full
   */
  private async queueRequest(url: string, options: RequestInit): Promise<Response> {
    return new Promise((resolve, reject) => {
      const queuedRequest: QueuedRequest = {
        id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        url,
        options,
        resolve,
        reject,
        queuedAt: new Date(),
        timeout: this.config.connectionTimeout,
      };

      this.requestQueue.push(queuedRequest);
      this.metrics.queuedRequests++;

      // Set timeout for queued request
      setTimeout(() => {
        const index = this.requestQueue.indexOf(queuedRequest);
        if (index !== -1) {
          this.requestQueue.splice(index, 1);
          this.metrics.queuedRequests--;
          reject(new Error('Request timeout in queue'));
        }
      }, queuedRequest.timeout);
    });
  }

  /**
   * Process queued requests
   */
  private processQueuedRequests(): void {
    if (this.requestQueue.length === 0) {
      return;
    }

    // Process requests in FIFO order
    const request = this.requestQueue.shift();
    if (request) {
      this.metrics.queuedRequests--;

      // Retry the request
      this.request(request.url, request.options)
        .then(request.resolve)
        .catch(request.reject);
    }
  }

  /**
   * Configure request options with keep-alive headers
   */
  private configureRequestOptions(options: RequestInit, connection: PooledConnection): RequestInit {
    const headers = new Headers(options.headers);
    if (this.config.enableKeepAlive) {
      headers.set('Connection', 'keep-alive');
      const timeoutSeconds = Math.floor(this.config.keepAliveTimeout / 1000);
      headers.set('Keep-Alive', `timeout=${timeoutSeconds}, max=100`);
    }

    if (!headers.has('Cache-Control')) {
      headers.set('Cache-Control', 'no-cache');
    }

    return {
      ...options,
      headers,
      signal: connection.controller.signal,
    };
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(host: string, error: Error): void {
    // Remove failed connections
    const hostConnections = this.connections.get(host) || [];
    const validConnections = hostConnections.filter(conn => !conn.isActive);
    if (validConnections.length !== hostConnections.length) {
      this.connections.set(host, validConnections);
      this.metrics.connectionTimeouts++;
    }
  }

  /**
   * Check if connection is expired
   */
  private isConnectionExpired(connection: PooledConnection): boolean {
    const now = Date.now();
    const lastUsed = connection.lastUsed.getTime();
    const maxIdleTime = this.config.maxIdleTime;
    return (now - lastUsed) > maxIdleTime;
  }

  /**
   * Get host from URL
   */
  private getHostFromUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      return `${urlObj.protocol}//${urlObj.host}`;
    } catch {
      // Fallback for relative URLs
      return 'localhost';
    }
  }

  /**
   * Update connection counts
   */
  private updateConnectionCounts(): void {
    let totalConnections = 0;
    let activeConnections = 0;
    let idleConnections = 0;

    for (const hostConnections of this.connections.values()) {
      for (const connection of hostConnections) {
        totalConnections++;
        if (connection.isActive) {
          activeConnections++;
        } else {
          idleConnections++;
        }
      }
    }

    this.metrics.totalConnections = totalConnections;
    this.metrics.activeConnections = activeConnections;
    this.metrics.idleConnections = idleConnections;
    this.metrics.queuedRequests = this.requestQueue.length;
  }

  /**
   * Update request metrics
   */
  private updateRequestMetrics(requestTime: number): void {
    const alpha = 0.1; // Smoothing factor
    this.metrics.averageRequestTime = 
      this.metrics.averageRequestTime * (1 - alpha) + requestTime * alpha;
  }

  /**
   * Start cleanup timer for expired connections
   */
  private startCleanupTimer(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredConnections();
    }, 60000); // Run every minute
  }

  /**
   * Cleanup expired connections
   */
  private cleanupExpiredConnections(): void {
    if (this.isShuttingDown) {
      return;
    }

    for (const [host, hostConnections] of this.connections.entries()) {
      const validConnections = hostConnections.filter(connection => {
        if (connection.isActive) {
          return true; // Keep active connections
        }
        if (this.isConnectionExpired(connection)) {
          // Abort expired connection
          connection.controller.abort();
          return false;
        }
        return true;
      });

      if (validConnections.length !== hostConnections.length) {
        this.connections.set(host, validConnections);
      }

      // Remove empty host entries
      if (validConnections.length === 0) {
        this.connections.delete(host);
      }
    }
  }
}

// Global connection pool instance
let connectionPool: HttpConnectionPool | null = null;

/**
 * Get the global HTTP connection pool instance
 */
export function getHttpConnectionPool(): HttpConnectionPool {
  if (!connectionPool) {
    // Get configuration from environment
    const configManager = getEnvironmentConfigManager();
    const timeoutManager = getTimeoutManager();
    const config: Partial<ConnectionPoolConfig> = {
      connectionTimeout: timeoutManager.getTimeout(OperationType.CONNECTION),
      keepAliveTimeout: 60000,
      maxConnections: 50,
      maxConnectionsPerHost: 10,
      enableKeepAlive: true,
    };
    connectionPool = new HttpConnectionPool(config);
  }
  return connectionPool;
}

/**
 * Initialize HTTP connection pool with custom configuration
 */
export function initializeHttpConnectionPool(config?: Partial<ConnectionPoolConfig>): HttpConnectionPool {
  if (connectionPool) {
    connectionPool.shutdown();
  }
  connectionPool = new HttpConnectionPool(config);
  return connectionPool;
}

/**
 * Shutdown the global HTTP connection pool
 */
export async function shutdownHttpConnectionPool(): Promise<void> {
  if (connectionPool) {
    await connectionPool.shutdown();
    connectionPool = null;
  }
}
