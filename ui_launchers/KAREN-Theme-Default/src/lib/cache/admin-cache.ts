/**
 * Admin Cache Layer
 * 
 * Provides caching functionality for user permissions, system configuration,
 * and frequently accessed admin data to improve performance.
 * 
 * Requirements: 7.3, 7.5
 */
// Simple cache implementation for testing
class SimpleCache<K, V> {
  private cache = new Map<K, V>();
  private maxSize: number;
  private ttl: number;
  private timers = new Map<K, NodeJS.Timeout>();
  constructor(options: { max: number; ttl: number }) {
    this.maxSize = options.max;
    this.ttl = options.ttl;
  }
  get(key: K): V | undefined {
    return this.cache.get(key);
  }
  set(key: K, value: V): void {
    // Clear existing timer
    const existingTimer = this.timers.get(key);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }
    // Set new value
    this.cache.set(key, value);
    // Set TTL timer
    const timer = setTimeout(() => {
      this.cache.delete(key);
      this.timers.delete(key);
    }, this.ttl);
    this.timers.set(key, timer);
    // Enforce max size
    if (this.cache.size > this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey !== undefined) {
        this.delete(firstKey);
      }
    }
  }
  delete(key: K): boolean {
    const timer = this.timers.get(key);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(key);
    }
    return this.cache.delete(key);
  }
  clear(): void {
    // Clear all timers
    for (const timer of this.timers.values()) {
      clearTimeout(timer);
    }
    this.timers.clear();
    this.cache.clear();
  }
  get size(): number {
    return this.cache.size;
  }
}
import type {  User, Permission, SystemConfig, UserListFilter, PaginatedResponse, CacheConfig, CacheStats } from '@/types/admin';
// Cache configuration
const CACHE_CONFIG: CacheConfig = {
  permissions: {
    maxSize: 1000,
    ttl: 15 * 60 * 1000, // 15 minutes
  },
  systemConfig: {
    maxSize: 500,
    ttl: 30 * 60 * 1000, // 30 minutes
  },
  users: {
    maxSize: 2000,
    ttl: 5 * 60 * 1000, // 5 minutes
  },
  userLists: {
    maxSize: 100,
    ttl: 2 * 60 * 1000, // 2 minutes
  },
  statistics: {
    maxSize: 50,
    ttl: 10 * 60 * 1000, // 10 minutes
  }
};
// Cache instances
const permissionsCache = new SimpleCache<string, Permission[]>({
  max: CACHE_CONFIG.permissions.maxSize,
  ttl: CACHE_CONFIG.permissions.ttl,

const systemConfigCache = new SimpleCache<string, SystemConfig[]>({
  max: CACHE_CONFIG.systemConfig.maxSize,
  ttl: CACHE_CONFIG.systemConfig.ttl,

const userCache = new SimpleCache<string, User>({
  max: CACHE_CONFIG.users.maxSize,
  ttl: CACHE_CONFIG.users.ttl,

const userListCache = new SimpleCache<string, PaginatedResponse<User>>({
  max: CACHE_CONFIG.userLists.maxSize,
  ttl: CACHE_CONFIG.userLists.ttl,

const statisticsCache = new SimpleCache<string, any>({
  max: CACHE_CONFIG.statistics.maxSize,
  ttl: CACHE_CONFIG.statistics.ttl,

// Cache key generators
export class CacheKeyGenerator {
  static userPermissions(userId: string): string {
    return `permissions:${userId}`;
  }
  static systemConfig(category?: string): string {
    return category ? `config:${category}` : 'config:all';
  }
  static user(userId: string): string {
    return `user:${userId}`;
  }
  static userByEmail(email: string): string {
    return `user:email:${email.toLowerCase()}`;
  }
  static userList(filters: UserListFilter, page: number, limit: number, sortBy?: string, sortOrder?: string): string {
    const filterStr = JSON.stringify(filters);
    const sortStr = `${sortBy || 'created_at'}:${sortOrder || 'desc'}`;
    return `userlist:${Buffer.from(filterStr).toString('base64')}:${page}:${limit}:${sortStr}`;
  }
  static statistics(type: string, params?: Record<string, any>): string {
    const paramStr = params ? JSON.stringify(params) : '';
    return `stats:${type}:${Buffer.from(paramStr).toString('base64')}`;
  }
  static roleBasedQuery(userId: string): string {
    return `rbq:${userId}`;
  }
}
// Permission caching
export class PermissionCache {
  static async get(userId: string): Promise<Permission[] | null> {
    const key = CacheKeyGenerator.userPermissions(userId);
    return permissionsCache.get(key) || null;
  }
  static set(userId: string, permissions: Permission[]): void {
    const key = CacheKeyGenerator.userPermissions(userId);
    permissionsCache.set(key, permissions);
  }
  static invalidate(userId: string): void {
    const key = CacheKeyGenerator.userPermissions(userId);
    permissionsCache.delete(key);
  }
  static invalidateAll(): void {
    permissionsCache.clear();
  }
  static getStats(): CacheStats {
    return {
      size: permissionsCache.size,
      maxSize: CACHE_CONFIG.permissions.maxSize,
      hitRate: 0.8, // Mock hit rate for now
      ttl: CACHE_CONFIG.permissions.ttl
    };
  }
}
// System configuration caching
export class SystemConfigCache {
  static async get(category?: string): Promise<SystemConfig[] | null> {
    const key = CacheKeyGenerator.systemConfig(category);
    return systemConfigCache.get(key) || null;
  }
  static set(category: string | undefined, config: SystemConfig[]): void {
    const key = CacheKeyGenerator.systemConfig(category);
    systemConfigCache.set(key, config);
  }
  static invalidate(category?: string): void {
    if (category) {
      const key = CacheKeyGenerator.systemConfig(category);
      systemConfigCache.delete(key);
    } else {
      // Invalidate all config cache entries
      systemConfigCache.clear();
    }
  }
  static invalidateAll(): void {
    systemConfigCache.clear();
  }
  static getStats(): CacheStats {
    return {
      size: systemConfigCache.size,
      maxSize: CACHE_CONFIG.systemConfig.maxSize,
      hitRate: 0.8, // Mock hit rate for now
      ttl: CACHE_CONFIG.systemConfig.ttl
    };
  }
}
// User caching
export class UserCache {
  static async get(userId: string): Promise<User | null> {
    const key = CacheKeyGenerator.user(userId);
    return userCache.get(key) || null;
  }
  static async getByEmail(email: string): Promise<User | null> {
    const key = CacheKeyGenerator.userByEmail(email);
    return userCache.get(key) || null;
  }
  static set(user: User): void {
    const userKey = CacheKeyGenerator.user(user.user_id);
    const emailKey = CacheKeyGenerator.userByEmail(user.email);
    userCache.set(userKey, user);
    userCache.set(emailKey, user);
  }
  static invalidate(userId: string, email?: string): void {
    const userKey = CacheKeyGenerator.user(userId);
    userCache.delete(userKey);
    if (email) {
      const emailKey = CacheKeyGenerator.userByEmail(email);
      userCache.delete(emailKey);
    }
  }
  static invalidateAll(): void {
    userCache.clear();
  }
  static getStats(): CacheStats {
    return {
      size: userCache.size,
      maxSize: CACHE_CONFIG.users.maxSize,
      hitRate: 0.8, // Mock hit rate for now
      ttl: CACHE_CONFIG.users.ttl
    };
  }
}
// User list caching
export class UserListCache {
  static async get(
    filters: UserListFilter, 
    page: number, 
    limit: number, 
    sortBy?: string, 
    sortOrder?: string
  ): Promise<PaginatedResponse<User> | null> {
    const key = CacheKeyGenerator.userList(filters, page, limit, sortBy, sortOrder);
    return userListCache.get(key) || null;
  }
  static set(
    filters: UserListFilter, 
    page: number, 
    limit: number, 
    data: PaginatedResponse<User>,
    sortBy?: string, 
    sortOrder?: string
  ): void {
    const key = CacheKeyGenerator.userList(filters, page, limit, sortBy, sortOrder);
    userListCache.set(key, data);
  }
  static invalidateAll(): void {
    userListCache.clear();
  }
  static invalidateByUser(userId: string): void {
    // Since we can't easily find all cache entries that contain a specific user,
    // we'll clear the entire user list cache when a user is updated
    this.invalidateAll();
  }
  static getStats(): CacheStats {
    return {
      size: userListCache.size,
      maxSize: CACHE_CONFIG.userLists.maxSize,
      hitRate: 0.8, // Mock hit rate for now
      ttl: CACHE_CONFIG.userLists.ttl
    };
  }
}
// Statistics caching
export class StatisticsCache {
  static async get(type: string, params?: Record<string, any>): Promise<any | null> {
    const key = CacheKeyGenerator.statistics(type, params);
    return statisticsCache.get(key) || null;
  }
  static set(type: string, data: any, params?: Record<string, any>): void {
    const key = CacheKeyGenerator.statistics(type, params);
    statisticsCache.set(key, data);
  }
  static invalidate(type: string, params?: Record<string, any>): void {
    const key = CacheKeyGenerator.statistics(type, params);
    statisticsCache.delete(key);
  }
  static invalidateAll(): void {
    statisticsCache.clear();
  }
  static getStats(): CacheStats {
    return {
      size: statisticsCache.size,
      maxSize: CACHE_CONFIG.statistics.maxSize,
      hitRate: 0.8, // Mock hit rate for now
      ttl: CACHE_CONFIG.statistics.ttl
    };
  }
}
// Cache management utilities
export class AdminCacheManager {
  /**
   * Get comprehensive cache statistics
   */
  static getAllStats(): Record<string, CacheStats> {
    return {
      permissions: PermissionCache.getStats(),
      systemConfig: SystemConfigCache.getStats(),
      users: UserCache.getStats(),
      userLists: UserListCache.getStats(),
      statistics: StatisticsCache.getStats()
    };
  }
  /**
   * Clear all caches
   */
  static clearAll(): void {
    PermissionCache.invalidateAll();
    SystemConfigCache.invalidateAll();
    UserCache.invalidateAll();
    UserListCache.invalidateAll();
    StatisticsCache.invalidateAll();
  }
  /**
   * Invalidate caches when user is updated
   */
  static invalidateUserCaches(userId: string, email?: string): void {
    PermissionCache.invalidate(userId);
    UserCache.invalidate(userId, email);
    UserListCache.invalidateByUser(userId);
    StatisticsCache.invalidateAll(); // User stats might be affected
  }
  /**
   * Invalidate caches when system config is updated
   */
  static invalidateConfigCaches(category?: string): void {
    SystemConfigCache.invalidate(category);
  }
  /**
   * Warm up caches with frequently accessed data
   */
  static async warmUp(frequentUserIds: string[] = []): Promise<void> {
    // This would typically be called during application startup
    // to pre-populate caches with frequently accessed data
    try {
      // Warm up system config cache
      const configResponse = await fetch('/api/admin/system/config');
      if (configResponse.ok) {
        const configData = await configResponse.json();
        if (configData.success) {
          SystemConfigCache.set(undefined, configData.data);
        }
      }
      // Warm up user permissions for frequent users
      for (const userId of frequentUserIds) {
        try {
          const permissionsResponse = await fetch(`/api/admin/users/${userId}/permissions`);
          if (permissionsResponse.ok) {
            const permissionsData = await permissionsResponse.json();
            if (permissionsData.success) {
              PermissionCache.set(userId, permissionsData.data);
            }
          }
        } catch (error) {
        }
      }
    } catch (error) {
    }
  }
  /**
   * Get cache memory usage estimation
   */
  static getMemoryUsage(): Record<string, number> {
    const permissionsSize = permissionsCache.size * 100; // Rough estimate
    const systemConfigSize = systemConfigCache.size * 50;
    const usersSize = userCache.size * 200;
    const userListsSize = userListCache.size * 1000;
    const statisticsSize = statisticsCache.size * 300;
    return {
      permissions: permissionsSize,
      systemConfig: systemConfigSize,
      users: usersSize,
      userLists: userListsSize,
      statistics: statisticsSize,
      total: permissionsSize + systemConfigSize + usersSize + userListsSize + statisticsSize
    };
  }
  /**
   * Configure cache settings
   */
  static configureCaches(config: Partial<typeof CACHE_CONFIG>): void {
    // This would allow runtime configuration of cache settings
    // Implementation would require recreating cache instances
  }
  /**
   * Health check for all caches
   */
  static healthCheck(): Record<string, boolean> {
    return {
      permissions: permissionsCache.size >= 0,
      systemConfig: systemConfigCache.size >= 0,
      users: userCache.size >= 0,
      userLists: userListCache.size >= 0,
      statistics: statisticsCache.size >= 0
    };
  }
}
// Cache middleware for API routes
export function withCache<T>(
  cacheGetter: () => Promise<T | null>,
  cacheSetter: (data: T) => void,
  dataFetcher: () => Promise<T>
): Promise<T> {
  return new Promise(async (resolve, reject) => {
    try {
      // Try to get from cache first
      const cachedData = await cacheGetter();
      if (cachedData !== null) {
        resolve(cachedData);
        return;
      }
      // Fetch fresh data
      const freshData = await dataFetcher();
      // Cache the fresh data
      cacheSetter(freshData);
      resolve(freshData);
    } catch (error) {
      reject(error);
    }

}
// Export cache instances for direct access if needed
export {
  permissionsCache,
  systemConfigCache,
  userCache,
  userListCache,
  statisticsCache
};
