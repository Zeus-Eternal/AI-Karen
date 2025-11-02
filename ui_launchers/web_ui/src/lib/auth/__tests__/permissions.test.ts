/**
 * Unit tests for permission and role utility functions
 */

import { roleHasPermission, roleHierarchy, getRolePermissions, hasRequiredRole, createPermissionChecker, determineUserRole, isValidRole, getRoleDisplayName, getRoleDescription, canManageRole, ROLE_PERMISSIONS, UserRole } from '../permissions';

describe('Permission Utilities', () => {
  describe('roleHasPermission', () => {
    it('should return true for super_admin with admin_management permission', () => {
      expect(roleHasPermission('super_admin', 'admin_management')).toBe(true);

    it('should return false for admin with admin_management permission', () => {
      expect(roleHasPermission('admin', 'admin_management')).toBe(false);

    it('should return true for admin with user_management permission', () => {
      expect(roleHasPermission('admin', 'user_management')).toBe(true);

    it('should return false for user with any admin permission', () => {
      expect(roleHasPermission('user', 'user_management')).toBe(false);
      expect(roleHasPermission('user', 'admin_management')).toBe(false);

    it('should return false for non-existent permission', () => {
      expect(roleHasPermission('super_admin', 'non_existent_permission')).toBe(false);


  describe('roleHierarchy', () => {
    it('should return true for super_admin >= admin', () => {
      expect(roleHierarchy('super_admin', 'admin')).toBe(true);

    it('should return true for super_admin >= user', () => {
      expect(roleHierarchy('super_admin', 'user')).toBe(true);

    it('should return true for admin >= user', () => {
      expect(roleHierarchy('admin', 'user')).toBe(true);

    it('should return false for admin >= super_admin', () => {
      expect(roleHierarchy('admin', 'super_admin')).toBe(false);

    it('should return false for user >= admin', () => {
      expect(roleHierarchy('user', 'admin')).toBe(false);

    it('should return true for same roles', () => {
      expect(roleHierarchy('admin', 'admin')).toBe(true);
      expect(roleHierarchy('user', 'user')).toBe(true);
      expect(roleHierarchy('super_admin', 'super_admin')).toBe(true);


  describe('getRolePermissions', () => {
    it('should return correct permissions for super_admin', () => {
      const permissions = getRolePermissions('super_admin');
      expect(permissions).toContain('admin_management');
      expect(permissions).toContain('user_management');
      expect(permissions).toContain('system_config');
      expect(permissions.length).toBeGreaterThan(5);

    it('should return correct permissions for admin', () => {
      const permissions = getRolePermissions('admin');
      expect(permissions).toContain('user_management');
      expect(permissions).not.toContain('admin_management');
      expect(permissions).not.toContain('system_config');

    it('should return empty array for user', () => {
      const permissions = getRolePermissions('user');
      expect(permissions).toEqual([]);


  describe('hasRequiredRole', () => {
    it('should return true when user role meets requirement', () => {
      expect(hasRequiredRole('super_admin', 'admin')).toBe(true);
      expect(hasRequiredRole('admin', 'user')).toBe(true);
      expect(hasRequiredRole('admin', 'admin')).toBe(true);

    it('should return false when user role does not meet requirement', () => {
      expect(hasRequiredRole('user', 'admin')).toBe(false);
      expect(hasRequiredRole('admin', 'super_admin')).toBe(false);


  describe('createPermissionChecker', () => {
    it('should create checker with correct role detection', () => {
      const checker = createPermissionChecker('admin');
      expect(checker.hasRole('admin')).toBe(true);
      expect(checker.hasRole('user')).toBe(true);
      expect(checker.hasRole('super_admin')).toBe(false);
      expect(checker.isAdmin()).toBe(true);
      expect(checker.isSuperAdmin()).toBe(false);

    it('should create checker from roles array', () => {
      const checker = createPermissionChecker(undefined, ['admin', 'user']);
      expect(checker.hasRole('admin')).toBe(true);
      expect(checker.isAdmin()).toBe(true);

    it('should check explicit permissions', () => {
      const checker = createPermissionChecker('user', undefined, ['special_permission']);
      expect(checker.hasPermission('special_permission')).toBe(true);
      expect(checker.hasPermission('user_management')).toBe(false);

    it('should fall back to role-based permissions', () => {
      const checker = createPermissionChecker('admin');
      expect(checker.hasPermission('user_management')).toBe(true);
      expect(checker.hasPermission('admin_management')).toBe(false);


  describe('determineUserRole', () => {
    it('should return super_admin when present in roles', () => {
      expect(determineUserRole(['user', 'admin', 'super_admin'])).toBe('super_admin');

    it('should return admin when present but no super_admin', () => {
      expect(determineUserRole(['user', 'admin'])).toBe('admin');

    it('should return user as default', () => {
      expect(determineUserRole(['user'])).toBe('user');
      expect(determineUserRole([])).toBe('user');
      expect(determineUserRole(['unknown_role'])).toBe('user');


  describe('isValidRole', () => {
    it('should return true for valid roles', () => {
      expect(isValidRole('super_admin')).toBe(true);
      expect(isValidRole('admin')).toBe(true);
      expect(isValidRole('user')).toBe(true);

    it('should return false for invalid roles', () => {
      expect(isValidRole('invalid_role')).toBe(false);
      expect(isValidRole('')).toBe(false);
      expect(isValidRole('ADMIN')).toBe(false);


  describe('getRoleDisplayName', () => {
    it('should return correct display names', () => {
      expect(getRoleDisplayName('super_admin')).toBe('Super Admin');
      expect(getRoleDisplayName('admin')).toBe('Admin');
      expect(getRoleDisplayName('user')).toBe('User');


  describe('getRoleDescription', () => {
    it('should return meaningful descriptions', () => {
      const superAdminDesc = getRoleDescription('super_admin');
      const adminDesc = getRoleDescription('admin');
      const userDesc = getRoleDescription('user');

      expect(superAdminDesc).toContain('Full system access');
      expect(adminDesc).toContain('User management');
      expect(userDesc).toContain('Standard user');


  describe('canManageRole', () => {
    it('should allow super_admin to manage everyone', () => {
      expect(canManageRole('super_admin', 'super_admin')).toBe(true);
      expect(canManageRole('super_admin', 'admin')).toBe(true);
      expect(canManageRole('super_admin', 'user')).toBe(true);

    it('should allow admin to manage only users', () => {
      expect(canManageRole('admin', 'user')).toBe(true);
      expect(canManageRole('admin', 'admin')).toBe(false);
      expect(canManageRole('admin', 'super_admin')).toBe(false);

    it('should not allow user to manage anyone', () => {
      expect(canManageRole('user', 'user')).toBe(false);
      expect(canManageRole('user', 'admin')).toBe(false);
      expect(canManageRole('user', 'super_admin')).toBe(false);


  describe('ROLE_PERMISSIONS constant', () => {
    it('should have all required permissions for super_admin', () => {
      const superAdminPerms = ROLE_PERMISSIONS.super_admin;
      expect(superAdminPerms).toContain('user_management');
      expect(superAdminPerms).toContain('admin_management');
      expect(superAdminPerms).toContain('system_config');
      expect(superAdminPerms).toContain('audit_logs');
      expect(superAdminPerms).toContain('security_settings');

    it('should have user management permissions for admin', () => {
      const adminPerms = ROLE_PERMISSIONS.admin;
      expect(adminPerms).toContain('user_management');
      expect(adminPerms).toContain('user_create');
      expect(adminPerms).toContain('user_edit');
      expect(adminPerms).toContain('user_delete');

    it('should have no permissions for user', () => {
      expect(ROLE_PERMISSIONS.user).toEqual([]);


