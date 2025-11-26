"use client";

import { useRouter, useSearchParams } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
import { useState, useEffect } from 'react';

export default function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component is mounted before rendering to avoid hydration mismatch
  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleLoginSuccess = async () => {
    const redirectFromQuery = searchParams?.get('redirectPath');
    let redirectFromStorage = '/';
    
    // Only access sessionStorage on client side to avoid hydration mismatch
    if (typeof window !== 'undefined') {
      redirectFromStorage = sessionStorage.getItem('redirectAfterLogin') || '/';
      sessionStorage.removeItem('redirectAfterLogin');
    }
    
    const redirectPath = redirectFromQuery ?? redirectFromStorage ?? '/';

    // Wait for next tick to ensure auth state has fully propagated
    await new Promise((resolve) => setTimeout(resolve, 0));

    // Redirect after auth state has settled
    router.replace(redirectPath);
  };

  // Show a loading state that matches the server rendering while mounting
  if (!isMounted) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
          <h1 className="text-2xl font-bold text-center mb-6 text-gray-800 dark:text-white">
            Loading...
          </h1>
          <div>Loading...</div>
        </div>
      </div>
    );
  }

  return <LoginForm onSuccess={handleLoginSuccess} />;
}
