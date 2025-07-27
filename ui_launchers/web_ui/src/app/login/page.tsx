"use client";
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/auth'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  // In production, inputs should start empty to avoid leaking defaults
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const ok = await login(username, password)
    if (ok) {
      router.push('/profile')
    } else {
      setError('Login failed')
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
            <Input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
            {error && <p className="text-destructive text-sm">{error}</p>}
            <Button type="submit" className="w-full">Sign In</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
