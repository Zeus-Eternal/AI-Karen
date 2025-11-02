'use client';

/**
 * Super Admin Dashboard Page
 * 
 * This is the main entry point for the super admin dashboard.
 * It provides navigation to all admin management features.
 */


import { SuperAdminRoute } from '@/components/auth/SuperAdminRoute';
import SuperAdminDashboard from '@/components/admin/SuperAdminDashboard';

export default function AdminPage() {
  return (
    <SuperAdminRoute>
      <SuperAdminDashboard />
    </SuperAdminRoute>
  );
}