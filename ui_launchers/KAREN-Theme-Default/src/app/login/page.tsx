"use client";

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleLoginSuccess = async () => {
    const redirectFromQuery = searchParams?.get('redirectPath');
    const redirectFromStorage = sessionStorage.getItem('redirectAfterLogin');
    const redirectPath = redirectFromQuery ?? redirectFromStorage ?? '/';

    sessionStorage.removeItem('redirectAfterLogin');
    // Wait briefly to ensure authentication state has settled
    await new Promise((resolve) => setTimeout(resolve, 500));

    router.replace(redirectPath);
  };

  return <LoginForm onSuccess={handleLoginSuccess} />;
}
