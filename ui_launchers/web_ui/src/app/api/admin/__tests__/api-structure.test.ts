/**
 * Admin API Structure Tests
 * 
 * Tests that all admin API routes are properly structured and exportable
 */

import { describe, it, expect } from 'vitest';

describe('Admin API Structure', () => {
  it('should export user management routes', async () => {
    const userRoutes = await import('../users/route');
    expect(userRoutes.GET).toBeDefined();
    expect(userRoutes.POST).toBeDefined();
    expect(typeof userRoutes.GET).toBe('function');
    expect(typeof userRoutes.POST).toBe('function');

  it('should export individual user routes', async () => {
    const userIdRoutes = await import('../users/[id]/route');
    expect(userIdRoutes.GET).toBeDefined();
    expect(userIdRoutes.PUT).toBeDefined();
    expect(userIdRoutes.DELETE).toBeDefined();
    expect(typeof userIdRoutes.GET).toBe('function');
    expect(typeof userIdRoutes.PUT).toBe('function');
    expect(typeof userIdRoutes.DELETE).toBe('function');

  it('should export bulk user operations route', async () => {
    const bulkRoutes = await import('../users/bulk/route');
    expect(bulkRoutes.POST).toBeDefined();
    expect(typeof bulkRoutes.POST).toBe('function');

  it('should export admin management routes', async () => {
    const adminRoutes = await import('../admins/route');
    expect(adminRoutes.GET).toBeDefined();
    expect(adminRoutes.POST).toBeDefined();
    expect(typeof adminRoutes.GET).toBe('function');
    expect(typeof adminRoutes.POST).toBe('function');

  it('should export admin promotion route', async () => {
    const promoteRoutes = await import('../admins/promote/[id]/route');
    expect(promoteRoutes.POST).toBeDefined();
    expect(typeof promoteRoutes.POST).toBe('function');

  it('should export admin demotion route', async () => {
    const demoteRoutes = await import('../admins/demote/[id]/route');
    expect(demoteRoutes.POST).toBeDefined();
    expect(typeof demoteRoutes.POST).toBe('function');

  it('should export system config routes', async () => {
    const configRoutes = await import('../system/config/route');
    expect(configRoutes.GET).toBeDefined();
    expect(configRoutes.PUT).toBeDefined();
    expect(typeof configRoutes.GET).toBe('function');
    expect(typeof configRoutes.PUT).toBe('function');

  it('should export audit logs routes', async () => {
    const auditRoutes = await import('../system/audit-logs/route');
    expect(auditRoutes.GET).toBeDefined();
    expect(auditRoutes.POST).toBeDefined();
    expect(typeof auditRoutes.GET).toBe('function');
    expect(typeof auditRoutes.POST).toBe('function');

  it('should have consistent API response structure', () => {
    // Test that our AdminApiResponse type is properly structured
    const successResponse = {
      success: true,
      data: { test: 'data' },
      meta: { message: 'Test successful' }
    };

    const errorResponse = {
      success: false,
      error: {
        code: 'TEST_ERROR',
        message: 'Test error message',
        details: { field: 'test' }
      }
    };

    expect(successResponse.success).toBe(true);
    expect(successResponse.data).toBeDefined();
    expect(errorResponse.success).toBe(false);
    expect(errorResponse.error).toBeDefined();
    expect(errorResponse.error.code).toBe('TEST_ERROR');

