"use client";

import * as React from 'react';
import { useState } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function Setup2FAPage() {
  const { user } = useAuth();
  const qrUrl = '';
  const [code, setCode] = useState('');
  const message = 'Two-factor authentication setup is currently not available.';

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    // The 2FA flow is intentionally disabled until the backend implementation is ready.
  };

  if (!user) return null;

  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Two-Factor Authentication</h1>
      {qrUrl && (
        <img src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrUrl)}`} alt="2FA QR" />
      )}
      <form onSubmit={handleConfirm} className="space-y-2">
        <Input value={code} onChange={e => setCode(e.target.value)} placeholder="Enter code" />
        <Button type="submit">Confirm</Button>
      </form>
      {message && <p className="text-sm">{message}</p>}
    </div>
  );
}
