"use client";

import AdminSettingsPage from "@/components/admin/AdminSettingsPage";

export default function AdminPage() {
  // Canonical admin surface now lives at /admin.
  // Keep this route as the single source of truth for fallback model controls,
  // maintenance, analytics, audit logs, and user management.
  return <AdminSettingsPage />;
}
