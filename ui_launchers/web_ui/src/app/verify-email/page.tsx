"use client";
import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [message, setMessage] = useState('Verifying...');

  useEffect(() => {
    const verify = async () => {
      const res = await fetch(`/api/auth/verify_email?token=${token}`);
      if (res.ok) setMessage('Email verified. You can log in.');
      else setMessage('Verification failed');
    };
    if (token) verify();
  }, [token]);

  return (
    <div className="flex items-center justify-center h-screen">
      <p>{message}</p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <p>Loading...</p>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
