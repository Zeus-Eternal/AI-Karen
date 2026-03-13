/**
 * Service Worker Registration
 * 
 * Handles service worker registration, updates, and
 * communication for offline capabilities.
 */

export interface ServiceWorkerConfig {
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onError?: (error: Error) => void;
}

export class ServiceWorkerManager {
  private swUrl: string;
  private config: ServiceWorkerConfig;
  private registration: ServiceWorkerRegistration | null = null;

  constructor(swUrl = '/sw.js', config: ServiceWorkerConfig = {}) {
    this.swUrl = swUrl;
    this.config = config;
  }

  /**
   * Register the service worker
   */
  async register(): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported in this browser');
      return null;
    }

    if (process.env.NODE_ENV !== 'production') {
      console.log('Service Worker registration skipped in development');
      return null;
    }

    try {
      console.log('🔧 Registering Service Worker...');
      
      this.registration = await navigator.serviceWorker.register(this.swUrl, {
        scope: '/',
      });

      console.log('✅ Service Worker registered successfully:', this.registration.scope);

      // Handle updates
      this.registration.addEventListener('updatefound', () => {
        this.handleUpdateFound();
      });

      // Handle controller change
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        this.handleControllerChange();
      });

      // Check for existing waiting service worker
      if (this.registration.waiting) {
        this.handleWaitingWorker(this.registration.waiting);
      }

      this.config.onSuccess?.(this.registration);
      return this.registration;

    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
      this.config.onError?.(error as Error);
      return null;
    }
  }

  /**
   * Unregister the service worker
   */
  async unregister(): Promise<boolean> {
    if (!this.registration) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        this.registration = registration;
      } else {
        return true; // No registration to unregister
      }
    }

    try {
      const unregistered = await this.registration.unregister();
      console.log(unregistered ? '✅ Service Worker unregistered' : '❌ Failed to unregister Service Worker');
      this.registration = null;
      return unregistered;
    } catch (error) {
      console.error('❌ Error unregistering Service Worker:', error);
      return false;
    }
  }

  /**
   * Get current registration
   */
  getRegistration(): ServiceWorkerRegistration | null {
    return this.registration;
  }

  /**
   * Check if service worker is active
   */
  isActive(): boolean {
    return !!navigator.serviceWorker.controller;
  }

  /**
   * Handle service worker update found
   */
  private handleUpdateFound(): void {
    const newWorker = this.registration?.installing;
    if (!newWorker) return;

    console.log('🔄 New Service Worker found');

    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        // New worker is installed but waiting
        this.handleWaitingWorker(newWorker);
      }
    });
  }

  /**
   * Handle waiting service worker
   */
  private handleWaitingWorker(worker: ServiceWorker): void {
    console.log('⏳ Service Worker waiting for activation');
    
    // Show update notification to user
    this.showUpdateNotification(() => {
      // Tell the waiting worker to skip waiting
      worker.postMessage({ type: 'SKIP_WAITING' });
    });
  }

  /**
   * Handle controller change (new service worker activated)
   */
  private handleControllerChange(): void {
    console.log('🚀 Service Worker controller changed');
    
    // Reload the page to get the new version
    window.location.reload();
  }

  /**
   * Show update notification to user
   */
  private showUpdateNotification(onAccept: () => void): void {
    // Create notification element
    const notification = document.createElement('div');
    notification.id = 'sw-update-notification';
    notification.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #3b82f6;
      color: white;
      padding: 16px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      max-width: 300px;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s ease;
    `;

    notification.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <strong>New version available</strong>
          <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">
            Refresh to get the latest updates
          </div>
        </div>
        <button id="sw-update-btn" style="
          background: white;
          color: #3b82f6;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          margin-left: 12px;
        ">Refresh</button>
      </div>
    `;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateY(0)';
      notification.style.opacity = '1';
    }, 100);

    // Handle button click
    const button = notification.querySelector('#sw-update-btn');
    button?.addEventListener('click', () => {
      onAccept();
      this.hideUpdateNotification();
    });

    // Auto-hide after 30 seconds
    setTimeout(() => {
      this.hideUpdateNotification();
    }, 30000);
  }

  /**
   * Hide update notification
   */
  private hideUpdateNotification(): void {
    const notification = document.getElementById('sw-update-notification');
    if (notification) {
      notification.style.transform = 'translateY(100px)';
      notification.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }
  }

  /**
   * Send message to service worker
   */
  postMessage(message: any): void {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage(message);
    }
  }

  /**
   * Listen for messages from service worker
   */
  addMessageListener(callback: (event: MessageEvent) => void): () => void {
    const handler = (event: MessageEvent) => callback(event);
    navigator.serviceWorker.addEventListener('message', handler);
    
    return () => {
      navigator.serviceWorker.removeEventListener('message', handler);
    };
  }

  /**
   * Request background sync
   */
  async requestBackgroundSync(tag: string): Promise<boolean> {
    if (!this.registration) return false;

    try {
      // Check if background sync is supported
      if (!('sync' in this.registration)) {
        console.warn('Background sync not supported');
        return false;
      }

      const syncManager = (this.registration as any).sync;
      const registration = await syncManager.register(tag);
      console.log('🔄 Background sync registered:', tag);
      return true;
    } catch (error) {
      console.error('❌ Failed to register background sync:', error);
      return false;
    }
  }

  /**
   * Subscribe to push notifications
   */
  async subscribeToPush(): Promise<PushSubscription | null> {
    if (!this.registration) return null;

    try {
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''
        ).buffer as ArrayBuffer,
      });

      console.log('🔔 Push subscription created:', subscription);
      return subscription;
    } catch (error) {
      console.error('❌ Failed to subscribe to push:', error);
      return null;
    }
  }

  /**
   * Convert URL base64 to Uint8Array
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
  }
}

// Singleton instance
let swManager: ServiceWorkerManager | null = null;

/**
 * Initialize service worker with default configuration
 */
export function initServiceWorker(config: ServiceWorkerConfig = {}): ServiceWorkerManager {
  if (!swManager) {
    swManager = new ServiceWorkerManager('/sw.js', config);
  }
  
  // Register when page loads
  if (document.readyState === 'complete') {
    swManager!.register();
  } else {
    window.addEventListener('load', () => {
      swManager!.register();
    });
  }

  return swManager;
}

/**
 * Get service worker manager instance
 */
export function getServiceWorkerManager(): ServiceWorkerManager | null {
  return swManager;
}

/**
 * Check if service worker is supported
 */
export function isServiceWorkerSupported(): boolean {
  return 'serviceWorker' in navigator;
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.warn('Notifications not supported');
    return 'denied';
  }

  if (Notification.permission === 'granted') {
    return 'granted';
  }

  try {
    const permission = await Notification.requestPermission();
    console.log('🔔 Notification permission:', permission);
    return permission;
  } catch (error) {
    console.error('❌ Error requesting notification permission:', error);
    return 'denied';
  }
}