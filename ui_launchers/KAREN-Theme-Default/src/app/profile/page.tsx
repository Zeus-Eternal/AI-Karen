"use client";

import * as React from 'react';
import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getMemoryService } from '@/services/memoryService';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [memoryCount, setMemoryCount] = useState<number | null>(null);
  const isClient = typeof window !== 'undefined';

  useEffect(() => {
    if (!user?.userId) return;

    let cancelled = false;
    const load = async () => {
      try {
        const stats = await getMemoryService().getMemoryStats(user.userId);
        if (!cancelled) {
          setMemoryCount(stats.totalMemories);
        }
      } catch {
        if (!cancelled) {
          setMemoryCount(null);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [user?.userId]);

  if (!isClient) {
    return <div>Loading...</div>;
  }

  if (!user) {
    router.push('/login');
    return null;
  }

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>Logged in as <span className="font-semibold">{user?.userId}</span></div>
          <div>Email: <span className="font-semibold">{user?.email}</span></div>
          <div>Roles: <span className="font-semibold">{user?.roles.join(', ')}</span></div>
          {memoryCount !== null && <div>Total memories: {memoryCount}</div>}
          
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={logout}>
              Log Out
            </Button>
          </div>

          <div className="text-sm text-gray-600">
            Profile editing and two-factor authentication setup are currently not available.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
