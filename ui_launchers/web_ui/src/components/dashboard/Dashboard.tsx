"use client";
import { useAuth } from '@/contexts/AuthContext';
import { HealthDashboard } from '../monitoring/health-dashboard';

export default function Dashboard() {
  const { user } = useAuth();
  if (!user) return null;
  const isAdmin = user.roles.includes('admin') || user.roles.includes('super_admin');
  return (
    <div className="space-y-4">
      {isAdmin ? (
        <>
          <h2 className="text-2xl font-semibold">Admin Dashboard</h2>
          <HealthDashboard />
        </>
      ) : (
        <>
          <h2 className="text-2xl font-semibold">My Dashboard</h2>
          <p className="text-muted-foreground">Welcome, {user.email}</p>
        </>
      )}
    </div>
  );
}
