"use client";
import { useRouter } from 'next/navigation'
import { LoginForm } from '@/components/auth/LoginForm'

export default function LoginPage() {
  const router = useRouter()

  const handleLoginSuccess = () => {
    // Redirect to main UI after successful login
    router.push('/')
  }

  return <LoginForm onSuccess={handleLoginSuccess} />
}
