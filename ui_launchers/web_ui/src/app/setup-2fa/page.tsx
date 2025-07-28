"use client";
import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function Setup2FAPage() {
  const { user, refreshUser } = useAuth();
  const [qrUrl, setQrUrl] = useState('');
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    authService.setupTwoFactor().then(res => setQrUrl(res.otpauth_url)).catch(err => setMessage(err.message));
  }, []);

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await authService.confirmTwoFactor(code);
      setMessage('Two-factor authentication enabled');
      await refreshUser();
    } catch (err: any) {
      setMessage(err.message);
    }
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
