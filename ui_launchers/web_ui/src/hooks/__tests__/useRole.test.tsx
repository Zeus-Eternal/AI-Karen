/**
 * Unit tests for useRole hook and related role hooks
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRole, useHasRole, useHasPermission, useIsAdmin, useIsSuperAdmin } from '../useRole';
import { useAuth } from '@/contexts/AuthContext';

// Mock the useAuth hook
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn()
}));

const mockUseAuth = useAuth as any;

describe('useRole Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  describe('useRole', () => {
    it('should return correct role information for super admin', () => {
      mockUseAuth.mockReturnValue({
        user: {
          user_id: '1',
          email: 'admin@test.com',
          roles: ['super_admin'],
          tenant_id: '1',
          role: 'super_admin'
        },
        isAuthenticated: true,
        hasRole: vi.fn((role) => role === 'super_admin'),
        hasPermission: vi.fn((permission) => ['admin_management', 'user_management', 'system_config'].includes(permission)),
        isAdmin: vi.fn(() => true),
        isSuperAdmin: vi.fn(() => true),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useRole());

      expect(result.current.role).toBe('super_admin');
      expect(result.current.isAdmin).toBe(true);
      expect(result.current.isSuperAdmin).toBe(true);
      expect(result.current.isUser).toBe(false);
      expect(result.current.canManageUsers).toBe(true);
      expect(result.current.canManageAdmins).toBe(true);
      expect(result.current.canManageSystem).toBe(true);

    it('should return correct role information for admin', () => {
      mockUseAuth.mockReturnValue({
        user: {
          user_id: '2',
          email: 'admin@test.com',
          roles: ['admin'],
          tenant_id: '1',
          role: 'admin'
        },
        isAuthenticated: true,
        hasRole: vi.fn((role) => role === 'admin' || role === 'user'),
        hasPermission: vi.fn((permission) => ['user_management'].includes(permission)),
        isAdmin: vi.fn(() => true),
        isSuperAdmin: vi.fn(() => false),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useRole());

      expect(result.current.role).toBe('admin');
      expect(result.current.isAdmin).toBe(true);
      expect(result.current.isSuperAdmin).toBe(false);
      expect(result.current.canManageUsers).toBe(true);
      expect(result.current.canManageAdmins).toBe(false);
      expect(result.current.canManageSystem).toBe(false);

    it('should return correct role information for regular user', () => {
      mockUseAuth.mockReturnValue({
        user: {
          user_id: '3',
          email: 'user@test.com',
          roles: ['user'],
          tenant_id: '1',
          role: 'user'
        },
        isAuthenticated: true,
        hasRole: vi.fn((role) => role === 'user'),
        hasPermission: vi.fn(() => false),
        isAdmin: vi.fn(() => false),
        isSuperAdmin: vi.fn(() => false),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useRole());

      expect(result.current.role).toBe('user');
      expect(result.current.isAdmin).toBe(false);
      expect(result.current.isSuperAdmin).toBe(false);
      expect(result.current.isUser).toBe(true);
      expect(result.current.canManageUsers).toBe(false);
      expect(result.current.canManageAdmins).toBe(false);
      expect(result.current.canManageSystem).toBe(false);

    it('should return null role when user is not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        hasRole: vi.fn(() => false),
        hasPermission: vi.fn(() => false),
        isAdmin: vi.fn(() => false),
        isSuperAdmin: vi.fn(() => false),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useRole());

      expect(result.current.role).toBe(null);
      expect(result.current.isAdmin).toBe(false);
      expect(result.current.isSuperAdmin).toBe(false);
      expect(result.current.isUser).toBe(false);


  describe('useHasRole', () => {
    it('should return true when user has required role', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn((role) => role === 'admin'),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useHasRole('admin'));
      expect(result.current).toBe(true);

    it('should return false when user does not have required role', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn((role) => role === 'user'),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useHasRole('admin'));
      expect(result.current).toBe(false);


  describe('useHasPermission', () => {
    it('should return true when user has required permission', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn((permission) => permission === 'user_management'),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useHasPermission('user_management'));
      expect(result.current).toBe(true);

    it('should return false when user does not have required permission', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn(() => false),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useHasPermission('admin_management'));
      expect(result.current).toBe(false);


  describe('useIsAdmin', () => {
    it('should return true for admin users', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(() => true),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useIsAdmin());
      expect(result.current).toBe(true);

    it('should return false for regular users', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(() => false),
        isSuperAdmin: vi.fn(),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useIsAdmin());
      expect(result.current).toBe(false);


  describe('useIsSuperAdmin', () => {
    it('should return true for super admin users', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(() => true),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useIsSuperAdmin());
      expect(result.current).toBe(true);

    it('should return false for non-super admin users', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        hasRole: vi.fn(),
        hasPermission: vi.fn(),
        isAdmin: vi.fn(),
        isSuperAdmin: vi.fn(() => false),
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn()

      const { result } = renderHook(() => useIsSuperAdmin());
      expect(result.current).toBe(false);


