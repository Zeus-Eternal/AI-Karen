/**
 * Tests for Admin Database Utils
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { AdminDatabaseUtils, getAdminDatabaseUtils } from '../admin-utils';
import { MockDatabaseClient } from '../client';
import { UserListFilter, PaginationParams } from '@/types/admin';

describe('AdminDatabaseUtils', () => {
  let adminUtils: AdminDatabaseUtils;
  let mockClient: MockDatabaseClient;

  beforeEach(() => {
    mockClient = new MockDatabaseClient();
    adminUtils = new AdminDatabaseUtils(mockClient);

  describe('getUserWithRole', () => {
    it('should return user with role information', async () => {
      const userId = '123e4567-e89b-12d3-a456-426614174000';
      const user = await adminUtils.getUserWithRole(userId);
      
      expect(user).toBeDefined();
      expect(user?.user_id).toBe(userId);
      expect(user?.role).toBe('super_admin');

    it('should return null for non-existent user', async () => {
      // Mock client returns empty result for non-matching queries
      const user = await adminUtils.getUserWithRole('non-existent');
      expect(user).toBeNull();


  describe('getUsersWithRoleFilter', () => {
    it('should return paginated users with default parameters', async () => {
      const result = await adminUtils.getUsersWithRoleFilter();
      
      expect(result).toBeDefined();
      expect(result.data).toBeInstanceOf(Array);
      expect(result.pagination).toBeDefined();
      expect(result.pagination.page).toBe(1);
      expect(result.pagination.limit).toBe(20);

    it('should apply role filter', async () => {
      const filter: UserListFilter = { role: 'admin' };
      const pagination: PaginationParams = { page: 1, limit: 10 };
      
      const result = await adminUtils.getUsersWithRoleFilter(filter, pagination);
      
      expect(result.pagination.limit).toBe(10);

    it('should apply search filter', async () => {
      const filter: UserListFilter = { search: 'admin' };
      
      const result = await adminUtils.getUsersWithRoleFilter(filter);
      
      expect(result).toBeDefined();


  describe('createAuditLog', () => {
    it('should create audit log entry', async () => {
      const auditEntry = {
        user_id: '123e4567-e89b-12d3-a456-426614174000',
        action: 'user.create',
        resource_type: 'user',
        resource_id: 'new-user-id',
        details: { email: 'test@example.com' }
      };

      const auditId = await adminUtils.createAuditLog(auditEntry);
      
      expect(auditId).toBeDefined();


  describe('userHasPermission', () => {
    it('should check user permissions', async () => {
      const userId = '123e4567-e89b-12d3-a456-426614174000';
      const permission = 'user.create';
      
      const hasPermission = await adminUtils.userHasPermission(userId, permission);
      
      expect(typeof hasPermission).toBe('boolean');


  describe('getSystemConfig', () => {
    it('should return system configuration', async () => {
      const config = await adminUtils.getSystemConfig();
      
      expect(config).toBeInstanceOf(Array);

    it('should filter by category', async () => {
      const config = await adminUtils.getSystemConfig('security');
      
      expect(config).toBeInstanceOf(Array);


  describe('canUserPerformAction', () => {
    it('should check if user can perform action', async () => {
      const userId = '123e4567-e89b-12d3-a456-426614174000';
      
      const canPerform = await adminUtils.canUserPerformAction(
        userId, 
        'create', 
        'user'
      );
      
      expect(typeof canPerform).toBe('boolean');


  describe('convenience function', () => {
    it('should create AdminDatabaseUtils instance', () => {
      const utils = getAdminDatabaseUtils();
      
      expect(utils).toBeInstanceOf(AdminDatabaseUtils);

    it('should use provided client', () => {
      const customClient = new MockDatabaseClient();
      const utils = getAdminDatabaseUtils(customClient);
      
      expect(utils).toBeInstanceOf(AdminDatabaseUtils);


