/**
 * Service Worker Registration
 * Manages service worker registration, updates, and communication
 */

'use client';

import { useState, useEffect } from 'react';

export interface ServiceWorkerConfig {
  enabled: boolean;
  scope: string;
  updateInterval: number;
  cacheName: string;
  cacheUrls: string[];
}

export interface ServiceWorkerMessage {
  type: string;
  payload?: unknown;
  id?: string;
}

export interface ServiceWorkerResponse {
  type: string;
  payload?: unknown;
  id?: string;
  success: boolean;
  error?: string;
}

class ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;
  private config: ServiceWorkerConfig;
  private messageListeners: Map<string, ((data: unknown) => void)> = new Map();
  private updateTimer: NodeJS.Timeout | null = null;

  constructor(config?: Partial<ServiceWorkerConfig>) {
    this.config = {
      enabled: true,
      scope: '/',
      updateInterval: 3600000, // 1 hour
      cacheName: 'karen-app-v1',
      cacheUrls: [
        '/',
        '/manifest.json',
        '/offline.html',
        ...['/static/js/', '/static/css/'].map(path => `${path}*`),
      ],
      ...config,
    };

    // Set up message listener
    this.setupMessageListener();
  }

  /**
   * Register service worker
   */
  async register(): Promise<boolean> {
    if (!this.config.enabled || !('serviceWorker' in navigator)) {
      console.warn('Service worker not supported or disabled');
      return false;
    }

    try {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: this.config.scope,
      });

      console.log('Service worker registered:', this.registration.scope);

      // Set up update checking
      this.setupUpdateChecking();

      // Set up initial cache
      await this.setupInitialCache();

      return true;
    } catch (error) {
      console.error('Service worker registration failed:', error);
      return false;
    }
  }

  /**
   * Unregister service worker
   */
  async unregister(): Promise<boolean> {
    if (!this.registration) {
      return true;
    }

    try {
      await this.registration.unregister();
      this.registration = null;
      
      // Clear update timer
      if (this.updateTimer) {
        clearInterval(this.updateTimer);
        this.updateTimer = null;
      }

      console.log('Service worker unregistered');
      return true;
    } catch (error) {
      console.error('Service worker unregistration failed:', error);
      return false;
    }
  }

  /**
   * Check if service worker is registered
   */
  isRegistered(): boolean {
    return this.registration !== null;
  }

  /**
   * Get current registration
   */
  getRegistration(): ServiceWorkerRegistration | null {
    return this.registration;
  }

  /**
   * Send message to service worker
   */
  async sendMessage(message: ServiceWorkerMessage): Promise<ServiceWorkerResponse> {
    if (!this.registration) {
      throw new Error('Service worker not registered');
    }

    return new Promise((resolve, reject) => {
      const messageId = message.id || this.generateId();
      const messageWithId = { ...message, id: messageId };

      // Set up response listener
      const responseListener = (event: MessageEvent) => {
        if (event.data.id === messageId) {
          navigator.serviceWorker.removeEventListener('message', responseListener);
          resolve(event.data);
        }
      };

      navigator.serviceWorker.addEventListener('message', responseListener);

      // Set timeout
      setTimeout(() => {
        navigator.serviceWorker.removeEventListener('message', responseListener);
        reject(new Error('Message timeout'));
      }, 5000);

      // Send message
      if (this.registration?.active) {
        this.registration.active.postMessage(messageWithId);
      } else {
        reject(new Error('Service worker not active'));
      }
    });
  }

  /**
   * Add message listener
   */
  addMessageListener(type: string, callback: (data: unknown) => void): () => void {
    this.messageListeners.set(type, callback);
    
    return () => {
      this.messageListeners.delete(type);
    };
  }

  /**
   * Remove message listener
   */
  removeMessageListener(type: string): void {
    this.messageListeners.delete(type);
  }

  /**
   * Force update service worker
   */
  async forceUpdate(): Promise<boolean> {
    if (!this.registration) {
      return false;
    }

    try {
      await this.registration.update();
      console.log('Service worker update triggered');
      return true;
    } catch (error) {
      console.error('Service worker update failed:', error);
      return false;
    }
  }

  /**
   * Setup message listener for service worker communications
   */
  private setupMessageListener(): void {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        const { type, payload } = event.data;

        if (type && this.messageListeners.has(type)) {
          const callback = this.messageListeners.get(type)!;
          try {
            callback(payload);
          } catch (error) {
            console.error(`Error in message listener for type ${type}:`, error);
          }
        }
      });
    }
  }

  /**
   * Set up automatic update checking
   */
  private setupUpdateChecking(): void {
    if (this.config.updateInterval > 0) {
      this.updateTimer = setInterval(() => {
        this.forceUpdate();
      }, this.config.updateInterval);
    }
  }

  /**
   * Set up initial cache
   */
  private async setupInitialCache(): Promise<void> {
    if (!('caches' in window)) {
      return;
    }

    try {
      const cache = await caches.open(this.config.cacheName);
      
      // Cache essential URLs
      const cachePromises = this.config.cacheUrls.map(async (url) => {
        try {
          await cache.add(new Request(url, { cache: 'no-store' }));
        } catch (error) {
          console.warn(`Failed to cache ${url}:`, error);
        }
      });

      await Promise.allSettled(cachePromises);
      console.log('Initial cache setup completed');
    } catch (error) {
      console.error('Initial cache setup failed:', error);
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  /**
   * Get service worker version
   */
  async getVersion(): Promise<string | null> {
    try {
      const response = await this.sendMessage({
        type: 'GET_VERSION',
      });
      
      return response.success ? (response.payload as string | null) : null;
    } catch (error) {
      console.error('Failed to get service worker version:', error);
      return null;
    }
  }

  /**
   * Clear cache
   */
  async clearCache(): Promise<boolean> {
    if (!('caches' in window)) {
      return false;
    }

    try {
      await caches.delete(this.config.cacheName);
      console.log('Cache cleared');
      return true;
    } catch (error) {
      console.error('Cache clear failed:', error);
      return false;
    }
  }

  /**
   * Get cache usage
   */
  async getCacheUsage(): Promise<{ usage: number; quota: number } | null> {
    if (!('storage' in navigator && 'estimate' in navigator.storage)) {
      return null;
    }

    try {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0,
      };
    } catch (error) {
      console.error('Failed to get cache usage:', error);
      return null;
    }
  }
}

// Singleton instance
let serviceWorkerManager: ServiceWorkerManager | null = null;

/**
 * Get or create service worker manager singleton
 */
export function getServiceWorkerManager(config?: Partial<ServiceWorkerConfig>): ServiceWorkerManager {
  if (!serviceWorkerManager) {
    serviceWorkerManager = new ServiceWorkerManager(config);
  }
  return serviceWorkerManager;
}

/**
 * Hook for React components to use service worker
 */
export function useServiceWorker(config?: Partial<ServiceWorkerConfig>) {
  const [isRegistered, setIsRegistered] = useState(false);
  const [version, setVersion] = useState<string | null>(null);
  const [cacheUsage, setCacheUsage] = useState<{ usage: number; quota: number } | null>(null);

  useEffect(() => {
    const manager = getServiceWorkerManager(config);
    
    // Register service worker
    manager.register().then(setIsRegistered);

    // Get version
    manager.getVersion().then(setVersion);

    // Get cache usage
    manager.getCacheUsage().then(setCacheUsage);

    // Set up version listener
    const unsubscribeVersion = manager.addMessageListener('VERSION_UPDATED', (newVersion) => {
      if (typeof newVersion === 'string') {
        setVersion(newVersion);
      }
    });

    return () => {
      unsubscribeVersion();
    };
  }, [config]);

  const manager = getServiceWorkerManager(config);

  return {
    isRegistered,
    version,
    cacheUsage,
    register: () => manager.register(),
    unregister: () => manager.unregister(),
    forceUpdate: () => manager.forceUpdate(),
    clearCache: () => manager.clearCache(),
    sendMessage: (message: ServiceWorkerMessage) => manager.sendMessage(message),
    addMessageListener: (type: string, callback: (data: unknown) => void) => 
      manager.addMessageListener(type, callback),
    removeMessageListener: (type: string) => manager.removeMessageListener(type),
  };
}

/**
 * Utility functions for common service worker operations
 */

/**
 * Check if service worker is supported
 */
export function isServiceWorkerSupported(): boolean {
  return 'serviceWorker' in navigator;
}

/**
 * Check if service worker is registered
 */
export async function isServiceWorkerRegistered(): Promise<boolean> {
  if (!isServiceWorkerSupported()) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    return registration !== undefined;
  } catch (error) {
    console.error('Failed to check service worker registration:', error);
    return false;
  }
}

/**
 * Wait for service worker to be ready
 */
export function waitForServiceWorker(): Promise<ServiceWorkerRegistration> {
  return new Promise((resolve, reject) => {
    if (!isServiceWorkerSupported()) {
      reject(new Error('Service worker not supported'));
      return;
    }

    navigator.serviceWorker.ready.then(resolve).catch(reject);
  });
}

/**
 * Get current service worker registration
 */
export async function getCurrentServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!isServiceWorkerSupported()) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    return registration || null;
  } catch (error) {
    console.error('Failed to get service worker registration:', error);
    return null;
  }
}
