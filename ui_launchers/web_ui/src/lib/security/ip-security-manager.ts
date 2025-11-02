/**
 * IP Security Manager for Admin Management System
 * 
 * Implements IP address tracking, whitelisting for super admins,
 * geolocation detection, and suspicious activity monitoring.
 * 
 * Requirements: 5.6
 */
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, SecurityEvent } from '@/types/admin';
export interface IpAccessRecord {
  ip_address: string;
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
  };
  user_agent?: string;
  is_suspicious: boolean;
  is_blocked: boolean;
}
export interface IpWhitelistEntry {
  id: string;
  ip_address: string;
  description: string;
  user_id?: string; // If specific to a user
  role_restriction?: 'super_admin' | 'admin';
  created_by: string;
  created_at: Date;
  is_active: boolean;
}
export interface IpSecurityConfig {
  super_admin_whitelist_enabled: boolean;
  admin_whitelist_enabled: boolean;
  max_failed_attempts_per_ip: number;
  ip_lockout_duration: number; // in milliseconds
  suspicious_activity_threshold: number;
  geolocation_monitoring: boolean;
  auto_block_suspicious_ips: boolean;
}
export class IpSecurityManager {
  private adminUtils = getAdminDatabaseUtils();
  // In-memory storage (use Redis in production)
  private ipAccessRecords = new Map<string, IpAccessRecord>();
  private ipWhitelist = new Map<string, IpWhitelistEntry>();
  private blockedIps = new Map<string, { blockedUntil: Date; reason: string }>();
  private failedAttempts = new Map<string, { count: number; lastAttempt: Date }>();
  // Default security configuration
  private config: IpSecurityConfig = {
    super_admin_whitelist_enabled: false,
    admin_whitelist_enabled: false,
    max_failed_attempts_per_ip: 10,
    ip_lockout_duration: 30 * 60 * 1000, // 30 minutes
    suspicious_activity_threshold: 20,
    geolocation_monitoring: true,
    auto_block_suspicious_ips: false
  };
  constructor() {
    this.loadConfiguration();
    this.loadWhitelist();
  }
  /**
   * Check if IP address is allowed for user role
   */
  async checkIpAccess(ipAddress: string, user: User): Promise<{ allowed: boolean; reason?: string }> {
    // Check if IP is blocked
    if (await this.isIpBlocked(ipAddress)) {
      return { allowed: false, reason: 'IP address is temporarily blocked' };
    }
    // Check whitelist requirements for super admins
    if (user.role === 'super_admin' && this.config.super_admin_whitelist_enabled) {
      const whitelisted = await this.isIpWhitelisted(ipAddress, user.user_id, 'super_admin');
      if (!whitelisted) {
        await this.logSecurityEvent({
          event_type: 'suspicious_activity',
          user_id: user.user_id,
          ip_address: ipAddress,
          details: {
            reason: 'super_admin_not_whitelisted',
            user_role: user.role,
            whitelist_enabled: true
          },
          severity: 'high'

        return { allowed: false, reason: 'IP address not whitelisted for super admin access' };
      }
    }
    // Check whitelist requirements for admins
    if (user.role === 'admin' && this.config.admin_whitelist_enabled) {
      const whitelisted = await this.isIpWhitelisted(ipAddress, user.user_id, 'admin');
      if (!whitelisted) {
        await this.logSecurityEvent({
          event_type: 'suspicious_activity',
          user_id: user.user_id,
          ip_address: ipAddress,
          details: {
            reason: 'admin_not_whitelisted',
            user_role: user.role,
            whitelist_enabled: true
          },
          severity: 'medium'

        return { allowed: false, reason: 'IP address not whitelisted for admin access' };
      }
    }
    return { allowed: true };
  }
  /**
   * Record IP access for tracking and analysis
   */
  async recordIpAccess(ipAddress: string, user: User, userAgent?: string): Promise<void> {
    const key = `${ipAddress}:${user.user_id}`;
    const now = new Date();
    let record = this.ipAccessRecords.get(key);
    if (!record) {
      // Create new access record
      record = {
        ip_address: ipAddress,
        user_id: user.user_id,
        user_email: user.email,
        user_role: user.role,
        access_count: 0,
        first_seen: now,
        last_seen: now,
        user_agent: userAgent,
        is_suspicious: false,
        is_blocked: false
      };
      // Get geolocation if enabled
      if (this.config.geolocation_monitoring) {
        record.location = await this.getIpLocation(ipAddress);
      }
    }
    // Update access record
    record.access_count++;
    record.last_seen = now;
    record.user_agent = userAgent || record.user_agent;
    this.ipAccessRecords.set(key, record);
    // Check for suspicious activity
    await this.checkSuspiciousActivity(record);
    // Log access
    await this.adminUtils.createAuditLog({
      user_id: user.user_id,
      action: 'ip.access_recorded',
      resource_type: 'ip_security',
      resource_id: ipAddress,
      details: {
        access_count: record.access_count,
        first_seen: record.first_seen.toISOString(),
        location: record.location,
        user_role: user.role
      },
      ip_address: ipAddress,
      user_agent: userAgent

  }
  /**
   * Record failed login attempt from IP
   */
  async recordFailedAttempt(ipAddress: string, userIdentifier?: string): Promise<void> {
    const now = new Date();
    const attempts = this.failedAttempts.get(ipAddress) || { count: 0, lastAttempt: now };
    // Reset count if last attempt was more than 1 hour ago
    if (now.getTime() - attempts.lastAttempt.getTime() > 60 * 60 * 1000) {
      attempts.count = 0;
    }
    attempts.count++;
    attempts.lastAttempt = now;
    this.failedAttempts.set(ipAddress, attempts);
    // Check if IP should be blocked
    if (attempts.count >= this.config.max_failed_attempts_per_ip) {
      await this.blockIp(ipAddress, 'excessive_failed_attempts', this.config.ip_lockout_duration);
    }
    // Log failed attempt
    await this.adminUtils.createAuditLog({
      user_id: 'system',
      action: 'ip.failed_attempt',
      resource_type: 'ip_security',
      resource_id: ipAddress,
      details: {
        attempt_count: attempts.count,
        user_identifier: userIdentifier,
        threshold: this.config.max_failed_attempts_per_ip
      },
      ip_address: ipAddress

  }
  /**
   * Add IP to whitelist
   */
  async addToWhitelist(
    ipAddress: string, 
    description: string, 
    createdBy: string,
    userId?: string,
    roleRestriction?: 'super_admin' | 'admin'
  ): Promise<IpWhitelistEntry> {
    const entry: IpWhitelistEntry = {
      id: this.generateId(),
      ip_address: ipAddress,
      description,
      user_id: userId,
      role_restriction: roleRestriction,
      created_by: createdBy,
      created_at: new Date(),
      is_active: true
    };
    this.ipWhitelist.set(ipAddress, entry);
    // Log whitelist addition
    await this.adminUtils.createAuditLog({
      user_id: createdBy,
      action: 'ip.whitelist_added',
      resource_type: 'ip_whitelist',
      resource_id: entry.id,
      details: {
        ip_address: ipAddress,
        description,
        user_id: userId,
        role_restriction: roleRestriction
      }

    return entry;
  }
  /**
   * Remove IP from whitelist
   */
  async removeFromWhitelist(ipAddress: string, removedBy: string): Promise<boolean> {
    const entry = this.ipWhitelist.get(ipAddress);
    if (!entry) {
      return false;
    }
    this.ipWhitelist.delete(ipAddress);
    // Log whitelist removal
    await this.adminUtils.createAuditLog({
      user_id: removedBy,
      action: 'ip.whitelist_removed',
      resource_type: 'ip_whitelist',
      resource_id: entry.id,
      details: {
        ip_address: ipAddress,
        description: entry.description,
        removed_by: removedBy
      }

    return true;
  }
  /**
   * Block IP address
   */
  async blockIp(ipAddress: string, reason: string, durationMs: number): Promise<void> {
    const blockedUntil = new Date(Date.now() + durationMs);
    this.blockedIps.set(ipAddress, { blockedUntil, reason });
    // Log IP blocking
    await this.adminUtils.createAuditLog({
      user_id: 'system',
      action: 'ip.blocked',
      resource_type: 'ip_security',
      resource_id: ipAddress,
      details: {
        reason,
        blocked_until: blockedUntil.toISOString(),
        duration_ms: durationMs
      },
      ip_address: ipAddress

    // Log security event
    await this.logSecurityEvent({
      event_type: 'suspicious_activity',
      ip_address: ipAddress,
      details: {
        action: 'ip_blocked',
        reason,
        blocked_until: blockedUntil.toISOString()
      },
      severity: 'medium'

  }
  /**
   * Unblock IP address
   */
  async unblockIp(ipAddress: string, unblockedBy: string): Promise<boolean> {
    const blocked = this.blockedIps.get(ipAddress);
    if (!blocked) {
      return false;
    }
    this.blockedIps.delete(ipAddress);
    // Log IP unblocking
    await this.adminUtils.createAuditLog({
      user_id: unblockedBy,
      action: 'ip.unblocked',
      resource_type: 'ip_security',
      resource_id: ipAddress,
      details: {
        original_reason: blocked.reason,
        unblocked_by: unblockedBy
      },
      ip_address: ipAddress

    return true;
  }
  /**
   * Get IP access statistics
   */
  getIpStatistics(): {
    totalUniqueIps: number;
    whitelistedIps: number;
    blockedIps: number;
    suspiciousIps: number;
    topAccessedIps: Array<{ ip: string; accessCount: number; users: number }>;
  } {
    const ipStats = new Map<string, { accessCount: number; users: Set<string> }>();
    let suspiciousCount = 0;
    // Aggregate access data
    for (const record of this.ipAccessRecords.values()) {
      const stats = ipStats.get(record.ip_address) || { accessCount: 0, users: new Set() };
      stats.accessCount += record.access_count;
      stats.users.add(record.user_id);
      ipStats.set(record.ip_address, stats);
      if (record.is_suspicious) {
        suspiciousCount++;
      }
    }
    // Get top accessed IPs
    const topAccessedIps = Array.from(ipStats.entries())
      .map(([ip, stats]) => ({
        ip,
        accessCount: stats.accessCount,
        users: stats.users.size
      }))
      .sort((a, b) => b.accessCount - a.accessCount)
      .slice(0, 10);
    return {
      totalUniqueIps: ipStats.size,
      whitelistedIps: this.ipWhitelist.size,
      blockedIps: this.blockedIps.size,
      suspiciousIps: suspiciousCount,
      topAccessedIps
    };
  }
  /**
   * Get whitelist entries
   */
  getWhitelistEntries(): IpWhitelistEntry[] {
    return Array.from(this.ipWhitelist.values()).filter(entry => entry.is_active);
  }
  /**
   * Get blocked IPs
   */
  getBlockedIps(): Array<{ ip: string; reason: string; blockedUntil: Date }> {
    const now = new Date();
    const blocked: Array<{ ip: string; reason: string; blockedUntil: Date }> = [];
    for (const [ip, blockInfo] of this.blockedIps.entries()) {
      if (blockInfo.blockedUntil > now) {
        blocked.push({
          ip,
          reason: blockInfo.reason,
          blockedUntil: blockInfo.blockedUntil

      }
    }
    return blocked;
  }
  /**
   * Update security configuration
   */
  async updateConfiguration(newConfig: Partial<IpSecurityConfig>, updatedBy: string): Promise<void> {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...newConfig };
    // Log configuration change
    await this.adminUtils.createAuditLog({
      user_id: updatedBy,
      action: 'ip.config_updated',
      resource_type: 'ip_security_config',
      details: {
        old_config: oldConfig,
        new_config: this.config,
        updated_by: updatedBy
      }

  }
  /**
   * Check if IP is whitelisted
   */
  private async isIpWhitelisted(ipAddress: string, userId?: string, role?: string): Promise<boolean> {
    const entry = this.ipWhitelist.get(ipAddress);
    if (!entry || !entry.is_active) {
      return false;
    }
    // Check user-specific whitelist
    if (entry.user_id && entry.user_id !== userId) {
      return false;
    }
    // Check role restriction
    if (entry.role_restriction && entry.role_restriction !== role) {
      return false;
    }
    return true;
  }
  /**
   * Check if IP is blocked
   */
  private async isIpBlocked(ipAddress: string): Promise<boolean> {
    const blocked = this.blockedIps.get(ipAddress);
    if (!blocked) {
      return false;
    }
    const now = new Date();
    if (now > blocked.blockedUntil) {
      // Block has expired, remove it
      this.blockedIps.delete(ipAddress);
      return false;
    }
    return true;
  }
  /**
   * Check for suspicious activity patterns
   */
  private async checkSuspiciousActivity(record: IpAccessRecord): Promise<void> {
    let suspicious = false;
    const reasons: string[] = [];
    // Check access frequency
    if (record.access_count > this.config.suspicious_activity_threshold) {
      suspicious = true;
      reasons.push('high_access_frequency');
    }
    // Check for role escalation attempts (multiple users from same IP)
    const sameIpRecords = Array.from(this.ipAccessRecords.values())
      .filter(r => r.ip_address === record.ip_address && r.user_id !== record.user_id);
    if (sameIpRecords.length > 2) {
      suspicious = true;
      reasons.push('multiple_users_same_ip');
    }
    // Check for admin access from new location
    if (record.user_role === 'super_admin' || record.user_role === 'admin') {
      const previousLocations = Array.from(this.ipAccessRecords.values())
        .filter(r => r.user_id === record.user_id && r.ip_address !== record.ip_address)
        .map(r => r.location?.country)
        .filter(Boolean);
      if (previousLocations.length > 0 && record.location?.country && 
          !previousLocations.includes(record.location.country)) {
        suspicious = true;
        reasons.push('new_geographic_location');
      }
    }
    if (suspicious) {
      record.is_suspicious = true;
      await this.logSecurityEvent({
        event_type: 'suspicious_activity',
        user_id: record.user_id,
        ip_address: record.ip_address,
        details: {
          reasons,
          access_count: record.access_count,
          user_role: record.user_role,
          location: record.location
        },
        severity: 'medium'

      // Auto-block if enabled
      if (this.config.auto_block_suspicious_ips) {
        await this.blockIp(record.ip_address, 'suspicious_activity_detected', this.config.ip_lockout_duration);
      }
    }
  }
  /**
   * Get IP geolocation (mock implementation)
   */
  private async getIpLocation(ipAddress: string): Promise<{ country?: string; region?: string; city?: string; timezone?: string }> {
    // In production, use a real geolocation service like MaxMind or ipapi
    // This is a mock implementation
    return {
      country: 'Unknown',
      region: 'Unknown',
      city: 'Unknown',
      timezone: 'UTC'
    };
  }
  /**
   * Log security event
   */
  private async logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'resolved' | 'created_at'>): Promise<void> {
    // This would integrate with the main security manager
  }
  /**
   * Load configuration from database
   */
  private async loadConfiguration(): Promise<void> {
    try {
      const configs = await this.adminUtils.getSystemConfig('security');
      for (const config of configs) {
        switch (config.key) {
          case 'super_admin_whitelist_enabled':
            this.config.super_admin_whitelist_enabled = config.value === 'true';
            break;
          case 'admin_whitelist_enabled':
            this.config.admin_whitelist_enabled = config.value === 'true';
            break;
          case 'max_failed_attempts_per_ip':
            this.config.max_failed_attempts_per_ip = parseInt(config.value as string) || 10;
            break;
          case 'ip_lockout_duration':
            this.config.ip_lockout_duration = parseInt(config.value as string) || 30 * 60 * 1000;
            break;
        }
      }
    } catch (error) {
    }
  }
  /**
   * Load whitelist from database
   */
  private async loadWhitelist(): Promise<void> {
    // In production, load from database
    // For now, this is a placeholder
  }
  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `ip_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }
}
// Export singleton instance
export const ipSecurityManager = new IpSecurityManager();
