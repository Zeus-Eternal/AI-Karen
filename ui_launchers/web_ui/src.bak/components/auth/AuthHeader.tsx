"use client";
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

export default function AuthHeader() {
  const { user } = useAuth()
  return (
    <Link href={user ? '/profile' : '/login'} className="text-sm font-medium underline">
      {user ? user.user_id : 'Login'}
    </Link>
  )
}
