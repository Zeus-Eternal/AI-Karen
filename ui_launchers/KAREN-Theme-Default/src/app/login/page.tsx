"use client";

import * as React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleLoginSuccess = () => {
    const redirectFromQuery = searchParams?.get('redirectPath');
    const redirectFromStorage = sessionStorage.getItem('redirectAfterLogin');
    const redirectPath = redirectFromQuery ?? redirectFromStorage ?? '/';

    sessionStorage.removeItem('redirectAfterLogin');

    // Redirect immediately - AuthContext has already updated authentication state
    router.replace(redirectPath);
  };

  return <LoginForm onSuccess={handleLoginSuccess} />;
}
