"use client";
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  // In production, inputs should start empty to avoid leaking defaults
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email || !password) {
      setError('Email and password are required')
      return
    }
    try {
      await login({ email, password, totp_code: totp || undefined })
      // Redirect to main UI instead of profile page
      router.push('/')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
            <Input type="text" value={totp} onChange={e => setTotp(e.target.value)} placeholder="2FA code (if enabled)" />
            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button type="submit" className="w-full">Sign In</Button>
            <div className="text-sm text-center space-x-2">
              <a href="/signup" className="underline">Sign Up</a>
              <a href="/reset-password" className="underline">Forgot Password?</a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
