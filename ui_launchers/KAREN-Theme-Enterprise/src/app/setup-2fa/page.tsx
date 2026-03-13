"use client";

import * as React from 'react';
import { useState } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const NOT_AVAILABLE_MESSAGE = 'Two-factor authentication setup is currently not available.';

export default function Setup2FAPage() {
  const { user } = useAuth();
  const [code, setCode] = useState('');

  const handleConfirm = (e: React.FormEvent) => {
    e.preventDefault();
    // The 2FA flow is intentionally disabled until the backend implementation is ready.
  };

  if (!user) return null;

  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Two-Factor Authentication</h1>
      <form onSubmit={handleConfirm} className="space-y-2">
        <Input value={code} onChange={e => setCode(e.target.value)} placeholder="Enter code" />
        <Button type="submit">Confirm</Button>
      </form>
      <p className="text-sm">{NOT_AVAILABLE_MESSAGE}</p>
    </div>
  );
}
