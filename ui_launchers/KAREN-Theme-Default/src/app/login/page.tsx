"use client";

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/auth/LoginForm';
export default function LoginPage() {
  const router = useRouter()
  const handleLoginSuccess = async () => {
    // Redirect to main UI after successful login
    // Longer delay to ensure session is fully established and AuthContext is updated
    await new Promise(resolve => setTimeout(resolve, 500));
    // Check if there's a stored redirect path
    const redirectPath = sessionStorage.getItem('redirectAfterLogin') || '/';
    sessionStorage.removeItem('redirectAfterLogin');
    // Use router.replace for better Next.js integration
    router.replace(redirectPath);
  }
  return <LoginForm onSuccess={handleLoginSuccess} />
}
