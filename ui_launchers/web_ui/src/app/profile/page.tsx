"use client";
import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getMemoryService } from '@/services/memoryService'

export default function ProfilePage() {
  const { user, updateCredentials, logout } = useAuth()
  const router = useRouter()
  const [memoryCount, setMemoryCount] = useState<number | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    if (!user) return
    setUsername(user.user_id)
    getMemoryService()
      .getMemoryStats(user.user_id)
      .then(stats => setMemoryCount(stats.totalMemories))
      .catch(() => setMemoryCount(null))
  }, [user])

  if (!user) {
    router.push('/login')
    return null
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    await updateCredentials(username !== user.user_id ? username : undefined, password || undefined)
    setPassword('')
  }

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>Logged in as <span className="font-semibold">{user.user_id}</span></div>
          {memoryCount !== null && <div>Total memories: {memoryCount}</div>}
          <form onSubmit={handleSave} className="space-y-3">
            <Input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="New password" />
            <div className="flex gap-2">
              <Button type="submit">Save</Button>
              <Button type="button" variant="secondary" onClick={logout}>Log Out</Button>
            </div>
          </form>
          <div>
            {user.two_factor_enabled ? (
              <a href="/setup-2fa" className="underline">Manage 2FA</a>
            ) : (
              <a href="/setup-2fa" className="underline">Enable Two-Factor Authentication</a>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
