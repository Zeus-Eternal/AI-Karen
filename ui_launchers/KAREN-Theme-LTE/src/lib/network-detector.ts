/**
 * Network Detector Utility
 * Provides network status monitoring and connectivity detection
 */

'use client';

import { useState, useEffect } from 'react';

export interface NetworkStatus {
  online: boolean;
  effectiveType?: 'slow-2g' | '2g' | '3g' | '4g';
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

interface NetworkConnection {
  effectiveType?: 'slow-2g' | '2g' | '3g' | '4g';
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
  addEventListener: (event: string, listener: () => void) => void;
}

export interface NetworkDetectorOptions {
  onOnline?: () => void;
  onOffline?: () => void;
  onStatusChange?: (status: NetworkStatus) => void;
  pollInterval?: number;
}

export class NetworkDetector {
  private isOnline: boolean = true;
  private listeners: Set<(status: NetworkStatus) => void> = new Set();
  private pollInterval?: NodeJS.Timeout;
  private options: NetworkDetectorOptions;

  constructor(options: NetworkDetectorOptions = {}) {
    this.options = {
      pollInterval: 30000, // 30 seconds
      ...options,
    };

    // Initialize with current status
    this.isOnline = navigator.onLine;
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Start polling if requested
    if (this.options.pollInterval && this.options.pollInterval > 0) {
      this.startPolling();
    }
  }

  /**
   * Get current network status
   */
  getStatus(): NetworkStatus {
    const connection = this.getConnectionInfo();
    
    return {
      online: this.isOnline,
      ...connection,
    };
  }

  /**
   * Check if currently online
   */
  isCurrentlyOnline(): boolean {
    return this.isOnline;
  }

  /**
   * Add status change listener
   */
  addListener(listener: (status: NetworkStatus) => void): () => void {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Remove status change listener
   */
  removeListener(listener: (status: NetworkStatus) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Set up browser event listeners
   */
  private setupEventListeners(): void {
    // Online/offline events
    const handleOnline = () => {
      if (!this.isOnline) {
        this.isOnline = true;
        this.notifyListeners();
        this.options.onOnline?.();
      }
    };

    const handleOffline = () => {
      if (this.isOnline) {
        this.isOnline = false;
        this.notifyListeners();
        this.options.onOffline?.();
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Connection change events (if supported)
    const connection = this.getConnectionObject();
    if (connection) {
      const handleConnectionChange = () => {
        this.notifyListeners();
      };

      connection.addEventListener('change', handleConnectionChange);
    }
  }

  /**
   * Get connection information if available
   */
  private getConnectionObject(): NetworkConnection | null {
    const connection = (
      (navigator as unknown as { connection?: NetworkConnection }).connection ||
      (navigator as unknown as { mozConnection?: NetworkConnection }).mozConnection ||
      (navigator as unknown as { webkitConnection?: NetworkConnection }).webkitConnection
    );
    return connection || null;
  }

  /**
   * Get connection info
   */
  private getConnectionInfo(): Omit<NetworkStatus, 'online'> {
    const connection = this.getConnectionObject();
    
    if (!connection) {
      return {};
    }

    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData,
    };
  }

  /**
   * Notify all listeners of status change
   */
  private notifyListeners(): void {
    const status = this.getStatus();
    
    this.listeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in network status listener:', error);
      }
    });
    
    this.options.onStatusChange?.(status);
  }

  /**
   * Start polling for connectivity
   */
  private startPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }

    this.pollInterval = setInterval(async () => {
      const wasOnline = this.isOnline;
      
      try {
        // Try to fetch a small resource to check connectivity
        const response = await fetch('/api/health', {
          method: 'HEAD',
          cache: 'no-cache',
          signal: AbortSignal.timeout(5000),
        });
        
        const currentlyOnline = response.ok;
        
        if (wasOnline !== currentlyOnline) {
          this.isOnline = currentlyOnline;
          this.notifyListeners();
          
          if (currentlyOnline) {
            this.options.onOnline?.();
          } else {
            this.options.onOffline?.();
          }
        }
      } catch (error) {
        if (wasOnline) {
          this.isOnline = false;
          this.notifyListeners();
          this.options.onOffline?.();
        }
      }
    }, this.options.pollInterval);
  }

  /**
   * Stop polling
   */
  stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = undefined;
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopPolling();
    this.listeners.clear();
  }
}

// Singleton instance
let networkDetector: NetworkDetector | null = null;

/**
 * Get or create the network detector singleton
 */
export function getNetworkDetector(options?: NetworkDetectorOptions): NetworkDetector {
  if (!networkDetector) {
    networkDetector = new NetworkDetector(options);
  }
  return networkDetector;
}

/**
 * Hook for React components to use network status
 */
export function useNetworkStatus(options?: NetworkDetectorOptions): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>(() => 
    getNetworkDetector(options).getStatus()
  );

  useEffect(() => {
    const detector = getNetworkDetector(options);
    
    const unsubscribe = detector.addListener((newStatus) => {
      setStatus(newStatus);
    });

    return unsubscribe;
  }, [options]);

  return status;
}

/**
 * Utility functions for common network operations
 */

/**
 * Check if connection is fast enough for video
 */
export function isFastConnection(status: NetworkStatus): boolean {
  if (!status.effectiveType) return true; // Assume fast if unknown
  
  return ['4g', '3g'].includes(status.effectiveType);
}

/**
 * Check if connection is metered or limited
 */
export function isLimitedConnection(status: NetworkStatus): boolean {
  return Boolean(status.saveData || 
    (status.effectiveType && ['slow-2g', '2g'].includes(status.effectiveType)));
}

/**
 * Get recommended quality based on connection
 */
export function getRecommendedQuality(status: NetworkStatus): 'high' | 'medium' | 'low' {
  if (!status.effectiveType) return 'high';
  
  switch (status.effectiveType) {
    case '4g':
      return 'high';
    case '3g':
      return 'medium';
    case '2g':
    case 'slow-2g':
      return 'low';
    default:
      return 'medium';
  }
}

/**
 * Check if online with retry logic
 */
export async function checkOnlineStatus(maxRetries: number = 3): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache',
        signal: AbortSignal.timeout(3000),
      });
      
      if (response.ok) {
        return true;
      }
    } catch (error) {
      if (i === maxRetries - 1) {
        return false;
      }
      
      // Exponential backoff
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, i) * 1000)
      );
    }
  }
  
  return false;
}