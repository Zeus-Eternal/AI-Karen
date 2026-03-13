/**
 * Production Service Worker for AI-Karen
 * 
 * Provides offline caching, performance optimizations, and
 * background sync capabilities for enhanced user experience.
 */

const CACHE_NAME = 'ai-karen-v1';
const STATIC_CACHE = 'ai-karen-static-v1';
const DYNAMIC_CACHE = 'ai-karen-dynamic-v1';
const API_CACHE = 'ai-karen-api-v1';

// Cache configuration
const CACHE_CONFIG = {
  static: {
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    maxEntries: 100,
  },
  dynamic: {
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    maxEntries: 50,
  },
  api: {
    maxAge: 5 * 60 * 1000, // 5 minutes
    maxEntries: 20,
  },
};

// Critical static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/_next/static/css/',
  '/_next/static/chunks/',
  '/fonts/',
  '/icons/',
];

// API routes to cache
const API_ROUTES = [
  '/api/chat',
  '/api/user',
  '/api/settings',
];

// Network-first routes (never cache)
const NETWORK_FIRST_ROUTES = [
  '/api/auth/login',
  '/api/auth/logout',
  '/api/auth/register',
];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('📦 Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => 
              cacheName !== CACHE_NAME && 
              cacheName !== STATIC_CACHE && 
              cacheName !== DYNAMIC_CACHE && 
              cacheName !== API_CACHE
            )
            .map((cacheName) => {
              console.log(`🗑️  Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

/**
 * Fetch event - handle network requests with caching strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') return;
  
  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') return;
  
  // Determine caching strategy
  if (NETWORK_FIRST_ROUTES.some(route => url.pathname.startsWith(route))) {
    event.respondWith(networkFirst(request));
  } else if (API_ROUTES.some(route => url.pathname.startsWith(route))) {
    event.respondWith(staleWhileRevalidate(request, API_CACHE));
  } else if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else {
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
  }
});

/**
 * Network-first strategy for critical routes
 */
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📡 Network failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    return cachedResponse || createOfflineResponse(request);
  }
}

/**
 * Cache-first strategy for static assets
 */
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // Check if cache is stale
    const dateHeader = cachedResponse.headers.get('date');
    if (dateHeader) {
      const cacheAge = Date.now() - new Date(dateHeader).getTime();
      const maxAge = cacheName === STATIC_CACHE ? 
        CACHE_CONFIG.static.maxAge : 
        CACHE_CONFIG.dynamic.maxAge;
      
      if (cacheAge > maxAge) {
        // Cache is stale, fetch fresh version
        try {
          const networkResponse = await fetch(request);
          if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
          }
          return networkResponse;
        } catch (error) {
          // Network failed, return stale cache
          return cachedResponse;
        }
      }
    }
    
    return cachedResponse;
  }
  
  // Not in cache, fetch from network
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('📡 Network failed:', error);
    return createOfflineResponse(request);
  }
}

/**
 * Stale-while-revalidate strategy
 */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  
  // Always try to fetch fresh version
  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch((error) => {
      console.log('📡 Network failed for stale-while-revalidate:', error);
      return null;
    });
  
  // Return cached version immediately if available
  if (cachedResponse) {
    // Revalidate in background
    fetchPromise.then((networkResponse) => {
      if (networkResponse && networkResponse.ok) {
        console.log('🔄 Updated cache for:', request.url);
      }
    });
    
    return cachedResponse;
  }
  
  // No cache available, wait for network
  return fetchPromise.then((networkResponse) => {
    return networkResponse || createOfflineResponse(request);
  });
}

/**
 * Check if request is for a static asset
 */
function isStaticAsset(request) {
  const url = new URL(request.url);
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.woff', '.woff2'];
  return staticExtensions.some(ext => url.pathname.endsWith(ext)) ||
         url.pathname.includes('/_next/static/') ||
         url.pathname.includes('/fonts/') ||
         url.pathname.includes('/icons/');
}

/**
 * Create offline response
 */
function createOfflineResponse(request) {
  const url = new URL(request.url);
  
  if (url.pathname === '/') {
    // Return offline page for navigation requests
    return new Response(
      `<!DOCTYPE html>
      <html>
        <head>
          <title>Offline - AI-Karen</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              display: flex; 
              align-items: center; 
              justify-content: center; 
              min-height: 100vh; 
              margin: 0; 
              background: #f8fafc;
              color: #1e293b;
              text-align: center;
            }
            .container { 
              max-width: 400px; 
              padding: 2rem; 
              background: white; 
              border-radius: 0.5rem; 
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            h1 { margin: 0 0 1rem 0; color: #3b82f6; }
            p { margin: 0 0 1.5rem 0; line-height: 1.6; }
            button { 
              background: #3b82f6; 
              color: white; 
              border: none; 
              padding: 0.75rem 1.5rem; 
              border-radius: 0.375rem; 
              cursor: pointer;
              font-size: 1rem;
            }
            button:hover { background: #2563eb; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>📱 You're Offline</h1>
            <p>It looks like you've lost your internet connection. Some features may not be available until you're back online.</p>
            <button onclick="window.location.reload()">Try Again</button>
          </div>
        </body>
      </html>`,
      {
        status: 200,
        statusText: 'OK',
        headers: {
          'Content-Type': 'text/html',
          'Cache-Control': 'no-cache',
        },
      }
    );
  }
  
  // Return 404 for other requests
  return new Response('Offline - Resource not available', {
    status: 404,
    statusText: 'Offline',
  });
}

/**
 * Background sync for offline actions
 */
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

/**
 * Handle background sync
 */
async function doBackgroundSync() {
  // Get all pending requests from IndexedDB
  const pendingRequests = await getPendingRequests();
  
  // Retry each request
  for (const request of pendingRequests) {
    try {
      const response = await fetch(request.url, request.options);
      if (response.ok) {
        await removePendingRequest(request.id);
        console.log('✅ Synced request:', request.url);
      }
    } catch (error) {
      console.log('❌ Failed to sync request:', request.url, error);
    }
  }
}

/**
 * Push notification handler
 */
self.addEventListener('push', (event) => {
  console.log('📬 Push notification received:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'New message from AI-Karen',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: '/',
      timestamp: Date.now(),
    },
    actions: [
      {
        action: 'open',
        title: 'Open App',
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
      },
    ],
  };
  
  event.waitUntil(
    self.registration.showNotification('AI-Karen', options)
  );
});

/**
 * Notification click handler
 */
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url || '/')
    );
  }
});

/**
 * IndexedDB helpers for offline queue
 */
async function getPendingRequests() {
  // Simplified implementation - in production, use proper IndexedDB
  return [];
}

async function removePendingRequest(id) {
  // Simplified implementation - in production, use proper IndexedDB
  return true;
}

/**
 * Cache cleanup utility
 */
async function cleanupCache(cacheName, maxEntries, maxAge) {
  const cache = await caches.open(cacheName);
  const requests = await cache.keys();
  
  // Remove old entries
  const now = Date.now();
  for (const request of requests) {
    const response = await cache.match(request);
    if (response) {
      const dateHeader = response.headers.get('date');
      if (dateHeader) {
        const cacheAge = now - new Date(dateHeader).getTime();
        if (cacheAge > maxAge) {
          await cache.delete(request);
        }
      }
    }
  }
  
  // Remove excess entries
  const remainingRequests = await cache.keys();
  if (remainingRequests.length > maxEntries) {
    const toDelete = remainingRequests.slice(maxEntries);
    await Promise.all(toDelete.map(request => cache.delete(request)));
  }
}

// Periodic cache cleanup
setInterval(() => {
  cleanupCache(STATIC_CACHE, CACHE_CONFIG.static.maxEntries, CACHE_CONFIG.static.maxAge);
  cleanupCache(DYNAMIC_CACHE, CACHE_CONFIG.dynamic.maxEntries, CACHE_CONFIG.dynamic.maxAge);
  cleanupCache(API_CACHE, CACHE_CONFIG.api.maxEntries, CACHE_CONFIG.api.maxAge);
}, 60 * 60 * 1000); // Every hour

console.log('🚀 AI-Karen Service Worker loaded');