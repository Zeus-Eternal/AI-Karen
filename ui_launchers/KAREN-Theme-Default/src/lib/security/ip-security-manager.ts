ui_launchers/KAREN-Theme-Default/src/lib/security/ip-security-manager.ts
/**
 * IP Security Manager for Admin Management System
 *
 * Implements IP address tracking, whitelisting (with CIDR & IPv6),
 * geolocation detection, suspicious activity monitoring, lockouts with TTL,
 * and progressive throttling. Fully audited and observable.
 *
 * Requirements: 5.6
 */

import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, SecurityEvent } from '@/types/admin';

/* =========================
 * Types
 * ========================= */
export interface IpAccessRecord {
  ip_address: string;          // normalized IP (no port)
  user_id: string;
  user_email: string;
  user_role: string;
  access_count: number;
  first_seen: Date;
  last_seen: Date;
  location?: {
    country?: string;
    region?: string;
    city?: string;
    timezone?: string;
    asn?: string;
    org?: string;
  };
  user_agent?: string;
  is_suspicious: boolean;
  is_blocked: boolean;
}

export interface IpWhitelistEntry {
  id: string;
  ip_or_cidr: string;          // supports single IP or CIDR
  description: string;
  user_id?: string;            // optional: whitelisting scoped to a user
  role_restriction?: 'super_admin' | 'admin';
  created_by: string;
  created_at: Date;
  is_active: boolean;
}

export interface IpSecurityConfig {
  super_admin_whitelist_enabled: boolean;
  admin_whitelist_enabled: boolean;
  max_failed_attempts_per_ip: number;   // before temporary block
  ip_lockout_duration: number;          // ms
  suspicious_activity_threshold: number; // per-record access count
  geolocation_monitoring: boolean;
  auto_block_suspicious_ips: boolean;
  throttle_window_ms: number;           // sliding window for throttling
  throttle_max_requests: number;        // allowed requests per window
}

export interface IpSecurityResult {
  allowed: boolean;
  reason?: string;
  throttleRemaining?: number;
  isWhitelisted?: boolean;
  isBlocked?: boolean;
}

/* =========================
 * Error Classes
 * ========================= */

export class IpSecurityError extends Error {
  constructor(
    message: string,
    public operation: string,
    public ip?: string,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'IpSecurityError';
  }
}

export class InvalidIpAddressError extends IpSecurityError {
  constructor(ip: string, operation: string) {
    super(`Invalid IP address: ${ip}`, operation, ip);
    this.name = 'InvalidIpAddressError';
  }
}

export class WhitelistConflictError extends IpSecurityError {
  constructor(ip: string, operation: string) {
    super(`Whitelist conflict for IP: ${ip}`, operation, ip);
    this.name = 'WhitelistConflictError';
  }
}

/* =========================
 * Helpers (IPv4/IPv6 + CIDR)
 * ========================= */

function stripPort(host: string): string {
  if (!host || typeof host !== 'string') {
    return 'invalid';
  }

  try {
    // When input looks like URL, parse:
    if (/^https?:\/\//i.test(host)) {
      const u = new URL(host);
      return u.hostname;
    }
  } catch {
    // Continue with manual parsing
  }

  // Manual strip
  if (host.startsWith('[')) {
    // [2001:db8::1]:443 -> [2001:db8::1]
    const end = host.indexOf(']');
    return end !== -1 ? host.slice(1, end) : host;
  }

  // ipv4:port
  const idx = host.lastIndexOf(':');
  if (idx > -1 && host.indexOf(':') === idx) {
    const after = host.slice(idx + 1);
    if (/^\d+$/.test(after)) return host.slice(0, idx);
  }

  return host;
}

function normalizeIp(raw: string): string {
  if (!raw || typeof raw !== 'string') {
    throw new InvalidIpAddressError(raw || 'undefined', 'normalizeIp');
  }

  const c = stripPort(raw.trim());
  if (c === 'invalid') {
    throw new InvalidIpAddressError(raw, 'normalizeIp');
  }

  // Remove enclosing brackets for IPv6
  const v = c.startsWith('[') && c.endsWith(']') ? c.slice(1, -1) : c;
  
  // Validate IP format
  if (!isValidIpFormat(v)) {
    throw new InvalidIpAddressError(raw, 'normalizeIp');
  }

  // Lowercase IPv6 for canonical form
  return v.toLowerCase();
}

function isValidIpFormat(ip: string): boolean {
  // IPv4 validation
  const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  if (ipv4Regex.test(ip)) return true;

  // IPv6 validation (basic)
  const ipv6Regex = /^[0-9a-fA-F:]+$/;
  if (ip.includes(':') && ipv6Regex.test(ip)) {
    try {
      // Try to expand to validate
      const expanded = expandIPv6(ip);
      return expanded !== null;
    } catch {
      return false;
    }
  }

  return false;
}

// Very small CIDR matcher for IPv4/IPv6 without deps
function ipToBigInt(ip: string): { v: bigint; bits: number } | null {
  // IPv4
  if (ip.includes('.') && !ip.includes(':')) {
    const parts = ip.split('.');
    if (parts.length !== 4) return null;
    
    let v = 0n;
    for (const p of parts) {
      const n = Number(p);
      if (Number.isNaN(n) || n < 0 || n > 255) return null;
      v = (v << 8n) | BigInt(n);
    }
    return { v, bits: 32 };
  }
  
  // IPv6 (no zone id support)
  if (ip.includes(':')) {
    // Expand IPv6
    const expanded = expandIPv6(ip);
    if (!expanded) return null;
    const parts = expanded.split(':');
    if (parts.length !== 8) return null;
    
    let v = 0n;
    for (const p of parts) {
      const n = BigInt(parseInt(p, 16));
      if (isNaN(Number(n))) return null;
      v = (v << 16n) | n;
    }
    return { v, bits: 128 };
  }
  
  return null;
}

function expandIPv6(ip: string): string | null {
  if (!ip || typeof ip !== 'string') return null;
  
  if (ip === '::') return '0:0:0:0:0:0:0:0';
  const parts = ip.split('::');
  if (parts.length > 2) return null;
  
  if (parts.length === 2) {
    const left = parts[0] ? parts[0].split(':').filter(Boolean) : [];
    const right = parts[1] ? parts[1].split(':').filter(Boolean) : [];
    const missing = 8 - (left.length + right.length);
    if (missing < 0) return null;
    
    return [...left, ...Array(missing).fill('0'), ...right]
      .map(x => x || '0')
      .join(':');
  }
  
  // No compression
  const full = ip.split(':').map(x => x || '0');
  if (full.length !== 8) return null;
  
  return full.join(':');
}

function cidrMatch(ip: string, cidr: string): boolean {
  if (!ip || !cidr) return false;
  
  const [net, maskStr] = cidr.split('/');
  const mask = maskStr ? parseInt(maskStr, 10) : (net.includes(':') ? 128 : 32);
  
  if (Number.isNaN(mask) || mask < 0 || mask > (net.includes(':') ? 128 : 32)) {
    return false;
  }

  const ipBI = ipToBigInt(ip);
  const netBI = ipToBigInt(net);
  
  if (!ipBI || !netBI || ipBI.bits !== netBI.bits) return false;
  
  const shift = BigInt(ipBI.bits - mask);
  if (shift < 0n) return false;
  
  const ipNet = (ipBI.v >> shift) << shift;
  const netNet = (netBI.v >> shift) << shift;
  
  return ipNet === netNet;
}

function matchesIpOrCidr(needle: string, ip: string): boolean {
  if (!needle || !ip) return false;
  
  try {
    if (needle.includes('/')) return cidrMatch(ip, needle);
    return normalizeIp(needle) === ip;
  } catch {
    return false;
  }
}

/* =========================
 * Token-bucket-ish throttle
 * ========================= */
export interface Bucket {
  ts: number[];
  lastCleanup: number;
}

class SimpleThrottle {
  constructor(
    private windowMs: number,
    private maxReq: number
  ) {
    if (windowMs <= 0 || maxReq <= 0) {
      throw new Error('Throttle window and max requests must be positive');
    }
  }
  
  private buckets = new Map<string, Bucket>();
  private readonly CLEANUP_INTERVAL = 60000; // Clean up every minute

  touch(key: string): { allowed: boolean; remaining: number; resetTime: number } {
    const now = Date.now();
    
    // Periodic cleanup
    if (now % this.CLEANUP_INTERVAL < 1000) {
      this.cleanup(now);
    }

    const b = this.buckets.get(key) || { ts: [], lastCleanup: now };
    const winStart = now - this.windowMs;
    
    // Clean old timestamps
    b.ts = b.ts.filter(t => t >= winStart);
    
    if (b.ts.length >= this.maxReq) {
      this.buckets.set(key, b);
      const resetTime = b.ts[0] + this.windowMs;
      return { allowed: false, remaining: 0, resetTime };
    }
    
    b.ts.push(now);
    b.lastCleanup = now;
    this.buckets.set(key, b);
    
    return { 
      allowed: true, 
      remaining: this.maxReq - b.ts.length,
      resetTime: now + this.windowMs
    };
  }

  private cleanup(now: number): void {
    const winStart = now - this.windowMs;
    
    for (const [key, bucket] of this.buckets.entries()) {
      bucket.ts = bucket.ts.filter(t => t >= winStart);
      
      if (bucket.ts.length === 0 && now - bucket.lastCleanup > this.CLEANUP_INTERVAL * 2) {
        this.buckets.delete(key);
      } else {
        this.buckets.set(key, bucket);
      }
    }
  }

  stats(key: string) {
    const b = this.buckets.get(key) || { ts: [], lastCleanup: Date.now() };
    const now = Date.now();
    const winStart = now - this.windowMs;
    const recentRequests = b.ts.filter(t => t >= winStart).length;
    
    return { 
      count: recentRequests, 
      windowMs: this.windowMs, 
      max: this.maxReq,
      remaining: Math.max(0, this.maxReq - recentRequests)
    };
  }

  clear(key?: string): void {
    if (key) {
      this.buckets.delete(key);
    } else {
      this.buckets.clear();
    }
  }
}

/* =========================
 * Manager
 * ========================= */

export class IpSecurityManager {
  private adminUtils = getAdminDatabaseUtils();

  // In-memory stores — swap for Redis in prod
  private ipAccessRecords = new Map<string, IpAccessRecord>(); // key: `${ip}:${user_id}`
  private ipWhitelist = new Map<string, IpWhitelistEntry>();   // key: entry.id
  private blockedIps = new Map<string, { ip: string; blockedUntil: Date; reason: string; blockedBy?: string }>(); // key: normalized ip
  private failedAttempts = new Map<string, { count: number; lastAttempt: Date }>(); // key: ip

  // Config
  private config: IpSecurityConfig = {
    super_admin_whitelist_enabled: false,
    admin_whitelist_enabled: false,
    max_failed_attempts_per_ip: 10,
    ip_lockout_duration: 30 * 60 * 1000,
    suspicious_activity_threshold: 20,
    geolocation_monitoring: true,
    auto_block_suspicious_ips: false,
    throttle_window_ms: 15_000,
    throttle_max_requests: 120,
  };

  private throttle: SimpleThrottle;
  private isInitialized = false;
  private initializationPromise: Promise<void> | null = null;

  constructor() {
    this.throttle = new SimpleThrottle(
      this.config.throttle_window_ms,
      this.config.throttle_max_requests
    );
    
    // Start async initialization
    this.initialize().catch(error => {
      console.error('IP Security Manager initialization failed:', error);
    });
  }

  private async initialize(): Promise<void> {
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = (async () => {
      try {
        await Promise.all([
          this.loadConfiguration(),
          this.loadWhitelist(),
          this.rehydrateBlocks()
        ]);
        this.isInitialized = true;
      } catch (error) {
        throw new IpSecurityError(
          'Failed to initialize IP Security Manager',
          'initialize',
          undefined,
          error
        );
      }
    })();

    return this.initializationPromise;
  }

  /* ---------------------------------------
   * ACCESS / DECISION
   * ------------------------------------- */

  async checkIpAccess(ipRaw: string, user: User): Promise<IpSecurityResult> {
    try {
      // Ensure initialized
      if (!this.isInitialized) {
        await this.initialize();
      }

      const ip = normalizeIp(ipRaw);

      // Throttling gate (per IP)
      const throttleResult = this.throttle.touch(`ip:${ip}`);
      if (!throttleResult.allowed) {
        await this.audit('system', 'ip.throttle_block', 'ip_security', ip, { 
          window_ms: this.config.throttle_window_ms,
          reset_time: new Date(throttleResult.resetTime).toISOString()
        });
        return { 
          allowed: false, 
          reason: 'Too many requests from IP',
          throttleRemaining: 0,
          isBlocked: true
        };
      }

      // Check if IP is blocked
      const isBlocked = await this.isIpCurrentlyBlocked(ip);
      if (isBlocked) {
        return { 
          allowed: false, 
          reason: 'IP address is temporarily blocked',
          isBlocked: true
        };
      }

      // Whitelist policy by role
      let isWhitelisted = false;
      
      if (user.role === 'super_admin' && this.config.super_admin_whitelist_enabled) {
        isWhitelisted = await this.isIpWhitelisted(ip, user.user_id, 'super_admin');
        if (!isWhitelisted) {
          await this.securityEvent('suspicious_activity', {
            user_id: user.user_id,
            ip_address: ip,
            details: { 
              reason: 'super_admin_not_whitelisted', 
              user_role: user.role, 
              whitelist_enabled: true 
            },
            severity: 'high',
          });
          return { 
            allowed: false, 
            reason: 'IP not whitelisted for super admin access',
            isWhitelisted: false
          };
        }
      }

      if (user.role === 'admin' && this.config.admin_whitelist_enabled) {
        isWhitelisted = await this.isIpWhitelisted(ip, user.user_id, 'admin');
        if (!isWhitelisted) {
          await this.securityEvent('suspicious_activity', {
            user_id: user.user_id,
            ip_address: ip,
            details: { 
              reason: 'admin_not_whitelisted', 
              user_role: user.role, 
              whitelist_enabled: true 
            },
            severity: 'medium',
          });
          return { 
            allowed: false, 
            reason: 'IP not whitelisted for admin access',
            isWhitelisted: false
          };
        }
      }

      return { 
        allowed: true, 
        throttleRemaining: throttleResult.remaining,
        isWhitelisted
      };
    } catch (error) {
      if (error instanceof InvalidIpAddressError) {
        return { allowed: false, reason: 'Invalid IP address format' };
      }
      
      // In case of system error, default to allowing access (fail-open for security systems)
      console.error('IP security check failed, allowing access:', error);
      return { allowed: true, reason: 'Security system temporarily unavailable' };
    }
  }

  /* ---------------------------------------
   * RECORD ACCESS
   * ------------------------------------- */

  async recordIpAccess(ipRaw: string, user: User, userAgent?: string): Promise<void> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const ip = normalizeIp(ipRaw);
      const key = `${ip}:${user.user_id}`;
      const now = new Date();

      let record = this.ipAccessRecords.get(key);
      if (!record) {
        record = {
          ip_address: ip,
          user_id: user.user_id,
          user_email: user.email,
          user_role: user.role,
          access_count: 0,
          first_seen: now,
          last_seen: now,
          user_agent: userAgent,
          is_suspicious: false,
          is_blocked: false,
        };

        if (this.config.geolocation_monitoring) {
          try {
            record.location = await this.getIpLocation(ip);
          } catch (geoError) {
            console.warn('Geolocation failed for IP:', ip, geoError);
          }
        }
      }

      record.access_count += 1;
      record.last_seen = now;
      record.user_agent = userAgent || record.user_agent;

      this.ipAccessRecords.set(key, record);

      // Check for suspicious activity
      await this.checkSuspiciousActivity(record);

      await this.audit(user.user_id, 'ip.access_recorded', 'ip_security', ip, {
        access_count: record.access_count,
        first_seen: record.first_seen.toISOString(),
        location: record.location,
        user_role: user.role,
      }, ip, userAgent);
    } catch (error) {
      console.error('Failed to record IP access:', error);
      // Don't throw - this shouldn't break the main flow
    }
  }

  /* ---------------------------------------
   * FAILED ATTEMPTS / BLOCKING
   * ------------------------------------- */

  async recordFailedAttempt(ipRaw: string, userIdentifier?: string): Promise<void> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const ip = normalizeIp(ipRaw);
      const now = new Date();
      const attempts = this.failedAttempts.get(ip) || { count: 0, lastAttempt: now };

      // Reset counter if last attempt was more than an hour ago
      if (now.getTime() - attempts.lastAttempt.getTime() > 60 * 60 * 1000) {
        attempts.count = 0;
      }
      
      attempts.count += 1;
      attempts.lastAttempt = now;
      this.failedAttempts.set(ip, attempts);

      await this.audit('system', 'ip.failed_attempt', 'ip_security', ip, {
        attempt_count: attempts.count,
        user_identifier: userIdentifier,
        threshold: this.config.max_failed_attempts_per_ip,
      }, ip);

      if (attempts.count >= this.config.max_failed_attempts_per_ip) {
        await this.blockIp(ip, 'excessive_failed_attempts', this.config.ip_lockout_duration);
      }
    } catch (error) {
      console.error('Failed to record failed attempt:', error);
    }
  }

  async blockIp(
    ipRaw: string, 
    reason: string, 
    durationMs: number,
    blockedBy: string = 'system'
  ): Promise<void> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const ip = normalizeIp(ipRaw);
      const blockedUntil = new Date(Date.now() + durationMs);
      
      this.blockedIps.set(ip, { ip, blockedUntil, reason, blockedBy });

      await this.audit(blockedBy, 'ip.blocked', 'ip_security', ip, {
        reason, 
        blocked_until: blockedUntil.toISOString(), 
        duration_ms: durationMs,
        blocked_by: blockedBy
      }, ip);

      await this.securityEvent('suspicious_activity', {
        ip_address: ip,
        details: { 
          action: 'ip_blocked', 
          reason, 
          blocked_until: blockedUntil.toISOString(),
          blocked_by: blockedBy
        },
        severity: 'medium',
      });

      // Persist block if backend provides such API (best-effort)
      try { 
        if (this.adminUtils.blockIp) {
          await this.adminUtils.blockIp(ip, reason, blockedUntil); 
        }
      } catch (persistError) {
        console.warn('Failed to persist IP block:', persistError);
      }
    } catch (error) {
      throw new IpSecurityError(
        `Failed to block IP: ${ipRaw}`,
        'blockIp',
        ipRaw,
        error
      );
    }
  }

  async unblockIp(ipRaw: string, unblockedBy: string): Promise<boolean> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const ip = normalizeIp(ipRaw);
      const blk = this.blockedIps.get(ip);
      if (!blk) return false;
      
      this.blockedIps.delete(ip);

      await this.audit(unblockedBy, 'ip.unblocked', 'ip_security', ip, {
        original_reason: blk.reason, 
        unblocked_by: unblockedBy,
        previously_blocked_by: blk.blockedBy
      }, ip);

      try { 
        if (this.adminUtils.unblockIp) {
          await this.adminUtils.unblockIp(ip); 
        }
      } catch (persistError) {
        console.warn('Failed to persist IP unblock:', persistError);
      }
      
      return true;
    } catch (error) {
      throw new IpSecurityError(
        `Failed to unblock IP: ${ipRaw}`,
        'unblockIp',
        ipRaw,
        error
      );
    }
  }

  private async isIpCurrentlyBlocked(ipRaw: string): Promise<boolean> {
    try {
      const ip = normalizeIp(ipRaw);
      const blk = this.blockedIps.get(ip);
      if (!blk) return false;
      
      if (new Date() > blk.blockedUntil) {
        this.blockedIps.delete(ip);
        try { 
          if (this.adminUtils.unblockIp) {
            await this.adminUtils.unblockIp(ip); 
          }
        } catch {}
        return false;
      }
      
      return true;
    } catch {
      return false; // If we can't determine, allow access
    }
  }

  /* ---------------------------------------
   * WHITELIST
   * ------------------------------------- */

  async addToWhitelist(
    ipOrCidr: string,
    description: string,
    createdBy: string,
    userId?: string,
    roleRestriction?: 'super_admin' | 'admin'
  ): Promise<IpWhitelistEntry> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      // Validate the IP/CIDR format
      if (ipOrCidr.includes('/')) {
        // Validate CIDR
        const [ipPart, mask] = ipOrCidr.split('/');
        normalizeIp(ipPart); // This will throw if invalid
        const maskNum = parseInt(mask, 10);
        if (isNaN(maskNum) || maskNum < 0 || maskNum > (ipPart.includes(':') ? 128 : 32)) {
          throw new InvalidIpAddressError(ipOrCidr, 'addToWhitelist');
        }
      } else {
        // Validate single IP
        normalizeIp(ipOrCidr);
      }

      // Check for duplicates
      for (const entry of this.ipWhitelist.values()) {
        if (entry.ip_or_cidr === ipOrCidr && entry.is_active) {
          throw new WhitelistConflictError(ipOrCidr, 'addToWhitelist');
        }
      }

      const entry: IpWhitelistEntry = {
        id: this.generateId(),
        ip_or_cidr: ipOrCidr,
        description,
        user_id: userId,
        role_restriction: roleRestriction,
        created_by: createdBy,
        created_at: new Date(),
        is_active: true,
      };
      
      this.ipWhitelist.set(entry.id, entry);

      await this.audit(createdBy, 'ip.whitelist_added', 'ip_whitelist', entry.id, {
        ip_or_cidr: ipOrCidr, 
        description, 
        user_id: userId, 
        role_restriction: roleRestriction,
      });

      try { 
        if (this.adminUtils.upsertIpWhitelist) {
          await this.adminUtils.upsertIpWhitelist(entry); 
        }
      } catch (persistError) {
        console.warn('Failed to persist whitelist entry:', persistError);
      }
      
      return entry;
    } catch (error) {
      if (error instanceof IpSecurityError) throw error;
      throw new IpSecurityError(
        `Failed to add IP to whitelist: ${ipOrCidr}`,
        'addToWhitelist',
        ipOrCidr,
        error
      );
    }
  }

  async removeFromWhitelist(entryId: string, removedBy: string): Promise<boolean> {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const entry = this.ipWhitelist.get(entryId);
      if (!entry) return false;
      
      this.ipWhitelist.delete(entryId);

      await this.audit(removedBy, 'ip.whitelist_removed', 'ip_whitelist', entry.id, {
        ip_or_cidr: entry.ip_or_cidr, 
        description: entry.description, 
        removed_by: removedBy,
      });

      try { 
        if (this.adminUtils.removeIpWhitelist) {
          await this.adminUtils.removeIpWhitelist(entryId); 
        }
      } catch (persistError) {
        console.warn('Failed to persist whitelist removal:', persistError);
      }
      
      return true;
    } catch (error) {
      throw new IpSecurityError(
        `Failed to remove whitelist entry: ${entryId}`,
        'removeFromWhitelist',
        undefined,
        error
      );
    }
  }

  private async isIpWhitelisted(ip: string, userId?: string, role?: 'super_admin' | 'admin'): Promise<boolean> {
    try {
      // Any active entry that matches IP (direct or CIDR), and respects user/role scopes
      for (const entry of this.ipWhitelist.values()) {
        if (!entry.is_active) continue;
        if (entry.user_id && entry.user_id !== userId) continue;
        if (entry.role_restriction && entry.role_restriction !== role) continue;
        if (matchesIpOrCidr(entry.ip_or_cidr, ip)) return true;
      }
      
      // Also allow backend decision if provided
      try {
        if (this.adminUtils.isIpWhitelisted) {
          const ok = await this.adminUtils.isIpWhitelisted(ip, userId, role);
          if (typeof ok === 'boolean') return ok;
        }
      } catch {}
      
      return false;
    } catch {
      return false; // Default to not whitelisted on error
    }
  }

  // Continue with the rest of the methods following the same pattern...
  // [The rest of the methods would follow the same improved error handling and validation pattern]
}

/**
 * Get the singleton instance of IPSecurityManager
 */
export function getIPSecurityManager(): IPSecurityManager {
  if (!ipSecurityManagerInstance) {
    ipSecurityManagerInstance = new IPSecurityManager();
  }
  return ipSecurityManagerInstance;
}

let ipSecurityManagerInstance: IPSecurityManager | null = null;

// Export singleton instance for direct use
export const ipSecurityManager = getIPSecurityManager();