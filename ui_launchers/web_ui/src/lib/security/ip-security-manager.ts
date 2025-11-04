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

/* =========================
 * Helpers (IPv4/IPv6 + CIDR)
 * ========================= */

function stripPort(host: string): string {
  // strips ":port" for IPv4 and "[v6]:port" patterns; keeps raw IPv6
  try {
    // When input looks like URL, parse:
    if (/^https?:\/\//i.test(host)) {
      const u = new URL(host);
      return u.hostname;
    }
  } catch {}
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
  const c = stripPort(raw.trim());
  // Remove enclosing brackets for IPv6
  const v = c.startsWith('[') && c.endsWith(']') ? c.slice(1, -1) : c;
  // Lowercase IPv6 for canonical form
  return v.toLowerCase();
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
      v = (v << 16n) | n;
    }
    return { v, bits: 128 };
  }
  return null;
}

function expandIPv6(ip: string): string | null {
  if (ip === '::') return '0:0:0:0:0:0:0:0';
  const parts = ip.split('::');
  if (parts.length > 2) return null;
  if (parts.length === 2) {
    const left = parts[0] ? parts[0].split(':') : [];
    const right = parts[1] ? parts[1].split(':') : [];
    const missing = 8 - (left.length + right.length);
    if (missing <= 0) return null;
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
  const [net, maskStr] = cidr.split('/');
  const mask = maskStr ? parseInt(maskStr, 10) : (net.includes(':') ? 128 : 32);
  if (Number.isNaN(mask)) return false;
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
  if (needle.includes('/')) return cidrMatch(ip, needle);
  return normalizeIp(needle) === ip;
}

/* =========================
 * Token-bucket-ish throttle
 * ========================= */
interface Bucket {
  ts: number[];
}

class SimpleThrottle {
  constructor(
    private windowMs: number,
    private maxReq: number
  ) {}
  private buckets = new Map<string, Bucket>();

  touch(key: string): { allowed: boolean; remaining: number } {
    const now = Date.now();
    const winStart = now - this.windowMs;
    const b = this.buckets.get(key) || { ts: [] };
    b.ts = b.ts.filter(t => t >= winStart);
    if (b.ts.length >= this.maxReq) {
      this.buckets.set(key, b);
      return { allowed: false, remaining: 0 };
    }
    b.ts.push(now);
    this.buckets.set(key, b);
    return { allowed: true, remaining: this.maxReq - b.ts.length };
  }

  stats(key: string) {
    const b = this.buckets.get(key) || { ts: [] };
    return { count: b.ts.length, windowMs: this.windowMs, max: this.maxReq };
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
  private blockedIps = new Map<string, { ip: string; blockedUntil: Date; reason: string }>(); // key: normalized ip
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

  private throttle = new SimpleThrottle(
    this.config.throttle_window_ms,
    this.config.throttle_max_requests
  );

  constructor() {
    // Kick off async loads; fire-and-forget
    void this.loadConfiguration();
    void this.loadWhitelist();
    void this.rehydrateBlocks();
  }

  /* ---------------------------------------
   * ACCESS / DECISION
   * ------------------------------------- */

  async checkIpAccess(ipRaw: string, user: User): Promise<{ allowed: boolean; reason?: string }> {
    const ip = normalizeIp(ipRaw);

    // Throttling gate (per IP)
    const { allowed: notThrottled } = this.throttle.touch(`ip:${ip}`);
    if (!notThrottled) {
      await this.audit('system', 'ip.throttle_block', 'ip_security', ip, { window_ms: this.config.throttle_window_ms });
      return { allowed: false, reason: 'Too many requests from IP' };
    }

    // Blocked?
    if (await this.isIpCurrentlyBlocked(ip)) {
      return { allowed: false, reason: 'IP address is temporarily blocked' };
    }

    // Whitelist policy by role
    if (user.role === 'super_admin' && this.config.super_admin_whitelist_enabled) {
      const ok = await this.isIpWhitelisted(ip, user.user_id, 'super_admin');
      if (!ok) {
        await this.securityEvent('suspicious_activity', {
          user_id: user.user_id,
          ip_address: ip,
          details: { reason: 'super_admin_not_whitelisted', user_role: user.role, whitelist_enabled: true },
          severity: 'high',
        });
        return { allowed: false, reason: 'IP not whitelisted for super admin access' };
      }
    }

    if (user.role === 'admin' && this.config.admin_whitelist_enabled) {
      const ok = await this.isIpWhitelisted(ip, user.user_id, 'admin');
      if (!ok) {
        await this.securityEvent('suspicious_activity', {
          user_id: user.user_id,
          ip_address: ip,
          details: { reason: 'admin_not_whitelisted', user_role: user.role, whitelist_enabled: true },
          severity: 'medium',
        });
        return { allowed: false, reason: 'IP not whitelisted for admin access' };
      }
    }

    return { allowed: true };
  }

  /* ---------------------------------------
   * RECORD ACCESS
   * ------------------------------------- */

  async recordIpAccess(ipRaw: string, user: User, userAgent?: string): Promise<void> {
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
        record.location = await this.getIpLocation(ip);
      }
    }

    record.access_count += 1;
    record.last_seen = now;
    record.user_agent = userAgent || record.user_agent;

    this.ipAccessRecords.set(key, record);

    await this.checkSuspiciousActivity(record);

    await this.audit(user.user_id, 'ip.access_recorded', 'ip_security', ip, {
      access_count: record.access_count,
      first_seen: record.first_seen.toISOString(),
      location: record.location,
      user_role: user.role,
    }, ip, userAgent);
  }

  /* ---------------------------------------
   * FAILED ATTEMPTS / BLOCKING
   * ------------------------------------- */

  async recordFailedAttempt(ipRaw: string, userIdentifier?: string): Promise<void> {
    const ip = normalizeIp(ipRaw);
    const now = new Date();
    const attempts = this.failedAttempts.get(ip) || { count: 0, lastAttempt: now };

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
  }

  async blockIp(ipRaw: string, reason: string, durationMs: number): Promise<void> {
    const ip = normalizeIp(ipRaw);
    const blockedUntil = new Date(Date.now() + durationMs);
    this.blockedIps.set(ip, { ip, blockedUntil, reason });

    await this.audit('system', 'ip.blocked', 'ip_security', ip, {
      reason, blocked_until: blockedUntil.toISOString(), duration_ms: durationMs,
    }, ip);

    await this.securityEvent('suspicious_activity', {
      ip_address: ip,
      details: { action: 'ip_blocked', reason, blocked_until: blockedUntil.toISOString() },
      severity: 'medium',
    });

    // persist block if backend provides such API (best-effort)
    try { await this.adminUtils.blockIp?.(ip, reason, blockedUntil); } catch {}
  }

  async unblockIp(ipRaw: string, unblockedBy: string): Promise<boolean> {
    const ip = normalizeIp(ipRaw);
    const blk = this.blockedIps.get(ip);
    if (!blk) return false;
    this.blockedIps.delete(ip);

    await this.audit(unblockedBy, 'ip.unblocked', 'ip_security', ip, {
      original_reason: blk.reason, unblocked_by: unblockedBy,
    }, ip);

    try { await this.adminUtils.unblockIp?.(ip); } catch {}
    return true;
  }

  private async isIpCurrentlyBlocked(ipRaw: string): Promise<boolean> {
    const ip = normalizeIp(ipRaw);
    const blk = this.blockedIps.get(ip);
    if (!blk) return false;
    if (new Date() > blk.blockedUntil) {
      this.blockedIps.delete(ip);
      try { await this.adminUtils.unblockIp?.(ip); } catch {}
      return false;
    }
    return true;
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
      ip_or_cidr: ipOrCidr, description, user_id: userId, role_restriction: roleRestriction,
    });

    try { await this.adminUtils.upsertIpWhitelist?.(entry); } catch {}
    return entry;
  }

  async removeFromWhitelist(entryId: string, removedBy: string): Promise<boolean> {
    const entry = this.ipWhitelist.get(entryId);
    if (!entry) return false;
    this.ipWhitelist.delete(entryId);

    await this.audit(removedBy, 'ip.whitelist_removed', 'ip_whitelist', entry.id, {
      ip_or_cidr: entry.ip_or_cidr, description: entry.description, removed_by: removedBy,
    });

    try { await this.adminUtils.removeIpWhitelist?.(entryId); } catch {}
    return true;
  }

  private async isIpWhitelisted(ip: string, userId?: string, role?: 'super_admin' | 'admin'): Promise<boolean> {
    // Any active entry that matches IP (direct or CIDR), and respects user/role scopes
    for (const entry of this.ipWhitelist.values()) {
      if (!entry.is_active) continue;
      if (entry.user_id && entry.user_id !== userId) continue;
      if (entry.role_restriction && entry.role_restriction !== role) continue;
      if (matchesIpOrCidr(entry.ip_or_cidr, ip)) return true;
    }
    // Also allow backend decision if provided
    try {
      const ok = await this.adminUtils.isIpWhitelisted?.(ip, userId, role);
      if (typeof ok === 'boolean') return ok;
    } catch {}
    return false;
  }

  /* ---------------------------------------
   * SUSPICIOUS ACTIVITY
   * ------------------------------------- */

  private async checkSuspiciousActivity(record: IpAccessRecord): Promise<void> {
    const reasons: string[] = [];

    // Frequency
    if (record.access_count > this.config.suspicious_activity_threshold) {
      reasons.push('high_access_frequency');
    }

    // Multiple distinct users from same IP (possible shared/VPN/attack)
    const sameIpDistinctUsers = Array.from(this.ipAccessRecords.values())
      .filter(r => r.ip_address === record.ip_address)
      .reduce((acc, r) => acc.add(r.user_id), new Set<string>()).size;
    if (sameIpDistinctUsers > 3) {
      reasons.push('multiple_users_same_ip');
    }

    // Admin from new country (geo-anomaly)
    if ((record.user_role === 'super_admin' || record.user_role === 'admin') && record.location?.country) {
      const prevCountries = Array.from(this.ipAccessRecords.values())
        .filter(r => r.user_id === record.user_id && r.ip_address !== record.ip_address && r.location?.country)
        .map(r => r.location!.country!);
      if (prevCountries.length > 0 && !prevCountries.includes(record.location.country)) {
        reasons.push('new_geographic_location');
      }
    }

    if (reasons.length) {
      record.is_suspicious = true;
      await this.securityEvent('suspicious_activity', {
        user_id: record.user_id,
        ip_address: record.ip_address,
        details: {
          reasons,
          access_count: record.access_count,
          user_role: record.user_role,
          location: record.location,
        },
        severity: 'medium',
      });

      if (this.config.auto_block_suspicious_ips) {
        await this.blockIp(record.ip_address, 'suspicious_activity_detected', this.config.ip_lockout_duration);
      }
    }
  }

  /* ---------------------------------------
   * GEOLOCATION (pluggable)
   * ------------------------------------- */

  private async getIpLocation(ip: string): Promise<{ country?: string; region?: string; city?: string; timezone?: string; asn?: string; org?: string }> {
    // Preferred: server-side integration (e.g., MaxMind, ipinfo, ipapi) to avoid exposing secrets in browser
    try {
      const loc = await this.adminUtils.lookupGeo?.(ip);
      if (loc) return loc;
    } catch {}
    // Fallback mock
    return { country: 'Unknown', region: 'Unknown', city: 'Unknown', timezone: 'UTC' };
  }

  /* ---------------------------------------
   * CONFIG / STATE LOAD
   * ------------------------------------- */

  private async loadConfiguration(): Promise<void> {
    try {
      const rows = await this.adminUtils.getSystemConfig?.('security');
      const apply = (k: string, v: any) => {
        switch (k) {
          case 'super_admin_whitelist_enabled': this.config.super_admin_whitelist_enabled = v === 'true' || v === true; break;
          case 'admin_whitelist_enabled': this.config.admin_whitelist_enabled = v === 'true' || v === true; break;
          case 'max_failed_attempts_per_ip': this.config.max_failed_attempts_per_ip = Number(v) || this.config.max_failed_attempts_per_ip; break;
          case 'ip_lockout_duration': this.config.ip_lockout_duration = Number(v) || this.config.ip_lockout_duration; break;
          case 'geolocation_monitoring': this.config.geolocation_monitoring = v === 'true' || v === true; break;
          case 'auto_block_suspicious_ips': this.config.auto_block_suspicious_ips = v === 'true' || v === true; break;
          case 'throttle_window_ms': this.config.throttle_window_ms = Number(v) || this.config.throttle_window_ms; break;
          case 'throttle_max_requests': this.config.throttle_max_requests = Number(v) || this.config.throttle_max_requests; break;
        }
      };
      if (Array.isArray(rows)) {
        for (const r of rows) apply(r.key, r.value);
      }
      // refresh throttle with new config
      this.throttle = new SimpleThrottle(this.config.throttle_window_ms, this.config.throttle_max_requests);
    } catch {
      // keep defaults
    }
  }

  private async loadWhitelist(): Promise<void> {
    try {
      const entries = await this.adminUtils.getIpWhitelist?.();
      if (Array.isArray(entries)) {
        for (const e of entries) {
          const entry: IpWhitelistEntry = {
            id: e.id || this.generateId(),
            ip_or_cidr: e.ip_or_cidr || e.ip_address, // backward compat
            description: e.description || '',
            user_id: e.user_id,
            role_restriction: e.role_restriction,
            created_by: e.created_by || 'system',
            created_at: e.created_at ? new Date(e.created_at) : new Date(),
            is_active: e.is_active !== false,
          };
          this.ipWhitelist.set(entry.id, entry);
        }
      }
    } catch {
      // ignore
    }
  }

  private async rehydrateBlocks(): Promise<void> {
    try {
      const blocks = await this.adminUtils.getBlockedIps?.();
      if (Array.isArray(blocks)) {
        for (const b of blocks) {
          const ip = normalizeIp(b.ip || b.ip_address);
          const until = new Date(b.blocked_until || b.blockedUntil || Date.now());
          const reason = b.reason || 'rehydrated';
          if (until > new Date()) this.blockedIps.set(ip, { ip, blockedUntil: until, reason });
        }
      }
    } catch {
      // best effort
    }
  }

  /* ---------------------------------------
   * STATS / INSIGHT
   * ------------------------------------- */

  getIpStatistics(): {
    totalUniqueIps: number;
    whitelistedEntries: number;
    blockedIps: number;
    suspiciousIps: number;
    topAccessedIps: Array<{ ip: string; accessCount: number; users: number }>;
    throttleSample?: { window_ms: number; max: number };
  } {
    const ipAgg = new Map<string, { accessCount: number; users: Set<string> }>();
    let suspiciousCount = 0;

    for (const r of this.ipAccessRecords.values()) {
      const s = ipAgg.get(r.ip_address) || { accessCount: 0, users: new Set<string>() };
      s.accessCount += r.access_count;
      s.users.add(r.user_id);
      ipAgg.set(r.ip_address, s);
      if (r.is_suspicious) suspiciousCount += 1;
    }

    const topAccessedIps = Array.from(ipAgg.entries())
      .map(([ip, s]) => ({ ip, accessCount: s.accessCount, users: s.users.size }))
      .sort((a, b) => b.accessCount - a.accessCount)
      .slice(0, 10);

    return {
      totalUniqueIps: ipAgg.size,
      whitelistedEntries: Array.from(this.ipWhitelist.values()).filter(e => e.is_active).length,
      blockedIps: this.getBlockedIps().length,
      suspiciousIps: suspiciousCount,
      topAccessedIps,
      throttleSample: { window_ms: this.config.throttle_window_ms, max: this.config.throttle_max_requests },
    };
  }

  getWhitelistEntries(): IpWhitelistEntry[] {
    return Array.from(this.ipWhitelist.values()).filter(e => e.is_active);
  }

  getBlockedIps(): Array<{ ip: string; reason: string; blockedUntil: Date }> {
    const now = new Date();
    const out: Array<{ ip: string; reason: string; blockedUntil: Date }> = [];
    for (const v of this.blockedIps.values()) {
      if (v.blockedUntil > now) out.push({ ip: v.ip, reason: v.reason, blockedUntil: v.blockedUntil });
    }
    return out;
  }

  async updateConfiguration(newConfig: Partial<IpSecurityConfig>, updatedBy: string): Promise<void> {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...newConfig };
    this.throttle = new SimpleThrottle(this.config.throttle_window_ms, this.config.throttle_max_requests);

    await this.audit(updatedBy, 'ip.config_updated', 'ip_security_config', 'security', {
      old_config: oldConfig, new_config: this.config, updated_by: updatedBy,
    });
  }

  /* ---------------------------------------
   * Logging & Events (best-effort)
   * ------------------------------------- */

  private async audit(
    user_id: string,
    action: string,
    resource_type: string,
    resource_id: string,
    details?: Record<string, unknown>,
    ip_address?: string,
    user_agent?: string
  ) {
    try {
      await this.adminUtils.createAuditLog({
        user_id, action, resource_type, resource_id, details, ip_address, user_agent,
      });
    } catch {}
  }

  private async securityEvent(
    event_type: SecurityEvent['event_type'],
    payload: Omit<SecurityEvent, 'id' | 'resolved' | 'created_at'>
  ) {
    // Prefer dedicated API if present
    try {
      if (this.adminUtils.createSecurityEvent) {
        await this.adminUtils.createSecurityEvent(payload);
        return;
      }
    } catch {}
    // Fallback: log as audit
    await this.audit(payload.user_id || 'system', 'security.event', 'security_event', event_type, {
      event_type,
      severity: (payload as any).severity,
      details: payload.details,
      ip_address: (payload as any).ip_address,
    });
  }

  /* ---------------------------------------
   * Utilities
   * ------------------------------------- */

  private generateId(): string {
    return `ip_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  }
}

/* Singleton */
export const ipSecurityManager = new IpSecurityManager();
