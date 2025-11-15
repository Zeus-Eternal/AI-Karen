"use client";

import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';

export default function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleLoginSuccess = async () => {
    const redirectFromQuery = searchParams?.get('redirectPath');
    const redirectFromStorage = sessionStorage.getItem('redirectAfterLogin');
    const redirectPath = redirectFromQuery ?? redirectFromStorage ?? '/';

    sessionStorage.removeItem('redirectAfterLogin');

    // Wait for next tick to ensure auth state has fully propagated
    await new Promise((resolve) => setTimeout(resolve, 0));

    // Redirect after auth state has settled
    router.replace(redirectPath);
  };

  return <LoginForm onSuccess={handleLoginSuccess} />;
}
