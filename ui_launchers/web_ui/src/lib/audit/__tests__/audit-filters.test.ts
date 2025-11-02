/**
 * Audit Filters Tests
 * 
 * Tests for audit log filtering, searching, and export functionality
 * to ensure accurate filtering and data processing.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {  AuditFilterBuilder, AuditSearchParser, AuditLogExporter, AUDIT_FILTER_PRESETS, ACTION_CATEGORIES, RESOURCE_TYPE_CATEGORIES, auditFilters, auditPagination } from '../audit-filters';
import { AuditLogFilter } from '@/types/admin';

describe('AuditFilterBuilder', () => {
  let builder: AuditFilterBuilder;

  beforeEach(() => {
    builder = new AuditFilterBuilder();

  describe('filter building', () => {
    it('should build filter by user', () => {
      const filter = builder.byUser('user-123').build();
      
      expect(filter).toEqual({
        user_id: 'user-123'


    it('should build filter by action', () => {
      const filter = builder.byAction('user.create').build();
      
      expect(filter).toEqual({
        action: 'user.create'


    it('should build filter by resource type', () => {
      const filter = builder.byResourceType('user').build();
      
      expect(filter).toEqual({
        resource_type: 'user'


    it('should build filter by date range', () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');
      
      const filter = builder.byDateRange(startDate, endDate).build();
      
      expect(filter).toEqual({
        start_date: startDate,
        end_date: endDate


    it('should build filter by start date only', () => {
      const startDate = new Date('2024-01-01');
      
      const filter = builder.fromDate(startDate).build();
      
      expect(filter).toEqual({
        start_date: startDate


    it('should build filter by end date only', () => {
      const endDate = new Date('2024-01-31');
      
      const filter = builder.toDate(endDate).build();
      
      expect(filter).toEqual({
        end_date: endDate


    it('should build filter by IP address', () => {
      const filter = builder.byIpAddress('192.168.1.100').build();
      
      expect(filter).toEqual({
        ip_address: '192.168.1.100'


    it('should chain multiple filters', () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');
      
      const filter = builder
        .byUser('user-123')
        .byAction('user.create')
        .byResourceType('user')
        .byDateRange(startDate, endDate)
        .byIpAddress('192.168.1.100')
        .build();
      
      expect(filter).toEqual({
        user_id: 'user-123',
        action: 'user.create',
        resource_type: 'user',
        start_date: startDate,
        end_date: endDate,
        ip_address: '192.168.1.100'


    it('should apply preset filter', () => {
      const filter = builder.applyPreset('TODAY').build();
      
      expect(filter.start_date).toBeInstanceOf(Date);
      expect(filter.end_date).toBeInstanceOf(Date);
      
      // Check that it's roughly today
      const today = new Date();
      const startOfDay = new Date(today.setHours(0, 0, 0, 0));
      const endOfDay = new Date(today.setHours(23, 59, 59, 999));
      
      expect(filter.start_date?.getDate()).toBe(startOfDay.getDate());
      expect(filter.end_date?.getDate()).toBe(endOfDay.getDate());

    it('should reset filter', () => {
      const filter = builder
        .byUser('user-123')
        .byAction('user.create')
        .reset()
        .build();
      
      expect(filter).toEqual({});

    it('should handle action category filter', () => {
      const filter = builder.byActionCategory('USER_MANAGEMENT').build();
      
      // Should set the first action from the category
      expect(filter.action).toBe(ACTION_CATEGORIES.USER_MANAGEMENT.actions[0]);



describe('AuditSearchParser', () => {
  describe('parseSearchQuery', () => {
    it('should parse simple text search', () => {
      const result = AuditSearchParser.parseSearchQuery('login failed');
      
      expect(result).toEqual({
        textSearch: 'login failed',
        filters: {},
        suggestions: []


    it('should parse user filter', () => {
      const result = AuditSearchParser.parseSearchQuery('user:john@example.com');
      
      expect(result).toEqual({
        textSearch: undefined,
        filters: {
          user_id: 'john@example.com'
        },
        suggestions: []


    it('should parse action filter', () => {
      const result = AuditSearchParser.parseSearchQuery('action:user.create');
      
      expect(result).toEqual({
        textSearch: undefined,
        filters: {
          action: 'user.create'
        },
        suggestions: []


    it('should parse resource filter', () => {
      const result = AuditSearchParser.parseSearchQuery('resource:user');
      
      expect(result).toEqual({
        textSearch: undefined,
        filters: {
          resource_type: 'user'
        },
        suggestions: []


    it('should parse IP address filter', () => {
      const result = AuditSearchParser.parseSearchQuery('ip:192.168.1.100');
      
      expect(result).toEqual({
        textSearch: undefined,
        filters: {
          ip_address: '192.168.1.100'
        },
        suggestions: []


    it('should parse date filters', () => {
      const result = AuditSearchParser.parseSearchQuery('from:2024-01-01 to:2024-01-31');
      
      expect(result.filters.start_date).toEqual(new Date('2024-01-01'));
      expect(result.filters.end_date).toEqual(new Date('2024-01-31'));
      expect(result.textSearch).toBeUndefined();

    it('should parse mixed query with text and filters', () => {
      const result = AuditSearchParser.parseSearchQuery('failed login user:john@example.com action:auth.login_failed');
      
      expect(result).toEqual({
        textSearch: 'failed login',
        filters: {
          user_id: 'john@example.com',
          action: 'auth.login_failed'
        },
        suggestions: []


    it('should generate suggestions for partial input', () => {
      const result = AuditSearchParser.parseSearchQuery('user:');
      
      expect(result.suggestions).toContain('user:john@example.com');
      expect(result.suggestions).toContain('user:admin@company.com');

    it('should generate action suggestions', () => {
      const result = AuditSearchParser.parseSearchQuery('action:');
      
      expect(result.suggestions.length).toBeGreaterThan(0);
      expect(result.suggestions).toContain('user.create');

    it('should generate resource suggestions', () => {
      const result = AuditSearchParser.parseSearchQuery('resource:');
      
      expect(result.suggestions.length).toBeGreaterThan(0);
      expect(result.suggestions).toContain('user');


  describe('getSearchSuggestions', () => {
    it('should return basic suggestions for short input', () => {
      const suggestions = AuditSearchParser.getSearchSuggestions('u');
      
      expect(suggestions).toContain('user:email@domain.com');
      expect(suggestions).toContain('action:user.create');

    it('should return action suggestions for action prefix', () => {
      const suggestions = AuditSearchParser.getSearchSuggestions('action:user');
      
      expect(suggestions.some(s => s.includes('user.create'))).toBe(true);

    it('should return resource suggestions for resource prefix', () => {
      const suggestions = AuditSearchParser.getSearchSuggestions('resource:u');
      
      expect(suggestions.some(s => s.includes('user'))).toBe(true);

    it('should limit suggestions to 10', () => {
      const suggestions = AuditSearchParser.getSearchSuggestions('action:');
      
      expect(suggestions.length).toBeLessThanOrEqual(10);



describe('AuditLogExporter', () => {
  const mockLogs = [
    {
      id: 'log-1',
      user_id: 'user-123',
      action: 'user.create',
      resource_type: 'user',
      resource_id: 'user-456',
      details: { email: 'test@example.com', role: 'user' },
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0',
      timestamp: new Date('2024-01-01T10:00:00Z'),
      user: {
        user_id: 'user-123',
        email: 'admin@example.com',
        full_name: 'Admin User'
      }
    },
    {
      id: 'log-2',
      user_id: 'user-456',
      action: 'auth.login',
      resource_type: 'session',
      resource_id: null,
      details: {},
      ip_address: '192.168.1.101',
      user_agent: 'Chrome/120.0',
      timestamp: new Date('2024-01-01T11:00:00Z'),
      user: {
        user_id: 'user-456',
        email: 'user@example.com',
        full_name: 'Regular User'
      }
    }
  ];

  describe('toCsv', () => {
    it('should export logs to CSV with headers', () => {
      const csv = AuditLogExporter.toCsv(mockLogs, true);
      
      const lines = csv.split('\n');
      expect(lines[0]).toContain('Timestamp');
      expect(lines[0]).toContain('User Email');
      expect(lines[0]).toContain('Action');
      
      expect(lines[1]).toContain('2024-01-01T10:00:00.000Z');
      expect(lines[1]).toContain('admin@example.com');
      expect(lines[1]).toContain('user.create');

    it('should export logs to CSV without headers', () => {
      const csv = AuditLogExporter.toCsv(mockLogs, false);
      
      const lines = csv.split('\n');
      expect(lines[0]).not.toContain('Timestamp');
      expect(lines[0]).toContain('2024-01-01T10:00:00.000Z');

    it('should handle empty logs array', () => {
      const csv = AuditLogExporter.toCsv([]);
      
      expect(csv).toBe('');

    it('should escape CSV special characters', () => {
      const logsWithSpecialChars = [{
        ...mockLogs[0],
        details: { message: 'Hello, "World"!\nNew line here' }
      }];
      
      const csv = AuditLogExporter.toCsv(logsWithSpecialChars, true);
      
      expect(csv).toContain('""Hello, """"World""""!\nNew line here""');


  describe('toJson', () => {
    it('should export logs to JSON', () => {
      const json = AuditLogExporter.toJson(mockLogs);
      const parsed = JSON.parse(json);
      
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed).toHaveLength(2);
      expect(parsed[0].id).toBe('log-1');

    it('should export logs to pretty JSON', () => {
      const json = AuditLogExporter.toJson(mockLogs, true);
      
      expect(json).toContain('\n');
      expect(json).toContain('  ');

    it('should handle empty logs array', () => {
      const json = AuditLogExporter.toJson([]);
      const parsed = JSON.parse(json);
      
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed).toHaveLength(0);


  describe('generateFilename', () => {
    it('should generate basic filename', () => {
      const filename = AuditLogExporter.generateFilename('csv');
      
      expect(filename).toMatch(/^audit-logs-\d{4}-\d{2}-\d{2}\.csv$/);

    it('should include date range in filename', () => {
      const filter: AuditLogFilter = {
        start_date: new Date('2024-01-01'),
        end_date: new Date('2024-01-31')
      };
      
      const filename = AuditLogExporter.generateFilename('json', filter);
      
      expect(filename).toContain('2024-01-01-to-2024-01-31');
      expect(filename).toEndWith('.json');

    it('should include action in filename', () => {
      const filter: AuditLogFilter = {
        action: 'user.create'
      };
      
      const filename = AuditLogExporter.generateFilename('csv', filter);
      
      expect(filename).toContain('user-create');

    it('should include resource type in filename', () => {
      const filter: AuditLogFilter = {
        resource_type: 'user'
      };
      
      const filename = AuditLogExporter.generateFilename('csv', filter);
      
      expect(filename).toContain('user');

    it('should include user ID in filename', () => {
      const filter: AuditLogFilter = {
        user_id: 'user-12345678-abcd-efgh'
      };
      
      const filename = AuditLogExporter.generateFilename('csv', filter);
      
      expect(filename).toContain('user-user-123');



describe('AUDIT_FILTER_PRESETS', () => {
  it('should have valid preset filters', () => {
    expect(AUDIT_FILTER_PRESETS.TODAY).toBeDefined();
    expect(AUDIT_FILTER_PRESETS.YESTERDAY).toBeDefined();
    expect(AUDIT_FILTER_PRESETS.LAST_7_DAYS).toBeDefined();
    expect(AUDIT_FILTER_PRESETS.LAST_30_DAYS).toBeDefined();
    expect(AUDIT_FILTER_PRESETS.THIS_MONTH).toBeDefined();
    expect(AUDIT_FILTER_PRESETS.LAST_MONTH).toBeDefined();

  it('should have proper date ranges', () => {
    const today = AUDIT_FILTER_PRESETS.TODAY.filter;
    expect(today.start_date).toBeInstanceOf(Date);
    expect(today.end_date).toBeInstanceOf(Date);
    expect(today.start_date!.getTime()).toBeLessThan(today.end_date!.getTime());


describe('ACTION_CATEGORIES', () => {
  it('should have valid action categories', () => {
    expect(ACTION_CATEGORIES.USER_MANAGEMENT).toBeDefined();
    expect(ACTION_CATEGORIES.ADMIN_MANAGEMENT).toBeDefined();
    expect(ACTION_CATEGORIES.AUTHENTICATION).toBeDefined();
    expect(ACTION_CATEGORIES.SYSTEM_CONFIG).toBeDefined();
    expect(ACTION_CATEGORIES.SECURITY).toBeDefined();
    expect(ACTION_CATEGORIES.AUDIT).toBeDefined();

  it('should have actions in each category', () => {
    Object.values(ACTION_CATEGORIES).forEach(category => {
      expect(category.name).toBeDefined();
      expect(Array.isArray(category.actions)).toBe(true);
      expect(category.actions.length).toBeGreaterThan(0);



describe('RESOURCE_TYPE_CATEGORIES', () => {
  it('should have valid resource type categories', () => {
    expect(RESOURCE_TYPE_CATEGORIES.USER).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.ADMIN).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.SYSTEM_CONFIG).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.AUDIT_LOG).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.SESSION).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.SECURITY_POLICY).toBeDefined();
    expect(RESOURCE_TYPE_CATEGORIES.SETUP).toBeDefined();

  it('should have name and value for each category', () => {
    Object.values(RESOURCE_TYPE_CATEGORIES).forEach(category => {
      expect(category.name).toBeDefined();
      expect(category.value).toBeDefined();
      expect(typeof category.name).toBe('string');
      expect(typeof category.value).toBe('string');



describe('auditFilters convenience functions', () => {
  it('should create filter builder', () => {
    const builder = auditFilters.builder();
    expect(builder).toBeInstanceOf(AuditFilterBuilder);

  it('should return today filter', () => {
    const filter = auditFilters.today();
    expect(filter.start_date).toBeInstanceOf(Date);
    expect(filter.end_date).toBeInstanceOf(Date);

  it('should return yesterday filter', () => {
    const filter = auditFilters.yesterday();
    expect(filter.start_date).toBeInstanceOf(Date);
    expect(filter.end_date).toBeInstanceOf(Date);

  it('should return user actions filter', () => {
    const filter = auditFilters.userActions();
    expect(filter.resource_type).toBe('user');

  it('should return admin actions filter', () => {
    const filter = auditFilters.adminActions();
    expect(filter.resource_type).toBe('admin');

  it('should return auth events filter', () => {
    const filter = auditFilters.authEvents();
    expect(filter.resource_type).toBe('session');

  it('should return security events filter', () => {
    const filter = auditFilters.securityEvents();
    expect(filter.resource_type).toBe('security_policy');

  it('should return failed logins filter', () => {
    const filter = auditFilters.failedLogins();
    expect(filter.action).toBe('auth.login_failed');

  it('should return successful logins filter', () => {
    const filter = auditFilters.successfulLogins();
    expect(filter.action).toBe('auth.login');


describe('auditPagination utilities', () => {
  it('should create default pagination', () => {
    const pagination = auditPagination.default();
    expect(pagination).toEqual({
      page: 1,
      limit: 50,
      sort_by: 'timestamp',
      sort_order: 'desc'


  it('should create large pagination', () => {
    const pagination = auditPagination.large();
    expect(pagination.limit).toBe(100);

  it('should create small pagination', () => {
    const pagination = auditPagination.small();
    expect(pagination.limit).toBe(25);

  it('should calculate offset correctly', () => {
    expect(auditPagination.calculateOffset(1, 50)).toBe(0);
    expect(auditPagination.calculateOffset(2, 50)).toBe(50);
    expect(auditPagination.calculateOffset(3, 25)).toBe(50);

  it('should calculate total pages correctly', () => {
    expect(auditPagination.calculateTotalPages(100, 50)).toBe(2);
    expect(auditPagination.calculateTotalPages(101, 50)).toBe(3);
    expect(auditPagination.calculateTotalPages(0, 50)).toBe(0);

  it('should check for next page correctly', () => {
    expect(auditPagination.hasNextPage(1, 3)).toBe(true);
    expect(auditPagination.hasNextPage(3, 3)).toBe(false);
    expect(auditPagination.hasNextPage(2, 3)).toBe(true);

  it('should check for previous page correctly', () => {
    expect(auditPagination.hasPrevPage(1)).toBe(false);
    expect(auditPagination.hasPrevPage(2)).toBe(true);
    expect(auditPagination.hasPrevPage(3)).toBe(true);

