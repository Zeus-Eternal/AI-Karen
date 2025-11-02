/**
 * Audit Logger Tests
 * 
 * Comprehensive tests for the audit logging system to ensure accuracy,
 * completeness, and reliability of audit log creation and retrieval.
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { NextRequest } from 'next/server';
import {  AuditLogger, getAuditLogger, auditLog, AUDIT_ACTIONS, AUDIT_RESOURCE_TYPES } from '../audit-logger';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';

// Mock the database utilities
vi.mock('@/lib/database/admin-utils');

const mockDbUtils = {
  createAuditLog: vi.fn(),
  getAuditLogs: vi.fn(),
};

(getAdminDatabaseUtils as Mock).mockReturnValue(mockDbUtils);

describe('AuditLogger', () => {
  let auditLogger: AuditLogger;
  let mockRequest: NextRequest;

  beforeEach(() => {
    auditLogger = new AuditLogger();
    
    // Create mock request
    mockRequest = {
      ip: '192.168.1.100',
      headers: new Map([
        ['user-agent', 'Mozilla/5.0 Test Browser'],
        ['x-forwarded-for', '10.0.0.1, 192.168.1.100'],
        ['x-real-ip', '10.0.0.1']
      ])
    } as any;

    // Reset mocks
    vi.clearAllMocks();

  afterEach(() => {
    vi.restoreAllMocks();

  describe('log method', () => {
    it('should create audit log with basic information', async () => {
      const mockAuditId = 'audit-123';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const result = await auditLogger.log(
        'user-123',
        AUDIT_ACTIONS.USER_CREATE,
        AUDIT_RESOURCE_TYPES.USER
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.USER_CREATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: {},
        ip_address: undefined,
        user_agent: undefined


    it('should create audit log with all optional parameters', async () => {
      const mockAuditId = 'audit-456';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const details = { email: 'test@example.com', role: 'admin' };

      const result = await auditLogger.log(
        'user-123',
        AUDIT_ACTIONS.USER_CREATE,
        AUDIT_RESOURCE_TYPES.USER,
        {
          resourceId: 'user-456',
          details,
          request: mockRequest
        }
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.USER_CREATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: 'user-456',
        details,
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should extract IP address from x-forwarded-for header', async () => {
      const mockAuditId = 'audit-789';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      // Mock request without direct IP but with x-forwarded-for
      const requestWithForwardedFor = {
        headers: new Map([
          ['x-forwarded-for', '203.0.113.1, 192.168.1.100'],
          ['user-agent', 'Test Browser']
        ])
      } as any;

      await auditLogger.log(
        'user-123',
        AUDIT_ACTIONS.AUTH_LOGIN,
        AUDIT_RESOURCE_TYPES.SESSION,
        { request: requestWithForwardedFor }
      );

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          ip_address: '203.0.113.1'
        })
      );

    it('should handle manual IP and user agent override', async () => {
      const mockAuditId = 'audit-manual';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      await auditLogger.log(
        'user-123',
        AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
        AUDIT_RESOURCE_TYPES.SECURITY_POLICY,
        {
          ip_address: '203.0.113.50',
          user_agent: 'Custom Agent'
        }
      );

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          ip_address: '203.0.113.50',
          user_agent: 'Custom Agent'
        })
      );


  describe('specialized logging methods', () => {
    it('should log user action correctly', async () => {
      const mockAuditId = 'audit-user-action';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const details = { old_role: 'user', new_role: 'admin' };

      const result = await auditLogger.logUserAction(
        'admin-123',
        AUDIT_ACTIONS.USER_ROLE_CHANGE,
        'user-456',
        details,
        mockRequest
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_ROLE_CHANGE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: 'user-456',
        details,
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log authentication action correctly', async () => {
      const mockAuditId = 'audit-auth-action';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const details = { login_method: 'password' };

      const result = await auditLogger.logAuthAction(
        'user-123',
        AUDIT_ACTIONS.AUTH_LOGIN,
        details,
        mockRequest
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.AUTH_LOGIN,
        resource_type: AUDIT_RESOURCE_TYPES.SESSION,
        resource_id: undefined,
        details,
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log system config action correctly', async () => {
      const mockAuditId = 'audit-config-action';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const details = { old_value: 'false', new_value: 'true' };

      const result = await auditLogger.logSystemConfigAction(
        'admin-123',
        AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
        'mfa_required',
        details,
        mockRequest
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
        resource_type: AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG,
        resource_id: 'mfa_required',
        details,
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log security event with severity', async () => {
      const mockAuditId = 'audit-security-event';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const details = { threat_type: 'brute_force', attempts: 5 };

      const result = await auditLogger.logSecurityEvent(
        'user-123',
        AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
        details,
        mockRequest
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
        resource_type: AUDIT_RESOURCE_TYPES.SECURITY_POLICY,
        resource_id: undefined,
        details: expect.objectContaining({
          ...details,
          severity: 'medium',
          timestamp: expect.any(String)
        }),
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log bulk operation correctly', async () => {
      const mockAuditId = 'audit-bulk-operation';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const userIds = ['user-1', 'user-2', 'user-3'];
      const details = { operation_type: 'activation' };

      const result = await auditLogger.logBulkOperation(
        'admin-123',
        AUDIT_ACTIONS.USER_BULK_ACTIVATE,
        AUDIT_RESOURCE_TYPES.USER,
        userIds,
        details,
        mockRequest
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_BULK_ACTIVATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: {
          ...details,
          resource_ids: userIds,
          count: 3
        },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'



  describe('audit log retrieval', () => {
    it('should get audit logs with default parameters', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-1',
            user_id: 'user-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            timestamp: new Date()
          }
        ],
        pagination: {
          page: 1,
          limit: 50,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.getAuditLogs();

      expect(result).toEqual(mockLogs);
      expect(mockDbUtils.getAuditLogs).toHaveBeenCalledWith(
        {},
        { page: 1, limit: 50 }
      );

    it('should get audit logs with filter and pagination', async () => {
      const filter = { user_id: 'user-123', action: AUDIT_ACTIONS.USER_CREATE };
      const pagination = { page: 2, limit: 25 };

      const mockLogs = {
        data: [],
        pagination: {
          page: 2,
          limit: 25,
          total: 0,
          total_pages: 0,
          has_next: false,
          has_prev: true
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.getAuditLogs(filter, pagination);

      expect(result).toEqual(mockLogs);
      expect(mockDbUtils.getAuditLogs).toHaveBeenCalledWith(filter, pagination);

    it('should get user audit logs', async () => {
      const userId = 'user-123';
      const mockLogs = {
        data: [],
        pagination: {
          page: 1,
          limit: 50,
          total: 0,
          total_pages: 0,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.getUserAuditLogs(userId);

      expect(result).toEqual(mockLogs);
      expect(mockDbUtils.getAuditLogs).toHaveBeenCalledWith(
        { user_id: userId },
        { page: 1, limit: 50 }
      );

    it('should get recent audit logs', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-1',
            user_id: 'user-123',
            action: AUDIT_ACTIONS.AUTH_LOGIN,
            resource_type: AUDIT_RESOURCE_TYPES.SESSION,
            timestamp: new Date()
          }
        ],
        pagination: {
          page: 1,
          limit: 100,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.getRecentAuditLogs(100);

      expect(result).toEqual(mockLogs.data);
      expect(mockDbUtils.getAuditLogs).toHaveBeenCalledWith(
        { start_date: expect.any(Date) },
        { page: 1, limit: 100, sort_by: 'timestamp', sort_order: 'desc' }
      );


  describe('audit log statistics', () => {
    it('should calculate audit log statistics', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-1',
            user_id: 'user-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            timestamp: new Date('2024-01-01')
          },
          {
            id: 'log-2',
            user_id: 'user-456',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            timestamp: new Date('2024-01-02')
          },
          {
            id: 'log-3',
            user_id: 'user-123',
            action: AUDIT_ACTIONS.AUTH_LOGIN,
            resource_type: AUDIT_RESOURCE_TYPES.SESSION,
            timestamp: new Date('2024-01-02')
          }
        ],
        pagination: {
          page: 1,
          limit: 10000,
          total: 3,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.getAuditLogStats();

      expect(result).toEqual({
        total_logs: 3,
        unique_users: 2,
        top_actions: [
          { action: AUDIT_ACTIONS.USER_CREATE, count: 2 },
          { action: AUDIT_ACTIONS.AUTH_LOGIN, count: 1 }
        ],
        top_resources: [
          { resource_type: AUDIT_RESOURCE_TYPES.USER, count: 2 },
          { resource_type: AUDIT_RESOURCE_TYPES.SESSION, count: 1 }
        ],
        logs_by_day: [
          { date: '2024-01-01', count: 1 },
          { date: '2024-01-02', count: 2 }
        ]



  describe('search functionality', () => {
    it('should search audit logs by text', async () => {
      const mockLogs = {
        data: [
          {
            id: 'log-1',
            user_id: 'user-123',
            action: AUDIT_ACTIONS.USER_CREATE,
            resource_type: AUDIT_RESOURCE_TYPES.USER,
            resource_id: 'user-456',
            user: { email: 'test@example.com' },
            timestamp: new Date()
          }
        ],
        pagination: {
          page: 1,
          limit: 10000,
          total: 1,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      };

      mockDbUtils.getAuditLogs.mockResolvedValue(mockLogs);

      const result = await auditLogger.searchAuditLogs('create');

      expect(result.data).toHaveLength(1);
      expect(result.data[0].action).toBe(AUDIT_ACTIONS.USER_CREATE);


  describe('singleton instance', () => {
    it('should return the same instance', () => {
      const instance1 = getAuditLogger();
      const instance2 = getAuditLogger();

      expect(instance1).toBe(instance2);


  describe('convenience functions', () => {
    beforeEach(() => {
      mockDbUtils.createAuditLog.mockResolvedValue('audit-convenience');

    it('should log user created event', async () => {
      await auditLog.userCreated('admin-123', 'user-456', 'test@example.com', 'user', mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_CREATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: 'user-456',
        details: { email: 'test@example.com', role: 'user' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log successful login event', async () => {
      await auditLog.loginSuccessful('user-123', mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.AUTH_LOGIN,
        resource_type: AUDIT_RESOURCE_TYPES.SESSION,
        resource_id: undefined,
        details: {},
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log failed login event', async () => {
      await auditLog.loginFailed('user-123', 'invalid_password', mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.AUTH_LOGIN_FAILED,
        resource_type: AUDIT_RESOURCE_TYPES.SESSION,
        resource_id: undefined,
        details: { reason: 'invalid_password' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log config update event', async () => {
      await auditLog.configUpdated('admin-123', 'mfa_required', false, true, mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
        resource_type: AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG,
        resource_id: 'mfa_required',
        details: { old_value: false, new_value: true },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log security breach event', async () => {
      const details = { threat_type: 'sql_injection', severity: 'high' };
      await auditLog.securityBreach('user-123', details, mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'user-123',
        action: AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
        resource_type: AUDIT_RESOURCE_TYPES.SECURITY_POLICY,
        resource_id: undefined,
        details: { ...details, severity: 'critical' },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log bulk user activation', async () => {
      const userIds = ['user-1', 'user-2', 'user-3'];
      await auditLog.bulkUserActivation('admin-123', userIds, mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_BULK_ACTIVATE,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: {
          resource_ids: userIds,
          count: 3
        },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'


    it('should log data export event', async () => {
      await auditLog.dataExported('admin-123', 'csv', 150, mockRequest);

      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith({
        user_id: 'admin-123',
        action: AUDIT_ACTIONS.USER_EXPORT,
        resource_type: AUDIT_RESOURCE_TYPES.USER,
        resource_id: undefined,
        details: { export_type: 'csv', record_count: 150 },
        ip_address: '192.168.1.100',
        user_agent: 'Mozilla/5.0 Test Browser'



  describe('error handling', () => {
    it('should handle database errors gracefully', async () => {
      const dbError = new Error('Database connection failed');
      mockDbUtils.createAuditLog.mockRejectedValue(dbError);

      await expect(
        auditLogger.log('user-123', AUDIT_ACTIONS.USER_CREATE, AUDIT_RESOURCE_TYPES.USER)
      ).rejects.toThrow('Database connection failed');

    it('should handle missing request headers gracefully', async () => {
      const mockAuditId = 'audit-no-headers';
      mockDbUtils.createAuditLog.mockResolvedValue(mockAuditId);

      const requestWithoutHeaders = {
        headers: new Map()
      } as any;

      const result = await auditLogger.log(
        'user-123',
        AUDIT_ACTIONS.AUTH_LOGIN,
        AUDIT_RESOURCE_TYPES.SESSION,
        { request: requestWithoutHeaders }
      );

      expect(result).toBe(mockAuditId);
      expect(mockDbUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          ip_address: undefined,
          user_agent: undefined
        })
      );


